import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "lab.schema.json"


def _schema_mode() -> str:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    required = schema.get("required", [])
    if "labs" in required:
        return "legacy"
    return "single"


def _legacy_fallback(modules: list[dict[str, Any]]) -> dict[str, Any]:
    labs = []
    for idx, module in enumerate(modules, start=1):
        title = module.get("title", f"Module {idx}")
        labs.append(
            {
                "title": f"Lab: {title}",
                "instructions": [
                    f"Complete a practical exercise for {title}",
                    "Share your approach and reasoning",
                ],
                "expected_outcome": f"Learner can apply concepts from {title}",
            }
        )
    return {"labs": labs}


def _single_fallback(modules: list[dict[str, Any]]) -> dict[str, Any]:
    module_title = modules[0].get("title", "Core Module") if modules else "Core Module"
    return {
        "title": f"Lab: {module_title}",
        "objective": f"Apply key concepts from {module_title} in a practical exercise.",
        "prerequisites": ["Basic familiarity with the training topic"],
        "setup": ["Open your coding environment"],
        "steps": [
            {"step": 1, "instruction": f"Review the goals for {module_title}."},
            {"step": 2, "instruction": "Implement the requested task step by step."},
            {"step": 3, "instruction": "Validate results and document key takeaways."},
        ],
        "checkpoints": [
            "Implementation runs without errors",
            "Results align with the lab objective",
        ],
    }


def _single_to_legacy(lab: dict[str, Any]) -> dict[str, Any]:
    steps = lab.get("steps", [])
    instructions = []
    if isinstance(steps, list):
        instructions = [step.get("instruction", "") for step in steps if isinstance(step, dict)]
    if not instructions:
        instructions = ["Complete the lab steps"]
    return {
        "labs": [
            {
                "title": lab.get("title", "Lab"),
                "instructions": instructions,
                "expected_outcome": lab.get("objective", "Learner can complete the lab objective"),
            }
        ]
    }


def _legacy_to_single(lab: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    labs = lab.get("labs")
    if not isinstance(labs, list) or not labs:
        return fallback

    first = labs[0]
    if not isinstance(first, dict):
        return fallback

    instructions = first.get("instructions", [])
    if not isinstance(instructions, list):
        instructions = []

    steps = []
    for index, instruction in enumerate(instructions, start=1):
        if isinstance(instruction, str) and instruction:
            steps.append({"step": index, "instruction": instruction})
    while len(steps) < 3:
        steps.append(
            {
                "step": len(steps) + 1,
                "instruction": f"Complete remaining task {len(steps) + 1}",
            }
        )

    checkpoints = [first.get("expected_outcome", "Lab objective met"), "Lab output reviewed"]

    return {
        "title": first.get("title", fallback["title"]),
        "objective": first.get("expected_outcome", fallback["objective"]),
        "prerequisites": fallback["prerequisites"],
        "setup": fallback["setup"],
        "steps": steps,
        "checkpoints": checkpoints,
    }


def generate_lab(curriculum: dict[str, Any]) -> dict[str, Any]:
    modules = curriculum.get("modules", [])
    mode = _schema_mode()

    legacy_fallback = _legacy_fallback(modules)
    single_fallback = _single_fallback(modules)
    fallback = single_fallback if mode == "single" else legacy_fallback

    if mode == "single":
        prompt = (
            "Return JSON only. Do not include markdown fences, labels, or extra prose. "
            "Produce a lab with keys title, objective, prerequisites, setup, steps, and checkpoints. "
            "steps must contain numbered instructional objects and checkpoints must contain validation criteria. "
            f"Curriculum: {json.dumps(curriculum)}"
        )
    else:
        prompt = (
            "Return JSON only. Do not include markdown fences, labels, or extra prose. "
            "Produce lab activities with key labs. "
            "Each lab must include title, instructions (string array), and expected_outcome. "
            f"Curriculum: {json.dumps(curriculum)}"
        )

    def _normalize(payload: dict) -> dict:
        if "lab" in payload and isinstance(payload["lab"], dict):
            payload = payload["lab"]

        def _coerce_string_list(value: Any, fallback_list: list[str]) -> list[str]:
            if isinstance(value, list):
                normalized = [item.strip() for item in value if isinstance(item, str) and item.strip()]
                return normalized or fallback_list
            if isinstance(value, str) and value.strip():
                return [value.strip()]
            return fallback_list

        def _coerce_steps(value: Any, fallback_steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
            if not isinstance(value, list):
                return fallback_steps

            normalized_steps: list[dict[str, Any]] = []
            for idx, item in enumerate(value, start=1):
                if isinstance(item, str) and item.strip():
                    normalized_steps.append({"step": idx, "instruction": item.strip()})
                    continue
                if not isinstance(item, dict):
                    continue

                instruction = item.get("instruction")
                if not isinstance(instruction, str) or not instruction.strip():
                    continue

                step_num = item.get("step")
                step_value = step_num if isinstance(step_num, int) and step_num > 0 else idx
                step_entry: dict[str, Any] = {
                    "step": step_value,
                    "instruction": instruction.strip(),
                }
                expected_output = item.get("expected_output")
                if isinstance(expected_output, str) and expected_output.strip():
                    step_entry["expected_output"] = expected_output.strip()
                normalized_steps.append(step_entry)

            if not normalized_steps:
                return fallback_steps

            while len(normalized_steps) < 3:
                normalized_steps.append(
                    {
                        "step": len(normalized_steps) + 1,
                        "instruction": f"Complete remaining task {len(normalized_steps) + 1}",
                    }
                )
            return normalized_steps

        if mode == "single":
            if all(key in payload for key in ("title", "objective", "prerequisites", "steps", "checkpoints")):
                return {
                    "title": payload.get("title", single_fallback["title"]),
                    "objective": payload.get("objective", single_fallback["objective"]),
                    "prerequisites": _coerce_string_list(
                        payload.get("prerequisites"),
                        single_fallback["prerequisites"],
                    ),
                    "setup": _coerce_string_list(payload.get("setup"), single_fallback["setup"]),
                    "steps": _coerce_steps(payload.get("steps"), single_fallback["steps"]),
                    "checkpoints": _coerce_string_list(
                        payload.get("checkpoints"),
                        single_fallback["checkpoints"],
                    ),
                }
            return _legacy_to_single(payload, single_fallback)

        if "labs" in payload and isinstance(payload["labs"], list):
            return {"labs": payload["labs"]}
        if all(key in payload for key in ("title", "objective", "steps")):
            return _single_to_legacy(payload)
        return legacy_fallback

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
