# Agent Instructions

AI development agents working within the SignVox repository MUST stringently adhere to the following principles:

1. **Read `SIGNVOX_CONTEXT.md` first.** Always review the established long-term vision before attempting major functionality changes.
2. **Inspect the existing repository before altering code.** Do not overwrite core modules without running audits (via `list_dir`, `view_file`) first.
3. **Do not introduce arbitrary dependencies.** Do not pull in large, generic libraries strictly because they exist. Each dependency must be justified for our particular constraints.
4. **Do not rewrite functioning elements.** Refactor only when there are systemic scaling constraints or unresolvable technical debt.
5. **Acknowledge and respect technical reality (Do not fake AI).** If an AI inference loop currently evaluates 2 frames per second or only translates 15 words reliably, explicitly enforce it. 
6. **Isolated experiments remain isolated.** Testing untested models should live exclusively within `experiments/` and verified rigorously before merging into `ai/`.
7. **Document major architectural permutations.** Significant integrations (e.g. implementing MediaPipe over native vision) must be justified as a Markdown log under `docs/decisions/`.
8. **Enforce broad testing suites.** Any stable feature must come accompanied by respective automated validation parameters.
9. **Prioritize end-user PII and Hardware Streams.** Real-time camera interactions expose severe privacy vulnerabilities. Protect data structures appropriately.
10. **Measure rather than assume.** Do not assume processing efficiency; run constraints tests to prove a framework scales to edge environments natively.
11. **Pause for clarification if a directive is ambiguous or risks integrity.** Never assume structural commitments blindly.
12. **Update these living documents when context evolves.** If architecture takes pivot points, ensure context remains the singular truth artifact.
