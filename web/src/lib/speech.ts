/**
 * Dedicated Browser SpeechSynthesis service for SignVox.
 * Exposes a safe, crash-free interface wrapping Web Speech API without rendering side-effects.
 */

// We evaluate presence at runtime for safety in diverse environments
export function isSpeechSupported(): boolean {
    return typeof window !== 'undefined' && typeof window.speechSynthesis !== 'undefined';
}

/**
 * Safely stops any currently active or queued utterances.
 */
export function stopSpeaking(): void {
    if (!isSpeechSupported()) return;
    window.speechSynthesis.cancel();
}

/**
 * Cancels current speech and speaks the text string asynchronously.
 * Avoids uncontrolled queues building up during rapid transcription.
 */
export function speakText(text: string): void {
    // 1. Fallback protection
    if (!isSpeechSupported()) return;
    
    // 2. Ignore empty input
    const cleanText = (text || '').trim();
    if (cleanText.length === 0) return;

    try {
        // 3. Queue cancellation (responsive behavior requested by product)
        window.speechSynthesis.cancel();

        // 4. Invocation
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = "en-US";
        // NOTE: We leave voice to standard browser defaults. No deep inspection required.

        // Dispatch natively
        window.speechSynthesis.speak(utterance);
    } catch (e) {
        // 5. Hard isolation against crashing application loop
        console.warn('SpeechSynthesis API failed:', e);
    }
}
