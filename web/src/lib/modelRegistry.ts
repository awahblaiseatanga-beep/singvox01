import { ASL_VOCAB, PILOT_VOCAB } from './vocab';
import {
  BASELINE_STABILIZER_CONFIG,
  PILOT_STABILIZER_CONFIG,
  type StabilizerConfig,
} from './temporalStabilizer';

/**
 * Single source of truth for the two recognition models.
 *
 * Every model owns its artifact, its class map and its expected output size.
 * They are deliberately bound together here so a class map can never be paired
 * with a model it does not belong to: `assertModelOutputSize` refuses to map
 * predictions when the ONNX output length disagrees with the active vocab.
 *
 * Verified evidence for these declarations is recorded in
 * docs/RECOGNITION_79_CLASS_RECOVERY_AUDIT.md.
 */
export type ModelId = 'pilot' | 'baseline';

export const PILOT_MODEL_URL =
  (import.meta.env.VITE_SPOTER_PILOT_URL as string | undefined)?.trim() || '/spoter_pilot.onnx';
export const BASELINE_MODEL_URL =
  (import.meta.env.VITE_SPOTER_V2_URL as string | undefined)?.trim() || '/spoter_v2_model.onnx';

export type ModelSpec = {
  id: ModelId;
  /** Short name for UI chips. */
  displayName: string;
  /** Recognition scope, phrased for the product UI. */
  scopeChip: string;
  /** Full scope sentence for the internal diagnostics header. */
  scopeDetail: string;
  modelUrl: string;
  vocab: Record<number, string>;
  /** Number of logits the ONNX graph must return. */
  classCount: number;
  stabilizerConfig: Partial<StabilizerConfig>;
  /** Present in the production GLB (web/public/avatar/…Competition_Prototype.glb). */
  avatarClipLabels: string[];
  status: 'validated' | 'experimental';
  notes: string[];
};

export const MODEL_REGISTRY: Record<ModelId, ModelSpec> = {
  pilot: {
    id: 'pilot',
    displayName: '3-Class Pilot',
    scopeChip: 'HELLO · YES · NO',
    scopeDetail: '3-class pilot (HELLO, YES, NO). Selectable fallback for the 79-class default.',
    modelUrl: PILOT_MODEL_URL,
    vocab: PILOT_VOCAB,
    classCount: 3,
    stabilizerConfig: PILOT_STABILIZER_CONFIG,
    avatarClipLabels: ['HELLO', 'YES', 'NO'],
    status: 'validated',
    notes: [
      'Trained on 10 fps ASL Citizen clips of three signs; every sign has an avatar clip.',
    ],
  },
  baseline: {
    id: 'baseline',
    displayName: '79-Class Baseline (SPOTER V2)',
    scopeChip: '79 ASL classes',
    scopeDetail:
      '79-class ASL baseline. Offline validation on its own held-out split: 86.0% top-1 on whole clips, ' +
      '80.4% on the recorded test split. Not yet validated on a live signer.',
    modelUrl: BASELINE_MODEL_URL,
    vocab: ASL_VOCAB,
    classCount: 79,
    stabilizerConfig: BASELINE_STABILIZER_CONFIG,
    avatarClipLabels: ['HELLO', 'YES', 'NO'],
    status: 'experimental',
    notes: [
      '79 logits; class indices match ai/sign-recognition/data/class_index_mapping.json exactly.',
      'Only HELLO, YES and NO have avatar clips. Other recognized signs return text only.',
      'The ONNX export has no attention-mask input, so it must be fed a whole sign, not a mostly empty window.',
      'No idle/rejection class exists, so any confident prediction is mapped to a sign.',
      'Avatar animation coverage is independent of recognition: uncovered signs show as text.',
    ],
  },
};

export function getModelSpec(id: ModelId): ModelSpec {
  return MODEL_REGISTRY[id];
}

/**
 * Model the product ships with.
 *
 * The 79-class SPOTER V2 baseline is the recognition scope SignVox presents:
 * it is the model whose class map the UI reports, so the displayed scope and the
 * running graph always agree. The 3-class pilot stays selectable as a fallback.
 * Caveats that must stay visible in the UI: only HELLO, YES and NO have avatar
 * animations, and no live-signer validation has been performed yet
 * (docs/RECOGNITION_79_CLASS_RECOVERY_AUDIT.md).
 */
export const DEFAULT_MODEL_ID: ModelId = 'baseline';

/** Number of classes a vocab map defines, verifying that the keys are 0..n-1. */
export function vocabClassCount(vocab: Record<number, string>, label = 'vocab'): number {
  const keys = Object.keys(vocab).map(Number).sort((a, b) => a - b);
  if (keys.length === 0) throw new Error(`${label} is empty`);
  for (let i = 0; i < keys.length; i += 1) {
    if (keys[i] !== i) throw new Error(`${label} is not a dense 0..n-1 index range (missing ${i})`);
    if (!vocab[keys[i]]) throw new Error(`${label} has an empty label at index ${i}`);
  }
  return keys.length;
}

/**
 * Guards the class map / model pairing. Called on load and on every prediction
 * so a 3-class map can never silently label a 79-class model (or vice versa).
 */
export function assertModelOutputSize(
  vocab: Record<number, string>,
  outputSize: number,
  modelUrl = 'model',
): number {
  const expected = vocabClassCount(vocab, `class map for ${modelUrl}`);
  if (outputSize !== expected) {
    throw new Error(
      `Model/class-map mismatch for ${modelUrl}: the model returned ${outputSize} logits but the ` +
        `active class map defines ${expected} classes. Refusing to label predictions.`,
    );
  }
  return expected;
}

/**
 * Avatar dispatch is independent of recognition: a recognised sign without a
 * clip must be surfaced honestly instead of playing an unrelated animation.
 * `animationClips` are named `ASL_<LABEL>` in the production GLB.
 */
export function avatarClipLabelsFromClipNames(clipNames: string[]): string[] {
  return clipNames
    .filter((name) => /^asl_/i.test(name))
    .map((name) => name.slice(4).toUpperCase())
    .filter((label) => label !== 'NEUTRAL');
}

export function hasAvatarClip(label: string, clipLabels: string[]): boolean {
  return clipLabels.includes(label.toUpperCase().trim());
}

// Fail fast at module load if the shipped vocabularies are malformed: a bad map
// must never be able to label a model's output.
for (const spec of Object.values(MODEL_REGISTRY)) {
  const count = vocabClassCount(spec.vocab, spec.id);
  if (count !== spec.classCount) {
    throw new Error(`${spec.id} declares ${spec.classCount} classes but its vocab defines ${count}`);
  }
  const overlap = Object.values(spec.vocab).filter((name) => name.trim() !== name || name === '');
  if (overlap.length > 0) throw new Error(`${spec.id} vocab contains blank or padded labels`);
}
