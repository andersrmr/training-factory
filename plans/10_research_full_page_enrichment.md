# Phase 2 – Step 2D: Research Full-Page Enrichment (Fetch + Extract + Better Snippets)

## Purpose
Improve governance and best-practices training quality by enriching research from fetched page content (not only search snippets) when `--web` is enabled.

## Scope
In scope:
- Add fetch+extract utility for HTTP retrieval and HTML text extraction
- Update research agent to optionally enrich sources when `request["research"]["web"] == True`
- Keep snippet count and `context_pack` size bounded
- Keep tests offline by monkeypatching fetch/extract behavior (no network)

Out of scope:
- No embeddings or vector DB
- No curriculum/slides citation propagation yet
- No YouTube transcript support
- No changes to research QA rules unless strictly necessary

## Implementation Notes
- Extract heading and body text from `H1/H2/H3`, `P`, and `LI` with a stdlib-safe extractor; allow optional `bs4` path if already available
- Fetch only top `K` sources (target range: 3–5), preferring Tier A/B sources first
- Add `retrieved_at` metadata and set snippet `loc` values from heading/paragraph index positions

## Acceptance Criteria
- With `web=True`, research sources include extracted snippet text from HTML (not just search snippets)
- Offline tests pass and explicitly confirm enrichment behavior
- All tests are green

## Next Step
Step 2E: propagate citations through curriculum and slides generation.
