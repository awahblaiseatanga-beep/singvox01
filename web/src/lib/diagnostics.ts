import type { SpoterInferenceSession } from './inference';
import type { SequenceQuality } from './sequenceBuffer';
import { FEATURE_DIMENSION } from './contracts';

export type RepeatabilityRunResult = {
  runIndex: number;
  topClassIndex: number;
  topClassName: string;
  topConfidence: number;
  top3: { classIndex: number; className: string; confidence: number }[];
  latencyMs: number;
  maxLogitDiffFromRun1: number;
  maxProbDiffFromRun1: number;
};

export type RepeatabilityReport = {
  isRepeatable: boolean;
  runsCount: number;
  maxLogitDeviation: number;
  maxProbDeviation: number;
  predictedClassConsistent: boolean;
  latencyStats: { minMs: number; avgMs: number; maxMs: number };
  runs: RepeatabilityRunResult[];
  tolerance: number;
  summary: string;
};

export type TrialRecord = {
  trialIndex: number;
  targetLabel?: string;
  timestampMs: number;
  top3: { classIndex: number; className: string; confidence: number }[];
  quality: SequenceQuality;
  latencyMs: number;
  sequenceSummary: {
    firstFrameNorm: number;
    lastFrameNorm: number;
    totalSequenceEnergy: number;
  };
};

/**
 * Executes an isolated 10-run repeatability diagnostic test on an identical frozen Float32Array tensor.
 * Deep-copies the buffer once and reuses that exact array across all runs.
 * Verifies determinism within an explicit numerical tolerance.
 */
export async function runRepeatabilityTest(
  session: SpoterInferenceSession,
  buffer: Float32Array,
  vocabMap: Record<number, string>,
  runs: number = 10,
  tolerance: number = 1e-4
): Promise<RepeatabilityReport> {
  if (buffer.length !== 60 * FEATURE_DIMENSION) {
    throw new Error(`Invalid buffer dimension: expected ${60 * FEATURE_DIMENSION}, got ${buffer.length}`);
  }

  // Exact single deep-copy of the input tensor: NO MediaPipe, normalization, or mutation between runs.
  const frozenInput = new Float32Array(buffer);

  const runsResults: RepeatabilityRunResult[] = [];
  let baseLogits: Float32Array | null = null;
  let baseProbs: number[] | null = null;
  let maxLogitDeviation = 0;
  let maxProbDeviation = 0;
  let predictedClassConsistent = true;
  const latencies: number[] = [];

  for (let i = 0; i < runs; i++) {
    const res = await session.predict(frozenInput, vocabMap);
    latencies.push(res.latencyMs);

    const probs = Array.from(res.logits).map((l, _, arr) => {
      const maxL = Math.max(...arr);
      const exps = arr.map((x) => Math.exp(x - maxL));
      const sum = exps.reduce((a, b) => a + b, 0);
      return Math.exp(l - maxL) / sum;
    });

    if (i === 0) {
      baseLogits = new Float32Array(res.logits);
      baseProbs = probs;
      runsResults.push({
        runIndex: 1,
        topClassIndex: res.topK[0]?.classIndex ?? -1,
        topClassName: res.topK[0]?.className ?? 'UNKNOWN',
        topConfidence: res.topK[0]?.confidence ?? 0,
        top3: res.topK.slice(0, 3),
        latencyMs: Number(res.latencyMs.toFixed(1)),
        maxLogitDiffFromRun1: 0,
        maxProbDiffFromRun1: 0,
      });
    } else {
      let runMaxLogitDiff = 0;
      let runMaxProbDiff = 0;

      for (let k = 0; k < res.logits.length; k++) {
        const lDiff = Math.abs(res.logits[k] - baseLogits![k]);
        if (lDiff > runMaxLogitDiff) runMaxLogitDiff = lDiff;
      }
      for (let k = 0; k < probs.length; k++) {
        const pDiff = Math.abs(probs[k] - baseProbs![k]);
        if (pDiff > runMaxProbDiff) runMaxProbDiff = pDiff;
      }

      if (runMaxLogitDiff > maxLogitDeviation) maxLogitDeviation = runMaxLogitDiff;
      if (runMaxProbDiff > maxProbDeviation) maxProbDeviation = runMaxProbDiff;

      if (res.topK[0]?.classIndex !== runsResults[0].topClassIndex) {
        predictedClassConsistent = false;
      }

      runsResults.push({
        runIndex: i + 1,
        topClassIndex: res.topK[0]?.classIndex ?? -1,
        topClassName: res.topK[0]?.className ?? 'UNKNOWN',
        topConfidence: res.topK[0]?.confidence ?? 0,
        top3: res.topK.slice(0, 3),
        latencyMs: Number(res.latencyMs.toFixed(1)),
        maxLogitDiffFromRun1: runMaxLogitDiff,
        maxProbDiffFromRun1: runMaxProbDiff,
      });
    }
  }

  const isRepeatable = maxLogitDeviation <= tolerance && predictedClassConsistent;
  const minMs = Math.min(...latencies);
  const maxMs = Math.max(...latencies);
  const avgMs = latencies.reduce((a, b) => a + b, 0) / latencies.length;

  const summary = isRepeatable
    ? `DETERMINISTIC: All ${runs} inference runs produced identical outputs within tolerance (${tolerance}). Max logit delta = ${maxLogitDeviation.toExponential(2)}.`
    : `NON-DETERMINISTIC: Discrepancy detected across runs. Max logit delta = ${maxLogitDeviation}, Class consistent = ${predictedClassConsistent}.`;

  return {
    isRepeatable,
    runsCount: runs,
    maxLogitDeviation,
    maxProbDeviation,
    predictedClassConsistent,
    latencyStats: {
      minMs: Number(minMs.toFixed(1)),
      avgMs: Number(avgMs.toFixed(1)),
      maxMs: Number(maxMs.toFixed(1)),
    },
    runs: runsResults,
    tolerance,
    summary,
  };
}

/**
 * Diagnostic Session Manager for controlled 5-trial sign performance recordings.
 */
export class DiagnosticSession {
  private trials: TrialRecord[] = [];
  readonly maxTrials: number = 5;

  get count(): number {
    return this.trials.length;
  }

  get isFull(): boolean {
    return this.trials.length >= this.maxTrials;
  }

  getTrials(): TrialRecord[] {
    return [...this.trials];
  }

  recordTrial(
    buffer: Float32Array,
    quality: SequenceQuality,
    top3: { classIndex: number; className: string; confidence: number }[],
    latencyMs: number,
    targetLabel?: string
  ): TrialRecord {
    if (this.isFull) {
      throw new Error(`Diagnostic session is full (maximum ${this.maxTrials} trials). Clear or export first.`);
    }

    // Compute compact sequence summary without storing massive video or face images
    let firstFrameNorm = 0;
    let lastFrameNorm = 0;
    let totalEnergy = 0;

    for (let k = 0; k < FEATURE_DIMENSION; k++) {
      firstFrameNorm += Math.abs(buffer[k]);
      lastFrameNorm += Math.abs(buffer[59 * FEATURE_DIMENSION + k]);
    }
    for (let k = 0; k < buffer.length; k++) {
      totalEnergy += Math.abs(buffer[k]);
    }

    const trial: TrialRecord = {
      trialIndex: this.trials.length + 1,
      targetLabel: targetLabel ? targetLabel.trim().toUpperCase() : undefined,
      timestampMs: Date.now(),
      top3,
      quality,
      latencyMs: Number(latencyMs.toFixed(1)),
      sequenceSummary: {
        firstFrameNorm: Number(firstFrameNorm.toFixed(2)),
        lastFrameNorm: Number(lastFrameNorm.toFixed(2)),
        totalSequenceEnergy: Number(totalEnergy.toFixed(2)),
      },
    };

    this.trials.push(trial);
    return trial;
  }

  clear(): void {
    this.trials = [];
  }

  exportJsonString(): string {
    const payload = {
      exportedAt: new Date().toISOString(),
      trialsCount: this.trials.length,
      trials: this.trials,
    };
    return JSON.stringify(payload, null, 2);
  }
}
