"""
frontend/ui_installed_char.py
==============================
Installed Characteristic Curve tab UI.
"""
from __future__ import annotations
import streamlit as st
from backend.installed_characteristic import calculate_installed_characteristic
from backend.models import InstalledCharResult, SizingInputs, SizingResult
from frontend.ui_charts import plot_installed_characteristic
from frontend.ui_styles import section_header_html


def render_installed_characteristic(
    result: SizingResult,
    inputs: SizingInputs,
) -> None:
    st.markdown("## 📈 Installed Characteristic Curve")
    st.markdown(
        "The **inherent** characteristic is measured under constant differential pressure (lab). "
        "The **installed** characteristic shows actual behaviour in the real piping system, "
        "where valve ΔP changes with flow rate."
    )

    if not result.success or result.Cv_required is None:
        st.info("ℹ Run a successful calculation first.")
        return

    Cv_rated = inputs.Cv_rated
    if Cv_rated is None:
        st.warning("⚠ Enter a **Rated Cv** in Process Inputs to generate the installed curve.")
        return

    # ── Parameters ─────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        beta = st.slider(
            "Valve Authority β (ΔP_valve / ΔP_system)",
            0.05, 1.00,
            value=float(inputs.system_dp_fraction),
            step=0.05, format="%.2f",
            key="ic_beta",
            help="β = 1: all ΔP across valve. β < 0.25: distorted characteristic.",
        )
    with col2:
        st.metric("Cv Required", f"{result.Cv_required:.3f}")
    with col3:
        st.metric("Cv Rated", f"{Cv_rated:.3f}")

    # ── Calculate ───────────────────────────────────────────────────────────
    try:
        ic_result: InstalledCharResult = calculate_installed_characteristic(
            Cv_rated=Cv_rated,
            Cv_required=result.Cv_required,
            char=inputs.char,
            beta=beta,
            R_inherent=inputs.Cv_rated / (inputs.Cv_rated * 0.02) if inputs.Cv_rated else 50.0,
        )
    except Exception as exc:
        st.error(f"Calculation error: {exc}")
        return

    # ── Chart ───────────────────────────────────────────────────────────────
    fig = plot_installed_characteristic(ic_result)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Assessment ──────────────────────────────────────────────────────────
    st.markdown(section_header_html("Controllability Assessment"), unsafe_allow_html=True)

    if ic_result.is_controllable:
        st.success(f"✅ {ic_result.recommendation}")
    else:
        st.error(f"⚠ {ic_result.recommendation}")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Design Opening", f"{ic_result.design_opening_pct:.1f} %" if ic_result.design_opening_pct else "—")
    with col_b:
        st.metric("Valve Authority β", f"{ic_result.beta:.2f}")
    with col_c:
        if ic_result.gain_variability_pct is not None:
            st.metric("Gain Variability", f"{ic_result.gain_variability_pct:.0f} %")

    # ── Data table ──────────────────────────────────────────────────────────
    with st.expander("📋 Curve Data Table", expanded=False):
        import pandas as pd
        df = pd.DataFrame([
            {
                "Opening [%]": p.opening_pct,
                "Cv Inherent": round(p.Cv_inherent, 3),
                "Cv Installed": round(p.Cv_installed, 3),
                "Flow (Inherent) [%]": round(p.flow_fraction_inherent * 100, 2),
                "Flow (Installed) [%]": round(p.flow_fraction_installed * 100, 2),
            }
            for p in ic_result.points[::5]  # every 5th point for readability
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Theory expander ─────────────────────────────────────────────────────
    with st.expander("📐 Theory & Background", expanded=False):
        st.markdown(
            """
            ### Installed Characteristic Theory

            **Inherent characteristic** (lab, constant ΔP):
            - Equal-percentage: `Cv(θ) = Cv_max × R^(θ-1)`
            - Linear: `Cv(θ) = Cv_max × θ`
            - Quick-opening: `Cv(θ) = Cv_max × √θ`

            **Installed characteristic** (real system, variable ΔP):

            The installed flow fraction is:

            ```
            q/q_design = (Cv(θ)/Cv_design) × √(β / (1 - β + β×(Cv/Cv_design)²))
            ```

            where **β** (valve authority) = ΔP_valve / ΔP_total at design flow.

            **Key rule of thumb:**
            - β ≥ 0.25: acceptable controllability
            - β ∈ [0.25, 0.5]: equal-% gives near-linear installed
            - β ≥ 0.70 with linear inherent: near-perfect installed linearity

            *Source: Driskell (1983), ISA-75.11.01-1985*
            """
        )
