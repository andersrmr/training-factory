# How to run: streamlit run apps/training_factory_gui/app.py
from __future__ import annotations

from datetime import datetime
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
from tf_gui.runner import run_pipeline_from_template
from tf_gui.state import clear_bundle, get_state, init_state_defaults


def _format_ts(value: Any) -> str:
    if isinstance(value, str) and value:
        return value
    return "(not loaded)"


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


def _render_run_log_tab(last_run_result: dict[str, Any] | None) -> None:
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
        st.header("Run Inputs (preview)")
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
        mode = mode_label.split()[0]
        if mode == "M1":
            mode_flags = "--offline"
        elif mode == "M2":
            mode_flags = "--web --search-provider fallback"
        elif mode == "M3":
            mode_flags = "--web --search-provider serpapi"
        else:
            mode_flags = ""

        product = st.selectbox(
            "product override",
            ["auto", "power_bi", "power_apps", "power_platform", "enterprise_chatgpt", "generic"],
            index=0,
        )
        if product == "auto":
            product_flag = ""
        else:
            product_flag = f"--product {product}"

        st.caption("Mode -> CLI Mapping:")
        st.caption("M1 = --offline")
        st.caption("M2 = --web --search-provider fallback")
        st.caption("M3 = --web --search-provider serpapi")

        st.header("Execution (Step 5)")
        out_dir = st.text_input("out_dir", value=str(state.get("out_dir") or "out/gui"))
        run_cwd = st.text_input("run_cwd", value=str(state.get("run_cwd") or ""))
        timeout_s = int(
            st.number_input(
                "timeout_s",
                min_value=1,
                value=int(state.get("timeout_s") or 600),
                step=1,
            )
        )
        command_template = st.text_area(
            "Command Template",
            value=str(state.get("run_command_template") or ""),
            height=130,
        )
        st.caption("Tokens available: {topic}, {audience}, {bundle_path}, {mode_flags}, {product_flag}")
        st.caption("Tip: edit the template to match your repo's actual CLI entrypoint.")
        st.caption("Bundles are written under out_dir/<MODE>/bundle.json to avoid overwriting.")

        st.session_state["out_dir"] = out_dir
        st.session_state["run_cwd"] = run_cwd
        st.session_state["timeout_s"] = timeout_s
        st.session_state["run_command_template"] = command_template
        st.session_state["mode_flags"] = mode_flags
        st.session_state["product_flag"] = product_flag

        escaped_topic = topic.replace('"', '\\"')
        bundle_path = f"{out_dir}/{mode}/bundle.json"
        os.makedirs(os.path.dirname(bundle_path), exist_ok=True)
        os.makedirs(f"{out_dir}/logs", exist_ok=True)
        tokens = {
            "topic": escaped_topic,
            "audience": audience,
            "bundle_path": bundle_path,
            "mode_flags": mode_flags,
            "product_flag": product_flag,
        }

        c_run, c_validate = st.columns(2)
        run_clicked = c_run.button("Run pipeline", type="primary")
        validate_clicked = c_validate.button("Validate only")

        if validate_clicked:
            st.warning("CLI does not expose a validation-only flag; performing GUI-side validation only.")
            bundle = st.session_state.get("bundle")
            if isinstance(bundle, dict):
                gui_validation = _validate_loaded_bundle(bundle)
                validate_result = {
                    "ok": gui_validation["ok"],
                    "errors": gui_validation["errors"],
                    "warnings": gui_validation["warnings"],
                }
                if gui_validation["ok"]:
                    st.success("GUI-side bundle validation passed.")
                else:
                    st.error("GUI-side bundle validation failed.")
            else:
                validate_result = {
                    "ok": False,
                    "errors": ["No loaded bundle available for GUI-side validation."],
                    "warnings": [],
                }
                st.error("No loaded bundle available for validation.")

        if run_clicked:
            result = run_pipeline_from_template(
                command_template,
                tokens,
                cwd=run_cwd.strip() or None,
                timeout_s=timeout_s,
                log_dir=f"{out_dir}/logs",
            )
            st.session_state["last_run_result"] = result

            with st.expander("Resolved command", expanded=False):
                st.code(" ".join(result.get("command", [])), language="bash")
                st.write(f"return code: {result.get('returncode')}")

            if result.get("ok") and isinstance(result.get("bundle_path"), str):
                resolved_bundle_path = str(result["bundle_path"])
                try:
                    st.session_state["bundle"] = load_bundle_from_path(resolved_bundle_path)
                    st.session_state["last_bundle_path"] = resolved_bundle_path
                    st.session_state["last_loaded_at"] = datetime.now().isoformat(timespec="seconds")
                    st.success("Pipeline run succeeded and bundle was loaded.")
                except ValueError as exc:
                    st.error(f"Pipeline finished but bundle load failed: {exc}")
            else:
                st.error("Pipeline run failed. See Run Log tab for details.")

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

        st.header("Status")
        loaded = st.session_state.get("bundle") is not None
        st.write(f"loaded bundle: {'yes' if loaded else 'no'}")
        st.write(f"last loaded: {_format_ts(st.session_state.get('last_loaded_at'))}")

    bundle = st.session_state.get("bundle")
    last_run_result = st.session_state.get("last_run_result")

    if isinstance(bundle, dict):
        summary = extract_run_summary(bundle)
        _render_run_summary(summary)
    else:
        st.info("Load a bundle from the sidebar to view parsed results.")

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
- Use **Run pipeline** in Step 5, then auto-load the produced bundle.
- Or use **Load last bundle** / **Upload bundle.json**.
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
        _render_run_log_tab(last_run_result if isinstance(last_run_result, dict) else None)

    with tab_about:
        _render_about_tab()


if __name__ == "__main__":
    main()
