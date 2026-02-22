# Eval Matrix – Phases A–C (Cases × Modes)

## Purpose
Build a repeatable, progressive evaluation approach:
- Phase A manual smoke tests
- Phase B lightweight harness + CSV summary
- Phase C adversarial stress cases

## Definitions
Modes:
- M1 = offline baseline: `--offline`
- M2 = web + fallback: `--web --search-provider fallback`
- M3 = web + serpapi: `--web --search-provider serpapi`

Cases (base set):
- C1: "Power BI fundamentals" — novice (non-sensitive)
- C2: "Power Apps basics" — intermediate (non-sensitive)
- C3: "Enterprise ChatGPT governance and risk controls" — intermediate (sensitive)
- C4: "Power Platform ALM governance best practices" — intermediate (sensitive)

Phase C adversarial additions:
- C5: "Enterprise ChatGPT best practices for regulated industries" — intermediate (sensitive)
- C6: "Power BI tenant governance, security, and deployment controls" — intermediate (sensitive)

## Matrix
| Case | M1 | M2 | M3 |
|---|---|---|---|
| C1 | A, B | A, B | A, B |
| C2 | A, B | A, B | A, B |
| C3 | A, B | A, B | A, B |
| C4 | A, B | A, B | A, B |
| C5 | - | C | C |
| C6 | - | C | C |

Run totals:
- Phase A runs C1..C4 across M1..M3 (12 runs)
- Phase B runs C1..C4 across M1..M3 (12 runs) and writes CSV
- Phase C runs C5..C6 across M2..M3 (4 runs) (skip M1)

## Output Paths
Standardize outputs to:
- `out/eval/<phase>/<case_id>/<mode_id>/bundle.json`

## Review Checklist
Inspect:
- `research_qa.status` + `research_qa.metrics`
- tier/domain diversity
- grounding checks + authority-tier check
- `brief.key_guidelines` and `curriculum.modules` alignment
