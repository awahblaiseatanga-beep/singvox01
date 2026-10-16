export const CanonicalBones = {
  // Required core
  Hips: "mixamorig4Hips",
  Spine: "mixamorig4Spine",
  Spine1: "mixamorig4Spine1",
  Spine2: "mixamorig4Spine2",
  Neck: "mixamorig4Neck",
  Head: "mixamorig4Head",

  // Arms Left
  LeftShoulder: "mixamorig4LeftShoulder",
  LeftArm: "mixamorig4LeftArm",
  LeftForeArm: "mixamorig4LeftForeArm",
  LeftHand: "mixamorig4LeftHand",

  // Arms Right
  RightShoulder: "mixamorig4RightShoulder",
  RightArm: "mixamorig4RightArm",
  RightForeArm: "mixamorig4RightForeArm",
  RightHand: "mixamorig4RightHand",

  // Left Fingers
  LeftHandThumb1: "mixamorig4LeftHandThumb1",
  LeftHandThumb2: "mixamorig4LeftHandThumb2",
  LeftHandThumb3: "mixamorig4LeftHandThumb3",
  LeftHandIndex1: "mixamorig4LeftHandIndex1",
  LeftHandIndex2: "mixamorig4LeftHandIndex2",
  LeftHandIndex3: "mixamorig4LeftHandIndex3",
  LeftHandIndex4: "mixamorig4LeftHandIndex4",
  LeftHandMiddle1: "mixamorig4LeftHandMiddle1",
  LeftHandMiddle2: "mixamorig4LeftHandMiddle2",
  LeftHandMiddle3: "mixamorig4LeftHandMiddle3",
  LeftHandRing1: "mixamorig4LeftHandRing1",
  LeftHandRing2: "mixamorig4LeftHandRing2",
  LeftHandRing3: "mixamorig4LeftHandRing3",
  LeftHandPinky1: "mixamorig4LeftHandPinky1",
  LeftHandPinky2: "mixamorig4LeftHandPinky2",
  LeftHandPinky3: "mixamorig4LeftHandPinky3",

  // Right Fingers
  RightHandThumb1: "mixamorig4RightHandThumb1",
  RightHandThumb2: "mixamorig4RightHandThumb2",
  RightHandThumb3: "mixamorig4RightHandThumb3",
  RightHandIndex1: "mixamorig4RightHandIndex1",
  RightHandIndex2: "mixamorig4RightHandIndex2",
  RightHandIndex3: "mixamorig4RightHandIndex3",
  RightHandIndex4: "mixamorig4RightHandIndex4",
  RightHandMiddle1: "mixamorig4RightHandMiddle1",
  RightHandMiddle2: "mixamorig4RightHandMiddle2",
  RightHandMiddle3: "mixamorig4RightHandMiddle3",
  RightHandRing1: "mixamorig4RightHandRing1",
  RightHandRing2: "mixamorig4RightHandRing2",
  RightHandRing3: "mixamorig4RightHandRing3",
  RightHandPinky1: "mixamorig4RightHandPinky1",
  RightHandPinky2: "mixamorig4RightHandPinky2",
  RightHandPinky3: "mixamorig4RightHandPinky3",
};

export const OptionalBones = {
  // Can add face bones later
};

export interface ValidationReport {
  isValid: boolean;
  missingRequired: string[];
  missingOptional: string[];
  duplicateMappings: string[];
  unexpectedIssues: string[];
}

export function validateBoneMap(object3D: import("three").Object3D): ValidationReport {
  const missingRequired: string[] = [];
  const missingOptional: string[] = [];
  
  const allNodes = new Set<string>();
  object3D.traverse((child: import("three").Object3D) => {
    if ((child as import("three").Bone).isBone) {
       allNodes.add(child.name.replace(/[:_]/g, ''));
    }
  });

  for (const [canonical, mixamoName] of Object.entries(CanonicalBones)) {
    const sanitized = mixamoName.replace(/[:_]/g, '');
    if (!allNodes.has(sanitized)) {
      missingRequired.push(canonical);
    }
  }

  for (const [canonical, mixamoName] of Object.entries(OptionalBones)) {
    if (!allNodes.has(mixamoName as string)) {
      missingOptional.push(canonical as string);
    }
  }

  const isValid = missingRequired.length === 0;

  return {
    isValid,
    missingRequired,
    missingOptional,
    duplicateMappings: [] as string[], // not applicable right now due to Dictionary
    unexpectedIssues: [] as string[]
  };
}
