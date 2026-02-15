from typing import Any


def generate_brief(request: dict[str, Any]) -> dict[str, Any]:
    topic = request.get("topic", "Untitled Topic")
    audience = request.get("audience", "general")
    return {
        "topic": topic,
        "audience": audience,
        "goals": [f"Understand fundamentals of {topic}"],
        "constraints": ["Keep explanations clear and concise"],
    }
