# SignVox — V2 model-hosting requirements (ONNX objects) (2026-10-16)

Blocker V2 of `docs/migration/vercel-launch-audit-2026-10-16.md`, reported separately as requested.

**Update 2026-10-16:** the contract itself was proven on loopback
(`docs/migration/onnx-hosting-contract-test-2026-10-16.md`), and Cloudflare R2 was evaluated with
current published limits and pricing — the setup procedure, CORS policy, cost model and Vercel
variables are in `docs/migration/r2-hosting-runbook-2026-10-16.md`. Nothing has been created or
uploaded: R2 needs the owner's account action.

**Status: requirements and a verification plan only.** No bucket exists, nothing has been uploaded,
no host has been chosen, and no request, redirect, CORS preflight, Range response or inference has
been exercised against any remote host. **Production recognition must not be claimed to work until
every item in §7 passes on the deployed origin.**

---

## 1. Why the models cannot ship in the repository

| Object | Bytes | MiB | Git | GitHub |
|---|---|---|---|---|
| `spoter_v2_model.onnx` | 121,801 | 0.12 | gitignored (`*.onnx`, `.gitignore:36`) | fine |
| `spoter_v2_model.onnx.data` | 187,711,488 | 179.02 | gitignored (`*.onnx.data`, `.gitignore:122`) | **exceeds GitHub's 100 MiB hard per-file block** |
| `spoter_pilot.onnx` | 1,711,205 | 1.63 | gitignored | fine |
| `spoter_pilot.onnx.data` | 187,580,416 | 178.89 | gitignored | **exceeds GitHub's 100 MiB hard per-file block** |

MEASURED: sizes above; all four digests verify against the committed ledger
`docs/migration/local-only-assets-sha256.txt` (`sha256sum -c` → exit 0):

```
2f97a595e0e96eea8fb894507bb2c8c67a975f73d65e4b7fe7ba41538216c767  spoter_v2_model.onnx
b0f2e924105fdac691f3839ec71de1fd4fd0bf0a2697363acf6d387bb1d7c7f5  spoter_v2_model.onnx.data
cd1b9f8c418c46c7283fa538310f5b4073aab944e66936da95b9aa504b837cc2  spoter_pilot.onnx
18a08aa8b5055ef6f483271103551ef6bf82a99f8e2be667e38247749ef9eec7  spoter_pilot.onnx.data
```

A clone-equivalent build therefore produces a `dist` with **no model at all** (MEASURED: 158.59 MiB /
19 files, zero `spoter_*` files), so the deployed site's recognition fetch 404s today.

## 2. Runtime contract the host must satisfy (from the code, not from a convention)

* `web/src/lib/inference.ts:90-93` sets `sessionOptions.externalData = [{ path: `${basename}.data`,
  data: `${modelUrl}.data` }]`. **The sidecar URL is derived by appending `.data` to the model URL.**
  Consequence: the graph and its sidecar must live side by side under one base URL, and the object
  names must be exactly the ones above — the suffix is never configured.
* `web/src/lib/inference.ts` configures `executionProviders: ['wasm']` and pins the runtime binary via
  `ort.env.wasm.wasmPaths` (`absoluteWasmPaths()`, line 65; the wasm URL is pinned at line 69), so the
  ONNX side is pure HTTP: fetch + ranged reads. No server-side code, no signing, no auth.
* The 79-class graph references 186 external-data tensors by `location/offset/length`; the pilot
  references 185. **CORRECTED 2026-10-16 after the loopback contract test**
  (`docs/migration/onnx-hosting-contract-test-2026-10-16.md` §6.2): with `onnxruntime-web@1.30.0` and
  this explicit `externalData` configuration, the library fetched the graph **and** the whole `.data`
  sidecar with plain full `GET`s and sent **no** `Range` header (measured server-side, per request).
  Range/206 therefore is **not** demonstrated as required; it remains recommended (cheap, useful for
  resumable or partial downloads, and safe against future ORT behaviour).
* Caching in the browser is what makes the 179 MiB acceptable: `immutable` + one year means a client
  pays it once. The avatar GLB (47.4 MiB) is committed and stays same-origin, so the model host
  carries the ONNX pairs only.

## 3. Requirements for the four objects

1. **Public read**, no signed URLs or auth headers (the app fetches them with a plain `fetch`/`GET`).
2. **Exact object names** from §1, all four under **one base prefix**.
3. **Content-Type: `application/octet-stream`**, and **no content transformation** — the objects must
   be byte-identical to the files whose digests are in §1 (verify after upload, §7.4).
4. **Range requests**: `Accept-Ranges: bytes` and `206 Partial Content` with a correct
   `Content-Range`. **Recommended, not measured-required** — see the correction in §2; a host that
   ignores `Range` and always returns the full object would still work with today's ORT, at the cost of
   any resume/partial-read capability.
5. **CORS**, because the page origin is the Vercel domain:
   * `Access-Control-Allow-Origin`: the deployed origin (or `*`; `web/vercel.json` already uses `*`
     for the same-origin `/spoter_.*` route, so `*` is consistent with the existing design).
   * `Access-Control-Expose-Headers: Content-Range, Content-Length, Accept-Ranges` — without these
     the browser hides the headers ORT needs.
   * **A preflight may be sent**: measured 2026-10-16, Chromium treats a single-range
     `Range: bytes=0-99` as CORS-safelisted (no preflight) but preflighted a suffix range
     (`bytes=-32`). So the host must answer `OPTIONS` with a 2xx and
     `Access-Control-Allow-Headers: range` plus `Access-Control-Allow-Methods: GET, HEAD, OPTIONS` —
     and a plain `curl -I` cannot confirm it is right, because it is the browser that decides when to
     preflight.
6. **`Cache-Control: public, max-age=31536000, immutable`** (mirrors what `web/vercel.json` already
   sets for `/spoter_.*`).
7. **Static, stable URLs.** Immutable caching means the URL is the version identity: any re-export of
   a model must land on a new path, or caches will serve the old weights forever.
8. **A production-ready hostname.** Do not serve production traffic from a development-only endpoint
   (Cloudflare documents `r2.dev` subdomains as development-oriented; use a custom domain or the
   serving domain you intend to keep). **Verify this on the chosen host's current docs before you
   switch it on** — it is a plan assumption, not something this audit tested.

## 4. Environment variables (build-time, Vite-inlined)

Vite replaces `import.meta.env.VITE_*` at **build** time, so these must exist in the Vercel project
before the build; changing them later requires a redeploy, and preview and production are separate
environments that each need them:

```
VITE_SPOTER_V2_URL=<base>/spoter_v2_model.onnx
VITE_SPOTER_PILOT_URL=<base>/spoter_pilot.onnx
# VITE_AVATAR_GLB_URL stays UNSET - the production GLB is committed and served same-origin.
```

Locally the same values go in `web/.env.local` (gitignored); `.env.example:31-33` already carries the
commented names.

## 5. Host candidates (choose before uploading anything)

The catalog check on 2026-10-16 lists these S3-compatible object stores, in the order the earlier
plan ranked them for this workload (public read, ~370 MB of objects, egress-dominated):

| Candidate | Why it is on the list | Caveat |
|---|---|---|
| **Cloudflare R2** (proposed in the plan) | S3-compatible, **zero egress fees** — the deciding factor when one cold visitor pulls ~179 MiB | `r2.dev` is dev-only; plan for a custom domain |
| Backblaze B2 | S3-compatible, cheapest storage tier | Free egress allowance is limited; check the current formula |
| Wasabi | S3-compatible, no egress fees | Minimum retention/pricing terms |
| Storj, Tigris | S3-compatible alternatives | Verify CORS-header and preflight support |
| Supabase Storage | already in this stack (Supabase client is a dependency) | free egress is metered (~5 GB/month per the earlier plan) — one cold visitor is ~0.18 GB, so ~28 visitors/month |
| Vercel Blob | named in Vercel's own "optimise deployment storage" guidance for large media | egress is billed; couples model delivery to the web host |
| GitHub LFS (deployment option, not a host) | Vercel documents an opt-in Git setting that pulls LFS objects | it puts 358 MiB into the repository, needs the LFS quota and the project setting enabled, and abandons the "small repo" property the migration is built on |

**Egress arithmetic (DERIVED from MEASURED sizes):** the 79-class pair is 179.1 MiB, the 3-class pilot
pair 180.5 MiB, and a cold visitor loads the 79-class pair — **≈17.5 GiB per 100 uncached visitors,
≈175 GiB per 1,000**. Immutable caching means repeat visits cost nothing, but the hosting choice
should be made on that number, not on object count. No pricing figure is quoted here as verified:
confirm current pricing on the vendor's own page before committing.

## 6. Deliberately unchanged

Nothing in this document touches the frozen vocabulary, the SPOTER V2 pipeline or architecture, model
preprocessing, or the production avatar. The plan is upload-and-point, not rewrite-and-optimise.
Optional later work (fp16/quantised re-export, or `onnxruntime-web` wasm trimming of ~82 MiB of
never-fetched variants in `dist`) is out of scope and would change validated artefacts.

## 7. Verification checklist to run before claiming production recognition works

Run against the **deployed origin**, not localhost (CORS and preflight differ).

| # | Check | Pass criterion |
|---|---|---|
| 7.1 | `curl -sSI <base>/spoter_v2_model.onnx` | `200`, `Content-Type: application/octet-stream`, `Accept-Ranges: bytes`, `Cache-Control` immutable, `Access-Control-Allow-Origin` present |
| 7.2 | `curl -sS -D- -o /dev/null -H "Range: bytes=0-99" <base>/spoter_v2_model.onnx` | `206` + correct `Content-Range` + `Access-Control-Expose-Headers` containing `Content-Range` |
| 7.3 | Preflight: `curl -sS -X OPTIONS -D- -o /dev/null -H "Origin: <deployed origin>" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: range" <base>/spoter_v2_model.onnx` | 2xx with `Access-Control-Allow-Headers: range` (and the same for `.onnx.data`) |
| 7.4 | Download both sidecars and compare `sha256sum` with §1 | byte-identical, no HTML/XML error body |
| 7.5 | Deploy with §4 set, then load the live site and inspect the network log | model requests return 200/206 from the host, no CORS error, no mixed-content or redirect-to-error-page |
| 7.6 | **Inference, not just download**: drive one known input through the live page | the same class/output as the local run; logits sane; no "Failed to load model" contract error |
| 7.7 | Cold-cache timing and size on a fresh browser profile | total bytes ≈ 179 MiB for the 79-class pair; latency recorded (no target asserted yet) |
| 7.8 | Both graphs resolve `${modelUrl}.data` (§2) | pilot and 79-class both load, including the pilot fallback path |

Until 7.1-7.8 pass, the honest status of the deployed site is: **the avatar and the UI work; the
recognition model is not available**. Nothing above has been run yet.
