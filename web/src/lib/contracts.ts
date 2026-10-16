export const HAND_LANDMARK_COUNT = 21;
export const POSE_LANDMARK_COUNT = 33;
export const FACE_LANDMARK_COUNT = 25;
export const FEATURE_DIMENSION = 366;
export const SEQUENCE_LENGTH = 60;
export const OFFSETS = { leftHand: 0, rightHand: 63, pose: 126, face: 291 } as const;
export const V2_SCALARS = {
  leftHand: 0.3886975049972534,
  rightHand: 0.3666480779647827,
  poseXyz: 1.8127285242080688,
  face: 0.3139561712741852,
} as const;

export type Point3 = { x: number; y: number; z: number };
export type PosePoint = Point3 & { visibility?: number; presence?: number };
export type HandSlot = 'leftHand' | 'rightHand';
export type GroupName = HandSlot | 'pose' | 'face';
export type GroupPresence = Record<GroupName, boolean>;
export type HandObservation = { label: string; landmarks: Point3[] };
export type RawLandmarkInput = { hands: HandObservation[]; pose: PosePoint[] | undefined; face: Point3[] | undefined };
export type HandAssignment = { mediaPipeLabel: string; canonicalSlot: HandSlot | 'unassigned' };
export type CanonicalFrame = { raw: Float32Array; presence: GroupPresence; invalidGroups: GroupName[]; handAssignments: HandAssignment[] };
export const emptyPresence = (): GroupPresence => ({ leftHand: false, rightHand: false, pose: false, face: false });
