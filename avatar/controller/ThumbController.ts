import * as THREE from 'three';
import { HandSide, clamp, ThumbPose } from './HandModel';
import { AvatarController } from './AvatarController';

export class ThumbController {
  private baseQuaternions: Map<number, THREE.Quaternion> = new Map();
  private joints: Map<number, THREE.Bone> = new Map();
  public readonly side: HandSide;

  private currentFlex: number = 0;
  private currentAbduction: number = 0;

  constructor(side: HandSide, avatar: AvatarController) {
    this.side = side;
    const prefix = side === 'left' ? 'LeftHand' : 'RightHand';

    for (let i = 1; i <= 3; i++) {
       const bone = avatar.getBone(`${prefix}Thumb${i}`);
       if (bone) {
         this.joints.set(i, bone);
         this.baseQuaternions.set(i, bone.quaternion.clone());
       }
    }
  }

  public setFlex(amount: number) {
    this.currentFlex = clamp(amount, 0, 1);
    this.update();
  }

  public setAbduction(amount: number) {
    this.currentAbduction = clamp(amount, -1, 1);
    this.update();
  }

  public setPose(pose: ThumbPose) {
    this.currentFlex = clamp(pose.flex, 0, 1);
    this.currentAbduction = clamp(pose.abduction, -1, 1);
    this.update();
  }

  public getSnapshot(): ThumbPose {
    return { flex: this.currentFlex, abduction: this.currentAbduction };
  }

  public update() {
    // Thumb flexion logic operates on slightly different axes dynamically
    const flexSign = this.side === 'left' ? 1 : -1;
    const maxFlex = (Math.PI / 2.5) * flexSign;

    const abdSign = this.side === 'left' ? 1 : -1;
    const maxAbd = (Math.PI / 4) * abdSign;

    const flexLocal = new THREE.Quaternion();
    const abdLocal = new THREE.Quaternion();

    for (let i = 1; i <= 3; i++) {
       const bone = this.joints.get(i);
       const restQuat = this.baseQuaternions.get(i);
       if (!bone || !restQuat) continue;

       // Flexion wraps Z/X primarily
       const flexRatio = i === 1 ? 0.3 : 1.0;
       flexLocal.setFromAxisAngle(new THREE.Vector3(0, 0, 1), this.currentFlex * maxFlex * flexRatio);

       if (i === 1) {
          abdLocal.setFromAxisAngle(new THREE.Vector3(0, 1, 0), this.currentAbduction * maxAbd);
          const combined = new THREE.Quaternion().multiplyQuaternions(abdLocal, flexLocal);
          bone.quaternion.copy(restQuat).multiply(combined);
       } else {
          bone.quaternion.copy(restQuat).multiply(flexLocal);
       }
    }
  }

  public reset() {
     this.currentFlex = 0;
     this.currentAbduction = 0;
     this.update();
  }
}
