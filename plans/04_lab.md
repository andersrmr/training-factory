# Step 4 Plan Record

## Goal
Add a new `lab` slice to the training pipeline, including schema, agent, graph node placement, and final bundle packaging, while keeping tests offline-deterministic.

## Graph changes
- Added `lab` to graph state.
- Added `_lab_node` that generates lab output from curriculum.
- Updated graph flow to insert lab before slides:
  - `START -> brief -> curriculum -> lab -> slides -> qa -> retry_gate -> (slides|package) -> END`
- Updated package assembly to include `lab`.

## Schemas added/updated
- Added: `schemas/lab.schema.json`
- Updated: `schemas/bundle.schema.json`
  - Added required `lab` section and schema definition.

## Tests updated
- Updated `tests/test_graph_smoke.py` to assert `result["packaging"]["lab"]["labs"]` exists.
- Existing routing/offline tests remained valid and passing.

## Commit message used
`Step 4: add lab agent + schema + graph node`
