import { FEATURE_DIMENSION, OFFSETS, type GroupName, type GroupPresence } from './contracts';
import type { CanonicalFrame } from './contracts';

/**
 * Fixed-cadence temporal sampler for the SPOTER V2 input contract.
 *
 * The contract is a 60-frame window whose frames are 125 ms apart (the training
 * extractor samples at 10 fps: docs/ai-ml/LANDMARK_PIPELINE_SPEC.md). The browser
 * cannot always *observe* the signer that often: three MediaPipe landmarkers run
 * per frame and cost ~150-195 ms together (measured, web/bench/recognition-bench.html),
 * and an ONNX inference costs another ~160 ms. The previous loop pushed one buffer
 * frame per completed detection, so the window was written at the *detection* rate
 * (~3-5 fps) instead of 125 ms. That had two consequences:
 *
 *   1. The 60-frame window took 12-20 s of wall-clock time to fill, so the first
 *      recognition of a session arrived far later than the sign that triggered it.
 *   2. Consecutive buffered frames sat ~200-310 ms apart, so live motion appeared
 *      roughly 2x slower than the 10 fps motion the model was trained on.
 *
 * This sampler decouples the two clocks. Detections remain real observations at
 * whatever rate the device can produce them; the buffer is written on a fixed
 * 125 ms grid, and a grid point that falls between two observations is the linear
 * blend of exactly those two real observations.
 *
 * What it deliberately does NOT do:
 *   - It never invents a landmark group that is missing in either observation.
 *     A group absent in one of the two bracketing observations is held from the
 *     newer one (byte-identical to what the previous loop pushed), never blended
 *     towards the zero fill that a missing group leaves behind.
 *   - It never changes the feature layout, the 366-D dimension, the V2 scalars or
 *     the sequence length. Every group in every emitted sample is either a real
 *     observation or a blend of two real observations.
 *   - It never stretches or drops frames to catch up after a stall: a page that
 *     was frozen long enough for the grid to fall behind restarts the grid at the
 *     current time instead of emitting a burst of stale motion.
 */

/** Training/contract frame interval: 60 frames x 125 ms = 7.5 s window. */
export const SAMPLE_INTERVAL_MS = 125;

/** A real detection, already assembled and V2-normalized. */
export type Observation = {
  normalized: Float32Array;
  presence: GroupPresence;
  invalidGroups: GroupName[];
  /** Timestamp of the frame this observation came from. */
  timestampMs: number;
};

export type SampledFrame = {
  normalized: Float32Array;
  presence: GroupPresence;
  invalidGroups: GroupName[];
  /** Grid timestamp this sample represents (not the observation timestamp). */
  timestampMs: number;
  /** True when the sample sits strictly between two real observations. */
  interpolated: boolean;
};

export type SamplerStats = {
  observed: number;
  sampled: number;
  interpolated: number;
  /** Times the grid was restarted because the page had stalled past catch-up. */
  stallRestarts: number;
};

const HAND_RANGES: { group: GroupName; start: number; end: number }[] = [
  { group: 'leftHand', start: OFFSETS.leftHand, end: OFFSETS.rightHand },
  { group: 'rightHand', start: OFFSETS.rightHand, end: OFFSETS.pose },
];

/** Pose rows are interleaved [x, y, z, visibility, presence] (docs/architecture/WEB_LANDMARK_PIPELINE.md). */
const POSE_STRIDE = 5;
const POSE_LANDMARKS = (OFFSETS.face - OFFSETS.pose) / POSE_STRIDE;

export class TemporalSampler {
  readonly intervalMs: number;
  private readonly maxCatchUpSamples: number;
  private older?: Observation;
  private newer?: Observation;
  private nextSampleMs = 0;
  private stats: SamplerStats = { observed: 0, sampled: 0, interpolated: 0, stallRestarts: 0 };

  constructor(intervalMs: number = SAMPLE_INTERVAL_MS, maxCatchUpSamples = 8) {
    if (intervalMs <= 0) throw new Error('Sample interval must be positive');
    this.intervalMs = intervalMs;
    this.maxCatchUpSamples = maxCatchUpSamples;
  }

  /** Records a real detection. The grid starts at the first observation. */
  observe(observation: Observation): void {
    if (this.newer) this.older = this.newer;
    this.newer = observation;
    if (!this.older && this.nextSampleMs === 0) {
      this.nextSampleMs = observation.timestampMs;
    }
    this.stats.observed += 1;
  }

  /** Emits every grid sample due at or before `nowMs`. */
  sampleUntil(nowMs: number): SampledFrame[] {
    if (!this.newer) return [];

    const stallLimitMs = this.intervalMs * this.maxCatchUpSamples;
    if (nowMs - this.nextSampleMs > stallLimitMs) {
      // The page was frozen (background tab, GC pause, model download): drop the
      // missed grid points rather than emit a burst of stale interpolations that
      // would fill the window with motion the signer has already finished.
      this.stats.stallRestarts += 1;
      this.nextSampleMs = nowMs;
    }

    const samples: SampledFrame[] = [];
    while (this.nextSampleMs <= nowMs && samples.length < this.maxCatchUpSamples) {
      samples.push(this.sampleAt(this.nextSampleMs));
      this.nextSampleMs += this.intervalMs;
    }
    return samples;
  }

  private sampleAt(timestampMs: number): SampledFrame {
    const newer = this.newer!;
    const older = this.older;
    const sample = !older || timestampMs <= older.timestampMs
      ? hold(newer, timestampMs)
      : timestampMs >= newer.timestampMs
        ? hold(newer, timestampMs)
        : blend(older, newer, timestampMs);
    this.stats.sampled += 1;
    if (sample.interpolated) this.stats.interpolated += 1;
    return sample;
  }

  getStats(): SamplerStats {
    return { ...this.stats };
  }

  /** Drops all observations and restarts the grid at the next observation. */
  reset(): void {
    this.older = undefined;
    this.newer = undefined;
    this.nextSampleMs = 0;
  }
}

/** The newest real observation, presented at a grid timestamp. */
function hold(observation: Observation, timestampMs: number): SampledFrame {
  return {
    normalized: observation.normalized,
    presence: { ...observation.presence },
    invalidGroups: [...observation.invalidGroups],
    timestampMs,
    interpolated: false,
  };
}

/**
 * Linear blend of two real observations. A group is blended only when both
 * observations carry it; otherwise the newer observation's values are held.
 */
function blend(older: Observation, newer: Observation, timestampMs: number): SampledFrame {
  const span = newer.timestampMs - older.timestampMs;
  const weight = span > 0 ? (timestampMs - older.timestampMs) / span : 1;
  const output = new Float32Array(FEATURE_DIMENSION);
  const presence: GroupPresence = { leftHand: false, rightHand: false, pose: false, face: false };

  for (const { group, start, end } of HAND_RANGES) {
    const both = older.presence[group] && newer.presence[group];
    presence[group] = newer.presence[group];
    for (let index = start; index < end; index += 1) {
      output[index] = both
        ? older.normalized[index] + (newer.normalized[index] - older.normalized[index]) * weight
        : newer.normalized[index];
    }
  }

  const poseBoth = older.presence.pose && newer.presence.pose;
  presence.pose = newer.presence.pose;
  for (let landmark = 0; landmark < POSE_LANDMARKS; landmark += 1) {
    const row = OFFSETS.pose + landmark * POSE_STRIDE;
    for (let axis = 0; axis < 3; axis += 1) {
      output[row + axis] = poseBoth
        ? older.normalized[row + axis] + (newer.normalized[row + axis] - older.normalized[row + axis]) * weight
        : newer.normalized[row + axis];
    }
    // Visibility/presence are detector confidences, not geometry: never blended.
    output[row + 3] = newer.normalized[row + 3];
    output[row + 4] = newer.normalized[row + 4];
  }

  const faceBoth = older.presence.face && newer.presence.face;
  presence.face = newer.presence.face;
  for (let index = OFFSETS.face; index < FEATURE_DIMENSION; index += 1) {
    output[index] = faceBoth
      ? older.normalized[index] + (newer.normalized[index] - older.normalized[index]) * weight
      : newer.normalized[index];
  }

  return {
    normalized: output,
    presence,
    // A held group is a real observation, not a malformed one, so it is not
    // reported as invalid; `presence` already records which groups are absent.
    invalidGroups: [...newer.invalidGroups],
    timestampMs,
    interpolated: true,
  };
}

/** Convenience wrapper for the engine: an assembled + normalized frame. */
export function observationFrom(
  frame: CanonicalFrame,
  normalized: Float32Array,
  timestampMs: number,
): Observation {
  return {
    normalized,
    presence: frame.presence,
    invalidGroups: frame.invalidGroups,
    timestampMs,
  };
}
