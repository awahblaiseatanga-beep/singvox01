# SignVox Web Vision Diagnostic

This is the active browser implementation path for SignVox Phase 1. It runs
camera landmark extraction locally in a modern browser; it does not load the
SPOTER model or perform sign inference.

## Run locally

```powershell
cd web
npm install
npm run dev
```

Use HTTPS in deployed environments because browser camera permission requires a
secure context. `localhost` is treated as secure for development.

## Product pages

The app has four public pages: landing (`#welcome`, default), **Live Translation**
(`#live`), **Avatar Studio** (`#avatar`) and **Join** (`#join`, waiting list and
partnership enquiries). The engineering screens
remain reachable by hash only (`#diagnostics` for the old diagnostic dashboard,
`#avatar-diagnostic` for the avatar rig test suite) and never appear in navigation.
All public pages stay mounted so the camera stream, recognition state and loaded
avatar survive navigation. See `docs/architecture/TWO_PAGE_PRODUCT_UI.md` for the
original two-page product history.

## Design layer

The UI uses the shared SignVox design layer: Tailwind v4 via the `@tailwindcss/vite`
plugin (pinned to `4.3.3`, the newest release whose peer range still accepts Vite 5)
plus the clay/Material-3 tokens and `svx-*` shell classes defined in `src/styles.css`.
Icon glyphs use the local `.svx-icon` class rather than Google's
`.material-symbols-outlined`, because that third-party rule is unlayered and would
override every Tailwind utility. See
`docs/architecture/PHASE_4_WEB_DESIGN_LAYER_INTEGRATION.md` for the cascade notes and
remaining migration work.

## Model artifact strategy

The `.task` files remain ignored and are not committed. Development defaults in
`src/lib/mediapipe.ts` point at versioned MediaPipe-hosted assets. Before a
production deployment, configure `VITE_MEDIAPIPE_*_MODEL_URL` and
`VITE_MEDIAPIPE_WASM_ROOT` to immutable, checksum-verified assets on the
deployment's approved artifact host. The host must serve the same task bundles
validated for the web pipeline; no automatic model download or substitution is
performed by the repository.

## Frozen feature contract

The output is exactly 366 float32 values:

- `0:63`: left hand, 21 × XYZ
- `63:126`: right hand, 21 × XYZ
- `126:291`: pose, 33 × interleaved `[X, Y, Z, visibility, presence]`
- `291:366`: face landmarks 0–24, XYZ

V2 spatial scalars apply only to XYZ values. Pose visibility and presence stay
at their original interleaved offsets.
