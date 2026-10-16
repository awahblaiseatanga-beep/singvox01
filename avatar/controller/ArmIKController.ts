import * as THREE from 'three';
import { AvatarController } from './AvatarController';
import { clamp } from './HandModel';

export class ArmIKController {
  private avatar: AvatarController;
  public readonly side: 'left' | 'right';

  private upperArm: THREE.Bone | null = null;
  private foreArm: THREE.Bone | null = null;
  private hand: THREE.Bone | null = null;
  private indexTip: THREE.Bone | null = null;
  private indexOffsetLocal = new THREE.Vector3();

  private upperArmRestQuat = new THREE.Quaternion();
  private foreArmRestQuat = new THREE.Quaternion();

  private L1: number = 0;
  private L2: number = 0;

  public solverActive = false;
  public ikMode: 'wrist' | 'indexFingertip' = 'wrist';
  private targetWorld = new THREE.Vector3();
  private virtualTarget = new THREE.Vector3();
  
  public fingerDirectionTarget: THREE.Vector3 | null = null;
  public palmNormalTarget: THREE.Vector3 | null = null;
  
  public debugS = new THREE.Vector3();
  public debugE = new THREE.Vector3();
  public debugW = new THREE.Vector3();
  public debugPole = new THREE.Vector3();
  public currentPoleWorld: THREE.Vector3 | null = null;

  // Cached scratchpad natively minimizing allocations
  private S = new THREE.Vector3();
  private BaseE = new THREE.Vector3();
  private BaseW = new THREE.Vector3();
  private naturalPole = new THREE.Vector3();
  private armDir = new THREE.Vector3();
  private projPole = new THREE.Vector3();
  private eCenter = new THREE.Vector3();
  private E = new THREE.Vector3();
  private currentPos = new THREE.Vector3();
  private targetDir = new THREE.Vector3();
  private childRestPos = new THREE.Vector3();
  private restDir = new THREE.Vector3();
  private axis = new THREE.Vector3();
  private deltaQuat = new THREE.Quaternion();
  private currentQuat = new THREE.Quaternion();
  private parentWorldQuat = new THREE.Quaternion();

  constructor(side: 'left' | 'right', avatar: AvatarController) {
    this.side = side;
    this.avatar = avatar;

    const prefix = side === 'left' ? 'Left' : 'Right';
    const upArm = avatar.getBone(`${prefix}Arm`);
    const fArm = avatar.getBone(`${prefix}ForeArm`);
    const h = avatar.getBone(`${prefix}Hand`);

    if (upArm && fArm && h) {
      this.upperArm = upArm;
      this.foreArm = fArm;
      this.hand = h;

      const index4 = avatar.getBone(`${prefix}HandIndex4`);
      const index3 = avatar.getBone(`${prefix}HandIndex3`);
      const index2 = avatar.getBone(`${prefix}HandIndex2`);

      if (index4 && index3 && index2) {
          this.indexTip = index4;
          
          // The leaf GLTF bone 'Index4' structurally returns its HEAD (the DIP joint) natively.
          // To track the explicit fingertip, we evaluate the anatomical progression from Index3 -> Index4
          const p3 = new THREE.Vector3(); index3.getWorldPosition(p3);
          const p4 = new THREE.Vector3(); index4.getWorldPosition(p4);
          
          // Index4 length is naturally ~80% of Index3 phalanx
          const dist = p4.distanceTo(p3) * 0.8;
          
          const restDirWorld = new THREE.Vector3().subVectors(p4, p3).normalize();
          
          const idx4RestWorldQuat = new THREE.Quaternion();
          index4.getWorldQuaternion(idx4RestWorldQuat);
          idx4RestWorldQuat.invert();
          
          const relativeLocalAxes = restDirWorld.applyQuaternion(idx4RestWorldQuat);
          this.indexOffsetLocal.copy(relativeLocalAxes).normalize().multiplyScalar(dist);
      } else if (index3 && index2) {
          this.indexTip = index3;
          
          // We derive a stable Local offset explicitly evaluated from the Index2 -> Index3 anatomical vector
          // Then we cast that vector directly into Index3's uncurled local coordinates.
          const p2 = new THREE.Vector3(); index2.getWorldPosition(p2);
          const p3 = new THREE.Vector3(); index3.getWorldPosition(p3);
          const dist = p3.distanceTo(p2) * 0.8; 
          
          // True anatomical world vector of the phalanx
          const restDirWorld = new THREE.Vector3().subVectors(p3, p2).normalize();
          
          // We translate the world vector smoothly into the *rest* local coordinates of Index3 itself. 
          // Using applyQuaternion with the inverted index3 world rotation maps the forward progression 
          const idx3RestWorldQuat = new THREE.Quaternion();
          index3.getWorldQuaternion(idx3RestWorldQuat);
          idx3RestWorldQuat.invert();
          
          const relativeLocalAxes = restDirWorld.applyQuaternion(idx3RestWorldQuat);
          
          this.indexOffsetLocal.copy(relativeLocalAxes).normalize().multiplyScalar(dist);
      }

      this.upperArmRestQuat.copy(upArm.quaternion);
      this.foreArmRestQuat.copy(fArm.quaternion);
    }
  }

  public setTarget(target: THREE.Vector3, poleWorld?: THREE.Vector3, mode: 'wrist' | 'indexFingertip' = 'wrist', fingerDirection?: THREE.Vector3, palmNormal?: THREE.Vector3) {
    if (target.lengthSq() < 0.0001) {
        this.solverActive = false; // Cleanly disabling tracker avoiding snap-to-chest zero failures
        return;
    }
    this.targetWorld.copy(target);
    this.currentPoleWorld = poleWorld || null;
    this.ikMode = mode;
    this.solverActive = true;

    if (fingerDirection && fingerDirection.lengthSq() > 0.0001) {
        this.fingerDirectionTarget = new THREE.Vector3().copy(fingerDirection).normalize();
    } else {
        this.fingerDirectionTarget = null;
    }

    if (palmNormal && palmNormal.lengthSq() > 0.0001) {
        this.palmNormalTarget = new THREE.Vector3().copy(palmNormal).normalize();
    } else {
        this.palmNormalTarget = null;
    }
  }

  public reset() {
    this.solverActive = false;
    if (this.upperArm && this.foreArm) {
      this.upperArm.quaternion.copy(this.upperArmRestQuat);
      this.foreArm.quaternion.copy(this.foreArmRestQuat);
    }
  }

  public getActualFingertipPosition(out: THREE.Vector3): boolean {
    if (!this.indexTip) return false;
    this.indexTip.getWorldPosition(out);
    if (this.indexOffsetLocal.lengthSq() > 0) {
        out.copy(this.indexOffsetLocal).applyMatrix4(this.indexTip.matrixWorld);
    }
    return true;
  }

  public update() {
    if (!this.solverActive || !this.upperArm || !this.foreArm || !this.hand) return;

    // Phase D: Stable Anatomical Elbow Pole using body-relative coordinate frame
    // We use the Avatar's root orientation to keep the pole independent of target position
    // Left arm natural bend is outward (+X), somewhat backward (-Z), and slightly down (-Y).
    const rootSpine = this.avatar.getBone('Spine') || this.avatar.rootScene!;
    const rootWorldQuat = new THREE.Quaternion();
    rootSpine.getWorldQuaternion(rootWorldQuat);
    const poleLocal = new THREE.Vector3(this.side === 'left' ? 1 : -1, -0.5, -0.2).normalize();
    this.naturalPole.copy(poleLocal).applyQuaternion(rootWorldQuat);

    let poleDir = this.naturalPole;
    if (this.currentPoleWorld) {
       poleDir.copy(this.currentPoleWorld).normalize();
    }
    
    if (Number.isNaN(poleDir.x)) {
        console.error(`FATAL: poleDir is NaN immediately after calculation! rootQuat: ${rootWorldQuat.toArray()}`);
    }

    if (this.ikMode !== 'indexFingertip') {
        this.virtualTarget.copy(this.targetWorld);
        this.debugW.copy(this.targetWorld);
        this.solveArmIK(this.virtualTarget, poleDir);
        return; 
    }

    // Phase B: Bounded iterative solver for Index Fingertip targeting mathematically
    const maxIters = 4; // Bounded loops resolving exactly avoiding infinite loops
    let residual = 1000;

    // DESTROY CYCLE: Hard-reset all components to mathematical Rest Pose to prevent cross-frame contamination
    this.upperArm.quaternion.copy(this.upperArmRestQuat);
    this.foreArm.quaternion.copy(this.foreArmRestQuat);
    this.upperArm.updateMatrixWorld(true);

    const wWorld = new THREE.Vector3();
    const tWorld = new THREE.Vector3();
    this.hand.updateMatrixWorld(true);
    this.hand.getWorldPosition(wWorld);
    
    if (!this.getActualFingertipPosition(tWorld)) {
        this.virtualTarget.copy(this.targetWorld);
        this.solveArmIK(this.virtualTarget, poleDir);
        return;
    }

    const currentOffset = new THREE.Vector3().subVectors(tWorld, wWorld);
    this.virtualTarget.copy(this.targetWorld).sub(currentOffset);

    for (let iter = 0; iter < maxIters; iter++) {
        this.solveArmIK(this.virtualTarget, poleDir);
        this.upperArm.updateMatrixWorld(true);
        this.foreArm.updateMatrixWorld(true);

        // Phase C: Deterministic targeting orientation (Hand rotation)
        if (this.fingerDirectionTarget && this.palmNormalTarget) {
            this.explicitHandOrientationPhaseC(this.fingerDirectionTarget, this.palmNormalTarget);
        } else {
            this.orientHandTowardsTargetPhaseC();
        }
        this.hand.updateMatrixWorld(true);

        this.hand.getWorldPosition(wWorld);
        this.getActualFingertipPosition(tWorld);

        residual = tWorld.distanceTo(this.targetWorld);
        if (residual < 0.005) {
            break; 
        }

        // Bounded refinement tracking Phase B mathematics explicitly
        // Lerp offsets gently to prevent 180-degree cyclic flips on constrained/unreachable targets
        const nextOffset = new THREE.Vector3().subVectors(tWorld, wWorld);
        currentOffset.lerp(nextOffset, 0.5);
        this.virtualTarget.copy(this.targetWorld).sub(currentOffset);
    }
    
    this.debugW.copy(this.virtualTarget);
  }

  private solveArmIK(targetWorldPos: THREE.Vector3, poleDir: THREE.Vector3) {
    if (!this.upperArm || !this.foreArm || !this.hand) return;
    
    this.upperArm.getWorldPosition(this.S);
    this.foreArm.getWorldPosition(this.BaseE);
    this.hand.getWorldPosition(this.BaseW);

    this.L1 = this.S.distanceTo(this.BaseE);
    this.L2 = this.BaseE.distanceTo(this.BaseW);
    if (this.L1 < 0.01) this.L1 = 0.25;
    if (this.L2 < 0.01) this.L2 = 0.25;

    this.debugS.copy(this.S);

    const totalLength = this.L1 + this.L2;
    const distanceToTarget = this.S.distanceTo(targetWorldPos);

    const minD = Math.abs(this.L1 - this.L2) + 0.001;
    const maxD = totalLength - 0.001;
    const safeDistance = clamp(distanceToTarget, minD, maxD);

    this.armDir.subVectors(targetWorldPos, this.S).normalize();

    this.upperArm.quaternion.copy(this.upperArmRestQuat);
    this.foreArm.quaternion.copy(this.foreArmRestQuat);
    
    // GUARANTEE STRICT ANATOMICAL REST PARITY IN WORLD SPACE BEFORE EVALUATING
    this.upperArm.updateMatrixWorld(true);

    const cosAlpha = (this.L1 * this.L1 + safeDistance * safeDistance - this.L2 * this.L2) / (2 * this.L1 * safeDistance);
    const alpha = Math.acos(clamp(cosAlpha, -1, 1));
    
    this.projPole.copy(poleDir).sub(this.targetDir.copy(this.armDir).multiplyScalar(poleDir.dot(this.armDir)));
    if (this.projPole.lengthSq() < 0.001) {
        this.projPole.set(0, 1, 0).cross(this.armDir);
        if (this.projPole.lengthSq() < 0.001) this.projPole.set(1, 0, 0).cross(this.armDir);
    }
    this.projPole.normalize();
    
    this.debugPole.copy(this.projPole).multiplyScalar(0.4);

    this.eCenter.copy(this.S).add(this.targetDir.copy(this.armDir).multiplyScalar(this.L1 * Math.cos(alpha)));
    this.E.copy(this.eCenter).add(this.projPole.multiplyScalar(this.L1 * Math.sin(alpha)));

    if (!Number.isFinite(this.E.x) || !Number.isFinite(this.E.y) || !Number.isFinite(this.E.z)) {
        console.error('IK ERROR: Non-Finite spatial array geometry triggered! Halting IK solve.');
        console.error(`S: ${this.S.toArray()} | target: ${targetWorldPos.toArray()}`);
        console.error(`L1: ${this.L1} | L2: ${this.L2} | safeDist: ${safeDistance}`);
        console.error(`alpha: ${alpha} | armDir: ${this.armDir.toArray()} | projPole: ${this.projPole.toArray()}`);
        console.error(`original poleDir was: ${poleDir.toArray()} | eCenter was: ${this.eCenter.toArray()}`);
        this.solverActive = false;
        return;
    }

    this.debugE.copy(this.E);

    this.lookAtBone(this.upperArm, this.E);
    this.upperArm.updateMatrixWorld(true);
    this.lookAtBone(this.foreArm, targetWorldPos);
  }

  private orientHandTowardsTargetPhaseC() {
      if (!this.hand || !this.indexTip) return;

      this.hand.getWorldPosition(this.currentPos);
      this.targetDir.subVectors(this.targetWorld, this.currentPos).normalize();
      
      this.getActualFingertipPosition(this.childRestPos);
      this.restDir.subVectors(this.childRestPos, this.currentPos).normalize();

      const angle = this.restDir.angleTo(this.targetDir);
      this.axis.crossVectors(this.restDir, this.targetDir);

      if (angle > 0.0001) {
         if (angle > Math.PI - 0.05 || this.axis.lengthSq() < 0.0001) {
             // Deterministic geometric elbow plane normal bypasses 180-degree shortest-path noise!
             this.axis.crossVectors(this.armDir, this.projPole);
             if (this.axis.lengthSq() < 0.0001) this.axis.set(0, 1, 0).cross(this.restDir);
         }
         this.axis.normalize();

         this.deltaQuat.setFromAxisAngle(this.axis, angle);
         this.hand.getWorldQuaternion(this.currentQuat);
         this.currentQuat.premultiply(this.deltaQuat);
         this.setWorldQuaternionSafely(this.hand, this.currentQuat);
      }
  }

  // R4.4 Explicit Hand Orientation targeting bypassing unconstrained shortest-path twists
  private explicitHandOrientationPhaseC(fingerDir: THREE.Vector3, palmNormal: THREE.Vector3) {
      if (!this.hand || !this.foreArm) return;

      // Extract explicit Orthogonal basis bridging ASL requests to ThreeJS matrices natively.
      // 1. Local Y maps entirely natively to the Finger Pointing vector
      const Y = fingerDir.clone().normalize();
      
      // 2. Local -Z structurally matches Palm Front (Mixamo base standard projection)
      // Thus Z points opposite the palm.
      const Z = palmNormal.clone().negate().normalize();
      
      // 3. Resolve perfect orthogonal alignment natively
      const X = new THREE.Vector3().crossVectors(Y, Z).normalize();
      Z.crossVectors(X, Y).normalize(); 

      // Build specific absolute rotation parsing standard Hand coordinates inherently
      const targetWorldMatrix = new THREE.Matrix4().makeBasis(X, Y, Z);
      const targetWorldQuat = new THREE.Quaternion().setFromRotationMatrix(targetWorldMatrix);

      // We explicitly decouple the target orientation absorbing pronation twists natively on the ForeArm, rescuing Wrist fractures explicitly.
      const parentWorldQuat = new THREE.Quaternion();
      this.foreArm.getWorldQuaternion(parentWorldQuat);
      
      // Project the Target into current ForeArm bounds local space natively
      const handLocalQuat = parentWorldQuat.clone().invert().multiply(targetWorldQuat);

      // Extract Euler natively applying Y-Axis explicitly isolating pronation twists
      // Eulers parse natively across sequential isolated array checks resolving bounds
      const euler = new THREE.Euler().setFromQuaternion(handLocalQuat, 'YXZ');
      const twistY = euler.y;

      // Stage 1: Transfer pure Twist cleanly up to the ForeArm physically mimicking radius/ulna pronation accurately
      const foreArmTwist = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), twistY);
      this.foreArm.quaternion.multiply(foreArmTwist);
      this.foreArm.updateMatrixWorld(true);

      // Stage 2: Constrain remaining orientation physically mapping deviation arrays onto Wrist structurally
      euler.y = 0; 

      // Clamping extreme anatomical variations strictly isolating biological bounds naturally
      euler.x = clamp(euler.x, -Math.PI/2, Math.PI/2); // Flexion limit
      euler.z = clamp(euler.z, -Math.PI/4, Math.PI/4); // Deviation limit

      this.hand.quaternion.setFromEuler(euler);
  }

  private lookAtBone(bone: THREE.Bone, targetWorldPos: THREE.Vector3) {
      const child = bone.children[0] as THREE.Bone;
      if (!child) return;

      bone.getWorldPosition(this.currentPos);
      this.targetDir.subVectors(targetWorldPos, this.currentPos).normalize();
      
      child.getWorldPosition(this.childRestPos);
      this.restDir.subVectors(this.childRestPos, this.currentPos).normalize();

      const angle = this.restDir.angleTo(this.targetDir);
      this.axis.crossVectors(this.restDir, this.targetDir);

      if (angle > 0.0001) {
         if (angle > Math.PI - 0.05 || this.axis.lengthSq() < 0.0001) {
             this.axis.crossVectors(this.armDir, this.projPole);
             if (this.axis.lengthSq() < 0.0001) this.axis.set(0, 1, 0).cross(this.restDir);
         }
         this.axis.normalize();

         this.deltaQuat.setFromAxisAngle(this.axis, angle);
         bone.getWorldQuaternion(this.currentQuat);
         this.currentQuat.premultiply(this.deltaQuat);
         this.setWorldQuaternionSafely(bone, this.currentQuat);
      }
  }

  private setWorldQuaternionSafely(bone: THREE.Bone, q: THREE.Quaternion) {
      const parent = bone.parent;
      if (parent) {
          parent.getWorldQuaternion(this.parentWorldQuat);
          this.parentWorldQuat.invert();
          bone.quaternion.copy(this.parentWorldQuat.multiply(q));
      } else {
          bone.quaternion.copy(q);
      }
  }
}
