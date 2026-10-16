import * as THREE from 'three';
import { AvatarController } from './AvatarController';

export type AnatomicalAnchorName =
  | "forehead" | "eyes" | "nose" | "mouth" | "chin"
  | "sternum" | "chest" | "belly"
  | "leftShoulder" | "rightShoulder"
  | "leftHip" | "rightHip";

export class AnatomicalAnchors {
  private avatar: AvatarController;

  constructor(avatar: AvatarController) {
    this.avatar = avatar;
  }

  public getAnchorWorldPosition(name: AnatomicalAnchorName, customOffset?: THREE.Vector3): THREE.Vector3 | null {
    let parentBone: THREE.Bone | undefined;
    let fallbackOffset = new THREE.Vector3(0, 0, 0);

    // Coordinate assumptions: 
    // ALL OFFSETS ARE DEFINED IN AVATAR BODY SPACE (Meters).
    // X = Left/Right, Y = Up/Down, Z = Forward/Backward
    // By using Body Space instead of Local Bone Space, we are immune to Mixamo's erratic
    // internal bone rotation axes and massive unapplied hierarchy scales (e.g. bone scale = 100).
    switch (name) {
      case 'forehead':
        parentBone = this.avatar.getBone('Head');
        fallbackOffset.set(0, 0.08, 0.16); // Up and significantly forward to surface cleanly
        break;
      case 'eyes':
        parentBone = this.avatar.getBone('Head');
        fallbackOffset.set(0, 0.03, 0.16);
        break;
      case 'nose':
        parentBone = this.avatar.getBone('Head');
        fallbackOffset.set(0, 0.0, 0.16);
        break;
      case 'mouth':
        parentBone = this.avatar.getBone('Head');
        fallbackOffset.set(0, -0.04, 0.15);
        break;
      case 'chin':
        parentBone = this.avatar.getBone('Head');
        fallbackOffset.set(0, -0.08, 0.14);
        break;
      case 'sternum':
        parentBone = this.avatar.getBone('Spine2');
        fallbackOffset.set(0, 0.05, 0.22); // Push boundary outwards clearing female breasts geometry naturally
        break;
      case 'chest':
        parentBone = this.avatar.getBone('Spine2');
        fallbackOffset.set(0, 0, 0.22); // Target clears native hand thickness under default wrist tracking
        break;
      case 'belly':
        parentBone = this.avatar.getBone('Spine');
        fallbackOffset.set(0, 0, 0.22); // Safely forward of pelvic arch
        break;
      case 'leftShoulder':
        parentBone = this.avatar.getBone('LeftShoulder');
        fallbackOffset.set(0.14, 0, 0.10); // Spread laterally and slightly further forward to prevent bicep crushing
        break;
      case 'rightShoulder':
        parentBone = this.avatar.getBone('RightShoulder');
        fallbackOffset.set(-0.14, 0, 0.10); 
        break;
      case 'leftHip':
        parentBone = this.avatar.getBone('Hips');
        fallbackOffset.set(0.14, -0.05, 0.12); // Pushed heavily forward (+Z) out of the thigh intersection zone
        break;
      case 'rightHip':
        parentBone = this.avatar.getBone('Hips');
        fallbackOffset.set(-0.14, -0.05, 0.12); 
        break;
    }

    if (!parentBone) {
      return null;
    }

    // Explicitly force full hierarchy cascade evaluation resolving lazy GLTF tree bindings natively
    if (this.avatar.rootScene) {
        this.avatar.rootScene.updateMatrixWorld(true);
    }

    // 1. Obtain strict absolute world position of the Target Bone.
    const worldPos = new THREE.Vector3();
    parentBone.getWorldPosition(worldPos);

    const finalOffset = customOffset || fallbackOffset;

    // 2. We expressly apply Body Space offsets isolated from native Bone Rotations.
    if (finalOffset.lengthSq() > 0 && this.avatar.rootScene) {
        const rootQuat = new THREE.Quaternion();
        this.avatar.rootScene.getWorldQuaternion(rootQuat);

        // Transform the additive meters by simply rotating it to match Root orientation (not scale!)
        const worldOffset = finalOffset.clone().applyQuaternion(rootQuat);
        worldPos.add(worldOffset);
    }

    return worldPos;
  }
}
