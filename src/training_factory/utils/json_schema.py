import json
from pathlib import Path
from typing import Any

from jsonschema import validate


def validate_json(instance: dict[str, Any], schema_path: str | Path) -> None:
    """Validate a JSON-like object against a schema file."""

    path = Path(schema_path)
    with path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    validate(instance=instance, schema=schema)
