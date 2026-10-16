import type { ASLRepresentation } from './textToASL';

export type RecognitionState = 'idle' | 'listening' | 'unsupported' | 'error';

export interface SpokenTextItem {
    id: string;
    text: string;
    timestamp: number;
    asl?: ASLRepresentation;
}

export interface SpeechRecognitionHooks {
    onStateChange?: (state: RecognitionState, errorMessage?: string) => void;
    onInterimResult?: (text: string) => void;
    onFinalResult?: (text: string) => void;
}

export function isSpeechRecognitionSupported(): boolean {
    return typeof window !== 'undefined' && (!!(window as any).SpeechRecognition || !!(window as any).webkitSpeechRecognition);
}

/**
 * Isolated browser UI abstraction encapsulating native asynchronous Audio interactions independently from ML/React loops.
 */
export class SpeechRecognitionService {
    private recognition: any = null;
    private hooks: SpeechRecognitionHooks = {};
    private isDeliberateStop: boolean = true;
    private sessionGeneration: number = 0;
    private lastCommittedResultIndex: number = -1;

    public setHooks(hooks: SpeechRecognitionHooks) {
        this.hooks = hooks;
    }

    public start() {
        if (!isSpeechRecognitionSupported()) {
            this.hooks.onStateChange?.('unsupported');
            return;
        }

        this.stop(); // Safe teardown boundary 
        this.isDeliberateStop = false;
        this.lastCommittedResultIndex = -1;
        const currentGeneration = ++this.sessionGeneration;
        
        const JSBrowserSR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        this.recognition = new JSBrowserSR();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onstart = () => {
            if (currentGeneration === this.sessionGeneration) this.hooks.onStateChange?.('listening');
        };

        this.recognition.onerror = (e: any) => {
            if (currentGeneration !== this.sessionGeneration) return;
            this.hooks.onStateChange?.('error', e.error);
            if (e.error === 'not-allowed' || e.error === 'service-not-allowed' || e.error === 'audio-capture') {
                this.isDeliberateStop = true; // Permanently fail to avoid restart loop
            }
        };

        this.recognition.onend = () => {
            if (currentGeneration !== this.sessionGeneration) return;
            if (!this.isDeliberateStop) {
                // Restart continuously for silent timeout drop protections natively
                // Uses timeout to naturally break recursion stacks bounds
                setTimeout(() => {
                    if (!this.isDeliberateStop && currentGeneration === this.sessionGeneration) {
                        try { this.recognition.start(); } catch(e){}
                    }
                }, 100);
            } else {
                this.hooks.onStateChange?.('idle');
            }
        };

        this.recognition.onresult = (e: any) => {
            if (currentGeneration !== this.sessionGeneration) return;
            
            let interimText = '';
            for (let i = e.resultIndex; i < e.results.length; ++i) {
                const result = e.results[i];
                if (result.isFinal) {
                    if (i > this.lastCommittedResultIndex) {
                        this.lastCommittedResultIndex = i;
                        this.hooks.onFinalResult?.(result[0].transcript.trim());
                    }
                } else {
                    interimText += result[0].transcript;
                }
            }

            if (interimText.length > 0) {
                this.hooks.onInterimResult?.(interimText.trim());
            } else {
                this.hooks.onInterimResult?.('');
            }
        };

        try { 
            this.recognition.start(); 
        } catch (e) { 
            /* already active safely */ 
        }
    }

    public stop() {
        this.isDeliberateStop = true;
        if (this.recognition) {
            try { this.recognition.stop(); } catch(e) {}
            this.recognition = null;
        }
        this.hooks.onStateChange?.('idle');
    }
}
