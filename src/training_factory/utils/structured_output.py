from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from training_factory.settings import get_settings
from training_factory.utils.json_extract import extract_json_object
from training_factory.utils.json_schema import validate_json


def generate_structured_output(
    model,
    prompt: str,
    schema_path: Path,
    *,
    normalize: Callable[[dict], dict] | None = None,
    offline_stub: dict | None = None,
) -> dict:
    """Generate, normalize, and validate structured output."""

    settings = get_settings()

    if settings.offline_mode:
        if offline_stub is None:
            raise ValueError("offline_stub is required when offline mode is enabled")
        payload = offline_stub
    else:
        fallback_text = json.dumps(offline_stub or {})
        raw = model.invoke_text(prompt=prompt, fallback_text=fallback_text)
        payload = extract_json_object(raw)

    if normalize is not None:
        payload = normalize(payload)

    validate_json(payload, schema_path)
    return payload
