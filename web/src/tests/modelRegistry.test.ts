import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import { ASL_VOCAB, PILOT_VOCAB } from '../lib/vocab';
import {
  DEFAULT_MODEL_ID,
  MODEL_REGISTRY,
  assertModelOutputSize,
  avatarClipLabelsFromClipNames,
  getModelSpec,
  hasAvatarClip,
  vocabClassCount,
} from '../lib/modelRegistry';

const repoRoot = path.resolve(process.cwd(), '..');
const classIndexMappingPath = path.join(repoRoot, 'ai', 'sign-recognition', 'data', 'class_index_mapping.json');
const pilotMappingPath = path.join(repoRoot, 'ai', 'sign-recognition', 'data', 'pilot_class_mapping.json');
const productionGlbPath = path.join(process.cwd(), 'public', 'avatar', 'SignVox_Female_Competition_Prototype.glb');

/** Animation clip names from a .glb container, without decoding the binary chunk. */
function readGlbAnimationNames(filePath: string): string[] {
  const fd = fs.openSync(filePath, 'r');
  try {
    const header = Buffer.alloc(20);
    fs.readSync(fd, header, 0, 20, 0);
    expect(header.subarray(0, 4).toString('ascii')).toBe('glTF');
    const jsonLength = header.readUInt32LE(12);
    const jsonChunk = Buffer.alloc(jsonLength);
    fs.readSync(fd, jsonChunk, 0, jsonLength, 20);
    const gltf = JSON.parse(jsonChunk.toString('utf8'));
    return (gltf.animations ?? []).map((animation: { name?: string }) => animation.name ?? '');
  } finally {
    fs.closeSync(fd);
  }
}

describe('recognition model registry', () => {
  it('ships the 79-class baseline as the default so the UI scope matches the running graph', () => {
    expect(DEFAULT_MODEL_ID).toBe('baseline');
    expect(MODEL_REGISTRY[DEFAULT_MODEL_ID].classCount).toBe(79);
    expect(MODEL_REGISTRY[DEFAULT_MODEL_ID].scopeChip).toBe('79 ASL classes');
    // The 3-class pilot stays available as the fallback the user can select.
    expect(MODEL_REGISTRY.pilot.classCount).toBe(3);
    // The default model recognises more signs than the avatar can animate; the
    // gap must stay declared so the UI can say so.
    expect(MODEL_REGISTRY[DEFAULT_MODEL_ID].avatarClipLabels.length).toBeLessThan(79);
  });

  it('binds each model to its own artifact, class count and stabilizer thresholds', () => {
    expect(MODEL_REGISTRY.pilot.classCount).toBe(3);
    expect(MODEL_REGISTRY.baseline.classCount).toBe(79);
    expect(MODEL_REGISTRY.pilot.modelUrl).not.toBe(MODEL_REGISTRY.baseline.modelUrl);
    expect(MODEL_REGISTRY.pilot.vocab).not.toBe(MODEL_REGISTRY.baseline.vocab);
    // The 79-class model must not inherit the 3-class commit thresholds.
    expect(MODEL_REGISTRY.baseline.stabilizerConfig).not.toEqual(MODEL_REGISTRY.pilot.stabilizerConfig);
    expect(vocabClassCount(getModelSpec('baseline').vocab)).toBe(79);
  });

  it('matches the 79-class app vocab to the training-time class index mapping', () => {
    expect(fs.existsSync(classIndexMappingPath)).toBe(true);
    const raw = JSON.parse(fs.readFileSync(classIndexMappingPath, 'utf8')) as Record<
      string,
      { class_index: number; canonical_name: string }
    >;
    const expected: Record<number, string> = {};
    for (const entry of Object.values(raw)) expected[entry.class_index] = entry.canonical_name;

    expect(Object.keys(expected)).toHaveLength(79);
    expect(Object.keys(ASL_VOCAB)).toHaveLength(79);
    for (let index = 0; index < 79; index += 1) {
      expect(ASL_VOCAB[index]).toBe(expected[index]);
    }
    // Class order must not be inferred alphabetically from the frozen 100-sign
    // vocabulary: index 0 is HELLO, 9 is YES, 10 is NO.
    expect(ASL_VOCAB[0]).toBe('HELLO');
    expect(ASL_VOCAB[9]).toBe('YES');
    expect(ASL_VOCAB[10]).toBe('NO');
    expect(ASL_VOCAB[78]).toBe('COLD');
  });

  it('matches the 3-class pilot vocab to the pilot training mapping', () => {
    expect(fs.existsSync(pilotMappingPath)).toBe(true);
    const raw = JSON.parse(fs.readFileSync(pilotMappingPath, 'utf8')) as Record<
      string,
      { class_index: number; canonical_name: string }
    >;
    const expected: Record<number, string> = {};
    for (const entry of Object.values(raw)) expected[entry.class_index] = entry.canonical_name;
    expect(expected).toEqual({ 0: 'HELLO', 1: 'YES', 2: 'NO' });
    expect(PILOT_VOCAB).toEqual(expected);
  });

  it('refuses to label predictions when the output size and class map disagree', () => {
    const logits79 = new Float32Array(79);
    const logits3 = new Float32Array(3);
    expect(assertModelOutputSize(ASL_VOCAB, logits79.length)).toBe(79);
    expect(assertModelOutputSize(PILOT_VOCAB, logits3.length)).toBe(3);
    // The two failure directions the audit called out explicitly.
    expect(() => assertModelOutputSize(PILOT_VOCAB, logits79.length)).toThrow(/79 logits.*3 classes/);
    expect(() => assertModelOutputSize(ASL_VOCAB, logits3.length)).toThrow(/3 logits.*79 classes/);
  });

  it('documents the real avatar coverage of the production GLB', () => {
    expect(fs.existsSync(productionGlbPath)).toBe(true);
    const clips = readGlbAnimationNames(productionGlbPath);
    const clipLabels = avatarClipLabelsFromClipNames(clips);
    expect(clipLabels.sort()).toEqual(['HELLO', 'NO', 'YES']);
    expect(getModelSpec('baseline').avatarClipLabels.slice().sort()).toEqual(['HELLO', 'NO', 'YES']);
    expect(hasAvatarClip('HELLO', clipLabels)).toBe(true);
    expect(hasAvatarClip('GOOD', clipLabels)).toBe(false);
    // 3 of 79 baseline classes have an animation; the other 76 are text only.
    expect(clipLabels.length).toBe(3);
  });
});
