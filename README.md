# training-factory

Minimal LangGraph scaffold for generating training assets from a topic and audience.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env` if you plan to use real LLM calls.

## Run

```bash
python -m training_factory generate --topic "Intro to Python" --audience novice
```

Optional output file:

```bash
python -m training_factory generate --topic "Intro to Python" --audience novice --output bundle.json
```

## Test

```bash
pytest
```
