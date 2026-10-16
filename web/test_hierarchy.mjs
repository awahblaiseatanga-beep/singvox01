import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import fs from 'fs';
import path from 'path';

// Fix globals for GLTFLoader in Node
global.self = global;
global.window = global;

function runTest() {
    const glbPath = path.resolve('public/avatar/SignVox_Female.glb');
    const buffer = fs.readFileSync(glbPath);
    const arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);

    const loader = new GLTFLoader();
    
    loader.parse(arrayBuffer, '', async (gltf) => {
        console.log("GLTF Parsed Successfully.");
        const rootScene = gltf.scene;

        // Instead of breaking encapsulation, let's load AvatarController by compiling it here roughly
        // BUT wait, we can't easily import TS files without ts-node. Let's just require the JS if it's built?
        // Let's use tsx or vitest. Actually `npx tsx` evaluates it seamlessly!
        
    }, undefined, (e) => console.error("Parse error:", e));
}

runTest();
