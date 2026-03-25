from __future__ import annotations

import streamlit as st


_DEFAULT_LAST_BUNDLE_PATH = "out/gui/M1/bundle.json"
_DEFAULT_SAVE_BUNDLE_PATH = "out/gui/manual/bundle.json"
_DEFAULT_OUT_DIR = "out/gui"
_DEFAULT_RUN_TEMPLATE = (
    'python -m training_factory.cli generate --topic "{topic}" --audience {audience} '
    '--out "{bundle_path}" --research-max-retries {research_max_retries} '
    '--qa-max-retries {qa_max_retries} {mode_flags} {product_flag}'
)


def init_state_defaults() -> None:
    if "bundle" not in st.session_state:
        st.session_state["bundle"] = None
    if "last_loaded_at" not in st.session_state:
        st.session_state["last_loaded_at"] = None
    if "last_bundle_path" not in st.session_state:
        st.session_state["last_bundle_path"] = _DEFAULT_LAST_BUNDLE_PATH
    if "save_bundle_path" not in st.session_state:
        st.session_state["save_bundle_path"] = _DEFAULT_SAVE_BUNDLE_PATH
    if "run_command_template" not in st.session_state:
        st.session_state["run_command_template"] = _DEFAULT_RUN_TEMPLATE
    if "execution_mode" not in st.session_state:
        st.session_state["execution_mode"] = "in_process"
    if "run_cwd" not in st.session_state:
        st.session_state["run_cwd"] = ""
    if "out_dir" not in st.session_state:
        st.session_state["out_dir"] = _DEFAULT_OUT_DIR
    if "last_run_result" not in st.session_state:
        st.session_state["last_run_result"] = None
    if "last_runtime_status" not in st.session_state:
        st.session_state["last_runtime_status"] = None
    if "timeout_s" not in st.session_state:
        st.session_state["timeout_s"] = 600
    if "research_max_retries" not in st.session_state:
        st.session_state["research_max_retries"] = 1
    if "qa_max_retries" not in st.session_state:
        st.session_state["qa_max_retries"] = 1
    if "mode_flags" not in st.session_state:
        st.session_state["mode_flags"] = ""
    if "product_flag" not in st.session_state:
        st.session_state["product_flag"] = ""


def get_state() -> dict[str, object]:
    init_state_defaults()
    return {
        "bundle": st.session_state.get("bundle"),
        "last_loaded_at": st.session_state.get("last_loaded_at"),
        "last_bundle_path": st.session_state.get("last_bundle_path"),
        "save_bundle_path": st.session_state.get("save_bundle_path"),
        "run_command_template": st.session_state.get("run_command_template"),
        "execution_mode": st.session_state.get("execution_mode"),
        "run_cwd": st.session_state.get("run_cwd"),
        "out_dir": st.session_state.get("out_dir"),
        "last_run_result": st.session_state.get("last_run_result"),
        "last_runtime_status": st.session_state.get("last_runtime_status"),
        "timeout_s": st.session_state.get("timeout_s"),
        "research_max_retries": st.session_state.get("research_max_retries"),
        "qa_max_retries": st.session_state.get("qa_max_retries"),
        "mode_flags": st.session_state.get("mode_flags"),
        "product_flag": st.session_state.get("product_flag"),
    }


def clear_bundle(*, clear_last_run_result: bool = False) -> None:
    st.session_state["bundle"] = None
    st.session_state["last_loaded_at"] = None
    st.session_state["last_runtime_status"] = None
    if clear_last_run_result:
        st.session_state["last_run_result"] = None
