import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { speakText, stopSpeaking, isSpeechSupported } from '../lib/speech';

if (typeof window === 'undefined') {
    (global as any).window = {};
}

describe('Speech Service isolated bounds', () => {
    // Mocks
    let mockCancel: any;
    let mockSpeak: any;
    
    const setupMocks = (supported: boolean) => {
        if (supported) {
            mockCancel = vi.fn();
            mockSpeak = vi.fn();

            // Intercept global window APIs defensively 
            Object.defineProperty(window, 'speechSynthesis', {
                writable: true,
                configurable: true,
                value: {
                    cancel: mockCancel,
                    speak: mockSpeak,
                }
            });

            // Mock SpeechSynthesisUtterance constructor globally
            Object.defineProperty(global, 'SpeechSynthesisUtterance', {
                writable: true,
                configurable: true,
                value: vi.fn().mockImplementation((text) => ({
                    text,
                    lang: '',
                }))
            });
        } else {
            Object.defineProperty(window, 'speechSynthesis', {
                configurable: true,
                value: undefined
            });
        }
    };
    
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('1, 9: correctly detects unsupported environments and avoids crashing', () => {
        setupMocks(false);
        expect(isSpeechSupported()).toBe(false);
        // Will silently return instead of throwing
        expect(() => speakText('HELLO')).not.toThrow();
        expect(() => stopSpeaking()).not.toThrow();
    });

    it('2, 3, 4, 5, 6: successfully calls speak, sets correct language, cancels prior queues', () => {
        setupMocks(true);
        expect(isSpeechSupported()).toBe(true);
        
        speakText('  MOTHER ');
        
        expect(mockCancel).toHaveBeenCalled();
        expect(mockSpeak).toHaveBeenCalled();
        
        // Assert constructor intercepted text
        expect(global.SpeechSynthesisUtterance).toHaveBeenCalledWith('MOTHER');

        // Assert language structure
        const utteranceInstance = (global.SpeechSynthesisUtterance as any).mock.results[0].value;
        expect(utteranceInstance.lang).toBe('en-US');
    });

    it('7: stopSpeaking invokes cancel reliably', () => {
        setupMocks(true);
        stopSpeaking();
        expect(mockCancel).toHaveBeenCalled();
        expect(mockSpeak).not.toHaveBeenCalled();
    });

    it('8: does not create utterances for empty strings', () => {
        setupMocks(true);
        speakText('');
        speakText('   ');
        
        // Neither function is run dynamically
        expect(global.SpeechSynthesisUtterance).not.toHaveBeenCalled();
        expect(mockSpeak).not.toHaveBeenCalled();
    });

    it('10: errors inside utterance/speak loop passively fail without breaking DOM', () => {
        setupMocks(true);
        // Emulate arbitrary system API rejection
        mockSpeak.mockImplementation(() => { throw new Error('Driver unavailable') });
        
        expect(() => { speakText('TEACHER') }).not.toThrow();
        expect(mockSpeak).toHaveBeenCalled();
    });
});

import { TemporalStabilizer, RawPrediction } from '../lib/temporalStabilizer';
import { TranscriptItem } from '../lib/signToText';

describe('Speech App Integration Loop Rules', () => {
    let mockCancel: any;
    let mockSpeak: any;
    let stabilizer: TemporalStabilizer;
    let transcript: TranscriptItem[] = [];
    let autoSpeakState: boolean = false;

    beforeEach(() => {
        mockCancel = vi.fn();
        mockSpeak = vi.fn();
        Object.defineProperty(window, 'speechSynthesis', {
            writable: true, configurable: true,
            value: { cancel: mockCancel, speak: mockSpeak }
        });
        Object.defineProperty(global, 'SpeechSynthesisUtterance', {
            writable: true, configurable: true,
            value: vi.fn().mockImplementation((text) => ({ text, lang: '' }))
        });

        transcript = [];
        autoSpeakState = false;
        stabilizer = new TemporalStabilizer({
            windowMs: 1000, minimumConfidence: 0.2, minimumStableEvidence: 0.4,
            minimumCommitEvidence: 0.65, minimumStableObservations: 2,
            minimumCommitObservations: 3, minimumStableDurationMs: 200, 
            transitionMargin: 0.15, dropThreshold: 0.25, maxObservations: 60
        });
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    const emulateProcessLoop = (f: RawPrediction) => {
        const state = stabilizer.process(f);
        if (state.committedSign) {
            transcript.push({ id: `T${f.timestampMs}`, signId: state.committedSign, displayText: state.committedSign, timestamp: f.timestampMs });
            if (autoSpeakState) { speakText(state.committedSign); }
        }
    };

    const createFrames = (className: string, conf: number, count: number, startT: number) => {
        return Array.from({ length: count }).map((_, i) => ({
            classIndex: 1, className, confidence: conf, timestampMs: startT + i * 100
        }));
    };

    it('11, 12: Manual Speak Latest and Stop Speaking do NOT modify transcript', () => {
        transcript.push({ id: '1', signId: 'FATHER', displayText: 'FATHER', timestamp: 0 });
        const len = transcript.length;
        
        speakText(transcript[transcript.length - 1].displayText);
        expect(transcript.length).toBe(len);
        
        stopSpeaking();
        expect(transcript.length).toBe(len);
    });

    it('13, 14: Auto-speak strictly fires exactly once on single commit, sustained signs skipped', () => {
        autoSpeakState = true;
        for (const f of createFrames('FATHER', 0.9, 10, 0)) emulateProcessLoop(f);
        
        expect(transcript.length).toBe(1);
        expect(mockSpeak).toHaveBeenCalledTimes(1); 
    });

    it('15: Two distinct commits produce separate trigger outputs', () => {
        autoSpeakState = true;
        for (const f of createFrames('FATHER', 0.9, 5, 0)) emulateProcessLoop(f);
        for (const f of createFrames('LOVE', 0.9, 5, 500)) emulateProcessLoop(f);
        
        expect(transcript.length).toBe(2);
        // Uses Hysteresis to override FATHER natively! 
        expect(mockSpeak).toHaveBeenCalledTimes(2); 
    });

    it('16: Repeated identical signs after re-arm trigger sequentially', () => {
        autoSpeakState = true;
        for (const f of createFrames('FATHER', 0.9, 5, 0)) emulateProcessLoop(f); // Commit 1

        // Idle - clear out stabilize drops by pushing Low conf frames (UNCERTAIN)
        for (const f of createFrames('UNCERTAIN', 0.1, 15, 600)) emulateProcessLoop(f);

        for (const f of createFrames('FATHER', 0.9, 10, 2200)) emulateProcessLoop(f); // Commit 2
        
        expect(transcript.length).toBe(2);
        expect(mockSpeak).toHaveBeenCalledTimes(2); 
    });
});
