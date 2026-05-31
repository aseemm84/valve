"""
frontend/ui_valve_guide.py  — Valve Body & Trim Selection Guide tab
"""
from __future__ import annotations
import streamlit as st
from backend.models import CavitationRegime, SizingInputs, SizingResult
from backend.valve_selection import select_valve_body_and_trim
from frontend.ui_styles import section_header_html


def render_valve_guide(result: SizingResult, inputs: SizingInputs) -> None:
    st.markdown("## 🔧 Valve Body & Trim Selection Guide")
    st.markdown(
        "Rule-based selection advisor for valve body style and trim type. "
        "Based on service conditions: fluid phase, pressure drop ratio, cavitation regime, "
        "noise level, and fluid properties."
    )

    if not result.success or result.Cv_required is None:
        st.info("ℹ Run a successful calculation first.")
        return

    cav_regime = (result.cavitation.regime if result.cavitation
                  else CavitationRegime.NONE)
    noise_dba = result.noise.overall_Lpe_dba if result.noise else None
    is_flashing = (result.cavitation.is_flashing if result.cavitation else False)
    T1_C = (result.T1_K - 273.15) if result.T1_K else 20.0

    try:
        sel = select_valve_body_and_trim(
            fluid_phase=result.fluid_phase,
            P1_bara=result.P1_bar or inputs.P1_bara,
            P2_bara=result.P2_bar or inputs.P2_bara,
            Cv_required=result.Cv_required,
            d_mm=inputs.d_mm,
            cavitation_regime=cav_regime,
            noise_dba=noise_dba,
            is_choked=result.is_choked,
            sizing_ratio=result.sizing_ratio,
            viscosity_cP=inputs.viscosity_cP,
            is_flashing=is_flashing,
            temperature_C=T1_C,
        )
    except Exception as exc:
        st.error(f"Selection error: {exc}")
        return

    # ── Body style ────────────────────────────────────────────────────────────
    st.markdown(section_header_html("Recommended Valve Body Style"), unsafe_allow_html=True)
    col_b, col_balt = st.columns([1, 2])
    with col_b:
        st.success(f"✅ **{sel.recommended_body.value}**")
    with col_balt:
        if sel.body_alternatives:
            alts = " | ".join(a.value for a in sel.body_alternatives)
            st.info(f"**Alternatives:** {alts}")
    st.markdown(f"**Rationale:** {sel.body_rationale}")

    # ── Trim type ─────────────────────────────────────────────────────────────
    st.markdown(section_header_html("Recommended Trim Type"), unsafe_allow_html=True)
    col_t, col_talt = st.columns([1, 2])
    with col_t:
        st.success(f"✅ **{sel.recommended_trim.value}**")
    with col_talt:
        if sel.trim_alternatives:
            alts = " | ".join(a.value for a in sel.trim_alternatives)
            st.info(f"**Alternatives:** {alts}")
    st.markdown(f"**Rationale:** {sel.trim_rationale}")

    # ── Materials and connections ─────────────────────────────────────────────
    st.markdown(section_header_html("Materials & End Connection"), unsafe_allow_html=True)
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Body Material", "")
        st.caption(sel.body_material)
    with col_m2:
        st.metric("Trim Material", "")
        st.caption(sel.trim_material)
    with col_m3:
        st.metric("End Connection", "")
        st.caption(sel.end_connection)

    # ── Notes ─────────────────────────────────────────────────────────────────
    if sel.notes:
        st.markdown(section_header_html("Engineering Notes & Cautions"), unsafe_allow_html=True)
        for note in sel.notes:
            if "🔴" in note:
                st.error(note)
            elif "🟡" in note or "⚠" in note:
                st.warning(note)
            else:
                st.info(note)
