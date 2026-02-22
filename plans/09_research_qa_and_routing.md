# Phase 2 – Step 2C: Research QA + Routing (Bounded Retry)

## Purpose
Add deterministic checks to ensure research sources are sufficiently authoritative and relevant.  
If research quality is insufficient, retry research with a bounded loop before generating content.

## Scope
In scope:
- Add `research_qa` (or `qa_research`) evaluation between `research` and `brief`
- Add `research_revision_count` (separate from slides `revision_count`) with bounded retry (e.g., `< 1`)
- Add routing:
  - if research QA fails and retry is available -> route back to `research`
  - else proceed to `brief` (or fail-safe proceed with warning status)

Out of scope:
- No changes to slides/lab/templates QA in this step (except minimal wiring if required)
- No vector DB and no embeddings

## Proposed Deterministic Checks
- Minimum authority tier counts (A/B thresholds)
- Keyword coverage against intent/topic tokens in source title/snippet text
- Domain diversity constraints
- Optional minimum source-count threshold

## Acceptance Criteria
- Offline tests cover pass/fail routing behavior for research QA
- No network calls in tests
- `pytest -q` is green

## Next Step
Integrate research QA results into the final QA report and/or bundle output.
