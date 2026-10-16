import * as THREE from 'three';
import { FingerName, HandSide, clamp, FingerPose } from './HandModel';
import { AvatarController } from './AvatarController';

export class FingerController {
  private baseQuaternions: Map<number, THREE.Quaternion> = new Map();
  private joints: Map<number, THREE.Bone> = new Map();
  public readonly side: HandSide;
  public readonly name: FingerName;

  private currentCurl: number = 0;
  private currentSpread: number = 0;

  constructor(side: HandSide, name: FingerName, avatar: AvatarController) {
    this.side = side;
    this.name = name;

    const prefix = side === 'left' ? 'LeftHand' : 'RightHand';
    const capName = name.charAt(0).toUpperCase() + name.slice(1);

    for (let i = 1; i <= 3; i++) {
       const bone = avatar.getBone(`${prefix}${capName}${i}`);
       if (bone) {
         this.joints.set(i, bone);
         this.baseQuaternions.set(i, bone.quaternion.clone());
       }
    }
  }

  public setCurl(amount: number) {
    this.currentCurl = clamp(amount, 0, 1);
    this.update();
  }

  public setSpread(amount: number) {
    this.currentSpread = clamp(amount, -1, 1);
    this.update();
  }

  public setPose(pose: FingerPose) {
    this.currentCurl = clamp(pose.curl, 0, 1);
    this.currentSpread = clamp(pose.spread, -1, 1);
    this.update();
  }

  public getSnapshot(): FingerPose {
    return { curl: this.currentCurl, spread: this.currentSpread };
  }

  public update() {
    const curlSign = this.side === 'left' ? 1 : -1;
    const maxCurl = (Math.PI / 2) * curlSign;

    const spreadSign = this.side === 'left' ? 1 : -1;
    const maxSpread = (Math.PI / 8) * spreadSign;

    const curlLocal = new THREE.Quaternion();
    const spreadLocal = new THREE.Quaternion();

    for (let i = 1; i <= 3; i++) {
       const bone = this.joints.get(i);
       const restQuat = this.baseQuaternions.get(i);
       if (!bone || !restQuat) continue;

       // Base joints get spread, subsequent joints just cascade curl
       const curlRatio = (i === 1) ? 0.8 : 1.0;
       curlLocal.setFromAxisAngle(new THREE.Vector3(0, 0, 1), this.currentCurl * maxCurl * curlRatio);

       // Mixamo canonical namespace uses Y or X for spread
       if (i === 1) {
          spreadLocal.setFromAxisAngle(new THREE.Vector3(0, 1, 0), this.currentSpread * maxSpread);
          const combined = new THREE.Quaternion().multiplyQuaternions(spreadLocal, curlLocal);
          bone.quaternion.copy(restQuat).multiply(combined);
       } else {
          bone.quaternion.copy(restQuat).multiply(curlLocal);
       }
    }
  }

  public reset() {
     this.currentCurl = 0;
     this.currentSpread = 0;
     this.update();
  }
}
