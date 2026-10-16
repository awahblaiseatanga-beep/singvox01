import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { AnatomicalAnchors } from '../../../avatar/controller/AnatomicalAnchors';

describe('Diagnostic Trace: Target Resolution Pipeline', () => {

    it('1. Selected anchor -> resolved anchor object -> target world position', () => {
        const root = new THREE.Object3D();
        const head = new THREE.Bone();
        head.name = 'mixamorig4Head';
        root.add(head);

        // Put the head conceptually at Y = 1.5 in world space
        head.position.set(0, 1.5, 0);

        const mockAvatar = {
            rootScene: root,
            getBone: (name: string) => name === 'Head' ? head : undefined
        };

        const anchors = new AnatomicalAnchors(mockAvatar as any);
        root.updateMatrixWorld(true);

        const pos = anchors.getAnchorWorldPosition('forehead');
        expect(pos).not.toBeNull();
        
        // Base head World = (0, 1.5, 0)
        // Offset = (0, 0.08, 0.16)
        // Expected = (0, 1.58, 0.16)
        expect(pos!.y).toBeCloseTo(1.58, 2);
    });

    it('2. Evaluates proper root-relative Body Space offset mappings', () => {
        const root = new THREE.Object3D();
        // Twist the entire root significantly!
        root.rotation.x = Math.PI / 2; // Face down 90 degrees!
        
        const hip = new THREE.Bone();
        hip.name = 'mixamorig4Hips';
        root.add(hip);
        hip.position.set(0, 1.0, 0); // In local space, Y is 1.0. 
        // In world space, since root is rotated X=90, hip is at Z=1.0! Wait, Y=(cos90)*1=0, Z=(sin90)*1=1!

        const mockAvatar = {
            rootScene: root,
            getBone: (name: string) => name === 'Hips' ? hip : undefined
        };

        const anchors = new AnatomicalAnchors(mockAvatar as any);
        root.updateMatrixWorld(true);

        const pos = anchors.getAnchorWorldPosition('leftHip');
        expect(pos).not.toBeNull();
        
        // Offset is (0.14, -0.05, 0.12)
        // Left hip + offset should map cleanly reflecting root twist.
        console.log(`[Diagnostic] Hip World Space Extracted: ${pos!.x.toFixed(2)}, ${pos!.y.toFixed(2)}, ${pos!.z.toFixed(2)}`);
    });

});
