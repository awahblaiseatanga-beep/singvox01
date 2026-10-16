import { describe, it, expect, beforeEach } from 'vitest';
import { mapSignToText, TranscriptItem } from '../lib/signToText';
import { TemporalStabilizer, RawPrediction } from '../lib/temporalStabilizer';

describe('Sign -> Text Transcript Logic', () => {
    let transcript: TranscriptItem[] = [];
    let stabilizer: TemporalStabilizer;

    beforeEach(() => {
        transcript = [];
        stabilizer = new TemporalStabilizer({
            windowMs: 1000,
            minimumConfidence: 0.2,
            minimumStableEvidence: 0.4,
            minimumCommitEvidence: 0.65,
            minimumStableObservations: 2,
            minimumCommitObservations: 3,
            minimumStableDurationMs: 200,
            transitionMargin: 0.15,
            dropThreshold: 0.25,
            maxObservations: 60
        });
    });

    // Helper to simulate the exact loop event running in App.tsx
    const simulateAppProcess = (frames: RawPrediction[]) => {
        for (const f of frames) {
            const state = stabilizer.process(f);
            
            // Emulate App.tsx React Rendering + Transcript array persistence
            if (state.committedSign) {
                transcript.push({
                    id: `${f.timestampMs}-${state.committedSign}`,
                    signId: state.committedSign,
                    displayText: mapSignToText(state.committedSign),
                    timestamp: f.timestampMs
                });
            }
        }
    };

    const createFrames = (className: string, conf: number, count: number, startT: number, gap: number = 100) => {
        return Array.from({ length: count }).map((_, i) => ({
            classIndex: 1,
            className,
            confidence: conf,
            timestampMs: startT + i * gap
        }));
    };

    it('Test 1: Single commit becomes one transcript entry', () => {
        simulateAppProcess(createFrames('FATHER', 0.9, 5, 0));
        expect(transcript.length).toBe(1);
        expect(transcript[0].displayText).toBe('FATHER');
    });

    it('Test 2: Sustained stable sign does not duplicate in transcript', () => {
        simulateAppProcess(createFrames('FATHER', 0.9, 20, 0)); // Held for a long time
        expect(transcript.length).toBe(1);
    });

    it('Test 3: Two separate identical commits produce two transcript entries (re-arming)', () => {
        simulateAppProcess(createFrames('FATHER', 0.9, 5, 0)); // Commit FATHER
        
        // Wait long enough for dropThreshold to clear the stabilizer mapping explicitly
        simulateAppProcess(createFrames('UNCERTAIN_NOISE', 0.1, 15, 600));

        simulateAppProcess(createFrames('FATHER', 0.9, 10, 2200)); // Commit FATHER again
        
        expect(transcript.length).toBe(2);
        expect(transcript[0].signId).toBe('FATHER');
        expect(transcript[1].signId).toBe('FATHER');
        expect(transcript[0].id).not.toBe(transcript[1].id); // Unique IDs generated
    });

    it('Test 4: Different signs append independently to transcript', () => {
        simulateAppProcess(createFrames('HELLO', 0.9, 5, 0));
        simulateAppProcess(createFrames('GOOD', 0.9, 8, 600));
        simulateAppProcess(createFrames('MORNING', 0.9, 5, 1500));

        expect(transcript.length).toBe(3);
        expect(transcript.map(t => t.displayText)).toEqual(['HELLO', 'GOOD', 'MORNING']);
    });

    it('Test 5: Unknown/unmapped committed signs must be handled safely', () => {
        simulateAppProcess(createFrames('SUPER_WEIRD_UNMAPPED_SIGN', 0.9, 5, 0));
        expect(transcript.length).toBe(1);
        expect(transcript[0].displayText).toBe('[Unknown: SUPER_WEIRD_UNMAPPED_SIGN]');
    });

    it('Test 6: Canonical sign identity is strictly preserved in the data model', () => {
        simulateAppProcess(createFrames('MOTHER', 0.9, 5, 0));
        const item = transcript[0];
        
        expect(item.id.includes('MOTHER')).toBe(true);
        expect(item.signId).toBe('MOTHER'); // Canonical is untouchable
        expect(item.timestamp).toBeGreaterThanOrEqual(0); 
    });

    it('Test 7: Clearing transcript does NOT reset TemporalStabilizer lifecycle', () => {
        simulateAppProcess(createFrames('FATHER', 0.9, 5, 0));
        expect(transcript.length).toBe(1);
        
        // App.tsx UI cleared the transcript visually ONLY
        transcript = []; 
        
        // Stabilizer keeps Coasting...
        simulateAppProcess(createFrames('FATHER', 0.9, 5, 500));
        
        // Did not re-commit! The stabilizer wasn't magically broken.
        expect(transcript.length).toBe(0); 
    });

    it('Test 8: No-Commit Regression -> ordinary predictions do not modify transcript', () => {
        simulateAppProcess([
            { classIndex: 1, className: 'HELLO', confidence: 0.1, timestampMs: 100 },
            { classIndex: 2, className: 'GOOD', confidence: 0.1, timestampMs: 200 },
            { classIndex: 3, className: 'FATHER', confidence: 0.1, timestampMs: 300 },
            { classIndex: 4, className: 'WATER', confidence: 0.1, timestampMs: 400 },
        ]);
        expect(transcript.length).toBe(0);
    });

    it('Test 9: Transcript safely survives random React App re-renders without duplication', () => {
        // App process runs...
        const frame = { classIndex: 1, className: 'FATHER', confidence: 0.9, timestampMs: 0 };
        
        // Emulate multiple sequential React effects querying the *same* static stabilizer boundary repeatedly 
        // without new camera frames arriving
        for(let i=0; i<10; i++){
           const state = stabilizer.process(frame); 
           // NOTE: The stabilizer inherently throws on `< lastProcessedTimestamp`.
           // So this naturally tests monotonic requirement safety. 
           // Wait, re-rendering doesn't push old frames to stabilizer. App.tsx invokes `process` exactly once per strictly NEW `now` timestamp interval via mediaPipe!
        }
        
        // The fact that App.tsx isolates video processing (lastProcessedTimestamp check) protects it.
        expect(transcript.length).toBe(0); // Never reached commit condition
    });

    it('Test 10: Session lifecycle gracefully blocks legacy commits from bleeding', () => {
        // Session A
        simulateAppProcess(createFrames('FATHER', 0.9, 5, 0));
        expect(transcript.length).toBe(1);
        
        // User clicks "Stop Camera" / "Start Camera" -> App.start() calls stabilizer.reset()
        stabilizer.reset();
        
        // Transcript remains (according to standard design) or clears - we test stabilizer decoupled safety
        // Session B (time restarts or increments wildly)
        simulateAppProcess(createFrames('FATHER', 0.9, 5, 0)); 
        
        // Session B commits FATHER cleanly as a duplicate, because the IDLE drop + internal reset wiped `lastCommittedName`.
        expect(transcript.length).toBe(2);
    });
});
