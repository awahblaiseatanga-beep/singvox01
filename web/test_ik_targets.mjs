import * as THREE from 'three';
import fs from 'fs';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { CanonicalBones } from '../avatar/controller/boneMap.ts';

// We must manually duplicate the ik math to rigorously benchmark and extract debug states locally
const glbData = fs.readFileSync('public/avatar/SignVox_Female.glb');
const glbArrayBuffer = glbData.buffer.slice(glbData.byteOffset, glbData.byteOffset + glbData.byteLength);

let L1 = 0.23, L2 = 0.27; // approximate
function solve(target, pole, side='left', isFingertip=false, wristSlider=false) {
    // Simple 2 bone + orient test
    // To rigorously test this, let's just log the real ArmIKController math by instantiating it!
}

// Actually, importing avatar controllers directly might require ts-node, let's use vitest to run an isolated test file on the Avatar logic!
