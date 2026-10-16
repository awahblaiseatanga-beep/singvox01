import { describe, it, expect } from 'vitest';
import * as THREE from 'three';
import { ArmIKController } from '../../../avatar/controller/ArmIKController';

// Minimal mock AvatarController resolving only needed Bones natively bridging testing limits
class MockAvatarController {
    public rootScene = new THREE.Object3D();
    private bones: Record<string, THREE.Bone> = {};
    
    constructor() {
        const rootSpine = new THREE.Bone(); rootSpine.name = 'Spine'; this.rootScene.add(rootSpine);
        const lShoulder = new THREE.Bone(); lShoulder.name = 'LeftShoulder';
        const lArm = new THREE.Bone(); lArm.name = 'LeftArm'; lArm.position.set(0, 0, 0); // At shoulder
        const lFore = new THREE.Bone(); lFore.name = 'LeftForeArm'; lFore.position.set(0, 0.2, 0); // 20cm down local Y
        const lHand = new THREE.Bone(); lHand.name = 'LeftHand'; lHand.position.set(0, 0.27, 0); // 27cm down local Y
        const lIndex2 = new THREE.Bone(); lIndex2.name = 'LeftHandIndex2'; lIndex2.position.set(0, 0.05, 0); 
        const lIndex3 = new THREE.Bone(); lIndex3.name = 'LeftHandIndex3'; lIndex3.position.set(0, 0.1, 0); // 10cm hand length local Y
        const lIndex4 = new THREE.Bone(); lIndex4.name = 'LeftHandIndex4'; lIndex4.position.set(0, 0.05, 0); // 5cm phalanx local Y
        
        rootSpine.add(lShoulder);
        lShoulder.add(lArm);
        lArm.add(lFore);
        lFore.add(lHand);
        lHand.add(lIndex2);
        lIndex2.add(lIndex3);
        lIndex3.add(lIndex4);
        
        this.bones = {
            'Spine': rootSpine, 'LeftShoulder': lShoulder, 'LeftArm': lArm, 
            'LeftForeArm': lFore, 'LeftHand': lHand, 'LeftHandIndex2': lIndex2, 'LeftHandIndex3': lIndex3, 'LeftHandIndex4': lIndex4
        };
        this.rootScene.updateMatrixWorld(true);
    }
    getBone(name: string) { return this.bones[name] || null; }
}

describe('SignVox R4.4 - Palm Orientation Decoupling Prototype', () => {

    it('1. Confirms Finger Pointing translates correctly through Phase C cleanly isolating Cartesian Target', async () => {
        const avatar = new MockAvatarController() as any;
        const ik = new ArmIKController('left', avatar);
        
        // Forehead Target broadly across the body
        const forehead = new THREE.Vector3(0.1, 0.5, 0.2); 
        const fingerDir = new THREE.Vector3(0, 1, -0.5).normalize(); // Point UP and BACK
        const palmNorm = new THREE.Vector3(-1, -1, 0).normalize(); // Face DOWN and ACROSS 

        ik.setTarget(forehead, undefined, 'indexFingertip', fingerDir, palmNorm);
        console.log(`Initial root pos: ${avatar.getBone('LeftArm').getWorldPosition(new THREE.Vector3()).toArray()}`);
        console.log(`Target: ${forehead.toArray()}`);

        ik.update();
        
        const tipPos = new THREE.Vector3();
        ik.getActualFingertipPosition(tipPos);
        
        console.log(`lArm: ${avatar.getBone('LeftArm').getWorldPosition(new THREE.Vector3()).toArray()}`);
        console.log(`lFore: ${avatar.getBone('LeftForeArm').getWorldPosition(new THREE.Vector3()).toArray()}`);
        console.log(`lHand: ${avatar.getBone('LeftHand').getWorldPosition(new THREE.Vector3()).toArray()}`);
        console.log(`lIndex4: ${avatar.getBone('LeftHandIndex4').getWorldPosition(new THREE.Vector3()).toArray()}`);
        
        console.log(`TipPos Output: ${tipPos.toArray()}`);
        console.log(`Arm solver state: ${ik.solverActive}`);

        const errorDist = tipPos.distanceTo(forehead);
        expect(errorDist).toBeLessThan(0.01); 
        
        // Mathematical Verification B: Twist Orientation Transfer
        // The twisting phase isolates roll exclusively on ForeArm tracking physiological anatomical limits natively!
        const lFore = avatar.getBone('LeftForeArm');
        const lHand = avatar.getBone('LeftHand');
        
        const foreEuler = new THREE.Euler().setFromQuaternion(lFore.quaternion, 'YXZ');
        const handEuler = new THREE.Euler().setFromQuaternion(lHand.quaternion, 'YXZ');
        
        // The Hand quaternion twist (Y) MUST be fundamentally 0 since the solver transfers ALL axial pronation directly onto the forearm!
        expect(Math.abs(handEuler.y)).toBeLessThan(0.001);
    });

});
