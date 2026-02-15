from typing import Any


def generate_slides(curriculum: dict[str, Any]) -> dict[str, Any]:
    modules = curriculum.get("modules", [])
    deck = []
    for idx, module in enumerate(modules, start=1):
        deck.append(
            {
                "slide": idx,
                "title": module.get("title", f"Module {idx}"),
                "bullets": ["Learning objective", "Core concept", "Example"],
            }
        )

    return {"deck": deck}
