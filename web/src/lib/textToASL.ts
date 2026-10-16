import { ASL_VOCAB, ASL_ALIASES } from './vocab';

export interface ASLToken {
  canonicalName: string | null;
  sourceWord: string;
  supported: boolean;
}

export interface ASLRepresentation {
  sourceText: string;
  tokens: ASLToken[];
}

// Map the strict native integer list to a quick evaluation set natively.
const SUPPORTED_ASL_SET = new Set<string>();
Object.values(ASL_VOCAB).forEach(val => Object.values(val).length > 0 && SUPPORTED_ASL_SET.add(val.toUpperCase()));

export function textToASL(text: string): ASLRepresentation {
    const tokens: ASLToken[] = [];
    
    if (!text || text.trim() === '') {
        return { sourceText: text || '', tokens: [] };
    }

    const words = text.trim().split(/\s+/);
    
    for (const rawWord of words) {
        // Drops punctuation securely mapping bounds cleanly without erasing exact casing from UI. 
        const cleanStr = rawWord.replace(/[^\w\s]/g, '').toUpperCase();
        
        let canonical: string | null = null;
        let isSupported = false;

        if (cleanStr.length > 0) {
            if (SUPPORTED_ASL_SET.has(cleanStr)) {
                canonical = cleanStr;
                isSupported = true;
            } else if (ASL_ALIASES[cleanStr]) {
                canonical = ASL_ALIASES[cleanStr];
                isSupported = true;
            }
        }
        
        tokens.push({
            canonicalName: canonical,
            sourceWord: rawWord, 
            supported: isSupported
        });
    }

    return {
        sourceText: text,
        tokens
    };
}
