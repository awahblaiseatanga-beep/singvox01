import { describe, it, expect } from 'vitest';
import { textToASL } from '../lib/textToASL';

describe('Text to ASL Canonical Representation Engine', () => {

    it('1, 2, 3: Normalizes whitespaces, casing, and gracefully bails empty nodes natively', () => {
        expect(textToASL("   ").tokens.length).toBe(0);
        expect(textToASL("").tokens.length).toBe(0);
        
        const spaceRes = textToASL(" hello   world ");
        expect(spaceRes.tokens.length).toBe(2);
        expect(spaceRes.tokens[0].canonicalName).toBe('HELLO'); // Normalizes casing 
    });

    it('4, 16, 17: Handles heavy punctuation strings robustly while preserving source values', () => {
        const result = textToASL("Yes, please! Wait... I don't understand.");
        expect(result.sourceText).toBe("Yes, please! Wait... I don't understand.");
        
        // Symbols should drop for mapping mapping correctly
        expect(result.tokens[0].canonicalName).toBe('YES');
        expect(result.tokens[1].canonicalName).toBe('PLEASE');
        expect(result.tokens[2].canonicalName).toBe('WAIT');
        expect(result.tokens[3].canonicalName).toBe('ME'); // alias logic hits! "I" => "ME"
        expect(result.tokens[4].canonicalName).toBe(null); // dont
        expect(result.tokens[4].supported).toBe(false); 
        expect(result.tokens[5].canonicalName).toBe('UNDERSTAND');
        
        // Exact spelling is preserved inside sourceWord accurately!
        expect(result.tokens[0].sourceWord).toBe('Yes,');
        expect(result.tokens[4].sourceWord).toBe("don't");
    });

    it('5, 6, 7, 14: Accurately preserves strings orders natively bounding duplicates gracefully', () => {
        const result = textToASL("Hello hello go go");
        expect(result.tokens.length).toBe(4);
        expect(result.tokens[0].canonicalName).toBe('HELLO');
        expect(result.tokens[1].canonicalName).toBe('HELLO');
        expect(result.tokens[2].canonicalName).toBe('GO');
        expect(result.tokens[3].canonicalName).toBe('GO');
    });

    it('8, 9, 13: Identifies unsupported words implicitly preserving sequence explicitly avoiding hallucinogenic drops', () => {
        const result = textToASL("Can you feel the love");
        
        expect(result.tokens[0].canonicalName).toBeNull(); // CAN
        expect(result.tokens[0].supported).toBe(false);
        expect(result.tokens[0].sourceWord).toBe('Can');
        
        expect(result.tokens[1].canonicalName).toBe('YOU');
        expect(result.tokens[2].canonicalName).toBe('FEEL');
        
        expect(result.tokens[3].canonicalName).toBeNull(); // THE
        expect(result.tokens[3].supported).toBe(false);
        
        expect(result.tokens[4].canonicalName).toBe('LOVE');
    });

    it('10, 11: Identifies requested explicit project Aliases gracefully redirecting values', () => {
        const result = textToASL("Now I hurt okay phone");
        
        expect(result.tokens[0].canonicalName).toBe('TODAY');
        expect(result.tokens[1].canonicalName).toBe('ME');
        expect(result.tokens[2].canonicalName).toBe('PAIN');
        expect(result.tokens[3].canonicalName).toBe('GOOD');
        expect(result.tokens[4].canonicalName).toBe('CALL');
    });

    it('12: Example test cases specifically pass bounding "I need help" mapping native', () => {
        const result = textToASL("I need help");
        expect(result.tokens[0].canonicalName).toBe("ME"); // Via User Alias dictionary matching exact structural definitions cleanly!
        expect(result.tokens[1].canonicalName).toBe("NEED");
        expect(result.tokens[2].canonicalName).toBe("HELP");
    });

    it('18: Determinism holds structurally when sequentially mapping exact structures', () => {
        for (let i = 0; i < 5; i++) {
            const result = textToASL("I need help");
            expect(result.tokens[1].canonicalName).toBe('NEED');
        }
    });

    // 15, 19, 20 are executed visually bounded directly inside App.tsx which tests multiple arrays sequentially!
});
