from __future__ import annotations

import streamlit as st


_DEFAULT_LAST_BUNDLE_PATH = "out/gui/M1/bundle.json"
_DEFAULT_OUT_DIR = "out/gui"
_DEFAULT_RUN_TEMPLATE = (
    'python -m training_factory.cli generate --topic "{topic}" --audience {audience} '
    '--out "{bundle_path}" {mode_flags} {product_flag}'
)


def init_state_defaults() -> None:
    if "bundle" not in st.session_state:
        st.session_state["bundle"] = None
    if "last_loaded_at" not in st.session_state:
        st.session_state["last_loaded_at"] = None
    if "last_bundle_path" not in st.session_state:
        st.session_state["last_bundle_path"] = _DEFAULT_LAST_BUNDLE_PATH
    if "run_command_template" not in st.session_state:
        st.session_state["run_command_template"] = _DEFAULT_RUN_TEMPLATE
    if "run_cwd" not in st.session_state:
        st.session_state["run_cwd"] = ""
    if "out_dir" not in st.session_state:
        st.session_state["out_dir"] = _DEFAULT_OUT_DIR
    if "last_run_result" not in st.session_state:
        st.session_state["last_run_result"] = None
    if "timeout_s" not in st.session_state:
        st.session_state["timeout_s"] = 600
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
        "run_command_template": st.session_state.get("run_command_template"),
        "run_cwd": st.session_state.get("run_cwd"),
        "out_dir": st.session_state.get("out_dir"),
        "last_run_result": st.session_state.get("last_run_result"),
        "timeout_s": st.session_state.get("timeout_s"),
        "mode_flags": st.session_state.get("mode_flags"),
        "product_flag": st.session_state.get("product_flag"),
    }


def clear_bundle(*, clear_last_run_result: bool = False) -> None:
    st.session_state["bundle"] = None
    st.session_state["last_loaded_at"] = None
    if clear_last_run_result:
        st.session_state["last_run_result"] = None
