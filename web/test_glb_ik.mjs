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
    
    loader.parse(arrayBuffer, '', (gltf) => {
        console.log("GLTF Parsed Successfully.");
        const rootScene = gltf.scene;
        
        let boneMap = new Map();
        rootScene.traverse(child => {
            if (child.isBone) {
                // Canonical mapping (simple)
                if (child.name === 'mixamorig4LeftArm') boneMap.set('LeftArm', child);
                if (child.name === 'mixamorig4LeftForeArm') boneMap.set('LeftForeArm', child);
                if (child.name === 'mixamorig4LeftHand') boneMap.set('LeftHand', child);
                if (child.name === 'mixamorig4LeftShoulder') boneMap.set('LeftShoulder', child);
                if (child.name === 'mixamorig4Spine') boneMap.set('Spine', child);
            }
        });
        
        const upArm = boneMap.get('LeftArm');
        const fArm = boneMap.get('LeftForeArm');
        const hand = boneMap.get('LeftHand');
        
        console.log("Bones Found:");
        console.log("UpperArm:", !!upArm);
        console.log("ForeArm:", !!fArm);
        console.log("Hand:", !!hand);
        
        // 1. Initial State
        rootScene.updateMatrixWorld(true);
        const w1 = new THREE.Vector3(); hand.getWorldPosition(w1);
        console.log("Initial Hand World:", w1);
        
        // Target Belly
        const spine = boneMap.get('Spine');
        const targetWorld = new THREE.Vector3();
        spine.getWorldPosition(targetWorld);
        targetWorld.add(new THREE.Vector3(0, 0, 0.12)); // Offset
        console.log("Target (Belly):", targetWorld);
        
        // Execute LookAt Logic
        const upperArmRestQuat = upArm.quaternion.clone();
        const foreArmRestQuat = fArm.quaternion.clone();
        
        upArm.quaternion.copy(upperArmRestQuat);
        fArm.quaternion.copy(foreArmRestQuat);
        
        const S = new THREE.Vector3(); upArm.getWorldPosition(S);
        const BaseE = new THREE.Vector3(); fArm.getWorldPosition(BaseE);
        const BaseW = new THREE.Vector3(); hand.getWorldPosition(BaseW);
        const L1 = S.distanceTo(BaseE);
        const L2 = BaseE.distanceTo(BaseW);
        
        console.log(`Phys L1: ${L1}, L2: ${L2}`);
        
        // Let's implement the IK explicitly identically
        const totalLength = L1 + L2;
        const distanceToTarget = S.distanceTo(targetWorld);
        console.log(`Distance S to Target: ${distanceToTarget}, Max Reach: ${totalLength}`);
        const safeDistance = Math.max(Math.abs(L1 - L2) + 0.001, Math.min(distanceToTarget, totalLength - 0.001));
        console.log(`Safe Distance constraint applies: ${safeDistance}`);

        const baseArmDir = new THREE.Vector3().subVectors(BaseW, S).normalize();
        const targetDir = new THREE.Vector3().subVectors(BaseE, S);
        const projBaseE = baseArmDir.clone().multiplyScalar(targetDir.dot(baseArmDir));
        const naturalPole = new THREE.Vector3().subVectors(BaseE, S).sub(projBaseE);
        if (naturalPole.lengthSq() > 0.0001) naturalPole.normalize();
        else naturalPole.set(-1, -0.5, -1).normalize();
        
        const cosAlpha = (L1 * L1 + safeDistance * safeDistance - L2 * L2) / (2 * L1 * safeDistance);
        const alpha = Math.acos(Math.max(-1, Math.min(1, cosAlpha)));
        
        const armDir = new THREE.Vector3().subVectors(targetWorld, S).normalize();
        let projPole = naturalPole.clone().sub(armDir.clone().multiplyScalar(naturalPole.dot(armDir)));
        
        if (projPole.lengthSq() < 0.001) {
            projPole.set(0, 1, 0).cross(armDir);
        }
        projPole.normalize();
        
        const E = S.clone().add(armDir.clone().multiplyScalar(L1 * Math.cos(alpha))).add(projPole.multiplyScalar(L1 * Math.sin(alpha)));
        console.log("Calculated E point:", E);
        
        function setWorldQuaternionSafely(bone, q) {
            if (bone.parent) {
                const parentW = new THREE.Quaternion();
                bone.parent.getWorldQuaternion(parentW);
                bone.quaternion.copy(parentW.invert().multiply(q));
            } else {
                bone.quaternion.copy(q);
            }
        }

        function lookAtBone(bone, tgt) {
            const currentPos = new THREE.Vector3();
            bone.getWorldPosition(currentPos);
            
            const childRestPos = new THREE.Vector3();
            bone.children[0].getWorldPosition(childRestPos);
            
            const rDir = new THREE.Vector3().subVectors(childRestPos, currentPos).normalize();
            const tDir = new THREE.Vector3().subVectors(tgt, currentPos).normalize();
            
            const angle = rDir.angleTo(tDir);
            const axis = new THREE.Vector3().crossVectors(rDir, tDir);
            if (angle > 0.001) {
                if(axis.lengthSq() < 0.001) axis.set(0,1,0).cross(rDir);
                axis.normalize();
                
                const delta = new THREE.Quaternion().setFromAxisAngle(axis, angle);
                const currentQ = new THREE.Quaternion();
                bone.getWorldQuaternion(currentQ);
                currentQ.premultiply(delta);
                setWorldQuaternionSafely(bone, currentQ);
            }
        }
        
        lookAtBone(upArm, E);
        upArm.updateMatrixWorld(true);
        console.log("Upper Arm lookAt Complete. World Pos:", upArm.getWorldPosition(new THREE.Vector3()));
        
        lookAtBone(fArm, targetWorld);
        fArm.updateMatrixWorld(true);
        console.log("Fore Arm lookAt Complete. Hand should be AT target now.");
        
        const wFinal = new THREE.Vector3();
        hand.getWorldPosition(wFinal);
        console.log(`Target: ${targetWorld.toArray().join(',')}`);
        console.log(`Final Hand: ${wFinal.toArray().join(',')}`);
        console.log(`Distance Closed: ${wFinal.distanceTo(targetWorld)}`);

    }, undefined, (e) => console.error("Parse error:", e));
}

runTest();
