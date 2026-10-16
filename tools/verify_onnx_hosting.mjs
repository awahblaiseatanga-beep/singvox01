#!/usr/bin/env node
// SignVox — external ONNX host verification (Phase 3 of the hosting task).
//
// Runs the multi-part hosting contract against a real, already-configured public host:
//   * all four objects: HEAD, plain GET, byte-range probes, content lengths, content types, caching
//   * CORS: preflight OPTIONS and a plain GET carrying an Origin, with the headers the browser needs
//   * SHA-256 of every downloaded object compared with docs/migration/local-only-assets-sha256.txt
//
// It never writes to the repository, never uploads, and holds no credentials. The model files are
// downloaded to a temporary directory, hashed, and deleted.
//
// Usage:
//   node tools/verify_onnx_hosting.mjs --base https://models.example.com
//   node tools/verify_onnx_hosting.mjs --base https://pub-xxxx.r2.dev --origin http://127.0.0.1:5199
//   node tools/verify_onnx_hosting.mjs --base https://models.example.com --no-download
//
// Exit code: 0 when every required check passes, 1 otherwise. Informational results (e.g. a host
// that ignores Range) are reported without failing the run, because ONNX Runtime was measured not to
// send ranged requests — see docs/migration/onnx-hosting-contract-test-2026-10-16.md §6.2.

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';

const OBJECTS = [
  { key: 'spoter_v2_model.onnx', size: 121801 },
  { key: 'spoter_v2_model.onnx.data', size: 187711488 },
  { key: 'spoter_pilot.onnx', size: 1711205 },
  { key: 'spoter_pilot.onnx.data', size: 187580416 },
];
const LEDGER = 'docs/migration/local-only-assets-sha256.txt';

function arg(name, fallback = null) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] && !process.argv[i + 1].startsWith('--')
    ? process.argv[i + 1]
    : fallback;
}
const has = (name) => process.argv.includes(`--${name}`);

const base = (arg('base') || '').replace(/\/+$/, '');
const origin = arg('origin', 'http://127.0.0.1:5199');
const control = arg('control');
const doDownload = !has('no-download');

if (!base) {
  console.error('usage: node tools/verify_onnx_hosting.mjs --base <https://host[/prefix]> [--origin <url>] [--control <url>] [--no-download]');
  process.exit(2);
}

const failures = [];
const notes = [];
const fail = (m) => failures.push(m);

function ledgerDigests() {
  const out = new Map();
  try {
    for (const line of fs.readFileSync(LEDGER, 'utf8').split('\n')) {
      const m = /^([0-9a-f]{64})\s+\*?(.*)$/.exec(line.trim());
      if (m && /spoter_.*\.onnx(\.data)?$/.test(m[2])) out.set(path.basename(m[2]), m[1]);
    }
  } catch (e) {
    fail(`cannot read the SHA-256 ledger ${LEDGER}: ${e.message}`);
  }
  return out;
}

const headerSummary = (h) => ({
  contentType: h.get('content-type'),
  contentLength: h.get('content-length'),
  contentRange: h.get('content-range'),
  acceptRanges: h.get('accept-ranges'),
  cacheControl: h.get('cache-control'),
  etag: h.get('etag') ? 'present' : null,
  allowOrigin: h.get('access-control-allow-origin'),
  allowMethods: h.get('access-control-allow-methods'),
  allowHeaders: h.get('access-control-allow-headers'),
  exposeHeaders: h.get('access-control-expose-headers'),
  age: h.get('age'),
  cfCacheStatus: h.get('cf-cache-status'),
  server: h.get('server'),
});

async function request(url, init = {}) {
  const started = Date.now();
  try {
    const res = await fetch(url, init);
    return { ok: true, status: res.status, headers: res.headers, res, ms: Date.now() - started };
  } catch (e) {
    return { ok: false, error: String(e?.message ?? e), ms: Date.now() - started };
  }
}

async function downloadSha256(url) {
  const res = await fetch(url);
  if (!res.ok) { await res.body?.cancel?.(); return { status: res.status, error: 'non-2xx' }; }
  const tmp = path.join(os.tmpdir(), `signvox-verify-${crypto.randomUUID()}.bin`);
  const hash = crypto.createHash('sha256');
  let bytes = 0;
  const out = fs.createWriteStream(tmp);
  for await (const chunk of res.body) { hash.update(chunk); bytes += chunk.length; out.write(chunk); }
  await new Promise((r) => out.end(r));
  fs.rmSync(tmp, { force: true });
  return { status: res.status, bytes, sha256: hash.digest('hex') };
}

const report = {
  base,
  origin,
  control: control || null,
  startedAt: new Date().toISOString(),
  objects: {},
  cors: {},
  controlCheck: null,
  failures: [],
  notes: [],
};

const digests = ledgerDigests();
console.log(`\n=== SignVox ONNX host verification ===`);
console.log(`base   : ${base}`);
console.log(`origin : ${origin}   (the browser origin CORS is being tested for)`);
console.log(`ledger : ${LEDGER} (${digests.size} expected digests)\n`);

for (const obj of OBJECTS) {
  const url = `${base}/${obj.key}`;
  const entry = { url };
  console.log(`--- ${obj.key}`);

  const head = await request(url, { method: 'HEAD' });
  if (!head.ok) {
    entry.head = { error: head.error };
    fail(`${obj.key}: HEAD failed — ${head.error}`);
  } else {
    entry.head = { status: head.status, headers: headerSummary(head.headers) };
    const ctype = head.headers.get('content-type') || '';
    if (head.status !== 200) {
      fail(`${obj.key}: HEAD returned ${head.status}, expected 200 (object missing or not publicly readable)`);
    } else {
      const len = Number(head.headers.get('content-length'));
      if (len !== obj.size) fail(`${obj.key}: HEAD Content-Length ${head.headers.get('content-length')} != expected ${obj.size}`);
      if (!/octet-stream/i.test(ctype)) notes.push(`${obj.key}: content-type is "${ctype || '(none)'}" — application/octet-stream is recommended for binary models`);
      if (/no-cache|no-store|max-age=0/i.test(head.headers.get('cache-control') || '')) notes.push(`${obj.key}: Cache-Control "${head.headers.get('cache-control')}" is not immutable-cache friendly`);
      if (!head.headers.get('accept-ranges')) notes.push(`${obj.key}: no Accept-Ranges header on HEAD (not required by ORT — informational)`);
    }
    console.log(`    HEAD ${head.status}  length=${head.headers.get('content-length')}  type=${ctype}  cache=${head.headers.get('cache-control')}  accept-ranges=${head.headers.get('accept-ranges') ?? '(none)'}  age=${head.headers.get('age') ?? '-'}  cf-cache=${head.headers.get('cf-cache-status') ?? '-'}`);
  }

  const get = await request(url, { headers: { Range: 'bytes=0-99' } });
  if (!get.ok) {
    entry.range = { error: get.error };
    fail(`${obj.key}: ranged GET failed — ${get.error}`);
  } else {
    const body = new Uint8Array(await get.res.arrayBuffer());
    entry.range = { status: get.status, bytes: body.length, headers: headerSummary(get.headers), first8Hex: [...body.slice(0, 8)].map((b) => b.toString(16).padStart(2, '0')).join('') };
    console.log(`    GET+Range bytes=0-99 -> ${get.status}  content-range=${get.headers.get('content-range') ?? '(none)'}  bytes=${body.length}`);
    if (get.status === 206) {
      if (!get.headers.get('content-range')) fail(`${obj.key}: 206 without Content-Range`);
      if (body.length !== 100) fail(`${obj.key}: 206 returned ${body.length} bytes, expected 100`);
    } else if (get.status === 200) {
      notes.push(`${obj.key}: host ignores Range and returns 200 (acceptable — ORT does not use ranges; resume/partial reads unavailable)`);
    } else {
      fail(`${obj.key}: ranged GET returned ${get.status}`);
    }
  }

  const suffix = await request(url, { headers: { Range: 'bytes=-32' } });
  if (suffix.ok) {
    const b = new Uint8Array(await suffix.res.arrayBuffer());
    entry.suffixRange = { status: suffix.status, bytes: b.length, contentRange: suffix.headers.get('content-range') };
    console.log(`    GET+Range bytes=-32  -> ${suffix.status}  content-range=${suffix.headers.get('content-range') ?? '(none)'}  bytes=${b.length}`);
  } else {
    entry.suffixRange = { error: suffix.error };
  }

  const plain = await request(url, { headers: { Origin: origin } });
  if (plain.ok) {
    entry.plainWithOrigin = { status: plain.status, headers: headerSummary(plain.headers) };
    await plain.res.body?.cancel?.();
    const acao = plain.headers.get('access-control-allow-origin');
    const expose = plain.headers.get('access-control-expose-headers') || '';
    if (!acao) fail(`${obj.key}: no Access-Control-Allow-Origin on a GET carrying Origin ${origin}`);
    if (!/content-range/i.test(expose)) notes.push(`${obj.key}: Expose-Headers lacks Content-Range (only matters if the app reads it — it does not today)`);
    console.log(`    GET (Origin) -> ${plain.status}  ACAO=${acao ?? '(none)'}  expose=${expose || '(none)'}`);
  } else {
    fail(`${obj.key}: plain GET failed — ${plain.error}`);
  }

  if (doDownload) {
    const dl = await downloadSha256(url);
    entry.download = { status: dl.status, bytes: dl.bytes ?? null, sha256: dl.sha256 ?? null, error: dl.error ?? null };
    const expected = digests.get(obj.key);
    if (dl.status !== 200 || dl.error) {
      fail(`${obj.key}: download failed — HTTP ${dl.status}${dl.error ? ` (${dl.error})` : ''}; the object is missing or not readable at the public URL, so its digest cannot be checked`);
      console.log(`    download FAILED — HTTP ${dl.status}${dl.error ? ` (${dl.error})` : ''} (no bytes hashed)`);
    } else {
      const sizeOk = dl.bytes === obj.size;
      const hashOk = expected ? dl.sha256 === expected : false;
      if (!sizeOk) fail(`${obj.key}: downloaded ${dl.bytes} bytes, expected ${obj.size}`);
      if (!expected) fail(`${obj.key}: no digest in the ledger to compare against`);
      else if (!hashOk) fail(`${obj.key}: SHA-256 mismatch — got ${dl.sha256}, ledger says ${expected}`);
      console.log(`    download ${dl.bytes} B  sha256=${dl.sha256.slice(0, 16)}…  ${hashOk && sizeOk ? 'MATCHES the ledger' : 'MISMATCH'}`);
    }
  }
  report.objects[obj.key] = entry;
  console.log('');
}

console.log('--- CORS');
const preflight = await request(`${base}/${OBJECTS[0].key}`, {
  method: 'OPTIONS',
  headers: { Origin: origin, 'Access-Control-Request-Method': 'GET', 'Access-Control-Request-Headers': 'range' },
});
if (preflight.ok) {
  report.cors.preflight = { status: preflight.status, headers: headerSummary(preflight.headers) };
  await preflight.res.body?.cancel?.();
  const h = preflight.headers;
  console.log(`    OPTIONS preflight -> ${preflight.status}`);
  console.log(`      ACAO=${h.get('access-control-allow-origin') ?? '(none)'}  methods=${h.get('access-control-allow-methods') ?? '(none)'}  allow-headers=${h.get('access-control-allow-headers') ?? '(none)'}  max-age=${h.get('access-control-max-age') ?? '(none)'}`);
  if (!h.get('access-control-allow-origin')) fail('preflight: no Access-Control-Allow-Origin');
  if (!/range/i.test(h.get('access-control-allow-headers') || '')) notes.push('preflight: Access-Control-Allow-Headers does not list "range" — only matters if the browser preflights a Range request (measured: single-range bytes=a-b is safelisted)');
} else {
  report.cors.preflight = { error: preflight.error };
  notes.push(`preflight OPTIONS to ${base} failed from Node (${preflight.error}) — a curl-level failure here is not proof the browser path fails, but it must be re-checked in a browser`);
  console.log(`    OPTIONS preflight -> FAILED from this client: ${preflight.error}`);
}

if (control) {
  console.log('\n--- negative control (must NOT be readable cross-origin)');
  const c = await request(`${control.replace(/\/+$/, '')}/${OBJECTS[0].key}`, { headers: { Origin: origin, Range: 'bytes=0-99' } });
  report.controlCheck = c.ok ? { status: c.status, allowOrigin: c.headers.get('access-control-allow-origin') } : { error: c.error };
  if (c.ok) await c.res.body?.cancel?.();
  console.log(`    ${c.ok ? `status ${c.status}, ACAO=${c.headers.get('access-control-allow-origin') ?? '(none)'}` : `blocked/failed: ${c.error}`}`);
  console.log('    (CORS is enforced by the browser, not by curl — this control is only conclusive when run in a browser)');
}

report.failures = failures;
report.notes = notes;
console.log('\n=== SUMMARY ===');
if (failures.length === 0) console.log('required checks: PASS');
else { console.log('required checks: FAIL'); for (const f of failures) console.log(`  - ${f}`); }
if (notes.length) { console.log('\nnotes (informational, not failures):'); for (const n of notes) console.log(`  - ${n}`); }
console.log('\nmachine-readable report:');
console.log(JSON.stringify(report, null, 2));
process.exit(failures.length === 0 ? 0 : 1);
