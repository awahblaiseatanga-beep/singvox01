# SignVox — Safe migration to the new canonical GitHub repository

**Date:** 2026-10-16
**Local checkout:** `D:/Singvox/Singvox` · branch `main` · baseline `aeed61c6b7796b0201326be8c715861849142645`
**Destination:** `https://github.com/awahblaiseatanga-beep/Singvox.git`
**Status of this document:** plan + evidence. **Nothing has been staged, committed, pushed, deployed, or changed on any remote.** The only files this task created or edited are listed in §11.

> This document is the rationale referenced by the header comment of the new
> `.gitignore` rules. It supersedes §9 of `docs/PRE_DEPLOYMENT_AUDIT_2026-10-16.md`
> where the two disagree, and it corrects three findings of that audit that are now
> stale (see §10).

---

## 1. Executive summary

1. **The destination repository exists, is empty, and is now PRIVATE** (re-verified 2026-10-16 after the owner changed its visibility). It was created `2026-10-16T02:45:34Z`, `size: 0`, default branch `main`, and `git ls-remote` returns **zero** refs. It is therefore safe to receive the existing history as an ordinary new-branch push — no force, no rewrite (§7, B1 — resolved).
2. **This machine can now push to the destination** (re-verified 2026-10-16). The `gh` CLI is still signed in only as the old account `abonkweawah-png`, which now receives **404** on the private repository, but Windows Credential Manager holds a working credential for the new owner (`git:https://awahblaiseatanga-beep@github.com`). `git push --dry-run new-origin main` succeeds both pinned and unpinned — `* [new branch] main -> main`, exit 0 — and wrote nothing (§7, B2 — resolved). The earlier `manager` hang was that helper waiting to be told which of the two stored accounts to use.
3. **The real risk was in the working tree, not the remote.** A naive `git add -A` with the pre-existing `.gitignore` would have attempted to stage every component the pre-deployment audit warned about — **1,839 generated `.npy` feature arrays (402 MiB)**, **1,970 MiB of training checkpoints (11 files)**, **512.1 MiB of avatar GLBs**, **381 MiB of Blender exports**, 216 MiB of `.blend`/`.blend1` sources, 88 MiB of third-party `.fbx`, **359.7 MiB of model weights**, the third-party video dataset (2.08 GiB) and a ~40,000-file Python virtualenv — i.e. the bulk of a 10.9 GiB checkout. The `.gitignore` was fixed **before anything was staged** (§3).
4. **After the fix, the payload that carries the project is 144,223,874 bytes (137.54 MiB) over 504 pre-existing new files plus 6 modified tracked files — 510 entries.** The 3 documents this task itself created add a further ~70 KiB, bringing the full staging list to **513 entries**; because those three files include this one, their exact bytes change on every edit, so the size is quoted as the stable 510-entry subtotal (§4.1). Everything is far below GitHub's 100 MiB per-file hard block; the single largest file is the 47.4 MiB production avatar GLB and only five files exceed 10 MiB (§4).
5. **The application source is complete and verified in place:** `npm run build` exit 0, `npx tsc -b --force` exit 0, `npx vitest run` 30 files / 198 tests passed exit 0 (§6). All 16 cross-directory imports that reach outside `web/` resolve to files that are either already tracked or inside the migration payload (§5.4).
6. **The two ~179 MiB ONNX external-data sidecars cannot enter Git and cannot be CLI-uploaded to Vercel.** They must be hosted externally and referenced through the existing `VITE_SPOTER_V2_URL` / `VITE_SPOTER_PILOT_URL` overrides, which are implemented and verified in code (§8).
7. **A recoverable backup exists outside the repository**: history bundle, 601-file source archive, the pre-change `.gitignore`, a git-state snapshot, and SHA-256 digests of the 28 large files that deliberately stay local (§2.5).
8. **The baseline history is now pushed** (2026-10-16, owner-approved). `git push new-origin main` returned `* [new branch] main -> main`, exit 0; remote `refs/heads/main` is `aeed61c6b7796b0201326be8c715861849142645`, identical to local HEAD — and because Git objects are content-addressed, identical bytes. No force, no rewrite. **Batches A/B/C remain uncommitted and nothing is staged** (§2.3).

**This plan stops before staging. The private destination repository and working write credentials for `awahblaiseatanga-beep` are now in place (§7, B1/B2 resolved); the only remaining gate is the owner's explicit approval to push (§12).**

---

## 2. Current state (measured)

### 2.1 Git

| Item | Value |
|---|---|
| `git rev-parse HEAD` | `aeed61c6b7796b0201326be8c715861849142645` |
| Branch | `main` |
| Commits in history | **1** (`git rev-list --count HEAD`) |
| Tracked files | **98** |
| Stashes | none |
| Submodules | none (no `.gitmodules`) |
| Modified tracked files | **6** |
| New (untracked, non-ignored) files | **503** before this task's docs; see §4 |
| Working-tree entries reported by `git status --porcelain` | 107 (6 modified + 101 untracked entries; Git collapses untracked directories) |

Modified tracked files (all pre-existing local work, preserved untouched):

```
 M .env.example
 M .gitignore                       <- this task added hygiene rules (§3)
 M ai/sign-recognition/training/dataloaders.py
 M app/App.tsx
 M app/package.json
 M docs/architecture/TECHNICAL_ARCHITECTURE.md
```

### 2.2 Remotes (all three now present; the two pre-existing ones are untouched)

```
origin       https://github.com/abonkweawah-png/SignVox-Avatar-Lab.git   (pre-existing, untouched)
old-origin   https://github.com/abonkweawah-png/Singvox.git              (pre-existing, untouched, empty)
new-origin   https://github.com/awahblaiseatanga-beep/Singvox.git        (added by this task, not a replacement)
```

`origin` and `old-origin` URLs, refspecs and `branch.main.remote` were not modified. `new-origin` was added rather than replacing anything, exactly as requested.

### 2.3 Destination repository (read-only checks)

| Check | Result |
|---|---|
| `git ls-remote …` before the first push | exit 0, **0 refs** → empty repository |
| Visibility | **private** — anonymous `GET /repos/awahblaiseatanga-beep/Singvox` now returns **404** (it returned `200` while public) |
| Write access | `git push --dry-run new-origin main` → `* [new branch] main -> main`, exit 0. The `gh` CLI is signed in only as `abonkweawah-png`, which now gets `404`; the working credential is `git:https://awahblaiseatanga-beep@github.com` in Windows Credential Manager |
| Authenticated account (gh CLI) | `abonkweawah-png` (keyring; scopes `gist`, `read:org`, `repo`, `workflow`) |

**Post-push state (2026-10-16).** The destination was empty, so the "if it contains commits or files, stop and report" condition never triggered; it now holds exactly one commit — the baseline — and `refs/heads/main` matches local HEAD. Both original blockers, visibility and write access, are resolved (§7, B1/B2). **Nothing is staged; batches A/B/C are uncommitted.**

### 2.4 Local size inventory (the reason for §3)

| Location | Size | Content | Git decision |
|---|---|---|---|
| `ai/sign-recognition/checkpoints/` | **1,970 MiB (1.92 GiB)**, 11 files, ~188 MB each | SPOTER experiment `.pt` checkpoints | excluded (`*.pt`) |
| `data/` (repository root only) | **2.08 GiB**, 1,845 files | downloaded third-party How2Sign validation video (`continuous_how2sign_val`, `sandbox_continuous`) | excluded (`/data/`, §3.1.1) |
| `experiments/continuous-asl/**/features/` | **402 MiB**, 1,839 files | generated landmark `.npy` feature arrays | excluded (`*.npy`) |
| `web/public/` | **955 MiB** | 2 graphs + 2 `.onnx.data` (359.7 MiB), 10 GLBs (512.1 MiB, of which **464.7 MiB** is unreferenced), 4 ort `.wasm` (82.1 MiB) | split — see §8 |
| `avatar/` | **685 MiB** excluding `node_modules/` = 381 MiB `exports/` + 216 MiB `.blend`/`.blend1` + 88 MiB `.fbx` | Blender sources, two third-party FBX characters, exported GLB/blend | excluded (`*.blend`, `*.blend1`, `*.fbx`, `*.glb`, `node_modules/`) |
| `.venv_pilot/` | ~40,000 files (incl. a 292 MiB native DLL, per the audit) | Python virtualenv | excluded (`.venv*/`) |
| `web/node_modules_old/` | stale install | — | excluded (`node_modules_old/`) |
| `web/dist/` | **983 MB** | build output | excluded (`dist/`) |

### 2.5 Backup (Phase 1.4) — created before anything else was touched

Location: **`D:/Singvox/_signvox_migration_backup_2026-10-16/`** (outside the repository; the repository itself was never `git add`-ed, reset, cleaned or stashed).

| Artifact | Size | Purpose |
|---|---|---|
| `signvox-history-all.bundle` | 228,274 B | `git bundle create … --all` — the complete local history in one restorable file (`git clone <file>` / `git fetch <file>`) |
| `signvox-source-2026-10-16.tar.gz` | 72,828,403 B | archive of the 601 files that constitute the migration payload (all 98 tracked files + all 503 new files); `tar -tzf … \| wc -l` = 601 |
| `source-file-list.txt` | 27,877 B | the exact list archived (601 paths) |
| `gitignore.before-2026-10-16.txt` | 1,090 B | pre-change `.gitignore`, so the hygiene edit can be reverted byte-for-byte |
| `git-state-snapshot.txt` | 3,907 B | captured `git status`, remotes, HEAD and log at backup time |
| `large-asset-sha256.txt` | 28 digests | SHA-256 of every large file that is deliberately **not** archived (checkpoints, model graphs and `.onnx.data`, `.blend`s, `.fbx`s) so their identity is provable later |

Disk headroom at backup time: 80 GB free on `D:`.
**Not** copied into the archive (by design): `.venv_pilot/`, `node_modules*`, `data/`, `dist/`, and the large binaries listed in `large-asset-sha256.txt` — these remain in place on disk and are only excluded from Git.

---

## 3. `.gitignore` hygiene (Phase 2) — proposed change, already applied

Rules were added **before** any staging. `git check-ignore` was used to confirm every rule, never a `git add -A`.

### 3.1 What was added (complete diff of the new block)

```diff
+# ===========================================================================
+# Migration hygiene (2026-10-16) — added while preparing the move to the new
+# canonical repository. Nothing here deletes or moves a local file; these rules
+# only keep local-only content out of Git. Rationale for every rule is recorded
+# in docs/REPOSITORY_MIGRATION_2026-10-16.md.
+# ===========================================================================
+
+# Python virtual environments of any name/variant (includes .venv_pilot)
+.venv*/
+venv*/
+
+# Locally downloaded third-party datasets (How2Sign validation video, sandboxes).
+# Redistribution is not permitted and the size is unmanageable in Git.
+# Anchored to the repository root on purpose: an unanchored `data/` also
+# matched ai/sign-recognition/data/ (corrected in the Batch A review, §3.1.1)
+/data/
+
+# Stale installs, local backups, build metadata, Vercel link state
+node_modules_old/
+*.backup
+*.tsbuildinfo
+.vercel/
+
+# Local agent state, not part of the shipped project
+.agents/
+
+# Blender/FBX sources and every exported avatar EXCEPT the single production GLB
+# the application loads (mirrors the keep-list in web/.vercelignore)
+*.blend
+*.blend1
+*.fbx
+*.glb
+!web/public/avatar/SignVox_Female_Competition_Prototype.glb
+
+# ONNX external weight sidecars (two ~179 MiB files; GitHub hard-blocks files
+# over 100 MiB). Host them externally and point VITE_SPOTER_V2_URL /
+# VITE_SPOTER_PILOT_URL at the host: the app fetches the graph from that URL and
+# its weights from `${modelUrl}.data`, so the two must stay side by side.
+*.onnx.data
+*.ckpt
+
+# Scratch diagnostics
+tmp_*
+
+# Generated intermediate arrays (landmark .npy dumps produced by the extraction
+# scripts, e.g. experiments/continuous-asl/**/features/). Regenerable, hundreds
+# of MiB. Source scripts and their JSON/CSV metrics stay tracked.
+*.npy
+
+# Gradle/Android build state
+.gradle/
+*.apk
+*.aab
```

The pre-existing rules (`*.onnx`, `*.pt`, `*.pth`, `*.h5`, `*.tflite`, `*.pb`, `*.task`, `*.keystore`, `.env`, `.env.*` with `!.env.example`, `dist/`, `__pycache__/`, dataset directories, `tools/audit_out.txt` via `*.out`, …) are unchanged.

### 3.1.1 Batch A review corrections (2026-10-16)

A `git check-ignore` pass over every payload path **and** every real local-only path found one over-broad rule and two gaps. All three are fixed; **nothing was removed**, so every pre-existing decision is preserved.

| Change | Why | Evidence |
|---|---|---|
| `data/` → **`/data/`** | The unanchored form also matched `ai/sign-recognition/data/`, so `pilot_class_mapping.json` — a class map Batch B requires — was silently un-stageable | `git check-ignore -v ai/sign-recognition/data/pilot_class_mapping.json` matched `.gitignore:96:data/` before and nothing after; the stageable set grew by exactly that one file (506 → 507 new files) |
| Added `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `id_ed25519*`, `.npmrc` | Phase 2 asks for credentials and private keys to be excluded. No such file exists in this checkout, so the rules are defensive | each new rule verified to fire; **zero** tracked files and zero payload paths match any of them |
| Added `.eslintcache`, `.vite/` | Tool caches | verified to fire; no payload path matches |

`.env.example` was extended in the same review: it documented only 3 of the 10 `VITE_*` variables the app reads. The 7 missing ones (the `VITE_SPOTER_*`, `VITE_AVATAR_GLB_URL`, `VITE_MEDIAPIPE_*` and `VITE_ORT_WASM_PROXY` overrides, §8) are now documented **commented-out** with their built-in defaults, because the MediaPipe options are read with `??` and an empty assignment would replace the default rather than fall back to it. No application behaviour changes.

### 3.2 Verification with `git check-ignore` (after the change)

| Path | Before | After |
|---|---|---|
| `.venv_pilot/pyvenv.cfg` | NOT ignored | **IGNORED** |
| `data/continuous_how2sign_val/videos` | NOT ignored | **IGNORED** |
| `web/node_modules_old/foo.js` | NOT ignored | **IGNORED** |
| `web/package-lock.json.backup` | NOT ignored | **IGNORED** |
| `web/tsconfig.tsbuildinfo` | NOT ignored | **IGNORED** |
| `web/public/spoter_v2_model.onnx.data` | NOT ignored | **IGNORED** |
| `web/public/spoter_pilot.onnx.data` | NOT ignored | **IGNORED** |
| `web/public/avatar/SignVox_Female_v5_HELLO.glb` | NOT ignored | **IGNORED** |
| `avatar/exports/SignVox_Female.glb` | NOT ignored | **IGNORED** |
| `avatar/models/Ch41_nonPBR.fbx` | NOT ignored | **IGNORED** |
| `avatar/SignVox_Female_Inspection.blend` | NOT ignored | **IGNORED** |
| `experiments/continuous-asl/phase_2c_26/features/*.npy` | NOT ignored | **IGNORED** |
| `app/android/.gradle/…/fileHashes.bin` | NOT ignored | **IGNORED** |
| `tmp_check_onnx.py`, `tools/tmp_dist_audit.py` | NOT ignored (only `tmp/`) | **IGNORED** |
| `web/.env.local` | IGNORED (`.gitignore:3`) | IGNORED |
| `ai/sign-recognition/data/pilot_class_mapping.json` | IGNORED (over-broad `data/`) | **tracked-eligible (corrected — §3.1.1)** |
| `web/public/avatar/SignVox_Female_Competition_Prototype.glb` | NOT ignored | **tracked-eligible (intended)** |
| `web/public/onnxruntime/ort-wasm-simd-threaded.wasm` | NOT ignored | **tracked-eligible (intended)** |
| `app/android/gradle/wrapper/gradle-wrapper.jar` | NOT ignored | **tracked-eligible (intended)** |
| `avatar/controller/AvatarController.ts` | NOT ignored | **tracked-eligible (intended)** |

Effect of the fix: the stageable set fell from `git status` territory containing ~3.9 GiB of unstageable content to **503 files / 137.5 MiB**, and the 1,839 `.npy` arrays, the virtualenv and the dataset are no longer stageable at all.

### 3.3 Deliberate non-decisions (kept local, not ignored, owner's call)

`find_data.py`, `inspect_ch41.py`, `inspect_fbx.py`, `inspect_glb.py`, `inspect_onnx.py`, `check_hierarchy.py` at the repository root and `tools/extracted_guide.txt` (a generated PDF text dump) are **one-off diagnostics that are neither ignored nor part of any proposed commit batch**. They are listed in §4.5 so the owner can either commit them deliberately, move them, or ignore them.

---

## 4. The complete proposed payload (Phase 4)

Counts and sizes below are measured (`git ls-files --others --exclude-standard`, `ls -l`, `awk`), not estimated.

### 4.1 Totals

| Metric | Value |
|---|---|
| New files | **507** = 504 pre-existing + the 3 documents created by this task (§11) |
| Payload bytes — 504 pre-existing new files **and** the 6 modified tracked files (510 entries) | **144,223,874 B = 137.54 MiB** |
| Plus the 3 self-describing documents created by this task | ≈70 KiB — recursive: grows with every edit to this file, so the 510-entry subtotal above is the authoritative figure |
| Full staging list | **513 entries** |
| Modified tracked files | 6 |
| Largest single file | **47.40 MiB** — `web/public/avatar/SignVox_Female_Competition_Prototype.glb` (< GitHub's 50 MiB warning, well under the 100 MiB block) |
| Files ≥ 50 MiB | **0** |
| Files ≥ 10 MiB | **5** (the GLB and the four ort `.wasm` variants) |

### 4.2 Bytes by extension (top of the table)

| Bytes | Files | Extension |
|---:|---:|---|
| 82.10 MiB | 4 | `.wasm` (onnxruntime-web runtimes) |
| 47.40 MiB | 1 | `.glb` (production avatar) |
| 3.43 MiB | 80 | `.json` |
| 0.88 MiB | 111 | `.md` |
| 0.84 MiB | 2 | `.mp4` (bench fixtures) |
| 0.75 MiB | 149 | `.py` |
| 0.75 MiB | 6 | `.csv` |
| 0.36 MiB | 20 | `.mjs` |
| 0.35 MiB | 66 | `.ts` |
| + `.tsx`, `.png`, `.html`, `.sql`, `.kt`, `.gradle`, `.jar`, `.ipynb`, `.bin`, `.css`, `.txt`, `.js`, `.xml`, `.properties` | | remainder ≈ 0.2 MiB |

### 4.3 Bytes by area

| Bytes | Files | Area |
|---:|---:|---|
| 129.91 MiB | 14 | `web/public/` (production GLB + 4 ort wasm runtimes + favicons + bench screenshots) |
| 1.70 MiB | 88 | `experiments/continuous-asl/` (scripts, configs, JSON/CSV metrics) |
| 1.40 MiB | 12 | `experiments/baseline-79-audit/` |
| 0.86 MiB | 3 | `web/bench/` (benchmark harness + 2 clips) |
| 0.81 MiB | 30 | `experiments/spoter_v3/` |
| 0.63 MiB | 68 | `web/src/` (application source) |
| 0.58 MiB | 62 | `docs/research/` |
| 0.52 MiB | 45 | `experiments/isolated-asl-benchmark/` |
| 0.31 MiB | 19 | `docs/ai-ml/` |
| 0.16 MiB | 27 | `app/android/` |
| remainder | | `docs/*`, `avatar/controller/`, `ai/`, `supabase/`, `web/tests/`, `web/*.mjs`, `web/package-lock.json` |

The **exact, complete, line-by-line file list** is `docs/migration/planned-files-2026-10-16.txt`: one repository-relative path per line, sorted, machine-readable, **513 entries = the 507 new files plus the 6 modified tracked files**. It includes itself.

### 4.4 Proposed commit batches (Phase 4.1–4.3)

Batches are ordered so that each one is independently reviewable and the repository is never left in a state where a documented command fails. **None of these is staged yet.**

**Batch A — repository hygiene and safe configuration templates**
`.gitignore` (modified) · `.env.example` (modified) · `web/.vercelignore` · `web/vercel.json` · `web/tsconfig.json` · `web/package.json` · `web/package-lock.json` · `web/vite.config.ts` · `web/index.html` · `app/package.json` (modified) · `app/.eslintrc.js` · `app/.prettierrc.js` · `app/app.json` · `app/babel.config.js` · `app/index.js` · `app/metro.config.js` · `app/tsconfig.json` · `app/scripts/` · `avatar/package.json` · `avatar/package-lock.json` · `docs/migration/` (manifest + asset digests) · `docs/REPOSITORY_MIGRATION_2026-10-16.md`
*Why first:* it establishes what may enter Git, and ships the configuration templates (including the `.env.example` contract) before any source lands.

**Batch B — application source, avatar controller, model pipeline, required class map**
`web/src/**` (application, `lib/`, `engine/`, `components/`, `pages/`, 37 `tests/`, `onnxruntime/` loaders) · `web/public/**` (production GLB + ort runtimes + favicons) · `web/bench/**` · `web/tests/**` · `web/*.mjs`, `web/*.cjs`, `web/*.ts`, `web/verify_assets.js`, `web/build-ico.mjs` · `avatar/controller/*.ts` (9 files, imported by the app) · `ai/sign-recognition/{models,preprocessing,training,data}/*` new files (`export_to_onnx.py`, `train_pilot_spoter.py`, `pilot_class_mapping.json`, `spoter_pilot_config.json`, `spoter_experiment_05b_scalars.json`) · `ai/sign-recognition/training/dataloaders.py` (modified) · `app/App.tsx` (modified) · `app/android/**` · `app/utils/`
*Why second:* this is the deployable application plus everything it imports. Verified in §5.4 — no import target is missing. The frozen ASL-100 vocabulary, the SPOTER V2 feature contract (60 × 366), normalization, class mapping, temporal sampler and latency profiler are all carried unchanged.

> **Batch B checklist — ignored model artifacts (carry-forward from Batch A).**
> `web/public/spoter_v2_model.onnx`, `web/public/spoter_pilot.onnx` and their `.data` sidecars are **not** in the payload: the pre-existing `*.onnx` rule and the new `*.onnx.data` rule (§3.1) exclude them, and the two ~179 MiB sidecars would exceed GitHub's 100 MiB per-file block in any case. Batch B must therefore:
> 1. keep `VITE_SPOTER_V2_URL` / `VITE_SPOTER_PILOT_URL` as the **only** runtime path for the graphs and their sidecars (§8) — they are documented, commented-out, in `.env.example` (§3.1.1);
> 2. confirm the production GLB `web/public/avatar/SignVox_Female_Competition_Prototype.glb` **is** included — it is the one negation under `*.glb` and the app's default avatar;
> 3. **not** silently re-enable `*.onnx`: committing a graph without its external-data sidecar still cannot run (`inference.ts` derives the sidecar as `${modelUrl}.data`), so the graph and weights must stay side by side on the chosen host.

**Batch C — documentation, tests, migrations, deployment configuration**
`docs/**` (all new reports: launch, recovery audit, speed optimisation, pre-deployment audit, `ai-ml/`, `architecture/`, `avatar/`, `blender/`, `competition/`, `decisions/`, `research/`, `testing/`) · `supabase/migrations/20261016120000_create_waitlist_signups.sql` · `supabase/tests/waitlist_signups_rls_test.sql` · `docs/architecture/TECHNICAL_ARCHITECTURE.md` (modified)
*Why third:* documentation and the (unapplied) Supabase migration describe the code that batch B lands.

`tools/**` (50 files) and `experiments/**` (222 files) are distributed across batches B and C by file type — the diagnostic and rig-authoring scripts travel with the model pipeline, the phase reports with the documentation. The only paths excluded from every batch are the six root scratch files and `tools/extracted_guide.txt` (§3.3, §4.5).

### 4.5 Left untracked by design (owner decision, nothing was deleted)

| Path | Why |
|---|---|
| `find_data.py`, `inspect_ch41.py`, `inspect_fbx.py`, `inspect_glb.py`, `inspect_onnx.py`, `check_hierarchy.py` | one-off diagnostics at the repository root |
| `tools/extracted_guide.txt` | generated text dump extracted from a PDF |

Recommended outcomes, in preference order: (a) commit them deliberately if they document a real procedure, or (b) add them to `.gitignore`. They are **not** in the proposed payload either way.

---

## 5. Verification (Phase 5)

### 5.1 Commands run, from `web/`

| Command | Result | Evidence |
|---|---|---|
| `npm run build` (i.e. `tsc -b && vite build`) | **exit 0** | `✓ 121 modules transformed`, `dist/assets/index-D3Faw0yY.js 1,717.44 kB │ gzip: 467.76 kB`, `dist/assets/index-DtwNF64Q.css 23.38 kB`, `✓ built in 1m 60s`; only the standard chunk-size advisory |
| `npx tsc -b --force` | **exit 0** | no diagnostics |
| `npx vitest run` | **exit 0** | `Test Files 30 passed (30)`, `Tests 198 passed (198)`, duration 146.00 s |

The suite count grew from the 29 files / 164 tests recorded in the pre-deployment audit because the waitlist/Supabase work (`web/src/tests/waitlistFlow.test.ts`, 34 tests) has landed since. Two stderr blocks in the log are **intentional negative-path assertions**, not failures: `speech.test.ts` > "errors inside utterance/speak loop passively fail without breaking DOM" (`SpeechSynthesis API failed: Error: Driver unavailable`) and the deliberate double-submit assertions in `baseline_threshold_eval.test.ts`. Exit status is 0 for both the run and every test file.

### 5.2 Nothing in the payload is a secret

Method: filename matching plus content pattern matching over the 486 non-binary files in the payload (the 17 binaries — `.glb`, `.wasm`, `.png`, `.ico`, `.mp4`, `.jar` — were excluded from content scanning). The scanner was validated with two positive controls (`import` and `SUPABASE`), which matched as expected, so a silent no-op run is excluded. **Only counts and file names are reported here; no value is printed anywhere in this document or in any artifact it created.**

| Pattern | Hits |
|---|---|
| `-----BEGIN … PRIVATE KEY-----` | **0** |
| AWS access key id (`AKIA…`) | **0** |
| GitHub token (`ghp_…`, `gho_…`, …) | **0** |
| Slack token (`xox…`) | **0** |
| OpenAI-style key (`sk-…`) | **0** |
| Google API key (`AIza…`) | **0** |
| JWT literal (`eyJ…`) | **0** |
| `postgres://`/`postgresql://` URI | **0** |
| assigned secret-looking literal (`api_key = "…"` etc.) | **0** |
| secret env assignment (`VERCEL_TOKEN=`, `ACCESS_KEY_ID=`…) | 1 — `docs/LAUNCH_REPORT_2026-10-15.md:123` is the instruction *"`npx vercel login` (or export `VERCEL_TOKEN=…`)"* — a **placeholder in prose, no value** |
| `service_role` / `sb_secret_` / `sbp_` | 5 files, **all defensive**: `.env.example` warns such a key must never appear; `docs/SUPABASE_WAITLIST_SETUP.md` documents the refusal; `web/src/lib/supabaseClient.ts` contains the validation that rejects the `sb_secret_` prefix and any JWT whose `role` is `service_role`; `web/src/tests/waitlistFlow.test.ts` asserts that refusal against a dummy `do_not_ship`-style fixture |

Filenames flagged as "secret-ish" were only three ML `tokenizer.py`/`tokenizer.json` files — false positives.

`web/.env.local` (present since 2026-10-16 02:09, 9 lines, 7 of them comments) is **ignored** by `.gitignore:3` (`.env.*`) and **untracked**. Variable **names only**: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` — both public-by-design variables that ship in the browser bundle. Shape checks over that file: `sb_secret_` = 0, `eyJ` = 0, `postgres://` = 0; the single `service_role` occurrence is on a **comment** line (verified by counting non-comment matches = 0). No secret is present, and no value from that file was read into this document.

### 5.3 Staged-set checks required by Phase 5

| Check | Result |
|---|---|
| No secret values staged | ✔ §5.2 |
| No `.env*` in the payload (`.env.example` is the only intended exception) | ✔ `(none)` — no `.env*` path in the payload; `.env.example` was already tracked |
| No huge dataset, virtualenv or generated file in the payload | ✔ `data/`, `.venv_pilot/`, `node_modules*`, `dist/`, `*.pt`, `*.onnx.data`, `*.npy`, `*.blend*`, `*.fbx`, non-production `*.glb` all verified ignored |
| No essential source omitted | ✔ §5.4 |
| All referenced files exist | ✔ §5.4 |
| Every payload file fits the Git strategy | ✔ largest 47.40 MiB, zero files ≥ 50 MiB |
| Every payload file fits the deployment strategy | ⚠ the 9 non-production GLBs are *in* `web/public/` and are copied by `vite build` into `dist/` (983 MB output). They are in `.vercelignore` for CLI uploads but that does **not** affect build output — see §8.3 |
| Destination repository private | ✔ re-verified — anonymous API returns `404` (was `200` while public) |

### 5.4 Import completeness — every cross-directory import resolves

`web/src` contains **16 occurrences** of imports that reach outside `web/` (the same 15–16 sites the pre-deployment audit flagged). Each was resolved to a real path using the correct repository-root mapping:

```
OK (already tracked)    ai/sign-recognition/data/class_index_mapping.json
OK (planned new file)   avatar/controller/AnatomicalAnchors.ts
OK (planned new file)   avatar/controller/ArmIKController.ts
OK (planned new file)   avatar/controller/AvatarController.ts
OK (planned new file)   avatar/controller/HandModel.ts
OK (planned new file)   avatar/controller/avatarCapabilities.ts
```

All six targets are inside the payload (or already tracked), so a clone of the destination repository at the tip of batch B can build without the repository layout being changed. **The layout is preserved exactly** — nothing was moved into a repository subdirectory, no dependency was removed, and no fallback behaviour was changed.

---

## 6. Commit / history plan (Phase 6.3–6.4)

1. **History first, unmodified — DONE 2026-10-16.** The destination was empty, so `git push new-origin main` was a plain branch creation carrying the single existing commit `aeed61c6b7796b0201326be8c715861849142645`; remote `refs/heads/main` now matches local HEAD exactly (verified). No force, no rebase, no history rewrite, no `filter-repo`. Nothing in the existing history contains a secret or a large file:
   * the 98 tracked files total **844,023 B (0.80 MiB)**, and the largest is 38.8 KiB (`ai/sign-recognition/training/run_experiment_01.py`) — no binary at all;
   * no `.env*`, no dataset, no checkpoint, no `.onnx`/`.glb` is tracked (all excluded by the pre-existing ignore rules);
   * §5.2 found no secret in the 486 text files of the payload, and the tracked set is a subset of that scan plus the already-scan-safe tracked files.
2. **Then three commits, one per batch**, in the order A → B → C of §4.4. Each commit is self-contained; the message for each will state what landed and what deliberately did not.
3. **Before each commit** the staged set will be re-verified (`git status --short`, `git diff --cached --stat`, and a size check that nothing approaches 100 MiB) and §5.1 re-run for batch B (source changes only; the docs and config batches do not affect the build).
4. **No force-push, ever.** `origin` and `old-origin` are never written to; `old-origin` is an empty repository and can be ignored entirely.

---

## 7. Unresolved blockers — owner action required

| # | Blocker | Evidence | Needed |
|---|---|---|---|
| **B1** | ~~destination is public~~ **RESOLVED 2026-10-16** | anonymous `GET /repos/awahblaiseatanga-beep/Singvox` now returns **404** (was `200` while public); the old account also gets 404 | done — the owner set the repository to **private** |
| **B2** | ~~this machine cannot push~~ **RESOLVED 2026-10-16** | `git push --dry-run new-origin main` → `* [new branch] main -> main`, **exit 0**, pinned and unpinned; credential `git:https://awahblaiseatanga-beep@github.com` present in Windows Credential Manager | done — the owner authenticated as the destination owner; a plain `git push` now works and wrote nothing in dry-run |
| **B3** | The two `.onnx.data` sidecars (357.9 MiB) cannot be committed and cannot be CLI-uploaded | GitHub hard-blocks > 100 MiB per file; the audit measured the Vercel CLI source upload at 493.8 MiB against a documented 100 MB Hobby budget | Choose the host in §8.2 and set the two URL variables; **no code change is required** |
| **B4** | 9 non-production GLBs (**464.7 MiB**, measured) remain in `web/public/avatar/` and are copied into `web/dist` (measured **983 MB** build output) | `web/dist` inventory; `vite build` copies `public/` wholesale | Move them out of `public/` (see §8.3) — noting that `web/src/tests/reproduce_trace.test.ts:24` loads `web/public/avatar/SignVox_Female.glb` from disk and would need its path updated |
| **B5** | Deploy method not yet chosen | The CLI path is blocked by size; a git-based deployment has no documented source-size cap | §8.3 |
| **B6** | `web/.env.local` exists locally with the public Supabase values, and `VITE_CONTACT_EMAIL` is still unset everywhere | §5.2; the pre-deployment audit's §7.5 | Set `VITE_CONTACT_EMAIL` (and the Supabase variables) in the deployment environment, not in Git |

Not a blocker but worth noting: `web/tsconfig.tsbuildinfo` and `web/dist/` are now ignored, so a build leaves no stageable churn.

---

## 8. External asset + deployment plan (Phase 3)

### 8.1 What the application actually needs at runtime

Verified against the code, not assumed:

| Asset | Size | Where the URL comes from | Override |
|---|---|---|---|
| `spoter_v2_model.onnx` (79-class graph) | 121,801 B | `modelRegistry.ts` `BASELINE_MODEL_URL` | `VITE_SPOTER_V2_URL` |
| `spoter_v2_model.onnx.data` | 187,711,488 B (179.0 MiB) | `inference.ts` → `data: \`${modelUrl}.data\`` | follows `VITE_SPOTER_V2_URL` automatically |
| `spoter_pilot.onnx` (3-class graph) | 1,711,205 B | `modelRegistry.ts` `PILOT_MODEL_URL` | `VITE_SPOTER_PILOT_URL` |
| `spoter_pilot.onnx.data` | 187,580,416 B (178.9 MiB) | `inference.ts` → `data: \`${modelUrl}.data\`` | follows `VITE_SPOTER_PILOT_URL` |
| `SignVox_Female_Competition_Prototype.glb` | 49,701,152 B (47.4 MiB) | `useSignVoxEngine.ts` `AVATAR_GLB_URL` | `VITE_AVATAR_GLB_URL` |
| `onnxruntime/ort-wasm-simd-threaded.{mjs,wasm}` | 24,381 B + 14,239,897 B | `inference.ts` (via `?url` import + `/onnxruntime/…wasm`) | **no override — hardcoded paths** |

Defaults keep the current behaviour exactly: every override falls back to the local `/public` path, so a full local checkout works with no environment variables set (this is why the build and tests above pass unchanged).

### 8.2 Where to host the binaries — recommendation

The deciding constraint is **egress**, because one cold visit pulls ~179 MiB.

| Option | Storage / transfer | Verdict |
|---|---|---|
| **Cloudflare R2** *(recommended)* | 10 GB-month storage, **egress free** (not a metered allowance); S3-compatible; object max 4.995 TiB; **CORS configurable**; Range supported. Serve in production from a custom domain — `r2.dev` URLs are documented as development-only with variable rate limits and 429s | Best fit: zero egress worries for a 179 MiB model, and CORS + Range are both documented capabilities. Needs a Cloudflare account and (for production) a domain |
| **Supabase Storage** | Already part of this stack (`@supabase/supabase-js` is a dependency; a public bucket is reachable through RLS); egress on the free plan is metered (~5 GB/month) | No new vendor, but ~28 model downloads/month would exhaust the free allowance and break the demo |
| **Vercel Blob** | Hobby includes 1 GB storage and 10 GB/month Blob data transfer; single Blob up to 5 TB but the **CDN caches only up to 512 MB**; **Hobby cannot buy overages — access stops until the limit resets** | 357.9 MiB fits the 1 GB storage, but a 179 MiB download exhausts 10 GB transfer in ~55 visits with no paid continuation, and the docs did **not** confirm that a public Blob URL sends CORS headers for cross-origin `fetch` |
| **Git LFS** | Free: 2 GB per file but only 10 GiB storage **and 10 GiB bandwidth per month** | ~55 model downloads/month; not viable for a public demo, and it does not solve the Vercel build path |

**Recommended variables once a host is chosen** (values belong in the deployment environment and in `web/.env.local` locally — never in Git):

```
VITE_SPOTER_V2_URL=https://<host>/spoter_v2_model.onnx      # .data must sit beside it
VITE_SPOTER_PILOT_URL=https://<host>/spoter_pilot.onnx      # .data must sit beside it
VITE_AVATAR_GLB_URL=https://<host>/SignVox_Female_Competition_Prototype.glb   # optional
```

Two hosting requirements that follow from the code: (1) the graph and its **`.data` file must share the same base URL**, because the app derives the sidecar as `${modelUrl}.data`; (2) the host must send **`Access-Control-Allow-Origin`** for cross-origin reads, because the model is fetched by the browser from a different origin (the existing behaviour adds `Access-Control-Allow-Origin: *` for `/spoter_(.*)` — mirror that on the host). For very large single-file downloads, Range support and a long `Cache-Control` are also worth mirroring from `web/vercel.json`.

No URL was invented and nothing was uploaded to any service: this is a decision for the owner.

### 8.3 Deployment strategy

* **Git-based Vercel deployment (recommended).** Connect the private repository and let Vercel build `web/` with the repository root as the project root (so the cross-directory imports of §5.4 resolve). No documented repository/source-size cap exists for git deployments — the 100 MB limit is explicitly a **CLI** limit — so the 47.4 MiB GLB and the ort runtimes can be served straight from the repository, and the only external requirement is the two model pairs from §8.2.
* **CLI deployment is not viable as configured.** The pre-deployment audit measured a 493.8 MiB upload honouring `web/.vercelignore` against a documented 100 MB Hobby budget, and `.vercelignore` cannot remove files that the build itself copies out of `public/`.
* **Reduce the build output before any deploy.** `web/dist` measured **983 MB**: 464.7 MiB of unreferenced GLBs copied out of `web/public/avatar/` (only the 47.4 MiB production GLB is referenced by the app), 359.7 MiB of models, 82.1 MiB of ort runtimes of which only 13.6 MiB is loaded, plus a **27 MiB duplicate `ort-wasm-simd-threaded.jsep-<hash>.wasm` that the bundler emits into `dist/assets/`** (it comes from `onnxruntime-web`'s package, not from the app: `web/src/lib/inference.ts` sets `ort.env.wasm.wasmPaths` to `/onnxruntime/ort-wasm-simd-threaded.wasm`). Moving the 9 experimental GLBs to `avatar/exports/` (already git-ignored) is the single highest-value deployment fix — and it requires the one-line test path update noted in B4.
* Unchanged and still valid: `web/vercel.json` build settings, the model/GLB/wasm `Cache-Control` headers, and the hash-router `/(.*) → /index.html` rewrite (with the audit's standing recommendation to narrow it so a missing 179 MiB asset returns 404 instead of `index.html`).
* Optional hygiene, **not** applied here because it would break a working dev tool: `web/verify_assets.js` checks the three unused ort variants, so they stay tracked; trimming them (~68.5 MiB) is a separate, deliberate change.

---

## 9. What was verified vs. assumed

**Verified by direct measurement or inspection here:** the git state, remote state, destination emptiness and its visibility/permissions, the destination's zero refs, all `.gitignore` effects via `git check-ignore`, the payload's exact file list/count/sizes/extension and area distribution, the largest-file analysis, the `web/dist` size and content, the 16 cross-directory imports and their six resolved targets, the build/typecheck/test exits and summaries, the secret scan (with working positive controls), the `.env.local` variable names and absence of secret shapes, the override implementation in `modelRegistry.ts` / `inference.ts` / `useSignVoxEngine.ts`, the `.data` sidecar derivation, and the backup contents.

**Not verified (cannot be, from here):** whether a push actually succeeds (B2 — the credential helper hangs, and the API says the account has no write access); whether the destination is private (it is not — B1); the live behaviour of any external asset host; Vercel's live project behaviour, build limits and plan status; GitHub's behaviour for the 47.4 MiB GLB specifically (documented thresholds are 50 MiB warning / 100 MiB block, so it is expected to pass with a warning); the un-backed-up binaries' integrity beyond the 28 recorded SHA-256 digests (nothing has been restored from the archive — it was verified by listing, `tar -tzf | wc -l` = 601, not by extraction); and any Python check, because no virtualenv was activated for this task.

**Assumed from the pre-deployment audit (not re-measured here):** the `data/` dataset's 2.08 GiB / 1,845 files, the size of `.venv_pilot`, the Vercel CLI's 493.8 MiB upload measurement, and GitHub's/Vercel's documented limits (which the audit cites to their official pages).

---

## 10. Corrections to `docs/PRE_DEPLOYMENT_AUDIT_2026-10-16.md`

That audit remains the correct analysis of its own moment; three of its findings no longer describe the tree:

1. **§4/§5 "Supabase is not used by this project at all"** is stale. `supabase/migrations/20261016120000_create_waitlist_signups.sql`, `supabase/tests/waitlist_signups_rls_test.sql`, `web/src/lib/supabaseClient.ts`, `web/src/lib/waitlist.ts`, `web/src/pages/JoinPage.tsx` and `web/src/tests/waitlistFlow.test.ts` now exist, `@supabase/supabase-js` is a dependency, and there is a `docs/SUPABASE_WAITLIST_SETUP.md`. **This migration task does not touch any of it** — no SQL was executed, no Supabase setting was changed, and the waitlist migration is **not applied**.
2. **§2.2 "no `.env` file exists anywhere"** is stale: `web/.env.local` exists (it is ignored and untracked, and contains only the two public-by-design variables — §5.2).
3. **§2.3/§9.3** do not yet list `*.npy`, `*.fbx`, `.gradle/`, `*.tsbuildinfo`, `*.ckpt`, `*.backup`, `data/`, `.agents/` or `node_modules_old/` as ignore candidates; §3 here adds them. The audit's claim that `*.glb` was unrestricted is now addressed by a `*.glb` rule with a single negation for the production GLB.

Also worth recording: the audit's `web/README.md` staleness (O7) and the missing CI (O8) are still open, and the test count has moved from 164 to 198.

---

## 11. Files created or edited by this task (nothing else was touched)

| Path | Change |
|---|---|
| `.gitignore` | **edited** — hygiene block appended, §3.1; corrected and extended during the Batch A review, §3.1.1 (pre-change copy preserved in the backup) |
| `.env.example` | **edited** — the 3 documented `VITE_*` variables extended with the 7 overrides added commented-out, §3.1.1 |
| `docs/REPOSITORY_MIGRATION_2026-10-16.md` | created — this document |
| `docs/migration/planned-files-2026-10-16.txt` | created — the exact payload manifest (513 entries after the `data/` correction) |
| `docs/migration/local-only-assets-sha256.txt` | created — SHA-256 of the large files that stay local |

Outside the repository: `D:/Singvox/_signvox_migration_backup_2026-10-16/` (§2.5) and the new `new-origin` remote (§2.2).

**Deliberately not done:** no `git add`/stage, `git commit`, `git fetch`, `git pull`, `git reset`, `git clean`, `git stash`, `git checkout`, `git rebase`, tag or branch change; no write of any kind to `origin` or `old-origin`; no deployment (preview or otherwise); no Supabase or database operation; no email; no file deleted, moved or renamed; no secret value printed or written. The **only** write to the destination so far is the owner-approved baseline push recorded in §1.8, which carried the pre-existing commit unchanged.

---

## 12. Exact next action requiring owner approval

> **Step 1 is done — the baseline commit is live on `new-origin`** (`aeed61c6b7796b0201326be8c715861849142645`, §1.8).
>
> **Waiting on your review now is Batch A — repository hygiene and safe configuration.** It is applied to the working tree but **not staged**:
> - `.gitignore` — the `data/` → `/data/` correction (which un-hid `ai/sign-recognition/data/pilot_class_mapping.json`) plus the credentials and tool-cache rules (§3.1.1);
> - `.env.example` — the 7 undocumented `VITE_*` overrides, added commented-out so no default is overridden (§3.1.1).
>
> Nothing else will be staged, committed or pushed without a further explicit go-ahead:
> 1. ~~`git push new-origin main`~~ — **done**;
> 2. `git add -- <batch A paths>` → commit → push (after owner review of this batch);
> 3. the same for batch B, then batch C, with the §5.1 checks re-run against batch B before its commit.
