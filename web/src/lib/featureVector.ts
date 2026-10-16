import { FACE_LANDMARK_COUNT, FEATURE_DIMENSION, HAND_LANDMARK_COUNT, OFFSETS, POSE_LANDMARK_COUNT, type CanonicalFrame, type GroupName, type HandObservation, type HandSlot, type Point3, type PosePoint, type RawLandmarkInput, emptyPresence } from './contracts';

const finite = (value: number | undefined): number | undefined => value !== undefined && Number.isFinite(value) ? value : undefined;
const validPoint3 = (point: Point3 | undefined): point is Point3 => point !== undefined && finite(point.x) !== undefined && finite(point.y) !== undefined && finite(point.z) !== undefined;

/** The input frame is unmirrored. Preview-only CSS mirroring never affects coordinates. */
export function canonicalSlotForMediaPipeLabel(label: string): HandSlot | 'unassigned' {
  if (label === 'Left') return 'rightHand';
  if (label === 'Right') return 'leftHand';
  return 'unassigned';
}

function writePoint3(target: Float32Array, start: number, point: Point3): void {
  target[start] = point.x; target[start + 1] = point.y; target[start + 2] = point.z;
}
function collectHand(target: Float32Array, offset: number, hand: HandObservation | undefined): boolean {
  if (!hand || hand.landmarks.length !== HAND_LANDMARK_COUNT || !hand.landmarks.every(validPoint3)) return false;
  hand.landmarks.forEach((point, index) => writePoint3(target, offset + index * 3, point));
  return true;
}
function collectPose(target: Float32Array, pose: PosePoint[] | undefined): boolean {
  if (!pose || pose.length !== POSE_LANDMARK_COUNT) return false;
  for (let index = 0; index < POSE_LANDMARK_COUNT; index += 1) {
    const point = pose[index];
    if (!validPoint3(point) || finite(point.visibility) === undefined || finite(point.presence) === undefined) return false;
    const start = OFFSETS.pose + index * 5;
    writePoint3(target, start, point); target[start + 3] = point.visibility!; target[start + 4] = point.presence!;
  }
  return true;
}
function collectFace(target: Float32Array, face: Point3[] | undefined): boolean {
  if (!face || face.length < FACE_LANDMARK_COUNT || !face.slice(0, FACE_LANDMARK_COUNT).every(validPoint3)) return false;
  face.slice(0, FACE_LANDMARK_COUNT).forEach((point, index) => writePoint3(target, OFFSETS.face + index * 3, point));
  return true;
}

/** Frozen V2 order: pose is 33 interleaved [x, y, z, visibility, presence] rows. */
export function assembleCanonicalFrame(input: RawLandmarkInput): CanonicalFrame {
  const raw = new Float32Array(FEATURE_DIMENSION);
  const presence = emptyPresence(); const invalidGroups: GroupName[] = [];
  const handAssignments = input.hands.map((hand) => ({ mediaPipeLabel: hand.label, canonicalSlot: canonicalSlotForMediaPipeLabel(hand.label) }));
  const assigned = new Map<HandSlot, HandObservation>();
  for (const hand of input.hands) { const slot = canonicalSlotForMediaPipeLabel(hand.label); if (slot !== 'unassigned' && !assigned.has(slot)) assigned.set(slot, hand); }
  for (const [slot, offset] of [['leftHand', OFFSETS.leftHand], ['rightHand', OFFSETS.rightHand]] as const) {
    const hand = assigned.get(slot); if (hand) { presence[slot] = collectHand(raw, offset, hand); if (!presence[slot]) invalidGroups.push(slot); }
  }
  presence.pose = collectPose(raw, input.pose); if (input.pose && !presence.pose) invalidGroups.push('pose');
  presence.face = collectFace(raw, input.face); if (input.face && !presence.face) invalidGroups.push('face');
  return { raw, presence, invalidGroups, handAssignments };
}
export function countNonFinite(values: Float32Array): { nan: number; inf: number } {
  let nan = 0; let inf = 0;
  for (const value of values) { if (Number.isNaN(value)) nan += 1; else if (!Number.isFinite(value)) inf += 1; }
  return { nan, inf };
}
