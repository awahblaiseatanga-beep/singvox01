import * as ort from 'onnxruntime-web';
import { ASL_VOCAB } from './vocab';
import { FEATURE_DIMENSION } from './contracts';
import { assertModelOutputSize } from './modelRegistry';
import wasmMjsUrl from '../onnxruntime/ort-wasm-simd-threaded.mjs?url';

export type InferenceResult = {
  logits: Float32Array;
  topK: { classIndex: number; className: string; confidence: number }[];
  latencyMs: number;
  provider: string;
};

/**
 * Runtime switches for ORT Web.
 *
 * `proxy` runs the WASM backend inside an ORT-managed Web Worker. MediaPipe's
 * `detectForVideo` is a synchronous call that blocks the main thread for ~150 ms,
 * so an in-page ONNX inference of the same order serialises with landmark
 * detection. Measured live on this machine (dev server, #diagnostics, real camera,
 * 79-class baseline, one 60x366 window per detection):
 *
 *   proxy off : 2.8 landmark observations/s, onnxInference 174.8 ms (main thread)
 *   proxy on  : 6.3 landmark observations/s, onnxInference 292.7 ms (worker)
 *
 * So the worker more than doubles how often the signer is actually observed and
 * keeps the main thread free between detects. It is nevertheless OFF by default:
 * with Vite's production bundle, ORT instantiates its worker from a URL derived
 * from ORT's own `import.meta.url`, which the bundler collapses onto the single
 * application chunk. The worker then loads the app bundle and dies with
 * "Uncaught ReferenceError: document is not defined", which also leaves ORT's
 * one-shot WASM init failed, so the in-page retry cannot recover either. That was
 * reproduced against `vite preview` of the production build; see
 * docs/RECOGNITION_SPEED_OPTIMIZATION_REPORT.md. The setting stays available as
 * an opt-in for development (`VITE_ORT_WASM_PROXY=1`) until the worker URL is
 * resolved for production builds.
 *
 * The worker resolves its own loader script, so `wasmPaths` must be absolute
 * URLs; a root-relative path that resolves fine in the page is not fetchable
 * from the worker and surfaces as "worker not ready".
 */
export type OrtRuntime = { proxy: boolean };

const ortRuntime: OrtRuntime = {
  proxy: (import.meta.env.VITE_ORT_WASM_PROXY as string | undefined) === '1',
};

/** Test/benchmark hook. Returns the previous setting. */
export function configureOrtRuntime(next: Partial<OrtRuntime>): OrtRuntime {
  const previous = { ...ortRuntime };
  Object.assign(ortRuntime, next);
  return previous;
}

/** True when this environment can host the ORT proxy worker (browser only). */
function proxyAvailable(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof document !== 'undefined' &&
    typeof Worker !== 'undefined'
  );
}

/** Absolute URLs so both the page and the proxy worker can fetch the loader. */
function absoluteWasmPaths(): { mjs: string; wasm: string } {
  const base = typeof document !== 'undefined' ? document.baseURI : 'http://localhost/';
  return {
    mjs: new URL(wasmMjsUrl, base).href,
    wasm: new URL('/onnxruntime/ort-wasm-simd-threaded.wasm', base).href,
  };
}

export class SpoterInferenceSession {
  private session: ort.InferenceSession | null = null;
  private provider: string = 'wasm';
  /** URL of the loaded graph, used in diagnostics and contract errors. */
  public modelUrl = '';

  private constructor() {}

  static async create(modelUrl: string): Promise<SpoterInferenceSession> {
    const instance = new SpoterInferenceSession();
    instance.modelUrl = modelUrl;

    const sessionOptions: ort.InferenceSession.SessionOptions = {
      executionProviders: ['wasm']
    };

    const modelName = modelUrl.substring(modelUrl.lastIndexOf('/') + 1);
    sessionOptions.externalData = [
      {
        path: `${modelName}.data`,
        data: `${modelUrl}.data`
      }
    ];

    try {
      // Browser: serve the MJS loader from the Vite source module and the binary
      // from the public payload. Under Node (unit tests) the `?url` import is not
      // a fetchable HTTP path, so leave ORT's own resolution in place.
      const inBrowser = proxyAvailable();
      const useProxy = inBrowser && ortRuntime.proxy;

      if (inBrowser) {
        ort.env.wasm.wasmPaths = absoluteWasmPaths();
      }

      const createSession = async (proxy: boolean) => {
        if (inBrowser) ort.env.wasm.proxy = proxy;
        return ort.InferenceSession.create(modelUrl, sessionOptions);
      };

      let usedProxy = useProxy;
      try {
        instance.session = await createSession(useProxy);
      } catch (proxyError) {
        if (!useProxy) throw proxyError;
        // Best-effort recovery only. ORT's WASM init is one-shot, so once a proxy
        // initialisation has failed the in-page retry usually fails too; the
        // second error below is the real diagnosis in that case.
        console.warn(
          '[ONNX] Proxy worker unavailable, retrying on the main thread. If this also fails, ' +
            'unset VITE_ORT_WASM_PROXY: the worker cannot boot in this build.',
          proxyError,
        );
        usedProxy = false;
        instance.session = await createSession(false);
      }

      instance.provider = usedProxy ? 'wasm (worker)' : 'wasm';
      console.log(`[ONNX] Session Initialized via ${instance.provider} for ${modelUrl}.`);
    } catch (e) {
      console.warn("[ONNX] WASM Initialization Failed:", e);
      throw new Error(`Failed to initialize ONNX Runtime for ${modelUrl}: \nWASM err: ${e}`);
    }

    return instance;
  }

  async predict(buffer: Float32Array, vocabMap: Record<number, string> = ASL_VOCAB): Promise<InferenceResult> {
    if (!this.session) throw new Error("Session is not initialized");
    if (buffer.length !== 60 * FEATURE_DIMENSION) throw new Error("Buffer must be exactly 60 * 366 floats");

    const tensor = new ort.Tensor('float32', buffer, [1, 60, FEATURE_DIMENSION]);
    
    const startTime = performance.now();
    const feeds: Record<string, ort.Tensor> = {};
    feeds[this.session.inputNames[0]] = tensor;
    
    const results = await this.session.run(feeds);
    const outputTensor = results[this.session.outputNames[0]];
    const logits = outputTensor.data as Float32Array;

    // Refuse to label a prediction whose shape disagrees with the active class
    // map. This is the guard that prevents a 3-class map being applied to the
    // 79-class model (or the reverse): such a pairing throws instead of
    // producing plausible-looking but meaningless signs.
    assertModelOutputSize(vocabMap, logits.length, this.modelUrl);

    const latencyMs = performance.now() - startTime;

    // Softmax
    const maxLogit = Math.max(...Array.from(logits));
    const exps = logits.map((x) => Math.exp(x - maxLogit));
    const sumExps = exps.reduce((a, b) => a + b, 0);
    const probs = exps.map((x) => x / sumExps);
    
    const topK = Array.from(probs)
      .map((confidence, index) => ({ classIndex: index, className: vocabMap[index] || "UNKNOWN", confidence }))
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 3);

    return { logits, topK, latencyMs, provider: this.provider };
  }

  /**
   * One-time model warm-up with dummy tensor input to compile WASM kernels and allocate memory.
   * Discards all dummy results so they are never presented as genuine predictions.
   */
  async warmup(): Promise<number> {
    if (!this.session) return 0;
    const dummyBuffer = new Float32Array(60 * FEATURE_DIMENSION);
    const tensor = new ort.Tensor('float32', dummyBuffer, [1, 60, FEATURE_DIMENSION]);
    const feeds: Record<string, ort.Tensor> = {};
    feeds[this.session.inputNames[0]] = tensor;

    const t0 = performance.now();
    await this.session.run(feeds);
    const warmupMs = performance.now() - t0;
    console.log(`[ONNX] Model kernels warmed up in ${warmupMs.toFixed(1)}ms (dummy output discarded)`);
    return warmupMs;
  }
}
