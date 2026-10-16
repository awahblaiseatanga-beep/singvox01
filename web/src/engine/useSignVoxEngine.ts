import { useCallback, useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { FEATURE_DIMENSION, type CanonicalFrame, type RawLandmarkInput } from '../lib/contracts';
import { assembleCanonicalFrame, countNonFinite } from '../lib/featureVector';
import { BrowserLandmarkerPipeline, mediaPipeConfig } from '../lib/mediapipe';
import { applyV2Normalization } from '../lib/normalize';
import { SpoterInferenceSession, type InferenceResult } from '../lib/inference';
import {
  describeAssetFailure,
  firstBlockingFailure,
  preflightModelAssets,
  probeAsset,
} from '../lib/assetPreflight';
import { TemporalStabilizer, type StabilizerState } from '../lib/temporalStabilizer';
import {
  TemporalSampler,
  SAMPLE_INTERVAL_MS,
  observationFrom,
  type SampledFrame,
} from '../lib/temporalSampler';
import { evaluateRecognitionGate, type GateDecision } from '../lib/recognitionGate';
import {
  DEFAULT_MODEL_ID,
  getModelSpec,
  avatarClipLabelsFromClipNames,
  hasAvatarClip,
  type ModelId,
  type ModelSpec,
} from '../lib/modelRegistry';
import { mapSignToText, type TranscriptItem } from '../lib/signToText';
import { speakText, stopSpeaking, isSpeechSupported } from '../lib/speech';
import { SpeechRecognitionService, type RecognitionState, type SpokenTextItem } from '../lib/speechRecognition';
import { textToASL } from '../lib/textToASL';
import React from 'react';
import { AvatarController } from '../../../avatar/controller/AvatarController';

/**
 * Large-asset URLs. Local `/public` paths are the default so the app works
 * unchanged from a full checkout. For hosted deployments where the ~180 MB
 * ONNX external-data files or the ~50 MB avatar GLB cannot live alongside
 * the static bundle (e.g. Vercel Hobby's 100 MB CLI upload budget), point
 * these at an external object-storage host instead — no code change needed.
 * The ONNX `.data` sidecar is resolved as `${modelUrl}.data` by inference.ts,
 * so keep each model and its `.data` file side by side under the same base URL.
 */
const AVATAR_GLB_URL = (import.meta.env.VITE_AVATAR_GLB_URL as string | undefined)?.trim()
  || '/avatar/SignVox_Female_Competition_Prototype.glb';
// The two recognition models and their class maps are declared together in
// lib/modelRegistry.ts so a model can never be paired with the wrong vocab.

import {
  SequenceBuffer,
  type SequenceBufferStatus,
  type SequenceQuality,
  type FrameMetadata,
} from '../lib/sequenceBuffer';
import {
  globalProfiler,
  type StageTimings,
  type ColdStartRecord,
} from '../lib/latencyProfiler';
import {
  runRepeatabilityTest,
  DiagnosticSession,
  type RepeatabilityReport,
  type TrialRecord,
} from '../lib/diagnostics';

type Metrics = {
  cameraFps: number;
  /** Buffer frames written per second (fixed 125 ms grid; < 8 means the page is behind). */
  processingFps: number;
  /** Real MediaPipe observations completed per second (the device's true ceiling). */
  observationFps: number;
  /** True when the newest buffered frame is a blend of two real observations. */
  interpolated: boolean;
  mpLatencyMs: number;
  mpPoseMs: number;
  mpHandsMs: number;
  mpFaceMs: number;
  featureLatencyMs: number;
  normLatencyMs: number;
  overallLatencyMs: number;
  dropped: number;
  timestampMs: number;
  dimensions: string;
  frame?: CanonicalFrame;
  /** Delegate each landmarker runs on, e.g. "GPU/GPU/GPU" (pose/hands/face). */
  mpDelegate: string;
  normalizedFinite: { nan: number; inf: number };
  sequenceStatus?: SequenceBufferStatus;
  sequenceQuality?: SequenceQuality | null;
};

type Snapshot = {
  rawLength: number;
  normalizedLength: number;
  leftHand: number[];
  rightHand: number[];
  poseXyz: number[];
  visibility: number;
  posePresence: number;
  face: number[];
  min: number;
  max: number;
  nan: number;
  inf: number;
  presence: CanonicalFrame['presence'];
  assignments: CanonicalFrame['handAssignments'];
};


/**
 * @param avatarSurface which screen currently owns the single avatar viewport.
 *   The renderer is bound to that screen's element, so switching surfaces
 *   rebinds it instead of leaving the canvas orphaned in an unmounted page.
 */
export function useSignVoxEngine(avatarSurface: 'product' | 'diagnostics' | 'none' = 'product') {
  const videoRef = useRef<HTMLVideoElement>(null);
  const avatarCanvasRef = useRef<HTMLDivElement>(null);
  const avatarCtrlRef = useRef<AvatarController | null>(null);
  const [avatarStatus, setAvatarStatus] = useState<string>('Initializing');
  const [activeModel, setActiveModel] = useState<ModelId>(DEFAULT_MODEL_ID);
  const activeModelRef = useRef<ModelId>(DEFAULT_MODEL_ID);

  const pipelineRef = useRef<BrowserLandmarkerPipeline>();
  const streamRef = useRef<MediaStream>();
  const activeRef = useRef(false);
  const workingRef = useRef(false);
  const captureNextRef = useRef(false);
  const lastProcessRef = useRef(0);
  const lastProcessedTimestampRef = useRef(0);
  const lastProcessedCountRef = useRef(0);
  const lastObservedCountRef = useRef(0);
  /** Real MediaPipe observations completed since the session started. */
  const observedRef = useRef(0);
  /** Fixed-cadence sampler: decouples buffer writes from detector completions. */
  const temporalSamplerRef = useRef(new TemporalSampler(SAMPLE_INTERVAL_MS));
  const cameraFpsRef = useRef(0);
  const lastVideoTimeRef = useRef(-1);
  const cameraFramesRef = useRef(0);
  const lastFpsSampleRef = useRef(performance.now());
  const processedRef = useRef(0);
  const droppedRef = useRef(0);
  const [status, setStatus] = useState('Camera stopped');
  const [error, setError] = useState<string>();
  const [metrics, setMetrics] = useState<Metrics>();
  const [snapshot, setSnapshot] = useState<Snapshot>();
  const [syntheticTest, setSyntheticTest] = useState<InferenceResult & { nan: number; inf: number; passed: boolean }>();
  const sequenceBufferRef = useRef(new SequenceBuffer());
  const inferenceSessionRef = useRef<SpoterInferenceSession>();
  const inferringRef = useRef(false);
  const [liveResult, setLiveResult] = useState<InferenceResult>();
  const stabilizerRef = useRef(new TemporalStabilizer());
  const [stableState, setStableState] = useState<StabilizerState>();
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const lastMetricsDisplayRef = useRef(0);
  const [latestDetection, setLatestDetection] = useState<RawLandmarkInput | null>(null);
  // Input-validity gate state, surfaced so the UI can explain a paused window
  // instead of appearing to have silently stopped recognising signs.
  const [recognitionGate, setRecognitionGate] = useState<GateDecision>();
  const recognitionGateRef = useRef<GateDecision | undefined>(undefined);
  const [showSkeleton, setShowSkeleton] = useState(false);

  // Latency Profiler Diagnostics State & Refs
  const lastDetectRef = useRef(0);
  const bufferReadyRecordedRef = useRef(false);
  const [coldStartReport, setColdStartReport] = useState<Partial<ColdStartRecord>>({});
  const [steadyStateReport, setSteadyStateReport] = useState<Record<string, StageTimings>>({});

  // Phase 1.1 Diagnostics State
  const [repeatabilityReport, setRepeatabilityReport] = useState<RepeatabilityReport | null>(null);
  const [runningRepeatability, setRunningRepeatability] = useState(false);
  const diagnosticSessionRef = useRef<DiagnosticSession>(new DiagnosticSession());
  const [diagnosticTrials, setDiagnosticTrials] = useState<TrialRecord[]>([]);
  const [targetLabelInput, setTargetLabelInput] = useState('');
  const [diagnosticNotice, setDiagnosticNotice] = useState<string | null>(null);

  const [autoSpeak, setAutoSpeak] = useState(false);
  const autoSpeakRef = useRef(false);

  // Independent Microphone State
  const [spokenText, setSpokenText] = useState<SpokenTextItem[]>([]);
  const [interimSpokenText, setInterimSpokenText] = useState<string>('');
  const [hearingState, setHearingState] = useState<RecognitionState>('idle');
  const recognizerRef = useRef<SpeechRecognitionService | null>(null);

  const [isDiagnosticMode, setIsDiagnosticMode] = useState(() => window.location.hash === '#avatar-diagnostic');

  useEffect(() => {
     activeModelRef.current = activeModel;
  }, [activeModel]);

  useEffect(() => {
     const hashChangeListener = () => setIsDiagnosticMode(window.location.hash === '#avatar-diagnostic');
     window.addEventListener('hashchange', hashChangeListener);
     return () => window.removeEventListener('hashchange', hashChangeListener);
  }, []);

  // Remeasure hook for the avatar renderer, populated by the mounting effect below.
  // Pages call it when they become visible so the viewport matches its container
  // even if the container was display:none while it was hidden.
  const avatarRemeasureRef = useRef<(() => void) | null>(null);

  // AvatarController 3D Canvas Mounting
  useEffect(() => {
     if (avatarSurface === 'none' || !avatarCanvasRef.current) return;

     const container = avatarCanvasRef.current;
     const scene = new THREE.Scene();
     scene.background = new THREE.Color(0x181824);

     const width = container.clientWidth || 400;
     const height = container.clientHeight || 500;

     const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
     camera.position.set(0, 1.25, 3.8);

     // WebGL is a hard requirement for this viewport. Three.js throws straight out
     // of the constructor when no context can be created (GPU process blocked,
     // hardware acceleration off, headless/remote browser), and an exception
     // thrown inside this effect unmounts the page instead of showing anything.
     // Report it as an avatar failure, which AvatarStudioPage renders visibly.
     let renderer: THREE.WebGLRenderer;
     try {
        renderer = new THREE.WebGLRenderer({ antialias: true });
     } catch (cause) {
        const detail = cause instanceof Error ? cause.message : String(cause);
        console.error('[Avatar] WebGL renderer could not be created:', cause);
        setAvatarStatus(`Error: 3D graphics (WebGL) are unavailable in this browser (${detail})`);
        return;
     }
     renderer.setSize(width, height);
     renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
     container.appendChild(renderer.domElement);

     // A context lost after start leaves a silent black viewport.
     const handleContextLost = (event: Event) => {
        event.preventDefault();
        console.error('[Avatar] WebGL context lost.');
        setAvatarStatus('Error: the 3D graphics context was lost. Reload the page to restore the avatar.');
     };
     renderer.domElement.addEventListener('webglcontextlost', handleContextLost);

     const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 2);
     hemiLight.position.set(0, 5, 0);
     scene.add(hemiLight);

     const dirLight = new THREE.DirectionalLight(0xffffff, 2);
     dirLight.position.set(0, 5, 5);
     scene.add(dirLight);

     const ctrl = new AvatarController();
     setAvatarStatus('Loading GLB model…');

     // Probe first: a GLB that the host answers with the SPA document makes
     // three.js fail with `Unexpected token '<'`, which reads like a broken model
     // rather than a file that was never deployed. The resolved URL is included
     // because a stale VITE_AVATAR_GLB_URL is the usual cause.
     probeAsset('avatar model (GLB)', AVATAR_GLB_URL)
        .then((probe) => {
           if (!probe.ok && probe.conclusive) throw new Error(describeAssetFailure(probe));
           return ctrl.loadGLB(AVATAR_GLB_URL);
        })
        .then(() => {
           if (ctrl.rootScene) scene.add(ctrl.rootScene);
           avatarCtrlRef.current = ctrl;
           setAvatarStatus('Ready');
        })
        .catch(err => {
           const detail = err instanceof Error ? err.message : String(err);
           console.error('[Avatar] GLB load failure:', err);
           setAvatarStatus(`Error: ${detail} (${AVATAR_GLB_URL})`);
        });

     const clock = new THREE.Clock();
     let animLoopAlive = true;

     const animate = () => {
        if (!animLoopAlive) return;
        requestAnimationFrame(animate);
        if (ctrl) {
           try {
              ctrl.update(clock.getDelta());
           } catch (e) {
              console.error('[Avatar] Render loop error:', e);
           }
        }
        renderer.render(scene, camera);
     };
     animate();

     const handleResize = () => {
        if (!container) return;
        const w = container.clientWidth;
        const h = container.clientHeight;
        // A container hidden behind an inactive page reports 0x0; skip rather
        // than collapsing the projection. The observer re-measures on reveal.
        if (w === 0 || h === 0) return;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
     };
     window.addEventListener('resize', handleResize);
     // Container-driven remeasure: page switches, orientation changes and
     // sidebar/layout changes all land here without reloading the GLB.
     const containerObserver = new ResizeObserver(handleResize);
     containerObserver.observe(container);
     avatarRemeasureRef.current = handleResize;

     return () => {
        animLoopAlive = false;
        window.removeEventListener('resize', handleResize);
        containerObserver.disconnect();
        renderer.domElement.removeEventListener('webglcontextlost', handleContextLost);
        avatarRemeasureRef.current = null;
        avatarCtrlRef.current = null;
        if (container.contains(renderer.domElement)) {
           container.removeChild(renderer.domElement);
        }
        renderer.dispose();
     };
  }, [avatarSurface]);

  useEffect(() => {
     const s = new SpeechRecognitionService();
     s.setHooks({
         onStateChange: (st) => setHearingState(st),
         onInterimResult: (t) => setInterimSpokenText(t),
         onFinalResult: (t) => {
             const representation = textToASL(t);
             setSpokenText(prev => [...prev, {
                 id: `${performance.now()}-${Math.random()}`,
                 text: t,
                 timestamp: performance.now(),
                 asl: representation
             }]);
         }
     });
     recognizerRef.current = s;
     return () => { s.stop(); };
  }, []);

  const toggleAutoSpeak = (e: React.ChangeEvent<HTMLInputElement>) => {
      setAutoSpeak(e.target.checked);
      autoSpeakRef.current = e.target.checked;
  };

  const speakLatest = () => {
      if (transcript.length === 0) return;
      speakText(transcript[transcript.length - 1].displayText);
  };

  const runSyntheticTest = async () => {
    try {
      const spec = getModelSpec(activeModelRef.current);
      const modelUrl = spec.modelUrl;
      const vocabMap = spec.vocab;
      const session = await SpoterInferenceSession.create(modelUrl);
      const dummy = new Float32Array(60 * FEATURE_DIMENSION).fill(0.1);
      const result = await session.predict(dummy, vocabMap);
      let nanCount = 0, infCount = 0;
      for (const logit of result.logits) {
          if (Number.isNaN(logit)) nanCount++;
          else if (!Number.isFinite(logit)) infCount++;
      }
      setSyntheticTest({ ...result, nan: nanCount, inf: infCount, passed: true });
    } catch (e) {
      console.error(e);
      alert(String(e));
    }
  };

  useEffect(() => () => {
    activeRef.current = false;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    pipelineRef.current?.close();
  }, []);

  const handleRunRepeatability = async () => {
    if (!sequenceBufferRef.current.isReady) {
      alert('Sequence buffer must be full (60 frames) to run the repeatability test.');
      return;
    }
    const flatBuffer = sequenceBufferRef.current.getFlattenedBuffer();
    if (!flatBuffer || !inferenceSessionRef.current) {
      alert('Inference session or buffer not available.');
      return;
    }

    setRunningRepeatability(true);
    setRepeatabilityReport(null);
    try {
      const vocabMap = getModelSpec(activeModelRef.current).vocab;
      const report = await runRepeatabilityTest(inferenceSessionRef.current, flatBuffer, vocabMap, 10, 1e-4);
      setRepeatabilityReport(report);
      setDiagnosticNotice(`10x repeatability test completed: ${report.isRepeatable ? 'Deterministic' : 'Non-deterministic'}.`);
    } catch (err) {
      console.error('[Diagnostic] Repeatability test failed:', err);
      alert(`Repeatability test failed: ${err}`);
    } finally {
      setRunningRepeatability(false);
    }
  };

  const handleRecordTrial = () => {
    if (!sequenceBufferRef.current.isReady) {
      alert('Sequence buffer must be full (60 frames) before capturing a trial.');
      return;
    }
    const flatBuffer = sequenceBufferRef.current.getFlattenedBuffer();
    const quality = sequenceBufferRef.current.getSequenceQuality();
    if (!flatBuffer || !quality || !liveResult) {
      alert('Waiting for a valid model prediction and buffer quality metrics.');
      return;
    }

    try {
      const trial = diagnosticSessionRef.current.recordTrial(
        flatBuffer,
        quality,
        liveResult.topK,
        liveResult.latencyMs,
        targetLabelInput
      );
      setDiagnosticTrials(diagnosticSessionRef.current.getTrials());
      setDiagnosticNotice(`Trial #${trial.trialIndex} recorded (${targetLabelInput ? targetLabelInput.toUpperCase() : 'unlabeled'}).`);
    } catch (err) {
      alert(String(err));
    }
  };

  const handleExportSession = () => {
    if (diagnosticTrials.length === 0) {
      alert('No trials recorded to export.');
      return;
    }
    const jsonStr = diagnosticSessionRef.current.exportJsonString();
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `signvox_diagnostic_session_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setDiagnosticNotice('Diagnostic session exported to local JSON.');
  };

  const handleClearSession = () => {
    diagnosticSessionRef.current.clear();
    setDiagnosticTrials([]);
    setDiagnosticNotice('Diagnostic session cleared.');
  };

  const start = async () => {
    if (activeRef.current) return;
    setError(undefined);
    setStatus('Requesting camera and initializing tracking…');
    setTranscript([]);

    const spec = getModelSpec(activeModelRef.current);
    stabilizerRef.current = new TemporalStabilizer(spec.stabilizerConfig);
    sequenceBufferRef.current.reset();
    temporalSamplerRef.current.reset();
    processedRef.current = 0;
    observedRef.current = 0;
    lastProcessedCountRef.current = 0;
    lastObservedCountRef.current = 0;
    bufferReadyRecordedRef.current = false;
    globalProfiler.resetSteadyState();

    try {
      const modelUrl = spec.modelUrl;

      globalProfiler.markColdStartBegin('cameraInit');
      globalProfiler.markColdStartBegin('mediaPipeInit');
      globalProfiler.markColdStartBegin('onnxInit');

      // 1. Preflight the model assets, then load ONNX and warm the kernels up.
      //    Neither graph can be committed: `spoter_v2_model.onnx.data` is 187 MB
      //    and GitHub blocks files over 100 MB. A deployment that has not been
      //    given VITE_SPOTER_V2_URL / VITE_SPOTER_PILOT_URL therefore requests
      //    `/spoter_v2_model.onnx`, which web/vercel.json rewrites to index.html —
      //    HTTP 200 and `text/html`. ONNX Runtime then tries to parse the SPA
      //    document as a protobuf graph and its error reads like a code fault.
      //    Probe first so the cause is unambiguous instead of inferred.
      const onnxPromise = preflightModelAssets(spec.displayName, modelUrl)
        .then((probes) => {
          const failure = firstBlockingFailure(probes);
          if (failure) throw new Error(`Sign model asset missing — ${describeAssetFailure(failure)}`);
          return SpoterInferenceSession.create(modelUrl);
        })
        .then(async (session) => {
          globalProfiler.markColdStartEnd('onnxInitMs', 'onnxInit');
          console.log(`[App] ONNX session created for ${modelUrl}. Running one-time kernel warm-up...`);
          const warmupStart = performance.now();
          await session.warmup();
          const warmupMs = performance.now() - warmupStart;
          globalProfiler.markColdStartEnd('onnxFirstInferenceMs', 'onnxInit');
          inferenceSessionRef.current = session;
          console.log(`[App] ONNX warmed up in ${warmupMs.toFixed(1)}ms.`);
          setStatus(`Live — using ${spec.displayName} model`);
        })
        .catch((cause) => {
          console.error('[App] Background ONNX load failed:', cause);
          setError(`ONNX model error: ${cause instanceof Error ? cause.message : String(cause)}`);
        });

      // 2. Camera stream request
      const cameraPromise = (async () => {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        });
        streamRef.current = stream;
        if (!videoRef.current) throw new Error('Camera element is unavailable.');
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        globalProfiler.markColdStartEnd('cameraPermissionAndReadyMs', 'cameraInit');
        return stream;
      })();

      // 3. MediaPipe Landmarker Pipeline creation
      const pipelinePromise = BrowserLandmarkerPipeline.create().then((pipe) => {
        globalProfiler.markColdStartEnd('mediaPipeInitMs', 'mediaPipeInit');
        return pipe;
      });

      // Progressive Activation: Wait ONLY for Camera + MediaPipe to start visual tracking immediately!
      const [, pipeline] = await Promise.all([cameraPromise, pipelinePromise]);
      pipelineRef.current = pipeline;
      activeRef.current = true;
      setStatus(`Camera & Tracking Active — loading ${spec.displayName} model…`);
      requestAnimationFrame(processLoop);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      setStatus('Unable to start');
      streamRef.current?.getTracks().forEach((track) => track.stop());
    }
  };

  const stop = () => {
    activeRef.current = false;
    sequenceBufferRef.current.reset();
    temporalSamplerRef.current.reset();
    bufferReadyRecordedRef.current = false;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = undefined;
    pipelineRef.current?.close(); pipelineRef.current = undefined;
    stabilizerRef.current.reset();
    setLatestDetection(null);
    setStatus('Camera stopped');
  };

  const processLoop = (now: number) => {
    if (!activeRef.current) return;
    const video = videoRef.current;
    const pipeline = pipelineRef.current;
    if (video && pipeline && video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
      if (video.currentTime !== lastVideoTimeRef.current) { cameraFramesRef.current += 1; lastVideoTimeRef.current = video.currentTime; }
      const elapsedSinceSample = now - lastFpsSampleRef.current;
      if (elapsedSinceSample >= 1000) {
        const cameraFps = (cameraFramesRef.current * 1000) / elapsedSinceSample;
        cameraFramesRef.current = 0; lastFpsSampleRef.current = now;
        cameraFpsRef.current = cameraFps;
        setMetrics((previous) => previous ? { ...previous, cameraFps } : previous);
      }

      const DETECT_INTERVAL_MS = 60; // Up to ~16.6 fps for smooth visual overlay
      const elapsedSinceDetect = now - lastDetectRef.current;

      if (elapsedSinceDetect >= DETECT_INTERVAL_MS) {
        if (workingRef.current) {
          droppedRef.current += 1;
        } else {
          workingRef.current = true;
          lastDetectRef.current = now;
          const frameStart = performance.now();
          try {
            const mpStart = performance.now();
            const rawDetectionOutput = pipeline.detect(video, now);
            const mpEnd = performance.now();
            setLatestDetection(rawDetectionOutput);

            const mpDuration = mpEnd - mpStart;
            globalProfiler.recordSample('mediaPipeDetect', mpDuration);
            if (rawDetectionOutput.diagnostics) {
              globalProfiler.recordSample('poseDetect', rawDetectionOutput.diagnostics.poseMs);
              globalProfiler.recordSample('handsDetect', rawDetectionOutput.diagnostics.handsMs);
              globalProfiler.recordSample('faceDetect', rawDetectionOutput.diagnostics.faceMs);
            }

            if (rawDetectionOutput.hands && rawDetectionOutput.hands.length > 0) {
              globalProfiler.recordFirstHandDetected();
            }

            // FEATURE ASSEMBLY + V2 NORMALIZATION: one real observation per completed
            // detection. Nothing about this stage changed; only how often its result is
            // written into the temporal buffer (see TemporalSampler below).
            const featureStart = performance.now();
            const frame = assembleCanonicalFrame(rawDetectionOutput);
            const featureEnd = performance.now();
            globalProfiler.recordSample('featureExtraction', featureEnd - featureStart);

            const normStart = performance.now();
            const normalized = applyV2Normalization(frame.raw);
            const normEnd = performance.now();
            globalProfiler.recordSample('v2Normalization', normEnd - normStart);

            const finite = countNonFinite(normalized);
            const latencyMs = performance.now() - frameStart;
            observedRef.current += 1;

            // SEQUENCE BUFFERING: the sampler emits on the fixed 125 ms grid that the
            // SPOTER V2 contract expects, using this observation plus the previous one.
            // A grid point between two observations is their linear blend; a grid point
            // at or after this observation is the observation itself. Previously a frame
            // was written only when a detection completed (>150 ms apart), so the window
            // filled at the detection rate and live motion ran slower than training.
            temporalSamplerRef.current.observe(observationFrom(frame, normalized, now));
            const samples: SampledFrame[] = temporalSamplerRef.current.sampleUntil(now);

            for (const sample of samples) {
              processedRef.current += 1;
              lastProcessedTimestampRef.current = sample.timestampMs;
              const sampleFinite = countNonFinite(sample.normalized);

              const metadata: FrameMetadata = {
                presence: {
                  leftHand: sample.presence.leftHand,
                  rightHand: sample.presence.rightHand,
                  pose: sample.presence.pose,
                  face: sample.presence.face,
                },
                nonFiniteCount: sampleFinite.nan + sampleFinite.inf,
                timestampMs: sample.timestampMs,
              };

              sequenceBufferRef.current.push(sample.normalized, metadata);
              if (sequenceBufferRef.current.length === 1) {
                globalProfiler.markColdStartBegin('bufferWarmup');
              }
              if (!bufferReadyRecordedRef.current && sequenceBufferRef.current.isReady) {
                bufferReadyRecordedRef.current = true;
                globalProfiler.markColdStartEnd('bufferWarmupMs', 'bufferWarmup');
              }
            }

            if (samples.length > 0) {
              const newest = samples[samples.length - 1];
              const currentSeqStatus = sequenceBufferRef.current.getStatus();
              const currentSeqQuality = sequenceBufferRef.current.getSequenceQuality();

              if (now - lastMetricsDisplayRef.current >= 500) {
                const elapsed = now - lastMetricsDisplayRef.current;
                const processingFps = ((processedRef.current - lastProcessedCountRef.current) * 1000) / Math.max(elapsed, 1);
                const observationFps = ((observedRef.current - lastObservedCountRef.current) * 1000) / Math.max(elapsed, 1);
                lastProcessedCountRef.current = processedRef.current;
                lastObservedCountRef.current = observedRef.current;
                lastMetricsDisplayRef.current = now;
                setMetrics({
                  cameraFps: cameraFpsRef.current,
                  processingFps,
                  observationFps,
                  interpolated: newest.interpolated,
                  mpLatencyMs: mpDuration,
                  mpPoseMs: rawDetectionOutput.diagnostics.poseMs,
                  mpHandsMs: rawDetectionOutput.diagnostics.handsMs,
                  mpFaceMs: rawDetectionOutput.diagnostics.faceMs,
                  featureLatencyMs: featureEnd - featureStart,
                  normLatencyMs: normEnd - normStart,
                  overallLatencyMs: latencyMs,
                  dropped: droppedRef.current,
                  timestampMs: now,
                  dimensions: `${video.videoWidth}×${video.videoHeight}`,
                  frame,
                  mpDelegate: `${pipeline.delegates.pose}/${pipeline.delegates.hands}/${pipeline.delegates.face}`,
                  normalizedFinite: finite,
                  sequenceStatus: currentSeqStatus,
                  sequenceQuality: currentSeqQuality,
                });
                setColdStartReport(globalProfiler.getColdStart());
                setSteadyStateReport(globalProfiler.getSteadyStateReport());
              }

              // Input-validity gate: a window whose landmarks are largely missing is
              // out of distribution for both models and provokes confident attractor
              // classes (measured: an all-zero window returns SICK 0.856). Such a
              // window is dropped before it can influence the transcript.
              const liveQuality = sequenceBufferRef.current.getSequenceQuality();
              const gate = evaluateRecognitionGate({
                anyHandPercent: liveQuality?.anyHandPercent ?? 0,
                posePercent: liveQuality?.posePercent ?? 0,
                frames: sequenceBufferRef.current.length,
              });
              if (gate.allowed) {
                if (recognitionGateRef.current?.reason !== gate.reason) {
                  recognitionGateRef.current = gate;
                  setRecognitionGate(gate);
                }
              } else if (sequenceBufferRef.current.isReady) {
                // Clear pending evidence so a stale window cannot commit later.
                stabilizerRef.current.reset();
                if (recognitionGateRef.current?.reason !== gate.reason) {
                  recognitionGateRef.current = gate;
                  setRecognitionGate(gate);
                }
              }

              if (gate.allowed && sequenceBufferRef.current.isReady && !inferringRef.current && inferenceSessionRef.current) {
                const flatBuffer = sequenceBufferRef.current.getFlattenedBuffer();
                if (flatBuffer) {
                  inferringRef.current = true;
                  const vocabMap = getModelSpec(activeModelRef.current).vocab;

                  const onnxStart = performance.now();
                  inferenceSessionRef.current.predict(flatBuffer, vocabMap).then(res => {
                    const onnxEnd = performance.now();
                    res.latencyMs = onnxEnd - onnxStart;
                    globalProfiler.recordSample('onnxInference', res.latencyMs);
                    setLiveResult(res);
                    const top = res.topK[0];
                    if (top) {
                      const stabStart = performance.now();
                      const state = stabilizerRef.current.process({
                        classIndex: top.classIndex,
                        className: top.className,
                        confidence: top.confidence,
                        timestampMs: now
                      });
                      globalProfiler.recordSample('stabilizerProcess', performance.now() - stabStart);

                      if (state.committedSign) {
                        const newId = `${now}-${state.committedSign}`;
                        const display = mapSignToText(state.committedSign!);
                        // Recognition and animation are separate: record whether the
                        // loaded GLB can actually play this sign so the UI can say so.
                        const clipAvailable = hasAvatarClip(state.committedSign!, avatarClipLabels());
                        setTranscript(prev => [...prev, {
                          id: newId,
                          signId: state.committedSign!,
                          displayText: display,
                          timestamp: now,
                          at: Date.now(),
                          avatarClipAvailable: clipAvailable
                        }]);

                        // ROUTE COMMITTED SIGN TO AVATAR CONTROLLER
                        if (avatarCtrlRef.current && state.committedSign) {
                          avatarCtrlRef.current.playSignByLabel(state.committedSign);
                        }

                        if (autoSpeakRef.current) {
                          speakText(display);
                        }
                      }
                      setStableState(state);
                    }
                    inferringRef.current = false;
                  }).catch(err => {
                    console.error(err);
                    inferringRef.current = false;
                  });
                }
              }

              if (captureNextRef.current) {
                captureNextRef.current = false;
                const values = Array.from(normalized);
                setSnapshot({
                  rawLength: frame.raw.length, normalizedLength: normalized.length,
                  leftHand: values.slice(0, 6), rightHand: values.slice(63, 69), poseXyz: values.slice(126, 129),
                  visibility: values[129], posePresence: values[130], face: values.slice(291, 297),
                  min: Math.min(...values), max: Math.max(...values), nan: finite.nan, inf: finite.inf,
                  presence: frame.presence, assignments: frame.handAssignments,
                });
              }
            }
            globalProfiler.recordSample('endToEndFrame', performance.now() - frameStart);
          } catch (cause) { setError(cause instanceof Error ? cause.message : String(cause)); }
          finally { workingRef.current = false; }
        }
      }
    }
    requestAnimationFrame(processLoop);
  };

  const frame = metrics?.frame;
  const mark = (value: boolean | undefined) => value ? '✓' : '✕';

  const focusTranscript = () => {
    document.getElementById('signvox-transcript')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Stable handle the views use to remeasure the avatar viewport on reveal.
  const remeasureAvatar = useCallback(() => {
    avatarRemeasureRef.current?.();
  }, []);

  /** Sign labels the loaded avatar GLB can actually animate (empty until it loads). */
  const avatarClipLabels = useCallback((): string[] => {
    return avatarClipLabelsFromClipNames((avatarCtrlRef.current?.animationClips ?? []).map((clip) => clip.name));
  }, []);

  const avatarCanPlay = useCallback(
    (label: string) => hasAvatarClip(label, avatarClipLabels()),
    [avatarClipLabels],
  );

  const activeModelSpec: ModelSpec = getModelSpec(activeModel);

  return {
    // view refs
    videoRef, avatarCanvasRef, avatarCtrlRef, pipelineRef, streamRef, activeRef, workingRef,
    captureNextRef, inferenceSessionRef, inferringRef, stabilizerRef, sequenceBufferRef,
    diagnosticSessionRef, recognizerRef, autoSpeakRef, activeModelRef,
    // profiling refs
    lastProcessRef, lastProcessedTimestampRef, cameraFpsRef, lastVideoTimeRef, cameraFramesRef,
    lastFpsSampleRef, processedRef, droppedRef, lastMetricsDisplayRef,    lastDetectRef, bufferReadyRecordedRef, temporalSamplerRef, observedRef,
    // status + telemetry state
    status, setStatus, error, setError, metrics, setMetrics, snapshot, setSnapshot,
    syntheticTest, setSyntheticTest, coldStartReport, setColdStartReport,
    steadyStateReport, setSteadyStateReport,
    // recognition state
    activeModel, setActiveModel, activeModelSpec, liveResult, setLiveResult, stableState, setStableState,
    avatarClipLabels, avatarCanPlay, recognitionGate,
    transcript, setTranscript, latestDetection, setLatestDetection,
    showSkeleton, setShowSkeleton,
    // avatar state
    avatarStatus, setAvatarStatus,
    // diagnostics state
    repeatabilityReport, setRepeatabilityReport, runningRepeatability, setRunningRepeatability,
    diagnosticTrials, setDiagnosticTrials, targetLabelInput, setTargetLabelInput,
    diagnosticNotice, setDiagnosticNotice,
    // speech state
    autoSpeak, setAutoSpeak, spokenText, setSpokenText, interimSpokenText, setInterimSpokenText,
    hearingState, setHearingState,
    // diagnostic route flag
    isDiagnosticMode, setIsDiagnosticMode,
    // imported speech helpers surfaced for the views
    isSpeechSupported, stopSpeaking,
    // actions
    toggleAutoSpeak, speakLatest, runSyntheticTest, handleRunRepeatability, handleRecordTrial,
    handleExportSession, handleClearSession, start, stop, processLoop,
    // derived
    frame, mark, focusTranscript, remeasureAvatar,
  };
}

export type SignVoxEngine = ReturnType<typeof useSignVoxEngine>;
