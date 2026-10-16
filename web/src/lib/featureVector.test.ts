import { describe, expect, it } from 'vitest';
import { FEATURE_DIMENSION, OFFSETS, V2_SCALARS, type Point3, type PosePoint } from './contracts';
import { assembleCanonicalFrame, canonicalSlotForMediaPipeLabel, countNonFinite } from './featureVector';
import { applyV2Normalization } from './normalize';

const point = (seed: number): Point3 => ({ x: seed, y: seed + 0.1, z: seed + 0.2 });
const posePoint = (seed: number): PosePoint => ({ ...point(seed), visibility: seed + 0.3, presence: seed + 0.4 });
const pose = Array.from({ length: 33 }, (_, index) => posePoint(index + 1));
const left = Array.from({ length: 21 }, (_, index) => point(index + 1));
const right = Array.from({ length: 21 }, (_, index) => point(index + 101));
const face = Array.from({ length: 30 }, (_, index) => point(index + 201));

describe('frozen SignVox V2 366-D assembly', () => {
  it('creates the exact feature length and canonical hand slots', () => {
    const frame = assembleCanonicalFrame({ hands: [{ label: 'Right', landmarks: left }, { label: 'Left', landmarks: right }], pose, face });
    expect(frame.raw).toHaveLength(FEATURE_DIMENSION);
    expect(Array.from(frame.raw.slice(0, 3))).toEqual([1, 1.100000023841858, 1.2000000476837158]);
    expect(frame.raw[63]).toBe(101);
    expect(frame.presence).toEqual({ leftHand: true, rightHand: true, pose: true, face: true });
    expect(canonicalSlotForMediaPipeLabel('Right')).toBe('leftHand');
    expect(canonicalSlotForMediaPipeLabel('Left')).toBe('rightHand');
  });

  it('keeps pose interleaved at every frozen V2 boundary', () => {
    const frame = assembleCanonicalFrame({ hands: [], pose, face: undefined });
    expect(Array.from(frame.raw.slice(126, 131))).toEqual([1, 1.100000023841858, 1.2000000476837158, 1.2999999523162842, 1.399999976158142]);
    expect(Array.from(frame.raw.slice(131, 136))).toEqual([2, 2.0999999046325684, 2.200000047683716, 2.299999952316284, 2.4000000953674316]);
    expect(Array.from(frame.raw.slice(286, 291))).toEqual([33, 33.099998474121094, 33.20000076293945, 33.29999923706055, 33.400001525878906]);
    expect(frame.raw[OFFSETS.pose + 3]).toBeCloseTo(1.3);
    expect(frame.raw[OFFSETS.pose + 4]).toBeCloseTo(1.4);
  });

  it('zero-fills missing groups and rejects non-finite groups', () => {
    const invalidPose = [...pose]; invalidPose[0] = { x: Number.NaN, y: Infinity, z: -Infinity, visibility: 1, presence: 1 };
    const frame = assembleCanonicalFrame({ hands: [], pose: invalidPose, face: undefined });
    // This implicitly tests missing LH (0:63), missing RH (63:126), and missing face (291:366) zero-fill
    expect(frame.presence).toEqual({ leftHand: false, rightHand: false, pose: false, face: false });
    expect(frame.invalidGroups).toEqual(['pose']);
    expect(Array.from(frame.raw.slice(0, 63)).every(v => v === 0)).toBe(true); // LH zero-fill
    expect(Array.from(frame.raw.slice(63, 126)).every(v => v === 0)).toBe(true); // RH zero-fill
    expect(Array.from(frame.raw.slice(291, 366)).every(v => v === 0)).toBe(true); // Face zero-fill
    expect([...frame.raw].every((value) => value === 0)).toBe(true);
    // Tests that NaN and Infinity were successfully detected and zeroed out
    expect(countNonFinite(frame.raw)).toEqual({ nan: 0, inf: 0 });
  });

  it('scales only the XYZ members of every interleaved pose row', () => {
    const raw = new Float32Array(FEATURE_DIMENSION);
    raw[126] = 18; raw[127] = 36; raw[128] = 54; raw[129] = 0.75; raw[130] = 0.25;
    // Missing shoulder landmarks retain the canonical no-op shoulder-centering path.
    const normalized = applyV2Normalization(raw);
    expect(normalized[126]).toBeCloseTo(18 / V2_SCALARS.poseXyz);
    expect(normalized[127]).toBeCloseTo(36 / V2_SCALARS.poseXyz);
    expect(normalized[128]).toBeCloseTo(54 / V2_SCALARS.poseXyz);
    expect(normalized[129]).toBeCloseTo(0.75);
    expect(normalized[130]).toBeCloseTo(0.25);
    expect(normalized).toHaveLength(366);
  });
});
