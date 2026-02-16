# Architecture Review — Step 3

## A) Current architecture summary

### Modules and responsibilities
- `src/training_factory/graph.py`: LangGraph orchestration for v0 flow (`brief -> curriculum -> slides -> qa -> package -> END`), conditional QA routing, final bundle validation.
- `src/training_factory/state.py`: `TrainingState` Pydantic model for top-level pipeline state (`request`, `brief`, `curriculum`, `slides`, `qa`, `packaging`, `revision_count`).
- `src/training_factory/agents/brief.py`: brief generation prompt/invoke/extract/normalize/validate.
- `src/training_factory/agents/curriculum.py`: curriculum generation prompt/invoke/extract/normalize/validate.
- `src/training_factory/agents/slides.py`: slides generation prompt/invoke/extract/normalize/validate.
- `src/training_factory/agents/qa.py`: QA generation prompt/invoke/extract/normalize/validate.
- `src/training_factory/llm.py`: `ChatOpenAI` construction and `invoke_text()` with local fallback when no API key.
- `src/training_factory/utils/json_extract.py`: `extract_json_object()` for fenced/prose-wrapped JSON extraction.
- `src/training_factory/utils/json_schema.py`: `validate_json()` helper using `jsonschema`.
- `schemas/*.json`: slice schemas (`brief`, `curriculum`, `slides`, `qa`) plus `bundle.schema.json`.
- `tests/test_graph_smoke.py`: end-to-end graph invoke + bundle schema assertion.
- `tests/test_json_extract.py`: unit tests for JSON extraction behavior.

### State flow through LangGraph nodes
1. `START -> brief`: consumes `state.request`, outputs `state.brief`.
2. `brief -> curriculum`: consumes `state.brief`, outputs `state.curriculum`.
3. `curriculum -> slides`: consumes `state.curriculum`, outputs `state.slides` (and conditionally increments `revision_count` if prior QA failed).
4. `slides -> qa`: consumes `state.slides`, outputs `state.qa`.
5. conditional from `qa`:
   - `qa.status == "pass"` -> `package`
   - `qa.status == "fail"` and `revision_count < 1` -> back to `slides`
   - otherwise -> `package`
6. `package -> END`: assembles `state.packaging`, validates against bundle schema, increments `revision_count`.

### Where JSON extraction and schema validation occur
- Extraction: per-agent via `extract_json_object()` in `src/training_factory/utils/json_extract.py`.
- Slice validation: each agent validates its normalized output against its slice schema.
- Bundle validation: `graph._package_node()` validates packaged output against `schemas/bundle.schema.json`.

## B) Cleanliness checks

- Separation of concerns: **PASS**
  - Graph orchestrates routing/state transitions; agents handle content generation + slice shaping; utils hold reusable extraction/validation functions.
- DRY-ness (JSON extract/validate centralization): **PASS (partial)**
  - Extract/validate primitives are centralized, but agent-level normalize/fallback patterns are duplicated.
- Schema boundaries (slice vs bundle): **PASS**
  - Slice schemas constrain each stage; bundle schema validates final packaged contract.
- Test determinism (without OpenAI calls): **PASS (with caveat)**
  - Deterministic when `OPENAI_API_KEY` is unset due to fallback path; if env key is present, tests may hit live model and become non-deterministic.
- Bounded QA loop (`revision_count` + routing): **PASS (edge semantics caveat)**
  - Routing prevents unbounded loops; max one retry path exists. `revision_count` currently mixes retry tracking with package completion increments.

## C) Risks / smells (ranked)

1. `revision_count` semantics are ambiguous.
   - It increments in `_slides_node` on retry and also in `_package_node`, so it does not strictly represent retries.
2. Prompt/normalization duplication across agents.
   - Four near-identical patterns increase drift risk as new slices are added.
3. Tests can become network-coupled if `OPENAI_API_KEY` is set in environment.
   - CI/local behavior can diverge unexpectedly.
4. Schema path resolution is file-system coupled via `parents[3]` patterns.
   - Fragile to package/layout refactors and hard to unit test in isolation.
5. Bundle schema duplicates slice schema shapes.
   - Increased maintenance overhead and drift risk unless updated in lockstep.

## D) Recommendations before Step 4+

1. Split counters into `revision_count` and `attempt_count` (or stop incrementing at package).
   - Impact: high
   - Effort: low
   - Why: makes QA-loop behavior and telemetry unambiguous.

2. Add a shared agent helper (e.g., `generate_structured_output()`) for invoke -> extract -> unwrap -> normalize -> validate.
   - Impact: high
   - Effort: medium
   - Why: removes repeated logic and reduces schema drift bugs.

3. Add an explicit test mode switch for agents (e.g., `TRAINING_FACTORY_OFFLINE=1`) that always uses fallbacks.
   - Impact: high
   - Effort: low
   - Why: guarantees deterministic tests regardless of ambient env vars.

4. Centralize schema path lookup in one module.
   - Impact: medium
   - Effort: low
   - Why: avoids repeated `Path(...parents[3])` coupling and eases refactors.

5. Add targeted QA routing tests (`pass`, `fail->retry`, `fail->package-after-limit`).
   - Impact: high
   - Effort: medium
   - Why: protects bounded-loop behavior from regressions.

6. Add per-agent negative-path tests (invalid JSON, wrong shape, wrapped keys).
   - Impact: medium
   - Effort: medium
   - Why: hardens the structured-output boundary as prompts evolve.

7. Consider deriving bundle schema from slice schemas (`$ref` with resolver) or generate both from one source.
   - Impact: medium
   - Effort: medium
   - Why: reduces duplicated contract maintenance.

8. Move prompt templates to dedicated constants/files.
   - Impact: medium
   - Effort: low
   - Why: reduces prompt sprawl and makes prompt review/versioning cleaner.

## E) Expansion readiness

**Is this clean enough to add Lab + Templates next?**
- **Yes, with caution.** The v0 slice is organized enough for incremental expansion, and the graph/agent/utils boundaries are usable.

**Watch-outs before/while adding Lab + Templates**
- Keep retry semantics explicit so additional QA gates do not produce confusing state counters.
- Avoid copy-pasting current agent boilerplate into new slices; introduce a shared structured-output helper first.
- Keep tests offline-deterministic to avoid flakiness as graph complexity increases.
- Control schema duplication growth as new bundle sections are introduced.

## Pytest status
- Ran `pytest` during this review.
- Result: **passed**.
