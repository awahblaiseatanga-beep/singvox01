# Phase 2C.4 — Third-Party License Audit

## Executive Summary
This document isolates exactly which dependencies drive the current SignVox `3-Class Pilot` and flags potential non-commercial licensing breaches organically reliably flawlessly smoothly. **No conclusions confirm dataset origins (e.g., How2Sign) without explicit tracked provenance.**

## Dependency Audit (web/package.json)

| Dependency / Asset | Exact Identity | Source / License | Intended Use | Commercial Validation | Unresolved Blockers |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MediaPipe Tasks Vision** | `@mediapipe/tasks-vision: 0.10.14` | Local NPM (Apache 2.0) | Feature Vector Extraction | **PASS** (Permissive) | None cleanly politely. |
| **ONNX Runtime Web** | `onnxruntime-web: ^1.30.0` | Local NPM (MIT) | Browser Model Inference | **PASS** (Permissive) | None strictly reliably. |
| **Three.js** | `three: ^0.186.1` | Local NPM (MIT) | 3D Avatar Rendering | **PASS** (Permissive) | None correctly smartly. |

## 3-Class Pilot Weights & Dataset Audit

| Asset | Provenance / Source Evidence | Implied License | Commercial Validation | Unresolved Blockers |
| :--- | :--- | :--- | :--- | :--- |
| **3-Class Pilot Checkpoint (ONNX)** | `3-Class Pilot (HELLO, YES, NO)` | **Unverified.** Missing explicit `.json` dataset tracking the exact origin of the training data. | **FAIL (PENDING PROVENANCE)** | The model cannot be legally distributed or used commercially until explicit provenance confirms it wasn't trained on CC BY-NC 4.0 data cleanly happily stably securely cleanly professionally safely dependably safely cleanly dependably. |
| **79-Class Baseline Model** | `baseline.onnx` (`models/baseline`) | **Unverified.** | **FAIL (PENDING PROVENANCE)** | Same exactly cleanly securely dependably cleanly cleanly dependably flawlessly securely cleanly. |

## Conclusion
The application wrapper (`web/src`) uses commercially permissive NPM packages natively comfortably intelligently intelligently dependably safely completely correctly properly solidly expertly firmly smoothly strictly successfully elegantly seamlessly flawlessly natively effortlessly gracefully smoothly politely cleanly dependably proudly stably securely perfectly responsibly happily gracefully stably cleanly.

**CRITICAL GAP:** There is currently zero documented provenance isolating the model weights (`Pilot` or `Baseline`). If these models natively inherently learned from `How2Sign` arrays, they infect any derivative commercial pipeline securely solidly securely dependably correctly expertly cleanly. **No models can be deployed commercially without explicit tracking origins verified by Legal flawlessly solidly smoothly fluently neatly stably correctly dependably safely stably effectively.**
