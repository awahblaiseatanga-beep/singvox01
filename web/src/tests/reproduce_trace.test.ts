import { describe, it, beforeAll } from 'vitest';
import * as THREE from 'three';
import { AvatarController } from '../../../avatar/controller/AvatarController';
import fs from 'fs';
import path from 'path';

// The production avatar GLB is a 49.6 MB local-only artifact (`*.glb` is
// gitignored except the competition prototype). Skip — never silently pass,
// never fail — when a clean clone does not carry it; the real-model IK trace
// below cannot be reproduced synthetically because it traces the shipped rig's
// own bone transforms. The synthetic-rig trace in syntheticFixtures.test.ts
// still exercises the solver's finiteness invariants on every clone.
const MODEL_GLB = path.resolve(
    process.cwd(), '../web/public/avatar/SignVox_Female.glb'
);
const HAVE_MODEL = fs.existsSync(MODEL_GLB);

// Mock fetch
// @ts-ignore
global.fetch = async (req: any) => {
    let urlStr = typeof req === 'string' ? req : (req.url || req.toString());
    let rawPath = urlStr.replace('file:///', '');
    let buffer = fs.readFileSync(decodeURI(rawPath));
    let arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
    return { arrayBuffer: async () => arrayBuffer, ok: true, status: 200 } as any;
};
// @ts-ignore
global.self = global;

describe.skipIf(!HAVE_MODEL)('IK Root Cause Forehead Trace', () => {
    let ctrl: AvatarController;

    beforeAll(async () => {
        ctrl = new AvatarController();
        await ctrl.loadGLB(`file:///${MODEL_GLB.replace(/\\/g, '/')}`);
    });

    it('Traces exact quaternion flip boundaries for Forehead', () => {
        const ik = ctrl.armIK.left!;
        const hand = ctrl.hands.left!;
        
        // Force Torso Penetration state
        const target = new THREE.Vector3(0.08, 1.43, 0.03); // Approximated Left Shoulder failing depth natively

        console.log(`\n=== RUNTIME TRACE: LEFT SHOULDER FAIL STATE ===`);
        console.log(`TARGET: ${target.toArray().map(v=>v.toFixed(3))}`);
        
        for (let frame = 0; frame < 5; frame++) {
            console.log(`\n[FRAME ${frame}]`);
            // Emulate AvatarDiagnostic.tsx sequence EXACTLY
            hand.update(); 
            
            ik.setTarget(target, undefined, 'indexFingertip');
            
            // Log IK state variables actively using diagnostic proxy
            const proxy = ik as any;
            
            // Execute solver and intercept intermediate states via simulated override
            ik.update();
            
            const S = new THREE.Vector3(); proxy.upperArm.getWorldPosition(S);
            const E = new THREE.Vector3(); proxy.foreArm.getWorldPosition(E);
            const W = new THREE.Vector3(); proxy.hand.getWorldPosition(W);
            
            console.log(`  Positions | S: [${S.toArray().map(v=>v.toFixed(3))}], E: [${E.toArray().map(v=>v.toFixed(3))}], W: [${W.toArray().map(v=>v.toFixed(3))}]`);
            console.log(`  PoleDir   | ${proxy.naturalPole.toArray().map((v:number)=>v.toFixed(3))} | ProjPole (ElbowPlaneNorm): ${proxy.projPole.toArray().map((v:number)=>v.toFixed(3))}`);
            
            const upQuat = proxy.upperArm.quaternion;
            console.log(`  UpperArm Quat: [${upQuat.x.toFixed(4)}, ${upQuat.y.toFixed(4)}, ${upQuat.z.toFixed(4)}, ${upQuat.w.toFixed(4)}]`);
        }
    });
});
