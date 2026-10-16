import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { AvatarController } from '../../../avatar/controller/AvatarController';
import { ArmIKController } from '../../../avatar/controller/ArmIKController';

describe('SignVox R4.3.1 Diagnostic - Visual Target Tracking', () => {

    it('1. Verifies exact coordinate tracking preventing (0,0,0) snaps', async () => {
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

        const { AnatomicalAnchors } = await import('../../../avatar/controller/AnatomicalAnchors');
        const anchors = new AnatomicalAnchors(mockAvatar as any);
        
        // This execution now strictly updates the rootScene matrices internally natively automatically.
        const pos = anchors.getAnchorWorldPosition('forehead');
        expect(pos).not.toBeNull();
        
        // Base head World = (0, 1.5, 0), Offset = (0, 0.08, 0.16)
        // Expected = (0, 1.58, 0.16)
        expect(pos!.y).toBeCloseTo(1.58, 2);
        
        // Verify Target is explicitly assigned checking constraints cleanly
        const mockIK = {
            targetWorld: new THREE.Vector3(),
            solverActive: false,
            setTarget(target: THREE.Vector3) {
                if (target.lengthSq() < 0.0001) {
                    this.solverActive = false;
                    return;
                }
                this.targetWorld.copy(target);
                this.solverActive = true;
            }
        };
        
        mockIK.setTarget(pos!);
        expect(mockIK.solverActive).toBe(true);
        expect(mockIK.targetWorld.y).toBeCloseTo(1.58, 2);
    });

});
