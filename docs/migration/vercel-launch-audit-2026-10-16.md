# SignVox — Vercel launch audit and Batch B revalidation (2026-10-16)

Status: §6.1, §6.3, §6.4 **APPLIED 2026-10-16 under owner approval** (see §6a for the verified
results). Nothing is staged, committed, pushed or deployed. The V2 model-hosting requirements are
now reported separately in `docs/migration/v2-model-hosting-requirements-2026-10-16.md`.
Owner decisions honoured: the four owner-modified files stay byte-for-byte untouched and out of
every batch; Git-based Vercel deployment from `new-origin/main`; R2 stays a *proposal* (no
bucket, no upload); all four prepared source edits below are **described, not applied**.

Every number below is labelled either **MEASURED** (produced by a command in this working tree or
in the copy of it described in §0) or **DERIVED** (arithmetic on measured values) or **NOT
CLAIMED**. Nothing in this document asserts that a Vercel deployment has been performed.

---

## 0. What was actually executed

| # | Action | Result |
|---|--------|--------|
| 1 | `npm run build` in `D:\Singvox\Singvox\web` (working tree, all local files present) | **exit 0**, 1m38s. `dist` = **982.91 MiB / 32 files** (MEASURED, `dist` inventory) |
| 2 | Copy of a *clone-equivalent* tree: `git ls-files` (101 tracked paths) + the 163 Batch B payload paths, `node_modules` junctioned to `web\node_modules`, 132.7 MiB | MEASURED tree |
| 3 | `npm run build` **in that clone-equivalent tree, unmodified** | **exit 1** — `tsc -b` fails before `vite build` ever runs: 11 × `TS2307 Cannot find module 'three'` from `../avatar/controller/*.ts` + 1 cascading `TS7006` |
| 4 | `npx vite build` alone in the same tree | **exit 0**, 14.8s — the bundler alias resolves `three`; only the *type-check* step fails |
| 5 | `npx tsc -b --force` in the same tree with the §6.1 tsconfig patch applied | **exit 0** — fix verified |
| 6 | `npm run build` in the same tree with the §6.1 patch | **exit 0**, 24s. `dist` = **158.59 MiB / 19 files** (MEASURED) |
| 7 | `npm audit` / `npm audit --omit=dev` in `web` | dev tooling: 5 advisories (2 critical, 1 high, 2 moderate); **production deps: 0 vulnerabilities** |
| 8 | Manifest revalidation against disk + git (`ls-files --others[-i] --exclude-standard`, `check-ignore --no-index`) | 163/163 paths valid, see §4 |
| 9 | `git check-ignore --no-index` on the ONNX pair and the production GLB | ONNX `*.onnx`/`*.onnx.data`: **IGNORED**; production GLB (negation): **not ignored** |

Step 3 is the single hard blocker and it is **verified, not simulated**: the tree in step 2 contains
exactly what a fresh clone of `new-origin/main` after Batch B would contain (tracked files + the
163 new paths), with dependencies installed the way Vercel installs them (only in `web/`).

---

## 1. The nine non-production GLBs under `web/public/avatar/`

**Inventory (MEASURED, `ls -l` + `dist` inventory).** 12 files, 512.29 MiB:

| File | Size | In Batch B? | Copied into `dist` by Vite? |
|------|------|-------------|------------------------------|
| `SignVox_Female_Competition_Prototype.glb` | 47.40 MiB | **yes** (1b) — the production avatar | yes |
| `SignVox_Female_v5_HELLO.glb` | 85.23 MiB | no (gitignored) | yes |
| `SignVox_Female_v2.glb` | 47.64 MiB | no | yes |
| `SignVox_Female_v3.glb` | 47.64 MiB | no | yes |
| `SignVox_Female_v4_Neutral.glb` | 47.42 MiB | no | yes |
| `SignVox_Female_v5_Neutral.glb` | 47.42 MiB | no | yes |
| `SignVox_Female_v6_Neutral.glb` | 47.42 MiB | no | yes |
| `SignVox_Female_v4_HELLO.glb` | 47.33 MiB | no | yes |
| `SignVox_Female.glb` | 47.28 MiB | no | yes |
| `SignVox_Female_backup.glb` | 47.28 MiB | no | yes |
| `test_front.png` / `test_side.png` / `test_hand.png` | 0.10 / 0.10 / 0.03 MiB | **yes** (1b) | yes |

**Production references** (only one file is ever fetched at runtime):
`web/src/engine/useSignVoxEngine.ts:41` → `/avatar/SignVox_Female_Competition_Prototype.glb`
(overridable with `VITE_AVATAR_GLB_URL`), and `web/src/components/AvatarDiagnostic.tsx:8` → the same
path, hard-coded.

**Test references:**
* `web/src/tests/modelRegistry.test.ts:18` reads the **production** GLB from disk (kept).
* `web/src/tests/reproduce_trace.test.ts:14` reads `web/public/avatar/SignVox_Female.glb` — a
  **non-production** GLB. After the owner-approved fixture fix it is `describe.skipIf`-guarded, so it
  skips when the file is absent (this is the "one-line path update" B4 refers to).

**Non-build references** (local Blender/Node tooling and prose only — none is run by `vite build`,
`vitest` or the deploy): `web/test_ik_targets.mjs`, `web/test_hierarchy.mjs`, `web/test_glb_ik.mjs`,
`web/measure_ik.mjs`, `web/clean_glb.cjs`, ~25 `tools/*.py|mjs` scripts, and 6 documents under
`docs/`.

**Do the nine need excluding for the Git+Vercel path? No — and this is the main simplification of
this audit.** All nine match `.gitignore`'s `*.glb` and are absent from every batch, so a
clone-equivalent build contains **zero** of them: the 158.59 MiB `dist` in step 6 has exactly four
files under `avatar/` (the production GLB + the three test PNGs). The 47.63 MiB `avatar/` size is
`47.40 + 0.23`. No file has to be deleted, moved or excluded, and no test breaks.

**What `web/.vercelignore` actually does.** It is a *CLI-upload* exclusion list. For a Git-connected
deployment it is inert: Vercel builds the clone, and what is excluded is whatever `.gitignore` keeps
out of the repo. Two small defects, both harmless here, worth knowing:
* it lists 10 lines for 9 files — `public/avatar/SignVox_Female_v5_HELLO.glb` appears twice;
* it does **not** list the three `public/avatar/test_*.png` (0.23 MiB) that *are* in Batch B and *do*
  land in `dist`.

**Optional hardening (proposed, not required for launch).** If those GLBs are ever committed by
mistake, `dist` grows by 464.66 MiB with no warning. Cheap guard: a `closeBundle` Vite plugin in
`web/vite.config.ts` that fails the build when `dist/avatar/` contains any `*.glb` other than the
production one. Not included in the prepared diffs because it changes a build file for a risk that
does not exist today.

---

## 2. `app/package.json` and the React Native app — separate plan (no change made)

**Facts (MEASURED).**
* `app/package.json` is one of the four preserved owner changes (`git status` → `M`), so it is out of
  Batch B and untouched.
* `app/` contains **no lockfile at all** (`app/package-lock.json`, `yarn.lock`: absent), while
  `web/` and `avatar/` both have `package-lock.json`. `npm ci` cannot install the RN app.
* Of the app's own files, **3 are already tracked** (`app/App.tsx` — owner-modified, `app/package.json`
  — owner-modified, `app/utils/normalization.ts`), and **35 are in Batch B** (8 config in 1a plus 27
  `app/android/**` files in 1b).
* The declared RN dependency set (`react-native@0.74.0`, `react-native-vision-camera@4.6.4`,
  `react-native-worklets-core@1.6.3`, `react-native-reanimated@^3.8.0`) has **no effect on the web
  build or the Vercel deployment**: nothing under `web/` imports from `app/`.

**Plan (proposal only).**
1. Keep `app/package.json` out of Batch B until decision D4 is answered by you.
2. Because `app/` would otherwise be committed *half-formed* — Android sources and JS config in,
   but the manifest that describes the dependency set, the app entry point and one util still out,
   and no lockfile to make any of it installable — **defer the 35 `app/*` paths from Batch B to the
   same decision**. Removing 35 paths from Batch B does not touch the web launch at all.
3. When the mobile app is resumed, treat it as one coherent commit: `app/package.json` + `app/App.tsx`
   + the rest of `app/`, plus a regenerated `app/package-lock.json`, as its own owner-approved batch.
4. Do not add `app/` to the Vercel project (Root Directory stays `web`); the RN app is not deployable
   there.

If you prefer to keep the 35 `app/*` paths in Batch B, nothing breaks *as long as this is deliberate*;
the recommendation above is only about not shipping a partial project.

---

## 3. Build/toolchain recheck

**3.1 There is no Vite/esbuild dependency conflict (MEASURED).**
`npm ls esbuild vite` → a single, deduped tree: `vite@5.4.11` (direct, and deduped for
`@tailwindcss/vite`, `@vitejs/plugin-react`, `vitest`) with exactly one `esbuild@0.21.5`. No peer
conflict, no duplicate esbuild, no invalid/extraneous entry.

What the phrase *was* probably about is an **advisory, not a conflict**: `esbuild <=0.24.2`
(GHSA-67mh-4wv8-2f99, "any website can send requests to the development server"), reachable only
through `vite`'s dev server. `npm audit` for `web`: **5 advisories, all in dev tooling**
(`esbuild`, `tinypool <=2.1.1`, `@vitest/mocker`, plus the two carrying them); `npm audit --omit=dev`
→ **found 0 vulnerabilities**. `esbuild`, `tinypool` and `@vitest/mocker` are not in `dist`: the
shipped bundle is `index-*.js` (1.64 MiB, 467 KiB gzip) + `index-*.css`, and `vite build` does not
run a dev server on Vercel. `npm audit fix --force` would move Vite to a new major — deliberately
**not** part of the smallest safe path.

**3.2 `web/package-lock.json` is consistent with `web/package.json` (MEASURED).**
`lockfileVersion: 3`; 17/17 declared dependencies and devDependencies match their lock ranges
character for character and each has a resolved version (`@mediapipe/tasks-vision 0.10.14`,
`@supabase/supabase-js 2.118.0`, `onnxruntime-web 1.30.0`, `react`/`react-dom` 18.3.1,
`three 0.186.1`, `vite 5.4.11`, `vitest 2.1.8`, `typescript 5.6.3`, …). `avatar/package-lock.json`
also exists; `app/` has none (§2).

**3.3 Vercel project settings — required, and one of them is currently missing.**
* **Root Directory = `web`** — mandatory. `web/vercel.json` is only read when it sits at the
  configured root; with the root left at the repo root, that file is ignored and the build command,
  output directory, SPA rewrite and cache headers all silently do nothing.
* **Project Settings → Build and Deployment → Root Directory → "Include source files outside of the
  Root Directory in the Build Step" = ON** — mandatory. Production files import outside `web/`:
  `web/src/engine/useSignVoxEngine.ts:29` and `web/src/components/AvatarDiagnostic.tsx:3-6` import
  `../../../avatar/controller/*`; `web/src/tests/*` import `../../../avatar/controller/*` too. Without
  the setting, `npm run build` cannot resolve those modules. **Documentation check (2026-10-16)**: the
  [Monorepos FAQ](https://vercel.com/docs/monorepos/monorepo-faq) (last updated 2026-08-11) documents
  the option under the Root Directory section and states that *"Vercel projects created after
  August 27th 2020 23:50 UTC have this option enabled by default"*, so a project created now should
  already have it on — **verify it in the UI anyway**, because
  [Configuring a Build](https://vercel.com/docs/builds/configure-a-build) (last updated 2026-08-28)
  states the opposite default behaviour: *"Your app will not be able to access files outside of that
  directory. You also cannot use `..` to move up a level."* No Pro-plan requirement is documented for
  the option. Vercel's own caveat: a **Hobby** project cannot connect to a Git repository owned by a
  Git *organization* — if `new-origin` is owned by an org, the project needs Pro (about the Git
  connection, not the option).
* The same page confirms the install path follows the Root Directory (*"The install path is set by
  the root directory"*), so `npm ci` in `web/vercel.json` runs in `web/` and honours
  `web/package-lock.json`. It also confirms Vercel installs `devDependencies` by default — required
  here, because `tsc` and `vite` are devDependencies; do not enable "exclude devDependencies" or set a
  production-only install for this project.
* `buildCommand` / `outputDirectory` / `framework: vite` / the SPA rewrite and the three cache-header
  rules in `web/vercel.json` are correct as they stand.
* `installCommand` is `npm install`; `npm ci` is stricter and honours the lockfile exactly (§6.4).
* Node: Vercel's documented default in 2026 is **24.x** and the supported set is 24.x/22.x; **pin it
  explicitly**, because `jsdom@30.1.2` (devDependency) declares `^22.22.2 || ^24.15.0 || >=26.0.0`
  and `@supabase/supabase-js@2.118.0` declares `>=22`. `.nvmrc` is *not* an override for Vercel's
  build version — use `engines.node` in `web/package.json` or the dashboard setting (§6.4).

**3.4 Production environment variables needed at build time.**
Read by the code (`import.meta.env.VITE_*`, Vite inlines them at build time):

| Variable | Needed for launch | Notes |
|---|---|---|
| `VITE_SUPABASE_URL` | **yes** | `web/src/lib/supabaseClient.ts:18`; without it the Join/waitlist path degrades (it reports the missing variable rather than crashing) |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | **yes** | `supabaseClient.ts:19` — publishable key only; never a service key |
| `VITE_SPOTER_V2_URL` | **yes, for recognition to work** | currently unset → the app fetches same-origin `/spoter_v2_model.onnx`, which will not exist (§5) |
| `VITE_SPOTER_PILOT_URL` | optional | fallback/pilot graph, same mechanism |
| `VITE_CONTACT_EMAIL` | recommended | `.env.example:10`; empty means the contact affordance has no address |
| `VITE_AVATAR_GLB_URL` | **leave unset** | the GLB is committed and served same-origin |
| `VITE_MEDIAPIPE_*` (5), `VITE_ORT_WASM_PROXY` | optional | all have working same-origin defaults (`.env.example:37-45`) |

No secret belongs in `web/`; the two Supabase values are public-by-design client values, but they
still belong in the Vercel project environment, not in a committed file.

---

## 4. Batch B revalidation — the list is **163** paths, not 165

**Count (MEASURED, parsed from `docs/migration/batch-b-manifest-2026-10-16.txt` revision 2):**

| Section | Paths | Header agrees |
|---|---|---|
| 1a configuration | 17 | ✔ |
| 1b application source | 139 | ✔ |
| 1c synthetic fixtures | 7 | ✔ |
| **Batch B total** | **163** | ✔ |
| 2 Batch C candidates | 340 | ✔ |
| 3 excluded scratch | 8 | ✔ |
| 4 preserved owner changes | 4 | ✔ (none leaks into Batch B) |
| 6 local-only, not committed | 28 | ✔ |

**Where 165 comes from.** Revision 1 of the manifest carried 165 application paths before the
owner-approved fixture fix and the configuration fold; revision 2 states 163 and is internally
consistent (17 + 139 + 7). The task text's "165" is the stale figure. **163 is the reconciled count**
and the exact list is regenerated at `docs/migration/batch-b-staging-list-2026-10-16.txt`.

**Checks performed on all 163 (MEASURED):**

| Check | Result |
|---|---|
| exists on disk | 163/163 |
| duplicated entry | none |
| git-ignored (would be silently skipped by `git add`) | **0/163** — including the six negation-guarded paths (production GLB, five fixtures), confirmed with `git check-ignore -q --no-index` → *not ignored* |
| already tracked (would be a no-op) | 0/163 |
| listed as untracked-and-not-ignored by `git ls-files --others --exclude-standard` | 163/163 (i.e. exactly the staging set) |
| overlaps section 3 (scratch) or section 4 (owner changes) | 0 |
| contains a non-production `.glb`, any `.onnx`/`.onnx.data`, `node_modules`, `dist`, a local dataset, a `*.npy`, a venv | 0 (only exception: the production GLB and the 5 trackable fixture files, both intended) |
| measured payload size | **131.8 MiB** (138,239,654 B); largest 5 = 47.40 + 27.00 + 25.54 + 15.98 + 13.58 MiB |

**Preserved as required:** the frozen vocabulary and the recognition pipeline are all present — either
in Batch B (`web/src/lib/{vocab,featureVector,normalize,sequenceBuffer,temporalSampler,
temporalStabilizer,recognitionGate,signToText,inference,modelRegistry,mediapipe,contracts}.ts`,
`ai/sign-recognition/data/pilot_class_mapping.json`) or already committed
(`docs/ai-ml/ASL_100_VOCABULARY_FROZEN.md`, `docs/ai-ml/asl100_vocabulary.json`,
`ai/sign-recognition/config/asl100_asl_citizen_mapping.json`,
`ai/sign-recognition/data/class_index_mapping.json`). The production avatar GLB is in Batch B. The
four owner changes remain modified-and-unstaged (`app/App.tsx`, `app/package.json`,
`ai/sign-recognition/training/dataloaders.py`, `docs/architecture/TECHNICAL_ARCHITECTURE.md`) and
none appears in the list.

**One correction to an intermediate finding.** During this audit a *simulation* that copied only the
163 payload paths (omitting the 101 already-tracked files) reported a second `tsc` error,
`TS2307 … class_index_mapping.json`. That was an artefact of the incomplete copy: the file is
already committed. The faithful tree (§0 step 2) does **not** reproduce it. Recorded here so the
distinction between simulation and verification is explicit.

---

## 5. Deployment payload size, and what still blocks a Vercel deployment

**Sizes (MEASURED).**

| Build | `dist` total | files | largest single file |
|---|---|---|---|
| this working tree (every local asset present) | 982.91 MiB | 32 | `spoter_v2_model.onnx.data` 179.02 MiB |
| clone-equivalent tree (tracked + 163 payload) — **this is what Vercel builds from Git** | **158.59 MiB** | **19** | `avatar/SignVox_Female_Competition_Prototype.glb` 47.40 MiB |

Clone-equivalent composition: `onnxruntime/` 82.27 MiB, `avatar/` 47.63 MiB, `assets/` 28.69 MiB
(27.00 MiB of it the bundler-emitted `ort-wasm-simd-threaded.jsep-*.wasm`), `index.html` + favicons
≈ 0.01 MiB.

**Is 158.59 MiB a blocker? No — not by documented limits.** Vercel documents the 100 MB source-upload
cap and 15,000-file cap as **CLI-upload** limits only; for Git-connected builds the docs state there
is *no upper limit on the number of output files* and specify **no total build-output cap and no
per-file cap** for static files. The 47.40 MiB GLB and 27.00 MiB wasm are therefore within documented
limits, and the older "493.8 MiB vs 100 MB" blocker applied to the *CLI* path, not to this one.
(Unchanged and still true: nothing has been deployed, so none of this is yet observed on Vercel.)

**What still blocks a successful Git-based Vercel deployment.**

| # | Blocker | Status / evidence | Fix |
|---|---|---|---|
| **V1** | **`npm run build` fails on a clean clone**: `tsc -b` → 11 × `TS2307 Cannot find module 'three'` from `avatar/controller/*.ts` (+ 1 cascading `TS7006`), so `vite build` never runs | **VERIFIED** in the clone-equivalent tree (§0 step 3). Cause: those nine files resolve `three` only through the gitignored `avatar/node_modules` (present here, absent in a clone — `require.resolve('three', {paths:['…/avatar/controller']})` → `avatar\node_modules\three`). Vercel installs dependencies only in `web/`, which is not an ancestor of `avatar/` | §6.1 — 2 lines in `web/tsconfig.json`. Verified: `tsc -b --force` → exit 0, full build → exit 0 |
| **V2** | **Recognition will 404 in production**: the four ONNX objects are not, and cannot be, in the repo — `spoter_v2_model.onnx.data` (179.02 MiB) and `spoter_pilot.onnx.data` (178.89 MiB) exceed GitHub's 100 MiB hard per-file block, and `*.onnx`/`*.onnx.data` are gitignored (`check-ignore --no-index` → IGNORED) | **VERIFIED** (framework: `.onnx.data` absent from the 158.59 MiB `dist`; runtime URL contract: `inference.ts:90-93` sets `externalData` to `${modelUrl}.data`) | Host the two graph+sidecar pairs at one public R2 prefix (proposal only, per your decision) and set `VITE_SPOTER_V2_URL` / `VITE_SPOTER_PILOT_URL` in the Vercel project. CORS + `Access-Control-Expose-Headers` + Range/206 + sibling naming are required, exactly as `manifest §5` records. The avatar needs nothing (its GLB is committed) |
| **V3** | **Root Directory / outside-root setting** | §3.3 — mandatory, currently undocumented anywhere in the repo (the README does not mention them) | Set both in the Vercel project before the first deploy; no file change needed |
| **V4** | **Unpinned Node** | `web/package.json` has no `engines`; Vercel's default 24.x satisfies every dependency, but a future default shift is unguarded (jsdom 30 already excludes Node 22 < 22.22.2) | §6.4 — add `engines.node` |
| **V5** | `installCommand: npm install` | A lockfile exists and matches; `npm install` may resolve within ranges | §6.4 — `npm ci` |
| **V6** | **Nothing secret is at risk, nothing else blocks** | `npm audit --omit=dev` → 0; the payload contains no `.env`, key or token (`.env.example` carries placeholders only) | — |

**Not a blocker, but 82.10 MiB of the 158.59 MiB `dist` is never fetched at runtime** (DERIVED from
`inference.ts`): `absoluteWasmPaths()` (line 65, pinning the URL at line 69) points the binary at
`/onnxruntime/ort-wasm-simd-threaded.wasm` (13.58 MiB) and the loader to the Vite-inlined
`?url` module, while `public/onnxruntime/` also ships `ort-wasm-simd-threaded.{jsep,asyncify,jspi}.wasm`
(27.00 + 25.54 + 15.98 = 68.52 MiB) and the bundler additionally emits
`assets/ort-wasm-simd-threaded.jsep-*.wasm` (27.00 MiB). Trimming those would take `dist` to
≈ 76.5 MiB and the repo payload from 131.8 MiB to ≈ 63.3 MiB. **Deliberately not proposed as part of
the smallest safe path**: it changes Batch B, and the claim "ORT never requests the other three
variants" is only reasoned from the configured `executionProviders: ['wasm']`, not yet observed in a
browser. If you want it, it is a separate, testable task.

---

## 6. Exact file changes

**APPLIED 2026-10-16 under owner approval** (§6a has the verification). All four files are inside
Batch B and remain unstaged. No other file was touched; the four protected owner files were confirmed
byte-identical by SHA-256 before and after (see §6a).

**6.1 `web/tsconfig.json` — fixes V1. Verified in the clone-equivalent tree (build exit 0).**

```diff
       "useDefineForClassFields": true,
+      "baseUrl": ".",
+      // `avatar/controller/*.ts` (outside web/, included via the Vercel
+      // "include source files outside the Root Directory" setting) imports `three`.
+      // Those files resolved it through the gitignored avatar/node_modules, which a
+      // clean clone does not have, so `tsc -b` failed there. Map the bare specifier
+      // to the declaration package that IS installed in web/node_modules.
+      "paths": {
+        "three": ["./node_modules/@types/three"],
+        "three/*": ["./node_modules/@types/three/*", "./node_modules/three/*"]
+      },
       "lib": ["DOM", "DOM.Iterable", "ES2022"],
```

Verified effect: `npx tsc -b --force` → exit 0 (was 12 errors); `npm run build` → exit 0.
The bundler is untouched: `vite.config.ts` already aliases `three` to `web/node_modules/three`, and
`vite build` alone passed before this change.

**6.3 `web/.vercelignore` — duplicate removed, scope and the shipped PNGs documented.**

```diff
-public/avatar/SignVox_Female_v5_HELLO.glb      (second, duplicate occurrence removed)
```

plus a rewritten header comment that records the CLI-only scope, that the nine GLBs are already
absent from a Git-built deployment, and that `public/avatar/test_{front,side,hand}.png` (0.23 MiB) are
in Batch B and **do** ship in `dist/avatar/` while no application code, test or benchmark reads them
(`tools/test_neutral_pose.py` and `tools/render_hands.py` write their renders to
`C:\Users\PC\.gemini\...`, a different directory). They were deliberately **not** added to the
exclusion list, so no asset behaviour changes.

**6.4 `web/package.json` — pin Node, tighten the install (V4, V5, optional):**

```diff
   "version": "0.1.0",
   "type": "module",
+  "engines": { "node": "24.x" },
```
and `web/vercel.json`:
```diff
-  "installCommand": "npm install",
+  "installCommand": "npm ci",
```

**6.5 `app/` — no change; see §2 for the recommendation to defer the 35 `app/*` paths.**

**Not proposed:** touching the four owner-changed files, upgrading Vite/Vitest for the dev-only
advisories, deleting `web/.vercelignore`, moving or deleting any GLB, creating an R2 bucket or
uploading anything.

## 6b. Exact staging list

`docs/migration/batch-b-staging-list-2026-10-16.txt` — **163 paths**, 17 + 139 + 7, 131.8 MiB,
generated from the reconciled manifest and re-validated against disk and git (§4). Nothing is
staged; `git status` is unchanged from the start of this task (102 untracked, 8 modified).

## 6a. Applied changes and their verification (2026-10-16)

Applied, in this order, with nothing staged:

| File | Change |
|---|---|
| `web/tsconfig.json` | `baseUrl: "."` + `paths` for `three` / `three/*` and an explanatory comment (§6.1) |
| `web/package.json` | `"engines": { "node": "24.x" }` — no dependency touched (§6.4) |
| `web/vercel.json` | `installCommand`: `npm install` → `npm ci` (§6.4) |
| `web/.vercelignore` | duplicate `SignVox_Female_v5_HELLO.glb` line removed; header comment corrected (§6.3) |

Verification (all MEASURED):

| Check | Result |
|---|---|
| `npx tsc -b --force` in `web/` | **exit 0** (was 12 errors in a clone tree) |
| `npm run build` in `web/` (production build) | **exit 0**, 1m55s; `dist` = 982.91 MiB / 32 files (unchanged — local assets are all present, and the change is type-resolution only) |
| `npm run build` in a **clone-equivalent tree** (101 tracked + 163 payload paths, deps installed only under `web/`) | **exit 0**, 59.7s (was **exit 1**); `dist` = **158.59 MiB / 19 files** |
| `sha256sum -c` against hashes taken before the edits, for the four protected files | all four **OK** (byte-for-byte unchanged) |
| `git diff --cached --name-only` | empty — nothing staged; `git status` still 104 untracked / 8 modified |

## 7. Not claimed

* No deployment has been performed, preview or production; no Vercel project, root directory, Node
  version or environment variable has been configured.
* The 158.59 MiB `dist` figure comes from a local copy of the repository, not from Vercel's builder:
  Vercel's own Node/ npm version and its file-system layout are not reproduced, only the file set and
  the dependency install location.
* The ONNX-over-HTTP path (remote `VITE_SPOTER_*_URL`, CORS, Range/206, `${modelUrl}.data` sibling
  resolution) has not been exercised against any host, including a local one.
* The recognition path itself was not re-validated; this audit covers build, packaging, hosting and
  repository correctness only.
* Test-suite results quoted in the manifest (§7) were not re-run in this pass.
