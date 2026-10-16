import { describe, it, expect } from 'vitest';
import {
  FEATURE_DIMENSION,
  SEQUENCE_LENGTH,
  OFFSETS,
  V2_SCALARS,
  HAND_LANDMARK_COUNT,
  POSE_LANDMARK_COUNT,
  FACE_LANDMARK_COUNT,
} from '../lib/contracts';
import { assembleCanonicalFrame, countNonFinite } from '../lib/featureVector';
import { applyV2Normalization, shoulderCenter } from '../lib/normalize';
import { SequenceBuffer } from '../lib/sequenceBuffer';
import { ASL_VOCAB, PILOT_VOCAB } from '../lib/vocab';
import classMappingJson from '../../../ai/sign-recognition/data/class_index_mapping.json';

describe('Phase 1 Live Camera-to-SPOTER V2 Pipeline', () => {
  describe('1. 366-Feature Dimension and Landmark Ordering', () => {
    it('verifies exact total length of 366 features', () => {
      expect(FEATURE_DIMENSION).toBe(366);
      expect(SEQUENCE_LENGTH).toBe(60);
    });

    it('verifies exact offset boundaries for each landmark group', () => {
      expect(OFFSETS.leftHand).toBe(0);
      expect(OFFSETS.leftHand + HAND_LANDMARK_COUNT * 3).toBe(63);

      expect(OFFSETS.rightHand).toBe(63);
      expect(OFFSETS.rightHand + HAND_LANDMARK_COUNT * 3).toBe(126);

      expect(OFFSETS.pose).toBe(126);
      expect(OFFSETS.pose + POSE_LANDMARK_COUNT * 5).toBe(291);

      expect(OFFSETS.face).toBe(291);
      expect(OFFSETS.face + FACE_LANDMARK_COUNT * 3).toBe(366);
    });

    it('verifies interleaved pose structure (33 landmarks × 5 channels: x, y, z, visibility, presence)', () => {
      const mockDetection = {
        pose: Array.from({ length: 33 }, (_, i) => ({
          x: 0.1 * (i + 1),
          y: 0.2 * (i + 1),
          z: 0.05 * (i + 1),
          visibility: 0.95,
          presence: 0.99,
        })),
        hands: [],
        face: undefined,
      };

      const frame = assembleCanonicalFrame(mockDetection);
      expect(frame.raw.length).toBe(366);

      // Check Landmark 0
      expect(frame.raw[126]).toBeCloseTo(0.1);
      expect(frame.raw[127]).toBeCloseTo(0.2);
      expect(frame.raw[128]).toBeCloseTo(0.05);
      expect(frame.raw[129]).toBeCloseTo(0.95);
      expect(frame.raw[130]).toBeCloseTo(0.99);

      // Check Landmark 32
      const offset32 = 126 + 32 * 5;
      expect(frame.raw[offset32]).toBeCloseTo(0.1 * 33);
      expect(frame.raw[offset32 + 1]).toBeCloseTo(0.2 * 33);
      expect(frame.raw[offset32 + 2]).toBeCloseTo(0.05 * 33);
      expect(frame.raw[offset32 + 3]).toBeCloseTo(0.95);
      expect(frame.raw[offset32 + 4]).toBeCloseTo(0.99);
    });
  });

  describe('2. Missing Landmark Handling', () => {
    it('zero-fills missing hands and face when only pose is present', () => {
      const mockDetection = {
        pose: Array.from({ length: 33 }, () => ({ x: 0.5, y: 0.5, z: 0.1, visibility: 0.9, presence: 0.9 })),
        hands: [],
        face: undefined,
      };

      const frame = assembleCanonicalFrame(mockDetection);
      expect(frame.presence.leftHand).toBe(false);
      expect(frame.presence.rightHand).toBe(false);
      expect(frame.presence.face).toBe(false);
      expect(frame.presence.pose).toBe(true);

      // Check left hand (0..62) is completely zeroed
      for (let i = 0; i < 63; i++) {
        expect(frame.raw[i]).toBe(0);
      }
      // Check right hand (63..125) is completely zeroed
      for (let i = 63; i < 126; i++) {
        expect(frame.raw[i]).toBe(0);
      }
      // Check face (291..365) is completely zeroed
      for (let i = 291; i < 366; i++) {
        expect(frame.raw[i]).toBe(0);
      }
    });

    it('gracefully handles completely empty detections without throwing or producing NaN/Inf', () => {
      const emptyDetection = {
        pose: undefined,
        hands: [],
        face: undefined,
      };

      const frame = assembleCanonicalFrame(emptyDetection);
      expect(frame.raw.length).toBe(366);
      const finite = countNonFinite(frame.raw);
      expect(finite.nan).toBe(0);
      expect(finite.inf).toBe(0);

      // Check all values are 0
      const allZero = frame.raw.every((v) => v === 0);
      expect(allZero).toBe(true);

      // Check normalization on all zeros does not divide by zero
      const normalized = applyV2Normalization(frame.raw);
      const normFinite = countNonFinite(normalized);
      expect(normFinite.nan).toBe(0);
      expect(normFinite.inf).toBe(0);
    });
  });

  describe('3. Normalization Consistency', () => {
    it('verifies exact V2 GroupNorm scalar values', () => {
      expect(V2_SCALARS.leftHand).toBeCloseTo(0.3886975, 5);
      expect(V2_SCALARS.rightHand).toBeCloseTo(0.3666481, 5);
      expect(V2_SCALARS.poseXyz).toBeCloseTo(1.8127285, 5);
      expect(V2_SCALARS.face).toBeCloseTo(0.3139562, 5);
    });

    it('scales only pose XYZ coordinates and leaves visibility and presence unchanged', () => {
      const raw = new Float32Array(366);
      // Set pose landmark 0
      raw[126] = 1.8127285242080688; // x
      raw[127] = 3.6254570484161376; // y
      raw[128] = 0.0; // z
      raw[129] = 0.85; // visibility
      raw[130] = 0.95; // presence

      // Without shoulder landmarks (11 and 12 are 0), shoulder centering is no-op
      const normalized = applyV2Normalization(raw);

      // x should be divided by poseXyz scalar -> 1.0
      expect(normalized[126]).toBeCloseTo(1.0, 4);
      // y should be divided by poseXyz scalar -> 2.0
      expect(normalized[127]).toBeCloseTo(2.0, 4);
      // z is 0
      expect(normalized[128]).toBe(0);
      // visibility and presence must remain unscaled
      expect(normalized[129]).toBeCloseTo(0.85, 4);
      expect(normalized[130]).toBeCloseTo(0.95, 4);
    });

    it('applies shoulder centering based on landmarks 11 and 12', () => {
      const raw = new Float32Array(366);
      // Left shoulder (idx 11): offset = 126 + 11*5 = 181
      raw[181] = 0.4; // x
      raw[182] = 0.5; // y
      raw[183] = 0.0; // z

      // Right shoulder (idx 12): offset = 126 + 12*5 = 186
      raw[186] = 0.6; // x
      raw[187] = 0.5; // y
      raw[188] = 0.0; // z

      // Midpoint: (0.5, 0.5, 0.0). Shoulder dist: 0.2
      // Set another landmark (e.g. nose idx 0 at offset 126): (0.5, 0.3, 0.0)
      raw[126] = 0.5;
      raw[127] = 0.3;
      raw[128] = 0.0;

      const centered = shoulderCenter(raw);
      // Nose centered x: (0.5 - 0.5) / 0.2 = 0.0
      expect(centered[126]).toBeCloseTo(0.0, 4);
      // Nose centered y: (0.3 - 0.5) / 0.2 = -1.0
      expect(centered[127]).toBeCloseTo(-1.0, 4);
    });
  });

  describe('4. Sequence Buffering and Insufficient Sequence Handling', () => {
    it('tracks buffering progress and reports readiness only at 60 frames', () => {
      const seqBuffer = new SequenceBuffer(60);
      expect(seqBuffer.capacity).toBe(60);
      expect(seqBuffer.length).toBe(0);
      expect(seqBuffer.isReady).toBe(false);
      expect(seqBuffer.getFlattenedBuffer()).toBeNull();

      const dummyFrame = new Float32Array(366);

      // Push 30 frames
      for (let i = 0; i < 30; i++) {
        seqBuffer.push(dummyFrame);
      }
      expect(seqBuffer.length).toBe(30);
      expect(seqBuffer.isReady).toBe(false);
      expect(seqBuffer.getStatus().progressPercent).toBe(50);
      expect(seqBuffer.getFlattenedBuffer()).toBeNull(); // Insufficient

      // Push 30 more frames -> total 60
      for (let i = 0; i < 30; i++) {
        seqBuffer.push(dummyFrame);
      }
      expect(seqBuffer.length).toBe(60);
      expect(seqBuffer.isReady).toBe(true);
      expect(seqBuffer.getStatus().progressPercent).toBe(100);

      const flat = seqBuffer.getFlattenedBuffer();
      expect(flat).not.toBeNull();
      expect(flat!.length).toBe(60 * 366);
    });

    it('enforces FIFO eviction once capacity is exceeded', () => {
      const seqBuffer = new SequenceBuffer(60);

      // Push 60 frames tagged by index in first float
      for (let i = 0; i < 60; i++) {
        const frame = new Float32Array(366);
        frame[0] = i;
        seqBuffer.push(frame);
      }

      let flat = seqBuffer.getFlattenedBuffer()!;
      expect(flat[0]).toBe(0); // Oldest frame is index 0
      expect(flat[59 * 366]).toBe(59); // Newest frame is index 59

      // Push frame 60 -> should evict frame 0, oldest is now frame 1
      const frame60 = new Float32Array(366);
      frame60[0] = 60;
      seqBuffer.push(frame60);

      expect(seqBuffer.length).toBe(60);
      flat = seqBuffer.getFlattenedBuffer()!;
      expect(flat[0]).toBe(1); // Frame 1 is now at index 0
      expect(flat[59 * 366]).toBe(60); // Frame 60 is at index 59
    });

    it('rejects invalid frame dimensions', () => {
      const seqBuffer = new SequenceBuffer(60);
      const invalidFrame = new Float32Array(100); // Invalid dimension
      expect(() => seqBuffer.push(invalidFrame)).toThrow(/Invalid frame dimension/);
    });

    it('resets cleanly', () => {
      const seqBuffer = new SequenceBuffer(60);
      seqBuffer.push(new Float32Array(366));
      expect(seqBuffer.length).toBe(1);
      seqBuffer.reset();
      expect(seqBuffer.length).toBe(0);
      expect(seqBuffer.isReady).toBe(false);
    });
  });

  describe('5. Vocabulary and 79-Class Checkpoint Output Dimensions', () => {
    it('verifies that ASL_VOCAB contains exactly 79 classes matching class_index_mapping.json', () => {
      const vocabKeys = Object.keys(ASL_VOCAB).map(Number);
      expect(vocabKeys.length).toBe(79);

      const mappingEntries = Object.entries(classMappingJson);
      expect(mappingEntries.length).toBe(79);

      for (const [keyStr, val] of mappingEntries) {
        const idx = Number(keyStr);
        expect(ASL_VOCAB[idx]).toBeDefined();
        expect(ASL_VOCAB[idx]).toBe(val.canonical_name);
      }
    });

    it('verifies Pilot vocabulary contains exactly 3 classes', () => {
      const pilotKeys = Object.keys(PILOT_VOCAB).map(Number);
      expect(pilotKeys.length).toBe(3);
      expect(PILOT_VOCAB[0]).toBe('HELLO');
      expect(PILOT_VOCAB[1]).toBe('YES');
      expect(PILOT_VOCAB[2]).toBe('NO');
    });

    it('simulates Top-3 prediction extraction from 79-class logits', () => {
      const logits = new Float32Array(79).fill(0.0);
      // Give class 9 (YES) logit 6.0, class 0 (HELLO) 4.0, class 10 (NO) 3.0
      logits[9] = 6.0;
      logits[0] = 4.0;
      logits[10] = 3.0;

      // Softmax
      const maxLogit = Math.max(...logits);
      const exps = logits.map((x) => Math.exp(x - maxLogit));
      const sumExps = exps.reduce((a, b) => a + b, 0);
      const probs = exps.map((x) => x / sumExps);

      const indexed = Array.from(probs).map((p, idx) => ({
        classIndex: idx,
        className: ASL_VOCAB[idx] || `CLASS_${idx}`,
        confidence: p,
      }));

      indexed.sort((a, b) => b.confidence - a.confidence);
      const top3 = indexed.slice(0, 3);

      expect(top3[0].className).toBe('YES');
      expect(top3[0].classIndex).toBe(9);
      expect(top3[0].confidence).toBeGreaterThan(0.7);

      expect(top3[1].className).toBe('HELLO');
      expect(top3[1].classIndex).toBe(0);

      expect(top3[2].className).toBe('NO');
      expect(top3[2].classIndex).toBe(10);
    });
  });
});
