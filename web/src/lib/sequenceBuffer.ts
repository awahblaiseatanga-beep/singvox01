import { FEATURE_DIMENSION, SEQUENCE_LENGTH } from './contracts';

export type SequenceBufferStatus = {
  length: number;
  capacity: number;
  isReady: boolean;
  progressPercent: number;
};

export type FrameMetadata = {
  presence: {
    leftHand: boolean;
    rightHand: boolean;
    pose: boolean;
    face: boolean;
  };
  nonFiniteCount: number;
  timestampMs: number;
};

export type SequenceQuality = {
  lhPercent: number;
  rhPercent: number;
  /** Percentage of frames where at least one hand was detected (either side). */
  anyHandPercent: number;
  posePercent: number;
  facePercent: number;
  framesWithNonFinite: number;
  totalNonFiniteValues: number;
  durationMs: number;
  avgIntervalMs: number;
  intervalStdDevMs: number;
  heuristicMovementCompleteness: {
    hasMovement: boolean;
    initialEnergy: number;
    peakEnergy: number;
    trailingEnergy: number;
    isClippingSuspected: boolean;
    note: string;
  };
};

/**
 * Bounded FIFO sequence buffer for SPOTER models.
 * Strictly enforces FEATURE_DIMENSION (366) per frame and bounded sequence length (default: 60).
 * Stores aligned FrameMetadata for each buffered frame without altering raw tensor vectors.
 */
export class SequenceBuffer {
  private buffer: Float32Array[] = [];
  private metadataBuffer: FrameMetadata[] = [];
  readonly capacity: number;

  constructor(capacity: number = SEQUENCE_LENGTH) {
    if (capacity <= 0) throw new Error('SequenceBuffer capacity must be greater than zero');
    this.capacity = capacity;
  }

  get length(): number {
    return this.buffer.length;
  }

  get isReady(): boolean {
    return this.buffer.length >= this.capacity;
  }

  getStatus(): SequenceBufferStatus {
    return {
      length: this.buffer.length,
      capacity: this.capacity,
      isReady: this.isReady,
      progressPercent: Math.min(100, Math.round((this.buffer.length / this.capacity) * 100)),
    };
  }

  /**
   * Pushes a canonical normalized frame into the buffer alongside optional detector metadata.
   * Enforces dimension 366. Drops oldest frame and metadata when capacity is reached (FIFO).
   */
  push(frame: Float32Array, metadata?: FrameMetadata): void {
    if (frame.length !== FEATURE_DIMENSION) {
      throw new Error(`Invalid frame dimension: expected ${FEATURE_DIMENSION}, got ${frame.length}`);
    }
    this.buffer.push(frame);
    this.metadataBuffer.push(
      metadata ?? {
        presence: { leftHand: false, rightHand: false, pose: false, face: false },
        nonFiniteCount: 0,
        timestampMs: performance.now(),
      }
    );

    if (this.buffer.length > this.capacity) {
      this.buffer.shift();
      this.metadataBuffer.shift();
    }
  }

  /**
   * Returns a contiguous Float32Array of shape [capacity * FEATURE_DIMENSION] (e.g. 60 * 366 = 21,960 floats)
   * ready for ONNX inference tensor creation.
   * Returns null if buffer does not have sufficient frames.
   */
  getFlattenedBuffer(): Float32Array | null {
    if (!this.isReady) {
      return null;
    }
    const flat = new Float32Array(this.capacity * FEATURE_DIMENSION);
    for (let i = 0; i < this.capacity; i++) {
      flat.set(this.buffer[i], i * FEATURE_DIMENSION);
    }
    return flat;
  }

  /**
   * Returns a copy of the metadata array aligned with the current buffer frames.
   */
  getMetadata(): FrameMetadata[] {
    return [...this.metadataBuffer];
  }

  /**
   * Computes sequence quality and cadence metrics over the buffered frames.
   * Returns null if buffer is not full.
   */
  getSequenceQuality(): SequenceQuality | null {
    if (!this.isReady) return null;

    let lhCount = 0;
    let rhCount = 0;
    let anyHandCount = 0;
    let poseCount = 0;
    let faceCount = 0;
    let framesWithNonFinite = 0;
    let totalNonFiniteValues = 0;

    for (let i = 0; i < this.capacity; i++) {
      const meta = this.metadataBuffer[i];
      if (meta.presence.leftHand) lhCount++;
      if (meta.presence.rightHand) rhCount++;
      if (meta.presence.leftHand || meta.presence.rightHand) anyHandCount++;
      if (meta.presence.pose) poseCount++;
      if (meta.presence.face) faceCount++;
      if (meta.nonFiniteCount > 0) {
        framesWithNonFinite++;
        totalNonFiniteValues += meta.nonFiniteCount;
      }
    }

    const tFirst = this.metadataBuffer[0].timestampMs;
    const tLast = this.metadataBuffer[this.capacity - 1].timestampMs;
    const durationMs = Math.max(0, tLast - tFirst);

    const intervals: number[] = [];
    for (let i = 1; i < this.capacity; i++) {
      intervals.push(this.metadataBuffer[i].timestampMs - this.metadataBuffer[i - 1].timestampMs);
    }

    const avgIntervalMs = intervals.length > 0 ? intervals.reduce((a, b) => a + b, 0) / intervals.length : 0;
    let variance = 0;
    for (const interval of intervals) {
      variance += Math.pow(interval - avgIntervalMs, 2);
    }
    const intervalStdDevMs = intervals.length > 0 ? Math.sqrt(variance / intervals.length) : 0;

    // Heuristic movement completeness check (hand displacement energy across consecutive frames)
    // Examines left hand (0..62) and right hand (63..125) differences
    const energies: number[] = [];
    for (let i = 1; i < this.capacity; i++) {
      const prev = this.buffer[i - 1];
      const curr = this.buffer[i];
      let diffSum = 0;
      for (let k = 0; k < 126; k++) {
        diffSum += Math.abs(curr[k] - prev[k]);
      }
      energies.push(diffSum / 126);
    }

    const initialWindow = energies.slice(0, 5);
    const initialEnergy = initialWindow.length ? initialWindow.reduce((a, b) => a + b, 0) / initialWindow.length : 0;
    const peakEnergy = energies.length ? Math.max(...energies) : 0;
    const trailingWindow = energies.slice(Math.max(0, energies.length - 5));
    const trailingEnergy = trailingWindow.length ? trailingWindow.reduce((a, b) => a + b, 0) / trailingWindow.length : 0;

    const hasMovement = peakEnergy > 0.02;
    // If movement at the window boundaries exceeds 40% of peak, sign may be clipped at start or end
    const isClippingSuspected =
      hasMovement && (initialEnergy > 0.4 * peakEnergy || trailingEnergy > 0.4 * peakEnergy);

    const note = !hasMovement
      ? 'Static sequence: minimal hand movement detected (heuristic indicator).'
      : isClippingSuspected
      ? 'Buffer boundary movement detected: sign may be truncated at window start or end (heuristic indicator).'
      : 'Movement peaks centrally: full sign movement likely contained within 60-frame window (heuristic indicator).';

    return {
      lhPercent: Math.round((lhCount / this.capacity) * 100),
      rhPercent: Math.round((rhCount / this.capacity) * 100),
      anyHandPercent: Math.round((anyHandCount / this.capacity) * 100),
      posePercent: Math.round((poseCount / this.capacity) * 100),
      facePercent: Math.round((faceCount / this.capacity) * 100),
      framesWithNonFinite,
      totalNonFiniteValues,
      durationMs: Math.round(durationMs),
      avgIntervalMs: Number(avgIntervalMs.toFixed(1)),
      intervalStdDevMs: Number(intervalStdDevMs.toFixed(1)),
      heuristicMovementCompleteness: {
        hasMovement,
        initialEnergy: Number(initialEnergy.toFixed(4)),
        peakEnergy: Number(peakEnergy.toFixed(4)),
        trailingEnergy: Number(trailingEnergy.toFixed(4)),
        isClippingSuspected,
        note,
      },
    };
  }

  /**
   * Resets the buffer to empty state.
   */
  reset(): void {
    this.buffer = [];
    this.metadataBuffer = [];
  }
}
