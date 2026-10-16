import fs from 'fs';
import * as ort from 'onnxruntime-node'; 
import { ASL_VOCAB } from '../lib/vocab';
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

    const session = await ort.InferenceSession.create(modelPath);
    console.log("Model loaded successfully.");

    // Section 1: Deep Dive into 0022932153577568393-HELLO trace
    const npyPath = `${datasetDir}/0022932153577568393-HELLO_features.npy`;
    const features = loadNpy(npyPath);
    const T = features.length / FEATURE_DIMENSION;
    
    // Test mid-sequence block where signal should be strong
    const start = Math.floor(T / 2) - 30; // 60 frame window center
    const flatBuffer = new Float32Array(60 * FEATURE_DIMENSION);
    for (let w = 0; w < 60; w++) {
        const frameIdx = Math.max(0, Math.min(start + w, T - 1));
        const frameOffset = frameIdx * FEATURE_DIMENSION;
        flatBuffer.set(features.subarray(frameOffset, frameOffset + FEATURE_DIMENSION), w * FEATURE_DIMENSION);
    }
    
    const tensor = new ort.Tensor('float32', flatBuffer, [1, 60, FEATURE_DIMENSION]);
    const feeds: any = {}; feeds[session.inputNames[0]] = tensor;
    let results = await session.run(feeds);
    let logits = results[session.outputNames[0]].data as Float32Array;
    let maxLogit = Math.max(...Array.from(logits));
    let exps = logits.map(x => Math.exp(x - maxLogit));
    let sumExps = exps.reduce((a, b) => a + b, 0);
    let probs = exps.map(x => x / sumExps);
    
    let topK = Array.from(probs)
      .map((confidence, index) => ({ index, className: ASL_VOCAB[index] || "UNKNOWN", confidence }))
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 5);
      
    console.log(`\\n--- TRACE DEEP DIVE: 0022932153577568393-HELLO ---`);
    console.log(`Top 5 Labels (Center frames):`);
    topK.forEach((k, i) => console.log(`  ${i+1}: Class ${k.index} (${k.className}) - ${(k.confidence*100).toFixed(2)}%`));


    // Section 2: Validation Split Evaluation for HELLO, YES, NO
    const manifestPath = `${root}/ai/sign-recognition/data/asl100_training_manifest.csv`;
    const manifest = fs.readFileSync(manifestPath, 'utf8').split('\n');
    const valSamples = manifest.filter(line => line.includes(',val'));

    const targets = ['HELLO', 'YES', 'NO'];
    let valMetrics: Record<string, { total: number, correct: number, matrix: Record<string, number> }> = {};
    
    for (const t of targets) {
        valMetrics[t] = { total: 0, correct: 0, matrix: {} };
        const matches = valSamples.filter(l => l.includes(`,${t},`));
        
        for (const line of matches) {
            const parts = line.split(',');
            const fileKey = parts[3]?.replace('.mp4', '');
            if (!fileKey) continue;
            
            let fPath = `${datasetDir}/${fileKey}_features.npy`;
            if (!fs.existsSync(fPath)) fPath = `${root}/ai/sign-recognition/data/processed_pilot/${fileKey}_features.npy`;
            if (!fs.existsSync(fPath)) continue;

            const npy = loadNpy(fPath);
            const frames = npy.length / FEATURE_DIMENSION;
            
            // Just scan all overlapping chunks and find the peak recognized sign
            let blockLogits = new Float32Array(79).fill(0);
            
            const tensorBuffer = new Float32Array(60 * FEATURE_DIMENSION);
            let frameStart = Math.max(0, Math.floor(frames / 2) - 30);
            for (let w = 0; w < 60; w++) {
                const idx = Math.max(0, Math.min(frameStart + w, frames - 1));
                tensorBuffer.set(npy.subarray(idx * FEATURE_DIMENSION, (idx + 1) * FEATURE_DIMENSION), w * FEATURE_DIMENSION);
            }
            const tnsr = new ort.Tensor('float32', tensorBuffer, [1, 60, FEATURE_DIMENSION]);
            const fds: any = {}; fds[session.inputNames[0]] = tnsr;
            const res = await session.run(fds);
            const outs = res[session.outputNames[0]].data as Float32Array;
            
            const mLogit = Math.max(...Array.from(outs));
            const xp = outs.map(x => Math.exp(x - mLogit));
            const sumXp = xp.reduce((a, b) => a + b, 0);
            const p = xp.map(x => x / sumXp);
            
            let top = Array.from(p).map((c, i) => ({ className: ASL_VOCAB[i] || 'UNKNOWN', c })).sort((a,b) => b.c - a.c)[0];
            
            valMetrics[t].total++;
            valMetrics[t].matrix[top.className] = (valMetrics[t].matrix[top.className] || 0) + 1;
            if (top.className === t) valMetrics[t].correct++;
        }
    }

    console.log(`\\n--- COMPETITION SIGNS VALIDATION METRICS ---`);
    for (const [sign, m] of Object.entries(valMetrics)) {
        console.log(`Sign: ${sign}`);
        console.log(`  Count : ${m.total}`);
        if(m.total > 0){
           console.log(`  Top-1 Acc  : ${((m.correct / m.total)*100).toFixed(1)}%`);
           console.log(`  Confusion Matrix: `, m.matrix);
        }
    }

}
run().catch(console.error);
