import { FEATURE_DIMENSION, OFFSETS, POSE_LANDMARK_COUNT, V2_SCALARS } from './contracts';

/** Exact Python behavior: center on shoulders 11/12 and scale by their 3-D distance. */
export function shoulderCenter(raw: Float32Array): Float32Array {
  const output = new Float32Array(raw);
  const poseHasSignal = output.slice(OFFSETS.pose, OFFSETS.face).some((value) => value !== 0);
  const left = OFFSETS.pose + 11 * 5; const right = OFFSETS.pose + 12 * 5;
  const shouldersPresent = [left, right].every((start) => output[start] !== 0 || output[start + 1] !== 0 || output[start + 2] !== 0);
  if (!poseHasSignal || !shouldersPresent) return output;
  const centerX = (output[left] + output[right]) / 2; const centerY = (output[left + 1] + output[right + 1]) / 2;
  const distance = Math.hypot(output[left] - output[right], output[left + 1] - output[right + 1], output[left + 2] - output[right + 2]);
  const scale = distance > 0.01 ? distance : 1;
  const normalize = (start: number) => { if (output[start] !== 0 || output[start + 1] !== 0 || output[start + 2] !== 0) { output[start] = (output[start] - centerX) / scale; output[start + 1] = (output[start + 1] - centerY) / scale; output[start + 2] /= scale; } };
  for (let start = OFFSETS.leftHand; start < OFFSETS.pose; start += 3) normalize(start);
  for (let landmark = 0; landmark < POSE_LANDMARK_COUNT; landmark += 1) normalize(OFFSETS.pose + landmark * 5);
  for (let start = OFFSETS.face; start < FEATURE_DIMENSION; start += 3) normalize(start);
  return output;
}
/** Frozen V2 scaling: visibility and presence (+3/+4) are not scaled. */
export function applyV2Normalization(raw: Float32Array): Float32Array {
  const output = shoulderCenter(raw);
  for (let index = OFFSETS.leftHand; index < OFFSETS.rightHand; index += 1) output[index] /= V2_SCALARS.leftHand;
  for (let index = OFFSETS.rightHand; index < OFFSETS.pose; index += 1) output[index] /= V2_SCALARS.rightHand;
  for (let landmark = 0; landmark < POSE_LANDMARK_COUNT; landmark += 1) { const start = OFFSETS.pose + landmark * 5; output[start] /= V2_SCALARS.poseXyz; output[start + 1] /= V2_SCALARS.poseXyz; output[start + 2] /= V2_SCALARS.poseXyz; }
  for (let index = OFFSETS.face; index < FEATURE_DIMENSION; index += 1) output[index] /= V2_SCALARS.face;
  return output;
}
