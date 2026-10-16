/**
 * Preflight for the large binary assets this app deliberately does not ship.
 *
 * The deployed site is a static SPA whose rewrite rule (`web/vercel.json`) sends
 * *every* unmatched path to `/index.html`. A missing file therefore does not
 * return 404: it returns `HTTP 200` with `Content-Type: text/html` and the SPA
 * document as the body. That is harmless for a link, but fatal for an asset:
 *
 *   - ONNX Runtime is handed an HTML document where it expects a protobuf graph
 *     and fails with an opaque parser error that reads like a code defect;
 *   - three.js `GLTFLoader` fails with `Unexpected token '<'`, which reads like a
 *     broken model rather than a model that was never deployed.
 *
 * The two ONNX graphs and their `.data` sidecars cannot live in the repository
 * (187 MB each, past GitHub's 100 MB per-file block), so a deployment must be
 * given the `VITE_SPOTER_*` hosts recorded in `.env.example`. Probing the URLs
 * before use turns "recognition silently does not work" into a definite
 * diagnosis naming the URL and the reason.
 *
 * Design rule: only *definitive* signals block a session. A probe that cannot
 * complete (offline, CORS on a HEAD, an intercepting proxy) is reported as
 * inconclusive and the caller proceeds, so this can never itself become the
 * reason recognition fails.
 */

export type AssetProbeFailure =
  /** The server answered with its own HTML document instead of the asset. */
  | 'spa-fallback'
  /** A definitive non-2xx answer. */
  | 'http-error'
  /** The asset answered, but with nothing that could be a file. */
  | 'empty-response'
  /** The probe could not complete; the asset itself is not implicated. */
  | 'network-error';

export type AssetProbe = {
  /** What this URL is for, phrased for an operator, e.g. "…model graph". */
  label: string;
  /** The URL as requested (resolved to absolute). */
  url: string;
  ok: boolean;
  /** False when the probe itself failed rather than the asset being wrong. */
  conclusive: boolean;
  status?: number;
  contentType?: string | null;
  failure?: AssetProbeFailure;
};

/** Body prefix of the SPA document, lower-cased and whitespace-trimmed. */
const HTML_BODY_MARKERS = ['<!doctype html', '<html'];

/** True when a body starts like an HTML document rather than a binary asset. */
export function isHtmlBody(bodyStart: string): boolean {
  const head = bodyStart.trimStart().slice(0, 256).toLowerCase();
  return (
    HTML_BODY_MARKERS.some((marker) => head.startsWith(marker)) || head.includes('id="root"')
  );
}

export type ResponseFacts = {
  status: number;
  contentType: string | null;
  /** First bytes of the body, when one was read. */
  bodyStart?: string;
};

export type ClassifiedResponse = {
  ok: boolean;
  /** True when the answer identifies a real problem, not an unknown. */
  conclusive: boolean;
  failure?: AssetProbeFailure;
};

/**
 * Decide whether a response to a request for a *binary* asset is the asset.
 *
 * Pure and total so it can be reasoned about — and tested — without a server.
 * The `spa-fallback` branch is the one that matters in production: it is the
 * single answer that a static host gives for a file that was never deployed.
 */
export function classifyAssetResponse(facts: ResponseFacts): ClassifiedResponse {
  const { status, contentType, bodyStart = '' } = facts;

  if (status < 200 || status >= 400) {
    return { ok: false, conclusive: true, failure: 'http-error' };
  }

  const mediaType = (contentType ?? '').split(';')[0].trim().toLowerCase();
  if (mediaType === 'text/html') {
    return { ok: false, conclusive: true, failure: 'spa-fallback' };
  }
  if (bodyStart.length > 0 && isHtmlBody(bodyStart)) {
    // The host mislabelled the fallback; the body still proves what happened.
    return { ok: false, conclusive: true, failure: 'spa-fallback' };
  }
  if (contentType === null && bodyStart.length === 0) {
    // Nothing observable: the probe learned nothing about the asset.
    return { ok: false, conclusive: false, failure: 'empty-response' };
  }

  return { ok: true, conclusive: true };
}

const PROBE_TIMEOUT_MS = 15_000;
const SNIFF_BYTES = 512;

function resolve(url: string): string {
  const base = typeof document !== 'undefined' ? document.baseURI : 'http://localhost/';
  try {
    return new URL(url, base).href;
  } catch {
    return url;
  }
}

type RawProbe = { status: number; contentType: string | null; bodyStart?: string };

async function requestAsset(
  url: string,
  method: 'HEAD' | 'GET',
  fetchImpl: typeof fetch,
): Promise<RawProbe> {
  const response = await fetchImpl(url, {
    method,
    // A ranged GET keeps a 187 MB sidecar from being downloaded just to read
    // its first bytes; the stream is cancelled after the sniff regardless.
    headers: method === 'GET' ? { Range: `bytes=0-${SNIFF_BYTES - 1}` } : undefined,
    signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
  });

  let bodyStart: string | undefined;
  if (method === 'GET' && response.body) {
    const reader = response.body.getReader();
    try {
      const { value } = await reader.read();
      if (value && value.byteLength > 0) {
        bodyStart = new TextDecoder('utf-8', { fatal: false }).decode(value);
      }
    } finally {
      await reader.cancel().catch(() => undefined);
    }
  }

  return { status: response.status, contentType: response.headers.get('content-type'), bodyStart };
}

/**
 * Probe one binary asset URL.
 *
 * HEAD answers the question outright on every host this app targets (GitHub
 * Pages, Vercel, R2 all return the discriminating `Content-Type`), so it is
 * tried first: no body is transferred and no CORS preflight is triggered. A
 * ranged GET is used only when HEAD is unusable or told us nothing.
 */
export async function probeAsset(
  label: string,
  url: string,
  fetchImpl: typeof fetch = fetch,
): Promise<AssetProbe> {
  const target = resolve(url);

  try {
    let raw = await requestAsset(target, 'HEAD', fetchImpl);
    let classified = classifyAssetResponse(raw);

    if (!classified.conclusive) {
      raw = await requestAsset(target, 'GET', fetchImpl);
      classified = classifyAssetResponse(raw);
    }

    return {
      label,
      url: target,
      ok: classified.ok,
      conclusive: classified.conclusive,
      status: raw.status,
      contentType: raw.contentType,
      failure: classified.failure,
    };
  } catch (cause) {
    return {
      label,
      url: target,
      ok: false,
      conclusive: false,
      failure: 'network-error',
      contentType: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/** The sidecar is always the graph URL plus this suffix (`inference.ts`). */
export const SIDECAR_SUFFIX = '.data';

/** Absolute URL of the `.data` sidecar that must sit beside the graph. */
export function sidecarUrl(modelUrl: string): string {
  return `${modelUrl}${SIDECAR_SUFFIX}`;
}

/**
 * Probe a model's graph and its external-data sidecar together.
 *
 * Both are required: the graph is small and can be present while the sidecar —
 * the part too large to commit — is missing.
 */
export async function preflightModelAssets(
  modelName: string,
  modelUrl: string,
  fetchImpl: typeof fetch = fetch,
): Promise<AssetProbe[]> {
  return Promise.all([
    probeAsset(`${modelName} model graph`, modelUrl, fetchImpl),
    probeAsset(`${modelName} model weights sidecar`, sidecarUrl(modelUrl), fetchImpl),
  ]);
}

/** The first probe that found a real problem, ignoring inconclusive ones. */
export function firstBlockingFailure(probes: AssetProbe[]): AssetProbe | undefined {
  return probes.find((probe) => !probe.ok && probe.conclusive);
}

/** Operator-facing sentence naming the URL and what actually came back. */
export function describeAssetFailure(probe: AssetProbe): string {
  const answer =
    probe.status === undefined
      ? 'the request did not complete'
      : `HTTP ${probe.status}${probe.contentType ? `, ${probe.contentType}` : ''}`;

  switch (probe.failure) {
    case 'spa-fallback':
      return (
        `the ${probe.label} is not present in this deployment — ${probe.url} answered with the ` +
        `app's own HTML page (${answer}) instead of the file. That is the single-page-app ` +
        `fallback for a missing asset. Host the file (and, for a model, its ${SIDECAR_SUFFIX} ` +
        `sidecar beside it) and set the matching VITE_ variable before redeploying.`
      );
    case 'http-error':
      return `the ${probe.label} is unavailable — ${probe.url} answered ${answer}.`;
    case 'empty-response':
      return `the ${probe.label} could not be verified — ${probe.url} answered ${answer} with no body to inspect.`;
    case 'network-error':
    default:
      return `the ${probe.label} could not be reached — ${probe.url} (${probe.contentType ?? 'no response'}).`;
  }
}
