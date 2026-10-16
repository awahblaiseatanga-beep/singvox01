import { describe, it, expect } from 'vitest';
import fs from 'fs';
import { SpoterInferenceSession } from '../lib/inference';
import { applyV2Normalization } from '../lib/normalize';
import { ASL_VOCAB } from '../lib/vocab';
import { BASELINE_STABILIZER_CONFIG, TemporalStabilizer } from '../lib/temporalStabilizer';
import { SequenceBuffer } from '../lib/sequenceBuffer';
import { TemporalSampler, SAMPLE_INTERVAL_MS, observationFrom } from '../lib/temporalSampler';
import { emptyPresence, type CanonicalFrame, type GroupPresence } from '../lib/contracts';

/**
 * Offline comparison of three ways of writing the SPOTER V2 window, replaying the
 * same recorded clip through the real production classes (SequenceBuffer,
 * TemporalStabilizer, SpoterInferenceSession) and the same V2 normalization.
 *
 *   observations : one buffer frame per completed detection - the loop that ran
 *                  before this pass. The window advances at the device's
 *                  observation rate, so 60 frames represent 60 observation
 *                  intervals of real time.
 *   gridHold     : fixed 125 ms grid, each grid point holding the newest real
 *                  observation. Isolates the cadence change.
 *   gridInterp   : fixed 125 ms grid via the shipped TemporalSampler, blending
 *                  grid points that fall between two real observations. This is
 *                  the behaviour the app now runs; the comparison against
 *                  gridHold isolates the interpolation itself.
 *
 * The clip's own 10 fps frames are the source of truth. A slower device observes
 * a subset of them, which is what the observation stream models.
 */

const FEATURE_DIM = 366;
const CLIP_FPS = 10;

// The parity replay needs two local-only recorded feature dumps and the full
// 79-class graph (all gitignored). Skip — never silently pass, never fail —
// when a clean clone does not carry them: the recorded top-1 / commit claims
// this test makes are evidence about those clips and that graph, and synthetic
// data must not stand in for them. The cadence invariants themselves (the
// fixed 125 ms grid completes a window sooner than the 150 ms observation
// cadence) are re-run on a synthetic timeline in syntheticFixtures.test.ts.
const ROOT = process.cwd().replace(/\\/g, '/').split('/web')[0];
const DATASET_DIR = `${ROOT}/ai/sign-recognition/data/dataset_extracted`;
const GRAPH_V2 = `${ROOT}/web/public/spoter_v2_model.onnx`;
const RECORDED_CLIPS = [
  { label: 'HELLO', base: '0022932153577568393-HELLO' },
  { label: 'YES', base: '9953610281521326-YES' },
];
const HAVE_FIXTURES =
  fs.existsSync(GRAPH_V2) &&
  RECORDED_CLIPS.every((clip) => fs.existsSync(`${DATASET_DIR}/${clip.base}_features.npy`));
/**
 * Measured cost of one full pose+hands+face pass on the MediaPipe GPU delegate
 * (web/bench/recognition-bench.html: 154.9 ms median over 40 recorded frames).
 * This is the rate the detector can actually observe the signer at.
 */
const OBSERVATION_INTERVAL_MS = 150;
// Replay length in clip frames (10 fps). Long clips are truncated so the three
// arms stay affordable in the default suite; the recorded sign sits well inside
// the first 12 s of both replay clips.
const TIMELINE_FRAMES = 120;
const SUB_STEP_MS = 25;

function loadNpy(filePath: string): Float32Array {
  const buffer = fs.readFileSync(filePath);
  const headerLen = buffer.readUInt16LE(8);
  const dataBuf = buffer.subarray(10 + headerLen);
  return new Float32Array(dataBuf.buffer, dataBuf.byteOffset, dataBuf.byteLength / 4);
}

type ArmResult = {
  readyAfterMs: number;
  inferenceCount: number;
  commits: string[];
  topClass: string;
  topConfidence: number;
  /** Top-1 class of the last window (used for the framing comparison). */
  finalTop: string;
  finalConfidence: number;
};

describe.skipIf(!HAVE_FIXTURES)('Temporal window framing parity on recorded clips', () => {
  it('reaches the recorded sign with the fixed 125 ms grid and preserves the top-1 decision', async () => {
    const clips = RECORDED_CLIPS;

    const session = await SpoterInferenceSession.create(GRAPH_V2);

    for (const clip of clips) {
      const features = loadNpy(`${DATASET_DIR}/${clip.base}_features.npy`);
      const leadFrames = 20;
      const clipFrames = Math.min(features.length / FEATURE_DIM, TIMELINE_FRAMES - leadFrames);
      const timeline: Float32Array[] = [];
      for (let i = 0; i < leadFrames; i += 1) timeline.push(features.subarray(0, FEATURE_DIM));
      for (let i = 0; i < clipFrames; i += 1) {
        timeline.push(features.subarray(i * FEATURE_DIM, (i + 1) * FEATURE_DIM));
      }
      while (timeline.length < TIMELINE_FRAMES) {
        timeline.push(features.subarray((clipFrames - 1) * FEATURE_DIM, clipFrames * FEATURE_DIM));
      }
      const timelineMs = (timeline.length / CLIP_FPS) * 1000;
      const normalized = timeline.map((raw) => applyV2Normalization(new Float32Array(raw)));
      const frameAt = (ms: number) =>
        normalized[Math.min(normalized.length - 1, Math.max(0, Math.round((ms / 1000) * CLIP_FPS)))];

      const allPresent = emptyPresence();
      allPresent.leftHand = true;
      allPresent.rightHand = true;
      allPresent.pose = true;
      allPresent.face = true;
      const frame: CanonicalFrame = {
        raw: new Float32Array(FEATURE_DIM),
        presence: allPresent,
        invalidGroups: [],
        handAssignments: [],
      };

      // Arm 1: previous behaviour - the window advances once per observation.
      const observations = await replay({
        session,
        timelineMs,
        produce: (nowMs) => {
          if (nowMs % OBSERVATION_INTERVAL_MS !== 0) return [];
          return [{ vector: frameAt(nowMs), presence: allPresent, timestampMs: nowMs }];
        },
      });

      // Arm 2: fixed grid, newest observation held at every grid point. The grid
      // starts at t=0 so its phase matches the sampler's (which starts on the
      // first observation), keeping the two cadences directly comparable.
      let gridHoldClock = -SAMPLE_INTERVAL_MS;
      const gridHold = await replay({
        session,
        timelineMs,
        produce: (nowMs) => {
          const due: number[] = [];
          while (gridHoldClock + SAMPLE_INTERVAL_MS <= nowMs) {
            gridHoldClock += SAMPLE_INTERVAL_MS;
            due.push(gridHoldClock);
          }
          return due.map((timestampMs) => ({ vector: frameAt(nowMs), presence: allPresent, timestampMs }));
        },
      });

      // Arm 3: fixed grid through the shipped sampler.
      const sampler = new TemporalSampler();
      const gridInterp = await replay({
        session,
        timelineMs,
        produce: (nowMs) => {
          if (nowMs % OBSERVATION_INTERVAL_MS === 0) {
            sampler.observe(observationFrom(frame, frameAt(nowMs), nowMs));
          }
          return sampler.sampleUntil(nowMs).map((sample) => ({
            vector: sample.normalized,
            presence: sample.presence as GroupPresence,
            timestampMs: sample.timestampMs,
          }));
        },
      });

      console.log(
        `\n[parity] ${clip.label}: ${clipFrames} recorded frames (${(clipFrames / CLIP_FPS).toFixed(1)} s), ` +
          `device observations every ${OBSERVATION_INTERVAL_MS} ms`,
      );
      for (const [name, arm] of [
        ['observations', observations],
        ['gridHold    ', gridHold],
        ['gridInterp  ', gridInterp],
      ] as const) {
        console.log(
          `  ${name}: window ready after ${String(arm.readyAfterMs).padStart(6)} ms, ` +
            `${String(arm.inferenceCount).padStart(3)} inferences, commits=[${arm.commits}], ` +
            `final=${arm.finalTop} ${arm.finalConfidence.toFixed(3)}`,
        );
      }

      // The fixed grid completes the window earlier than the observation cadence.
      expect(gridInterp.readyAfterMs).toBeLessThan(observations.readyAfterMs);
      expect(gridHold.readyAfterMs).toBe(gridInterp.readyAfterMs);
      // Recognition is preserved with the fixed grid, and the recorded sign is
      // still the one that gets committed.
      expect(gridInterp.commits).toContain(clip.label);
      // The interpolated framing still resolves the clip's own sign on the final
      // window. On HELLO the held grid drifts to another class at the same window
      // (measured: CHILD 0.897 held vs HELLO 0.982 interpolated), so holding is
      // not the safe reference here; the recorded clip is.
      expect(gridInterp.finalTop).toBe(clip.label);
    }
  }, 300_000);
});

/** Drives the real buffer + stabilizer + ONNX session over a timeline. */
async function replay(input: {
  session: SpoterInferenceSession;
  timelineMs: number;
  produce: (nowMs: number) => { vector: Float32Array; presence: GroupPresence; timestampMs: number }[];
}): Promise<ArmResult> {
  const { session, timelineMs, produce } = input;
  const buffer = new SequenceBuffer();
  const stabilizer = new TemporalStabilizer(BASELINE_STABILIZER_CONFIG);
  const commits: string[] = [];
  let readyAfterMs = 0;
  let inferenceCount = 0;
  let topClass = '—';
  let topConfidence = 0;
  let finalTop = '—';
  let finalConfidence = 0;

  for (let nowMs = 0; nowMs <= timelineMs; nowMs += SUB_STEP_MS) {
    for (const produced of produce(nowMs)) {
      buffer.push(produced.vector, {
        presence: produced.presence,
        nonFiniteCount: 0,
        timestampMs: produced.timestampMs,
      });
    }
    if (!buffer.isReady || nowMs % SAMPLE_INTERVAL_MS !== 0) continue;
    if (readyAfterMs === 0) readyAfterMs = nowMs;

    const flat = buffer.getFlattenedBuffer();
    if (!flat) continue;
    const result = await session.predict(flat, ASL_VOCAB);
    // The 79-class baseline must still return 79 logits on every window.
    expect(result.logits.length).toBe(79);
    const top = result.topK[0];
    inferenceCount += 1;
    finalTop = top.className;
    finalConfidence = top.confidence;
    if (top.confidence > topConfidence) {
      topConfidence = top.confidence;
      topClass = top.className;
    }
    const state = stabilizer.process({
      classIndex: top.classIndex,
      className: top.className,
      confidence: top.confidence,
      timestampMs: nowMs,
    });
    if (state.committedSign && !commits.includes(state.committedSign)) commits.push(state.committedSign);
  }

  return { readyAfterMs, inferenceCount, commits, topClass, topConfidence, finalTop, finalConfidence };
}
