"""
frontend/ui_noise.py
====================
Noise analysis display tab (IEC 60534-8-3 and 8-4).
"""

from __future__ import annotations

import streamlit as st

from backend.models import FluidPhase, SizingResult
from frontend.ui_styles import metric_card_html, section_header_html


def render_noise(result: SizingResult) -> None:
    """
    Render the full noise analysis panel.

    Parameters
    ----------
    result : SizingResult
        Completed sizing result. Noise data is in result.noise.
    """
    if not result.success:
        st.error("Fix sizing errors before viewing noise analysis.")
        return

    noise = result.noise
    if noise is None:
        st.info("ℹ No noise data available for this phase/condition combination.")
        return

    phase = result.fluid_phase

    st.markdown(section_header_html("Noise Analysis"), unsafe_allow_html=True)

    # ── Standard reference ─────────────────────────────────────────────────
    if phase in (FluidPhase.GAS, FluidPhase.STEAM):
        standard_ref = "IEC 60534-8-3:2011 — Aerodynamic Noise Prediction"
    else:
        standard_ref = "IEC 60534-8-4:2015 — Hydrodynamic Noise Prediction"

    st.caption(f"📐 Standard: {standard_ref}")

    # ── Summary metric ──────────────────────────────────────────────────────
    Lpe = noise.overall_Lpe_dba
    limit = noise.limit_dba

    if Lpe is not None:
        col_lpe, col_limit, col_margin = st.columns(3)
        with col_lpe:
            status = "error" if noise.exceeds_limit else "ok"
            st.markdown(
                metric_card_html("Lpe [dB(A)] at 1 m", f"{Lpe:.1f}", "dB(A)",
                                 delta="⚠ Exceeds limit" if noise.exceeds_limit else "✅ Within limit",
                                 status=status),
                unsafe_allow_html=True,
            )
        with col_limit:
            st.markdown(
                metric_card_html("Site Noise Limit", f"{limit:.0f}", "dB(A)", status="info"),
                unsafe_allow_html=True,
            )
        with col_margin:
            margin = limit - Lpe
            m_status = "error" if margin < 0 else "ok" if margin > 5 else "warn"
            st.markdown(
                metric_card_html("Noise Margin", f"{margin:+.1f}", "dB(A)",
                                 status=m_status),
                unsafe_allow_html=True,
            )
    else:
        st.info("ℹ Noise level could not be calculated for these conditions.")

    # ── Gas / Steam noise detail ─────────────────────────────────────────────
    if phase in (FluidPhase.GAS, FluidPhase.STEAM):
        st.markdown(section_header_html("Aerodynamic Noise Chain (IEC 60534-8-3)"), unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if noise.Wm_watts is not None:
                st.metric("Wm — Mechanical Stream Power", f"{noise.Wm_watts:.3e} W")
            if noise.eta_acoustic is not None:
                st.metric("η_a — Acoustic Efficiency (Baumann)", f"{noise.eta_acoustic:.3e}",
                          help="Mach-dependent per IEC 60534-8-3:2011 / Baumann (1987). Corrected in v2.0.")
            if noise.Wa_watts is not None:
                st.metric("Wa — Acoustic Power", f"{noise.Wa_watts:.3e} W")

        with col_b:
            if noise.Lpi_db is not None:
                st.metric("Lpi — Internal Sound Power Level", f"{noise.Lpi_db:.1f} dB re 1pW")
            if noise.TL_db is not None:
                st.metric("TL — Pipe Wall Transmission Loss", f"{noise.TL_db:.1f} dB")
            if noise.Mvc is not None:
                is_sonic = noise.is_sonic
                st.metric(
                    "Mvc — Mach at Vena Contracta",
                    f"{noise.Mvc:.4f}",
                    delta="🔴 SONIC (choked)" if is_sonic else "✅ Subsonic",
                )

        # v2.0 fix highlight
        st.info(
            "🔧 **v2.0 Fix — Acoustic Efficiency:**  "
            "η_a is now computed from the Mach-dependent Baumann (1987) correlation "
            "(η_a = 10⁻⁴ × Mvc³·⁶ for Mvc ≤ 0.3; sonic-jet regime for Mvc > 0.3) "
            "instead of the previous fixed constant. This significantly improves "
            "accuracy at high pressure-drop ratios."
        )

    # ── Liquid noise detail ──────────────────────────────────────────────────
    elif phase == FluidPhase.LIQUID:
        if noise.Lpe_liquid_dba is not None:
            st.markdown(section_header_html("Hydrodynamic Noise (IEC 60534-8-4)"), unsafe_allow_html=True)
            st.metric("Lpe (Hydrodynamic)", f"{noise.Lpe_liquid_dba:.1f} dB(A)")
            st.caption(f"Noise regime: {noise.noise_regime}")

    # ── Noise reduction recommendations ─────────────────────────────────────
    if Lpe and Lpe > limit:
        st.markdown(section_header_html("Noise Reduction Recommendations"), unsafe_allow_html=True)

        excess = Lpe - limit
        st.error(f"🔴 Predicted noise exceeds site limit by **{excess:.1f} dB(A)**.")

        recs = _noise_reduction_recs(Lpe, limit, phase)
        for rec in recs:
            st.markdown(f"- {rec}")


def _noise_reduction_recs(Lpe: float, limit: float, phase: FluidPhase) -> list[str]:
    """Generate noise reduction recommendations."""
    excess = Lpe - limit
    recs = []

    if phase in (FluidPhase.GAS, FluidPhase.STEAM):
        if excess > 20:
            recs.append("**Upstream silencer / reactive attenuator** — most effective for high excess (>20 dB).")
            recs.append("**Multi-stage pressure reduction** — divide ΔP across two or more valves in series.")
        if excess > 10:
            recs.append("**Anti-noise trim** (drilled-hole / whisper cage) — typically 10–20 dB reduction.")
            recs.append("**Acoustic pipe insulation lagging** — typically 5–15 dB attenuation.")
        recs.append("**Increase pipe wall thickness** (heavier schedule downstream) — increases TL.")
        recs.append("**Reduce valve ΔP** — if process allows, reducing Mvc reduces η_a dramatically (cubic relationship).")

    elif phase == FluidPhase.LIQUID:
        recs.append("**Anti-cavitation trim** — reduces bubble collapse energy and associated noise.")
        recs.append("**Increase downstream back-pressure** — reduces cavitation if not already choked.")
        recs.append("**Acoustic insulation lagging** on downstream pipe.")
        recs.append("**Multi-stage let-down** with two valves in series.")

    return recs if recs else ["Consult noise specialist for site-specific solution."]
