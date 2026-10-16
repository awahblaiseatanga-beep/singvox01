import fs from 'fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
// Workaround for Node.js loading
import { JSDOM } from 'jsdom';
const { window } = new JSDOM();
global.window = window;
global.document = window.document;

async function load() {
    const data = fs.readFileSync('d:/Singvox/Singvox/web/public/avatar/SignVox_Female_v3.glb');
    const arrayBuffer = data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength);
    const loader = new GLTFLoader();
    
    loader.parse(arrayBuffer, '', (gltf) => {
        let bones = [];
        gltf.scene.traverse((child) => {
            if (child.isBone) {
                bones.push(child.name);
            }
        });
        
        console.log("TOTAL BONES:", bones.length);
        const indexBones = bones.filter(b => b.includes("Index"));
        console.log("INDEX BONES FOUND:");
        console.log(indexBones.join("\n"));
        
        // Print all bones to see if namespace is mixamorig4:BoneName or Mixamorig4BoneName etc
        console.log("PREFIX SAMPLE:");
        console.log(bones.slice(0, 5).join(", "));
    }, (error) => {
        console.error(error);
    });
}
load();
