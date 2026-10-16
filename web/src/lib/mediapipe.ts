import {
  FaceLandmarker,
  FilesetResolver,
  HandLandmarker,
  PoseLandmarker,
  type NormalizedLandmark,
} from '@mediapipe/tasks-vision';
import type { Point3, PosePoint, RawLandmarkInput } from './contracts';

export type MediaPipeDelegate = 'GPU' | 'CPU';

export const mediaPipeConfig = {
  wasmRoot: import.meta.env.VITE_MEDIAPIPE_WASM_ROOT ?? 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm',
  poseModelUrl: import.meta.env.VITE_MEDIAPIPE_POSE_MODEL_URL ?? 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task',
  handModelUrl: import.meta.env.VITE_MEDIAPIPE_HAND_MODEL_URL ?? 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
  faceModelUrl: import.meta.env.VITE_MEDIAPIPE_FACE_MODEL_URL ?? 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
  /**
   * Landmarker delegate. Measured on this machine over 40 recorded frames
   * (web/bench/recognition-bench.html): all three landmarkers on CPU cost
   * 189 ms/frame; on the GPU delegate 155 ms/frame with the same detections and a
   * mean landmark shift of 0.0055 (normalized units). The GPU delegate is the
   * default and the CPU delegate is the automatic fallback, so a device or
   * browser without a usable GPU path still starts.
   */
  delegate: (import.meta.env.VITE_MEDIAPIPE_DELEGATE as MediaPipeDelegate | undefined) ?? ('GPU' as MediaPipeDelegate),
} as const;

/**
 * Builds one landmarker, preferring `preferred` and falling back to CPU if the
 * requested delegate cannot be created (no WebGL2, blocked GPU process, driver
 * rejection). The fallback is per landmarker so one rejecting model cannot take
 * the whole pipeline down.
 */
async function createLandmarkerWithFallback<T>(
  name: string,
  preferred: MediaPipeDelegate,
  build: (delegate: MediaPipeDelegate) => Promise<T>,
): Promise<{ landmarker: T; delegate: MediaPipeDelegate }> {
  try {
    return { landmarker: await build(preferred), delegate: preferred };
  } catch (error) {
    if (preferred === 'CPU') throw error;
    console.warn(`[MediaPipe] ${name} could not use the ${preferred} delegate, falling back to CPU:`, error);
    return { landmarker: await build('CPU'), delegate: 'CPU' };
  }
}

const toPoint3 = (landmark: NormalizedLandmark): Point3 => ({ x: landmark.x, y: landmark.y, z: landmark.z });
const toPosePoint = (landmark: NormalizedLandmark): PosePoint => ({
  ...toPoint3(landmark),
  visibility: landmark.visibility ?? 0,
  presence: (landmark as any).presence ?? 0,
});

/** Browser Tasks wrapper. It deliberately accepts the unmodified HTMLVideoElement. */
export class BrowserLandmarkerPipeline {
  /** Delegate each landmarker actually runs on, for diagnostics and the report. */
  delegates: Record<'pose' | 'hands' | 'face', MediaPipeDelegate> = { pose: 'CPU', hands: 'CPU', face: 'CPU' };

  private constructor(
    private readonly pose: PoseLandmarker,
    private readonly hands: HandLandmarker,
    private readonly face: FaceLandmarker,
  ) {}

  static async create(preferredDelegate: MediaPipeDelegate = mediaPipeConfig.delegate): Promise<BrowserLandmarkerPipeline> {
    const fileset = await FilesetResolver.forVisionTasks(mediaPipeConfig.wasmRoot);
    const [pose, hands, face] = await Promise.all([
      createLandmarkerWithFallback('PoseLandmarker', preferredDelegate, (delegate) =>
        PoseLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: mediaPipeConfig.poseModelUrl, delegate },
          runningMode: 'VIDEO',
          numPoses: 1,
        })),
      createLandmarkerWithFallback('HandLandmarker', preferredDelegate, (delegate) =>
        HandLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: mediaPipeConfig.handModelUrl, delegate },
          runningMode: 'VIDEO',
          numHands: 2,
        })),
      createLandmarkerWithFallback('FaceLandmarker', preferredDelegate, (delegate) =>
        FaceLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: mediaPipeConfig.faceModelUrl, delegate },
          runningMode: 'VIDEO',
          numFaces: 1,
          outputFaceBlendshapes: false,
          outputFacialTransformationMatrixes: false,
        })),
    ]);
    const pipeline = new BrowserLandmarkerPipeline(pose.landmarker, hands.landmarker, face.landmarker);
    pipeline.delegates = { pose: pose.delegate, hands: hands.delegate, face: face.delegate };
    console.log('[MediaPipe] Landmarkers ready with delegates:', pipeline.delegates);
    return pipeline;
  }

  detect(video: HTMLVideoElement, timestampMs: number): RawLandmarkInput & { diagnostics: any } {
    const t0 = performance.now();
    const poseResult = this.pose.detectForVideo(video, timestampMs);
    const t1 = performance.now();
    const handResult = this.hands.detectForVideo(video, timestampMs);
    const t2 = performance.now();
    const faceResult = this.face.detectForVideo(video, timestampMs);
    const t3 = performance.now();
    
    return {
      pose: poseResult.landmarks[0]?.map(toPosePoint),
      hands: handResult.landmarks.map((landmarks, index) => ({
        label: handResult.handedness[index]?.[0]?.categoryName ?? 'Unknown',
        landmarks: landmarks.map(toPoint3),
      })),
      face: faceResult.faceLandmarks[0]?.map(toPoint3),
      diagnostics: { poseMs: t1 - t0, handsMs: t2 - t1, faceMs: t3 - t2 }
    } as RawLandmarkInput & { diagnostics: any };
  }

  close(): void {
    this.pose.close();
    this.hands.close();
    this.face.close();
  }
}
