import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { createServer, type Server } from 'node:http';
import { readFileSync } from 'node:fs';
import {
  SIDECAR_SUFFIX,
  classifyAssetResponse,
  describeAssetFailure,
  firstBlockingFailure,
  isHtmlBody,
  preflightModelAssets,
  probeAsset,
  sidecarUrl,
} from '../lib/assetPreflight';

/**
 * Regression tests for the production failure this preflight exists to catch.
 *
 * `web/vercel.json` rewrites every unmatched path to `/index.html`, so a large
 * asset that was never deployed is answered with `HTTP 200 text/html` and the
 * SPA document — not with 404. Both symptoms this suite guards against were
 * observed that way: ONNX Runtime and three.js `GLTFLoader` each receive an HTML
 * document and fail with an error that looks like a code defect.
 */

/** The real SPA document that the production rewrite serves for a missing file. */
const SPA_DOCUMENT = readFileSync(new URL('../../index.html', import.meta.url));

describe('asset preflight: response classification', () => {
  it('treats an HTML answer as the SPA fallback, not as an asset', () => {
    const result = classifyAssetResponse({
      status: 200,
      contentType: 'text/html',
      bodyStart: SPA_DOCUMENT.subarray(0, 256).toString('utf-8'),
    });
    expect(result.ok).toBe(false);
    expect(result.failure).toBe('spa-fallback');
    expect(result.conclusive).toBe(true);
  });

  it('detects the fallback even when the host mislabels the media type', () => {
    const result = classifyAssetResponse({
      status: 200,
      contentType: 'application/octet-stream',
      bodyStart: SPA_DOCUMENT.subarray(0, 256).toString('utf-8'),
    });
    expect(result.ok).toBe(false);
    expect(result.failure).toBe('spa-fallback');
  });

  it('accepts a real binary asset', () => {
    expect(classifyAssetResponse({ status: 200, contentType: 'application/octet-stream' }).ok).toBe(true);
    expect(classifyAssetResponse({ status: 206, contentType: 'application/octet-stream' }).ok).toBe(true);
    expect(classifyAssetResponse({ status: 200, contentType: 'model/gltf-binary' }).ok).toBe(true);
  });

  it('reports a definitive HTTP failure as conclusive', () => {
    const notFound = classifyAssetResponse({ status: 404, contentType: 'text/plain' });
    expect(notFound.ok).toBe(false);
    expect(notFound.failure).toBe('http-error');
    expect(notFound.conclusive).toBe(true);

    const serverError = classifyAssetResponse({ status: 500, contentType: null });
    expect(serverError.failure).toBe('http-error');
  });

  it('never treats an unreadable probe answer as a defect in the asset', () => {
    const blank = classifyAssetResponse({ status: 200, contentType: null });
    expect(blank.ok).toBe(false);
    expect(blank.conclusive).toBe(false);
    expect(blank.failure).toBe('empty-response');
  });

  it('recognises an HTML body from its opening bytes', () => {
    expect(isHtmlBody('  <!DOCTYPE html>\n<html lang="en">')).toBe(true);
    expect(isHtmlBody('\n<html>')).toBe(true);
    expect(isHtmlBody('<div id="root"></div>')).toBe(true);
    expect(isHtmlBody('\x08\x00\x00\x00binaryprotobuf')).toBe(false);
  });
});

describe('asset preflight: against a host that rewrites missing paths like the SPA', () => {
  let server: Server;
  let origin: string;
  /** A port with nothing listening, for the inconclusive-probe case. */
  let deadOrigin: string;

  beforeAll(async () => {
    server = createServer((req, res) => {
      const url = req.url ?? '/';
      // The production host: any path that is not a real file gets index.html.
      if (url.startsWith('/spoter_')) {
        res.writeHead(200, { 'Content-Type': 'text/html', 'Cache-Control': 'no-cache' });
        res.end(SPA_DOCUMENT);
        return;
      }
      if (url.startsWith('/hosted/')) {
        res.writeHead(200, { 'Content-Type': 'application/octet-stream' });
        res.end(Buffer.alloc(64, 7));
        return;
      }
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('not found');
    });
    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));

    const address = server.address();
    if (address === null || typeof address === 'string') throw new Error('server did not bind');
    origin = `http://127.0.0.1:${address.port}`;

    const probeServer = createServer((_req, res) => res.end());
    await new Promise<void>((resolve) => probeServer.listen(0, '127.0.0.1', resolve));
    const probeAddress = probeServer.address();
    if (probeAddress === null || typeof probeAddress === 'string') throw new Error('probe server did not bind');
    deadOrigin = `http://127.0.0.1:${probeAddress.port}`;
    await new Promise<void>((resolve) => probeServer.close(() => resolve()));
  });

  afterAll(async () => {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  });

  it('blocks the default, unhosted model URLs and names the reason', async () => {
    const probes = await preflightModelAssets('79-class baseline', `${origin}/spoter_v2_model.onnx`);

    expect(probes).toHaveLength(2);
    expect(probes.map((p) => p.label)).toEqual([
      '79-class baseline model graph',
      '79-class baseline model weights sidecar',
    ]);
    for (const probe of probes) {
      expect(probe.ok).toBe(false);
      expect(probe.failure).toBe('spa-fallback');
    }
    expect(probes[1].url).toBe(`${origin}/spoter_v2_model.onnx${SIDECAR_SUFFIX}`);

    const failure = firstBlockingFailure(probes);
    expect(failure?.label).toBe('79-class baseline model graph');

    const message = describeAssetFailure(failure!);
    expect(message).toContain('is not present in this deployment');
    expect(message).toContain(`${origin}/spoter_v2_model.onnx`);
    expect(message).toContain('HTTP 200, text/html');
    expect(message).toContain(SIDECAR_SUFFIX);
  });

  it('passes a model whose graph and sidecar are really hosted', async () => {
    const probes = await preflightModelAssets('79-class baseline', `${origin}/hosted/spoter_v2_model.onnx`);

    expect(probes.every((probe) => probe.ok)).toBe(true);
    expect(probes.every((probe) => probe.conclusive)).toBe(true);
    expect(firstBlockingFailure(probes)).toBeUndefined();
  });

  it('reports a hard HTTP failure', async () => {
    const probe = await probeAsset('avatar model', `${origin}/nothing-here`);
    expect(probe.failure).toBe('http-error');
    expect(probe.status).toBe(404);
    expect(probe.conclusive).toBe(true);
  });

  it('reports an unreachable host as inconclusive so it can never block a session', async () => {
    const probes = await preflightModelAssets('79-class baseline', `${deadOrigin}/spoter_v2_model.onnx`);

    expect(probes.every((probe) => probe.failure === 'network-error')).toBe(true);
    expect(probes.every((probe) => probe.conclusive === false)).toBe(true);
    expect(firstBlockingFailure(probes)).toBeUndefined();
    expect(sidecarUrl(`${deadOrigin}/spoter_v2_model.onnx`)).toBe(
      `${deadOrigin}/spoter_v2_model.onnx${SIDECAR_SUFFIX}`,
    );
  });
});
