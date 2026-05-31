"""
frontend/ui_rangeability.py  — Rangeability & Turndown Analysis tab
"""
from __future__ import annotations
import streamlit as st
from backend.models import SizingInputs, SizingResult
from backend.rangeability import calculate_rangeability
from frontend.ui_charts import plot_rangeability_bar
from frontend.ui_styles import section_header_html


def render_rangeability(result: SizingResult, inputs: SizingInputs) -> None:
    st.markdown("## 📊 Rangeability & Turndown Analysis")
    st.markdown(
        "Rangeability is the ratio of maximum to minimum controllable Cv. "
        "Turndown is the ratio of design flow to minimum controllable flow. "
        "Both determine whether a single valve can handle the full operating range."
    )

    if not result.success or result.Cv_required is None:
        st.info("ℹ Run a successful calculation first.")
        return

    Cv_rated = inputs.Cv_rated
    if Cv_rated is None:
        st.warning("⚠ Enter a **Rated Cv** in Process Inputs for rangeability analysis.")
        return

    noise_dba = result.noise.overall_Lpe_dba if result.noise else None

    try:
        rang = calculate_rangeability(
            Cv_rated=Cv_rated,
            Cv_required=result.Cv_required,
            valve_type=inputs.valve_type,
            char=inputs.char,
            is_choked=result.is_choked,
            noise_dba=noise_dba,
        )
    except Exception as exc:
        st.error(f"Rangeability calculation error: {exc}")
        return

    # ── Metrics ─────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Effective Rangeability", f"{rang.effective_rangeability:.1f}:1")
    with col2:
        st.metric("Required Turndown", f"{rang.turndown_ratio:.1f}:1")
    with col3:
        adequate_label = "✅ Adequate" if rang.rangeability_adequate else "⚠ Insufficient"
        st.metric("Status", adequate_label)
    with col4:
        st.metric("Min Flow Fraction", f"{rang.min_controllable_flow_fraction*100:.1f} %")

    # ── Bar chart ────────────────────────────────────────────────────────────
    fig = plot_rangeability_bar(
        Cv_rated=rang.Cv_max,
        Cv_required=result.Cv_required,
        Cv_min=rang.Cv_min,
        turndown_ratio=rang.turndown_ratio,
        rangeability=rang.effective_rangeability,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Leakage class ────────────────────────────────────────────────────────
    st.markdown(section_header_html("Leakage Class Guidance"), unsafe_allow_html=True)
    col_lc, col_ld = st.columns([1, 2])
    with col_lc:
        st.metric("Recommended Leakage Class", rang.recommended_leakage_class)
    with col_ld:
        st.info(f"📋 {rang.leakage_class_description}")

    # ── Recommendation ────────────────────────────────────────────────────────
    st.markdown(section_header_html("Engineering Assessment"), unsafe_allow_html=True)
    if rang.rangeability_adequate:
        st.success(rang.recommendation)
    else:
        st.error(rang.recommendation)
