# Training Factory — Architecture Snapshot (v1)

## Overview
Training Factory v1 is a LangGraph-based structured training bundle generator. Its goal is to generate validated training assets from a topic plus audience input.

## Current Pipeline (LangGraph)
Pipeline order:

1. brief
2. curriculum
3. slides
4. lab
5. templates
6. qa
7. package

Retry logic:

- QA evaluates output quality and completeness.
- If `qa.status == "fail"` and `revision_count < 1`, the graph routes back to `slides` for one bounded revision pass.
- Otherwise, the flow proceeds to `package`.

## State Model (TrainingState)
The v1 state tracks:

- `request`
- `brief`
- `curriculum`
- `slides`
- `lab`
- `templates`
- `qa`
- `packaging`
- `revision_count`

## Templates Canonical Shape
```json
{
  "templates": {
    "readme_md": { "content": "..." },
    "runbook_md": { "content": "..." }
  }
}
```

## Bundle Output Shape
Top-level bundle keys:

- `request`
- `brief`
- `curriculum`
- `lab`
- `slides`
- `templates`
- `qa`

## Features Implemented in v1
- Structured-output agents
- JSON schema validation (slice + bundle)
- Canonical template normalization
- QA gate with bounded retry
- CLI demo command
- Deterministic offline mode
- Passing pytest suite

## Known Limitations (v1)
- Slide content minimal
- QA logic lightweight
- JSON bundle only (no PPTX export)
- Coarse retry logic

## Next Phase (Planned Improvements)
- Improve slide realism
- Add meta/provenance block
- Optional targeted retry
- Optional PPTX export
- Optional dynamic Mermaid graph generation
