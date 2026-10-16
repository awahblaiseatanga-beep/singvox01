/**
 * LatencyProfiler: Instrumentation utility for measuring cold-start
 * and steady-state timings across all 10 stages of the recognition pipeline.
 */

export type StageTimings = {
  median: number;
  p95: number;
  min: number;
  max: number;
  count: number;
};

export type ColdStartRecord = {
  cameraPermissionAndReadyMs: number;
  mediaPipeInitMs: number;
  mediaPipeFirstDetectMs: number;
  onnxInitMs: number;
  onnxFirstInferenceMs: number;
  bufferWarmupMs: number;
  firstHandVisibleToRenderMs: number;
};

export class LatencyProfiler {
  // Cold start markers
  private coldStartStartTimes: Map<string, number> = new Map();
  private coldStart: Partial<ColdStartRecord> = {};

  // Steady-state samples (ring buffers capped at maxSamples)
  private maxSamples = 100;
  private samples: {
    mediaPipeDetect: number[];
    poseDetect: number[];
    handsDetect: number[];
    faceDetect: number[];
    featureExtraction: number[];
    v2Normalization: number[];
    onnxInference: number[];
    stabilizerProcess: number[];
    overlayRender: number[];
    endToEndFrame: number[];
  } = {
    mediaPipeDetect: [],
    poseDetect: [],
    handsDetect: [],
    faceDetect: [],
    featureExtraction: [],
    v2Normalization: [],
    onnxInference: [],
    stabilizerProcess: [],
    overlayRender: [],
    endToEndFrame: [],
  };

  private firstHandDetectedTimestamp: number | null = null;
  private firstHandRenderedTimestamp: number | null = null;

  // MARKERS FOR COLD START
  markColdStartBegin(stage: string): void {
    this.coldStartStartTimes.set(stage, performance.now());
  }

  markColdStartEnd(stage: keyof ColdStartRecord, beginStageName?: string): number {
    const start = this.coldStartStartTimes.get(beginStageName ?? stage);
    if (start === undefined) return 0;
    const duration = performance.now() - start;
    this.coldStart[stage] = duration;
    return duration;
  }

  recordFirstHandDetected(): void {
    if (this.firstHandDetectedTimestamp === null) {
      this.firstHandDetectedTimestamp = performance.now();
    }
  }

  recordFirstHandRendered(): void {
    if (this.firstHandDetectedTimestamp !== null && this.firstHandRenderedTimestamp === null) {
      this.firstHandRenderedTimestamp = performance.now();
      this.coldStart.firstHandVisibleToRenderMs = this.firstHandRenderedTimestamp - this.firstHandDetectedTimestamp;
    }
  }

  // SAMPLE RECORDING FOR STEADY STATE
  recordSample(category: keyof typeof this.samples, durationMs: number): void {
    if (!Number.isFinite(durationMs) || durationMs < 0) return;
    const arr = this.samples[category];
    arr.push(durationMs);
    if (arr.length > this.maxSamples) {
      arr.shift();
    }
  }

  static computeStats(values: number[]): StageTimings {
    if (values.length === 0) {
      return { median: 0, p95: 0, min: 0, max: 0, count: 0 };
    }
    const sorted = [...values].sort((a, b) => a - b);
    const count = sorted.length;
    const min = sorted[0];
    const max = sorted[count - 1];

    const median =
      count % 2 === 1
        ? sorted[Math.floor(count / 2)]
        : (sorted[count / 2 - 1] + sorted[count / 2]) / 2;

    const p95Index = Math.min(count - 1, Math.floor(count * 0.95));
    const p95 = sorted[p95Index];

    return {
      median: Math.round(median * 100) / 100,
      p95: Math.round(p95 * 100) / 100,
      min: Math.round(min * 100) / 100,
      max: Math.round(max * 100) / 100,
      count,
    };
  }

  getColdStart(): Partial<ColdStartRecord> {
    return { ...this.coldStart };
  }

  getSteadyStateReport(): Record<string, StageTimings> {
    const report: Record<string, StageTimings> = {};
    for (const [key, list] of Object.entries(this.samples)) {
      report[key] = LatencyProfiler.computeStats(list);
    }
    return report;
  }

  resetSteadyState(): void {
    for (const key of Object.keys(this.samples) as (keyof typeof this.samples)[]) {
      this.samples[key] = [];
    }
  }
}

export const globalProfiler = new LatencyProfiler();
