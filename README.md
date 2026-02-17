# Training Factory (LangGraph) — v1

A LangGraph-based pipeline that generates structured technical training assets from a single topic prompt.

## What it does

Given a topic (e.g. “Power BI basics”) and an audience level (e.g. novice), Training Factory produces a validated training bundle:

- **Brief**: goals + constraints
- **Curriculum**: module outline (timed)
- **Lab**: hands-on exercise steps
- **Slides**: slide deck outline (JSON)
- **Templates**: README + Runbook markdown
- **QA**: checks bundle completeness and basic coherence
- **Bundle**: packaged JSON artifact validated against JSON Schema

This project is designed as a “first vertical slice” to demonstrate clean multi-agent orchestration, schema-driven outputs, deterministic offline tests, and a CLI demo path.

## Why this exists

Creating training materials is repetitive and time-consuming: research, outline, slides, labs, and documentation templates.
This system automates a baseline version of that workflow so teams can iterate faster and standardize training deliverables.

Example use cases:
- Power BI / Power Apps onboarding
- Enterprise ChatGPT usage training
- GitHub version control training

## Architecture

Pipeline (v1):
`brief -> curriculum -> slides -> lab -> templates -> qa -> package`

Each stage is a small “agent” that produces structured JSON constrained by a schema. The graph coordinates state flow and implements a bounded retry loop.

### LangGraph diagram

```mermaid
flowchart LR
  START([START]) --> brief[brief]
  brief --> curriculum[curriculum]
  curriculum --> slides[slides]
  slides --> lab[lab]
  lab --> templates[templates]
  templates --> qa[qa]
  qa --> retry_gate{retry_gate}
  retry_gate -->|qa pass| package[package]
  retry_gate -->|qa fail & revision_count < 1| slides
  package --> END([END])
