import json
import os
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any

import typer

from training_factory.graph import run_pipeline
from training_factory.settings import get_settings
from training_factory.utils.json_schema import validate_json

app = typer.Typer(add_completion=False, help="Generate training assets from a topic.")
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "bundle.schema.json"


class SearchProviderChoice(str, Enum):
    serpapi = "serpapi"
    fallback = "fallback"


@app.callback()
def main() -> None:
    """CLI entrypoint for training-factory commands."""


@contextmanager
def _offline_override(enabled: bool):
    if not enabled:
        yield
        return

    previous = os.environ.get("TRAINING_FACTORY_OFFLINE")
    os.environ["TRAINING_FACTORY_OFFLINE"] = "1"
    get_settings.cache_clear()
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("TRAINING_FACTORY_OFFLINE", None)
        else:
            os.environ["TRAINING_FACTORY_OFFLINE"] = previous
        get_settings.cache_clear()


def _extract_bundle(state: Any) -> dict[str, Any]:
    state_data = state.model_dump() if hasattr(state, "model_dump") else dict(state)
    packaging = state_data.get("packaging", {})
    bundle = packaging.get("bundle") if isinstance(packaging, dict) else None
    if isinstance(bundle, dict):
        return bundle
    if isinstance(packaging, dict):
        return packaging
    raise typer.BadParameter("Pipeline did not return a valid packaging bundle")


@app.command("generate")
def generate(
    topic: str = typer.Option(..., "--topic", help="Training topic to generate."),
    audience: str = typer.Option("novice", "--audience", help="Target audience profile."),
    out: Path = typer.Option(Path("bundle.json"), "--out", help="Output bundle JSON path."),
    offline: bool = typer.Option(False, "--offline", help="Force offline mode for this run."),
    web: bool = typer.Option(False, "--web", help="Enable web-capable research provider selection."),
    search_provider: SearchProviderChoice = typer.Option(
        SearchProviderChoice.fallback,
        "--search-provider",
        help="Research search provider to use.",
    ),
) -> None:
    request = {
        "topic": topic,
        "audience": audience,
        "research": {"web": web, "search_provider": search_provider.value},
    }

    with _offline_override(offline):
        state = run_pipeline(
            topic=request["topic"],
            audience=request["audience"],
            research=request["research"],
        )

    bundle = _extract_bundle(state)
    validate_json(bundle, SCHEMA_PATH)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")

    brief_topic = bundle.get("brief", {}).get("topic")
    request_topic = bundle.get("request", {}).get("topic")
    resolved_topic = brief_topic or request_topic or topic

    modules = bundle.get("curriculum", {}).get("modules", [])
    deck = bundle.get("slides", {}).get("deck", [])
    qa_status = bundle.get("qa", {}).get("status", "unknown")

    module_count = len(modules) if isinstance(modules, list) else 0
    slide_count = len(deck) if isinstance(deck, list) else 0

    typer.echo(f"Wrote bundle to {out}")
    typer.echo(f"Topic: {resolved_topic}")
    typer.echo(f"Curriculum modules: {module_count}")
    typer.echo(f"Slides: {slide_count}")
    typer.echo(f"QA status: {qa_status}")


if __name__ == "__main__":
    app()
