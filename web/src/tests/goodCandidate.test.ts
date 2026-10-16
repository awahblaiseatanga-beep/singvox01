import { describe, it, expect } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as THREE from 'three';
import { AvatarController } from '../../../avatar/controller/AvatarController';

// GOOD pilot: candidate GLB must carry a real ASL_GOOD clip, and the production
// AvatarController must resolve playSignByLabel('GOOD') to it (not neutral).
const CANDIDATE = path.resolve(
  __dirname, '../../../experiments/avatar/pilot_good/SignVox_GOOD_Candidate.glb'
);

// The candidate GLB is a 49.8 MB local-only artifact (`*.glb` is gitignored
// except the production avatar). Skip — never silently pass, never fail — when
// a clean clone does not carry it. The tracked synthetic fixture in
// syntheticFixtures.test.ts covers the same structural invariants everywhere.
const HAVE_CANDIDATE = fs.existsSync(CANDIDATE);

function readGltfJson(p: string): any {
  const b = fs.readFileSync(p);
  const jsonLen = b.readUInt32LE(12);
  return JSON.parse(b.subarray(20, 20 + jsonLen).toString('utf8'));
}

describe.skipIf(!HAVE_CANDIDATE)('GOOD candidate (ASL_002) pilot', () => {
  it('candidate GLB exists and contains an ASL_GOOD rotation clip', () => {
    expect(fs.existsSync(CANDIDATE)).toBe(true);
    const js = readGltfJson(CANDIDATE);
    const names = (js.animations as any[]).map((a) => a.name);
    expect(names).toContain('ASL_GOOD');
    const good = (js.animations as any[]).find((a) => a.name === 'ASL_GOOD');
    const nodes = (js.nodes as any[]).map((n) => n.name);
    const rotTargets = new Set(
      good.channels
        .filter((c: any) => c.target.path === 'rotation')
        .map((c: any) => nodes[c.target.node])
    );
    for (const bone of ['mixamorig4:RightArm', 'mixamorig4:RightForeArm', 'mixamorig4:RightHand']) {
      expect(rotTargets.has(bone)).toBe(true);
    }
  });

  it("playSignByLabel('GOOD') resolves to clip:ASL_GOOD, not neutral", () => {
    const js = readGltfJson(CANDIDATE);
    const names = (js.animations as any[]).map((a) => a.name);
    const controller = new AvatarController();
    controller.rootScene = new THREE.Group();
    controller.mixer = new THREE.AnimationMixer(controller.rootScene);
    controller.animationClips = names.map((n) => new THREE.AnimationClip(n, 1.0, []));
    controller.hands.left = { update: () => {} } as any;
    controller.hands.right = { update: () => {} } as any;
    controller.armIK.left = { update: () => {} } as any;
    controller.armIK.right = { update: () => {} } as any;
    controller.playSignByLabel('GOOD');
    expect(controller.animationMode).toBe('clip:ASL_GOOD');
  });
});
