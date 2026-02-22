# Phase 2 – Step 2F1: QA Checks for Citation Presence + Validity

## Purpose
- Extend QA to verify grounding signals exist and are internally consistent:
  - `curriculum.references_used` present
  - `modules[].sources` present
  - all cited ids exist in `research.sources[].id`

## Scope
In scope:
- Update QA agent to accept `curriculum` + `research` inputs (minimal signature change).
- Add deterministic checks for citation presence and validity.
- Update `qa.schema.json` only if strictly necessary.
- Update graph QA node call accordingly.
- Add offline tests that demonstrate QA fails when citations are missing or invalid.

Out of scope:
- No tier-based requirements yet (deferred to 2F2).
- No slide citation enforcement yet.
- No changes to research agent or scoring.

## Acceptance Criteria
- QA status fails when curriculum citation fields are missing or invalid.
- QA status passes when citations are valid.
- `pytest -q` is green.
