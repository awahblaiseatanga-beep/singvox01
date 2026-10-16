# SignVox — production incident: missing avatar and broken live translation (2026-10-16)

Status: **code fix applied, committed and pushed** to `singvox01/main` as `fac4370`. The
deployment-side half (hosting the two ONNX graphs, Vercel project settings) is **not** done here and
is the only thing left before recognition can work on the deployed site.

Every claim below is labelled **MEASURED** (produced by a command or a browser observation in this
session), **DERIVED** (arithmetic or reasoning on measured values) or **NOT CLAIMED**.

---

## 1. Symptom, and what it actually was

Reported: the deployed site shows **no 3D avatar** and **live translation does not work**.

Both symptoms have one cause and it is a hosting cause, not a code cause: **the deployment is
missing the large binary assets, and the host answers for them in a way that hides the fact.**

`web/vercel.json` contains the standard SPA rewrite:

```json
"rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
```

A file that does not exist therefore does **not** return 404. It returns
`HTTP 200`, `Content-Type: text/html`, with the app's own `index.html` as the body:

* ONNX Runtime is handed an HTML document where it expects a protobuf graph and fails with an opaque
  parser error;
* three.js `GLTFLoader` fails with `Unexpected token '<'`.

Both errors read like defects in this repository, so every attempt to debug them by reading code
started from a false premise. **MEASURED** — this is not theory; the behaviour is reproduced in
`web/src/tests/assetPreflight.test.ts` against a server configured to rewrite exactly like
`web/vercel.json`:

```
HEAD http://127.0.0.1:4189/spoter_v2_model.onnx       → 200   (Fetch)
HEAD http://127.0.0.1:4189/spoter_v2_model.onnx.data  → 200   (Fetch)
```

Two `HTTP 200`s for two files that do not exist anywhere in the deployment.

### 1.1 Why the assets are absent — and which of the two causes is live

| Asset | In Git? | Can it be? |
|---|---|---|
| `web/public/avatar/SignVox_Female_Competition_Prototype.glb` | **yes** | yes — 47.40 MiB, under GitHub's 100 MiB per-file block. **MEASURED**: `git cat-file -s` = 49,701,152 B; first bytes `glTF\x02` (a real binary glTF, **not** a Git-LFS pointer — there is no `.gitattributes` in this repository); `.gitignore` re-includes it explicitly (`!web/public/avatar/SignVox_Female_Competition_Prototype.glb`) |
| `spoter_v2_model.onnx` + `.data` | **no** | **no** — the sidecar is 179.02 MiB, past the 100 MiB hard block; `*.onnx` and `*.onnx.data` are gitignored |
| `spoter_pilot.onnx` + `.data` | **no** | **no** — same reason |

**DERIVED, and this is the part to read carefully:** the avatar GLB *is* in the repository, so an
avatar that is missing in production cannot be explained by the repository at its current commit.
It is explained by one of two things, and the new error message distinguishes them:

| Cause | What the deployment serves for a missing asset | Message the fix prints |
|---|---|---|
| Assets genuinely absent (V2: ONNX never hosted) | SPA fallback — `HTTP 200 text/html` | *"…answered with the app's own HTML page (HTTP 200, text/html) instead of the file. That is the single-page-app fallback for a missing asset."* |
| `web/vercel.json` never applied — **Root Directory not set to `web`** | a real `404` | *"…is unavailable — `<url>` answered HTTP 404."* |

Both are fixed by project configuration, not by a code change, and both were already written up as
blockers in `docs/migration/vercel-launch-audit-2026-10-16.md` (§3.3 V3, §5 V2). This incident is
what those blockers look like from the user's side.

---

## 2. The fix

Five files, `fac4370`. The principle: **a code defect and an undeployed file must never look the
same again.** Where an opaque failure was possible, it is replaced by a definite diagnosis that names
the URL and what actually came back.

| File | Change |
|---|---|
| `web/src/lib/assetPreflight.ts` *(new)* | Probes an asset URL before it is used. `HEAD` first (no body, no CORS preflight); a ranged `GET` sniffs the first 512 bytes only when `HEAD` told us nothing. Classifies the answer as `spa-fallback` / `http-error` / `empty-response` / `network-error`. **Only a *conclusive* failure blocks a session**, so a probe that merely cannot complete (offline, CORS, intercepting proxy) can never itself become the reason recognition fails. |
| `web/src/engine/useSignVoxEngine.ts` | Probes the model graph **and** its `.data` sidecar before `SpoterInferenceSession.create`, and the avatar GLB before `loadGLB`. Both failure paths now surface the resolved URL. Also guards the previously unguarded `new THREE.WebGLRenderer()` — three.js throws straight out of the constructor with no WebGL context, and an exception thrown inside that effect unmounts the page instead of showing anything — and reports `webglcontextlost` rather than leaving a silent black viewport. |
| `web/src/lib/uiStatus.ts` | Two genuine misdiagnoses removed (**§3**), plus the status chip now reports the real failure. |
| `web/src/tests/assetPreflight.test.ts` *(new)* | 10 tests. The one that matters runs a real HTTP server configured to rewrite like `web/vercel.json` and asserts the message names the URL and `HTTP 200, text/html`. |
| `web/src/tests/uiStatus.test.ts` *(new)* | 9 tests pinning the preflight message to the user-facing copy, including the two regressions below. |

---

## 3. Two misdiagnoses found while fixing this

These are real bugs in the existing code, found because the incident forced the error paths to be
read carefully. Both are now regression-tested.

**3.1 Any error quoting an `https` URL was reported as a TLS problem.** The secure-context branch
tested `raw.includes('https')`, so `"Failed to initialize ONNX Runtime for
https://pub-….r2.dev/spoter_v2_model.onnx: WASM err"` — the single most informative string this app
can produce — was displayed to the user as *"A secure connection is required"*. It now matches the
actual secure-context symptoms (`secure context`, `insecure`, `mediadevices`, `getusermedia`), which
is also what a page without a secure context really produces: no `navigator.mediaDevices`, so the
failure arrives as a missing `getUserMedia`, not as a named `DOMException`.

**3.2 A missing model file was reported as "Camera unavailable".** `deriveLiveStatus` returned that
label for *every* engine error. In the reproduced incident the camera and all three landmarkers were
running perfectly; only the model was missing. Telling someone their camera is broken when the
deployment is missing a file sends them to fix the wrong thing. The chip now reads the real failure:

| Failure | Chip |
|---|---|
| model file not in the deployment | `Recognition unavailable` |
| permission denied | `Camera blocked` |
| no camera present | `No camera` |
| camera held by another app | `Camera busy` |
| no secure context | `Needs HTTPS` |
| other model/ONNX failure | `Sign model unavailable` |
| anything else | `Camera unavailable` |

---

## 4. Evidence

### 4.1 Build and tests

| Check | Result |
|---|---|
| `npx tsc -b --force` (`web/`) | **exit 0** — MEASURED |
| `npx vite build` (clean clone, unhosted config) | **exit 0**, 58.6s — MEASURED |
| `npx vitest run src/tests/uiStatus.test.ts src/tests/assetPreflight.test.ts` | **19/19 passed** — MEASURED |
| Full suite, clean clone, with the fix | **220 passed, 5 skipped, 0 failed; exit 0** — MEASURED. The 5 skips are the asset-dependent traces, which skip because a clean clone has no ONNX files |
| Full suite, this working tree (every local asset present) | 33 files / 222 tests, 0 failures — MEASURED in the previous pass. It takes ≈29 minutes here because the two asset-dependent traces then run the real models instead of skipping |

### 4.2 End-to-end in a real browser — the unhosted configuration (the incident)

`vite preview` on the built, unhosted bundle, `#live`, **Start translation** pressed. **MEASURED** —
network log:

```
HEAD http://127.0.0.1:4189/spoter_v2_model.onnx       → 200
HEAD http://127.0.0.1:4189/spoter_v2_model.onnx.data  → 200
GET  https://cdn.jsdelivr.net/…/vision_wasm_internal.wasm → 200
GET  https://storage.googleapis.com/mediapipe-models/…/hand_landmarker.task → 200
```

Console:

```
[App] Background ONNX load failed: Error: Sign model asset missing — the 79-Class Baseline
(SPOTER V2) model graph is not present in this deployment — http://127.0.0.1:4189/spoter_v2_model.onnx
answered with the app's own HTML page (HTTP 200, text/html) instead of the file. That is the
single-page-app fallback for a missing asset. Host the file (and, for a model, its .data sidecar
beside it) and set the matching VITE_ variable before redeploying.
```

On screen: status chip **`Recognition unavailable`**, panel heading **"Sign recognition is
unavailable in this build"**, hint *"The sign model file is missing from this deployment…"*, with the
technical sentence below it for whoever operates the deployment. The message that used to read
*"Camera unavailable"* is gone (`document.body.innerText.includes('Camera unavailable')` → `false`).
MediaPipe still initialised normally — `[MediaPipe] Landmarkers ready with delegates` — so the
preflight did not disturb the camera path.

### 4.3 End-to-end in a real browser — the R2-hosted configuration (the fix on the happy path)

Same build with `VITE_SPOTER_V2_URL` pointing at the R2 prefix. **MEASURED**:

```
HEAD https://pub-….r2.dev/spoter_v2_model.onnx       → 200
HEAD https://pub-….r2.dev/spoter_v2_model.onnx.data  → 200
GET  https://pub-….r2.dev/spoter_v2_model.onnx       → 200
GET  https://pub-….r2.dev/spoter_v2_model.onnx.data  → 200
GET  /onnxruntime/ort-wasm-simd-threaded.wasm        → 200
```

then, from the in-app diagnostics: **`ONNX Runtime: PASS`**, provider **WASM**, `Input: [1,60,366]`,
`Output: 79 logits`, no `NaN`/`Inf`. The 187 MB sidecar really loads and the session really
initialises against the hosted model — the positive path is verified, not assumed.

Avatar positive path, same session: `HEAD /avatar/SignVox_Female_Competition_Prototype.glb → 200`,
then `GET … → 200` and the model loads.

---

## 5. What is still outstanding — and it is not code

**V2 — host the ONNX files.** Recognition cannot work on the deployed site until the two
graph+sidecar pairs are hosted and the URLs are set in the Vercel project. The full requirements
(CORS, `Access-Control-Expose-Headers`, Range/206, the `${modelUrl}.data` sibling rule) are in
`docs/migration/v2-model-hosting-requirements-2026-10-16.md` and
`docs/migration/r2-hosting-runbook-2026-10-16.md`; `tools/verify_onnx_hosting.mjs` checks a candidate
host against them before a deploy. Until then the app will say so plainly instead of failing opaquely
— which is the whole point of this change, not a substitute for the hosting.

**V3 — Vercel project settings.** Root Directory = `web`, and *"Include source files outside of the
Root Directory in the Build Step"* = ON (production code imports `avatar/controller/*` from outside
`web/`). Details and the documentation check are in the launch audit §3.3.

`VITE_AVATAR_GLB_URL` must stay **unset**: the GLB is committed and served same-origin.

---

## 6. Manual smoke-test checklist

Run in this order on the **deployed** URL after the V2/V3 configuration above. Steps 1–3 need no
camera. Keep the browser console open (F12) for all of them — the console is where the precise
diagnosis appears.

| # | Step | Expected |
|---|---|---|
| 1 | Hard-reload the deployed site (Cmd/Ctrl+Shift+R) | `index.html` 200; one `assets/index-*.js` 200; **no 404 and no HTML answer for a `.glb`, `.onnx`, `.wasm` or `.task`** in the Network tab |
| 2 | Avatar page (`#avatar`) | Avatar visible and idle-animating. Network shows `HEAD /avatar/SignVox_Female_Competition_Prototype.glb` → **200** and `GET` → **200**. The status chip leaves *"Loading GLB model…"* and settles on **Ready** |
| 3 | Avatar page, on a browser with WebGL disabled (`chrome://flags` → disable hardware acceleration, or `--disable-gpu`) | A visible message: **"Error: 3D graphics (WebGL) are unavailable in this browser (…)"**. The page must stay mounted — **not** a blank/white screen |
| 4 | Live page (`#live`) → **Start translation**; allow the camera | Video appears; chip: *Starting camera…* → *Preparing recognition…* → *Getting ready* → **Ready**. Console: `[MediaPipe] Landmarkers ready with delegates` |
| 5 | Console in step 4 | **No** `Sign model asset missing`. If it appears, read the sentence: it names the URL and whether the answer was the SPA page (`HTTP 200, text/html`) or a real `HTTP 404` — §1.1 says which misconfiguration that is |
| 6 | Same session, diagnostics page (`#diagnostics`) → **Run Synthetic ONNX Test** (no camera needed) | **`ONNX Runtime: PASS`**, provider WASM, `Input: [1,60,366]`, `Output: 79 logits`, no `NaN`/`Inf`. This is the single fastest proof that the hosted model is really being served to a real browser |
| 7 | Sign **HELLO**, then **YES**, then **NO**, each held steady in frame for ~2 s | Recognised sign appears in *Translation*; the avatar plays the matching clip; the sign is appended to *Recent translations* |
| 8 | Sign something outside HELLO/YES/NO (e.g. **THANK YOU**) | Recognised as text; console notes the missing clip (`no clip "ASL_THANK_YOU" found — returning to neutral`); the avatar returns to neutral. Text-only is the correct, honest behaviour here |
| 9 | Press **End session**, then **Start translation** again | Camera stops and restarts cleanly; the buffer refills; no duplicated recognition or stuck *End session* |
| 10 | Deny camera permission (browser site settings → Block → reload → Start translation) | Chip **`Camera blocked`**, heading **"Camera access is blocked"**, hint pointing at browser settings — *not* a generic failure |
| 11 | Join page (`#join`) | Submitting shows the waiting-list outcome; with Supabase unconfigured it reports the missing configuration rather than throwing |

**Two regressions worth re-checking by hand**, because both were live misdiagnoses:

* No error containing an `https://` URL may be reported as *"A secure connection is required"*.
  Reproduce by reading the console while step 5 fails (if it fails) — the ONNX message quotes an
  https URL and must be classified as a hosting problem.
* A model-only failure must never say *"Camera unavailable"*. In step 5, the camera is working; the
  chip must say **`Recognition unavailable`**.

### 6.1 Rebuilding against the hosted models

```bash
cd web
VITE_SPOTER_V2_URL=https://<host>/spoter_v2_model.onnx \
VITE_SPOTER_PILOT_URL=https://<host>/spoter_pilot.onnx \
  npm run build          # both values are inlined at build time, so a redeploy is required
```

Setting them in the Vercel project environment does the same thing for a Git-connected deployment.
They are **build-time** values: changing one has no effect until the site is rebuilt.

---

## 7. Not claimed

* **No deployment was performed.** Nothing was deployed, previewed, promoted or published; no Vercel
  project setting, environment variable or R2 object was created or changed.
* The R2-hosted browser run in §4.3 proves the model loads from a **public R2 dev URL**. It does not
  prove the CORS preflight, Range/206 or `Access-Control-Expose-Headers` behaviour of the production
  host chosen for launch; `tools/verify_onnx_hosting.mjs` is the check for that.
* Which of the two §1.1 causes is live **on the user's Vercel project** was not observed — the
  deployment could not be inspected from this session. The fix makes the deployed site itself report
  which one it is, in one browser session.
* No live signer was tested; §4.3 exercises the model with the synthetic diagnostic input, and §4.2
  exercises the failure path. Recognition *accuracy* on a live signer remains as documented in
  `docs/RECOGNITION_79_CLASS_RECOVERY_AUDIT.md`.
* The working-tree test suite was last run before the status-chip change of §3.2; the post-change
  full-suite run is the clean-clone one (220 passed / 5 skipped / exit 0). The chip change touches
  `web/src/lib/uiStatus.ts` only, whose callers are `App.tsx` and `LiveTranslationPage.tsx`.
