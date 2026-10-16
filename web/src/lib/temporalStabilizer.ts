export type RawPrediction = {
  classIndex: number;
  className: string;
  confidence: number;
  timestampMs: number;
};

export type StabilizerConfig = {
  windowMs: number;
  maxObservations: number;
  minimumConfidence: number;
  minimumStableEvidence: number;
  minimumCommitEvidence: number;
  minimumStableObservations: number;
  minimumCommitObservations: number;
  minimumStableDurationMs: number;
  transitionMargin: number;
  dropThreshold: number;
};

export type StabilizerState = {
  rawPrediction: RawPrediction;
  currentStableName: string | null;
  stabilityEvidence: number;
  status: 'Listening' | 'Uncertain' | 'Stable';
  committedSign: string | null;
};

export const PILOT_STABILIZER_CONFIG: Partial<StabilizerConfig> = {
  minimumCommitEvidence: 0.65,
  minimumStableEvidence: 0.40,
  dropThreshold: 0.25
};

export const BASELINE_STABILIZER_CONFIG: Partial<StabilizerConfig> = {
  minimumCommitEvidence: 0.25,
  minimumStableEvidence: 0.15,
  dropThreshold: 0.10,
  minimumConfidence: 0.05
};

export class TemporalStabilizer {
  private buffer: RawPrediction[] = [];
  private config: StabilizerConfig;
  private currentStableName: string | null = null;
  private lastProcessedTimestamp: number = -1;
  private lastCommittedName: string | null = null;

  constructor(config: Partial<StabilizerConfig> = {}) {
    this.config = {
      windowMs: 2000,
      maxObservations: 60,
      minimumConfidence: 0.2,
      minimumStableEvidence: 0.4,
      minimumCommitEvidence: 0.65,
      minimumStableObservations: 2,
      minimumCommitObservations: 3,
      minimumStableDurationMs: 400,
      transitionMargin: 0.15,
      dropThreshold: 0.25,
      ...config
    };
  }

  process(prediction: RawPrediction): StabilizerState {
    if (this.lastProcessedTimestamp > -1 && prediction.timestampMs < this.lastProcessedTimestamp) {
        throw new Error(`Out of order timestamp: ${prediction.timestampMs} < ${this.lastProcessedTimestamp}`);
    }
    this.lastProcessedTimestamp = prediction.timestampMs;

    this.buffer.push(prediction);

    // Prune the buffer (Time bound)
    const cutoff = prediction.timestampMs - this.config.windowMs;
    this.buffer = this.buffer.filter(p => p.timestampMs >= cutoff);
    
    // Prune the buffer (Size bound)
    if (this.buffer.length > this.config.maxObservations) {
        this.buffer = this.buffer.slice(this.buffer.length - this.config.maxObservations);
    }

    // Compute weights and evidence
    let totalWeight = 0;
    const scores = new Map<string, number>();

    for (const p of this.buffer) {
       const age = prediction.timestampMs - p.timestampMs;
       const weight = 1.0 - (age / this.config.windowMs);
       totalWeight += weight;

       if (p.confidence >= this.config.minimumConfidence) {
           const classScore = (scores.get(p.className) || 0) + (p.confidence * weight);
           scores.set(p.className, classScore);
       }
    }

    // Convert scores to normalized evidence 0.0 - 1.0
    let bestClass: string | null = null;
    let highestEvidence = 0;
    
    for (const [cls, score] of scores.entries()) {
       const evidence = totalWeight > 0 ? score / totalWeight : 0;
       scores.set(cls, evidence);
       
       if (evidence > highestEvidence) {
           highestEvidence = evidence;
           bestClass = cls;
       }
    }

    const duration = this.buffer.length > 0 ? prediction.timestampMs - this.buffer[0].timestampMs : 0;
    const observations = this.buffer.length;

    let committedSign: string | null = null;
    let status: StabilizerState['status'] = this.buffer.length === 0 ? 'Listening' : 'Uncertain';
    
    // Evaluate drops
    if (this.currentStableName) {
        const currentEvidence = scores.get(this.currentStableName) || 0;
        if (currentEvidence < this.config.dropThreshold) {
            this.currentStableName = null;
            this.lastCommittedName = null; // Re-arm duplicate suppression
        }
    }

    // Evaluate state transitions
    if (this.currentStableName) {
        const currentEvidence = scores.get(this.currentStableName) || 0;
        
        if (bestClass && bestClass !== this.currentStableName) {
            const nextEvidence = scores.get(bestClass) || 0;
            if (
               nextEvidence >= this.config.minimumStableEvidence && 
               nextEvidence > currentEvidence + this.config.transitionMargin &&
               observations >= this.config.minimumStableObservations &&
               duration >= this.config.minimumStableDurationMs
            ) {
               this.currentStableName = bestClass;
            }
        }
    } else {
        if (bestClass && highestEvidence >= this.config.minimumStableEvidence &&
            observations >= this.config.minimumStableObservations &&
            duration >= this.config.minimumStableDurationMs) {
            this.currentStableName = bestClass;
        }
    }

    // Evaluate commits
    let stabilityEvidence = 0;
    if (this.currentStableName) {
        status = 'Stable';
        stabilityEvidence = scores.get(this.currentStableName) || 0;
        
        if (stabilityEvidence >= this.config.minimumCommitEvidence &&
            observations >= this.config.minimumCommitObservations) {
            
            if (this.currentStableName !== this.lastCommittedName) {
                committedSign = this.currentStableName;
                this.lastCommittedName = this.currentStableName;
            }
        }
    }

    return {
        rawPrediction: prediction,
        currentStableName: this.currentStableName,
        stabilityEvidence,
        status,
        committedSign
    };
  }

  reset() {
      this.buffer = [];
      this.currentStableName = null;
      this.lastProcessedTimestamp = -1;
      this.lastCommittedName = null;
  }
}
