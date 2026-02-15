# Step 2 — Graph Wiring + LLM-backed Agents

## Goal
Implement the working v0 vertical slice using LangGraph:

brief → curriculum → slides → qa → package → END

Each agent:
- Calls the OpenAI LLM
- Returns JSON only
- Validates against its schema
- Updates only its portion of the shared state

QA includes a bounded revision loop.

---

## Definition of Done
- Graph compiles and runs in the order:
  brief → curriculum → slides → qa → package
- Agents are LLM-backed in runtime.
- Tests pass without requiring real OpenAI calls.
- Final output includes `packaging.bundle` that validates against the bundle schema.

---

## Summary of Changes
- Implemented LangGraph node sequence for v0.
- Added conditional routing from QA:
  - pass → package
  - fail (1st time) → slides
  - otherwise → package
- Updated agents to:
  - call the LLM
  - return JSON-only outputs
  - validate against schemas
- Added deterministic stub behavior for tests.
- Ensured end-to-end graph test passes.

---

## Commit
Step 2: v0 graph wiring + LLM-backed agents
