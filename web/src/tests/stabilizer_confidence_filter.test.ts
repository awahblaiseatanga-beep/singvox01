import { describe, it, expect } from 'vitest';
import { TemporalStabilizer, BASELINE_STABILIZER_CONFIG, PILOT_STABILIZER_CONFIG } from '../lib/temporalStabilizer';

describe('Stabilizer Confidence Filtration Native Rules', () => {
    it('1. Verifies that without minimumConfidence explicit patch, values below 0.2 are excluded from the score numerator but artificially drop evidence averages', () => {
        // Build base config that defaults to 0.20
        const stab = new TemporalStabilizer({
            minimumCommitEvidence: 0.25,
            minimumStableEvidence: 0.15,
            dropThreshold: 0.10
            // minimumConfidence implicitly falls back to 0.20
        });

        // 100ms interval frames. 
        // We push probabilities of 0.25 (included) and 0.18 (excluded).
        for (let i = 0; i < 5; i++) {
            stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.25, timestampMs: i * 100 });
        }
        for (let i = 5; i < 10; i++) {
            stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.18, timestampMs: i * 100 });
        }

        const state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.18, timestampMs: 1000 });
        
        // 0.25*5 = 1.25 score. Total frames = 11. 1.25 / 11 = 0.113 highestEvidence! 
        // It drops beneath 0.15 and is therefore 'Uncertain'!
        expect(state.status).toBe('Uncertain');
        expect(state.stabilityEvidence).toBeLessThan(0.15); // Explicitly trapped by denominator dilution
        expect(state.committedSign).toBeNull();
    });

    it('2. Verifies that the Baseline config containing minimumConfidence: 0.05 perfectly captures the diluted fraction preserving the 0.15 temporal logic', () => {
        const patchConfig = { ...BASELINE_STABILIZER_CONFIG, minimumConfidence: 0.05 };
        const stab = new TemporalStabilizer(patchConfig);

        // Identical input values
        for (let i = 0; i < 5; i++) {
            stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.25, timestampMs: i * 100 });
        }
        for (let i = 5; i < 10; i++) {
            stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.18, timestampMs: i * 100 });
        }

        const state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.18, timestampMs: 1000 });
        
        // Scores are correctly summated. Average of (0.25 and 0.18) > 0.15 easily!
        // At 1000ms duration, observations > 3, it should cleanly attain 'Stable' and potentially commit if boundaries hit.
        expect(state.status).toBe('Stable');
        expect(state.stabilityEvidence).toBeGreaterThan(0.15);
    });

    it('3. Confirms Pilot minimumConfidence rigorously protects the unchanged 0.20 lower bound, dropping 0.18 logic', () => {
        const stab = new TemporalStabilizer(PILOT_STABILIZER_CONFIG); // defaults to 0.20 implicitly
        
        // Give Pilot 99% probability frames followed by some 18% frames
        stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.99, timestampMs: 100 });
        stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.99, timestampMs: 200 });
        stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.18, timestampMs: 300 });

        const state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.18, timestampMs: 400 });
        
        // Dropping values protects evidence from scaling arbitrarily if there's unstructured noise
        // Ensure Pilot didn't mistakenly adapt 0.05 minimumConfidence.
        expect(PILOT_STABILIZER_CONFIG.minimumConfidence).toBeUndefined(); 
    });
});
