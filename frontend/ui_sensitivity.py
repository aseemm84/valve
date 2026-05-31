"""
frontend/ui_sensitivity.py
==========================
Sensitivity / What-If Analysis tab UI.
"""
from __future__ import annotations
import streamlit as st
from backend.models import SizingInputs, SizingResult
from backend.sensitivity import SWEEP_PARAMS, run_sensitivity
from frontend.ui_charts import plot_sensitivity_line, plot_sensitivity_tornado
from frontend.ui_styles import section_header_html


def render_sensitivity(
    result: SizingResult,
    inputs: SizingInputs,
    orchestrator_fn,
) -> None:
    st.markdown("## 🔍 Sensitivity / What-If Analysis")
    st.markdown(
        "Sweep a single input parameter ±N% around the base case and see how "
        "Cv required, noise, sizing ratio, and cavitation σ respond. "
        "The **sensitivity index** shows the normalised rate of change."
    )

    if not result.success or result.Cv_required is None:
        st.info("ℹ Run a successful calculation first.")
        return

    # ── Controls ────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        swept_param = st.selectbox(
            "Parameter to Sweep",
            options=list(SWEEP_PARAMS.keys()),
            index=0,
            key="sens_param",
        )
    with col2:
        sweep_range = st.slider(
            "Sweep Range (±%)",
            5, 50, 20, 5,
            key="sens_range",
            help="Total range is ±N% around the base case value.",
        )
    with col3:
        n_steps = st.select_slider(
            "Number of Steps",
            options=[10, 15, 20, 30, 40],
            value=20,
            key="sens_steps",
        )

    run_btn = st.button("▶ Run Sensitivity Analysis", type="primary", key="btn_sens_run")

    if "sens_result" not in st.session_state:
        st.session_state["sens_result"] = None

    if run_btn:
        with st.spinner("Running parametric sweep…"):
            try:
                sens = run_sensitivity(
                    base_inputs=inputs,
                    orchestrator_fn=orchestrator_fn,
                    swept_parameter=swept_param,
                    sweep_range_pct=float(sweep_range),
                    n_steps=n_steps,
                )
                st.session_state["sens_result"] = sens
            except Exception as exc:
                st.error(f"Sweep error: {exc}")
                return

    sens_result = st.session_state.get("sens_result")
    if sens_result is None:
        st.info("Configure options above and click **▶ Run Sensitivity Analysis**.")
        return

    if sens_result.swept_parameter != swept_param:
        st.info("Parameters changed — click **▶ Run Sensitivity Analysis** to update.")

    st.markdown(section_header_html("Sensitivity Results"), unsafe_allow_html=True)

    # ── Tornado chart ────────────────────────────────────────────────────────
    col_t, col_l = st.columns([1, 1])
    with col_t:
        st.markdown("**Sensitivity Index (max |∂Output/∂Input|)**")
        fig_tornado = plot_sensitivity_tornado(
            sens_result.sensitivity_summary,
            sens_result.swept_parameter,
        )
        st.plotly_chart(fig_tornado, use_container_width=True, config={"displayModeBar": False})

    with col_l:
        output_choice = st.selectbox(
            "Output to Plot",
            options=["Cv_required", "noise_dba", "sizing_ratio", "cavitation_sigma"],
            format_func=lambda x: {
                "Cv_required": "Cv Required",
                "noise_dba": "Noise [dB(A)]",
                "sizing_ratio": "Sizing Ratio",
                "cavitation_sigma": "Cavitation σ",
            }[x],
            key="sens_output_choice",
        )
        fig_line = plot_sensitivity_line(sens_result, output_choice)
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

    # ── Summary metrics ──────────────────────────────────────────────────────
    st.markdown(section_header_html("Sensitivity Summary"), unsafe_allow_html=True)

    if sens_result.sensitivity_summary:
        cols = st.columns(len(sens_result.sensitivity_summary))
        for col, (output_name, s_index) in zip(cols, sens_result.sensitivity_summary.items()):
            label = output_name.replace("_", " ").title()
            with col:
                sensitivity_class = (
                    "🔴 High" if s_index > 1.5
                    else "🟡 Moderate" if s_index > 0.7
                    else "✅ Low"
                )
                st.metric(label, f"{s_index:.3f}", delta=sensitivity_class)

    st.caption(
        f"Base value of **{swept_param}**: {sens_result.base_value:.4g}  |  "
        f"Sweep: ±{sens_result.sweep_range_pct:.0f}%  |  "
        f"Steps: {sens_result.n_steps}  |  "
        f"Dominant output: **{sens_result.dominant_output}**"
    )

    # ── Data table ──────────────────────────────────────────────────────────
    with st.expander("📋 Full Sweep Data Table", expanded=False):
        import pandas as pd
        rows = [
            {
                "Parameter Value": round(p.parameter_value, 4),
                "% Change": round(p.parameter_pct_change, 1),
                "Cv Required": round(p.Cv_required, 4) if p.Cv_required else None,
                "Sizing Ratio": round(p.sizing_ratio, 4) if p.sizing_ratio else None,
                "Noise dB(A)": round(p.noise_dba, 1) if p.noise_dba else None,
                "σ Cavitation": round(p.cavitation_sigma, 4) if p.cavitation_sigma else None,
                "Choked": "Yes" if p.is_choked else "No",
            }
            for p in sens_result.points
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
