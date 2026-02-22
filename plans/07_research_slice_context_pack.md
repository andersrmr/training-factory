# Phase 2 – Step 2A: Research Slice + Context Pack (Offline-safe)

## Purpose
Introduce a research slice that produces a small ranked source set and a bounded `context_pack` string for downstream agents, while remaining deterministic and offline-testable.

## Scope
In scope:
- New `src/training_factory/agents/research.py` with `generate_research(request) -> dict`
- Deterministic authority scoring and ranking
- `schemas/research.schema.json`
- Pytests for scoring behavior and `context_pack` shape (no network)

Out of scope (not done in this step):
- No `graph.py` rewiring
- No `brief.py` signature changes
- No brief schema updates or citation enforcement
- No package schema changes

## Data Model
Canonical research output shape:
- `query_plan`
- `sources[]` with fields:
  - `id`
  - `title`
  - `url`
  - `domain`
  - `publisher`
  - `authority_tier`
  - `score`
  - `snippets` (list of short evidence strings)
- `context_pack` (bounded string for downstream prompt context)

`request["research"]` controls provider selection (`--web`, `--search-provider`), but tests remain offline by default.

## Deterministic Scoring Rubric
- Domain allowlist tiering: assign `authority_tier` via deterministic A/B/C/D mapping.
- Keyword overlap: score intent keyword matches against source title/snippet text.
- Diversity: cap per-domain representation in final selected sources.
- Freshness: apply optional boost only when reliable metadata exists; otherwise neutral.

## Acceptance Criteria
- `generate_research()` returns schema-valid payload.
- `context_pack` is non-empty for known topics.
- Tests pass without network access.
- Existing pipeline behavior is unchanged in this step.

## Next Step
Step 2B: wire a research node into the graph and update brief generation to cite sources via `key_guidelines`.
