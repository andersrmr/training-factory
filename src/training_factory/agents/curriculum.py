from typing import Any


def generate_curriculum(brief: dict[str, Any]) -> dict[str, Any]:
    topic = brief.get("topic", "Untitled Topic")
    return {
        "modules": [
            {"title": f"{topic}: Foundations", "duration_minutes": 30},
            {"title": f"{topic}: Practice", "duration_minutes": 30},
        ]
    }
