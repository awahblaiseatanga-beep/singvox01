import fs from 'fs';
import * as ort from 'onnxruntime-node'; // Using native Node backend so it won't crash
import { ASL_VOCAB } from '../lib/vocab';
import { TemporalStabilizer, BASELINE_STABILIZER_CONFIG } from '../lib/temporalStabilizer';
import { FEATURE_DIMENSION } from '../lib/contracts';

function loadNpy(filePath: string): Float32Array {
    const buffer = fs.readFileSync(filePath);
    const headerLen = buffer.readUInt16LE(8);
    const offset = 10 + headerLen;
    const dataBuf = buffer.subarray(offset);
    return new Float32Array(dataBuf.buffer, dataBuf.byteOffset, dataBuf.byteLength / 4);
}

async function run() {
    const root = process.cwd().replace(/\\/g, '/').split('/web')[0];
    const datasetDir = `${root}/ai/sign-recognition/data/dataset_extracted`;
    const modelPath = `${root}/web/public/spoter_v2_model.onnx`;

    console.log("Loading ONNX model...");
    const session = await ort.InferenceSession.create(modelPath);

    // Pick a HELLO trace
    const npyPath = `${datasetDir}/0022932153577568393-HELLO_features.npy`;
    if (!fs.existsSync(npyPath)) {
        console.error("NPY file not found");
        return;
    }

    const features = loadNpy(npyPath);
    const T = features.length / FEATURE_DIMENSION;
    console.log(`Trace loaded: ${T} frames`);

    const stab = new TemporalStabilizer({ ...BASELINE_STABILIZER_CONFIG, minimumConfidence: 0.05 });

    for (let i = 0; i < Math.max(80, T); i++) {
        const end = i + 1;
        const start = Math.max(0, end - 60);
        const winCount = end - start;
        
        const flatBuffer = new Float32Array(60 * FEATURE_DIMENSION);
        for (let w = 0; w < 60; w++) {
            const frameIdx = w < (60 - winCount) ? start : start + (w - (60 - winCount));
            const frameOffset = Math.min(frameIdx, T - 1) * FEATURE_DIMENSION;
            flatBuffer.set(features.subarray(frameOffset, frameOffset + FEATURE_DIMENSION), w * FEATURE_DIMENSION);
        }
        
        const tensor = new ort.Tensor('float32', flatBuffer, [1, 60, FEATURE_DIMENSION]);
        const feeds: Record<string, ort.Tensor> = {};
        feeds[session.inputNames[0]] = tensor;
        
        const results = await session.run(feeds);
        const logits = results[session.outputNames[0]].data as Float32Array;

        const maxLogit = Math.max(...Array.from(logits));
        const exps = logits.map((x) => Math.exp(x - maxLogit));
        const sumExps = exps.reduce((a, b) => a + b, 0);
        const probs = exps.map((x) => x / sumExps);
        
        const topK = Array.from(probs)
          .map((confidence, index) => ({ classIndex: index, className: ASL_VOCAB[index] || "UNKNOWN", confidence }))
          .sort((a, b) => b.confidence - a.confidence)
          .slice(0, 3);
          
        const top = topK[0];
        const state = stab.process({
            classIndex: top.classIndex,
            className: top.className,
            confidence: top.confidence,
            timestampMs: i * 125
        });

        console.log(`[Frame ${i}] Top: ${top.className} (${(top.confidence*100).toFixed(1)}%) | Runner: ${topK[1].className} (${(topK[1].confidence*100).toFixed(1)}%) | Status: ${state.status} | Evid: ${(state.stabilityEvidence*100).toFixed(1)}% | Comm: ${state.committedSign}`);
    }
}

run().catch(console.error);
