import { describe, it, expect, beforeEach } from 'vitest';
import * as THREE from 'three';
import { AvatarController } from '../../../avatar/controller/AvatarController';

describe('Avatar Controller Playback Interpolation Logic', () => {
    let controller: AvatarController;

    beforeEach(() => {
        controller = new AvatarController();
        controller.rootScene = new THREE.Group();
        
        // Mock the internal components that require heavy DOM
        controller.mixer = new THREE.AnimationMixer(controller.rootScene);
        
        // 1. Mock an 'ASL_HELLO' explicit animation clip that exists
        const track = new THREE.VectorKeyframeTrack('testbone.position', [0, 1], [0,0,0, 1,1,1]);
        const testClip = new THREE.AnimationClip('ASL_HELLO', 1.0, [track]);
        controller.animationClips = [testClip];

        // 2. Mount manual sub-controllers
        controller.hands.left = { update: () => {} } as any;
        controller.hands.right = { update: () => {} } as any;
        controller.armIK.left = { update: () => {} } as any;
        controller.armIK.right = { update: () => {} } as any;
    });

    it('Setting active explicit clip correctly overrides system execution mode', () => {
        controller.setMode('clip:ASL_HELLO');
        expect(controller.animationMode).toBe('clip:ASL_HELLO');
        
        const act = controller.mixer!.clipAction(controller.animationClips[0]);
        expect(act.isRunning()).toBe(true);
    });

    it('Verifies manual IK and hand controllers do not stomp external track payload data', () => {
        // Setup spies to verify if the FK stomping occurs
        let leftHandStomped = false;
        let leftArmStomped = false;
        
        controller.hands.left!.update = () => { leftHandStomped = true; };
        controller.armIK.left!.update = () => { leftArmStomped = true; };
        
        // When processing explicit clips, interpolation updates MUST skip manual bone resetting
        controller.setMode('clip:ASL_HELLO');
        controller.update(0.016);
        
        expect(leftHandStomped).toBe(false);
        expect(leftArmStomped).toBe(false);

        // When standard neutral execution occurs, hands are required to enforce IK ownership bounds
        controller.setMode('manual');
        controller.update(0.016);
        
        expect(leftHandStomped).toBe(true);
        expect(leftArmStomped).toBe(true);
    });
});
