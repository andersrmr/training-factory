# Phase 2 – Step 2B: Wire Research into Graph + Grounded Brief Output

## Purpose
Ensure brief generation is grounded in `research.context_pack` and emits explicit citations to `src_*` sources.

## Scope
In scope:
- Add `research` to graph state and execution order: `START -> research -> brief`
- Update brief interface to `generate_brief(request, research)`
- Update `schemas/brief.schema.json` to require:
  - `references_used: string[]` (non-empty)
  - `key_guidelines: [{ guideline, rationale, sources[] }]` with non-empty `sources`
- Add or adjust tests to validate grounded brief output
- Preserve offline determinism in tests

Out of scope:
- No changes to `curriculum` / `slides` / `lab` / `templates` agents in this step
- No QA changes yet (research QA is deferred)
- No bundle schema changes yet (unless strictly required)

## Acceptance Criteria
- Pipeline runs offline end-to-end.
- Tests enforce strict grounding:
  - `references_used` is non-empty
  - each `key_guideline` has at least one source id
- All tests are green.

## Next Step
Add research QA checks (tier counts and keyword coverage) and route back to `research` on failure.
