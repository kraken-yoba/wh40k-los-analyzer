# Work Log

## 2026-06-16

- Created and hardened the product design spec for deterministic Warhammer 40k terrain/deployment extraction, base-aware 2D LOS, heatmaps, exposure analysis, and local GUI workflows.
- Ran adversarial reviewer subagents for extraction/PDF-CV, LOS/math, GUI trust workflow, and verification/reproducibility; integrated their findings into the spec.
- Added infrastructure requirements for a public-ready repository, source-PDF policy, CI, and tooling.
- Created an implementation plan for project infrastructure.
- Set the end-to-end product goal: deterministic official-PDF extraction, canonical validation, base-aware LOS, GUI workflows, browser UX tests, security/code review, and independent reviewer approval.
- Pivoted the infrastructure from Node/Vite to a Python-only FastAPI-served GUI after deciding the project does not need Node for the first release.
- Verified the Python-only checkpoint with Ruff, mypy, pytest, and whitespace checks.
- Ran consultant subagents for extraction/data spine, LOS/math, and UX/release evidence. Key adjustment: implement a synthetic canonical data spine and fixture-first GUI before official-PDF extraction.
- Split verification intent into public, GUI, and full-local gates so public CI stays copyright-safe while final release can require the pinned official-PDF cache.
