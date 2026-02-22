from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import shlex
import subprocess
import time
from typing import TypedDict


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
