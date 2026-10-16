import { describe, it, expect } from 'vitest';
import { deriveLiveStatus, friendlyError } from '../lib/uiStatus';
import { firstBlockingFailure, describeAssetFailure, type AssetProbe } from '../lib/assetPreflight';

/**
 * The asset preflight turns a missing model file into a definite error string.
 * These tests pin the two halves of that contract together: the message the
 * engine throws must be classified as a hosting problem by the UI, and it must
 * not be mistaken for the generic "check your connection" advice.
 */
describe('friendlyError: missing model asset is reported as a hosting problem', () => {
  /** Exactly how useSignVoxEngine builds the message after a preflight failure. */
  const engineMessage = (probe: AssetProbe) =>
    `ONNX model error: Sign model asset missing — ${describeAssetFailure(probe)}`;

  const spaFallbackProbe: AssetProbe = {
    label: '79-Class Baseline (SPOTER V2) model graph',
    url: 'https://example.vercel.app/spoter_v2_model.onnx',
    ok: false,
    conclusive: true,
    status: 200,
    contentType: 'text/html',
    failure: 'spa-fallback',
  };

  it('classifies the preflight message as unavailable rather than a connection problem', () => {
    const friendly = friendlyError(engineMessage(spaFallbackProbe));
    expect(friendly.title).toBe('Sign recognition is unavailable in this build');
    expect(friendly.hint).not.toMatch(/connection/i);
  });

  it('does not swallow genuine model errors', () => {
    const friendly = friendlyError('ONNX model error: Failed to initialize ONNX Runtime: WASM err');
    expect(friendly.title).toBe('Sign model could not load');
  });

  it('keeps the camera failures it already handled', () => {
    expect(friendlyError('NotAllowedError: Permission denied').title).toBe('Camera access is blocked');
    expect(friendlyError('NotFoundError: no camera').title).toBe('No camera found');
  });

  // Regression: the secure-context branch matched the substring `https`, so any
  // error quoting an https asset URL was reported as a TLS problem — including
  // the R2-hosted model URL, which is the very case an operator needs to read.
  it('does not read an https URL in an error as a secure-connection failure', () => {
    const hosted = friendlyError(
      'Failed to initialize ONNX Runtime for https://pub-example.r2.dev/spoter_v2_model.onnx: WASM err',
    );
    expect(hosted.title).not.toBe('A secure connection is required');
    expect(hosted.title).toBe('Sign model could not load');
  });

  it('still reports a missing secure context', () => {
    expect(friendlyError("Cannot read properties of undefined (reading 'getUserMedia')").title).toBe(
      'A secure connection is required',
    );
  });

  // Regression: the status chip said "Camera unavailable" for *every* engine
  // error, so a deployment missing its model file — with the camera and
  // landmarks running perfectly — told the user their camera was broken.
  it('shows the real failure in the status chip, not "Camera unavailable"', () => {
    const live = deriveLiveStatus({
      status: 'live',
      error: engineMessage(spaFallbackProbe),
      isActive: true,
      bufferReady: false,
      bufferProgress: 0,
    });
    expect(live.phase).toBe('error');
    expect(live.label).toBe('Recognition unavailable');
    expect(live.label).not.toBe('Camera unavailable');
    expect(live.detail).not.toMatch(/camera/i);
  });

  it('still names a camera problem as a camera problem', () => {
    const live = deriveLiveStatus({
      status: 'requesting camera',
      error: 'NotAllowedError: Permission denied',
      isActive: true,
      bufferReady: false,
      bufferProgress: 0,
    });
    expect(live.label).toBe('Camera blocked');
    expect(live.detail).toMatch(/browser settings/i);
  });

  it('gives every friendly error a short chip label', () => {
    const samples = [
      'NotAllowedError: Permission denied',
      'NotFoundError: no camera',
      'NotReadableError: could not start video source',
      "Cannot read properties of undefined (reading 'getUserMedia')",
      engineMessage(spaFallbackProbe),
      'ONNX model error: Failed to initialize ONNX Runtime',
      'something unexpected',
    ];
    for (const sample of samples) {
      const friendly = friendlyError(sample);
      expect(friendly.chip.length).toBeGreaterThan(0);
      expect(friendly.chip.length).toBeLessThanOrEqual(24);
    }
  });

  it('is only reached when a probe is conclusive and failing', () => {
    const inconclusive: AssetProbe = {
      ...spaFallbackProbe,
      conclusive: false,
      failure: 'network-error',
    };
    expect(firstBlockingFailure([inconclusive])).toBeUndefined();
    expect(firstBlockingFailure([inconclusive, spaFallbackProbe])).toBe(spaFallbackProbe);
  });
});
