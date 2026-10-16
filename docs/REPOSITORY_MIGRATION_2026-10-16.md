# SignVox — Safe migration to the new canonical GitHub repository

**Date:** 2026-10-16 (Batch B reconciliation revision)
**Local checkout:** `D:/Singvox/Singvox` · branch `main` · local HEAD `c17f1c339ce1f065fc31d2ee909e79a15eca219b` · baseline commit `aeed61c6b7796b0201326be8c715861849142645`
**Destination:** `https://github.com/awahblaiseatanga-beep/Singvox.git` — its `refs/heads/main` is still `aeed61c6…`; the two commits made locally after the baseline push (`7e0c741`, `c17f1c3`) have **not** been pushed.
**Status of this document:** plan + evidence. **Nothing has been staged, committed, pushed, deployed, or changed on any remote, and no cloud resource has been created.** The index is empty. The files this task created or edited are listed in §11.

> This document is the rationale referenced by the header comment of the new
> `.gitignore` rules. It supersedes §9 of `docs/PRE_DEPLOYMENT_AUDIT_2026-10-16.md`
> where the two disagree, and it corrects three findings of that audit that are now
> stale (see §10).

---

## 1. Executive summary

1. **The destination repository exists, is empty, and is now PRIVATE** (re-verified 2026-10-16 after the owner changed its visibility). It was created `2026-10-16T02:45:34Z`, `size: 0`, default branch `main`, and `git ls-remote` returns **zero** refs. It is therefore safe to receive the existing history as an ordinary new-branch push — no force, no rewrite (§7, B1 — resolved).
2. **This machine can now push to the destination** (re-verified 2026-10-16). The `gh` CLI is still signed in only as the old account `abonkweawah-png`, which now receives **404** on the private repository, but Windows Credential Manager holds a working credential for the new owner (`git:https://awahblaiseatanga-beep@github.com`). `git push --dry-run new-origin main` succeeds both pinned and unpinned — `* [new branch] main -> main`, exit 0 — and wrote nothing (§7, B2 — resolved). The earlier `manager` hang was that helper waiting to be told which of the two stored accounts to use.
3. **The real risk was in the working tree, not the remote.** A naive `git add -A` with the pre-existing `.gitignore` would have attempted to stage every component the pre-deployment audit warned about — **1,839 generated `.npy` feature arrays (402 MiB)**, **1,970 MiB of training checkpoints (11 files)**, **512.1 MiB of avatar GLBs**, **381 MiB of Blender exports**, 216 MiB of `.blend`/`.blend1` sources, 88 MiB of third-party `.fbx`, **359.7 MiB of model weights**, the third-party video dataset (2.08 GiB) and a ~40,000-file Python virtualenv — i.e. the bulk of a 10.9 GiB checkout. The `.gitignore` was fixed **before anything was staged** (§3).
4. **After the fix, the payload that carries the project is 144,223,874 bytes (137.54 MiB) over 504 pre-existing new files plus 6 modified tracked files — 510 entries.** The 3 documents this task itself created add a further ~70 KiB, bringing the full staging list to **513 entries**; because those three files include this one, their exact bytes change on every edit, so the size is quoted as the stable 510-entry subtotal (§4.1). **After the Batch A commits the pending set is 508 entries / 137.53 MiB — §4.1 is authoritative for the current numbers.** Everything is far below GitHub's 100 MiB per-file hard block; the single largest file is the 47.4 MiB production avatar GLB and only five files exceed 10 MiB (§4).
5. **The application source is complete and verified in place:** `npm run build` exit 0, `npx tsc -b --force` exit 0, `npx vitest run` 30 files / 198 tests passed exit 0 (§6). All 16 cross-directory imports that reach outside `web/` resolve to files that are either already tracked or inside the migration payload (§5.4).
6. **The two ~179 MiB ONNX external-data sidecars cannot enter Git and cannot be CLI-uploaded to Vercel.** They must be hosted externally and referenced through the existing `VITE_SPOTER_V2_URL` / `VITE_SPOTER_PILOT_URL` overrides, which are implemented and verified in code (§8).
7. **A recoverable backup exists outside the repository**: history bundle, 601-file source archive, the pre-change `.gitignore`, a git-state snapshot, and SHA-256 digests of the 28 large files that deliberately stay local (§2.5).
8. **The baseline history is pushed; two later local commits are not.** `git push new-origin main` returned `* [new branch] main -> main`, exit 0; remote `refs/heads/main` is `aeed61c6b7796b0201326be8c715861849142645`. Since then two further commits were created locally — `7e0c741` (`.gitignore` + `.env.example` hygiene, this plan, the 513-entry manifest) and `c17f1c3` (the local-only asset ledger) — so **local HEAD is now `c17f1c3` and the destination is one push behind**. No force, no rewrite. Nothing is staged (§2.1, §2.3).
9. **Four committed tests depend on gitignored local fixtures** and therefore cannot pass on a clean clone: `goodCandidate`, `reproduce_trace`, `baseline_threshold_eval` and `temporal_sampling_parity`. Guards that skip them **only when the fixture is absent** are prepared but **not applied** (§4.6).

**This plan stops before staging.** The private destination repository and working write credentials for `awahblaiseatanga-beep` are in place (§7, B1/B2 resolved), the baseline commit is live, and the pending set is classified in `docs/migration/batch-b-manifest-2026-10-16.txt` (**508 entries**). Four decisions still need the owner's approval before Batch B can be staged (§13).

---

## 2. Current state (measured)

### 2.1 Git (as of the Batch B reconciliation, 2026-10-16)

| Item | Value |
|---|---|
| `git rev-parse HEAD` | `c17f1c339ce1f065fc31d2ee909e79a15eca219b` |
| Branch | `main` |
| Baseline (initial) commit | `aeed61c6b7796b0201326be8c715861849142645` |
| Commits in history | **3** (`git rev-list --count HEAD`): `aeed61c6` → `7e0c741` → `c17f1c3` |
| Tracked files | **101** |
| Stashes | none |
| Submodules | none (no `.gitmodules`) |
| Modified tracked files | **5** (4 pre-existing owner changes + this plan) |
| New (untracked, non-ignored) files | **505** = 504 pending payload files + this revision's revised manifest; see §4.1 |
| Index (staged paths) | **0** — `git diff --cached --name-only` is empty |
| Upstream | `main` tracks `origin/main` (unchanged, not pushed to by this task) |
| Destination tip | `new-origin` `refs/heads/main` = `aeed61c6…` — **two commits behind local HEAD** |

Modified tracked files:

```
 M ai/sign-recognition/training/dataloaders.py   <- pre-existing owner change (preserved, §4.7)
 M app/App.tsx                                   <- pre-existing owner change (preserved, §4.7)
 M app/package.json                              <- pre-existing owner change (preserved, §4.7)
 M docs/REPOSITORY_MIGRATION_2026-10-16.md       <- this task's plan (committed in 7e0c741, edited again here)
 M docs/architecture/TECHNICAL_ARCHITECTURE.md   <- pre-existing owner change (preserved, §4.7)
```

`.gitignore` and `.env.example` are no longer listed: their hygiene edits were committed in `7e0c741` (§3.1.1).

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

**Post-push state (2026-10-16).** The destination was empty, so the "if it contains commits or files, stop and report" condition never triggered; it holds exactly one commit — the baseline — and `refs/heads/main` is `aeed61c6…`. Both original blockers, visibility and write access, are resolved (§7, B1/B2). Two further commits were then made **locally only** (`7e0c741` hygiene + manifest, `c17f1c3` asset ledger), so the destination is now two commits behind. **Nothing is staged.**

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

**As originally measured, before any staging:** 507 new files + 6 modified tracked files = **513 entries / 137.54 MiB**. That figure is kept because §1.4 and §2.5 quote it.

**As of the Batch B reconciliation (current):** this plan, `docs/migration/planned-files-2026-10-16.txt`, `docs/migration/local-only-assets-sha256.txt`, `.gitignore` and `.env.example` were committed in `7e0c741` + `c17f1c3`, so they left the pending set.

| Metric | Value |
|---|---|
| Entries committed since the audit | **5** (`.gitignore`, `.env.example`, this plan, `planned-files-2026-10-16.txt`, `local-only-assets-sha256.txt`) — §2.1 |
| **Pending entries** | **508** = 504 untracked new files + 4 modified tracked files |
| **Pending payload bytes** | **144,218,206 B = 137.53 MiB** (measured with `stat` over the 508 paths) |
| Batch B | **156** = 17 configuration + 139 application source |
| Batch C | **340** |
| Excluded from every batch | **8** (§4.5) |
| Preserved, unstaged owner changes | **4** (§4.7) |
| Plus this revision's revised manifest | `docs/migration/batch-b-manifest-2026-10-16.txt` — self-describing, grows with every edit (like this document) |
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

The **authoritative, line-by-line classification** is now `docs/migration/batch-b-manifest-2026-10-16.txt` (508 entries, one repository-relative path per line, sorted). `docs/migration/planned-files-2026-10-16.txt` is kept as the original 513-entry list; it is committed and describes the pre-commit set.

### 4.4 Proposed commit batches (Phase 4.1–4.3) — reconciled with the revised manifest

The line-by-line classification is `docs/migration/batch-b-manifest-2026-10-16.txt`; the batches below state the same result in prose. **None of it is staged.**

**Batch A — repository hygiene and safe configuration templates — ALREADY COMMITTED**
Committed as `7e0c741` (`.gitignore`, `.env.example`, this plan, `docs/migration/planned-files-2026-10-16.txt`) and `c17f1c3` (`docs/migration/local-only-assets-sha256.txt`). Those five paths are therefore **no longer in any pending batch**, and `git status` no longer lists `.gitignore` or `.env.example`. The configuration templates that were originally grouped with them (`web/.vercelignore`, `web/vercel.json`, `web/tsconfig.json`, …) moved into Batch B by owner decision, recorded as Batch B manifest §1a.

**Batch B — application source plus the configuration a reproducible build, test and deploy needs — 156 files**
*1a. Configuration (17, manifest §1a):* `web/package.json`, `web/package-lock.json`, `web/tsconfig.json`, `web/vite.config.ts`, `web/vercel.json`, `web/.vercelignore`, `web/index.html`, `app/.eslintrc.js`, `app/.prettierrc.js`, `app/app.json`, `app/babel.config.js`, `app/index.js`, `app/metro.config.js`, `app/tsconfig.json`, `app/scripts/copy_mediapipe_models.py`, `avatar/package.json`, `avatar/package-lock.json`. Each inspected individually: manifests, lockfiles, TypeScript/Vite/Vercel config and the React Native entry/build config. No secret, no generated config, no unrelated scaffolding in any of them.
*1b. Application source (139, manifest §1b):* `web/src/**` (application, `lib/`, `engine/`, `components/`, `pages/`, `tests/`), `web/public/**` (**only** the production GLB, the four ort runtimes and the favicons — every other asset under `public/` is gitignored), `web/bench/**`, `web/tests/**`, `web/*.mjs`, `web/verify_assets.js`, `avatar/controller/*.ts` (imported by the app), the five new `ai/sign-recognition/**` files and `app/android/**`.
*Why second:* this is the deployable application plus everything it imports. Verified in §5.4 — no import target is missing. The frozen ASL-100 vocabulary, the SPOTER V2 feature contract (60 × 366), normalization, class mapping, temporal sampler and latency profiler are all carried unchanged.
*Deliberately not in Batch B:* `app/package.json`, `ai/sign-recognition/training/dataloaders.py` and `app/App.tsx` — pre-existing owner changes, preserved and unstaged (§4.7). Note the consequence: Batch B carries the build configuration, so until the `app/package.json` decision (§13, D4) is made, a staging of Batch B alone would not be independently buildable.

> **Batch B checklist — ignored model artifacts (carry-forward from Batch A).**
> `web/public/spoter_v2_model.onnx`, `web/public/spoter_pilot.onnx` and their `.data` sidecars are **not** in the payload: the pre-existing `*.onnx` rule and the new `*.onnx.data` rule (§3.1) exclude them, and the two ~179 MiB sidecars would exceed GitHub's 100 MiB per-file block in any case. Batch B must therefore:
> 1. keep `VITE_SPOTER_V2_URL` / `VITE_SPOTER_PILOT_URL` as the **only** runtime path for the graphs and their sidecars (§8) — they are documented, commented-out, in `.env.example` (§3.1.1);
> 2. confirm the production GLB `web/public/avatar/SignVox_Female_Competition_Prototype.glb` **is** included — it is the one negation under `*.glb` and the app's default avatar;
> 3. **not** silently re-enable `*.onnx`: committing a graph without its external-data sidecar still cannot run (`inference.ts` derives the sidecar as `${modelUrl}.data`), so the graph and weights must stay side by side on the chosen host.

**Batch C — documentation, migrations, research and tooling — 340 files**
`docs/**` (all new reports: launch, recovery audit, speed optimisation, pre-deployment audit, `ai-ml/`, `architecture/`, `avatar/`, `blender/`, `competition/`, `decisions/`, `research/`, `testing/`) · `supabase/migrations/20261016120000_create_waitlist_signups.sql` · `supabase/tests/waitlist_signups_rls_test.sql` · `tools/**` · `experiments/**`.
*Why third:* documentation and the (unapplied) Supabase migration describe the code Batch B lands. `tools/**` and `experiments/**` ride along because no production dependency on them exists — verified by searching `web/src`, `web/tests`, `web/bench`, `ai/`, `avatar/controller/` and `app/` for imports; nothing matches. (The earlier counts of 46/50 for `tools/` and 192/222 for `experiments/` were both wrong; the manifest counts every path.)
*Deliberately not in Batch C:* `docs/architecture/TECHNICAL_ARCHITECTURE.md` — a pre-existing owner change (§4.7).

Reconciliation totals: Batch B 156 + Batch C 340 + excluded 8 + preserved 4 = **508**, exactly the pending set of §4.1, and no path appears in two batches. The excluded eight are §4.5, the preserved four are §4.7, the reproducibility gap is §4.6.

### 4.5 Scratch diagnostics — excluded from every batch (owner decision, nothing deleted)

> **Correction (2026-10-16, Batch B reconciliation).** An earlier revision of this section claimed these seven paths were "not in the proposed payload either way". That was **wrong**: the manifest (`docs/migration/planned-files-2026-10-16.txt`) lists **all seven**, and all seven are untracked on disk. They are now excluded from every proposed batch by **decision**, recorded here, instead of being implied by the manifest.

| Path | Size | Purpose | Verdict |
|---|---|---|---|
| `find_data.py` | 298 B | one-off regex scan of a local `.onnx` for its `.data` reference; hardcodes `d:\Singvox\...` | exclude |
| `inspect_ch41.py` | 354 B | one-off: prints `mixamorig` bones from `Ch41_nonPBR.fbx`; hardcoded path | exclude |
| `inspect_fbx.py` | 1,194 B | one-off: bone/AnimStack strings from two FBX files; hardcoded paths | exclude |
| `inspect_glb.py` | 1,520 B | GLB inspector, portable (argv) but a **duplicate** of `tools/inspect_glb.py` | exclude (duplicate) |
| `inspect_onnx.py` | 676 B | one-off: prints the ONNX external-data location; hardcoded path | exclude |
| `check_hierarchy.py` | 1,740 B | GLB hand-bone hierarchy check; no test or build references it | exclude |
| `tools/extracted_guide.txt` | 14,672 B | **generated** by `tools/extract_pdf.py` from a PDF | exclude (generated) |

**Required for reproducible tests, benchmarks or production functionality: none.** Verified by searching `web/src`, `web/tests`, `web/bench`, `tools/`, `ai/` and `avatar/controller/` for any reference — the only hits are documentation prose and `tools/extract_pdf.py` *writing* `tools/extracted_guide.txt`. All seven stay on disk; nothing was deleted.

**Also excluded on the same grounds:** `tools/audit_out.txt` (402 B, mtime 2026-10-10). Verified **generated, not a fixture**: `tools/tmp_audit_asl.py:8` writes it (`out_path = r"d:\Singvox\Singvox\tools\audit_out.txt"`) by summarising `D:\ASL_Citizen\splits\{train,val,test}.csv` against `docs/ai-ml/asl100_vocabulary.json`, and that writer is itself ignored by the pre-existing `tmp_*` rule. No test, benchmark or production path reads the output — searching `web/src`, `web/tests`, `web/bench`, `docs` and `ai/` finds only prose. The claim elsewhere that it was ignored "via `*.out`" is **wrong** — `*.out` does not match `audit_out.txt`, which ends in `.txt`, and `git check-ignore tools/audit_out.txt` still reports no match (exit 1). It is therefore excluded by **decision**, exactly like the seven files above; the anchored rule `/tools/audit_out.txt` was **applied on 2026-10-16** (§13, D3; now `.gitignore` line 165) and re-confirmed with `git check-ignore -v`. The file has not been deleted or moved — it stays on disk, now ignored.

---

### 4.6 Reproducibility gap — gitignored fixtures required by four committed tests

**Status: resolved by explicit skips on 2026-10-16** (§13, D1 applied). The 31-file / 206-test suite of §5.1 passes here because the fixtures exist on this machine. Four committed test files read local-only assets that the `.gitignore` rules keep out of the payload, so on a clean clone they cannot pass — they now report as *skipped* instead of failing or silently passing. Established by resolving every fixture path with `fs.existsSync`, confirming each with `git check-ignore -v`, and searching every test file under `web/src`, `web/tests` and `web/src/lib` for the asset patterns.

| Test (all Batch B) | Required local fixture(s) | Rule that excludes it | Behaviour on a clean clone |
|---|---|---|---|
| `web/src/tests/goodCandidate.test.ts` | `experiments/avatar/pilot_good/SignVox_GOOD_Candidate.glb` (49,800,688 B) | `*.glb` | **fails** — `expect(fs.existsSync(CANDIDATE)).toBe(true)` |
| `web/src/tests/reproduce_trace.test.ts` | `web/public/avatar/SignVox_Female.glb` (49,576,404 B) | `*.glb` (the negated production GLB is a different file) | **fails** in `beforeAll` (`ctrl.loadGLB`) |
| `web/src/tests/baseline_threshold_eval.test.ts` | `ai/sign-recognition/data/asl100_training_manifest.csv` (143,079 B); `ai/sign-recognition/data/{dataset_extracted,processed_pilot}/**_features.npy`; `web/public/spoter_v2_model.onnx`; `web/public/spoter_pilot.onnx` | `/asl100_training_manifest.csv`, `*.npy` and the dataset dirs (pre-existing rules), `*.onnx` | **fails** — `fs.readFileSync(manifestPath)` |
| `web/src/tests/temporal_sampling_parity.test.ts` | `ai/sign-recognition/data/dataset_extracted/{0022932153577568393-HELLO,9953610281521326-YES}_features.npy`; `web/public/spoter_v2_model.onnx` | as above | **silently no-ops** — `console.log('[parity] recorded features unavailable, skipping'); return;` |

**Correction to the earlier reading.** The first pass in `docs/migration/batch-b-manifest-2026-10-16.txt` §7 said the two ONNX-dependent tests needed only the recorded dataset. They also need the graph files, which `*.onnx` keeps out of the repository. The `VITE_SPOTER_*_URL` overrides of §8.2 do **not** help here: both tests build an absolute filesystem path under `web/public/`, not an HTTP URL. The other **26** of the 30 test files vitest runs are unaffected — e.g. `modelRegistry.test.ts` reads `class_index_mapping.json` (tracked), `pilot_class_mapping.json` (payload §1b) and the production GLB (payload §1b), so it stays reproducible. (Vitest's `test.include` is `src/**/*.test.ts` + `tests/**/*.test.ts`, so `src/tests/avatarLifecycle.test.tsx` is outside the suite altogether — hence 30 of the 31 collected test files run.)

**Applied 2026-10-16 (§13, D1).** For each of the four files a guard that skips **only when the fixture is absent** — `fs.existsSync` at module scope feeding vitest 2.1.8 `it.skipIf` / `describe.skipIf` (`ChainableTestAPI.skipIf` verified present in the installed `@vitest/runner`). When the fixture exists the test executes with **every** assertion unchanged; no assertion is relaxed, removed or wrapped, so a real failure can never become a skip. `temporal_sampling_parity.test.ts` additionally lost its silent `return` and now reports the missing inputs as an explicit skip, and `reproduce_trace.test.ts` had its GLB path hoisted to module scope so the guard can test it.

**Added in the same change.** `web/src/tests/syntheticFixtures.test.ts` (8 always-on tests) covers the structural invariants that need no local asset: a tracked deterministic 46-bone rig GLB (8,692 B) and two 274-byte synthetic ONNX graphs with their zero-byte `.data` sidecars, all generated by the dependency-free `web/src/tests/fixtures/generate_fixtures.mjs` (30,865 B of fixtures in total), driven through the real `AvatarController.loadGLB`, the real `SpoterInferenceSession` and the real sampler/stabilizer classes. It makes **no** accuracy claim — that remains exclusive to the recorded-clip tests. Measured after the apply: **this checkout 31 files / 206 tests pass, 0 skipped, exit 0**; **a payload-only clone 27 files / 201 tests pass, 4 files / 5 tests skipped, 0 failed**.

**What this does not claim.** With the guards applied the suite is still **not** reproducible on a clean clone: four test files report as *skipped* instead of passing, and this has not yet been validated in a genuine fresh clone (§13, D5). Real reproducibility needs the fixtures to ship, or the tests to leave the default suite (§13, D1).

---

### 4.7 Pre-existing owner changes — preserved exactly, unstaged

These four tracked files carry work that predates this migration task. **Nothing in this task modified, staged, reverted or discarded any of them.**

| File | State (`git diff --stat`) | Status |
|---|---|---|
| `ai/sign-recognition/training/dataloaders.py` | modified, 15 lines changed | preserved; whether it joins a batch is a **pending decision** (§13, D4). §4.4 previously listed it in Batch B — that listing is superseded. |
| `app/App.tsx` | modified, 239 lines changed | preserved; pending decision (§13, D4) |
| `app/package.json` | modified, 27 lines changed — full diff and analysis in §13.1 | preserved; pending decision (§13, D4) |
| `docs/architecture/TECHNICAL_ARCHITECTURE.md` | modified, 7 lines added | preserved; §4.4 previously listed it in Batch C — superseded. |

A fifth tracked file, `docs/REPOSITORY_MIGRATION_2026-10-16.md`, is this task's own plan: committed in `7e0c741` and modified again by the reconciliation edits recorded in §11.

---

## 5. Verification (Phase 5)

### 5.1 Commands run, from `web/`

| Command | Result | Evidence |
|---|---|---|
| `npm run build` (i.e. `tsc -b && vite build`) | **exit 0** | `✓ 121 modules transformed`, `dist/assets/index-D3Faw0yY.js 1,717.44 kB │ gzip: 467.76 kB`, `dist/assets/index-DtwNF64Q.css 23.38 kB`, `✓ built in 1m 60s`; only the standard chunk-size advisory |
| `npx tsc -b --force` | **exit 0** | no diagnostics |
| `npx vitest run` (2026-10-16, after the approved fixture fix) | **exit 0** | `Test Files 31 passed (31)`, `Tests 206 passed (206)`, **0 skipped**, duration 78.65 s. The pre-fix run in this same tree was `30 passed (30)` / `198 passed (198)` in 146.00 s; the delta is exactly the 8 synthetic tests in the new file. |

The suite count grew from the 29 files / 164 tests of the pre-deployment audit to 30 / 198 when the waitlist/Supabase work (`web/src/tests/waitlistFlow.test.ts`, 34 tests) landed, and then to 31 / 206 on 2026-10-16 when the synthetic-fixture file was added (§4.6). Two stderr blocks in the log are **intentional negative-path assertions**, not failures: `speech.test.ts` > "errors inside utterance/speak loop passively fail without breaking DOM" (`SpeechSynthesis API failed: Error: Driver unavailable`) and the deliberate double-submit assertions in `baseline_threshold_eval.test.ts`. Exit status is 0 for both the run and every test file.

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

1. **History first, unmodified — DONE 2026-10-16.** The destination was empty, so `git push new-origin main` was a plain branch creation carrying the single existing commit `aeed61c6b7796b0201326be8c715861849142645`; remote `refs/heads/main` is that commit. It is **no longer equal to local HEAD**, which has advanced to `7e0c741` and then `c17f1c3` (both local-only, §2.1). No force, no rebase, no history rewrite, no `filter-repo`. Nothing in the existing history contains a secret or a large file:
   * the 98 tracked files total **844,023 B (0.80 MiB)**, and the largest is 38.8 KiB (`ai/sign-recognition/training/run_experiment_01.py`) — no binary at all;
   * no `.env*`, no dataset, no checkpoint, no `.onnx`/`.glb` is tracked (all excluded by the pre-existing ignore rules);
   * §5.2 found no secret in the 486 text files of the payload, and the tracked set is a subset of that scan plus the already-scan-safe tracked files.
2. **Then one commit per remaining batch**, in the order B → C of §4.4 — Batch A is already committed as `7e0c741` + `c17f1c3`. Each commit is self-contained; the message will state what landed and what deliberately did not.
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

#### 8.2.1 Exact objects to publish, and the hosting contract they require

Measured from the files on disk; **nothing was invented and nothing was uploaded**.

| Object name to use at the host | Local source | Size | Content |
|---|---|---|---|
| `spoter_v2_model.onnx` | `web/public/spoter_v2_model.onnx` | 121,801 B | 79-class graph; declares 186 external-data tensors |
| `spoter_v2_model.onnx.data` | `web/public/spoter_v2_model.onnx.data` | 187,711,488 B (179.0 MiB) | its weights |
| `spoter_pilot.onnx` | `web/public/spoter_pilot.onnx` | 1,711,205 B | 3-class graph; declares 185 external-data tensors |
| `spoter_pilot.onnx.data` | `web/public/spoter_pilot.onnx.data` | 187,580,416 B (178.9 MiB) | its weights |

Requirements, each traced to the code that imposes it:

1. **The four objects must share one base URL, and the sidecar name must be exactly `<graph name>.data`.** `web/src/lib/inference.ts` sets `sessionOptions.externalData = [{ path: `${modelName}.data`, data: `${modelUrl}.data` }]`, and `modelRegistry.ts` resolves the graph from `VITE_SPOTER_V2_URL` / `VITE_SPOTER_PILOT_URL` (`?.trim() || '/spoter_…'`). So a host serving `<base>/spoter_v2_model.onnx` **must** also serve `<base>/spoter_v2_model.onnx.data` — no renaming, no directory split.
2. **HTTP `Range` support is required, not merely nice to have.** The graphs carry `location`/`offset`/`length` for every external-data tensor (verified: 186 entries in the 79-class graph, 185 in the pilot; the `location` string is exactly `spoter_v2_model.onnx.data` / `spoter_pilot.onnx.data`), so the runtime reads the sidecar by byte range instead of downloading it whole. The installed `onnxruntime-web` issues ranged requests (`Range` occurs in its bundler output, `dist/ort.bundle.min.mjs`). A host that ignores `Range` and always returns the whole 179 MiB body still works, but every tensor read then re-transfers the file. Responses must not be content-encoding-transformed.
3. **CORS for the deployed origin.** `Access-Control-Allow-Origin` (mirror the `*` that `web/vercel.json` already sets for `/spoter_(.*)`, or echo the exact origin with `Vary: Origin`), plus `Access-Control-Expose-Headers: Content-Range, Content-Length, Accept-Ranges` so the ranged reads are readable by the page.
4. **`Cache-Control: public, max-age=31536000, immutable`** — mirroring `web/vercel.json`. The bytes are version-pinned by filename, so no revalidation is needed; `ETag`/`Last-Modified` should stay enabled for conditional re-reads.
5. **`Content-Type: application/octet-stream`** for all four objects.

**Build-time variables for Vercel** (Vite inlines `VITE_*` at build time, so they must exist in the Vercel project environment *before* the build — and in `web/.env.local` for local work; never in Git):

```
VITE_SPOTER_V2_URL=https://<base>/spoter_v2_model.onnx
VITE_SPOTER_PILOT_URL=https://<base>/spoter_pilot.onnx
# VITE_AVATAR_GLB_URL stays UNSET: the production GLB is committed and served
# same-origin, so its built-in default /avatar/SignVox_Female_Competition_Prototype.glb
# is preserved exactly.
```

The Vercel **build** needs nothing from the host; only the browser at runtime does. The production GLB keeps its same-origin path in both cases: `vite build` copies it from `web/public/avatar/` into `dist/avatar/`, and `useSignVoxEngine.ts` uses `/avatar/SignVox_Female_Competition_Prototype.glb` unless `VITE_AVATAR_GLB_URL` overrides it — which is why the object list above contains **no** GLB.

One documentation defect found while checking this: the committed `.env.example` comment says the two sidecars **and the ~48 MiB avatar GLB** are not committed. That is now wrong for the GLB — the production GLB **is** in Batch B (§1b), and the comment's own default path for it is correct. The comment was corrected on 2026-10-16 (§13, D2 applied): it now reads "the two ~179 MiB ONNX external-data sidecars are not committed (the ~48 MiB production avatar GLB is)", with every variable, default and commented-out override untouched.

No URL was invented, no account was registered, no bucket was created and nothing was uploaded: the host and `<base>` are the owner's decision, and **deployment readiness is not claimed**.

### 8.3 Deployment strategy

* **Git-based Vercel deployment (recommended).** Connect the private repository and let Vercel build `web/` with the repository root as the project root (so the cross-directory imports of §5.4 resolve). No documented repository/source-size cap exists for git deployments — the 100 MB limit is explicitly a **CLI** limit — so the 47.4 MiB GLB and the ort runtimes can be served straight from the repository, and the only external requirement is the two model pairs from §8.2.
* **CLI deployment is not viable as configured.** The pre-deployment audit measured a 493.8 MiB upload honouring `web/.vercelignore` against a documented 100 MB Hobby budget, and `.vercelignore` cannot remove files that the build itself copies out of `public/`.
* **Reduce the build output before any deploy.** `web/dist` measured **983 MB**: 464.7 MiB of unreferenced GLBs copied out of `web/public/avatar/` (only the 47.4 MiB production GLB is referenced by the app), 359.7 MiB of models, 82.1 MiB of ort runtimes of which only 13.6 MiB is loaded, plus a **27 MiB duplicate `ort-wasm-simd-threaded.jsep-<hash>.wasm` that the bundler emits into `dist/assets/`** (it comes from `onnxruntime-web`'s package, not from the app: `web/src/lib/inference.ts` sets `ort.env.wasm.wasmPaths` to `/onnxruntime/ort-wasm-simd-threaded.wasm`). Moving the 9 experimental GLBs to `avatar/exports/` (already git-ignored) is the single highest-value deployment fix — and it requires the one-line test path update noted in B4.
* Unchanged and still valid: `web/vercel.json` build settings, the model/GLB/wasm `Cache-Control` headers, and the hash-router `/(.*) → /index.html` rewrite (with the audit's standing recommendation to narrow it so a missing 179 MiB asset returns 404 instead of `index.html`).
* Optional hygiene, **not** applied here because it would break a working dev tool: `web/verify_assets.js` checks the three unused ort variants, so they stay tracked; trimming them (~68.5 MiB) is a separate, deliberate change.

---

## 9. What was verified vs. assumed

**Verified by direct measurement or inspection here:** the git state, remote state, destination emptiness and its visibility/permissions, the destination's zero refs, all `.gitignore` effects via `git check-ignore`, the payload's exact file list/count/sizes/extension and area distribution, the largest-file analysis, the `web/dist` size and content, the 16 cross-directory imports and their six resolved targets, the build/typecheck/test exits and summaries, the secret scan (with working positive controls), the `.env.local` variable names and absence of secret shapes, the override implementation in `modelRegistry.ts` / `inference.ts` / `useSignVoxEngine.ts`, the `.data` sidecar derivation, and the backup contents.

**Verified in the Batch B reconciliation (2026-10-16):** current git state (`HEAD` `c17f1c3`, 3 commits, 101 tracked files, 5 modified tracked, 505 untracked-non-ignored, **empty index**, `new-origin` = `aeed61c6…`); the manifest's arithmetic (508 = 17 + 139 + 340 + 8 + 4, every path present on disk, none of the five committed paths leaked, no duplicates) and the 508-path byte total; the four fixture-dependent tests and **every** fixture path they need, including the two `*.onnx` graphs the first pass missed; `tools/audit_out.txt` as generated output of `tools/tmp_audit_asl.py`; each graph's external-data metadata (`location`/`offset`/`length`, 186 and 185 tensors); `Range` in the installed `onnxruntime-web` bundle; vitest 2.1.8's `skipIf` on both `ChainableTestAPI` and `ChainableSuiteAPI`; and the full `app/package.json` delta including the fact that it is unchanged since the baseline commit.

**Not verified (cannot be, from here):** the live behaviour of any external asset host — none exists, §8.2.1 is a plan and not a created resource; Vercel's live project behaviour, build limits and plan status; GitHub's behaviour for the 47.4 MiB GLB specifically (documented thresholds are 50 MiB warning / 100 MiB block, so it is expected to pass with a warning); the un-backed-up binaries' integrity beyond the 28 recorded SHA-256 digests (nothing has been restored from the archive — it was verified by listing, `tar -tzf | wc -l` = 601, not by extraction); whether a clean clone of the destination really builds and which of the four tests actually skip there (implied by §5.4 and §4.6, **not** exercised — no clone was made and no guard is applied); and any Python check, because no virtualenv was activated for this task. The earlier "push cannot be verified" entry is obsolete: the baseline push succeeded (§1.8) and the two later commits were never pushed.

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
| `docs/migration/planned-files-2026-10-16.txt` | created — the exact payload manifest (513 entries after the `data/` correction; **520 after the 2026-10-16 synthetic-fixture addendum**) |
| `docs/migration/local-only-assets-sha256.txt` | created — SHA-256 of the large files that stay local |
| `docs/migration/batch-b-manifest-2026-10-16.txt` | created (Batch B reconciliation) — the revised 508-entry classification, the corrected reproducibility gap (§4.6) and the asset contract (§8.2.1); supersedes the batch split formerly in §4.4. **Reconciled to revision 2 on 2026-10-16**: 163-file Batch B (new §1c), the applied decisions (§8) and the 515-entry denominator |
| `web/src/tests/syntheticFixtures.test.ts` | **created 2026-10-16** — 8 always-on structural tests over the tracked synthetic fixtures (§4.6) |
| `web/src/tests/fixtures/generate_fixtures.mjs` + 5 fixture files | **created 2026-10-16** — the deterministic dependency-free generator and its 30,865 B of output (§4.6) |
| `web/src/tests/{goodCandidate,reproduce_trace,baseline_threshold_eval,temporal_sampling_parity}.test.ts` | **edited 2026-10-16** — `skipIf` guards only; every pre-existing assertion byte-identical to the reviewed proposal (`cmp`-verified) |

Outside the repository: `D:/Singvox/_signvox_migration_backup_2026-10-16/` (§2.5) and the new `new-origin` remote (§2.2).

**Still deliberately not done (2026-10-16 revision):** no `git add`/stage, `git commit`, `git push`, `git fetch`, `git pull`, `git reset`, `git clean`, `git stash`, `git checkout`, `git restore`, `git rebase`, tag, branch or remote change; no deployment (preview or otherwise); no cloud resource, bucket or account created and no asset uploaded; no Supabase or database operation; no email; no file deleted, moved or renamed; no secret value printed or written. **Now done, with owner approval:** the §4.6 guards and synthetic fixtures, their `.gitignore` negations, the §4.5 anchored rule and the §8.2.1 `.env.example` correction — applied to the working tree and verified (§13, D1–D3). The **only** write to any remote remains the baseline push recorded in §1.8.

---

## 12. Exact next action requiring owner approval

> **Done so far:** the baseline commit is live on `new-origin` (`aeed61c6…`, §1.8); Batch A (the `.gitignore` and `.env.example` hygiene, this plan, `docs/migration/planned-files-2026-10-16.txt` and `docs/migration/local-only-assets-sha256.txt`) is committed locally as `7e0c741` + `c17f1c3`. **Both of those commits are unpushed**, so `new-origin` is two commits behind local `main`.
>
> **Applied since (2026-10-16, owner-approved):** D1 (the four fixture guards plus the tracked synthetic fixtures and their generator), D2 (the `.env.example` one-liner) and D3 (the anchored `/tools/audit_out.txt` rule). Verified with `npx tsc -b --force` (exit 0) and `npx vitest run` (31 files / 206 tests, 0 skipped, exit 0); `git diff --cached` is still empty.
>
> **Waiting on your review now:** D4 (the four preserved owner changes) and D5 (this plan's own status lines), then the Batch B staging decision using the reconciled 163-file list in `docs/migration/batch-b-manifest-2026-10-16.txt`.
>
> Nothing will be staged, committed, pushed or deployed without a further explicit go-ahead:
> 1. ~~`git push new-origin main`~~ — **done** (baseline only);
> 2. resolve D1–D4 in §13 — for D1 and D3 that means showing, then applying, the prepared diffs;
> 3. `git add -- <batch B paths>` → commit → re-run the §5.1 checks, reporting **skipped tests separately from passed and failed**, then push on a separate go-ahead;
> 4. the same for Batch C, after which the two unpushed Batch A commits ride along with the documented history.

---

## 13. Decisions awaiting owner approval

D1–D3 were **applied on 2026-10-16** with owner approval and now carry their verification; D4 and D5 remain open. `git diff --cached` is empty — nothing in this section is staged.

| # | Decision | Prepared artifact | Recommendation |
|---|---|---|---|
| **D1** — **APPLIED 2026-10-16** | Four committed tests could not pass on a clean clone (§4.6): `goodCandidate`, `reproduce_trace`, `baseline_threshold_eval`, `temporal_sampling_parity`. | Option (b): one `fs.existsSync` guard per file feeding `it.skipIf` / `describe.skipIf`, so the test skips **only** when its fixture is absent and runs with every assertion intact when it is present; `temporal_sampling_parity` also lost its silent `return`. Plus tracked synthetic fixtures (`web/src/tests/fixtures/`, 30,865 B, deterministic generator) and `web/src/tests/syntheticFixtures.test.ts` (8 structural tests, no accuracy claim) so the same invariants are covered on every clone (§4.6). | Applied and verified: this checkout 31 files / 206 tests pass, 0 skipped, exit 0; a payload-only clone 27 files / 201 tests pass with 4 files / 5 tests skipped and 0 failed. Rejected alternatives: (a) commit the ~97 MiB of fixture inputs, or (c) drop the four files from the default suite. |
| **D2** — **APPLIED 2026-10-16** | `.env.example` said the avatar GLB is not committed, which is wrong (§8.2.1). | A one-line reword that keeps every variable and default untouched. | Apply. `.env.example` is already committed (`7e0c741`), so this becomes a new modification of a tracked file. |
| **D3** — **APPLIED 2026-10-16** (.gitignore line 165, `git check-ignore -v`-confirmed) | `tools/audit_out.txt` was untracked and deliberately not ignored (§4.5). | An anchored rule `/tools/audit_out.txt` plus a one-line comment naming `tools/tmp_audit_asl.py` as its writer. | Apply the anchored rule rather than a broad `*audit_out*` pattern — the exact path avoids repeating the over-broad-pattern mistake of §3.1.1. |
| **D4** | The four preserved owner changes (§4.7) — in particular whether `app/package.json` joins Batch B. | None; this task must not edit them. | See §13.1 and §13.2. |
| **D5** | This plan's own status lines (§4.5, §4.6, §5.1, §8.2.1, §11, §12, §13) still described the applied decisions as pending, and the Batch B manifest measured 156 files against a tree that now holds 163. | Reconciled in this revision (2026-10-16): the applied state is recorded inline and the manifest was moved to revision 2. | Keep the plan and the manifest agreeing; re-read both before staging. |

### 13.1 `app/package.json` — complete diff, and why it matters

The file is unchanged since the baseline commit (`git diff aeed61c HEAD -- app/package.json` is empty), so the working-tree delta below **is** the whole change:

```diff
diff --git a/app/package.json b/app/package.json
index 5d2a8c6..a60813a 100644
--- a/app/package.json
+++ b/app/package.json
@@ -5,19 +5,32 @@
   "scripts": {
     "android": "react-native run-android",
     "ios": "react-native run-ios",
-    "start": "react-native start"
+    "start": "react-native start",
+    "test": "jest"
   },
   "dependencies": {
     "react": "18.2.0",
-    "react-native": "0.74.0",
-    "react-native-vision-camera": "^4.0.0",
-    "react-native-worklets-core": "^1.0.0",
-    "react-native-reanimated": "^3.8.0"
+    "react-native-vision-camera": "4.6.4",
+    "react-native-worklets-core": "1.6.3",
+    "react-native-reanimated": "^3.8.0",
+    "react-native": "0.74.0"
   },
   "devDependencies": {
+    "@types/react-native": "^0.73.0",
     "@babel/core": "^7.20.0",
+    "@babel/preset-env": "^7.20.0",
+    "@babel/runtime": "^7.20.0",
+    "@react-native/babel-preset": "0.74.81",
+    "@react-native/eslint-config": "0.74.81",
+    "@react-native/metro-config": "0.74.81",
+    "@react-native/typescript-config": "0.74.81",
     "@types/react": "^18.2.6",
-    "@types/react-native": "^0.73.0",
-    "typescript": "^5.0.4"
+    "@types/react-test-renderer": "^18.0.0",
+    "babel-jest": "^29.6.3",
+    "eslint": "^8.19.0",
+    "jest": "^29.6.3",
+    "prettier": "2.8.8",
+    "react-test-renderer": "18.2.0",
+    "typescript": "5.0.4"
   }
```

Facts read off the diff: 27 changed lines (+24/−7); **no dependency removed** (`react-native` and `@types/react-native` survive — they are reordered); no secret, no `postinstall`, no `resolutions`/`overrides`, no new registry, no private scope; the two previously loose ranges (`^4.0.0`, `^1.0.0`) are now **pinned** to `4.6.4` / `1.6.3`; and there is **no `app/package-lock.json`** on disk, so `app/` has no lockfile in or out of the payload.

Why it is required for a reproducible build: `app/babel.config.js` loads `react-native-worklets-core/plugin` and `@react-native/babel-preset`; `app/metro.config.js` requires `@react-native/metro-config`; `app/tsconfig.json` extends `@react-native/typescript-config`. **None of those four packages exists in the committed `devDependencies`**, and the VisionCamera / worklets-core versions the new code depends on were only unconstrained `^` ranges. A clean `npm install` from the committed file therefore cannot resolve the toolchain the repository's own config files reference, so the React Native app — unlike `web/` — would not be reproducible. `"test": "jest"` likewise exposes the Jest setup that the new devDependencies bring.

Safe inclusion, **if** approved: stage only this path, verbatim, from the working tree (`git add -- app/package.json`) after recording its pre-staging `git hash-object` so the exact bytes stay provable and restorable. Do **not** use `git checkout --` / `git restore`, `git add -p` slicing, or any file rewrite: the change is the owner's, so it lands as-is or not at all. It stays listed apart from Batch B until the owner says otherwise.

### 13.2 The other three preserved changes

`ai/sign-recognition/training/dataloaders.py` (15 lines), `app/App.tsx` (239 lines) and `docs/architecture/TECHNICAL_ARCHITECTURE.md` (7 lines) are equally untouched by this task. Each needs the same yes/no: include verbatim in a named batch (B for the first two, C for the third, as §4.4 originally proposed), or leave uncommitted. Whichever is chosen, §4.4 and manifest §4 must be updated **together** so the two documents keep agreeing.
