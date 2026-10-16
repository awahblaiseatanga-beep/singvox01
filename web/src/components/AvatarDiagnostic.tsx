import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { AvatarController } from '../../../avatar/controller/AvatarController';
import { AvatarCapabilities } from '../../../avatar/controller/avatarCapabilities';
import { HandSide } from '../../../avatar/controller/HandModel';
import { AnatomicalAnchorName } from '../../../avatar/controller/AnatomicalAnchors';

const GLB_URL = '/avatar/SignVox_Female_Competition_Prototype.glb';

const ANCHORS: AnatomicalAnchorName[] = [
    "forehead", "eyes", "nose", "mouth", "chin",
    "sternum", "chest", "belly",
    "leftShoulder", "rightShoulder", "leftHip", "rightHip"
];

// Development-only diagnostic instrumentation counters
const globalMetrics = {
    activeLoops: 0,
    activeControllers: 0,
    controllerUpdates: 0,
    renderFrames: 0,
    diagnosticObjectsAdded: 10 // Based on the static debugObjects count
};

export const AvatarDiagnostic: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const timeDisplayRef = useRef<HTMLSpanElement>(null);
    const [controller, setController] = useState<AvatarController | null>(null);
    const [capabilities, setCapabilities] = useState<AvatarCapabilities | null>(null);
    const [status, setStatus] = useState<string>('Initializing');
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [animationMode, setAnimationMode] = useState<"manual" | "generic">('manual');
    const [showIKGeometry, setShowIKGeometry] = useState<boolean>(true);
    const showIKRef = useRef(showIKGeometry);
    useEffect(() => { showIKRef.current = showIKGeometry; }, [showIKGeometry]);

    const [ikEnabled, setIkEnabled] = useState<boolean>(true); // Global IK evaluation boundary toggle
    const ikEnabledRef = useRef(ikEnabled);
    useEffect(() => { ikEnabledRef.current = ikEnabled; }, [ikEnabled]);

    const [leftPose, setLeftPose] = useState({ thumbFlex: 0, thumbAbd: 0, indexCurl: 0, middleCurl: 0, ringCurl: 0, pinkyCurl: 0, spread: 0, wristX: 0 });
    const [rightPose, setRightPose] = useState({ thumbFlex: 0, thumbAbd: 0, indexCurl: 0, middleCurl: 0, ringCurl: 0, pinkyCurl: 0, spread: 0, wristX: 0 });

    const [leftIK, setLeftIK] = useState({ anchor: '', poleX: 0, poleY: 0, poleZ: 0, mode: 'wrist', pNx: 0, pNy: 0, pNz: 0, fDx: 0, fDy: 0, fDz: 0 });
    const leftIKRef = useRef(leftIK);

    const [rightIK, setRightIK] = useState({ anchor: '', poleX: 0, poleY: 0, poleZ: 0, mode: 'wrist',  pNx: 0, pNy: 0, pNz: 0, fDx: 0, fDy: 0, fDz: 0 });
    const rightIKRef = useRef(rightIK);

    useEffect(() => {
        if (!containerRef.current) return;

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x222222);

        // IK Sub-Geometry Visualizers
        const debugObjects = {
            lS: new THREE.Mesh(new THREE.SphereGeometry(0.04), new THREE.MeshBasicMaterial({ color: 0x00ff00 })),
            lE: new THREE.Mesh(new THREE.SphereGeometry(0.04), new THREE.MeshBasicMaterial({ color: 0xffff00 })),
            lW: new THREE.Mesh(new THREE.SphereGeometry(0.04), new THREE.MeshBasicMaterial({ color: 0xff0000 })),
            lTip: new THREE.Mesh(new THREE.SphereGeometry(0.02), new THREE.MeshBasicMaterial({ color: 0xff00ff })),
            rS: new THREE.Mesh(new THREE.SphereGeometry(0.04), new THREE.MeshBasicMaterial({ color: 0x00ff00 })),
            rE: new THREE.Mesh(new THREE.SphereGeometry(0.04), new THREE.MeshBasicMaterial({ color: 0xffff00 })),
            rW: new THREE.Mesh(new THREE.SphereGeometry(0.04), new THREE.MeshBasicMaterial({ color: 0xff0000 })),
            rTip: new THREE.Mesh(new THREE.SphereGeometry(0.02), new THREE.MeshBasicMaterial({ color: 0xff00ff })),
            lLine1: new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xffffff })),
            lLine2: new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xffffff })),
            rLine1: new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xffffff })),
            rLine2: new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xffffff })),
            lPole: new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0x00ffff })),
            rPole: new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0x00ffff }))
        };

        Object.values(debugObjects).forEach(obj => scene.add(obj));

        const camera = new THREE.PerspectiveCamera(45, (window.innerWidth * 0.7) / window.innerHeight, 0.1, 100);
        camera.position.set(0, 1.2, 4.5);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth * 0.7, window.innerHeight);
        containerRef.current.appendChild(renderer.domElement);

        const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 2);
        hemiLight.position.set(0, 5, 0);
        scene.add(hemiLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 2);
        dirLight.position.set(0, 5, 5);
        scene.add(dirLight);

        const ctrl = new AvatarController();
        setStatus('Loading GLB...');
        
        ctrl.loadGLB(GLB_URL)
            .then(() => {
                if (ctrl.rootScene) {
                    scene.add(ctrl.rootScene);
                }
                setController(ctrl);
                globalMetrics.activeControllers++;
                setCapabilities(ctrl.capabilities);
                setStatus('Loaded');
            })
            .catch((e: any) => {
                setStatus('Error');
                setErrorMsg(e.message);
            });

        const clock = new THREE.Clock();
        let loopAlive = true;
        globalMetrics.activeLoops++;
        
        const animate = () => {
            if (!loopAlive) return;
            requestAnimationFrame(animate);
            globalMetrics.renderFrames++;
            if (ctrl) {
               try {
                   // Ensure dynamic global evaluate toggles bind implicitly against valid current references (Fix stale closure bug)
                    if (ctrl.armIK.left) {
                       const lRef = leftIKRef.current;
                       ctrl.armIK.left.solverActive = ikEnabledRef.current && !!lRef.anchor;
                       if (ctrl.armIK.left.solverActive && ctrl.anchors) {
                           const aLeft = ctrl.anchors.getAnchorWorldPosition(lRef.anchor as AnatomicalAnchorName);
                           
                           let pDir: THREE.Vector3 | undefined = undefined;
                           if (Number(lRef.poleX) !== 0 || Number(lRef.poleY) !== 0 || Number(lRef.poleZ) !== 0) {
                               pDir = new THREE.Vector3(Number(lRef.poleX), Number(lRef.poleY), Number(lRef.poleZ));
                           }
                           
                           let fDir: THREE.Vector3 | undefined = undefined;
                           let palmNorm: THREE.Vector3 | undefined = undefined;
                           
                           if (Number(lRef.fDx) !== 0 || Number(lRef.fDy) !== 0 || Number(lRef.fDz) !== 0) {
                               fDir = new THREE.Vector3(Number(lRef.fDx), Number(lRef.fDy), Number(lRef.fDz));
                           }
                           if (Number(lRef.pNx) !== 0 || Number(lRef.pNy) !== 0 || Number(lRef.pNz) !== 0) {
                               palmNorm = new THREE.Vector3(Number(lRef.pNx), Number(lRef.pNy), Number(lRef.pNz));
                           }

                           if (aLeft) ctrl.armIK.left.setTarget(aLeft, pDir, lRef.mode as 'wrist'|'indexFingertip', fDir, palmNorm);
                       }
                   }
                   if (ctrl.armIK.right) {
                       const rRef = rightIKRef.current;
                       ctrl.armIK.right.solverActive = ikEnabledRef.current && !!rRef.anchor;
                       if (ctrl.armIK.right.solverActive && ctrl.anchors) {
                           const aRight = ctrl.anchors.getAnchorWorldPosition(rRef.anchor as AnatomicalAnchorName);
                           
                           let pDir: THREE.Vector3 | undefined = undefined;
                           if (Number(rRef.poleX) !== 0 || Number(rRef.poleY) !== 0 || Number(rRef.poleZ) !== 0) {
                               pDir = new THREE.Vector3(Number(rRef.poleX), Number(rRef.poleY), Number(rRef.poleZ));
                           }
                           
                           let fDir: THREE.Vector3 | undefined = undefined;
                           let palmNorm: THREE.Vector3 | undefined = undefined;
                           
                           if (Number(rRef.fDx) !== 0 || Number(rRef.fDy) !== 0 || Number(rRef.fDz) !== 0) {
                               fDir = new THREE.Vector3(Number(rRef.fDx), Number(rRef.fDy), Number(rRef.fDz));
                           }
                           if (Number(rRef.pNx) !== 0 || Number(rRef.pNy) !== 0 || Number(rRef.pNz) !== 0) {
                               palmNorm = new THREE.Vector3(Number(rRef.pNx), Number(rRef.pNy), Number(rRef.pNz));
                           }

                           if (aRight) ctrl.armIK.right.setTarget(aRight, pDir, rRef.mode as 'wrist'|'indexFingertip', fDir, palmNorm);
                       }
                   }
                   
                   // Before IK solve distances
                   let leftInitialDist = -1;
                   let rightInitialDist = -1;
                   if (ctrl.armIK.left?.solverActive && ctrl.getBone('LeftHand')) {
                       const tmp = new THREE.Vector3();
                       ctrl.getBone('LeftHand')!.getWorldPosition(tmp);
                       leftInitialDist = tmp.distanceTo((ctrl.armIK.left as any).targetWorld);
                   }
                   if (ctrl.armIK.right?.solverActive && ctrl.getBone('RightHand')) {
                       const tmp = new THREE.Vector3();
                       ctrl.getBone('RightHand')!.getWorldPosition(tmp);
                       rightInitialDist = tmp.distanceTo((ctrl.armIK.right as any).targetWorld);
                   }

                   ctrl.update(clock.getDelta());
                   globalMetrics.controllerUpdates++;

                   // Throttled UI logging
                   if (globalMetrics.renderFrames % 60 === 0) {
                        const hasLeft = ctrl.armIK.left?.solverActive;
                        const hasRight = ctrl.armIK.right?.solverActive;
                        
                        if (hasLeft || hasRight) {
                            console.groupCollapsed(`[SignVox Diagnostic] Target Selection Pipeline (Frame ${globalMetrics.renderFrames})`);
                            console.log(`IK Enabled: Yes`);
                            console.log(`Solver Executed: Yes (L: ${hasLeft}, R: ${hasRight})`);
                            
                            if (hasLeft && ctrl.getBone('LeftHand')) {
                                const w = new THREE.Vector3();
                                ctrl.getBone('LeftHand')!.getWorldPosition(w);
                                const currentT = (ctrl.armIK.left as any).targetWorld.toArray().map((x:any)=>x.toFixed(2));
                                const currentW = w.toArray().map((x:any)=>x.toFixed(2));
                                const dt = w.distanceTo((ctrl.armIK.left as any).targetWorld);
                                console.log(`[LEFT ARM] Target ID: ${leftIKRef.current.anchor} | Target Resolved: Yes | Target (World): ${currentT.join(', ')}`);
                                console.log(`[LEFT ARM] Valid Bones: Yes | IK Mode: ${leftIKRef.current.mode}`);
                                console.log(`[LEFT ARM] Hand Position After Solve: ${currentW.join(', ')}`);
                                console.log(`[LEFT ARM] Distance -> Before: ${leftInitialDist.toFixed(3)}m, After: ${dt.toFixed(3)}m`);
                                console.log(`[LEFT ARM] Rotations Applied: ${dt < leftInitialDist ? 'Yes (Distance Closed)' : 'Rejected/Saturated'}`);
                            }

                            if (hasRight && ctrl.getBone('RightHand')) {
                                const w = new THREE.Vector3();
                                ctrl.getBone('RightHand')!.getWorldPosition(w);
                                const currentT = (ctrl.armIK.right as any).targetWorld.toArray().map((x:any)=>x.toFixed(2));
                                const currentW = w.toArray().map((x:any)=>x.toFixed(2));
                                const dt = w.distanceTo((ctrl.armIK.right as any).targetWorld);
                                console.log(`[RIGHT ARM] Target ID: ${rightIKRef.current.anchor} | Target Resolved: Yes | Target (World): ${currentT.join(', ')}`);
                                console.log(`[RIGHT ARM] Valid Bones: Yes | IK Mode: ${rightIKRef.current.mode}`);
                                console.log(`[RIGHT ARM] Hand Position After Solve: ${currentW.join(', ')}`);
                                console.log(`[RIGHT ARM] Distance -> Before: ${rightInitialDist.toFixed(3)}m, After: ${dt.toFixed(3)}m`);
                                console.log(`[RIGHT ARM] Rotations Applied: ${dt < rightInitialDist ? 'Yes (Distance Closed)' : 'Rejected/Saturated'}`);
                            }
                            console.groupEnd();
                        }
                   }
               } catch(err: any) {
                   console.error("AVATAR UPDATE CRASH:", err);
                   setErrorMsg(`CRITICAL UPDATE FAILURE: ${err.message || String(err)}`);
                   loopAlive = false; // Systemically lock the chain isolating error propagation natively
                   return;
               }

               const isVis = showIKRef.current;
               Object.values(debugObjects).forEach(obj => obj.visible = isVis);

               // Update Diagnostic Fingertips unconditionally 
               if (ctrl.armIK.left) {
                   const tPos = new THREE.Vector3();
                   if (ctrl.armIK.left.getActualFingertipPosition(tPos)) {
                       debugObjects.lTip.position.copy(tPos);
                       debugObjects.lTip.visible = isVis;
                   } else {
                       debugObjects.lTip.visible = false;
                   }
               }
               if (ctrl.armIK.right) {
                   const tPos = new THREE.Vector3();
                   if (ctrl.armIK.right.getActualFingertipPosition(tPos)) {
                       debugObjects.rTip.position.copy(tPos);
                       debugObjects.rTip.visible = isVis;
                   } else {
                       debugObjects.rTip.visible = false;
                   }
               }

               if (isVis && ikEnabledRef.current && ctrl.armIK.left?.solverActive) {
                   debugObjects.lS.position.copy(ctrl.armIK.left.debugS);
                   debugObjects.lE.position.copy(ctrl.armIK.left.debugE);
                   debugObjects.lW.position.copy(ctrl.armIK.left.debugW);
                   debugObjects.lLine1.geometry.setFromPoints([ctrl.armIK.left.debugS, ctrl.armIK.left.debugE]);
                   debugObjects.lLine2.geometry.setFromPoints([ctrl.armIK.left.debugE, ctrl.armIK.left.debugW]);
                   debugObjects.lPole.geometry.setFromPoints([ctrl.armIK.left.debugE, ctrl.armIK.left.debugE.clone().add(ctrl.armIK.left.debugPole)]);
               } else {
                   debugObjects.lS.visible = false; debugObjects.lE.visible = false; debugObjects.lW.visible = false;
                   debugObjects.lLine1.visible = false; debugObjects.lLine2.visible = false;
                   debugObjects.lPole.visible = false;
               }

               if (isVis && ikEnabledRef.current && ctrl.armIK.right?.solverActive) {
                   debugObjects.rS.position.copy(ctrl.armIK.right.debugS);
                   debugObjects.rE.position.copy(ctrl.armIK.right.debugE);
                   debugObjects.rW.position.copy(ctrl.armIK.right.debugW);
                   debugObjects.rLine1.geometry.setFromPoints([ctrl.armIK.right.debugS, ctrl.armIK.right.debugE]);
                   debugObjects.rLine2.geometry.setFromPoints([ctrl.armIK.right.debugE, ctrl.armIK.right.debugW]);
                   debugObjects.rPole.geometry.setFromPoints([ctrl.armIK.right.debugE, ctrl.armIK.right.debugE.clone().add(ctrl.armIK.right.debugPole)]);
               } else {
                   debugObjects.rS.visible = false; debugObjects.rE.visible = false; debugObjects.rW.visible = false;
                   debugObjects.rLine1.visible = false; debugObjects.rLine2.visible = false;
                   debugObjects.rPole.visible = false;
               }
            }
            
            // Update Animation Metrics directly against DOM refs bridging out-of-sync contexts gracefully
            if (ctrl && timeDisplayRef.current) {
                const act = ctrl.getActiveAction();
                if (act) {
                   timeDisplayRef.current.innerText = `[${ctrl.animationMode}] Time: ${act.time.toFixed(2)}s / ${act.getClip().duration.toFixed(2)}s | ${act.paused ? 'PAUSED' : 'PLAYING'}`;
                } else {
                   timeDisplayRef.current.innerText = `MANUAL MODE (No Clip)`;
                }
            }

            renderer.render(scene, camera);
        };
        animate();

        const handleResize = () => {
            if (!containerRef.current) return;
            const width = window.innerWidth * 0.7;
            camera.aspect = width / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(width, window.innerHeight);
        };
        window.addEventListener('resize', handleResize);

        return () => {
            loopAlive = false;
            globalMetrics.activeLoops = Math.max(0, globalMetrics.activeLoops - 1);
            globalMetrics.activeControllers = Math.max(0, globalMetrics.activeControllers - 1);
            window.removeEventListener('resize', handleResize);
            if (containerRef.current && renderer.domElement) {
                containerRef.current.removeChild(renderer.domElement);
            }
            renderer.dispose();
            Object.values(debugObjects).forEach(obj => {
                if ('geometry' in obj) obj.geometry.dispose();
                if ('material' in obj) {
                    (obj.material as THREE.Material).dispose();
                }
            });
        };
    }, []);

    const updatePose = (side: HandSide, key: string, value: number) => {
        if (!controller) return;
        const hc = side === 'left' ? controller.hands.left : controller.hands.right;
        if (!hc) return;

        if (side === 'left') {
            const next = { ...leftPose, [key]: value };
            setLeftPose(next);
            if (key === 'thumbFlex') hc.thumb.setFlex(value);
            if (key === 'thumbAbd') hc.thumb.setAbduction(value);
            if (key === 'indexCurl') hc.index.setCurl(value);
            if (key === 'middleCurl') hc.middle.setCurl(value);
            if (key === 'ringCurl') hc.ring.setCurl(value);
            if (key === 'pinkyCurl') hc.pinky.setCurl(value);
            if (key === 'spread') { hc.index.setSpread(value); hc.middle.setSpread(value); hc.ring.setSpread(value); hc.pinky.setSpread(value); }
            if (key === 'wristX') hc.setWristRotation(value, 0, 0);
        } else {
            const next = { ...rightPose, [key]: value };
            setRightPose(next);
            if (key === 'thumbFlex') hc.thumb.setFlex(value);
            if (key === 'thumbAbd') hc.thumb.setAbduction(value);
            if (key === 'indexCurl') hc.index.setCurl(value);
            if (key === 'middleCurl') hc.middle.setCurl(value);
            if (key === 'ringCurl') hc.ring.setCurl(value);
            if (key === 'pinkyCurl') hc.pinky.setCurl(value);
            if (key === 'spread') { hc.index.setSpread(value); hc.middle.setSpread(value); hc.ring.setSpread(value); hc.pinky.setSpread(value); }
            if (key === 'wristX') hc.setWristRotation(value, 0, 0);
        }
    };

    const updateIK = (side: HandSide, key: string, value: string | number) => {
        if (!controller || !controller.anchors) return;
        const state = side === 'left' ? leftIK : rightIK;
        const next = { ...state, [key]: value };
        
        if (side === 'left') {
            setLeftIK(next);
            leftIKRef.current = next;
        } else {
            setRightIK(next);
            rightIKRef.current = next;
        }

        const ikController = side === 'left' ? controller.armIK.left : controller.armIK.right;
        if (!ikController) return;

        if (next.anchor === '') {
            ikController.reset();
        } else {
            const anchorTarget = controller.anchors.getAnchorWorldPosition(next.anchor as AnatomicalAnchorName);
            if (anchorTarget) {
                const isZeroPole = Number(next.poleX) === 0 && Number(next.poleY) === 0 && Number(next.poleZ) === 0;
                const pDir = isZeroPole ? undefined : new THREE.Vector3(Number(next.poleX), Number(next.poleY), Number(next.poleZ));

                const isZeroFinger = Number(next.fDx) === 0 && Number(next.fDy) === 0 && Number(next.fDz) === 0;
                const fDir = isZeroFinger ? undefined : new THREE.Vector3(Number(next.fDx), Number(next.fDy), Number(next.fDz));

                const isZeroPalm = Number(next.pNx) === 0 && Number(next.pNy) === 0 && Number(next.pNz) === 0;
                const palmNorm = isZeroPalm ? undefined : new THREE.Vector3(Number(next.pNx), Number(next.pNy), Number(next.pNz));
                
                ikController.setTarget(anchorTarget, pDir, String(next.mode) as 'wrist'|'indexFingertip', fDir, palmNorm);
            }
        }
    };

    const resetHand = (side: HandSide) => {
        if (!controller) return;
        const hc = side === 'left' ? controller.hands.left : controller.hands.right;
        if (hc) hc.reset();
        
        const zeros = { thumbFlex: 0, thumbAbd: 0, indexCurl: 0, middleCurl: 0, ringCurl: 0, pinkyCurl: 0, spread: 0, wristX: 0 };
        if (side === 'left') setLeftPose(zeros); else setRightPose(zeros);
    };

    const resetArm = (side: HandSide) => {
        if (!controller) return;
        updateIK(side, 'anchor', '');
        updateIK(side, 'poleX', 0); updateIK(side, 'poleY', 0); updateIK(side, 'poleZ', 0);
        updateIK(side, 'fDx', 0); updateIK(side, 'fDy', 0); updateIK(side, 'fDz', 0);
        updateIK(side, 'pNx', 0); updateIK(side, 'pNy', 0); updateIK(side, 'pNz', 0);
    };

    const setR44ForeheadTest = (side: HandSide) => {
        if (!controller) return;
        // Load the R4.4 Experimental Forehead Evaluation explicitly resolving Palm boundaries
        updateIK(side, 'anchor', 'forehead');
        updateIK(side, 'mode', 'indexFingertip');
        updateIK(side, 'poleX', side === 'left' ? 1 : -1); updateIK(side, 'poleY', 0); updateIK(side, 'poleZ', -0.5); // Elbow pointed out and slightly back
        updateIK(side, 'fDx', 0); updateIK(side, 'fDy', 1); updateIK(side, 'fDz', -0.5); // Finger pointed UP and BACK (Salute alignment)
        updateIK(side, 'pNx', side === 'left' ? -1 : 1); updateIK(side, 'pNy', -1); updateIK(side, 'pNz', 0); // Palm faces Down / Across
    };

    const setPreset = (side: HandSide, presetName: string) => {
        if (!controller) return;
        const hc = side === 'left' ? controller.hands.left : controller.hands.right;
        if (!hc) return;

        let target = { thumbFlex: 0, thumbAbd: 0, indexCurl: 0, middleCurl: 0, ringCurl: 0, pinkyCurl: 0, spread: 0, wristX: 0 };
        
        if (presetName === 'Closed') {
            target = { thumbFlex: 1, thumbAbd: 0, indexCurl: 1, middleCurl: 1, ringCurl: 1, pinkyCurl: 1, spread: 0, wristX: 0 };
        } else if (presetName === 'Spread') {
            target = { thumbFlex: 0, thumbAbd: -1, indexCurl: 0, middleCurl: 0, ringCurl: 0, pinkyCurl: 0, spread: 0.8, wristX: 0 };
        }

        if (side === 'left') setLeftPose(target); else setRightPose(target);
        hc.thumb.setFlex(target.thumbFlex);
        hc.thumb.setAbduction(target.thumbAbd);
        hc.index.setCurl(target.indexCurl);
        hc.middle.setCurl(target.middleCurl);
        hc.ring.setCurl(target.ringCurl);
        hc.pinky.setCurl(target.pinkyCurl);
        hc.index.setSpread(target.spread); hc.middle.setSpread(target.spread); hc.ring.setSpread(target.spread); hc.pinky.setSpread(target.spread);
    };

    const renderSlider = (side: HandSide, label: string, key: string, min: string, max: string, step: string) => {
        const val = side === 'left' ? (leftPose as any)[key] : (rightPose as any)[key];
        return (
            <div style={{ marginBottom: 2 }}>
                <label style={{ display: 'block', fontSize: 11 }}>{label} ({val.toFixed(2)})</label>
                <input type="range" min={min} max={max} step={step} value={val} onChange={e => updatePose(side, key, parseFloat(e.target.value))} style={{width:'100%'}}/>
            </div>
        );
    };

    const renderIKSlider = (side: HandSide, label: string, key: string, min: string, max: string, step: string) => {
        const val = side === 'left' ? (leftIK as any)[key] : (rightIK as any)[key];
        return (
            <div style={{ marginBottom: 2 }}>
                <label style={{ display: 'block', fontSize: 11 }}>{label} ({Number(val).toFixed(2)})</label>
                <input type="range" min={min} max={max} step={step} value={val} onChange={e => updateIK(side, key, parseFloat(e.target.value))} style={{width:'100%'}}/>
            </div>
        );
    };

    const renderHandPanel = (side: HandSide) => {
        return (
            <div style={{ flex: 1, padding: 5, border: '1px solid #444' }}>
                <h4 style={{margin: '5px 0'}}>{side.toUpperCase()} HAND</h4>
                {renderSlider(side, 'Thumb Flex', 'thumbFlex', '0', '1', '0.05')}
                {renderSlider(side, 'Thumb Abduction', 'thumbAbd', '-1', '1', '0.05')}
                {renderSlider(side, 'Index Curl', 'indexCurl', '0', '1', '0.05')}
                {renderSlider(side, 'Middle Curl', 'middleCurl', '0', '1', '0.05')}
                {renderSlider(side, 'Ring Curl', 'ringCurl', '0', '1', '0.05')}
                {renderSlider(side, 'Pinky Curl', 'pinkyCurl', '0', '1', '0.05')}
                {renderSlider(side, 'Global Spread', 'spread', '-1', '1', '0.05')}
                {renderSlider(side, 'Wrist X-Axis', 'wristX', '-1.5', '1.5', '0.1')}
                
                <div style={{ marginTop: 10, display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    <button style={{fontSize: 10}} onClick={() => setPreset(side, 'Neutral')}>Neutral</button>
                    <button style={{fontSize: 10}} onClick={() => setPreset(side, 'Closed')}>Closed</button>
                    <button style={{fontSize: 10}} onClick={() => setPreset(side, 'Spread')}>Spread</button>
                    <button style={{fontSize: 10}} onClick={() => resetHand(side)}>Reset</button>
                </div>
            </div>
        );
    };

    const renderIKPanel = (side: HandSide) => {
        const val = side === 'left' ? leftIK.anchor : rightIK.anchor;
        const modeVal = side === 'left' ? leftIK.mode : rightIK.mode;
        return (
            <div style={{ flex: 1, padding: 5, border: '1px solid #446', marginTop: 10 }}>
                <h4 style={{margin: '5px 0'}}>{side.toUpperCase()} ARM IK</h4>
                <div style={{ marginBottom: 4 }}>
                    <label style={{ display: 'block', fontSize: 11 }}>Anchor Target</label>
                    <select value={val} onChange={e => updateIK(side, 'anchor', e.target.value)} style={{width:'100%', fontSize:11}}>
                        <option value="">-- None (Rest) --</option>
                        {ANCHORS.map(a => <option key={a} value={a}>{a}</option>)}
                    </select>
                </div>
                <div style={{ marginBottom: 4 }}>
                    <label style={{ display: 'block', fontSize: 11 }}>IK Modality</label>
                    <select value={modeVal} onChange={e => updateIK(side, 'mode', e.target.value)} style={{width:'100%', fontSize:11}}>
                        <option value="wrist">Wrist Pivot (Default Center)</option>
                        <option value="indexFingertip">Index Fingertip Contact</option>
                    </select>
                </div>
                {renderIKSlider(side, 'Pole X (0=Auto)', 'poleX', '-2', '2', '0.1')}
                {renderIKSlider(side, 'Pole Y (0=Auto)', 'poleY', '-2', '2', '0.1')}
                {renderIKSlider(side, 'Pole Z (0=Auto)', 'poleZ', '-2', '2', '0.1')}
                
                <h5 style={{margin: '8px 0 2px 0', color: '#aaf'}}>R4.4 ORIENTATION TARGETS</h5>
                {renderIKSlider(side, 'Finger Dir X', 'fDx', '-1', '1', '0.1')}
                {renderIKSlider(side, 'Finger Dir Y', 'fDy', '-1', '1', '0.1')}
                {renderIKSlider(side, 'Finger Dir Z', 'fDz', '-1', '1', '0.1')}
                {renderIKSlider(side, 'Palm Normal X', 'pNx', '-1', '1', '0.1')}
                {renderIKSlider(side, 'Palm Normal Y', 'pNy', '-1', '1', '0.1')}
                {renderIKSlider(side, 'Palm Normal Z', 'pNz', '-1', '1', '0.1')}
                
                <div style={{ marginTop: 10, display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    <button style={{fontSize: 10}} onClick={() => setR44ForeheadTest(side)}>Test R4.4 Forehead Salute</button>
                    <button style={{fontSize: 10}} onClick={() => resetArm(side)}>Reset {side} Arm</button>
                </div>
            </div>
        );
    };

    return (
        <div style={{ display: 'flex', width: '100vw', height: '100vh', background: '#111', color: '#fff' }}>
            <div ref={containerRef} style={{ width: '70%', height: '100%' }} />

            <div style={{ width: '30%', height: '100%', padding: '10px', boxSizing: 'border-box', overflowY: 'auto' }}>
                <h2 style={{margin: '0 0 10px 0'}}>Controller Diagnostic</h2>
                <h3 style={{margin: '0 0 10px 0'}}>Status: {status}</h3>
                {errorMsg && <p style={{ color: 'red' }}>{errorMsg}</p>}

                {/* ANIMATION PREVIEW DOMAIN */}
                <div style={{ paddingBottom: 10, borderBottom: '1px solid #333', marginBottom: 10, background: '#1c1c3c', padding: 10 }}>
                    <h3 style={{margin: '0 0 5px 0'}}>Animation Preview Mode</h3>
                    <p style={{margin: '4px 0'}}>Current Selected Mode: <strong>{animationMode}</strong></p>
                    <p style={{margin: '4px 0'}}>Runtime Source Metadata:</p>
                    <div style={{ fontVariantNumeric: 'tabular-nums', fontFamily: 'monospace', fontSize: 13, backgroundColor:'#000', padding: 5, margin: '5px 0' }}>
                        <span ref={timeDisplayRef}>MANUAL MODE (No Clip)</span>
                    </div>

                    <div style={{ marginTop: 10, display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                        <button style={{padding: '5px 10px'}} onClick={() => {
                            if (controller) {
                                const act = controller.getActiveAction();
                                if (act) act.paused = !act.paused;
                            }
                        }}>Play / Pause</button>
                        <button style={{padding: '5px 10px'}} onClick={() => {
                            if (controller) {
                                const act = controller.getActiveAction();
                                if (act) {
                                    act.reset();
                                    act.play();
                                }
                            }
                        }}>Restart</button>
                        <button style={{padding: '5px 10px', backgroundColor: '#551111', color: 'white'}} onClick={() => {
                            setAnimationMode('manual');
                            controller?.setMode('manual');
                        }}>Return to Manual</button>
                    </div>

                    <p style={{margin: 2, marginTop: 15, fontSize: 13}}>Target Pipeline Clip:{' '}
                        <select value={animationMode} onChange={e => {
                            const mode = e.target.value as any;
                            setAnimationMode(mode);
                            controller?.setMode(mode);
                        }} style={{maxWidth: '100%'}}>
                            <option value="manual">Manual (No Default Animations)</option>
                            <option value="generic">Generic (Play Mixamo Idle)</option>
                            {controller?.animationClips.map((clip, idx) => (
                                <option key={idx} value={`clip:${clip.name}`}>Clip: {clip.name}</option>
                            ))}
                        </select>
                    </p>
                </div>

                {capabilities && (
                    <div style={{ paddingBottom: 10, borderBottom: '1px solid #333', marginBottom: 10 }}>
                        <p style={{margin: 2}}>Structural Skeleton: {capabilities.isStructuralValid ? 'VALID' : 'INVALID'}</p>
                        <p style={{margin: 2}}>Signing Skeleton: {capabilities.isSigningValid ? 'VALID' : 'INVALID'}</p>
                        <p style={{margin: 2}}>Actual Skeleton Bones: {capabilities.boneCount}</p>
                        <p style={{margin: 2, marginTop: 10, backgroundColor: '#551111', padding: '5px'}}>
                            <label>
                                <input type="checkbox" checked={ikEnabled} onChange={e => {
                                    setIkEnabled(e.target.checked);
                                    if (!e.target.checked && controller) {
                                        controller.armIK.left?.reset();
                                        controller.armIK.right?.reset();
                                    }
                                }} />
                                <strong>MASTER IK ENABLED</strong>
                            </label>
                        </p>
                        <p style={{margin: 2, marginTop: 10}}>
                            <label>
                                <input type="checkbox" checked={showIKGeometry} onChange={e => setShowIKGeometry(e.target.checked)} />
                                Show IK Geometry (S / E / W)
                            </label>
                        </p>
                        <div style={{ marginTop: 10, padding: 5, background: '#111', fontSize: 11, border: '1px solid #444' }}>
                           <p style={{margin:0}}><strong>Dev Instrumentation</strong></p>
                           <p style={{margin:0}}>Active RAF Loops: {globalMetrics.activeLoops}</p>
                           <p style={{margin:0}}>Active Controllers: {globalMetrics.activeControllers}</p>
                           <p style={{margin:0}}>Cumulative Controller Updates: {globalMetrics.controllerUpdates}</p>
                           <p style={{margin:0}}>Cumulative Render Frames: {globalMetrics.renderFrames}</p>
                           <p style={{margin:0}}>Diagnostic Objects Bound: {globalMetrics.diagnosticObjectsAdded}</p>
                        </div>
                    </div>
                )}

                <div style={{ display: 'flex', gap: '5px' }}>
                    {renderHandPanel('left')}
                    {renderHandPanel('right')}
                </div>
                
                <div style={{ display: 'flex', gap: '5px' }}>
                    {renderIKPanel('left')}
                    {renderIKPanel('right')}
                </div>
            </div>
        </div>
    );
};
