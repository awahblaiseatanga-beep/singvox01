/**
 * Input-validity gate for recognition.
 *
 * Measured model behaviour (docs/RECOGNITION_79_CLASS_RECOVERY_AUDIT.md,
 * experiments/baseline-79-audit/): the 79-class baseline was trained on clips
 * where the signer's landmarks are present in essentially every frame. When it
 * is fed a window dominated by missing-landmark (all-zero) frames it does not
 * return "nothing" — it returns a confident attractor class:
 *
 *   all-zero window                              -> SICK 0.856
 *   real pose/face but hand blocks zeroed        -> YESTERDAY 0.692
 *   a real HELLO clip with 50/60 zero frames     -> DAY 0.321 (sign lost)
 *   the same clip with landmarks present         -> HELLO 0.416 (correct)
 *
 * So a mostly-empty window is not merely uninformative, it is actively
 * misleading, and the stabilizer will commit its output. This gate refuses such
 * a window before inference is allowed to influence the transcript.
 *
 * It does not change the model, the 366-D contract, the normalization scalars
 * or any threshold: it only decides whether the buffered window is a valid
 * observation at all.
 */

export type CoverageInput = {
  /** Percentage of buffered frames where at least one hand was detected. */
  anyHandPercent: number;
  /** Percentage of buffered frames where the pose (shoulders) was detected. */
  posePercent: number;
  /** Frames currently in the buffer. */
  frames: number;
};

export type GateDecision = {
  allowed: boolean;
  reason: 'ok' | 'buffer-empty' | 'no-hands' | 'no-pose';
  /** Short, non-technical explanation for the UI. */
  detail: string;
};

/**
 * Thresholds chosen from the measured degradation curve: a real clip stayed
 * correctly recognised while at least ~30% of the window carried landmarks, and
 * collapsed to an attractor class below ~20%. 25% sits between the two observed
 * regimes and is deliberately permissive so a genuine sign is never gated out.
 */
export const MIN_HAND_COVERAGE_PERCENT = 25;
export const MIN_POSE_COVERAGE_PERCENT = 25;

export function evaluateRecognitionGate(input: CoverageInput): GateDecision {
  if (input.frames <= 0) {
    return { allowed: false, reason: 'buffer-empty', detail: 'Waiting for camera frames.' };
  }
  if (input.anyHandPercent < MIN_HAND_COVERAGE_PERCENT) {
    return {
      allowed: false,
      reason: 'no-hands',
      detail: 'Hands not visible — recognition is paused until your hands are in frame.',
    };
  }
  if (input.posePercent < MIN_POSE_COVERAGE_PERCENT) {
    return {
      allowed: false,
      reason: 'no-pose',
      detail: 'Upper body not visible — step back so your shoulders are in frame.',
    };
  }
  return { allowed: true, reason: 'ok', detail: 'Tracking.' };
}
