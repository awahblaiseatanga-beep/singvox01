import { describe, expect, it } from 'vitest';
import { FEATURE_DIMENSION, OFFSETS, type GroupPresence } from './contracts';
import { SAMPLE_INTERVAL_MS, TemporalSampler, type Observation } from './temporalSampler';

function obs(
  timestampMs: number,
  fills: Partial<Record<'leftHand' | 'rightHand' | 'pose' | 'face', number>>,
  presence?: Partial<GroupPresence>,
): Observation {
  const normalized = new Float32Array(FEATURE_DIMENSION);
  const groups: GroupPresence = { leftHand: false, rightHand: false, pose: false, face: false };
  for (const [group, value] of Object.entries(fills) as [keyof GroupPresence, number][]) {
    groups[group] = true;
    const [start, end] = ranges[group];
    for (let index = start; index < end; index += 1) normalized[index] = value;
  }
  if (presence) Object.assign(groups, presence);
  return { normalized, presence: groups, invalidGroups: [], timestampMs };
}

const ranges: Record<keyof GroupPresence, [number, number]> = {
  leftHand: [OFFSETS.leftHand, OFFSETS.rightHand],
  rightHand: [OFFSETS.rightHand, OFFSETS.pose],
  pose: [OFFSETS.pose, OFFSETS.face],
  face: [OFFSETS.face, FEATURE_DIMENSION],
};

describe('TemporalSampler', () => {
  it('starts the grid on the first observation and emits on a fixed 125 ms cadence', () => {
    const sampler = new TemporalSampler();
    sampler.observe(obs(1000, { leftHand: 0.2, pose: 0.1, face: 0.3 }));
    const samples = sampler.sampleUntil(1250);

    expect(samples.map((sample) => sample.timestampMs)).toEqual([1000, 1125, 1250]);
    expect(SAMPLE_INTERVAL_MS).toBe(125);
    expect(samples[0].interpolated).toBe(false);
    // The grid is uniform, which is what the 366-D sequence contract assumes.
    for (let index = 1; index < samples.length; index += 1) {
      expect(samples[index].timestampMs - samples[index - 1].timestampMs).toBe(125);
    }
  });

  it('emits nothing before the first observation arrives', () => {
    const sampler = new TemporalSampler();
    expect(sampler.sampleUntil(5000)).toEqual([]);
  });

  it('blends a group present in both bracketing observations', () => {
    const sampler = new TemporalSampler();
    sampler.observe(obs(1000, { leftHand: 0.2, rightHand: 0.6, pose: 0.4, face: 0.8 }));
    sampler.observe(obs(1250, { leftHand: 0.4, rightHand: 0.8, pose: 0.6, face: 1.0 }));
    const samples = sampler.sampleUntil(1250);
    const middle = samples[1];

    expect(middle.interpolated).toBe(true);
    for (const [group, expected] of [['leftHand', 0.3], ['rightHand', 0.7], ['pose', 0.5], ['face', 0.9]] as const) {
      const [start] = ranges[group];
      expect(middle.normalized[start]).toBeCloseTo(expected, 5);
    }
    expect(sampler.getStats()).toMatchObject({ observed: 2, sampled: 3, interpolated: 1 });
  });

  it('never half-fills a hand that is missing in one of the two observations', () => {
    const sampler = new TemporalSampler();
    // Older frame has no left hand detected: its left-hand block is the zero fill.
    sampler.observe(obs(1000, { rightHand: 0.5, pose: 0.4 }, { leftHand: false }));
    sampler.observe(obs(1250, { leftHand: 0.9, rightHand: 0.5, pose: 0.4 }));
    const middle = sampler.sampleUntil(1250)[1];

    // Held from the newer observation, NOT blended towards zero.
    expect(middle.normalized[OFFSETS.leftHand]).toBeCloseTo(0.9, 5);
    expect(middle.presence.leftHand).toBe(true);
  });

  it('holds a group the newer observation lost instead of blending it away', () => {
    const sampler = new TemporalSampler();
    sampler.observe(obs(1000, { leftHand: 0.9, pose: 0.4, face: 0.7 }));
    sampler.observe(obs(1250, { pose: 0.4, face: 0.7 }, { leftHand: false }));
    const middle = sampler.sampleUntil(1250)[1];

    // The zero fill of the missing group is propagated, never a phantom partial hand.
    expect(middle.normalized[OFFSETS.leftHand]).toBe(0);
    expect(middle.presence.leftHand).toBe(false);
  });

  it('does not interpolate pose visibility/presence confidences', () => {
    const sampler = new TemporalSampler();
    const older = obs(1000, { pose: 0.1 });
    const newer = obs(1250, { pose: 0.3 });
    const row = OFFSETS.pose;
    older.normalized[row + 3] = 0.5;
    older.normalized[row + 4] = 0.5;
    newer.normalized[row + 3] = 0.9;
    newer.normalized[row + 4] = 0.7;
    sampler.observe(older);
    sampler.observe(newer);
    const middle = sampler.sampleUntil(1250)[1];

    expect(middle.normalized[row]).toBeCloseTo(0.2, 5);
    expect(middle.normalized[row + 3]).toBeCloseTo(0.9, 5);
    expect(middle.normalized[row + 4]).toBeCloseTo(0.7, 5);
  });

  it('restarts the grid after a stall instead of emitting a burst of stale frames', () => {
    const sampler = new TemporalSampler();
    sampler.observe(obs(1000, { leftHand: 0.2, pose: 0.1, face: 0.3 }));
    const samples = sampler.sampleUntil(5000);

    expect(samples).toHaveLength(1);
    expect(samples[0].timestampMs).toBe(5000);
    expect(sampler.getStats().stallRestarts).toBe(1);
  });

  it('reset() drops the observations so the grid restarts on the next observation', () => {
    const sampler = new TemporalSampler();
    sampler.observe(obs(1000, { leftHand: 0.2, pose: 0.1, face: 0.3 }));
    sampler.reset();

    expect(sampler.sampleUntil(2000)).toEqual([]);
    sampler.observe(obs(3000, { leftHand: 0.2, pose: 0.1, face: 0.3 }));
    expect(sampler.sampleUntil(3000)[0].timestampMs).toBe(3000);
  });

  it('keeps every sample at the frozen 366-dimension contract', () => {
    const sampler = new TemporalSampler();
    sampler.observe(obs(1000, { leftHand: 0.2, pose: 0.1, face: 0.3 }));
    sampler.observe(obs(1200, { leftHand: 0.4, pose: 0.3, face: 0.5 }));
    for (const sample of sampler.sampleUntil(1200)) {
      expect(sample.normalized.length).toBe(FEATURE_DIMENSION);
      expect(sample.normalized.every((value) => Number.isFinite(value))).toBe(true);
    }
  });
});
