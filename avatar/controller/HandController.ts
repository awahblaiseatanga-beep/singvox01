import * as THREE from 'three';
import { HandSide, HandPose, WristPose } from './HandModel';
import { FingerController } from './FingerController';
import { ThumbController } from './ThumbController';
import { AvatarController } from './AvatarController';

export class HandController {
  public readonly side: HandSide;
  
  public readonly thumb: ThumbController;
  public readonly index: FingerController;
  public readonly middle: FingerController;
  public readonly ring: FingerController;
  public readonly pinky: FingerController;

  private wristBone: THREE.Bone | null = null;
  private wristBaseQuat: THREE.Quaternion | null = null;
  private currentWrist: WristPose = { rotationX: 0, rotationY: 0, rotationZ: 0 };

  constructor(side: HandSide, avatar: AvatarController) {
    this.side = side;

    this.thumb = new ThumbController(side, avatar);
    this.index = new FingerController(side, 'index', avatar);
    this.middle = new FingerController(side, 'middle', avatar);
    this.ring = new FingerController(side, 'ring', avatar);
    this.pinky = new FingerController(side, 'pinky', avatar);

    const prefix = side === 'left' ? 'LeftHand' : 'RightHand';
    const wrist = avatar.getBone(prefix);
    if (wrist) {
      this.wristBone = wrist;
      this.wristBaseQuat = wrist.quaternion.clone();
    }
  }

  public update() {
    this.thumb.update();
    this.index.update();
    this.middle.update();
    this.ring.update();
    this.pinky.update();
    
    // Stomp wrist
    if (this.wristBone && this.wristBaseQuat) {
       const euler = new THREE.Euler(this.currentWrist.rotationX, this.currentWrist.rotationY, this.currentWrist.rotationZ, 'XYZ');
       const externalRot = new THREE.Quaternion().setFromEuler(euler);
       this.wristBone.quaternion.copy(this.wristBaseQuat).multiply(externalRot);
    }
  }

  public setWristRotation(rotX: number, rotY: number, rotZ: number) {
    this.currentWrist = { rotationX: rotX, rotationY: rotY, rotationZ: rotZ };
    this.update();
  }

  public setPose(pose: HandPose) {
    this.thumb.setPose(pose.thumb);
    this.index.setPose(pose.index);
    this.middle.setPose(pose.middle);
    this.ring.setPose(pose.ring);
    this.pinky.setPose(pose.pinky);
    if (pose.wrist) {
       this.setWristRotation(pose.wrist.rotationX, pose.wrist.rotationY, pose.wrist.rotationZ);
    }
  }

  public snapshot(): HandPose {
    return {
      thumb: this.thumb.getSnapshot(),
      index: this.index.getSnapshot(),
      middle: this.middle.getSnapshot(),
      ring: this.ring.getSnapshot(),
      pinky: this.pinky.getSnapshot(),
      wrist: { ...this.currentWrist }
    };
  }

  public restore(pose: HandPose) {
    this.setPose(pose);
  }

  public reset() {
    this.thumb.reset();
    this.index.reset();
    this.middle.reset();
    this.ring.reset();
    this.pinky.reset();
    this.setWristRotation(0, 0, 0);
  }
}
