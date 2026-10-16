import { describe, it, expect, beforeAll } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as THREE from 'three';
import { AvatarController } from '../../../avatar/controller/AvatarController';
import { CanonicalBones } from '../../../avatar/controller/boneMap';
import { SpoterInferenceSession } from '../lib/inference';
import { ASL_VOCAB, PILOT_VOCAB } from '../lib/vocab';
import { SequenceBuffer } from '../lib/sequenceBuffer';
import { BASELINE_STABILIZER_CONFIG, TemporalStabilizer } from '../lib/temporalStabilizer';
import { TemporalSampler, SAMPLE_INTERVAL_MS, observationFrom } from '../lib/temporalSampler';
import { emptyPresence, type CanonicalFrame, type GroupPresence } from '../lib/contracts';

/**
 * Structural tests against the tracked synthetic fixtures in
 * `web/src/tests/fixtures/` (regenerate with `node generate_fixtures.mjs`).
 *
 * These fixtures carry NO trained weights and NO recorded signer data. What
 * they prove is the plumbing on every clone:
 *   - the production AvatarController can load a rig of canonical bone names,
 *     resolve a sign label to its clip, refuse an unknown label, and drive the
 *     real IK/hand controllers without producing non-finite transforms;
 *   - the production SpoterInferenceSession can open a graph, run a 60x366
 *     window through it, and refuse a class map that disagrees with the graph's
 *     logit count.
 *
 * They deliberately prove NOTHING about recognition accuracy: the ONNX graphs
 * are hand-encoded Reshape+Slice graphs, not trained SPOTER models. Accuracy,
 * thresholds and commit behaviour stay covered exclusively by the recorded-clip
 * tests, which skip explicitly when their local-only assets are absent.
 */

const FIXTURES = path.resolve(__dirname, 'fixtures');
const SYNTH_GLB = path.join(FIXTURES, 'signvox_synth_rig.glb');
const SYNTH_ONNX_79 = path.join(FIXTURES, 'synth_79.onnx');
const SYNTH_ONNX_3 = path.join(FIXTURES, 'synth_3.onnx');

/** GLB JSON chunk parse, copied from goodCandidate.test.ts. */
function readGltfJson(p: string): any {
  const b = fs.readFileSync(p);
  const jsonLen = b.readUInt32LE(12);
  return JSON.parse(b.subarray(20, 20 + jsonLen).toString('utf8'));
}

describe('synthetic rig fixture (structural avatar invariants)', () => {
  it('fixture exists and carries an ASL_GOOD rotation clip on the right arm chain', () => {
    expect(fs.existsSync(SYNTH_GLB)).toBe(true);
    const js = readGltfJson(SYNTH_GLB);
    const names = (js.animations as any[]).map((a) => a.name);
    expect(names).toContain('ASL_GOOD');
    const good = (js.animations as any[]).find((a) => a.name === 'ASL_GOOD');
    const nodes = (js.nodes as any[]).map((n) => n.name);
    const rotTargets = new Set(
      good.channels
        .filter((c: any) => c.target.path === 'rotation')
        .map((c: any) => nodes[c.target.node])
    );
    for (const bone of ['mixamorig4:RightArm', 'mixamorig4:RightForeArm', 'mixamorig4:RightHand']) {
      expect(rotTargets.has(bone)).toBe(true);
    }
  });

  describe('through the real AvatarController.loadGLB', () => {
    let controller: AvatarController;

    beforeAll(async () => {
      // Same file:// fetch shim reproduce_trace.test.ts uses, so loadGLB runs
      // the real GLTFLoader path under Node.
      // @ts-ignore - test-only fetch shim
      global.fetch = async (req: any) => {
        const urlStr = typeof req === 'string' ? req : (req.url || req.toString());
        const rawPath = urlStr.replace('file:///', '');
        const buffer = fs.readFileSync(decodeURI(rawPath));
        const arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
        return { arrayBuffer: async () => arrayBuffer, ok: true, status: 200 } as any;
      };
      // @ts-ignore - ORT expects a self global under Node
      global.self = global;

      controller = new AvatarController();
      await controller.loadGLB(`file:///${SYNTH_GLB.replace(/\\/g, '/')}`);
    });

    it('maps every canonical bone and validates as signing-capable', () => {
      expect(controller.boneMapCache.size).toBe(Object.keys(CanonicalBones).length);
      expect(controller.capabilities.isSigningValid).toBe(true);
      expect(controller.capabilities.isStructuralValid).toBe(true);
    });

    it("playSignByLabel('GOOD') resolves to clip:ASL_GOOD, and an unknown label falls back to neutral", () => {
      controller.playSignByLabel('GOOD');
      expect(controller.animationMode).toBe('clip:ASL_GOOD');
      controller.playSignByLabel('NOT_A_SIGN');
      expect(controller.animationMode).toBe('clip:ASL_NEUTRAL');
    });

    it('drives the real hand + IK controllers over 5 frames without non-finite transforms', () => {
      // Same target reproduce_trace.test.ts uses to force the torso-penetration
      // state; the assertions it lacks are added here.
      const target = new THREE.Vector3(0.08, 1.43, 0.03);
      const ik = controller.armIK.left!;
      for (let frame = 0; frame < 5; frame++) {
        controller.hands.left!.update();
        ik.setTarget(target, undefined, 'indexFingertip');
        ik.update();
        const proxy = ik as any;
        for (const bone of [proxy.upperArm, proxy.foreArm, proxy.hand]) {
          const w = bone.getWorldPosition(new THREE.Vector3());
          expect([w.x, w.y, w.z].every(Number.isFinite)).toBe(true);
        }
        const q = proxy.upperArm.quaternion;
        expect([q.x, q.y, q.z, q.w].every(Number.isFinite)).toBe(true);
      }
    });
  });
});

// File-scope sessions: both the plumbing block below and the cadence block at
// the end of this file drive the synthetic 79-class graph.
let session79: SpoterInferenceSession;
let session3: SpoterInferenceSession;

beforeAll(async () => {
  // inference.ts always declares an externalData entry at `${modelUrl}.data`,
  // so ORT opens the (empty) sidecar next to each fixture unconditionally.
  session79 = await SpoterInferenceSession.create(SYNTH_ONNX_79.replace(/\\/g, '/'));
  session3 = await SpoterInferenceSession.create(SYNTH_ONNX_3.replace(/\\/g, '/'));
});

describe('synthetic ONNX fixtures (inference plumbing, NOT accuracy)', () => {
  it('runs a 60x366 window and returns one logit per vocab entry', async () => {
    const window = new Float32Array(60 * 366);
    const r79 = await session79.predict(window, ASL_VOCAB);
    expect(r79.logits.length).toBe(79);
    expect(r79.topK[0].className).not.toBe('UNKNOWN');
    const r3 = await session3.predict(window, PILOT_VOCAB);
    expect(r3.logits.length).toBe(3);
  });

  it('refuses a class map that disagrees with the graph logit count', async () => {
    const window = new Float32Array(60 * 366);
    await expect(session79.predict(window, PILOT_VOCAB)).rejects.toThrow(/logits/);
    await expect(session3.predict(window, ASL_VOCAB)).rejects.toThrow(/logits/);
  });

  it('refuses a buffer that is not exactly 60x366 floats', async () => {
    await expect(session79.predict(new Float32Array(10), ASL_VOCAB)).rejects.toThrow(/60 \* 366/);
  });
});

/**
 * Cadence half of temporal_sampling_parity.test.ts, on a deterministic
 * synthetic timeline through the real SequenceBuffer / TemporalStabilizer /
 * TemporalSampler and the synthetic 79-class graph.
 *
 * Deliberately asserts NO recognition evidence: no commit, no top-1 label. The
 * recorded-clip test keeps those claims; this block only proves that the fixed
 * 125 ms grid completes a window sooner than the 150 ms observation cadence —
 * a property of the sampler, not of the model or the signer.
 */
describe('synthetic cadence replay (timing invariants only, NOT recognition)', () => {
  const FEATURE_DIM = 366;
  const CLIP_FPS = 10;
  const OBSERVATION_INTERVAL_MS = 150;
  const TIMELINE_FRAMES = 120;
  const SUB_STEP_MS = 25;

  it('grid sampling completes the window earlier than the observation cadence', async () => {
    const timeline: Float32Array[] = [];
    for (let i = 0; i < TIMELINE_FRAMES; i += 1) {
      const frame = new Float32Array(FEATURE_DIM);
      for (let j = 0; j < FEATURE_DIM; j += 1) frame[j] = Math.sin((i * FEATURE_DIM + j) * 0.01);
      timeline.push(frame);
    }
    const timelineMs = (timeline.length / CLIP_FPS) * 1000;
    const frameAt = (ms: number) =>
      timeline[Math.min(timeline.length - 1, Math.max(0, Math.round((ms / 1000) * CLIP_FPS)))];

    const allPresent = emptyPresence();
    allPresent.leftHand = true;
    allPresent.rightHand = true;
    allPresent.pose = true;
    allPresent.face = true;

    const replay = async (
      produce: (nowMs: number) => { vector: Float32Array; presence: GroupPresence; timestampMs: number }[],
    ) => {
      const buffer = new SequenceBuffer();
      let readyAfterMs = 0;
      let inferenceCount = 0;
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
        const result = await session79.predict(flat, ASL_VOCAB);
        expect(result.logits.length).toBe(79);
        inferenceCount += 1;
      }
      return { readyAfterMs, inferenceCount };
    };

    const observations = await replay((nowMs) =>
      nowMs % OBSERVATION_INTERVAL_MS !== 0
        ? []
        : [{ vector: frameAt(nowMs), presence: allPresent, timestampMs: nowMs }],
    );

    let gridHoldClock = -SAMPLE_INTERVAL_MS;
    const gridHold = await replay((nowMs) => {
      const due: number[] = [];
      while (gridHoldClock + SAMPLE_INTERVAL_MS <= nowMs) {
        gridHoldClock += SAMPLE_INTERVAL_MS;
        due.push(gridHoldClock);
      }
      return due.map((timestampMs) => ({ vector: frameAt(nowMs), presence: allPresent, timestampMs }));
    });

    const sampler = new TemporalSampler();
    const gridInterp = await replay((nowMs) => {
      if (nowMs % OBSERVATION_INTERVAL_MS === 0) {
        sampler.observe(
          observationFrom(
            {
              raw: new Float32Array(FEATURE_DIM),
              presence: allPresent,
              invalidGroups: [],
              handAssignments: [],
            } as unknown as CanonicalFrame,
            frameAt(nowMs),
            nowMs,
          ),
        );
      }
      return sampler.sampleUntil(nowMs).map((sample) => ({
        vector: sample.normalized,
        presence: sample.presence as GroupPresence,
        timestampMs: sample.timestampMs,
      }));
    });

    expect(gridInterp.readyAfterMs).toBeGreaterThan(0);
    expect(gridInterp.readyAfterMs).toBeLessThan(observations.readyAfterMs);
    expect(gridHold.readyAfterMs).toBe(gridInterp.readyAfterMs);
    expect(gridInterp.inferenceCount).toBeGreaterThan(0);
  });
});
