# Phase 2 – Step 2F2: QA Enforcement of Authority Tier Usage

## Purpose
- Move from “citations exist” to “citations are sufficiently authoritative” for governance and best-practices training.
- Require curriculum to cite Tier A/B sources where appropriate.

## Scope
In scope:
- Extend deterministic QA checks to enforce minimum authority-tier usage in curriculum citations.
- Add a simple topic-sensitivity heuristic (`governance` / `security` / `risk` / `ALM` style keywords) to determine strictness.
- Add offline tests demonstrating pass/fail behavior.

Out of scope:
- No slide citation enforcement yet.
- No claim-level semantic verification yet.
- No changes to research scoring/enrichment beyond reading existing `authority_tier` fields.

## Proposed Rules
- Always require at least one Tier A or at least two Tier B sources to be cited in `curriculum.references_used`.
- If topic contains any of: `governance`, `security`, `risk`, `compliance`, `policy`, `ALM`, `lifecycle`:
  - require at least one Tier A cited.
- Otherwise:
  - allow (`Tier A >= 1`) OR (`Tier B >= 2`).

## Acceptance Criteria
- QA fails when curriculum cites only Tier C/D sources.
- QA passes when curriculum cites required Tier A/B sources under the rule.
- `pytest -q` is green.
