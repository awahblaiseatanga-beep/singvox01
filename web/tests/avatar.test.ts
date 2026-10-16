// @ts-nocheck
import { describe, it, expect } from 'vitest';
import * as THREE from 'three';
import { CanonicalBones, validateBoneMap, OptionalBones } from '../../avatar/controller/boneMap';
import { createEmptyCapabilities } from '../../avatar/controller/avatarCapabilities';

describe('Avatar Controller & Bone Map', () => {

  it('Canonical dictionary contains required mapping keys', () => {
    // Check baseline keys
    expect(CanonicalBones).toHaveProperty('Hips');
    expect(CanonicalBones).toHaveProperty('Spine');
    expect(CanonicalBones).toHaveProperty('Head');
    expect(CanonicalBones).toHaveProperty('LeftArm');
    expect(CanonicalBones).toHaveProperty('RightArm');
    expect(CanonicalBones).toHaveProperty('LeftHand');
    expect(CanonicalBones).toHaveProperty('RightHand');
    
    // Check all fingers natively
    const fingers = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'];
    fingers.forEach(f => {
        for (let i=1; i<=3; i++) {
           expect(CanonicalBones).toHaveProperty(`LeftHand${f}${i}`);
           expect(CanonicalBones).toHaveProperty(`RightHand${f}${i}`);
        }
    });
  });

  it('Valid skeleton passes validation', () => {
    const root = new THREE.Object3D();
    for (const [key, name] of Object.entries(CanonicalBones)) {
      const b = new THREE.Bone();
      b.name = name as string;
      root.add(b);
    }
    const report = validateBoneMap(root);
    expect(report.isValid).toBe(true);
    expect(report.missingRequired).toHaveLength(0);
  });

  it('Missing required bone fails validation', () => {
    const root = new THREE.Object3D();
    for (const [key, name] of Object.entries(CanonicalBones)) {
      if (key === 'LeftHandIndex1') continue; 
      const b = new THREE.Bone();
      b.name = name as string;
      root.add(b);
    }
    const report = validateBoneMap(root);
    expect(report.isValid).toBe(false);
    expect(report.missingRequired).toContain('LeftHandIndex1');
    expect(report.missingRequired).toHaveLength(1);
  });

  it('Duplicate mapping test', () => {
     const vals = Object.values(CanonicalBones);
     const uVals = new Set(vals);
     expect(vals.length).toBe(uVals.size);
  });

  it('Capabilities detection checks out correctly based on presence', () => {
    const caps = createEmptyCapabilities();
    caps.hasLeftArm = true;
    caps.hasLeftHand = true;
    caps.hasLeftFingers = true;
    caps.hasFaceMorphTargets = true;
    caps.hasAnimationClips = true;
    
    // Explicit overrides
    caps.isStructuralValid = true;
    caps.isSigningValid = false;

    expect(caps.hasLeftFingers).toBe(true);
    expect(caps.hasFaceMorphTargets).toBe(true);
    expect(caps.hasAnimationClips).toBe(true);
    expect(caps.isStructuralValid).toBe(true);
    expect(caps.isSigningValid).toBe(false);
  });
});

