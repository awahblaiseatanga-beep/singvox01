import { describe, it, expect } from 'vitest';
import fs from 'fs';
import { SpoterInferenceSession } from '../lib/inference';
import { applyV2Normalization } from '../lib/normalize';
import { PILOT_VOCAB, ASL_VOCAB } from '../lib/vocab';
import { TemporalStabilizer } from '../lib/temporalStabilizer';

// This trace needs the local-only manifest, the extracted .npy clips and both
// full ONNX graphs (all gitignored). Skip — never silently pass, never fail —
// when a clean clone does not carry them: the recorded-sample commitment
// metrics it prints cannot be produced from synthetic fixtures, and inventing
// them would fabricate accuracy evidence. The inference plumbing itself is
// covered on every clone by syntheticFixtures.test.ts.
const ROOT = process.cwd().replace(/\\/g, '/').split('/web')[0];
const MANIFEST = `${ROOT}/ai/sign-recognition/data/asl100_training_manifest.csv`;
const DATASET_DIR = `${ROOT}/ai/sign-recognition/data/dataset_extracted`;
const PILOT_DIR = `${ROOT}/ai/sign-recognition/data/processed_pilot`;
const GRAPH_V2 = `${ROOT}/web/public/spoter_v2_model.onnx`;
const GRAPH_PILOT = `${ROOT}/web/public/spoter_pilot.onnx`;
const HAVE_FIXTURES =
    fs.existsSync(MANIFEST) &&
    fs.existsSync(GRAPH_V2) &&
    fs.existsSync(GRAPH_PILOT) &&
    (fs.existsSync(DATASET_DIR) || fs.existsSync(PILOT_DIR));

function loadNpy(filePath: string): Float32Array {
    const buffer = fs.readFileSync(filePath);
    // Rough parse: first 10 bytes: \x93NUMPY + version + header_len
    const headerLen = buffer.readUInt16LE(8);
    const offset = 10 + headerLen;
    const dataBuf = buffer.subarray(offset);
    return new Float32Array(dataBuf.buffer, dataBuf.byteOffset, dataBuf.byteLength / 4);
}

describe.skipIf(!HAVE_FIXTURES)('Baseline Threshold Validation Trace', () => {
    it('Traces specific validation samples using exact App.tsx sequence logic to evaluate commitment metrics', async () => {
        const root = ROOT;
        const manifestPath = `${root}/ai/sign-recognition/data/asl100_training_manifest.csv`;
        const datasetDir = `${root}/ai/sign-recognition/data/dataset_extracted`;
        
        const manifest = fs.readFileSync(manifestPath, 'utf8').split('\n');
        const valSamples = manifest.filter(line => line.includes(',val\r') || line.includes(',val'));
        
        const targets = ['HELLO', 'YES', 'NO'];
        const selected = targets.map(t => {
            const matches = valSamples.filter(l => l.includes(`,${t},`));
            return { class: t, file: matches[0]?.split(',')[3] };
        }).filter(s => s.file);

        if (selected.length === 0) {
            console.log("No exact split matches found in dataset_extracted. Checking processed_pilot...");
            // Use processed_pilot as a fallback validation set
            selected.push({ class: 'YES', file: '9953610281521326-YES.mp4' });
            selected.push({ class: 'HELLO', file: '0022932153577568393-HELLO.mp4' }); // train, but works for trace
        }

        // Plain filesystem paths: this trace runs under Node (it reads .npy fixtures),
        // and a file:// URI is not resolvable by the local ONNX loader.
        const sessV2 = await SpoterInferenceSession.create(`${root}/web/public/spoter_v2_model.onnx`);
        const sessPilot = await SpoterInferenceSession.create(`${root}/web/public/spoter_pilot.onnx`);
        expect(sessV2.modelUrl).toContain('spoter_v2_model.onnx');

        for (const sample of selected) {
            const base = sample.file.replace('.mp4', '');
            let npyPath = `${datasetDir}/${base}_features.npy`;
            if (!fs.existsSync(npyPath)) {
                npyPath = `${root}/ai/sign-recognition/data/processed_pilot/${base}_features.npy`;
            }
            if (!fs.existsSync(npyPath)) {
                console.log("Missing NPY for " + base);
                continue;
            }

            const features = loadNpy(npyPath);
            const T = features.length / 366;
            
            async function runTrace(sess: SpoterInferenceSession, vocab: any, minCommit: number) {
                const stab = new TemporalStabilizer({ minimumCommitEvidence: minCommit });
                const commits: string[] = [];
                let maxProb = 0;
                let maxRunner = 0;
                
                for (let i = 0; i < Math.max(80, T); i++) {
                    const end = i + 1;
                    const start = Math.max(0, end - 60);
                    const winCount = end - start;
                    
                    // Apply the V2 normalization the app applies between landmark
                    // assembly and the buffer. The stored .npy features are the
                    // extractor output BEFORE the group scalars, so skipping this
                    // step feeds the model an unscaled sequence (measured to collapse
                    // its predictions onto a few attractor classes). Shoulder
                    // re-centring is a no-op here because the .npy is already
                    // shoulder-centred.
                    const flatBuffer = new Float32Array(60 * 366);
                    for (let w = 0; w < 60; w++) {
                        const frameIdx = w < (60 - winCount) ? start : start + (w - (60 - winCount));
                        const frameOffset = Math.min(frameIdx, T - 1) * 366;
                        const frame = applyV2Normalization(new Float32Array(features.subarray(frameOffset, frameOffset + 366)));
                        flatBuffer.set(frame, w * 366);
                    }
                    
                    const result = await sess.predict(flatBuffer, vocab);
                    // predict() refuses a class map that disagrees with the logit
                    // count, so this also proves the 79-class graph returns 79 logits.
                    expect(result.logits.length).toBe(Object.keys(vocab).length);
                    const top = result.topK[0];
                    const runner = result.topK[1];
                    
                    if (top.className === sample.class && top.confidence > maxProb) {
                        maxProb = top.confidence;
                        maxRunner = runner ? runner.confidence : 0;
                    }
                    
                    const state = stab.process({
                        classIndex: top.classIndex,
                        className: top.className,
                        confidence: top.confidence,
                        timestampMs: i * 125
                    });
                    
                    if (state.committedSign && !commits.includes(state.committedSign)) {
                        commits.push(state.committedSign);
                    }
                }
                return { commits, maxProb, maxRunner };
            }
            
            console.log(`\nSample: ${sample.class} (${base})`);
            const p = await runTrace(sessPilot, PILOT_VOCAB, 0.65);
            console.log(`Pilot 0.65: Commits=[${p.commits}] TopConf=${p.maxProb.toFixed(3)} Runner=${p.maxRunner.toFixed(3)}`);
            
            const b65 = await runTrace(sessV2, ASL_VOCAB, 0.65);
            console.log(`Base 0.65 : Commits=[${b65.commits}] TopConf=${b65.maxProb.toFixed(3)} Runner=${b65.maxRunner.toFixed(3)}`);
            
            const b25 = await runTrace(sessV2, ASL_VOCAB, 0.25);
            console.log(`Base 0.25 : Commits=[${b25.commits}] TopConf=${b25.maxProb.toFixed(3)} Runner=${b25.maxRunner.toFixed(3)}`);
        }
        // This trace replays hundreds of 60x366 windows through ONNX (measured at
        // ~108 s alone on this machine), so the default 5 s timeout is not a
        // meaningful bound for it: under parallel load the timeout timer can fire
        // while the worker is awaiting inference. Only the timeout is declared;
        // every assertion in the trace is unchanged.
    }, 300_000);
});
