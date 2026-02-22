# Training Factory – Architecture v2

## 1. System Overview
- Goal: generate grounded, governance-focused training bundles from `topic` + `audience` inputs.
- Output is oriented to best-practices and risk-aware technical governance training.
- Execution model is a deterministic, testable, multi-agent LangGraph pipeline.

## 2. End-to-End Pipeline
Current graph flow:
- `research`
- `research_qa` (bounded retry x1)
- `brief` (grounded, citation-aware)
- `curriculum` (citation-enforced)
- `slides`
- `lab`
- `templates`
- `qa` (bounded retry x1)
- `package`

Retry/state controls:
- `research_revision_count` tracks bounded research retry.
- `revision_count` tracks bounded slides retry after QA fail.
- Retries are bounded and deterministic.

## 3. Research Layer

### 3.1 SearchProvider Abstraction
- `SearchProvider` protocol defines search contract.
- `SimpleFallbackSearchProvider` provides deterministic curated results.
- `SerpApiSearchProvider` provides broader live recall.
- Registry selection uses `request["research"]` (`web`, `search_provider`).

### 3.2 Query Planning
- Product detection via `_detect_product`.
- Product-aware topic-anchor queries.
- Governance/best-practice expansion queries.
- `query_plan` includes detected `product`.

### 3.3 Deterministic Scoring
- Authority tiers: A/B/C/D.
- Keyword-overlap scoring.
- Preferred-domain boost.
- Product-aware URL path boost/penalty.
- Diversity rule: max 2 sources per non-Tier-A domain.
- Top 8 sources selected.

### 3.4 Full-Page Enrichment
- `fetch_url()` retrieves page HTML.
- `extract_snippets()` extracts candidate snippets.
- Boilerplate filtering removes low-signal/gate text.
- Keyword-density scoring prioritizes relevant snippets.
- Snippets capped at `<=4` per source.
- `context_pack` has a fixed size cap.

## 4. Grounding & Citation Enforcement

### 4.1 Brief
- `references_used` required.
- `key_guidelines[].sources` required.
- Citation IDs filtered/validated to existing `research.sources` IDs.

### 4.2 Curriculum
- `references_used` required.
- `modules[].sources` required.
- Citation IDs validated against `research.sources`.

## 5. QA Layer

### 5.1 Research QA
- Minimum source count check.
- Authority threshold checks.
- Keyword coverage ratio check.
- Domain concentration check.
- Sensitive-topic detection.
- Tier-A enforcement for sensitive topics.

### 5.2 Bundle QA
- Slides/lab alignment checks.
- Template presence/alignment checks.
- Citation validity check.
- Authority-tier compliance check.

## 6. Evaluation Framework
- Phase A: manual cases × modes.
- Phase B: lightweight eval harness with CSV summary.
- Phase C: adversarial sensitive-topic testing.
- Modes:
  - M1: offline baseline.
  - M2: web + fallback.
  - M3: web + serpapi.

Quality/testing posture:
- 30+ passing tests.
- Deterministic offline fixtures.
- CSV summary metrics include tier counts, keyword coverage, domain diversity, and QA status.

## 7. Design Principles
- Deterministic over probabilistic behavior.
- No vector DB.
- No embeddings (v2).
- Governance-first orientation.
- Authority-tier prioritization.
- Explainable scoring.
- Bounded retries.
- Fully schema-validated outputs.

## 8. Known Limitations (Explicit)
- Relevance is keyword-based (no semantic retrieval).
- Keyword coverage ratio can overestimate quality.
- Vendor-document bias is possible.
- Generated curriculum may remain framework-heavy with limited operational depth.

## 9. Version 2 Status
- v2 achieves stable, grounded, governance-aware training generation.
- Product-aware retrieval is implemented.
- Sensitive-topic enforcement is implemented.
- Ready for Phase 3 (deeper operationalization and/or semantic enhancements).
