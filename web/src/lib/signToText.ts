import { ASL_VOCAB } from './vocab';

export type TranscriptItem = {
    id: string;
    signId: string;
    displayText: string;
    /** Monotonic pipeline timestamp (requestAnimationFrame time). */
    timestamp: number;
    /** Wall-clock time the sign was committed, for display in the UI. */
    at?: number;
    /**
     * Whether the loaded avatar GLB has a clip for this sign.
     * Recognition is independent of animation: a recognised sign with no clip
     * is shown as text and never replaced by an unrelated animation.
     */
    avatarClipAvailable?: boolean;
};

/**
 * Safely maps a canonical sign identity to display text.
 * Requires the existing ASL_VOCAB as the source of truth to prevent isolated mapping errors.
 */
export function mapSignToText(canonicalName: string): string {
    const knownKeys = Object.values(ASL_VOCAB);
    
    // Safely handle unknown signs gracefully.
    if (!knownKeys.includes(canonicalName)) {
        return `[Unknown: ${canonicalName}]`;
    }

    // Since our existing vocab is uniformly capitalized, we can return it directly,
    // or apply casing formats here later if requested by Design.
    return canonicalName;
}
