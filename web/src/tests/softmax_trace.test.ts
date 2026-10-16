import { describe, it, expect } from 'vitest';
import { TemporalStabilizer } from '../lib/temporalStabilizer';

describe('Softmax Probability Calibration Trace', () => {
    it('Traces the spread of probability mass for Pilot (3 classes) vs Baseline (79 classes) under identical logit strength', () => {
        // Assume the target class gets a logit of 5.0, and the others get 1.0.
        const mockLogitsPilot = new Float32Array([5.0, 1.0, 1.0]);
        const mockLogitsBaseline = new Float32Array(79);
        mockLogitsBaseline.fill(1.0);
        mockLogitsBaseline[9] = 5.0; // Index 9 is ASL_YES

        const simulateSoftmax = (logits: Float32Array) => {
            const maxLogit = Math.max(...Array.from(logits));
            const exps = logits.map((x) => Math.exp(x - maxLogit));
            const sumExps = exps.reduce((a, b) => a + b, 0);
            return exps.map((x) => x / sumExps);
        };

        const probsPilot = simulateSoftmax(mockLogitsPilot);
        const probsBaseline = simulateSoftmax(mockLogitsBaseline);

        console.log(`Pilot Top Confidence (3 classes): ${(probsPilot[0] * 100).toFixed(2)}%`);
        console.log(`Baseline Top Confidence (79 classes): ${(probsBaseline[9] * 100).toFixed(2)}%`);

        // Pilot easily surpasses 0.65
        expect(probsPilot[0]).toBeGreaterThan(0.65);
        
        // Baseline fails to surpass 0.65, but DOES surpass 0.40 (minimumStableEvidence)
        expect(probsBaseline[9]).toBeLessThan(0.65);
        expect(probsBaseline[9]).toBeGreaterThan(0.40);
        
        // Simulate Stabilizer Process
        const stabilizer = new TemporalStabilizer();
        const pilotState = stabilizer.process({ classIndex: 0, className: "HELLO", confidence: probsPilot[0], timestampMs: 0 });
        
        // Push 10 frames of Baseline to show it becomes stable but never commits
        const baselineStab = new TemporalStabilizer();
        let baselineState;
        for(let i=0; i<10; i++) {
            baselineState = baselineStab.process({ classIndex: 9, className: "YES", confidence: probsBaseline[9], timestampMs: i*130 });
        }
        
        console.log(`Baseline state after 10 identical 'YES' frames: Status=${baselineState?.status}, CurrentStable=${baselineState?.currentStableName}, Committed=${baselineState?.committedSign}`);
        expect(baselineState?.status).toBe('Stable');
        expect(baselineState?.committedSign).toBeNull();
    });
});
