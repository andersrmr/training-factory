# Step 1 — State and Schemas

Implement Step 1: state and JSON schemas.

Requirements:
- Create TrainingState in src/training_factory/state.py.
- Fields:
  request
  brief
  curriculum
  slides
  qa
  packaging
  revision_count

- Create minimal JSON schemas in schemas/ for:
  brief
  curriculum
  slides
  qa
  bundle

- Implement validate_json() in utils/json_schema.py using jsonschema.

- Update all agents to return JSON that conforms to their schema.

- Update tests so the graph output is validated against the bundle schema.

Run pytest and fix issues until green.
Commit as: "Step 1: state + schemas".
