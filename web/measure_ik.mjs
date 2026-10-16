import fs from 'fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { AvatarController } from './src/avatar/controller/AvatarController.ts';
import { AnatomicalAnchorName } from './src/avatar/controller/AnatomicalAnchors.ts';

async function runBenchmark() {
    const glbPath = './public/avatar/SignVox_Female.glb';
    const glbData = fs.readFileSync(glbPath);
    const arrayBuffer = glbData.buffer.slice(glbData.byteOffset, glbData.byteOffset + glbData.byteLength);

    const loader = new GLTFLoader();
    
    let gltfResult;
    try {
        gltfResult = await new Promise((resolve, reject) => {
            loader.parse(arrayBuffer, '', (gltf) => resolve(gltf), (err) => reject(err));
        });
    } catch(e) {
        console.error("Parse failed", e);
        return;
    }

    // Bypass AvatarController GLTFLoader fetch natively mapping cleanly 
    const ctrl = new AvatarController();
    ctrl.rootScene = gltfResult.scene;
    ctrl.animationClips = gltfResult.animations || [];
    
    const bonesList = [];
    let foundSkeleton = null;
    let boneCount = 0, meshCount = 0;
    
    ctrl.rootScene.traverse((child) => {
        if (child.isBone) {
           boneCount++;
           bonesList.push(child);
        }
        if (child.isSkinnedMesh) {
          meshCount++;
          if (child.skeleton && !foundSkeleton) foundSkeleton = child.skeleton;
        } else if (child.isMesh) {
          meshCount++;
        }
    });

    if (!foundSkeleton && bonesList.length > 0) {
       foundSkeleton = new THREE.Skeleton(bonesList);
    }
    ctrl.skeleton = foundSkeleton;
    
    // Call private build cache
    ctrl['buildBoneMapCache']();
    ctrl['calculateCapabilities'](boneCount, meshCount, false);
    
    const { AnatomicalAnchors } = await import('./src/avatar/controller/AnatomicalAnchors.ts');
    const { ArmIKController } = await import('./src/avatar/controller/ArmIKController.ts');
    const { HandController } = await import('./src/avatar/controller/HandController.ts');
    
    ctrl.anchors = new AnatomicalAnchors(ctrl);
    ctrl.armIK = { left: new ArmIKController('left', ctrl), right: new ArmIKController('right', ctrl) };
    ctrl.hands = { left: new HandController('left', ctrl), right: new HandController('right', ctrl) };

    const runBench = (side, targetName, mode, activeTestName) => {
         const target = ctrl.anchors.getAnchorWorldPosition(targetName);
         
         // 1. Hands update organically
         ctrl.hands[side].update();

         // 2. Arm IK update
         const ik = ctrl.armIK[side];
         ik.setTarget(target, undefined, mode);
         ik.update();

         // Update root bounds organically
         ctrl.rootScene.updateMatrixWorld(true);

         const W = ctrl.getBone(side === 'left' ? 'LeftHand' : 'RightHand');
         const E = ctrl.getBone(side === 'left' ? 'LeftForeArm' : 'RightForeArm');
         const S = ctrl.getBone(side === 'left' ? 'LeftArm' : 'RightArm');
         const Tip = ctrl.getBone(side === 'left' ? 'LeftHandIndex4' : 'RightHandIndex4');

         const vTip = new THREE.Vector3(); Tip.getWorldPosition(vTip);
         const vW = new THREE.Vector3(); W.getWorldPosition(vW);
         const vE = new THREE.Vector3(); E.getWorldPosition(vE);
         const vS = new THREE.Vector3(); S.getWorldPosition(vS);
         const vPol = ik.naturalPole;

         const distBase = vTip.distanceTo(target);

         console.log(`\n=== [${activeTestName}] ===`);
         console.log(`Target (${targetName}): [${target.x.toFixed(3)}, ${target.y.toFixed(3)}, ${target.z.toFixed(3)}]`);
         console.log(`Shoulder: [${vS.x.toFixed(3)}, ${vS.y.toFixed(3)}, ${vS.z.toFixed(3)}]`);
         console.log(`Elbow: [${vE.x.toFixed(3)}, ${vE.y.toFixed(3)}, ${vE.z.toFixed(3)}]`);
         console.log(`Wrist: [${vW.x.toFixed(3)}, ${vW.y.toFixed(3)}, ${vW.z.toFixed(3)}]`);
         console.log(`Index Fingertip: [${vTip.x.toFixed(3)}, ${vTip.y.toFixed(3)}, ${vTip.z.toFixed(3)}]`);
         
         const SW = new THREE.Vector3().subVectors(vW, vS);
         const SE = new THREE.Vector3().subVectors(vE, vS);
         const BendNormal = new THREE.Vector3().crossVectors(SW, SE).normalize();
         console.log(`Elbow Bend-Plane Normal: [${BendNormal.x.toFixed(3)}, ${BendNormal.y.toFixed(3)}, ${BendNormal.z.toFixed(3)}]`);
         console.log(`Allocated Anatomical Pole Hint: [${vPol.x.toFixed(3)}, ${vPol.y.toFixed(3)}, ${vPol.z.toFixed(3)}]`);
         
         console.log(`>> Fingertip distance from Target: ${distBase.toFixed(6)} meters`);
         
         // Mathematical Check: Change Index Curl!
         ctrl.hands[side].index.setCurl(1.0); // Fully curl
         ctrl.hands[side].update(); // Apply UI
         ik.update(); // Evaluate Offset again natively
         ctrl.rootScene.updateMatrixWorld(true);

         const nTip = new THREE.Vector3(); Tip.getWorldPosition(nTip);
         const distCurled = nTip.distanceTo(target);
         console.log(`>> Fingertip distance AFTER Curl Slider evaluated: ${distCurled.toFixed(6)} meters`);
         
         // Reset for next test natively
         ctrl.hands[side].reset();
         ik.reset();
         ctrl.rootScene.updateMatrixWorld(true);
    };

    runBench('left', 'eyes', 'indexFingertip', 'Left arm -> Eyes');
    runBench('left', 'belly', 'indexFingertip', 'Left arm -> Belly');
    runBench('left', 'chest', 'indexFingertip', 'Left arm -> Chest');
    runBench('right', 'eyes', 'indexFingertip', 'Right arm -> Eyes');
    runBench('right', 'belly', 'indexFingertip', 'Right arm -> Belly');
    runBench('right', 'rightHip', 'indexFingertip', 'Right arm -> Right Hip');
}

runBenchmark();
