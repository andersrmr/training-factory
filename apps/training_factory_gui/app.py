# How to run: streamlit run apps/training_factory_gui/app.py
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import sys
from typing import Any

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tf_gui.bundle_view import (
    extract_run_summary,
    extract_sources_table,
    load_bundle_from_path,
    load_bundle_from_upload,
    render_bundle_summary,
    safe_read_text,
)
from tf_gui.runner import run_pipeline_from_template, run_pipeline_in_process, save_bundle_to_path
from tf_gui.state import clear_bundle, get_state, init_state_defaults
from training_factory.settings import get_settings


def _format_ts(value: Any) -> str:
    if isinstance(value, str) and value:
        return value
    return "(not loaded)"


def _coerce_timeout_seconds(value: Any, default: int = 600) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def _coerce_retry_count(value: Any, default: int = 1) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    if isinstance(value, str):
        try:
            return max(0, int(value.strip()))
        except ValueError:
            return default
    return default


def _validate_loaded_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    for key in ["request", "research", "brief", "curriculum", "qa"]:
        if key not in bundle:
            errors.append(f"Missing top-level key: {key}")

    qa = bundle.get("qa", {}) if isinstance(bundle.get("qa"), dict) else {}
    qa_status = str(qa.get("status", "")).strip()
    if qa_status not in {"pass", "fail"}:
        warnings.append("qa.status is missing or not pass/fail.")

    research = bundle.get("research", {}) if isinstance(bundle.get("research"), dict) else {}
    sources = research.get("sources", []) if isinstance(research, dict) else []
    source_ids = {
        str(source.get("id", "")).strip()
        for source in sources
        if isinstance(source, dict) and str(source.get("id", "")).strip()
    }

    brief = bundle.get("brief", {}) if isinstance(bundle.get("brief"), dict) else {}
    brief_refs = brief.get("references_used", []) if isinstance(brief, dict) else []
    if isinstance(brief_refs, list):
        invalid_brief_refs = [ref for ref in brief_refs if isinstance(ref, str) and ref not in source_ids]
        if invalid_brief_refs:
            warnings.append("brief.references_used has IDs not found in research.sources.")

    curriculum = bundle.get("curriculum", {}) if isinstance(bundle.get("curriculum"), dict) else {}
    modules = curriculum.get("modules", []) if isinstance(curriculum, dict) else []
    if not isinstance(modules, list):
        errors.append("curriculum.modules is not a list.")
    else:
        for module in modules:
            if not isinstance(module, dict):
                continue
            module_sources = module.get("sources", [])
            if not isinstance(module_sources, list):
                continue
            invalid_module_refs = [
                ref for ref in module_sources if isinstance(ref, str) and ref not in source_ids
            ]
            if invalid_module_refs:
                warnings.append("One or more curriculum.modules[].sources IDs are missing from research.sources.")
                break

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _render_secret_notice(*, mode: str) -> None:
    settings = get_settings()
    missing: list[str] = []
    notes: list[str] = []

    if not settings.openai_api_key:
        missing.append("`OPENAI_API_KEY`")
        notes.append("Without it, model-backed generation and semantic QA will not run normally.")

    if mode == "M3" and not settings.serpapi_api_key:
        missing.append("`SERPAPI_API_KEY`")
        notes.append("Without it, M3 will fall back to the simpler fallback search provider.")

    if not missing:
        return

    message = "Add these Streamlit secrets to enable full functionality: " + ", ".join(missing) + "."
    if notes:
        message += " " + " ".join(notes)
    st.warning(message)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _compute_runtime_status(
    *,
    mode: str,
    execution_mode: str,
    result: dict[str, Any] | None,
    bundle: dict[str, Any] | None,
) -> dict[str, Any]:
    settings = get_settings()
    missing_openai = not bool(settings.openai_api_key)
    missing_serpapi = mode == "M3" and not bool(settings.serpapi_api_key)
    requested_provider = "fallback" if mode in {"M1", "M2"} else "serpapi"

    bundle_request = _as_dict(_as_dict(bundle).get("request"))
    bundle_research = _as_dict(bundle_request.get("research"))
    bundle_search_provider = str(bundle_research.get("search_provider", "")).strip().lower()
    effective_search_provider = bundle_search_provider or requested_provider
    if mode == "M3" and missing_serpapi:
        effective_search_provider = "fallback"

    if mode == "M1":
        llm_behavior = "Offline mode was active, so stub outputs were used instead of model calls."
    elif missing_openai:
        llm_behavior = "OPENAI_API_KEY was missing, so model-backed generation fell back to stub outputs."
    else:
        llm_behavior = f"OpenAI model-backed generation was enabled with {settings.openai_model}."

    reasons: list[str] = []
    if mode == "M1":
        reasons.append("M1 intentionally disables live model usage and runs offline.")
    if missing_openai and mode != "M1":
        reasons.append("OPENAI_API_KEY was missing, so model-backed generation and semantic QA did not run normally.")
    if missing_serpapi:
        reasons.append("SERPAPI_API_KEY was missing, so requested M3 search used the fallback provider instead.")

    run_ok = bool(_as_dict(result).get("ok")) if isinstance(result, dict) else False
    degraded = bool(reasons)
    if run_ok and degraded:
        headline = "Run succeeded in degraded mode."
        tone = "warning"
    elif run_ok:
        headline = "Run succeeded with the requested configuration."
        tone = "success"
    elif degraded:
        headline = "Run failed after degrading from the requested configuration."
        tone = "error"
    else:
        headline = "Run failed."
        tone = "error"

    return {
        "headline": headline,
        "tone": tone,
        "mode": mode,
        "execution_mode": execution_mode,
        "requested_search_provider": requested_provider,
        "effective_search_provider": effective_search_provider,
        "llm_behavior": llm_behavior,
        "missing_secrets": [
            secret
            for secret, missing in (
                ("OPENAI_API_KEY", missing_openai),
                ("SERPAPI_API_KEY", missing_serpapi),
            )
            if missing
        ],
        "reasons": reasons,
    }


def _render_runtime_status(status: dict[str, Any] | None) -> None:
    if not isinstance(status, dict):
        return

    tone = str(status.get("tone", "info"))
    headline = str(status.get("headline", "Runtime status unavailable."))
    if tone == "success":
        st.success(headline)
    elif tone == "warning":
        st.warning(headline)
    elif tone == "error":
        st.error(headline)
    else:
        st.info(headline)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mode", str(status.get("mode", "(missing)")))
    c2.metric("Execution", str(status.get("execution_mode", "(missing)")))
    c3.metric("Requested Search", str(status.get("requested_search_provider", "(missing)")))
    c4.metric("Effective Search", str(status.get("effective_search_provider", "(missing)")))

    st.caption(str(status.get("llm_behavior", "")))

    missing_secrets = status.get("missing_secrets", [])
    if isinstance(missing_secrets, list) and missing_secrets:
        st.write("Missing secrets:", ", ".join(str(item) for item in missing_secrets))

    reasons = status.get("reasons", [])
    if isinstance(reasons, list) and reasons:
        for reason in reasons:
            st.markdown(f"- {reason}")


def _render_run_summary(summary: dict[str, Any]) -> None:
    st.subheader("Run Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Topic", str(summary.get("topic", "(missing)")))
    c2.metric("Audience", str(summary.get("audience", "(missing)")))
    c3.metric("Mode", str(summary.get("mode", "(missing)")))
    c4.metric("Product", str(summary.get("product", "(missing)")))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("QA Status", str(summary.get("qa_status", "(missing)")))
    c6.metric("Web", str(summary.get("web", "(missing)")))
    c7.metric("Search Provider", str(summary.get("search_provider", "(missing)")))
    c8.metric("Domain Count", int(summary.get("domain_count", 0)))

    c9, c10 = st.columns(2)
    c9.metric("Research Retries Used", int(summary.get("research_retries_used", 0)))
    c10.metric("QA Retries Used", int(summary.get("qa_retries_used", 0)))

    tiers = summary.get("tier_counts", {}) if isinstance(summary.get("tier_counts"), dict) else {}
    st.markdown(
        "Tier counts: "
        f"A={tiers.get('A', 0)}, "
        f"B={tiers.get('B', 0)}, "
        f"C={tiers.get('C', 0)}, "
        f"D={tiers.get('D', 0)}"
    )


def _render_sources_tab(bundle: dict[str, Any]) -> None:
    table = extract_sources_table(bundle)
    if isinstance(table, list):
        st.write(table)
        rows = table
    else:
        st.dataframe(table, use_container_width=True)
        rows = table.to_dict(orient="records")

    st.caption("Source links")
    for idx, row in enumerate(rows, start=1):
        url = str(row.get("url", "")).strip()
        title = str(row.get("title", "")).strip() or f"Source {idx}"
        if not url:
            continue
        if hasattr(st, "link_button"):
            st.link_button(title, url)
        else:
            st.markdown(f"- [{title}]({url})")


def _render_raw_json_tab(bundle: dict[str, Any]) -> None:
    key_search = st.text_input("Search top-level keys", value="").strip().lower()
    if key_search:
        matches = [k for k in bundle.keys() if key_search in str(k).lower()]
        st.write("Matching keys:", matches or "(none)")
        if matches:
            st.json({k: bundle.get(k) for k in matches})
    st.subheader("Full Bundle")
    st.json(bundle)


def _render_run_log_tab(
    last_run_result: dict[str, Any] | None,
    runtime_status: dict[str, Any] | None = None,
) -> None:
    _render_runtime_status(runtime_status)

    if not isinstance(last_run_result, dict):
        st.info("No run executed yet.")
        return

    status_cols = st.columns(5)
    status_cols[0].metric("Return Code", int(last_run_result.get("returncode", -1)))
    status_cols[1].metric("OK", "yes" if bool(last_run_result.get("ok")) else "no")
    status_cols[2].metric("Started", str(last_run_result.get("started_at", "")))
    status_cols[3].metric("Finished", str(last_run_result.get("finished_at", "")))
    status_cols[4].metric("Duration (s)", str(last_run_result.get("duration_s", "")))

    command = last_run_result.get("command")
    if isinstance(command, list):
        st.code(" ".join(command), language="bash")

    if int(last_run_result.get("returncode", 1)) != 0:
        st.warning("Run failed. If needed, edit the command template to match this repo's actual CLI entrypoint.")

    log_path = last_run_result.get("log_path")
    if isinstance(log_path, str) and log_path:
        log_text = safe_read_text(log_path)
        if log_text:
            st.download_button(
                label="Download run log",
                data=log_text,
                file_name=Path(log_path).name,
                mime="text/plain",
            )

    with st.expander("stdout", expanded=False):
        st.code(str(last_run_result.get("stdout", "")), language="text")
    with st.expander("stderr", expanded=False):
        st.code(str(last_run_result.get("stderr", "")), language="text")


def _render_bundle_actions(bundle: dict[str, Any], default_save_path: str) -> None:
    bundle_json = json.dumps(bundle, indent=2) + "\n"
    st.subheader("Bundle Actions")
    st.caption("Download the currently loaded bundle from the browser.")
    st.download_button(
        label="Download bundle.json",
        data=bundle_json,
        file_name="bundle.json",
        mime="application/json",
    )

    st.subheader("Save to Disk")
    st.caption("Write the currently loaded bundle to a local file path.")
    save_path = st.text_input("save_bundle_path", value=default_save_path)
    st.session_state["save_bundle_path"] = save_path
    if st.button("Save current bundle to disk"):
        try:
            saved_path = save_bundle_to_path(bundle, save_path)
            st.session_state["last_bundle_path"] = saved_path
            st.success(f"Saved bundle to {saved_path}.")
        except ValueError as exc:
            st.error(str(exc))


def _render_about_tab() -> None:
    st.subheader("Pipeline")
    st.markdown(
        """
```mermaid
graph LR
    research --> research_qa
    research_qa --> brief
    brief --> curriculum
    curriculum --> slides
    slides --> lab
    lab --> templates
    templates --> qa
    qa --> package
```
        """
    )
    st.caption("Retries are bounded and deterministic: research_qa max 1 retry, qa max 1 retry.")

    st.subheader("System Characteristics (v2)")
    st.markdown("- Deterministic graph execution with bounded retries")
    st.markdown("- Authority-tiered source scoring (A/B/C/D)")
    st.markdown("- Keyword and product-aware retrieval/scoring")
    st.markdown("- Boilerplate-filtered full-page snippet enrichment")
    st.markdown("- Citation-aware brief/curriculum grounding")
    st.markdown("- Schema-validated bundle outputs")


def main() -> None:
    st.set_page_config(page_title="Training Factory GUI", layout="wide")
    init_state_defaults()
    state = get_state()

    st.title("Training Factory — Governance-Grounded Training Bundle Generator")
    st.write(
        "Results-first viewer for deterministic, schema-validated bundles with authoritative grounding, "
        "bounded retries, and controlled pipeline execution."
    )

    validate_result: dict[str, Any] | None = None

    with st.sidebar:
        st.caption("Configure generation inputs, run the pipeline, and inspect loaded bundles.")

        st.header("Generation")
        topic = st.text_input("topic", value="Power BI fundamentals")

        audience_options = ["novice", "intermediate", "advanced", "Custom..."]
        selected_audience = st.selectbox("audience", audience_options, index=0)
        custom_audience = ""
        if selected_audience == "Custom...":
            custom_audience = st.text_input("custom audience")
        audience = custom_audience.strip() or ("novice" if selected_audience == "Custom..." else selected_audience)

        mode_label = st.radio(
            "research mode",
            ["M1 offline", "M2 web+fallback", "M3 web+serpapi"],
            index=0,
        )
        st.caption("Mode mapping: M1: offline | M2: web + fallback | M3: web + serpapi")
        mode = mode_label.split()[0]
        if mode == "M1":
            mode_flags = "--offline"
        elif mode == "M2":
            mode_flags = "--web --search-provider fallback"
        elif mode == "M3":
            mode_flags = "--web --search-provider serpapi"
        else:
            mode_flags = ""
        _render_secret_notice(mode=mode)

        st.caption("The app automatically detects the topic area and uses it to guide research.")
        product_flag = ""

        st.header("Run Controls")
        execution_mode = st.radio(
            "execution mode",
            ["In-process (Recommended)", "CLI subprocess"],
            index=0 if str(state.get("execution_mode") or "in_process") == "in_process" else 1,
        )
        execution_mode_value = "in_process" if execution_mode.startswith("In-process") else "cli"
        out_dir = st.text_input("out_dir", value=str(state.get("out_dir") or "out/gui"))
        if execution_mode_value == "in_process":
            st.caption(
                "In-process runs keep the bundle in memory. A run log is written to `out_dir/logs`, "
                "and the bundle is only written to disk if you use `Save current bundle to disk`."
            )
        else:
            st.caption(
                "CLI runs write a run log to `out_dir/logs` and write bundles under "
                "`out_dir/<MODE>/bundle.json` before the GUI reloads them."
            )
        st.caption(
            "Need retry tuning? Open `Advanced settings` to adjust `research_max_retries` "
            "and `qa_max_retries`."
        )

        with st.expander("Advanced settings", expanded=False):
            run_cwd = st.text_input(
                "run_cwd",
                value=str(state.get("run_cwd") or ""),
                help=(
                    "Working directory used only for CLI subprocess runs. Leave blank to run from "
                    "the app's current project directory."
                ),
            )
            timeout_default = _coerce_timeout_seconds(state.get("timeout_s"))
            retry_default = _coerce_retry_count(state.get("research_max_retries"))
            qa_retry_default = _coerce_retry_count(state.get("qa_max_retries"))
            timeout_s = int(
                st.number_input(
                    "timeout_s",
                    min_value=1,
                    value=timeout_default,
                    step=1,
                    help=(
                        "Maximum time, in seconds, to wait for a CLI subprocess run before stopping it. "
                        "Not used for in-process runs."
                    ),
                )
            )
            research_max_retries = int(
                st.number_input(
                    "research_max_retries",
                    min_value=0,
                    value=retry_default,
                    step=1,
                    help="Maximum number of times to rerun research when research_qa fails.",
                )
            )
            qa_max_retries = int(
                st.number_input(
                    "qa_max_retries",
                    min_value=0,
                    value=qa_retry_default,
                    step=1,
                    help="Maximum number of times to rerun slides/lab/templates when qa fails.",
                )
            )
            if execution_mode_value == "cli":
                command_template = st.text_area(
                    "Command Template",
                    value=str(state.get("run_command_template") or ""),
                    height=130,
                )
                st.caption(
                    "Tokens available: {topic}, {audience}, {bundle_path}, {research_max_retries}, "
                    "{qa_max_retries}, {mode_flags}, {product_flag}"
                )
                st.caption("Tip: edit the template to match this repo's actual CLI entrypoint.")
            else:
                command_template = str(state.get("run_command_template") or "")
                st.caption("CLI template is only used in CLI subprocess mode.")

        st.session_state["execution_mode"] = execution_mode_value
        st.session_state["out_dir"] = out_dir
        st.session_state["run_cwd"] = run_cwd
        st.session_state["timeout_s"] = timeout_s
        st.session_state["research_max_retries"] = research_max_retries
        st.session_state["qa_max_retries"] = qa_max_retries
        st.session_state["run_command_template"] = command_template
        st.session_state["mode_flags"] = mode_flags
        st.session_state["product_flag"] = product_flag

        escaped_topic = topic.replace('"', '\\"')
        bundle_path = f"{out_dir}/{mode}/bundle.json"
        os.makedirs(f"{out_dir}/logs", exist_ok=True)
        tokens = {
            "topic": escaped_topic,
            "audience": audience,
            "bundle_path": bundle_path,
            "research_max_retries": str(research_max_retries),
            "qa_max_retries": str(qa_max_retries),
            "mode_flags": mode_flags,
            "product_flag": product_flag,
        }

        c_run, c_validate = st.columns(2)
        run_clicked = c_run.button("Run pipeline", type="primary")
        validate_clicked = c_validate.button("Validate loaded bundle")
        st.caption(
            "`Validate loaded bundle` checks the bundle currently loaded in the GUI. "
            "It does not run the pipeline or generate a new bundle."
        )

        if validate_clicked:
            st.warning("This runs GUI-side validation on the currently loaded bundle only.")
            bundle = st.session_state.get("bundle")
            if isinstance(bundle, dict):
                gui_validation = _validate_loaded_bundle(bundle)
                validate_result = {
                    "ok": gui_validation["ok"],
                    "errors": gui_validation["errors"],
                    "warnings": gui_validation["warnings"],
                }
                if gui_validation["ok"]:
                    st.success("Loaded bundle passed GUI-side validation.")
                else:
                    st.error("Loaded bundle failed GUI-side validation.")
            else:
                validate_result = {
                    "ok": False,
                    "errors": ["No loaded bundle is available to validate."],
                    "warnings": [],
                }
                st.error("No loaded bundle is available to validate.")

        if run_clicked:
            if execution_mode_value == "in_process":
                offline = mode == "M1"
                web = mode in {"M2", "M3"}
                search_provider = "fallback" if mode in {"M1", "M2"} else "serpapi"
                result, bundle_payload = run_pipeline_in_process(
                    topic=topic,
                    audience=audience,
                    web=web,
                    search_provider=search_provider,
                    research_max_retries=research_max_retries,
                    qa_max_retries=qa_max_retries,
                    offline=offline,
                    log_dir=f"{out_dir}/logs",
                )
            else:
                result = run_pipeline_from_template(
                    command_template,
                    tokens,
                    cwd=run_cwd.strip() or None,
                    timeout_s=timeout_s,
                    log_dir=f"{out_dir}/logs",
                )
                bundle_payload = None
            st.session_state["last_run_result"] = result

            with st.expander("Resolved command", expanded=False):
                st.code(" ".join(result.get("command", [])), language="bash")
                st.write(f"return code: {result.get('returncode')}")

            if execution_mode_value == "in_process":
                if result.get("ok") and isinstance(bundle_payload, dict):
                    st.session_state["bundle"] = bundle_payload
                    st.session_state["last_loaded_at"] = datetime.now().isoformat(timespec="seconds")
                    st.success("Pipeline run succeeded and bundle is loaded in memory.")
                else:
                    st.error("Pipeline run failed. See Run Log tab for details.")
            else:
                if result.get("ok") and isinstance(result.get("bundle_path"), str):
                    resolved_bundle_path = str(result["bundle_path"])
                    try:
                        st.session_state["bundle"] = load_bundle_from_path(resolved_bundle_path)
                        st.session_state["last_bundle_path"] = resolved_bundle_path
                        st.session_state["last_loaded_at"] = datetime.now().isoformat(timespec="seconds")
                        st.success("Pipeline run succeeded and bundle was loaded from disk.")
                    except ValueError as exc:
                        st.error(f"Pipeline finished but bundle load failed: {exc}")
                else:
                    st.error("Pipeline run failed. See Run Log tab for details.")

            status_bundle = st.session_state.get("bundle")
            st.session_state["last_runtime_status"] = _compute_runtime_status(
                mode=mode,
                execution_mode=execution_mode_value,
                result=result,
                bundle=status_bundle if isinstance(status_bundle, dict) else None,
            )

        if isinstance(validate_result, dict):
            with st.expander("Validation result", expanded=False):
                st.write(validate_result)

        st.header("Bundle Loading")
        path_value = st.text_input(
            "last_bundle_path",
            value=str(state.get("last_bundle_path") or "out/gui/M1/bundle.json"),
        )
        st.session_state["last_bundle_path"] = path_value

        if st.button("Load last bundle"):
            try:
                st.session_state["bundle"] = load_bundle_from_path(path_value)
                st.session_state["last_loaded_at"] = datetime.now().isoformat(timespec="seconds")
                st.success("Loaded bundle from path.")
            except ValueError as exc:
                st.error(str(exc))

        uploaded = st.file_uploader("Upload bundle.json", type=["json"])
        if uploaded is not None:
            try:
                st.session_state["bundle"] = load_bundle_from_upload(uploaded)
                st.session_state["last_loaded_at"] = datetime.now().isoformat(timespec="seconds")
                st.success("Loaded uploaded bundle.")
            except ValueError as exc:
                st.error(str(exc))

        if st.button("Clear loaded bundle"):
            clear_bundle()
            st.info("Cleared loaded bundle.")

        if isinstance(st.session_state.get("bundle"), dict):
            _render_bundle_actions(
                st.session_state["bundle"],
                str(state.get("save_bundle_path") or f"{out_dir}/{mode}/bundle.json"),
            )

        st.header("Status")
        loaded = st.session_state.get("bundle") is not None
        st.write(f"loaded bundle: {'yes' if loaded else 'no'}")
        st.write(f"last loaded: {_format_ts(st.session_state.get('last_loaded_at'))}")
        last_run_result = st.session_state.get("last_run_result")
        if isinstance(last_run_result, dict):
            run_ok = bool(last_run_result.get("ok"))
            st.write(f"last run: {'ok' if run_ok else 'fail'}")
        last_runtime_status = st.session_state.get("last_runtime_status")
        if isinstance(last_runtime_status, dict):
            st.write(str(last_runtime_status.get("headline", "runtime status unavailable")))

    bundle = st.session_state.get("bundle")
    last_run_result = st.session_state.get("last_run_result")
    last_runtime_status = st.session_state.get("last_runtime_status")

    if isinstance(bundle, dict):
        summary = extract_run_summary(bundle)
        _render_run_summary(summary)
    else:
        st.info("Load a bundle from the sidebar to view parsed results.")

    _render_runtime_status(last_runtime_status if isinstance(last_runtime_status, dict) else None)

    tab_summary, tab_sources, tab_json, tab_run_log, tab_about = st.tabs(
        ["Bundle Summary", "Research Sources", "Raw JSON", "Run Log", "About / Architecture"]
    )

    with tab_summary:
        if isinstance(bundle, dict):
            render_bundle_summary(st, bundle)
        else:
            st.markdown(
                """
### Placeholder
- Use **Run pipeline** to generate and load a bundle in memory.
- Or use **Load last bundle** / **Upload bundle.json** from the sidebar.
                """
            )

    with tab_sources:
        if isinstance(bundle, dict):
            _render_sources_tab(bundle)
        else:
            st.write("(missing)")

    with tab_json:
        if isinstance(bundle, dict):
            _render_raw_json_tab(bundle)
        else:
            st.write("(missing)")

    with tab_run_log:
        _render_run_log_tab(
            last_run_result if isinstance(last_run_result, dict) else None,
            last_runtime_status if isinstance(last_runtime_status, dict) else None,
        )

    with tab_about:
        _render_about_tab()


if __name__ == "__main__":
    main()
