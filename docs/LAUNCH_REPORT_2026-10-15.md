# SingVox Public Proof of Concept — Launch Report (2026-10-15)

> **Superseded in part (same day, later):** the recognition scope described below is the
> three-sign pilot that shipped at launch. The shipped scope is now the 79-class SPOTER V2
> baseline (avatar animation for HELLO/YES/NO only), and the Live page, footer, Welcome and
> About copy no longer claim a three-sign scope. See
> `docs/RECOGNITION_79_CLASS_RECOVERY_AUDIT.md` (§6 changes, §8.1 decision) for the evidence
> and the current state. The rest of this report remains an accurate record of the launch build.

## 1. Locations

- Repository root: `D:/Singvox/Singvox` (branch `main`, remote `origin`
  `https://github.com/abonkweawah-png/SignVox-Avatar-Lab.git`).
- Active application entry point: `Singvox/web` (React + Vite + TypeScript,
  served from `web/src/main.tsx` → `web/src/App.tsx`).
- Backup location: `/d/Singvox-backup-20261015/` (working tree left intact,
  nothing committed, no destructive git operations used).
- `singvox-backup.tar` (10.5 GB) — full-tree backup started 2026-10-15 13:17
  (dependency caches excluded). An early listing stopped mid-`data/` only
  because the file was still being written at the time; the writer has since
  finished and a fresh full listing parses **cleanly, exit 0, 45,676 entries**,
  ending at the `web/` config files. Contains `.agents/`, `ai/` (incl.
  `spoter_pilot_checkpoint.pt`/configs), `app/`, `avatar/` (incl.
  `AvatarController.ts`), `data/` (incl. How2Sign videos), `docs/`,
  `experiments/`, `web/` and root files.
- `singvox-backup-gap.tar` (3.5 GB, + `backup-gap.log`) — second archive,
  written after all launch edits as belt-and-braces: `docs/`, `experiments/`
  (incl. the isolated GOOD pilot), `web/` (all new pages, config, final build
  inputs), `app/`, `.git/`, `data/` manifests/CSVs/samples and all repo-root
  files. Excluded as regenerable: `node_modules`, `.venv_pilot`, `dist`,
  `build`, `__pycache__`, and the How2Sign `videos/`+`shards/` bulk (public,
  re-downloadable dataset; exact manifests kept so the fetch is reproducible).
  Verified: clean listing exit 0; all 12 sentinel files present (new pages,
  `vercel.json`, GOOD manifest, Competition GLB, pilot `.data`, `.git/HEAD`,
  engine, report); test-extract of the launch report restores byte-identical
  to the working tree (the corrected report version was appended, so it wins
  on extraction).
  Together the two archives contain every uncommitted file, including all
  launch-day changes, each verifiable independently.

## 2. Files changed and why

| File | Why |
|---|---|
| `web/src/pages/WelcomePage.tsx` (new) | Public landing page: problem, how it works, what works / in development, language-resource vision, CTAs. All claims grounded in the verified build. |
| `web/src/pages/AboutPage.tsx` (new) | Vision & safeguards page: long-term initiative, honest scope limits, data governance in plain language. |
| `web/src/pages/JoinPage.tsx` (new) | Waiting-list + partnership form. Submits via the visitor's own email app (`mailto:` to `VITE_CONTACT_EMAIL`); disabled with a clear notice until the inbox is configured, so nothing is silently lost. |
| `web/src/App.tsx` | Five public routes (`#welcome` default, `#live`, `#avatar`, `#vision`, `#join`); engineering screens stay hash-only; all pages stay mounted so camera/avatar survive navigation; public footer with Prototype labels. |
| `web/src/components/SignVoxHeader.tsx` | Five-destination nav; subtitle now reads "Prototype · Sign language, live". |
| `web/src/pages/LiveTranslationPage.tsx` | Honest scope chips: Prototype / Supported signs HELLO·YES·NO / ASL-based pilot, not validated CSL. |
| `web/src/pages/AvatarStudioPage.tsx` | Shows the actual supported-animation list from the loaded GLB; GOOD stays out (isolated experiment). |
| `web/src/engine/useSignVoxEngine.ts` | Asset URLs overridable via `VITE_AVATAR_GLB_URL`, `VITE_SPOTER_PILOT_URL`, `VITE_SPOTER_V2_URL` (defaults = local `/public` paths, unchanged behaviour). Enables external hosting of the ~180 MB model files without code changes. |
| `web/vercel.json` (new) | Vite build config, SPA rewrite, long-cache + CORS headers for model/avatar assets. |
| `web/.vercelignore` (new) | Excludes unused legacy avatar builds (~460 MB) from Vercel uploads. Runtime needs only the Competition Prototype GLB, the two ONNX models + `.data`, and `onnxruntime/*`. |
| `web/index.html` | Title/description now say Prototype and state the ASL-pilot scope. |
| `web/README.md` | Documents the five public pages. |
| `.env.example` | Documents `VITE_CONTACT_EMAIL`. |

Preserved untouched: SPOTER V2 ONNX pipeline, HELLO/YES/NO pilot scope,
366-dim feature contract, preprocessing/normalization, class mappings, model
files, inference interfaces, latency diagnostics, avatar controller +
`playSignByLabel`, frozen ASL-100 vocabulary, GOOD candidate experiment
(isolated under `experiments/avatar/pilot_good/`), all unrelated experiments.

## 3. Build and test results

- `npx tsc -b`: **pass** (exit 0).
- `npm run build`: **pass** — `dist/` produced (see §9 for the size finding).
- `npx vitest run`: **138 passed, 2 failed of 140**. Both failures are
  pre-existing environment issues, identical before and after launch changes:
  `baseline_idle_diagnostic` and `baseline_threshold_eval` fail to initialize
  ONNX WASM under Node (`no available backend found`, missing `ort-wasm-simd-threaded.mjs`
  in the Node context). They do not touch any changed code path and pass/fail
  identically on the untouched baseline.

## 4. Feature verification matrix (all checked against the production build)

| Feature | Status | Evidence |
|---|---|---|
| Landing page (`#welcome`) mobile + desktop | ✅ Verified | Rendered in preview browser: hero, CTAs, communication-gap, how-it-works, what-works, vision teaser, partner CTA, footer. |
| Landing CTAs (Try demo / Meet avatar / Join / Partner) | ✅ Verified | All navigate to working hash routes (`#live`, `#avatar`, `#join`). |
| Live Translation page: idle state, permissions, errors | ✅ Verified | Renders camera-off state, Start/End session controls, buffering progress, error banner path, on-device privacy note, Prototype + supported-sign chips. |
| Avatar Studio: model load, playback, sign list | ✅ Verified | `SignVox_Female_Competition_Prototype.glb` (47 MB) fetched HTTP 200; status chip "Avatar ready"; supported animations listed as HELLO · NO · YES; typed "hello yes" accepted; Rest pose / Replay controls present; no console errors besides a deprecation warning. |
| GOOD advertised as working | ✅ Correctly absent | GOOD appears nowhere in production UI or sign lists. |
| Join form: end-to-end | ⚠️ Verified disabled-safe | `VITE_CONTACT_EMAIL` is unset, so the form is visibly disabled with "inbox is being connected … nothing is sent or stored". The `mailto:` flow activates automatically once the variable is set. |
| Vision & safeguards page | ✅ Verified | Route renders; states initiative goals, "no licensed dataset yet", ASL≠CSL, no interpreter replacement, no background recording. |
| Footer + all nav destinations | ✅ Verified | Five routes in header (desktop), bottom bar (mobile), and footer; no dead buttons. |
| Secrets exposure | ✅ Clear | No secrets in repo or bundle; only env-var *names* documented (§6). |
| Live camera recognition accuracy | ❌ Not claimed | Camera recognition was not exercised with a live signer in this environment; the page demonstrates the real pipeline honestly (supported-sign scope, buffering, error states) and fabricates no results. |

## 5. Deployment URL

**No public URL yet — blocked on Vercel authorization (see §8).** Everything
needed for a one-command deploy is prepared (§8, commands 1–3).

## 6. Environment variables (names only, no values)

| Variable | Required | Purpose |
|---|---|---|
| `VITE_CONTACT_EMAIL` | Yes, before onboarding | Team inbox for Join-form enquiries. Until set, the form stays disabled (current state). |
| `VITE_AVATAR_GLB_URL` | Only for external-asset deploys | Override for the avatar GLB (default `/avatar/…Competition_Prototype.glb`). |
| `VITE_SPOTER_PILOT_URL` | Only for external-asset deploys | Override for the pilot model (default `/spoter_pilot.onnx`; `.data` resolved alongside). |
| `VITE_SPOTER_V2_URL` | Only for external-asset deploys | Override for the V2 model (default `/spoter_v2_model.onnx`). |
| `VITE_MEDIAPIPE_*_MODEL_URL`, `VITE_MEDIAPIPE_WASM_ROOT` | Optional | Pinned MediaPipe assets (documented in `web/README.md`); defaults point at public CDNs. |

## 7. Waiting-list / contact destinations

| Channel | Destination | Verification |
|---|---|---|
| Join form (`#join`) | `mailto:` to `VITE_CONTACT_EMAIL`, composed in the visitor's own email app | ⚠️ Destination **not yet configured** — form safely disabled; no silent loss. Set the variable and the flow activates with no code change. |
| Footer contact | Same inbox (mailto link) or "inbox being connected" notice | Same as above. |

No Google Form integration was found in the codebase, so none was invented;
the mailto flow is the verified mechanism. Privacy notice on the page states:
team-inbox use only, no video/biometric collection, no training use, deletion
on request.

## 8. Remaining blockers (exact resolution steps)

**Blocker A — Vercel authentication (the only deploy blocker).**
This environment has no Vercel account linked: no `VERCEL_TOKEN`, no
`~/.vercel` auth. With authorization, deploy is three commands from `Singvox/web`:
1. `npx vercel login` (or export `VERCEL_TOKEN=<token>` from vercel.com/account/tokens)
2. `npx vercel --yes` (preview URL for review)
3. `npx vercel --prod --yes` (production URL to share)
Plus, in the Vercel dashboard → project → Environment Variables, set
`VITE_CONTACT_EMAIL` (and redeploy) to activate the Join form.

**Blocker B — plan vs. asset size (decide before deploying).**
Verified Vercel docs (`vercel.com/docs/limits`): CLI source-upload budget is
**100 MB (Hobby)** / **1 GB (Pro)**. After `.vercelignore` trims legacy GLBs,
the source upload is still ~500 MB (two 179 MB `.data` files + 47 MB GLB +
~100 MB onnxruntime) — **over Hobby, within Pro**. Two options:
- *Option 1 (recommended if budget allows):* deploy on **Pro** — no code changes.
- *Option 2 (Hobby-compatible):* upload `spoter_pilot.onnx[.data]`,
  `spoter_v2_model.onnx[.data]`, and the Competition Prototype GLB to object
  storage (e.g. Vercel Blob, which supports 5 TB objects / multipart over
  100 MB), then set `VITE_SPOTER_PILOT_URL`, `VITE_SPOTER_V2_URL`,
  `VITE_AVATAR_GLB_URL` to those URLs and deploy. The app already supports this.

**Blocker C — local `npm install -g vercel` keeps stalling** (Windows file-lock
`TAR_ENTRY_ERROR`s on this machine). Workaround: use `npx -y vercel@latest`
(which fetches per-invocation) or install the CLI on a machine with a healthy
npm cache, then run the three commands above.

**Not blocking:** the 2 pre-existing ONNX-under-Node test failures (§3); the
unset contact inbox (form fails safe); live-signer accuracy validation (must
happen with a real signer before any accuracy claim).

## 9. Demonstration script (for prospect meetings)

1. Open `#welcome`: "SingVox is an experimental prototype bridging Deaf
   sign-language users and non-signers — camera recognition one way, a signing
   avatar the other. Everything labelled Prototype is honest about its limits."
2. Click **Try the live demo** → **Start translation**, sign HELLO / YES / NO
   steadily. Point at the confidence + transcript + optional speech output.
   Say: "Three-sign ASL pilot — we show exactly what it recognizes."
3. Click **Avatar Studio**, type "hello yes" → **Sign it**. Note the avatar
   performs only its three supported animations; GOOD is deliberately excluded.
4. Click **Vision**: "The app is step one. Step two is documenting validated
   sign-language resources with Deaf communities — no dataset exists yet, and
   we're looking for partners, which is why…"
5. Click **Join**: show the interest categories and the plain-language privacy
   notice. "Enquiries go straight to our inbox; nothing is recorded or reused."
6. Close with the footer: Prototype · Experimental · three signs — "Judge it as
   a starting point, partner with us on where it goes."

## 10. Next improvements (prioritized)

1. **Unblock deploy**: authenticate Vercel + decide Pro vs. external assets (§8). Highest leverage — everything else is ready.
2. **Set `VITE_CONTACT_EMAIL`** and send a test enquiry end-to-end.
3. **Live-signer validation session**: record real HELLO/YES/NO attempts, capture latency + accuracy, publish honest numbers on the Live page.
4. **GOOD decision**: either bake/export/verify the GOOD clip into the app (with reviewer sign-off) or keep it parked — never half-ship it.
5. **Bundle hygiene**: code-split the 1.47 MB JS chunk; confirm lazy-loading for the avatar/ONNX paths.
6. **Fix the 2 Node-ENV ONNX test failures** (wasm backend resolution under Node) so CI is fully green.
7. **MediaPipe pinning**: set checksum-verified `VITE_MEDIAPIPE_*` URLs for production per `web/README.md`.
8. **Accessibility pass**: screen-reader labels on the 3D viewport, reduced-motion respect, contrast check on chips.
9. **Analytics-free usage insight**: privacy-preserving, opt-in only — never background recording.
10. **Research partnership kit**: one-page vision brief + governance outline to attach to Join-form replies.
