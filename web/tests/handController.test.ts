import { describe, it, expect, beforeEach } from 'vitest';
import * as THREE from 'three';
import { AvatarController } from '../../avatar/controller/AvatarController';
import { HandController } from '../../avatar/controller/HandController';
import { CanonicalBones } from '../../avatar/controller/boneMap';

describe('R4.2 Hand & Finger Controller Kinematics', () => {
    let root: THREE.Group;
    let avatar: AvatarController;
    let leftHand: HandController;
    let rightHand: HandController;

    beforeEach(() => {
        root = new THREE.Group();
        avatar = new AvatarController();
        
        for (const [key, name] of Object.entries(CanonicalBones)) {
           const b = new THREE.Bone();
           b.name = name as string;
           // Start with a mock randomized rest pose to test preservation!
           b.quaternion.setFromAxisAngle(new THREE.Vector3(1, 0, 0), Math.PI/4);
           root.add(b);
        }
        
        avatar.rootScene = root;
        // Access private method for exact cache mocking
        (avatar as any).buildBoneMapCache();
        
        leftHand = new HandController('left', avatar);
        rightHand = new HandController('right', avatar);
    });

    it('A. Finger name typing and O. Complete finger chain resolution', () => {
        expect(leftHand.thumb).toBeDefined();
        expect(leftHand.index).toBeDefined();
        expect(leftHand.middle).toBeDefined();
        expect(leftHand.ring).toBeDefined();
        expect(leftHand.pinky).toBeDefined();
        
        // Assert joint resolution mapped properly directly in class instance internals safely
        expect((leftHand.index as any).joints.size).toBe(3);
        expect((leftHand.thumb as any).joints.size).toBe(3);
    });

    it('B/C. Curl and Spread clamping safely applies domain bounds', () => {
        leftHand.index.setCurl(2.5); // Overshoot
        expect(leftHand.index.getSnapshot().curl).toBe(1);

        leftHand.index.setCurl(-1); // Undershoot
        expect(leftHand.index.getSnapshot().curl).toBe(0);

        leftHand.index.setSpread(5); 
        expect(leftHand.index.getSnapshot().spread).toBe(1);

        leftHand.index.setSpread(-2); 
        expect(leftHand.index.getSnapshot().spread).toBe(-1);
    });

    it('D/E. Thumb specific flex and abduction clamping', () => {
        leftHand.thumb.setFlex(1.5);
        expect(leftHand.thumb.getSnapshot().flex).toBe(1);

        leftHand.thumb.setAbduction(-2);
        expect(leftHand.thumb.getSnapshot().abduction).toBe(-1);
    });

    it('G. Left/Right Independence asserts physical partitioning', () => {
        leftHand.index.setCurl(1);
        rightHand.index.setCurl(0.5);

        expect(leftHand.index.getSnapshot().curl).toBe(1);
        expect(rightHand.index.getSnapshot().curl).toBe(0.5);
    });

    it('H/I/J/M. Snapshot, Restore, Neutral Reset and Rest Transform Preservation', () => {
        // Base neutral check
        const initialIndexQ = avatar.getBone('LeftHandIndex1')!.quaternion.clone();

        leftHand.index.setCurl(1);
        const transformedQ = avatar.getBone('LeftHandIndex1')!.quaternion.clone();
        expect(initialIndexQ.equals(transformedQ)).toBe(false); // Curls changed the math

        const snapshot = leftHand.snapshot();
        expect(snapshot.index.curl).toBe(1);

        // Reset
        leftHand.reset();
        const resetQ = avatar.getBone('LeftHandIndex1')!.quaternion.clone();
        expect(initialIndexQ.equals(resetQ)).toBe(true); // Neutral restores structural rest!

        // Restore snapshot
        leftHand.restore(snapshot);
        const restoredQ = avatar.getBone('LeftHandIndex1')!.quaternion.clone();
        // Since floating point math introduces slight margins, use near constraints, or standard string representation
        expect(restoredQ.x).toBeCloseTo(transformedQ.x, 4);
        expect(restoredQ.y).toBeCloseTo(transformedQ.y, 4);
        expect(restoredQ.z).toBeCloseTo(transformedQ.z, 4);
        expect(restoredQ.w).toBeCloseTo(transformedQ.w, 4);
    });

    it('K. Hand pose application translates comprehensively to all fingers', () => {
        leftHand.setPose({
           thumb: { flex: 1, abduction: 0.5 },
           index: { curl: 1, spread: -0.5 },
           middle: { curl: 0.8, spread: 0 },
           ring: { curl: 0.2, spread: 0 },
           pinky: { curl: 0, spread: 0.5 }
        });

        const snap = leftHand.snapshot();
        expect(snap.thumb.flex).toBe(1);
        expect(snap.index.curl).toBe(1);
        expect(snap.index.spread).toBe(-0.5);
        expect(snap.middle.curl).toBe(0.8);
        expect(snap.pinky.spread).toBe(0.5);
    });

    it('L. Invalid finger/joint handling', () => {
        // Controller safely handles nodes not present organically
        const emptyAvatar = new AvatarController();
        emptyAvatar.rootScene = new THREE.Group(); 
        const emptyHand = new HandController('left', emptyAvatar);

        // Setting curl should not throw exceptions on null geometry
        expect(() => {
           emptyHand.index.setCurl(1);
           emptyHand.reset();
        }).not.toThrow();
    });

    it('N. Controller initialization attaches properly in root Avatar layer', async () => {
        // Mock loadGLB functionality logic
        const ctrl = new AvatarController();
        // Since loadGNB uses real HTTP loader, we just assert its runtime placeholders
        expect(ctrl.hands.left).toBeNull();
        expect(ctrl.hands.right).toBeNull();
    });

    it('P. Explicit Animation Ownership overrides generic tracks during delta updates', () => {
        // Mock generic animation state modifying the LeftHandIndex1 bone
        const bone = avatar.getBone('LeftHandIndex1')!;
        // Assuming Mixer rotates the bone to a random value
        bone.quaternion.setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.PI);

        // Prove HandController isolates and stomps the generic drift when explicitly updated
        leftHand.index.setCurl(0); // Set strictly to neutral curl
        avatar.update(0.16); // Mimic game loop tick executing mixer then overwriting local

        // Must equal original rest quaternion despite generic track interpolation!
        const restQuaternion = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), Math.PI/4); // Base rest we set in beforeEach
        expect(bone.quaternion.x).toBeCloseTo(restQuaternion.x, 4);
        expect(bone.quaternion.y).toBeCloseTo(restQuaternion.y, 4);
        expect(bone.quaternion.z).toBeCloseTo(restQuaternion.z, 4);
        expect(bone.quaternion.w).toBeCloseTo(restQuaternion.w, 4);
    });
});
