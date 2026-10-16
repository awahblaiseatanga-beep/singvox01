export interface AvatarCapabilities {
  hasSkeleton: boolean;
  isStructuralValid: boolean;
  isSigningValid: boolean;
  hasHips: boolean;
  hasSpine: boolean;
  hasHead: boolean;
  hasLeftArm: boolean;
  hasRightArm: boolean;
  hasLeftHand: boolean;
  hasRightHand: boolean;
  hasLeftFingers: boolean;
  hasRightFingers: boolean;
  hasFaceMorphTargets: boolean;
  hasHeadBone: boolean;
  hasAnimationClips: boolean;
  boneCount: number;
  meshCount: number;
  animationCount: number;
}

export function createEmptyCapabilities(): AvatarCapabilities {
  return {
    hasSkeleton: false,
    isStructuralValid: false,
    isSigningValid: false,
    hasHips: false,
    hasSpine: false,
    hasHead: false,
    hasLeftArm: false,
    hasRightArm: false,
    hasLeftHand: false,
    hasRightHand: false,
    hasLeftFingers: false,
    hasRightFingers: false,
    hasFaceMorphTargets: false,
    hasHeadBone: false,
    hasAnimationClips: false,
    boneCount: 0,
    meshCount: 0,
    animationCount: 0
  };
}
