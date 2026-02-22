# Phase 2 – Topic-Anchor Queries + Product-Aware Scoring

## Problem
Power BI topics can over-rank Power Platform ALM pages because governance/lifecycle keyword overlap can outweigh product-specific relevance.

## Solution
1. Add product-aware anchor queries in `query_plan` (for example `site:learn.microsoft.com/power-bi`) so retrieval is steered toward product-relevant sources earlier.
2. Add small deterministic score adjustments by URL path and product detection so product-aligned pages rank above adjacent-product pages unless the topic explicitly asks for ALM/lifecycle.

## Acceptance
- For topics containing "Power BI", top sources include `/power-bi/` pages.
- `/power-platform/` pages are not over-prioritized for Power BI unless ALM/lifecycle is explicitly mentioned.
- Query plan includes product-aware anchor queries near the top.

## Tests
- Verify anchor queries appear in `query_plan` and product detection is set.
- Verify deterministic scoring adjustment changes ordering so product-aligned URLs rank above adjacent-product URLs in offline tests.
