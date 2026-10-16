# SignVox — Pre-Deployment Audit (2026-10-16)

**Scope:** audit readiness of `D:/Singvox/Singvox` (web application `Singvox/web`) for
deployment, covering local source state, GitHub synchronisation, Supabase, database
schema, environment variables, large-asset/Vercel readiness, and a safe migration plan
for a new GitHub account.

**Audit-only.** No commit, push, pull, merge, rebase, remote change, branch change,
Supabase call, migration or deployment was performed. Nothing was discarded, and no
secret value is printed anywhere in this document.

Classification key used throughout: **VERIFIED PASS** · **VERIFIED ISSUE** ·
**NOT VERIFIED** · **NOT REQUIRED FOR CURRENT PROOF OF CONCEPT**.

---

## 1. Executive summary

1. **The local source is complete and it builds — but almost none of it is committed.**
   Local history is a single commit, `aeed61c6b7796b0201326be8c715861849142645`
   ("Add SignVox source, model pipeline, and project documentation", 2026-10-05), which
   contains 98 files and **no `web/`, no `avatar/`, no `experiments/`, no `data/`**.
   The React/Vite application, the avatar controller, the recognition-recovery work and
   the speed-optimization work all exist **only on disk, untracked**. — VERIFIED ISSUE
2. **`origin` is not behind the local commit; it is behind the work.** The remote
   `abonkweawah-png/SignVox-Avatar-Lab` (public) has exactly one branch `main` at
   `aeed61c…` — the same SHA as local HEAD. A recursive listing of that tree returns
   **zero** paths matching `web/` or `avatar/`. — VERIFIED ISSUE
3. **Supabase is not used by this project at all.** No client, no SDK dependency, no
   CLI config, no `SUPABASE_*` variable name, no migration file, no `.sql` file, and no
   auth/session/OAuth code exists in the repository. The current proof of concept has no
   database or authentication dependency, so no schema needs to be created for launch.
   — NOT REQUIRED FOR CURRENT PROOF OF CONCEPT
4. **The waiting list is a client-side `mailto:` flow, and it is currently disabled**
   because `VITE_CONTACT_EMAIL` is unset and no `.env` file exists anywhere. It fails
   safe (disabled, with an explanation, nothing stored). — VERIFIED ISSUE (config only)
5. **Deployment is blocked by asset size, not by code.** A CLI deploy from `web/`
   honouring the existing `.vercelignore` still uploads **493.8 MiB** (measured) against
   Vercel's documented **100 MB Hobby CLI source-upload limit**; and the same assets
   **cannot be committed to GitHub** either, because two of them exceed GitHub's 100 MiB
   per-file hard block. — VERIFIED ISSUE
6. **The build reaches outside `web/`.** `web/src` imports repo-root `avatar/controller/*`
   and `ai/sign-recognition/data/class_index_mapping.json` (15 import sites), so any
   deployment must include the repository root, not just `web/`. — VERIFIED ISSUE
7. Local production build passes in this audit (`npm run build` → exit 0), so the code
   itself is deployable; the blockers are packaging, tracking and configuration.
   — VERIFIED PASS

---

## 2. Local repository status

### 2.1 Git state (measured)

| Item | Value |
|---|---|
| Git root | `D:/Singvox/Singvox` |
| Current branch | `main` (tracks `origin/main`) |
| Local HEAD SHA | `aeed61c6b7796b0201326be8c715861849142645` |
| HEAD subject / date | "Add SignVox source, model pipeline, and project documentation" / 2026-10-05 21:45:59 +0100 |
| Commits in history | **1** (`git rev-list --count HEAD` = 1) |
| Tracked files | **98** |
| Stashes | none |
| Remotes | `origin` → `https://github.com/abonkweawah-png/SignVox-Avatar-Lab.git`; `old-origin` → `https://github.com/abonkweawah-png/Signvox.git` |
| Remote-tracking refs | `refs/remotes/origin/main` = `aeed61c…`; no `old-origin/*` refs exist |

Top level of the single commit (`git ls-tree HEAD --name-only`):
`.env.example`, `.gitignore`, `AGENTS.md`, `README.md`, `SIGNVOX_CONTEXT.md`, `ai`,
`app`, `docs`, `download_mediapipe_tasks.py`, `live_inference_tester.py`, `tools`.
`web` is absent. — VERIFIED ISSUE

### 2.2 Working-tree state

- **6 modified tracked files** (unstaged): `.env.example` (+4), `.gitignore` (+6),
  `ai/sign-recognition/training/dataloaders.py`, `app/App.tsx`, `app/package.json`,
  `docs/architecture/TECHNICAL_ARCHITECTURE.md`. All appear intentional; the
  `.gitignore` change adds `*.keystore` and `*.task`, and `.env.example` documents
  `VITE_CONTACT_EMAIL`. Nothing was discarded. — VERIFIED PASS
- **110 untracked top-level entries**, including the entire application. Untracked
  top-level groups and their entry counts: `tools` (50), `docs` (30), `app` (9),
  `ai` (6), `web` (1), `experiments`, `data`, `avatar`, `.venv_pilot`, `.agents`, plus
  scratch files (`find_data.py`, `inspect_*.py`, `tmp_check_onnx.py`,
  `tmp_check_scale.ts`, `tmp_verify_tip.js`, `check_hierarchy.py`).
  — VERIFIED ISSUE
- No `.env`, `.env.local`, `.env.development` or `.env.production` exists in `web/` or at
  the repository root (only the tracked template `.env.example`). — VERIFIED PASS

### 2.3 File-presence matrix (Task 1)

All paths below were checked with `test -f` **and** `git ls-files --error-unmatch`.

| Required item | Path | On disk | Git state |
|---|---|---|---|
| Launch report | `docs/LAUNCH_REPORT_2026-10-15.md` | present (13,541 B) | UNTRACKED |
| 79-class recovery audit | `docs/RECOGNITION_79_CLASS_RECOVERY_AUDIT.md` | present (22,623 B) | UNTRACKED |
| Speed-optimization report | `docs/RECOGNITION_SPEED_OPTIMIZATION_REPORT.md` | present (19,963 B) | UNTRACKED |
| Speed-optimization report (this audit) | `docs/PRE_DEPLOYMENT_AUDIT_2026-10-16.md` | created by this audit | UNTRACKED |
| Web app manifest | `web/package.json` | present (726 B) | UNTRACKED |
| Temporal sampler (new) | `web/src/lib/temporalSampler.ts` | present (8,811 B) | UNTRACKED |
| Model registry | `web/src/lib/modelRegistry.ts` | present (6,209 B) | UNTRACKED |
| Recognition gate | `web/src/lib/recognitionGate.ts` | present (2,721 B) | UNTRACKED |
| Inference implementation | `web/src/lib/inference.ts` | present (7,872 B) | UNTRACKED |
| Camera/recognition engine | `web/src/engine/useSignVoxEngine.ts` | present (34,925 B) | UNTRACKED |
| MediaPipe wrapper | `web/src/lib/mediapipe.ts` | present (5,673 B) | UNTRACKED |
| Vercel config | `web/vercel.json` | present (769 B) | UNTRACKED |
| Vercel ignore | `web/.vercelignore` | present (859 B) | UNTRACKED |
| Production GLB | `web/public/avatar/SignVox_Female_Competition_Prototype.glb` | present (49,701,152 B ≈ 47.4 MiB) | UNTRACKED, **and not gitignored** |
| 79-class graph | `web/public/spoter_v2_model.onnx` | present (121,801 B) | ignored by `*.onnx` |
| 79-class external weights | `web/public/spoter_v2_model.onnx.data` | present (187,711,488 B ≈ 179 MiB) | UNTRACKED, **and not gitignored** |
| Pilot graph | `web/public/spoter_pilot.onnx` | present (1,711,205 B) | ignored by `*.onnx` |
| Pilot external weights | `web/public/spoter_pilot.onnx.data` | present (187,580,416 B ≈ 178.9 MiB) | UNTRACKED, **and not gitignored** |
| ONNX runtime wasm | `web/public/onnxruntime/ort-wasm-simd-threaded.wasm` | present (14,239,897 B) | UNTRACKED |
| Avatar controller (imported by the app) | `avatar/controller/AvatarController.ts` | present (12,682 B) | UNTRACKED |
| Class-index mapping (imported by a test/build dep) | `ai/sign-recognition/data/class_index_mapping.json` | present | TRACKED |
| V2 scalars | `ai/sign-recognition/models/spoter_v2_groupnorm_scalars.json` | present | TRACKED |
| Landmark pipeline spec | `docs/ai-ml/LANDMARK_PIPELINE_SPEC.md` | present | TRACKED |

**Application scripts** (`web/package.json`) are present and correct: `dev` = `vite`,
`build` = `tsc -b && vite build`, `test` = `vitest run`. — VERIFIED PASS

`web/README.md` exists but still opens with "it does not load the SPOTER model or perform
sign inference", which is stale relative to the shipped app. — VERIFIED ISSUE (docs only)

### 2.4 `.gitignore` and `.vercelignore` review (Task 1)

`.gitignore` (tracked, currently modified) ignores, among others: `.env`, `.env.*`
(with `!.env.example`), `node_modules/`, `__pycache__/`, `venv/`, `.venv/`, `dist/`,
`build/`, `*.onnx`, `*.pt`, `*.pth`, `*.h5`, `*.tflite`, `*.pb`, `*.task`, `*.keystore`,
`*.log`, `*.bak`, plus generated dataset directories.

Direct `git check-ignore` results (the important ones):

| Path | Result |
|---|---|
| `.env`, `.env.local`, `web/.env.local` | ignored (`.gitignore:2,3`) |
| `web/node_modules`, `web/dist` | ignored |
| `ai/sign-recognition/models/spoter_pilot_checkpoint.pt` | ignored (`*.pt`) |
| `web/public/spoter_v2_model.onnx` | ignored (`*.onnx`) |
| **`web/public/spoter_v2_model.onnx.data`** | **NOT IGNORED** |
| **`web/public/avatar/SignVox_Female_Competition_Prototype.glb`** | **NOT IGNORED** |
| **`.venv_pilot/`** | **NOT IGNORED** |
| **`data/continuous_how2sign_val/videos`** | **NOT IGNORED** |
| **`web/node_modules_old/`** | **NOT IGNORED** (the pattern is `node_modules/`, which does not match `node_modules_old`) |
| **`web/package-lock.json.backup`** | **NOT IGNORED** |
| **`avatar/exports/*.blend`, `avatar/exports/*.glb`, `experiments/**/*.glb`** | **NOT IGNORED** (no `*.blend` or `*.glb` rule) |

Consequence: a naive `git add -A` would stage, among other things, 375 MiB of
`.onnx.data` **without their graphs** (a non-functional model pair), ~573 MiB of avatar
GLBs in `web/public/avatar/`, ~684 MiB under `avatar/` (Blender `.blend` + GLB exports),
~2.08 GiB of third-party How2Sign validation video under `data/`, and roughly 40,000
files of Python virtualenv under `.venv_pilot/` (including a 292 MiB `torch_cpu.dll`).
— VERIFIED ISSUE

`.vercelignore` (untracked, at `web/.vercelignore`) excludes 9 backup/experimental avatar
GLBs plus `node_modules`, `dist`, `*.log`, and documents that only the competition GLB,
the two models with their `.data`, and `public/onnxruntime/*` are runtime-required.
It works as intended for what it lists. — VERIFIED PASS (with the residual-size issue in §7)

---

## 3. GitHub remote synchronisation findings (Task 2)

All remote inspection was read-only (`git ls-remote`, `gh api`, `gh api --jq`). No fetch,
push, merge, rebase, remote change or commit was performed.

### 3.1 Configured remotes

```
origin       https://github.com/abonkweawah-png/SignVox-Avatar-Lab.git (fetch/push)
old-origin   https://github.com/abonkweawah-png/Signvox.git            (fetch/push)
branch.main.remote = origin ; branch.main.merge = refs/heads/main
```

`origin` matches the intended SignVox project described in the task (the Avatar-Lab
repository). — VERIFIED PASS

### 3.2 Remote state (measured)

```
$ git ls-remote origin
aeed61c6b7796b0201326be8c715861849142645        HEAD
aeed61c6b7796b0201326be8c715861849142645        refs/heads/main      (exit 0)
$ git ls-remote old-origin
(no refs returned, exit 0)
```

| Item | Value |
|---|---|
| Local HEAD | `aeed61c6b7796b0201326be8c715861849142645` |
| `origin` default branch | `main` |
| `origin` `main` SHA | `aeed61c6b7796b0201326be8c715861849142645` |
| Ahead / behind / diverged | **none of these — identical SHAs** |
| `origin` branches | one (`main`), unprotected |
| `origin` visibility | **public** (GitHub API `"visibility": "public"`, `"private": false`) |
| `origin` last push | 2026-10-05T20:48:19Z; repo size 222 KB; language Python |
| Authenticated account | `abonkweawah-png` (via `gh` CLI, keyring) with `admin`/`push` on `origin` |

Interpretation: `git status`-style "up to date" is true **and misleading**. The remote is
level with a commit that omits the entire application. — VERIFIED ISSUE

### 3.3 What the remote actually contains

`gh api repos/.../contents` (top level) returns exactly:
`.env.example`, `.gitignore`, `AGENTS.md`, `README.md`, `SIGNVOX_CONTEXT.md`, `ai/`,
`app/`, `docs/`, `download_mediapipe_tasks.py`, `live_inference_tester.py`, `tools/`.

Remote `docs/` contains only `ai-ml/`, `architecture/`, `testing/` — none of the launch,
recovery-audit or performance documents.

```
$ gh api "repos/abonkweawah-png/SignVox-Avatar-Lab/git/trees/main?recursive=1" \
    --jq '.tree[] | select(.path|test("web/|avatar/")) | .path'
(no output)
```

So on GitHub: **no React/Vite web app, no avatar controller, no recognition-recovery
work, no performance work, no model assets, no training/experiment source.** The remote
is the initial scaffold. — VERIFIED ISSUE

### 3.4 `old-origin`

`gh api repos/abonkweawah-png/Singvox` returns `default_branch: main`, `pushed_at:
2026-09-30T08:11:43Z`, and **`size: 0`**; `git ls-remote old-origin` returns no refs.
This is an **empty repository** (created but never pushed to). An unauthenticated
`curl` to the same API path returned 404 while the authenticated call returned data, so
the earlier "Not Found" observation is an artefact of that request, not evidence about
the repository. Neither remote should be treated as holding SignVox work.
— VERIFIED PASS (empty, not a risk)

Other repositories visible to the authenticated account (for awareness only, never to be
touched or consolidated into SignVox): `nkniels/KmerLife`, `abonkweawah-png/MOTOLOGA-MOBILE`.

### 3.5 Git LFS and large-file policy

No `.gitattributes` exists in the repository, so no Git LFS filters are configured;
GitHub's documented policy is a **50 MiB warning** and a **100 MiB hard block per file**,
with **Git LFS per-file limit 2 GB on Free** but only **10 GiB storage + 10 GiB
bandwidth per month** ([About large files on GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github),
[About Git LFS](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage),
[Git LFS billing](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)).

Because `web/public/spoter_v2_model.onnx.data` (179 MiB) and
`web/public/spoter_pilot.onnx.data` (178.9 MiB) exceed 100 MiB, **they cannot be pushed
to GitHub without LFS**, and the 47.4 MiB GLB is in the warning band. The model assets
need either LFS or external hosting; they are not required to be *in* the repository for
the app to run (see §7 and §9). — VERIFIED ISSUE

---

## 4. Supabase connection and Auth findings (Task 3)

Method: repository-wide inspection of `web/src`, `web/`, `app/`, `docs/`, `tools/`,
root files and all manifests. Whole-tree `du`/recursive `find` over the checkout is
impractical (the tree is ~10.9 GiB including virtualenvs), so searches were scoped to
source and configuration directories.

| Question | Finding |
|---|---|
| Supabase project URL configured in the app | **None.** `grep -ri supabase web/src` → no match. |
| Does anything point at project ref `aelfubrwzvwqurytobga`? | **No.** The string does not appear anywhere in the repository (searched source, config, docs, root files). |
| Supabase client initialisation | **Does not exist.** No `createClient`, no `@supabase/*` dependency in `web/package.json` or `app/package.json`, and no `@supabase` directory in `web/node_modules`. |
| Supabase CLI/local config | No `supabase/` directory, no `config.toml`, no `.supabase` link file, and no `SUPABASE_*` variable name in any config or in the process environment (checked by **name only**). |
| Is Supabase Auth used? | **No.** No sign-in, sign-up, session, OAuth, JWT or token handling exists in `web/src` (the only near-matches are the words "Signing Skeleton", "signing movements" and "signing avatar"). |
| Database tables or queries used by the app | **None.** The only network calls in `web/src` are the MediaPipe CDN/task URLs and same-origin model/GLB assets. There is no application API, no ORM, no SQL. |
| Waiting-list submission path | **Client-side `mailto:`** built in `web/src/pages/JoinPage.tsx`: it composes a `mailto:` link addressed to `VITE_CONTACT_EMAIL` and the visitor sends it from their own mail app. Nothing is POSTed, and nothing is stored. |
| Are auth/DB features needed for launch? | **No.** — NOT REQUIRED FOR CURRENT PROOF OF CONCEPT |
| Live Supabase project state (tables, migrations, auth users) | **NOT VERIFIED.** Verifying it needs an authenticated Supabase session/token; none exists on this machine, no Supabase CLI is installed, and the audit forbids touching the project. The previously reported "no tables / no migrations / zero users" state therefore cannot be re-confirmed from here, and the local application does not depend on it either way. |

Because there is no Supabase dependency, **no tables, buckets, policies or auth settings
should be created for this proof of concept**, and the project ref mentioned in the task
should be treated as unrelated to the shipped app until a concrete requirement appears.
— VERIFIED PASS (no hidden dependency)

One privacy-relevant note in favour of the current design: the Join page states, and the
code confirms, that no video, landmarks or biometric data leave the device, and the
waiting-list page collects no camera data. Any future Supabase integration for
waiting-list storage would change that data-protection posture and should be a deliberate,
documented decision (see §8).

---

## 5. Database schema and migration comparison (Task 4)

- **Local migration files:** none. `find` for `*.sql` (depth-limited across the source
  tree) and for any `migrations` directory returned nothing; no Prisma, TypeORM, Knex or
  Drizzle config exists. — VERIFIED PASS
- **Live migration history:** NOT VERIFIED (no Supabase credentials/CLI; see §4).
- **Expected application tables:** none required. The proof of concept has no
  persistence: camera frames are processed in-browser and discarded, watch-list enquiries
  go out by email from the visitor's own client, and the avatar GLB is a static asset.
- **RLS / policies:** not applicable (no tables owned by this application). If Supabase is
  introduced later, RLS must be enabled with per-user ownership policies — the standing
  rule is that a service-role key must never reach the browser.
- **Mismatch that would block launch:** none, because nothing in the app queries a
  database. — VERIFIED PASS
- **Destructive migrations:** none exist locally, so none can be applied. — VERIFIED PASS

---

## 6. Environment-variable readiness (Task 5)

No `.env` file of any kind exists in the checkout, so **every** variable below is
currently unset and each falls back to the default in code. Variable *names* were read
from `.env.example` and from `import.meta.env.*` usage; no values are printed anywhere.

### 6.1 Variables the web application actually reads

| Variable | Purpose | Needed for | Configured locally? | Needed in Vercel? | Class |
|---|---|---|---|---|---|
| `VITE_CONTACT_EMAIL` | Team inbox that receives Join-page enquiries via the visitor's `mailto:` | runtime UX (inlined at build) | **No** (absent → Join form disabled) | **Yes, to enable the waiting list** | Public config |
| `VITE_AVATAR_GLB_URL` | Override host for the production GLB | build-time | No (default `/avatar/SignVox_Female_Competition_Prototype.glb`) | Only if the GLB is hosted off-Vercel | Public config |
| `VITE_SPOTER_V2_URL` | Override host for the 79-class model (`.data` resolved as `${url}.data`) | build-time | No (default `/spoter_v2_model.onnx`) | Only if models are hosted off-Vercel | Public config |
| `VITE_SPOTER_PILOT_URL` | Override host for the 3-class pilot model | build-time | No (default `/spoter_pilot.onnx`) | Only if models are hosted off-Vercel | Public config |
| `VITE_MEDIAPIPE_WASM_ROOT` | MediaPipe Tasks wasm root | build-time | No (defaults to `cdn.jsdelivr.net/...@0.10.14`) | Recommended: pin to an immutable, verified host | Public config |
| `VITE_MEDIAPIPE_POSE_MODEL_URL` / `_HAND_` / `_FACE_` | MediaPipe task bundles | build-time | No (defaults to `storage.googleapis.com/mediapipe-models/...` pinned versions) | Recommended: pin/self-host before public launch | Public config |
| `VITE_MEDIAPIPE_DELEGATE` | `GPU` (default) or `CPU` landmarker delegate | build-time | No (defaults to `GPU` with automatic CPU fallback) | Optional | Public config |
| `VITE_ORT_WASM_PROXY` | Set to `1` to run ONNX in the ORT web worker | build-time | No (default off) | Leave unset (see §7) | Public config |

Evidence: `grep -rno "import.meta.env.VITE_[A-Z_0-9]*" web/src` yields exactly those ten
names, and all ten are `VITE_`-prefixed.

**ONNX Runtime wasm asset path has no environment override.** `web/src/lib/inference.ts`
hardcodes the runtime paths — the loader as a Vite-resolved URL
(`src/onnxruntime/ort-wasm-simd-threaded.mjs?url`, emitted to `dist/assets/ort-wasm-simd-threaded-<hash>.mjs`)
and the binary as `/onnxruntime/ort-wasm-simd-threaded.wasm` — resolved to absolute URLs at
runtime. Consequence for deployment: those two paths must exist in the deployment (they are
shipped by `vite build` and by `public/onnxruntime/`), and moving the runtime elsewhere would
require a code change rather than a variable. The four other `ort-wasm-*` variants in
`public/onnxruntime/` are never loaded by the app.

### 6.2 Variables that exist only in the root template

`.env.example` (tracked) also lists `API_BASE_URL`, `AI_SERVICE_URL`, `MODEL_ENDPOINT`,
`DATABASE_URL`, `AUTH_KEY`. **Nothing in the repository reads any of them** (no
`process.env` reference, no server code in the shipped app). Treat them as scaffold
placeholders, not requirements. — NOT REQUIRED FOR CURRENT PROOF OF CONCEPT

### 6.3 Missing configuration that could break the public demo

| Missing variable | Effect if unset |
|---|---|
| `VITE_CONTACT_EMAIL` | Join page renders with the form disabled and a visible explanation; no enquiry can be sent. Functional but inert. |
| `VITE_MEDIAPIPE_*` | Works today via third-party CDNs. For a public launch this is a documented risk: the pipeline silently depends on `cdn.jsdelivr.net` and `storage.googleapis.com` availability, and the repo's own guidance is to pin checksum-verified assets. |
| (Nothing else) | The app has no other external service, so no other missing variable can break the demo. |

### 6.4 Secret-exposure analysis

- Every application variable is `VITE_*`, therefore **inlined into the client bundle at
  build time and publicly readable**. No secret may ever be stored in one. Nothing secret
  is stored in one today. — VERIFIED PASS
- `.gitignore` covers `.env` and `.env.*` while keeping `!.env.example` tracked, so local
  secrets would not be committed. No `.env` exists to leak. — VERIFIED PASS
- Risk to guard against: the root template's `DATABASE_URL` / `AUTH_KEY` names invite the
  future mistake of adding e.g. `VITE_SUPABASE_URL` + a service-role key. Any Supabase
  integration must keep secrets server-side and expose at most the public anon key
  (and, for this static POC, nothing at all).
- Operational note for the migration in §9: this machine has `gh` authenticated as
  `abonkweawah-png` (token in the OS keyring, scopes `gist`, `read:org`, `repo`,
  `workflow`) and Git uses the `manager` credential helper, so a push from here acts as
  that account. Token values were neither printed nor stored by this audit.

---

## 7. Deployment and large-asset readiness (Task 6)

### 7.1 Vercel configuration (present, and largely correct)

`web/vercel.json`: `buildCommand` `npm run build`, `outputDirectory` `dist`,
`installCommand` `npm install`, `framework` `vite`, a catch-all rewrite
`/(.*) → /index.html`, and immutable `Cache-Control` headers for `/onnxruntime/(.*)`,
`/avatar/(.*)` and `/spoter_(.*)` (the last also with `Access-Control-Allow-Origin: *`).
The model caching rules are correct for how the app fetches assets, including the
`${modelUrl}.data` sidecar. — VERIFIED PASS

Hardening note: the catch-all rewrite means a **missing or truncated asset path returns
`index.html` with HTTP 200** instead of a 404, which would turn a failed 179 MiB model
download into an opaque ONNX parse error. Narrow the rewrite to non-asset paths.
— VERIFIED ISSUE (hardening, not launch-blocking)

### 7.2 Upload / deployment size (measured)

`web/.vercelignore` is applied; `dist` and `node_modules` are excluded by the tooling.

| Scenario | Files | Size |
|---|---:|---:|
| CLI deploy from `web/` **honouring `.vercelignore`** | 110 | **493.8 MiB** |
| CLI deploy from `web/` **without** the ignore file | 119 | 958.4 MiB |
| Whole checkout, excluding `.venv_pilot` and `node_modules_old` | 37,208 | **10.9 GiB** |
| Local build output `web/dist` after `npm run build` | 32 | 982.7 MiB |

Largest files in the 493.8 MiB upload: `public/spoter_v2_model.onnx.data` 179.0 MiB,
`public/spoter_pilot.onnx.data` 178.9 MiB, `public/avatar/SignVox_Female_Competition_Prototype.glb`
47.4 MiB, then four `public/onnxruntime/*.wasm` variants totalling ~82 MiB (the app only
loads `ort-wasm-simd-threaded.wasm`, 13.6 MiB).

Vercel's documented limit: **"When using the CLI to deploy, the maximum size of the source
files that can be uploaded is limited to 100 MB for Hobby and 1 GB for Pro"**, and the
build-troubleshooting report flags files over 100 MB ([Limits](https://vercel.com/docs/limits),
[Build troubleshooting](https://vercel.com/docs/deployments/troubleshoot-a-build)). Git-based
deployments are documented separately and no numeric source limit is stated for them, but
the docs do not guarantee exemption either. There is **no documented per-file maximum for
static build output**.

Conclusion: the ~500 MB source-upload problem the task refers to is **measured at 493.8 MiB
and is not resolved** — `.vercelignore` roughly halved it (958.4 → 493.8 MiB) but the
remainder is still ~5× the documented Hobby CLI budget, and the same files cannot simply be
moved into the repository instead (§3.5). — VERIFIED ISSUE (launch blocker for Vercel Hosting
as configured)

### 7.3 Build behaviour and cross-directory dependency

`npm run build` (audit run, from `web/`): **exit 0**, "✓ 77 modules transformed",
`dist/assets/index-C5qcbcrO.js` 1,482.45 kB (gzip 405.15 kB), `dist/assets/index-DV70o4TQ.css`
26.71 kB, built in 2m 4s. Only the standard chunk-size advisory was emitted.
— VERIFIED PASS

However, `web/src` imports **outside** the `web/` directory:

```
web/src/engine/useSignVoxEngine.ts:29  from '../../../avatar/controller/AvatarController'
web/src/components/AvatarDiagnostic.tsx:3-6  '../../../avatar/controller/{AvatarController,avatarCapabilities,HandModel,AnatomicalAnchors}'
web/src/tests/camera_pipeline.test.ts:15  '../../../ai/sign-recognition/data/class_index_mapping.json'
(+ 11 more in web/src/tests/*)
```

Therefore a deployment whose root is only `web/` **cannot build**: it needs repo-root
`avatar/controller/*` and `ai/sign-recognition/data/class_index_mapping.json` present. The
Vercel project must either set the Root Directory to the repository root with the build
command pointed at `web/`, or otherwise ensure those paths are uploaded.
— VERIFIED ISSUE (configuration)

### 7.4 Model loading, caching and cold start

- Cache headers for models/GLB/wasm are correct (§7.1). — VERIFIED PASS
- The ONNX worker (`VITE_ORT_WASM_PROXY`) **remains disabled by default**, as the task
  states: it measured 6.3 vs 2.8 landmark observations/s in development but cannot boot
  from the production bundle (ORT derives its worker URL from its own `import.meta.url`,
  which the bundler collapses onto the application chunk; the worker then dies with
  "document is not defined" and, because ORT's WASM init is one-shot, the in-page retry
  cannot recover in that page). Reproduced against `vite preview`. The flag stays
  available for development only. — VERIFIED PASS (documented, deliberate)
- Cold start measured in the preceding performance pass: ONNX model initialisation
  17.6 s on an origin that had not cached the 179 MiB `.data` file (3.4–3.8 s warm),
  camera readiness 4.0–6.8 s, and 60-frame window readiness ~7.4 s. On a large-asset
  deployment the first-visit cost is dominated by that download. — VERIFIED ISSUE
  (mitigations in §10)
- Client-side route fallback (`/(.*) → /index.html`) supports the five hash routes; the
  app is a hash-router SPA, so no server routing is needed. — VERIFIED PASS

### 7.5 Waiting-list flow

Functional as designed but **inert until `VITE_CONTACT_EMAIL` is set**: the form,
validation, `mailto:` composition and review-before-send UI exist and are wired, and with
the variable unset the form is hidden behind a clear "inbox not connected" notice and
sends nothing. Setting the variable (locally and in Vercel) is the only step required to
activate it. — VERIFIED ISSUE (configuration)

---

## 8. Security risks and missing configuration

| # | Risk | Assessment |
|---|---|---|
| 1 | Large binary assets would be committed by a careless `git add -A` (375 MiB of `.onnx.data` **without** graphs, ~573 MiB of GLBs, ~684 MiB under `avatar/`, 2.08 GiB of downloaded dataset). | **High.** `.gitignore` is asymmetric: `*.onnx` is ignored but `*.onnx.data` is not, and there is no `*.glb`/`*.blend` rule. Fix before any staging. |
| 2 | `.venv_pilot/` (~40k files, includes a 292 MiB native DLL) is not ignored. | **High.** Would dwarf every other change and may exceed push limits. |
| 3 | `data/` holds third-party How2Sign validation video (1,845 files, 2.08 GiB). Publishing it would be a redistribution/licensing problem as well as a size problem. | **High.** Must stay local. |
| 4 | Secret leakage into the client bundle via a `VITE_*` variable. | **Currently none** (no secret is set anywhere). Standing rule: never put a Supabase service-role key, DB URL or token into any `VITE_*` variable. |
| 5 | Public repository exposure: `origin` is **public**, and its description says it is the source of truth. Once the app is pushed there, source and any committed assets become public. | **Medium–High.** Decide intentionally whether the code should be public before publishing; the audit recommends a private repository first. |
| 6 | Third-party CDN dependency for MediaPipe wasm + task bundles (`cdn.jsdelivr.net`, `storage.googleapis.com`). | **Medium.** Availability/supply-chain dependency; the repo's own guidance is to pin immutable, checksum-verified URLs before production. |
| 7 | `gh`/git credentials present on this machine, and `origin` grants `admin`/`push`. Any accidental push goes live immediately to a public repo. | **Medium.** Keep the migration dry-runs read-only and confirm the target repository is private before the first push. |
| 8 | Models served from the deployment itself: a missing/truncated `.data` yields `index.html` (HTTP 200) under the catch-all rewrite rather than a 404, obscuring the failure. | **Low–Medium.** Narrow the rewrite; consider a preload + integrity check. |
| 9 | No CI configuration is present in the repository, so the verified test suite is not enforced before deploys. | **Low.** Optional improvement. |
| 10 | Stale documentation: `web/README.md` still claims the web app "does not load the SPOTER model or perform sign inference". | **Low.** Docs only; misleading for a new contributor. |

No secret, token, password, private key or full `.env` content appears in this report, and
none was written to any file.

---

## 9. Safe new-repository migration plan (Task 7)

Objective: move the verified local project to a **new (private) repository under a
different GitHub account or email**, preserving the intended source tree, existing
history where practical, documentation, configuration examples, all local uncommitted
work, and a verified story for the large assets — while never publishing things that must
stay private or that cannot legally/size-wise be published.

### 9.1 Recommended method: new empty repository + push existing history, then commit in reviewed batches

1. **Create the new repository empty.** Do not initialise it with a README, licence or
   `.gitignore` — an auto-generated initial commit would make the push non-fast-forward
   and tempt a force-push. An empty repository accepts the existing history cleanly.
   Make it **private**.
2. **Fix `.gitignore` first, before staging anything.** Add at minimum:
   `.venv_pilot/`, `.venv*/`, `data/`, `web/node_modules_old/`, `web/package-lock.json.backup`,
   `*.blend`, `*.blend1`, `*.data` (or a precise rule for `web/public/*.onnx.data`), and a
   deliberate decision for `*.glb` (track only the production GLB if it is committed at
   all). Keep `*.pt`, `*.onnx`, `*.task`, `.env`, `.env.*`.
3. **Add a second remote for the new repository instead of replacing `origin`** —
   e.g. `git remote add new-origin <new-url>` — so the audited checkout keeps pointing at
   the current remote and no existing remote is modified. (Remote addition is *not* done by
   this audit; it is the owner's call at migration time.)
4. **Push the existing history first** (`git push new-origin main`). This carries the
   scaffold commit `aeed61c…` and preserves history; no force is needed against an empty
   remote.
5. **Then commit the untracked work in reviewable batches**, verifying the staged set
   before each commit (`git status --short`, `git diff --cached --stat`, and a size check
   that no staged file approaches 100 MiB):
   - Batch A — application source: `web/` **except** `web/public/*.onnx*`,
     `web/public/avatar/*`, `web/dist`, `web/node_modules*`; plus repo-root
     `avatar/controller/`, `avatar/package.json`, and `docs/`, `tools/`, `app/` source.
   - Batch B — documentation and configuration examples: `README.md`, `AGENTS.md`,
     `SIGNVOX_CONTEXT.md`, `.env.example`, `web/vercel.json`, `web/.vercelignore`,
     `web/README.md` (corrected), and the numbered audit/launch/performance docs.
   - Batch C — model/asset strategy (choose one, see §9.2).
6. **Verify before pushing anything:** confirm the target repository is private, confirm
   `git log --stat` contains no `.env`, no `.venv*`, no `data/`, no `.blend`, no checkpoint,
   and confirm every pushed file is well under 100 MiB (GitHub hard-blocks at 100 MiB).
   A `git push --dry-run` is a safe read-only check for size/ref problems.
7. **Never force-push and never overwrite an existing remote** without separate explicit
   approval. Do not delete `origin` or `old-origin`; `old-origin` is an empty repository and
   can simply be ignored.
8. **Clean up the working tree deliberately, not blindly.** The scratch files at the
   repository root (`find_data.py`, `inspect_ch41.py`, `inspect_fbx.py`, `inspect_glb.py`,
   `inspect_onnx.py`, `check_hierarchy.py`, `tmp_check_onnx.py`, `tmp_check_scale.ts`,
   `tmp_verify_tip.js`) are uncommitted scratch; decide per file whether it belongs in
   history (some are genuinely useful diagnostics). Removing them would be a
   *user* decision, not an audit action.

### 9.2 The large-asset decision (the only genuinely hard part)

| Option | Git LFS | External hosting (recommended) |
|---|---|---|
| Mechanics | `.gitattributes` for `*.onnx.data`, `*.glb`, `*.pt`; commit pointers | Upload models/GLB to object storage/CDN; set `VITE_SPOTER_V2_URL`, `VITE_SPOTER_PILOT_URL`, `VITE_AVATAR_GLB_URL` |
| Cost/limits | Free: 2 GB per file, but only 10 GiB storage + 10 GiB bandwidth per month → a 179 MiB model downloaded by ~50 visitors can exhaust a month | Storage/CDN billed separately; Vercel Blob documents up to 5 TB per file (files >512 MB are not cached) |
| Repo weight | ~420 MiB of history for the runtime assets alone | Repo stays small (source ≈ a few MiB) |
| Vercel fit | Still leaves the ~494 MiB upload problem for the build unless assets are also excluded | Solves both GitHub *and* Vercel size limits, and is already supported by code (`VITE_*` overrides exist precisely for this) |
| Recommendation | Acceptable interim if the repo must be self-contained | **Preferred**: keep source in Git, keep binaries in object storage |

Whichever is chosen, the 9 backup GLBs and the three unused `ort-wasm-*` variants should be
excluded from both GitHub and the deployment upload.

### 9.3 Files that must never be pushed

`.env` / `.env.*` (all variants; `.env.example` is the only intended exception) · any
token, credential, service-role key or private key · `.venv/`, `.venv_pilot/`, `venv/` ·
`node_modules/`, `web/node_modules_old/`, `dist/`, `build/` · `__pycache__/`, `.pytest_cache`,
`.mypy_cache`, `.ruff_cache` · `data/` (third-party How2Sign validation video) · model
checkpoints (`*.pt`, `*.pth`, `*.onnx`, `*.onnx.data`, `*.h5`, `*.tflite`, `*.pb` unless a
deliberate LFS decision is taken) · Blender `.blend`/`.blend1` files and experimental GLBs ·
`.agents/` local agent state if it is not intended for sharing · OS/IDE files (`.DS_Store`,
`Thumbs.db`, `.vscode/`, `.idea/`) · `*.log`, `*_backup*`, `package-lock.json.backup` · and
anything from the unrelated repositories (`nkniels/KmerLife`, `MOTOLOGA-MOBILE`) that may be
present locally.

---

## 10. Prioritised action list

### Blockers (must be resolved before a public deployment)

| # | Action | Why (evidence) |
|---|---|---|
| **B1** | Commit the actual application: `web/`, `avatar/`, the new `docs/`, `tools/`, `app/` changes — 110 untracked entries plus 6 modified tracked files | Remote `main` = local `aeed61c…` but contains **zero** paths under `web/` or `avatar/`; GitHub has nothing of the app |
| **B2** | Fix `.gitignore` (`.venv_pilot/`, `data/`, `web/node_modules_old/`, `*.blend`, `*.data`, GLB policy) **before** any `git add -A` | `git check-ignore` shows `.onnx.data`, `*.glb`, `*.blend`, `.venv_pilot/`, `data/`, `node_modules_old/` all currently stageable; one command would try to stage ~3.9 GiB |
| **B3** | Choose and implement the asset strategy: external object storage for the two models + GLB (using the existing `VITE_SPOTER_*` / `VITE_AVATAR_GLB_URL` overrides) **or** Git LFS plus a paid Vercel plan | CLI upload measured at **493.8 MiB** vs documented **100 MB** Hobby CLI cap; two files exceed GitHub's **100 MiB** hard block |
| **B4** | Make the Vercel project able to build: include repo-root `avatar/` and `ai/sign-recognition/data/class_index_mapping.json` (Root Directory = repo root, build in `web/`) | 15 import sites escape `web/`; a `web/`-only upload cannot resolve them |
| **B5** | Set `VITE_CONTACT_EMAIL` locally and in Vercel, or accept a disabled waiting list at launch | `web/src/pages/JoinPage.tsx` disables the form when it is unset; no `.env` exists |
| **B6** | Decide the visibility of the target repository and keep it private until the first reviewed push | `origin` is **public** today; a mistaken push of the full tree would publish third-party dataset content and large binaries |

### Optional improvements

| # | Action |
|---|---|
| O1 | Narrow the `/(.*)` rewrite so missing assets return 404 instead of `index.html`, protecting the 179 MiB model load path |
| O2 | Pin MediaPipe wasm/task assets to immutable, checksum-verified URLs via `VITE_MEDIAPIPE_*` |
| O3 | Exclude `web/bench/` and `web/node_modules_old/` from deployment uploads |
| O4 | Add model preload + a download-progress affordance to reduce the ~17.6 s first-visit cold start |
| O5 | Move model weights and GLBs out of `web/public/` entirely so the repository and the build output stop carrying ~420 MiB |
| O6 | Truncate/ignore the unused `ort-wasm-*` variants (only `ort-wasm-simd-threaded.wasm` is loaded) |
| O7 | Correct `web/README.md` (it still says the web app performs no inference) |
| O8 | Add CI (build + `vitest`) so the verified suite is enforced before deploys |
| O9 | Migrate the ONNX worker to a purpose-built module worker to recover the measured 6.3 vs 2.8 observations/s in production (verify against `vite preview` first) |
| O10 | If persistence is ever wanted, adopt Supabase deliberately (server-side secrets, RLS, per-user ownership) and document the data-protection change |

### Verification summary for the audit itself

| Check | Command | Result |
|---|---|---|
| Production build | `cd web && npm run build` | **exit 0** — 77 modules, `index-C5qcbcrO.js` 1,482.45 kB, 2m 4s |
| Test suite | `cd web && npx vitest run` | **29 files, 164 tests passed, 0 failures** (209.6 s); zero failure markers in the log |
| Remote comparison | `git ls-remote origin` / `gh api` | read-only; `main` = `aeed61c…` on both sides |
| Supabase presence | scoped greps over source/config/docs/manifests | no match anywhere |
| Secret material | filename check + `env` **names only** | no `.env*` present; no `SUPABASE_*`/`VERCEL_*`/`GITHUB_*` names except the local tooling token holder |
| Working tree unchanged by this audit | `git status --short -- web` | still the single untracked entry `?? web/`, exactly as at audit start |

Both build and tests were run in this audit against the current tree; no source file was
modified by the audit.

---

## 11. Audit declaration

No commit, push, pull, merge, rebase, fetch, remote change, branch change, tag, stash,
reset, clean or checkout was executed. No Supabase operation of any kind was performed and
no migration was applied. Nothing was deployed — neither a preview nor an anonymous
deployment. No secret, token, key or full `.env` value was printed or written to disk by
this audit. The only file created is this report.

**This audit stops here and waits for authorization before any repository, remote,
Supabase or deployment change.**
