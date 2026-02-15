# Step 0 — Scaffold Repository

Create a new Python repo scaffold called training-factory with this layout (dirs + placeholder files). Use src/ layout.

Must include:
- pyproject.toml (use dependencies: langgraph, langchain-core, langchain-openai, openai, pydantic, pydantic-settings, python-dotenv, jsonschema, tenacity, typer, rich; plus dev extras pytest, ruff, mypy)
- src/training_factory/__init__.py
- src/training_factory/settings.py (pydantic-settings, reads OPENAI_API_KEY and OPENAI_MODEL, etc.)
- src/training_factory/llm.py (ChatOpenAI wrapper)
- src/training_factory/state.py (TrainingState model for v0: request, brief, curriculum, slides, qa, packaging, revision_count)
- src/training_factory/graph.py (LangGraph skeleton wired brief->curriculum->slides->qa->package)
- src/training_factory/agents/{brief.py,curriculum.py,slides.py,qa.py} with stub functions returning minimal valid objects
- src/training_factory/utils/json_schema.py with a validate_json() helper (jsonschema)
- schemas/ folder with minimal JSON schemas for each agent output slice (brief, curriculum, slides, qa) and bundle schema
- tests/test_graph_smoke.py that runs the graph end-to-end with a sample request
- README.md with setup + run instructions
- .env.example

Rules:
- Keep it runnable end-to-end (even if content is minimal).
- Add a CLI entrypoint (src/training_factory/cli.py using typer) to run: python -m training_factory generate --topic "..." --audience novice
- Make frequent small commits with clear messages.
After scaffold, run pytest and fix any issues until green.
