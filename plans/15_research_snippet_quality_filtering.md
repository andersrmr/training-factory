# Phase 2 – Snippet Quality Filtering (Boilerplate + Keyword Density)

## Problem Statement
During web enrichment, some extracted snippets are boilerplate or access-gate text rather than useful training evidence. Observed example from Microsoft Learn includes snippets such as:
- "This browser is no longer supported."
- "Upgrade to Microsoft Edge..."
- "Access to this page requires authorization..."

These snippets dilute research quality for governance and best-practices training.

## Approach (B): Filter Boilerplate + Score/Prioritize Snippets
Implement deterministic snippet-quality logic in extraction:
- Filter known boilerplate/access-gate patterns using case-insensitive substring matching.
- Score each candidate snippet using heading relevance, keyword presence, keyword density, and text length.
- Penalize boilerplate and very short low-signal snippets.
- Rank by score (descending), tie-break by original document order, and keep top snippets.
- Keep behavior stdlib-only and deterministic.

## Acceptance Criteria
- Web mode enrichment returns semantically useful snippets for governance/best-practices topics.
- Boilerplate/gate snippets (browser support, authorization prompts, etc.) are excluded.
- Research flow passes intent keywords (topic tokens + query-plan intent keywords) into extraction.
- Tests cover boilerplate removal and confirm useful ALM/governance snippets remain.
