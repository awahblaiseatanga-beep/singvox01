import { describe, it, expect } from 'vitest';
import { TemporalStabilizer, PILOT_STABILIZER_CONFIG, BASELINE_STABILIZER_CONFIG } from '../lib/temporalStabilizer';

describe('Model-Specific Temporal Commit Boundaries', () => {

  it('Pilot config safely mounts with 0.65 boundary and evaluates correctly', () => {
        const stab = new TemporalStabilizer(PILOT_STABILIZER_CONFIG);
        let state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.50, timestampMs: 100 });
        expect(state.status).toBe('Uncertain');

        state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.50, timestampMs: 200 });
        state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.50, timestampMs: 600 });
        
        expect(state.status).toBe('Stable');
        expect(state.committedSign).toBeNull(); // moving average ~0.50 < 0.65

        // Inject strong uniform evidence to breach 0.65 threshold
        let committed = false;
        const check = (s: any) => { if (s.committedSign === 'HELLO') committed = true; };
        check(stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.95, timestampMs: 1000 }));
        check(stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.95, timestampMs: 1400 }));
        check(stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.95, timestampMs: 1800 }));
        
        expect(committed).toBe(true);
    });

    it('Baseline config safely mounts with 0.25 boundary and successfully commits low probabilities', () => {
        const stab = new TemporalStabilizer(BASELINE_STABILIZER_CONFIG);
        let state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.35, timestampMs: 100 });
        state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.35, timestampMs: 200 });
        state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.35, timestampMs: 600 });
        
        expect(state.status).toBe('Stable'); // Threshold is 0.15 for Stable
        expect(state.committedSign).toBe('HELLO'); // Threshold is 0.25 for Commit, 0.35 breached it!
    });

    it('App Model-Switch natively isolates and wipes state', () => {
        let activeRef = new TemporalStabilizer(PILOT_STABILIZER_CONFIG);
        
        activeRef.process({ classIndex: 0, className: 'HELLO', confidence: 0.95, timestampMs: 100 });
        activeRef.process({ classIndex: 0, className: 'HELLO', confidence: 0.95, timestampMs: 400 });
        let state = activeRef.process({ classIndex: 0, className: 'HELLO', confidence: 0.95, timestampMs: 600 });
        expect(state.committedSign).toBe('HELLO');

        // Emulate App.tsx Start
        activeRef = new TemporalStabilizer(BASELINE_STABILIZER_CONFIG);
        
        const resetState = activeRef.process({ classIndex: 1, className: 'YES', confidence: 0.40, timestampMs: 700 });
        expect(resetState.status).toBe('Uncertain'); 
        expect(resetState.committedSign).toBeNull();
        
        activeRef.process({ classIndex: 1, className: 'YES', confidence: 0.40, timestampMs: 800 });
        const finalState = activeRef.process({ classIndex: 1, className: 'YES', confidence: 0.40, timestampMs: 1200 });
        
    });

    it('Baseline config resists fluctuating prediction commits (verifying 0.15 justification and 400ms guard rails)', () => {
        const stab = new TemporalStabilizer(BASELINE_STABILIZER_CONFIG);
        // Minimum stable duration is 400ms.
        
        // Spike 1 (100ms) False prediction
        let state = stab.process({ classIndex: 2, className: 'NO', confidence: 0.8, timestampMs: 100 });
        expect(state.status).toBe('Uncertain');
        
        // Drops below threshold / completely empty frames for 200ms
        state = stab.process({ classIndex: 0, className: 'HELLO', confidence: 0.1, timestampMs: 300 });
        expect(state.status).toBe('Uncertain');
        
        // Spike 2 (another isolated frame)
        state = stab.process({ classIndex: 2, className: 'NO', confidence: 0.8, timestampMs: 400 });
        expect(state.status).toBe('Uncertain'); // NEVER reaches 400ms stability duration 
        expect(state.committedSign).toBeNull();
    });
});
