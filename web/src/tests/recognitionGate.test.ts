import { describe, it, expect } from 'vitest';
import {
  evaluateRecognitionGate,
  MIN_HAND_COVERAGE_PERCENT,
  MIN_POSE_COVERAGE_PERCENT,
} from '../lib/recognitionGate';
import { SequenceBuffer, type FrameMetadata } from '../lib/sequenceBuffer';
import { FEATURE_DIMENSION } from '../lib/contracts';

const meta = (leftHand: boolean, rightHand: boolean, pose: boolean): FrameMetadata => ({
  presence: { leftHand, rightHand, pose, face: pose },
  nonFiniteCount: 0,
  timestampMs: 0,
});

describe('recognition input-validity gate', () => {
  it('rejects the all-zero window that provokes the SICK attractor', () => {
    // Measured: an all-zero 60-frame window returns SICK at 0.856 confidence.
    const decision = evaluateRecognitionGate({ anyHandPercent: 0, posePercent: 0, frames: 60 });
    expect(decision.allowed).toBe(false);
    expect(decision.reason).toBe('no-hands');
  });

  it('rejects a window whose hands are missing but whose pose is present', () => {
    // Measured: real pose/face with hand blocks zeroed returns YESTERDAY 0.692,
    // so pose coverage alone must not satisfy the gate.
    const decision = evaluateRecognitionGate({ anyHandPercent: 0, posePercent: 100, frames: 60 });
    expect(decision.allowed).toBe(false);
    expect(decision.reason).toBe('no-hands');
  });

  it('rejects a window without shoulders because normalization needs them', () => {
    const decision = evaluateRecognitionGate({ anyHandPercent: 100, posePercent: 0, frames: 60 });
    expect(decision.allowed).toBe(false);
    expect(decision.reason).toBe('no-pose');
  });

  it('allows a window that carries landmarks across the measured valid regime', () => {
    // Measured: a real clip stayed correctly recognised with roughly a third of
    // the window carrying landmarks, and collapsed to DAY below a fifth.
    const allowed = evaluateRecognitionGate({ anyHandPercent: 30, posePercent: 100, frames: 60 });
    expect(allowed.allowed).toBe(true);
    expect(allowed.reason).toBe('ok');
    expect(MIN_HAND_COVERAGE_PERCENT).toBeLessThan(30);
    expect(MIN_POSE_COVERAGE_PERCENT).toBeLessThanOrEqual(100);
  });

  it('reports an empty buffer separately from missing hands', () => {
    const decision = evaluateRecognitionGate({ anyHandPercent: 0, posePercent: 0, frames: 0 });
    expect(decision.reason).toBe('buffer-empty');
  });

  it('derives coverage from the sequence buffer the live loop uses', () => {
    const buffer = new SequenceBuffer(60);
    const frame = new Float32Array(FEATURE_DIMENSION);
    for (let i = 0; i < 60; i += 1) buffer.push(frame, meta(i < 3, false, true));
    const quality = buffer.getSequenceQuality();
    expect(quality).not.toBeNull();
    expect(quality!.anyHandPercent).toBe(5);
    expect(quality!.posePercent).toBe(100);
    // 3 of 60 frames carry a hand: below the gate, exactly the state the live
    // loop must refuse instead of committing an attractor class.
    expect(evaluateRecognitionGate({
      anyHandPercent: quality!.anyHandPercent,
      posePercent: quality!.posePercent,
      frames: buffer.length,
    }).allowed).toBe(false);

    const buffer2 = new SequenceBuffer(60);
    for (let i = 0; i < 60; i += 1) buffer2.push(frame, meta(i < 20, false, true));
    const quality2 = buffer2.getSequenceQuality()!;
    expect(quality2.anyHandPercent).toBe(33);
    expect(evaluateRecognitionGate({
      anyHandPercent: quality2.anyHandPercent,
      posePercent: quality2.posePercent,
      frames: buffer2.length,
    }).allowed).toBe(true);
  });
});
