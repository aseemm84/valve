"""
Control Valve Sizer v2.0 — Main Streamlit Application
======================================================
Entry point for the Streamlit web application.

Architecture
------------
This file is intentionally thin. All rendering is in frontend/;
all math is in backend/. This file's sole responsibilities:

1. Page configuration and CSS injection.
2. Optional dependency check at session start.
3. Sidebar global settings.
4. Tab layout (13 tabs in v2.0).
5. Triggering orchestrator.run_sizing() on button click.
6. Storing result AND inputs_model in st.session_state.
7. Dispatching to each tab's render function.
8. Rendering the persistent footer.

v2.0 new tabs (8)
-----------------
📈 Installed Char    — inherent vs installed flow characteristic
🔍 Sensitivity       — what-if parametric sweep
📉 Rangeability      — Cv range, turndown, leakage class
🔧 Valve Guide       — body and trim selection advisor
🔩 Actuator          — actuator sizing guidance
💾 Save / Load       — JSON save/load of complete calculation
🗂 Compare           — multi-case comparison table
📖 User Guide        — in-app step-by-step guide

Run
---
    streamlit run app.py

Developer
---------
Aseem Mehrotra | https://www.linkedin.com/in/aseem-mehrotra/
GitHub         | https://github.com/aseemm84/valve
"""

from __future__ import annotations

import traceback
from typing import Any, Callable

import streamlit as st

# ── Backend ───────────────────────────────────────────────────────────────────
from backend.models import FluidPhase, SizingInputs, SizingResult
from backend.orchestrator import run_sizing

# ── Frontend — core panels (v1.x) ────────────────────────────────────────────
from frontend.ui_inputs import (
    build_sizing_inputs,
    render_fluid_properties,
    render_process_conditions,
    render_sidebar_globals,
    render_valve_parameters,
)
from frontend.ui_noise import render_noise
from frontend.ui_report import render_report_panel
from frontend.ui_results import render_results
from frontend.ui_styles import (
    app_header_html,
    inject_custom_css,
    render_footer,
    section_header_html,
)
from frontend.ui_warnings import render_warning_panel

# ── Frontend — original charts ────────────────────────────────────────────────
from frontend.ui_charts import (
    plot_cavitation_map,
    plot_cv_characteristic,
    plot_noise_gauge,
    plot_pressure_profile,
    plot_sizing_gauge,
)

# ── Frontend — v2.0 feature panels ────────────────────────────────────────────
from frontend.ui_installed_char import render_installed_characteristic
from frontend.ui_sensitivity import render_sensitivity
from frontend.ui_rangeability import render_rangeability
from frontend.ui_valve_guide import render_valve_guide
from frontend.ui_actuator import render_actuator
from frontend.ui_save_load import render_save_load_panel
from frontend.ui_comparison import render_comparison
from frontend.ui_user_guide import render_user_guide


# =============================================================================
# PAGE CONFIGURATION  (must be the very first Streamlit call)
# =============================================================================

st.set_page_config(
    page_title="Control Valve Sizer v2.0",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/aseemm84/valve",
        "Report a bug": "https://github.com/aseemm84/valve/issues",
        "About": (
            "### Control Valve Sizer v2.0\n"
            "Professional sizing per **IEC 60534-2-1:2011** and **ISA-75.01.01-2012**.\n\n"
            "Noise prediction per **IEC 60534-8-3:2011** and **IEC 60534-8-4:2015**.\n\n"
            "Steam properties via **IAPWS-IF97**.\n\n"
            "Developed by [Aseem Mehrotra](https://www.linkedin.com/in/aseem-mehrotra/)"
        ),
    },
)


# =============================================================================
# DEPENDENCY GUARD
# =============================================================================

def _check_dependencies() -> dict[str, bool]:
    """
    Check optional heavy dependencies once per browser session.

    Results cached in session_state so the import is attempted only on
    first page load, not on every widget callback.

    Returns
    -------
    dict[str, bool]
        Keys: 'iapws', 'fpdf2', 'openpyxl'
    """
    if "dep_check_done" not in st.session_state:
        deps: dict[str, bool] = {}

        for pkg, key in [("iapws", "iapws"), ("fpdf", "fpdf2"), ("openpyxl", "openpyxl")]:
            try:
                __import__(pkg)
                deps[key] = True
            except ImportError:
                deps[key] = False

        st.session_state["dep_check_done"] = True
        st.session_state["deps"] = deps

    return st.session_state.get("deps", {"iapws": True, "fpdf2": True, "openpyxl": True})


# =============================================================================
# SAFE CHART RENDERER
# =============================================================================

def _safe_chart(fig_func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """
    Call fig_func(*args, **kwargs) and render with st.plotly_chart.

    Any exception from the chart function is caught silently; a short
    informational caption is shown instead of crashing the tab.
    """
    try:
        fig = fig_func(*args, **kwargs)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception as exc:
        st.caption(f"ℹ Chart unavailable: {exc}")


# =============================================================================
# SESSION STATE INITIALISATION
# =============================================================================

def _init_session_state() -> None:
    """Initialise all session-state keys with safe defaults."""
    defaults: dict[str, Any] = {
        "result":         None,   # SizingResult | None
        "inputs_model":   None,   # SizingInputs | None   ← NEW in v2.0
        "calc_error":     None,   # str | None
        "calc_attempted": False,  # True after first CALCULATE click
        # v2.0 feature state
        "comparison_cases": [],   # list[ComparisonCase]
        "sens_result":    None,   # SensitivityResult | None
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# =============================================================================
# HELPER: "not yet calculated" message
# =============================================================================

def _not_calculated_info(tab_name: str = "") -> None:
    """Show a friendly prompt when no calculation has been run yet."""
    st.info(
        "👈 Fill in the **📋 Process Inputs** tab, then click "
        "**🔬 CALCULATE** in the sidebar."
        + (f"  This tab ({tab_name}) will populate after a successful calculation." if tab_name else "")
    )


def _error_info() -> None:
    """Show error panel when calc failed."""
    st.error(st.session_state.get("calc_error") or "Unknown error. Check Process Inputs.")


def _result_guard() -> tuple[SizingResult | None, SizingInputs | None]:
    """
    Return (result, inputs_model) from session state, or (None, None).

    Also renders any error message.
    """
    if not st.session_state["calc_attempted"]:
        return None, None
    if st.session_state.get("calc_error") and not st.session_state.get("result"):
        _error_info()
        return None, None
    return st.session_state.get("result"), st.session_state.get("inputs_model")


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main() -> None:
    """
    Top-level application function.

    Called on every Streamlit script re-run. Session state ensures that
    results and inputs_model persist across re-runs and tab switches.
    """
    _init_session_state()
    inject_custom_css()

    # ── Dependency check (once per session) ──────────────────────────────────
    deps = _check_dependencies()

    if not deps.get("iapws", True):
        st.warning(
            "⚠ **Steam sizing unavailable:** the `iapws` library is not installed. "
            "Liquid and gas calculations are unaffected. "
            "To enable: `pip install iapws==1.5.2`",
            icon="♨️",
        )

    # ── App header (with LinkedIn badge) ─────────────────────────────────────
    st.markdown(app_header_html(), unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    sidebar_vals = render_sidebar_globals()
    unit_system  = sidebar_vals["unit_system"]
    fluid_phase  = sidebar_vals["fluid_phase"]

    # Block Steam if iapws unavailable
    if fluid_phase == "Steam" and not deps.get("iapws", True):
        st.sidebar.error(
            "Steam requires `iapws`. Select Liquid or Gas, or install iapws."
        )

    # ── Tab layout  (13 tabs: 5 original + 8 new) ────────────────────────────
    (
        tab_inputs,
        tab_results,
        tab_noise,
        tab_warnings,
        tab_report,
        tab_installed,
        tab_sensitivity,
        tab_rangeability,
        tab_valve_guide,
        tab_actuator,
        tab_save_load,
        tab_compare,
        tab_user_guide,
    ) = st.tabs([
        "📋 Process Inputs",
        "📊 Sizing Results",
        "🔊 Noise Analysis",
        "⚠ Warnings",
        "📄 Report",
        "📈 Installed Char",
        "🔍 Sensitivity",
        "📉 Rangeability",
        "🔧 Valve Guide",
        "🔩 Actuator",
        "💾 Save / Load",
        "🗂 Compare",
        "📖 User Guide",
    ])

    # =========================================================================
    # TAB 1 — PROCESS INPUTS
    # =========================================================================
    with tab_inputs:
        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            process_vals = render_process_conditions(unit_system, fluid_phase)
            fluid_vals   = render_fluid_properties(unit_system, fluid_phase)

        with col_right:
            valve_vals = render_valve_parameters(unit_system)

        # ── Quick input summary expander ──────────────────────────────────────
        st.divider()
        with st.expander(
            "🔍 Input Summary — what will be sent to the sizing engine",
            expanded=False,
        ):
            delta_P = process_vals["P1_gauge"] - process_vals["P2_gauge"]
            atm     = 1.01325 if unit_system == "SI" else 14.696
            p_unit  = "bar" if unit_system == "SI" else "psi"

            st.markdown(
                f"""
| Parameter | Value | Unit |
|---|---|---|
| Fluid Phase | **{fluid_phase}** | |
| Unit System | **{unit_system}** | |
| P1 (gauge) | **{process_vals['P1_gauge']:.3f}** | {p_unit}g |
| P2 (gauge) | **{process_vals['P2_gauge']:.3f}** | {p_unit}g |
| ΔP | **{delta_P:.3f}** | {p_unit} |
| P1 (absolute) | **{process_vals['P1_gauge'] + atm:.4f}** | {p_unit}a |
| Flow | **{process_vals['flow_value']:.4f}** | basis: {process_vals['flow_basis'].value} |
| FL | **{valve_vals['FL']:.3f}** | — |
| xT | **{valve_vals['xT']:.3f}** | — |
| Valve Bore d | **{valve_vals['d']:.1f}** | {'mm' if unit_system == 'SI' else 'in'} |
| Sizing Margin | **{sidebar_vals['sizing_margin_pct']:.0f}** | % |
| Valve Authority β | **{valve_vals.get('system_dp_fraction', 0.5):.2f}** | — |
"""
            )

    # =========================================================================
    # CALCULATE BUTTON LOGIC  (runs on every script re-run when clicked)
    # =========================================================================
    if sidebar_vals["calculate_clicked"]:

        # Block steam + missing iapws
        if fluid_phase == "Steam" and not deps.get("iapws", True):
            st.error(
                "❌ Cannot size Steam service: `iapws` is not installed. "
                "Select Liquid or Gas, or install: `pip install iapws==1.5.2`"
            )
            st.session_state.update({
                "calc_attempted": True,
                "result":         None,
                "inputs_model":   None,
                "calc_error":     "iapws not installed",
            })

        else:
            with st.spinner("🔬 Running sizing calculation…"):
                try:
                    inputs_model: SizingInputs = build_sizing_inputs(
                        sidebar_vals, process_vals, fluid_vals, valve_vals
                    )
                    result: SizingResult = run_sizing(inputs_model)

                    st.session_state["result"]       = result
                    st.session_state["inputs_model"] = inputs_model  # ← v2.0 key addition
                    st.session_state["calc_error"]   = None
                    st.session_state["calc_attempted"] = True
                    st.session_state["sens_result"]  = None  # invalidate stale sensitivity

                except Exception as exc:
                    st.session_state.update({
                        "result":         None,
                        "inputs_model":   None,
                        "calc_error":     (
                            f"**Input Error:** {exc}\n\n"
                            f"```\n{traceback.format_exc()}\n```"
                        ),
                        "calc_attempted": True,
                    })

        # Toast notifications
        r = st.session_state.get("result")
        if r and r.success:
            st.toast("✅ Calculation complete — see Results tab", icon="✅")
        elif st.session_state.get("calc_error"):
            st.toast("❌ Input error — check your inputs", icon="❌")
        else:
            st.toast("⚠ Completed with warnings", icon="⚠")

    # =========================================================================
    # TAB 2 — SIZING RESULTS
    # =========================================================================
    with tab_results:
        if not st.session_state["calc_attempted"]:
            _not_calculated_info()

        elif st.session_state.get("calc_error") and not st.session_state.get("result"):
            _error_info()

        else:
            result: SizingResult = st.session_state["result"]

            if result is None:
                st.error("No result available. Check inputs and recalculate.")
            else:
                render_results(result, unit_system)

                # ── Charts ──────────────────────────────────────────────────
                if result.success:
                    st.divider()
                    col_chart1, col_chart2 = st.columns(2, gap="medium")

                    with col_chart1:
                        cv_rated_val = valve_vals.get("Cv_rated")
                        if cv_rated_val and result.Cv_required:
                            _safe_chart(
                                plot_cv_characteristic,
                                Cv_rated=cv_rated_val,
                                Cv_required=result.Cv_required,
                                R_inherent=valve_vals.get("R_inherent", 50.0),
                                char=valve_vals.get("char"),
                                opening_pct=result.opening_pct,
                            )
                        else:
                            st.info(
                                "Enter **Rated Cv** in the Inputs tab to see "
                                "the characteristic curve."
                            )

                    with col_chart2:
                        if result.sizing_ratio and result.Cv_required:
                            cv_rated_for_gauge = result.Cv_required / result.sizing_ratio
                            _safe_chart(
                                plot_sizing_gauge,
                                sizing_ratio=result.sizing_ratio,
                                Cv_required=result.Cv_required,
                                Cv_rated=cv_rated_for_gauge,
                            )
                        else:
                            st.info("Enter **Rated Cv** to see the sizing ratio gauge.")

                    # Pressure profile (liquid only)
                    if (
                        result.fluid_phase == FluidPhase.LIQUID
                        and result.cavitation
                        and result.P1_bar
                        and result.P2_bar
                    ):
                        st.markdown(
                            section_header_html("Pressure Profile Through Valve"),
                            unsafe_allow_html=True,
                        )
                        Pv_bar_si = fluid_vals.get("Pv", 0.023)
                        if unit_system == "US":
                            from backend.constants import PSI_TO_BAR
                            Pv_bar_si = Pv_bar_si * PSI_TO_BAR
                        _safe_chart(
                            plot_pressure_profile,
                            P1_bar=result.P1_bar,
                            P_vc_bar=result.cavitation.P_vc,
                            P2_bar=result.P2_bar,
                            Pv_bar=Pv_bar_si,
                            delta_P_max_bar=result.delta_P_max_bar,
                        )

                    # Cavitation map (liquid with active cavitation)
                    if (
                        result.fluid_phase == FluidPhase.LIQUID
                        and result.cavitation
                        and result.cavitation.regime.value != "none"
                        and result.P1_bar
                        and result.P2_bar
                    ):
                        st.markdown(
                            section_header_html("Cavitation Map"),
                            unsafe_allow_html=True,
                        )
                        Pv_bar_si = fluid_vals.get("Pv", 0.023)
                        if unit_system == "US":
                            from backend.constants import PSI_TO_BAR
                            Pv_bar_si = Pv_bar_si * PSI_TO_BAR
                        _safe_chart(
                            plot_cavitation_map,
                            P1_bar=result.P1_bar,
                            P2_bar=result.P2_bar,
                            Pv_bar=Pv_bar_si,
                            FL=valve_vals["FL"],
                            delta_P_max=result.cavitation.delta_P_max,
                            delta_P_incipient=result.cavitation.delta_P_incipient,
                        )

    # =========================================================================
    # TAB 3 — NOISE ANALYSIS
    # =========================================================================
    with tab_noise:
        if not st.session_state["calc_attempted"]:
            _not_calculated_info("Noise Analysis")
        elif st.session_state.get("calc_error") and not st.session_state.get("result"):
            _error_info()
        else:
            result: SizingResult = st.session_state["result"]
            if result is not None:
                render_noise(result)

                if result.success and result.noise:
                    st.divider()
                    col_ng, _ = st.columns([1, 1])
                    with col_ng:
                        _safe_chart(
                            plot_noise_gauge,
                            Lpe_dba=result.noise.overall_Lpe_dba,
                            limit_dba=sidebar_vals["noise_limit_dba"],
                        )

    # =========================================================================
    # TAB 4 — WARNINGS
    # =========================================================================
    with tab_warnings:
        if not st.session_state["calc_attempted"]:
            _not_calculated_info("Warnings")
        elif st.session_state.get("calc_error") and not st.session_state.get("result"):
            _error_info()
        else:
            result: SizingResult = st.session_state["result"]
            if result is not None:
                render_warning_panel(result)

    # =========================================================================
    # TAB 5 — REPORT
    # =========================================================================
    with tab_report:
        if not st.session_state["calc_attempted"]:
            _not_calculated_info("Report")
        elif st.session_state.get("calc_error") and not st.session_state.get("result"):
            _error_info()
        else:
            result: SizingResult = st.session_state["result"]
            if result is not None:
                render_report_panel(result)

    # =========================================================================
    # TAB 6 — INSTALLED CHARACTERISTIC CURVE  (v2.0)
    # =========================================================================
    with tab_installed:
        if not st.session_state["calc_attempted"]:
            _not_calculated_info("Installed Characteristic")
        else:
            result, inputs_model = _result_guard()
            if result is not None and inputs_model is not None:
                render_installed_characteristic(result, inputs_model)

    # =========================================================================
    # TAB 7 — SENSITIVITY / WHAT-IF  (v2.0)
    # =========================================================================
    with tab_sensitivity:
        if not st.session_state["calc_attempted"]:
            _not_calculated_info("Sensitivity Analysis")
        else:
            result, inputs_model = _result_guard()
            if result is not None and inputs_model is not None:
                render_sensitivity(
                    result=result,
                    inputs=inputs_model,
                    orchestrator_fn=run_sizing,   # pass as dependency (no circular import)
                )

    # =========================================================================
    # TAB 8 — RANGEABILITY & TURNDOWN  (v2.0)
    # =========================================================================
    with tab_rangeability:
        if not st.session_state["calc_attempted"]:
            _not_calculated_info("Rangeability Analysis")
        else:
            result, inputs_model = _result_guard()
            if result is not None and inputs_model is not None:
                render_rangeability(result, inputs_model)

    # =========================================================================
    # TAB 9 — VALVE BODY & TRIM SELECTION GUIDE  (v2.0)
    # =========================================================================
    with tab_valve_guide:
        if not st.session_state["calc_attempted"]:
            _not_calculated_info("Valve Selection Guide")
        else:
            result, inputs_model = _result_guard()
            if result is not None and inputs_model is not None:
                render_valve_guide(result, inputs_model)

    # =========================================================================
    # TAB 10 — ACTUATOR SIZING GUIDANCE  (v2.0)
    # =========================================================================
    with tab_actuator:
        if not st.session_state["calc_attempted"]:
            _not_calculated_info("Actuator Sizing")
        else:
            result, inputs_model = _result_guard()
            if result is not None and inputs_model is not None:
                render_actuator(result, inputs_model)

    # =========================================================================
    # TAB 11 — SAVE / LOAD  (v2.0)
    # =========================================================================
    with tab_save_load:
        current_result  = st.session_state.get("result")
        current_inputs  = st.session_state.get("inputs_model")

        load_payload = render_save_load_panel(
            current_inputs=current_inputs,
            current_result=current_result,
        )

        # If a file was loaded, inject into session state so results refresh
        if load_payload and load_payload.get("loaded_inputs"):
            st.session_state["inputs_model"]  = load_payload["loaded_inputs"]
            st.session_state["result"]        = load_payload["loaded_result"]
            st.session_state["calc_attempted"] = True
            st.session_state["calc_error"]    = None
            st.session_state["sens_result"]   = None
            st.rerun()

    # =========================================================================
    # TAB 12 — MULTI-CASE COMPARISON TABLE  (v2.0)
    # =========================================================================
    with tab_compare:
        current_result  = st.session_state.get("result")
        current_inputs  = st.session_state.get("inputs_model")
        render_comparison(current_result, current_inputs)

    # =========================================================================
    # TAB 13 — USER GUIDE  (v2.0)
    # =========================================================================
    with tab_user_guide:
        render_user_guide()

    # =========================================================================
    # PERSISTENT FOOTER  (v2.0 — LinkedIn + GitHub branding)
    # =========================================================================
    render_footer()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
