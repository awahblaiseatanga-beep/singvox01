export type HandSide = "left" | "right";

export type FingerName = "thumb" | "index" | "middle" | "ring" | "pinky";

export type FingerJoint = 1 | 2 | 3;

export interface ThumbPose {
  flex: number;      // 0..1  (Extended -> Bent inward)
  abduction: number; // -1..1 (Spread away from palm -> Squeezed against palm)
}

export interface FingerPose {
  curl: number;      // 0..1 (Extended -> Fist curl)
  spread: number;    // -1..1 (Splayed outward -> Splayed inward / neutral 0)
}

export interface WristPose {
  rotationX: number; // Radians offset from neutral
  rotationY: number; // Radians offset from neutral
  rotationZ: number; // Radians offset from neutral
}

export interface HandPose {
  thumb: ThumbPose;
  index: FingerPose;
  middle: FingerPose;
  ring: FingerPose;
  pinky: FingerPose;
  wrist?: WristPose;
}

export function clamp(val: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, val));
}
