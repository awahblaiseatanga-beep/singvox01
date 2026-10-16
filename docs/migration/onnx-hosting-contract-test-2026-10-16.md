# SignVox — ONNX hosting contract test against a loopback HTTP server (2026-10-16)

Companion to `docs/migration/v2-model-hosting-requirements-2026-10-16.md` and
`docs/migration/vercel-launch-audit-2026-10-16.md`.

**Scope:** verify that the *contract* the production code expects of an external ONNX host can be
satisfied, end to end, on loopback — HTTP semantics, CORS from a separate web origin, byte integrity,
and real inference over HTTP compared with the same inference run off local files.

**Status:** all seven requested checks were executed and passed, except where §6 records a failure or
a correction. **Nothing was uploaded, no bucket was created, no vendor was contacted, no money was
spent, and no source artifact, model file, preprocessing step, vocabulary or pipeline was modified.**
Nothing is staged, committed, pushed or deployed.

All harness files lived outside the repository except two temporary files that were deleted after the
run (§8). The model files themselves were only read.

---

## 1. Harness (temporary, loopback only)

One Node process (`node server.mjs`, no dependencies) exposing three loopback origins:

| Port | Role | Root | CORS |
|---|---|---|---|
| 18081 | **model host** — serves the real files under their exact production names (`/spoter_v2_model.onnx`, `/spoter_v2_model.onnx.data`, `/spoter_pilot.onnx`, `/spoter_pilot.onnx.data`) | `D:\Singvox\Singvox\web\public` | yes (`*` + expose `Content-Range, Content-Length, Accept-Ranges`, `OPTIONS` → `allow-headers: range`) |
| 18082 | aux origin — the pre-built 60×366 input windows (`/window/{v2,pilot}.f32`) | temp dir | yes |
| 18083 | **negative control** — same files, **no** CORS headers | `web/public` | no |

Every request was logged as JSON (`server.log`) with method, path, `Range`, `Origin`,
`Access-Control-Request-Headers`, status, `Content-Range` and bytes served.

The *browser* origin was the project's own Vite dev server, `http://127.0.0.1:5199` (a temporary page
that imports the real `/src/lib/inference.ts`). So the browser test was genuinely cross-origin:
page `127.0.0.1:5199` → model host `127.0.0.1:18081`, exactly the production shape (app origin →
external model origin), using the production inference module, not a reimplementation.

## 2. HTTP semantics (CLI, `curl`)

| # | Request | Result |
|---|---|---|
| 1 | `GET /spoter_v2_model.onnx` | **200**, `121801` B (matches the ledger size exactly) |
| 2 | `GET /spoter_v2_model.onnx.data` | **200**, `187711488` B |
| 3 | `GET /spoter_pilot.onnx` | **200**, `1711205` B |
| 4 | `GET /spoter_pilot.onnx.data` | **200**, `187580416` B |
| 5 | `HEAD /spoter_v2_model.onnx` | **200** + `Content-Type: application/octet-stream`, `Cache-Control: public, max-age=31536000, immutable`, `Accept-Ranges: bytes`, `Content-Length: 121801`, `Access-Control-Allow-Origin: *`, `Access-Control-Expose-Headers: Content-Range, Content-Length, Accept-Ranges` |
| 6 | `GET` + `Range: bytes=0-99` (graph) | **206**, `Content-Length: 100`, `Content-Range: bytes 0-99/121801`; first 8 bytes `080a12077079746f` = byte-identical to the local file |
| 7 | `GET` + `Range: bytes=0-99` (sidecar) | **206**, `Content-Range: bytes 0-99/187711488` |
| 8 | `GET` + `Range: bytes=-32` (suffix form) | **206**, `Content-Range: bytes 121769-121800/121801`; body identical to the local file's last 32 bytes |
| 9 | `GET` + `Range: bytes=99999999-` | **416** + `Content-Range: bytes */121801` |
| 10 | `OPTIONS` with `Origin` + `Access-Control-Request-Method: GET` + `Access-Control-Request-Headers: range` | **204** + `Access-Control-Allow-Origin: *`, `Access-Control-Allow-Methods: GET, HEAD, OPTIONS`, `Access-Control-Allow-Headers: range`, `Access-Control-Expose-Headers: …`, `Access-Control-Max-Age: 86400` — for **both** the graph and the sidecar |
| 11 | Unknown path | **404** |

## 3. CORS from a separate web origin (browser, Chromium 130 / Electron 33)

Page origin `http://127.0.0.1:5199`, model origin `127.0.0.1:18081`:

| Probe | Result |
|---|---|
| `HEAD` graph (cross-origin) | `200`, readable `content-type`, `accept-ranges: bytes`, `content-length`, `cache-control` |
| `fetch` + `Range: bytes=0-99` | **`206`**, readable **`content-range: bytes 0-99/121801`** (only possible if `Access-Control-Allow-Origin` **and** `Expose-Headers` are correct), body 100 B, first bytes `080a12077079746f` |
| `fetch` + `Range: bytes=0-99` on `.data` | **`206`**, `content-range: bytes 0-99/187711488` |
| `fetch` + `Range: bytes=-32` | **`206`**, `content-range: bytes 121769-121800/121801` |
| `fetch` + `Range: bytes=99999999-` | **`416`**, readable `content-range: bytes */121801` |
| **Negative control**: same `Range` request against the no-CORS host `18083` | **blocked** — console: *"Access to fetch at 'http://127.0.0.1:18083/spoter_v2_model.onnx' from origin 'http://127.0.0.1:5199' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present"*; network `net::ERR_FAILED` |
| Preflight actually sent by the browser | yes — server log shows `OPTIONS /spoter_v2_model.onnx origin=http://127.0.0.1:5199 ACRH=range → 204` |

Note: `Access-Control-Allow-Origin` itself reads back as `null` from JS in this browser build — that is
a browser visibility rule for `Access-Control-*` response headers, not a missing header. The decisive
evidence is the pair (206 with a readable `Content-Range` cross-origin) + (hard CORS failure against
the no-CORS control). The CLI header dump in §2 #10 captures the literal headers.

## 4. Byte integrity

* All four objects downloaded in full from the loopback host and hashed: **OK** against
  `docs/migration/local-only-assets-sha256.txt` (`spoter_v2_model.onnx`, `spoter_v2_model.onnx.data`,
  `spoter_pilot.onnx`, `spoter_pilot.onnx.data` — 4/4 match).
* `sha256sum -c` re-run on the source files on disk after the test: **all 4 OK** (exit 0) — the
  artifacts were never modified.

## 5. Real inference over HTTP vs the same input locally (the decisive check)

Input format = the existing supported one: `Float32Array(60 × 366)`, built from the existing recorded
fixtures exactly as the recognition tests do (`loadNpy` + `applyV2Normalization`), fed to
`session.inputNames[0]` as `[1, 60, 366]` through the **production** `SpoterInferenceSession`.

| Model | Fixture (existing) | Window | Local file run | HTTP run (in browser) | Comparison |
|---|---|---|---|---|---|
| 79-class `spoter_v2_model.onnx` | `dataset_extracted/0022932153577568393-HELLO_features.npy` (31 frames) | `60×366`, sha256 `a58ca43c…03d2d` | 79 logits, top-1 **HELLO 0.997422**, load 3251 ms, infer 190.4 ms | 79 logits, top-1 **HELLO 0.997422**, load 3011.9 ms, infer 349.4 ms | **max abs logit diff = 0.000000000; 0 of 79 logits differ; identical top-1 and confidence** |
| 3-class `spoter_pilot.onnx` | `processed_pilot/6901051427765104-NO_features.npy` (16 frames) | `60×366`, sha256 `509cc4f1…1f482e` | 3 logits, top-1 **YES 0.999698**, load 1379 ms, infer 199.1 ms | 3 logits, top-1 **YES 0.999698**, load 1969.6 ms, infer 440.6 ms | **max abs logit diff = 0.000000000; 0 of 3 logits differ** |

Both sessions were created with the production code path
(`SpoterInferenceSession.create('http://127.0.0.1:18081/spoter_v2_model.onnx')`), which sets
`externalData = [{ path: '<basename>.data', data: '<modelUrl>.data' }]` — so the derived-suffix
contract was exercised, not bypassed. Browser console shows both sessions initialising via `wasm` and
no CORS/loader errors.

**Therefore: for these two models, loading the graph *and* its sidecar over cross-origin HTTP yields
bit-identical logits to loading from local files.** The hosting mechanism does not change recognition
output.

Two honest caveats on that table:
* **Label mismatch is a model observation, not a hosting result:** the pilot returned YES 0.999698 for
  a clip stored as `…-NO_features.npy` — *identically* in both runs. This says nothing about hosting;
  it is a pilot-model/preprocessing observation that I did not investigate (out of scope) and it does
  not affect the equality result.
* The 79-class run agrees with the recorded clip's own label (HELLO), consistent with the repo's
  existing parity test.

## 6. Findings, failures and corrections (things that did *not* go as the requirements assumed)

1. **`onnxruntime-web` in Node cannot load a model from an HTTP URL** (FAILED, expected-unknown).
   In Node, ORT resolves the model path with `fs`, so
   `SpoterInferenceSession.create('http://127.0.0.1:18081/spoter_v2_model.onnx')` failed with
   `ENOENT: no such file or directory, open 'D:\Singvox\Singvox\web\http:\127.0.0.1:18081\spoter_v2_model.onnx'`
   (stack: `wasm-utils-load-file.ts` → `readFile`). Consequence: **the HTTP contract cannot be tested
   from the Node/vitest suite at all** — it must be tested in a browser (as done here). Node can still
   host and serve, and its local-file inference remains a valid reference.
2. **ORT did *not* issue ranged requests during inference** (correction). The server-side trace of the
   browser run shows, for each model, a plain **full `GET`** of the graph *and* a plain full `GET` of the
   `.data` sidecar — no `Range` header at all:
   `GET /spoter_v2_model.onnx → 200 (121801 B)`, `GET /spoter_v2_model.onnx.data → 200 (187711488 B)`,
   `GET /spoter_pilot.onnx → 200`, `GET /spoter_pilot.onnx.data → 200`. Because `inference.ts` passes
   an explicit `externalData` URL, ORT downloads the whole sidecar and slices it in memory rather than
   reading tensor offsets with ranges. **The existing documents' claim that "Range/206 is REQUIRED, not
   optional, because the installed onnxruntime-web issues ranged requests" is not supported by this
   measurement** — with onnxruntime-web 1.30.0 and this configuration, no ranged request was made by
   the library. Range/206 support stays recommended (cheap, useful for resumable/partial downloads and
   for any future ORT behaviour change) but must not be described as measured-required.
3. **A single-range `Range` header does not always trigger a preflight** (correction/nuance).
   Chromium treated `Range: bytes=0-99` as a CORS-safelisted request header (no `OPTIONS`), and
   preflighted the suffix form `bytes=-32` (server log: `OPTIONS … ACRH=range → 204`, then the 206).
   So a host must still answer `OPTIONS` correctly, but a green `curl` preflight test does not prove
   the browser path is exercised for every request shape.
4. Cold-cache transfer is the real cost: one cold browser load moved **179.1 MiB** (79-class pair) and
   **180.5 MiB** (pilot pair) — measured server-side as `563.1 MiB` and `562.7 MiB` including the CLI
   verification downloads.

## 7. Checks not run (explicit)

* Any real external host: no vendor, no bucket, no upload, no signed URL, no custom domain.
* TLS/HTTPS, HTTP/2/3, a CDN, compression (`gzip`/`br`), and redirect behaviour.
* Browsers other than the bundled Chromium 130 (Firefox/Safari CORS and preflight behaviour untested).
* Concurrent clients, range-resume of an interrupted download, and multi-hour cache revalidation.
* The deployed site (no deploy), the live camera path, MediaPipe landmark extraction, and the full
  recognition pipeline end-to-end. This test compares *inference equality on a fixed window*, not
  live recognition accuracy.
* Recognition quality/accuracy: not re-measured, and the pilot label mismatch in §5 is not explained.
* The other two `public/onnxruntime/*.wasm` variants and the video-passthrough path: untouched.

## 8. Cleanup record

* Loopback model host / aux origin / control host: stopped, ports 18081-18083 released.
* Vite dev server on 5199: stopped.
* Temporary in-repo files created for the test and deleted afterwards:
  `web/__tmp_v2_local_infer.mts`, `web/__tmp_v2_contract.html`.
* Temporary out-of-repo files (harness server, scripts, downloaded copies, logs): removed.
* The four model artifacts were read-only throughout; `sha256sum -c` against the ledger still passes.
* `git status`: no staged files; no tracked file modified by this test.
