from typing import Any


def generate_qa(slides: dict[str, Any]) -> dict[str, Any]:
    deck = slides.get("deck", [])
    checks = []
    for slide in deck:
        title = slide.get("title", "Unknown")
        checks.append({"prompt": f"What is one key idea from '{title}'?", "answer": "Sample answer"})

    return {"checks": checks}
