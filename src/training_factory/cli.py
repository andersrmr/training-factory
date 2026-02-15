import json
from pathlib import Path

import typer
from rich.console import Console

from training_factory.graph import run_pipeline

app = typer.Typer(add_completion=False, help="Generate training assets from a topic.")
console = Console()


@app.command("generate")
def generate(
    topic: str = typer.Option(..., "--topic", help="Training topic to generate."),
    audience: str = typer.Option("novice", "--audience", help="Target audience profile."),
    output: Path | None = typer.Option(None, "--output", help="Optional output JSON file."),
) -> None:
    state = run_pipeline(topic=topic, audience=audience)
    payload = state.model_dump()

    if output:
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.print(f"Saved bundle to [bold]{output}[/bold]")

    console.print_json(json.dumps(payload))
