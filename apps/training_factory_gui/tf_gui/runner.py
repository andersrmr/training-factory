from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import subprocess
import time
from typing import Any, TypedDict

from training_factory.graph import run_pipeline
from training_factory.settings import get_settings
from training_factory.utils.json_schema import validate_json

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "bundle.schema.json"


class RunResult(TypedDict):
    ok: bool
    returncode: int
    command: list[str]
    started_at: str
    finished_at: str
    duration_s: float
    stdout: str
    stderr: str
    bundle_path: str | None
    log_path: str | None


def _offline_override(enabled: bool):
    if not enabled:
        class _NoopContext:
            def __enter__(self):
                return None

            def __exit__(self, exc_type, exc, tb):
                return False

        return _NoopContext()

    class _OfflineContext:
        def __enter__(self):
            self.previous = os.environ.get("TRAINING_FACTORY_OFFLINE")
            os.environ["TRAINING_FACTORY_OFFLINE"] = "1"
            get_settings.cache_clear()
            return None

        def __exit__(self, exc_type, exc, tb):
            if self.previous is None:
                os.environ.pop("TRAINING_FACTORY_OFFLINE", None)
            else:
                os.environ["TRAINING_FACTORY_OFFLINE"] = self.previous
            get_settings.cache_clear()
            return False

    return _OfflineContext()


def _extract_bundle(state: Any) -> dict[str, Any]:
    state_data = state.model_dump() if hasattr(state, "model_dump") else dict(state)
    packaging = state_data.get("packaging", {})
    bundle = packaging.get("bundle") if isinstance(packaging, dict) else None
    if isinstance(bundle, dict):
        return bundle
    if isinstance(packaging, dict):
        return packaging
    raise ValueError("Pipeline did not return a valid packaging bundle")


@dataclass
class _RunLogPayload:
    command: list[str]
    started_at: str
    finished_at: str
    duration_s: float
    returncode: int
    stdout: str
    stderr: str


def substitute_tokens(template: str, tokens: dict[str, str]) -> str:
    resolved = template
    for key in sorted(tokens.keys()):
        resolved = resolved.replace("{" + key + "}", tokens[key])
    return resolved


def parse_command(command_str: str) -> list[str]:
    trimmed = command_str.strip()
    if not trimmed:
        return []
    return shlex.split(trimmed)


def run_command(
    command: list[str],
    cwd: str | None,
    env_overrides: dict[str, str] | None,
    timeout_s: int,
) -> tuple[int, str, str]:
    if not command:
        return 2, "", "Empty command."

    env = None
    if env_overrides:
        env = dict(os.environ)
        env.update(env_overrides)

    try:
        completed = subprocess.run(
            command,
            cwd=cwd or None,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_s,
        )
        return completed.returncode, completed.stdout or "", completed.stderr or ""
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        timeout_message = f"Command timed out after {timeout_s}s."
        if stderr:
            stderr = stderr + "\n" + timeout_message
        else:
            stderr = timeout_message
        return 124, stdout, stderr
    except Exception as exc:  # defensive guard for UI failures
        return 1, "", f"Failed to execute command: {exc}"


def _write_log(log_dir: str, payload: _RunLogPayload) -> str | None:
    try:
        target_dir = Path(log_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = datetime.now().strftime("run_%Y%m%d_%H%M%S.log")
        log_path = target_dir / filename
        log_path.write_text(
            "\n".join(
                [
                    "[command]",
                    " ".join(payload.command),
                    "",
                    f"[started_at] {payload.started_at}",
                    f"[finished_at] {payload.finished_at}",
                    f"[duration_s] {payload.duration_s}",
                    f"[returncode] {payload.returncode}",
                    "",
                    "[stdout]",
                    payload.stdout,
                    "",
                    "[stderr]",
                    payload.stderr,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return str(log_path)
    except Exception:
        return None


def save_bundle_to_path(bundle: dict[str, Any], path: str) -> str:
    target = Path(path.strip())
    if not str(target):
        raise ValueError("Bundle save path is empty.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    return str(target)


def run_pipeline_in_process(
    *,
    topic: str,
    audience: str,
    web: bool,
    search_provider: str,
    research_max_retries: int,
    offline: bool,
    log_dir: str,
) -> tuple[RunResult, dict[str, Any] | None]:
    started_dt = datetime.now()
    started_at = started_dt.isoformat(timespec="seconds")
    started_clock = time.perf_counter()
    command = [
        "in-process",
        "run_pipeline",
        f"topic={topic}",
        f"audience={audience}",
        f"web={web}",
        f"search_provider={search_provider}",
        f"research_max_retries={research_max_retries}",
        f"offline={offline}",
    ]

    stdout = ""
    stderr = ""
    bundle: dict[str, Any] | None = None
    returncode = 0
    try:
        request_research = {
            "web": web,
            "search_provider": search_provider,
            "max_retries": research_max_retries,
        }
        with _offline_override(offline):
            state = run_pipeline(topic=topic, audience=audience, research=request_research)
        bundle = _extract_bundle(state)
        validate_json(bundle, SCHEMA_PATH)
        module_count = len(bundle.get("curriculum", {}).get("modules", [])) if isinstance(bundle, dict) else 0
        slide_count = len(bundle.get("slides", {}).get("deck", [])) if isinstance(bundle, dict) else 0
        qa_status = bundle.get("qa", {}).get("status", "unknown") if isinstance(bundle, dict) else "unknown"
        stdout = "\n".join(
            [
                "Pipeline run completed in-process.",
                f"Topic: {topic}",
                f"Curriculum modules: {module_count}",
                f"Slides: {slide_count}",
                f"QA status: {qa_status}",
            ]
        )
    except Exception as exc:
        returncode = 1
        stderr = str(exc)

    finished_dt = datetime.now()
    finished_at = finished_dt.isoformat(timespec="seconds")
    duration_s = round(time.perf_counter() - started_clock, 3)
    payload = _RunLogPayload(
        command=command,
        started_at=started_at,
        finished_at=finished_at,
        duration_s=duration_s,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )
    log_path = _write_log(log_dir, payload)
    result: RunResult = {
        "ok": returncode == 0 and bundle is not None,
        "returncode": returncode,
        "command": command,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_s": duration_s,
        "stdout": stdout,
        "stderr": stderr,
        "bundle_path": None,
        "log_path": log_path,
    }
    return result, bundle


def run_pipeline_from_template(
    template: str,
    tokens: dict[str, str],
    cwd: str | None,
    timeout_s: int,
    log_dir: str,
) -> RunResult:
    started_dt = datetime.now()
    started_at = started_dt.isoformat(timespec="seconds")
    started_clock = time.perf_counter()

    resolved_command_str = substitute_tokens(template, tokens)
    resolved_command_str = " ".join(resolved_command_str.split())
    command = parse_command(resolved_command_str)

    if command:
        returncode, stdout, stderr = run_command(command, cwd, env_overrides=None, timeout_s=timeout_s)
    else:
        returncode, stdout, stderr = 2, "", "Command template resolved to an empty command."

    finished_dt = datetime.now()
    finished_at = finished_dt.isoformat(timespec="seconds")
    duration_s = round(time.perf_counter() - started_clock, 3)

    token_bundle_path = tokens.get("bundle_path", "").strip()
    token_out_dir = tokens.get("out_dir", "").strip()
    resolved_bundle_path: str | None = None

    if token_bundle_path:
        candidate = Path(token_bundle_path)
        if candidate.exists() and candidate.is_file():
            resolved_bundle_path = str(candidate)

    if resolved_bundle_path is None and token_out_dir:
        candidate = Path(token_out_dir) / "bundle.json"
        if candidate.exists() and candidate.is_file():
            resolved_bundle_path = str(candidate)

    expected_bundle = bool(token_bundle_path or token_out_dir)
    ok = returncode == 0 and (not expected_bundle or resolved_bundle_path is not None)

    payload = _RunLogPayload(
        command=command,
        started_at=started_at,
        finished_at=finished_at,
        duration_s=duration_s,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )
    log_path = _write_log(log_dir, payload)

    result: RunResult = {
        "ok": ok,
        "returncode": returncode,
        "command": command,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_s": duration_s,
        "stdout": stdout,
        "stderr": stderr,
        "bundle_path": resolved_bundle_path,
        "log_path": log_path,
    }
    return result
