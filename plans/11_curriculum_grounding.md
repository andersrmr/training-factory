# Phase 2 – Step 2E: Propagate Grounded Citations into Curriculum

## Purpose
- Extend grounding beyond the brief by requiring curriculum outputs to reference research source IDs (`src_###`).
- Improve governance/best-practices credibility by maintaining traceability from `research -> brief -> curriculum`.

## Scope
In scope:
- Update curriculum agent to accept research and/or brief references and emit citations:
  - `references_used: string[]` (non-empty)
  - `modules[].sources: string[]` (non-empty)
- Update curriculum schema accordingly.
- Update bundle schema if needed to keep packaging validation passing.
- Add offline tests that enforce curriculum citations are valid research source IDs.

Out of scope:
- No slide citation requirements yet.
- No QA changes beyond minimal schema/validation needed.
- No changes to research scoring or research QA rules.

## Acceptance Criteria
- Curriculum includes non-empty `references_used` and module `sources`.
- All cited IDs exist in `research.sources[].id`.
- `pytest -q` passes offline.

## Next Step
- Step 2F: add QA checks ensuring curriculum citations exist and are consistent with brief/research.
