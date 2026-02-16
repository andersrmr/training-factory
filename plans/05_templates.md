# Step 5 Plan Record

## Goal
Add a new `templates` slice (README/RUNBOOK content) to the training pipeline, including schema, agent, graph placement before QA, and final bundle packaging, while keeping tests offline-deterministic.

## Graph changes
- Added `templates` to graph state.
- Added `_templates_node` that generates templates from slides.
- Inserted templates node between slides and QA:
  - `... -> lab -> slides -> templates -> qa -> retry_gate -> ...`
- Updated QA node input to review templates output.
- Updated package assembly to include `templates`.

## Schemas added/updated
- Added: `schemas/templates.schema.json`
- Updated: `schemas/bundle.schema.json`
  - Added required `templates` section and schema definition.

## Tests updated
- Updated `tests/test_graph_smoke.py` to assert:
  - `result["packaging"]["templates"]["README.md"]` is non-empty
  - `result["packaging"]["templates"]["RUNBOOK.md"]` is non-empty
- Existing routing/offline tests remained valid and passing.

## Commit message used
`Step 5: add templates agent + schema + graph node`
