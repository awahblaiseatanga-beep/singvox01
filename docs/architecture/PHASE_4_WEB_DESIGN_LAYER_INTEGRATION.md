# Phase 4 — Web Design Layer Integration (Tailwind v4 + SignVox design tokens)

Status: **integration complete, verified** (build + tests + live browser probes).
Scope: `Singvox/web` only. Recognition, avatar and diagnostic logic were not changed.

## What was integrated

The SingVox design language from the AI Studio prototype (claymorphic / Material 3 look)
was brought into the real web app as a **design layer**, without touching the behaviour of
the diagnostic shell:

| Area | Change |
| --- | --- |
| Tooling | `tailwindcss@4.3.3` + `@tailwindcss/vite@4.3.3` added to `devDependencies` (both pinned exactly) |
| Build | `vite.config.ts` plugins are now `[react(), tailwindcss()]`; the `vitest` test config and the `three` alias are unchanged |
| Tokens | `src/styles.css` gained `@theme` tokens (M3 + clay palette, Inter/mono font stacks, `--radius-clay`) so utilities such as `bg-primary-bright`, `text-secondary-container`, `rounded-clay` exist |
| Components layer | Ported `clay-card-light`, `clay-card-low`, `clay-btn-gradient`, `clay-chip`, `clay-floating-bar`, plus new `svx-appbar` / `svx-brand-mark` / `svx-chip[-ok|-warn]` / `svx-icon-btn` / `svx-icon` classes |
| Typography | `index.html` loads Inter + Material Symbols Outlined and carries the real page title, description and `theme-color` |
| App shell | New `src/components/SignVoxHeader.tsx` — branded sticky app bar with live camera-status and avatar-status chips (tone derived from the status string) and a transcript jump button; mounted above `<main>` in `App.tsx` |
| Anchor | The stabilized-recognition section got `id="signvox-transcript"` so the header button has a target |

### Why `4.3.3` exactly

Requirement: keep Vite 5. The `@tailwindcss/vite` peer range was read from the registry for
every 4.x release published so far — `^5.2.0 || ^6` for the earliest versions and
`^5.2.0 || ^6 || ^7 || ^8` for the newest batch. So `4.3.3` supports the installed
`vite@5.4.11`, but a future `^4.x` could drop Vite 5, which is why both packages are pinned
exactly instead of `^`. React (18.3.1), Vite (5.4.11) and TypeScript (5.6.3) are untouched —
verified after install.

## Cascade notes (found empirically, worth knowing before the screen migration)

Tailwind v4 emits `@layer theme, base, components, utilities`. Three interactions mattered:

1. **The legacy app CSS is still unlayered.** Rules like `:root`, `main`, `button`, `.grid`,
   `.snapshot` were left exactly as they were, because unlayered CSS beats *every* Tailwind
   layer. That is why the existing dark diagnostic shell looks unchanged — but it also means a
   Tailwind utility placed on an element that a legacy element-selector already styles (most
   notably `button { padding: 11px 15px }`) will lose. Migrating those rules into
   `@layer base` / `@layer components` is the first task of the screen-migration phase.
2. **Google Fonts ships an unlayered `.material-symbols-outlined { font-size: 24px }` rule.**
   Because it is third-party and unlayered, no layered utility can override it (confirmed in
   Chromium). The design layer therefore uses its own `.svx-icon` class with the same font
   settings, which utilities *can* size (`text-[13px]` etc. verified at runtime).
3. **`@layer components` loses to `@layer utilities`** for ordinary custom classes
   (`svx-chip` + `text-white` resolved to white, `svx-appbar` + `static` resolved to static),
   which is the behaviour the ported clay classes rely on.

Source scanning is pinned (`@import "tailwindcss" source(none); @source "../src";`) so Tailwind
never walks `web/node_modules_old`, which is not covered by any ignore rule.

## Verification

- `npm run build` (`tsc -b && vite build`) — **passes**; emitted CSS grew from a 1.6 kB
  hand-written sheet to 13.01 kB with generated utilities.
- `npm test` — **136 passed, 2 failed**. Both failures are **pre-existing and unrelated**:
  re-running `baseline_idle_diagnostic.test.ts` and `baseline_threshold_eval.test.ts` with the
  original Tailwind-free `vite.config.ts` reproduces them exactly (an ONNX wasm path that
  resolves to `D:\src\onnxruntime\...` under the node test environment, and a forensic
  stabilizer assertion).
- Live dev server (`vite` on `127.0.0.1:5188`): app bar computed styles confirmed sticky +
  `blur(18px)`, brand gradient, green `Avatar: Ready` / amber `Camera stopped` chips,
  icons at 18/13/13/20 px, Inter + Material Symbols both reported as loaded, no console
  errors, all requests 200.

## Known issues / carry-over

- **`onnxruntime-node` is an undeclared dependency.** Three ad-hoc node scripts under
  `src/tests` (`check_onnx.ts`, `analyze_baseline_drop.ts`, `audit_baseline_accuracy.ts`)
  import it, and `tsc -b` typechecks `src/**`, so `npm run build` only works while that
  package happens to be installed locally. This install pruned it; it was restored with
  `npm install --no-save onnxruntime-node`. Any future `npm install` will prune it again.
  Fix properly by either declaring it as a devDependency or moving those scripts out of the
  typechecked tree.
- The header's transcript button is a no-op until the recognition section mounts
  (`stableState` is null before the first sign), which is when the badge would show a count.
- The clay *light* classes are available but unused: the diagnostic panels still use their
  original dark look.

## Verified backup

`D:\signvox-backup-2026-10-14\Singvox` holds a full copy taken before these edits:
111,493 files / 14,808,046,745 bytes, matching the source file count exactly
(robocopy exit 1 = "files copied").

## Next phase (suggested)

Migrate the screens onto the design layer: move the legacy element/class rules into the
proper cascade layers, then restyle the camera panel, avatar panel, prediction cards and the
transcript strip with the clay/M3 tokens so the light-theme design language from the prototype
is realised end to end.
