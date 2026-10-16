import { describe, it, expect } from 'vitest';
import { SequenceBuffer } from '../lib/sequenceBuffer';
import {
  DiagnosticSession,
  runRepeatabilityTest,
  type RepeatabilityReport,
} from '../lib/diagnostics';
import { FEATURE_DIMENSION } from '../lib/contracts';
import type { SpoterInferenceSession } from '../lib/inference';

describe('Phase 1.1 Consistency Diagnosis Test Suite', () => {
  describe('1. SequenceBuffer FrameMetadata & FIFO Alignment', () => {
    it('maintains strict 1:1 alignment between feature frames and detector metadata across FIFO evictions', () => {
      const buffer = new SequenceBuffer(5);

      for (let i = 0; i < 5; i++) {
        const frame = new Float32Array(FEATURE_DIMENSION).fill(i);
        buffer.push(frame, {
          presence: { leftHand: i % 2 === 0, rightHand: i % 2 !== 0, pose: true, face: false },
          nonFiniteCount: i === 3 ? 2 : 0,
          timestampMs: 1000 + i * 33.3,
        });
      }

      expect(buffer.length).toBe(5);
      expect(buffer.isReady).toBe(true);

      let metadata = buffer.getMetadata();
      expect(metadata.length).toBe(5);
      expect(metadata[0].timestampMs).toBeCloseTo(1000);
      expect(metadata[0].presence.leftHand).toBe(true);
      expect(metadata[3].nonFiniteCount).toBe(2);

      // Push 2 more frames (indices 5 and 6) -> evicts indices 0 and 1
      buffer.push(new Float32Array(FEATURE_DIMENSION).fill(5), {
        presence: { leftHand: false, rightHand: true, pose: true, face: true },
        nonFiniteCount: 0,
        timestampMs: 1000 + 5 * 33.3,
      });

      buffer.push(new Float32Array(FEATURE_DIMENSION).fill(6), {
        presence: { leftHand: true, rightHand: false, pose: true, face: true },
        nonFiniteCount: 0,
        timestampMs: 1000 + 6 * 33.3,
      });

      expect(buffer.length).toBe(5);
      const flat = buffer.getFlattenedBuffer()!;
      expect(flat[0]).toBe(2); // Oldest frame is now frame index 2
      expect(flat[4 * FEATURE_DIMENSION]).toBe(6); // Newest frame is frame index 6

      metadata = buffer.getMetadata();
      expect(metadata[0].timestampMs).toBeCloseTo(1000 + 2 * 33.3);
      expect(metadata[0].presence.leftHand).toBe(true); // Index 2 had leftHand: true
      expect(metadata[4].timestampMs).toBeCloseTo(1000 + 6 * 33.3);
      expect(metadata[4].presence.leftHand).toBe(true); // Index 6 had leftHand: true
    });

    it('computes accurate SequenceQuality metrics over buffered frames', () => {
      const capacity = 10;
      const buffer = new SequenceBuffer(capacity);

      for (let i = 0; i < capacity; i++) {
        const frame = new Float32Array(FEATURE_DIMENSION);
        // Add artificial hand motion in frames 3..7
        if (i >= 3 && i <= 7) {
          frame[0] = (i - 3) * 0.1;
        }
        buffer.push(frame, {
          presence: {
            leftHand: i < 5, // 50%
            rightHand: i >= 5, // 50%
            pose: true, // 100%
            face: false, // 0%
          },
          nonFiniteCount: i === 0 ? 1 : 0,
          timestampMs: 1000 + i * 33.0,
        });
      }

      const quality = buffer.getSequenceQuality();
      expect(quality).not.toBeNull();
      expect(quality!.lhPercent).toBe(50);
      expect(quality!.rhPercent).toBe(50);
      expect(quality!.posePercent).toBe(100);
      expect(quality!.facePercent).toBe(0);
      expect(quality!.framesWithNonFinite).toBe(1);
      expect(quality!.totalNonFiniteValues).toBe(1);
      expect(quality!.durationMs).toBe(297);
      expect(quality!.avgIntervalMs).toBeCloseTo(33.0, 1);
      expect(quality!.intervalStdDevMs).toBeCloseTo(0.0, 1);
      expect(quality!.heuristicMovementCompleteness.note).toBeDefined();
    });
  });

  describe('2. DiagnosticSession & Trial Recording', () => {
    it('records up to 5 trials with complete diagnostics and exports JSON', () => {
      const session = new DiagnosticSession();
      expect(session.count).toBe(0);
      expect(session.isFull).toBe(false);

      const dummyBuffer = new Float32Array(60 * FEATURE_DIMENSION).fill(0.05);
      const dummyQuality = {
        lhPercent: 80,
        rhPercent: 90,
        anyHandPercent: 95,
        posePercent: 100,
        facePercent: 100,
        framesWithNonFinite: 0,
        totalNonFiniteValues: 0,
        durationMs: 1980,
        avgIntervalMs: 33.3,
        intervalStdDevMs: 1.2,
        heuristicMovementCompleteness: {
          hasMovement: true,
          initialEnergy: 0.005,
          peakEnergy: 0.08,
          trailingEnergy: 0.004,
          isClippingSuspected: false,
          note: 'Movement centered',
        },
      };

      const trial1 = session.recordTrial(
        dummyBuffer,
        dummyQuality,
        [{ classIndex: 0, className: 'HELLO', confidence: 0.85 }],
        12.5,
        'HELLO'
      );

      expect(trial1.trialIndex).toBe(1);
      expect(trial1.targetLabel).toBe('HELLO');
      expect(trial1.top3[0].className).toBe('HELLO');
      expect(trial1.sequenceSummary.totalSequenceEnergy).toBeGreaterThan(0);
      expect(session.count).toBe(1);

      // Record 4 more trials to reach max capacity (5)
      for (let i = 2; i <= 5; i++) {
        session.recordTrial(
          dummyBuffer,
          dummyQuality,
          [{ classIndex: 9, className: 'YES', confidence: 0.75 }],
          14.0,
          'YES'
        );
      }

      expect(session.count).toBe(5);
      expect(session.isFull).toBe(true);

      // Attempting to record 6th trial should throw
      expect(() => {
        session.recordTrial(
          dummyBuffer,
          dummyQuality,
          [{ classIndex: 9, className: 'YES', confidence: 0.75 }],
          14.0
        );
      }).toThrow(/Diagnostic session is full/);

      // Verify export JSON string
      const jsonStr = session.exportJsonString();
      const parsed = JSON.parse(jsonStr);
      expect(parsed.trialsCount).toBe(5);
      expect(parsed.trials.length).toBe(5);
      expect(parsed.trials[0].targetLabel).toBe('HELLO');
      expect(parsed.trials[1].targetLabel).toBe('YES');

      // Clear session
      session.clear();
      expect(session.count).toBe(0);
      expect(session.isFull).toBe(false);
    });
  });

  describe('3. Identical-Input Repeatability (Investigation A)', () => {
    it('verifies deterministic repeatability on 10 runs with identical logits', async () => {
      // Mock session returning deterministic outputs
      const mockSession = {
        predict: async (buffer: Float32Array) => {
          // Verify input length
          expect(buffer.length).toBe(60 * FEATURE_DIMENSION);
          const logits = new Float32Array(79);
          logits[0] = 5.0; // HELLO
          logits[1] = 2.0;
          return {
            logits,
            topK: [
              { classIndex: 0, className: 'HELLO', confidence: 0.95 },
              { classIndex: 1, className: 'THANK_YOU', confidence: 0.04 },
            ],
            latencyMs: 10.5,
            provider: 'wasm',
          };
        },
      } as unknown as SpoterInferenceSession;

      const inputBuffer = new Float32Array(60 * FEATURE_DIMENSION).fill(0.123);
      const vocab = { 0: 'HELLO', 1: 'THANK_YOU' };

      const report: RepeatabilityReport = await runRepeatabilityTest(
        mockSession,
        inputBuffer,
        vocab,
        10,
        1e-4
      );

      expect(report.runsCount).toBe(10);
      expect(report.isRepeatable).toBe(true);
      expect(report.predictedClassConsistent).toBe(true);
      expect(report.maxLogitDeviation).toBe(0);
      expect(report.maxProbDeviation).toBe(0);
      expect(report.summary).toContain('DETERMINISTIC');
      expect(report.runs.length).toBe(10);
    });

    it('detects and flags non-deterministic behavior if logits drift across runs', async () => {
      let callCount = 0;
      const mockSession = {
        predict: async () => {
          callCount++;
          const logits = new Float32Array(79);
          // Introduce drift in call #5
          logits[0] = callCount === 5 ? 5.5 : 5.0;
          return {
            logits,
            topK: [{ classIndex: 0, className: 'HELLO', confidence: 0.9 }],
            latencyMs: 8.0,
            provider: 'wasm',
          };
        },
      } as unknown as SpoterInferenceSession;

      const inputBuffer = new Float32Array(60 * FEATURE_DIMENSION);
      const report = await runRepeatabilityTest(mockSession, inputBuffer, {}, 10, 1e-4);

      expect(report.runsCount).toBe(10);
      expect(report.isRepeatable).toBe(false);
      expect(report.maxLogitDeviation).toBeCloseTo(0.5);
      expect(report.summary).toContain('NON-DETERMINISTIC');
    });
  });
});
