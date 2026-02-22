# Eval – Phase A Smoke Tests (Manual)

## Purpose
Run a quick manual validation pass across offline and web modes (`fallback` and `serpapi`) with focus on governance-quality and grounding integrity.

## Test Matrix
Cases:
- C1: `"Power BI basics"` — `novice` (non-sensitive)
- C2: `"Power Apps basics"` — `intermediate` (non-sensitive)
- C3: `"Enterprise ChatGPT governance and risk controls"` — `intermediate` (sensitive)
- C4: `"Power Platform ALM governance best practices"` — `intermediate` (sensitive)

Modes:
- M1: offline baseline: `--offline`
- M2: web + fallback: `--web --search-provider fallback`
- M3: web + serpapi: `--web --search-provider serpapi`

## Commands (12 Total)
```bash
uv run training-factory generate --topic "Power BI basics" --audience novice --out out/eval/phase_a/C1/M1/bundle.json --offline
uv run training-factory generate --topic "Power BI basics" --audience novice --out out/eval/phase_a/C1/M2/bundle.json --web --search-provider fallback
uv run training-factory generate --topic "Power BI basics" --audience novice --out out/eval/phase_a/C1/M3/bundle.json --web --search-provider serpapi

uv run training-factory generate --topic "Power Apps basics" --audience intermediate --out out/eval/phase_a/C2/M1/bundle.json --offline
uv run training-factory generate --topic "Power Apps basics" --audience intermediate --out out/eval/phase_a/C2/M2/bundle.json --web --search-provider fallback
uv run training-factory generate --topic "Power Apps basics" --audience intermediate --out out/eval/phase_a/C2/M3/bundle.json --web --search-provider serpapi

uv run training-factory generate --topic "Enterprise ChatGPT governance and risk controls" --audience intermediate --out out/eval/phase_a/C3/M1/bundle.json --offline
uv run training-factory generate --topic "Enterprise ChatGPT governance and risk controls" --audience intermediate --out out/eval/phase_a/C3/M2/bundle.json --web --search-provider fallback
uv run training-factory generate --topic "Enterprise ChatGPT governance and risk controls" --audience intermediate --out out/eval/phase_a/C3/M3/bundle.json --web --search-provider serpapi

uv run training-factory generate --topic "Power Platform ALM governance best practices" --audience intermediate --out out/eval/phase_a/C4/M1/bundle.json --offline
uv run training-factory generate --topic "Power Platform ALM governance best practices" --audience intermediate --out out/eval/phase_a/C4/M2/bundle.json --web --search-provider fallback
uv run training-factory generate --topic "Power Platform ALM governance best practices" --audience intermediate --out out/eval/phase_a/C4/M3/bundle.json --web --search-provider serpapi
```

## Output Checklist (Per Run)
1. `research_qa.status` and `research_qa.checks`
2. `research_qa.metrics`: `tier_counts`, `keyword_coverage_ratio`, `domain_counts`
3. `research.sources`: top sources look authoritative; Tier A/B present for sensitive topics
4. `brief.key_guidelines`: each guideline has `sources`; each source id exists in `research.sources[].id`
5. `curriculum.modules`: each module has `sources`; for sensitive topics, at least one Tier A appears in `references_used`
6. `qa.checks`: confirm these are `Yes`:
   - citation presence/validity checks
   - authority-tier enforcement check for sensitive cases

## Expected Outcomes
- M1 offline likely passes but may be shallow; confirm strict grounding requirements are still satisfied.
- M2 should show enriched snippets and improved keyword coverage.
- M3 should improve recall/diversity for the Enterprise ChatGPT case and strengthen tier usage.
