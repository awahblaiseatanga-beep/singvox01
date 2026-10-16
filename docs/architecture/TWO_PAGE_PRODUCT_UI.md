# SignVox web — two-page product UI

Status: implemented and verified in the browser. The recognition, avatar and
diagnostic engines are unchanged; only their presentation moved.

## Routes

| Hash | Screen | Audience |
| --- | --- | --- |
| `#live` (default) | Live Translation | product |
| `#avatar` | Avatar Studio | product |
| `#diagnostics` | Former diagnostic dashboard (dark, internal) | engineering |
| `#avatar-diagnostic` | Existing avatar rig test suite (`AvatarDiagnostic`) | engineering |

Only the first two appear in navigation. The engineering screens stay reachable by
hash and are deliberately absent from the nav and from any in-product link.

## File structure

```
src/
  App.tsx                     shell: hash routing, app bar, bottom nav, both pages kept mounted
  engine/useSignVoxEngine.ts  the whole pipeline (camera, MediaPipe, features, buffer,
                              inference, stabilizer, transcript, speech, avatar, profiling,
                              diagnostics) extracted verbatim from the old App.tsx
  pages/LiveTranslationPage.tsx
  pages/AvatarStudioPage.tsx
  components/SignVoxHeader.tsx   app bar, light (product) + dark (diagnostics) variants
  components/DiagnosticDashboard.tsx  the old dense dark dashboard, moved verbatim
  components/HandOverlay.tsx     unchanged
  lib/uiStatus.ts             user-facing status labels + friendly camera error copy
  lib/*                       unchanged pipeline modules
```

Both product pages stay mounted and are toggled with `hidden`, so the camera
stream, landmark pipeline, sequence buffer, recognition state and the loaded GLB
avatar all survive navigation (no model reload, no state loss). The single avatar
renderer is bound to the surface that currently owns it (`useSignVoxEngine(avatarSurface)`),
so moving between the product shell and `#diagnostics` re-binds instead of orphaning
the canvas.

## What was removed from the user interface (not from the codebase)

Model selector and model/JIT parameters, profiling panels and cold-start timings,
landmark/feature/buffer counters, tensor snapshots, synthetic ONNX test, diagnostic
frame capture, the Phase 1.1 consistency lab and trial recorder, and the avatar test
suite entry point. All of it still runs and is reachable on the engineering routes.

## Honesty rules the UI follows

- The translation area shows only committed signs from the existing stabilizer, and an
  empty state ("Your translation will appear here when a sign is recognized.") otherwise.
- The pilot vocabulary is what the pipeline reports — no ASL-100 claims, and the paused
  79-class baseline is not selectable from the product UI.
- Avatar Studio lists the animation clips actually loaded in the controller
  (`ASL_HELLO`, `ASL_NO`, `ASL_YES` in the current GLB) and marks any other word as
  "not available" instead of inventing a gesture.
- Text-to-sign plays supported words in sequence using real clip durations.

## Responsive behaviour

Mobile-first: one column with a floating bottom nav below 768 px; the same two
destinations move into the app bar from `md` upward. The camera viewport keeps its
16:9 box and the existing mirrored preview, and the pages switch to two columns when
there is real horizontal room (`lg`, or `sm` + landscape).

Verified numerically in the browser (viewport widths 320 / 375 / 768 / 1024 / 1440 /
1600 and landscape 844×390) for: no horizontal overflow, correct single/two-column
tracks, 16:9 camera boxes, ≥44 px button targets, safe-area padding on the bottom nav,
avatar canvas matching its container exactly, and the accessibility tree showing only
product controls.
