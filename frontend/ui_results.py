"""
frontend/ui_results.py
======================
Sizing results display — primary metrics, secondary metrics,
flow regime banner, and tabulated results.

All values are rendered in the user's selected unit system.
"""

from __future__ import annotations

import streamlit as st

from backend.constants import BAR_TO_PSI, KGH_TO_LBH, M3H_TO_GPM, MM_TO_INCH
from backend.models import CavitationRegime, FluidPhase, SizingResult
from frontend.ui_styles import metric_card_html, section_header_html


def render_results(result: SizingResult, unit_system: str) -> None:
    """
    Render the complete sizing results panel.

    Parameters
    ----------
    result : SizingResult
        The result from orchestrator.run_sizing().
    unit_system : str
        "SI" or "US" — controls unit labels for display.
    """
    if not result.success:
        _render_error_panel(result)
        return

    _render_success_banner(result)
    _render_primary_metrics(result, unit_system)
    st.divider()
    _render_secondary_metrics(result, unit_system)
    st.divider()
    _render_detailed_table(result, unit_system)


def _render_error_panel(result: SizingResult) -> None:
    """Render error state."""
    st.error(f"❌ Sizing Failed: {result.error_message or 'Unknown error'}")
    if result.hard_violations:
        st.markdown("**Constraint violations:**")
        for v in result.hard_violations:
            st.markdown(f"- 🔴 {v}")


def _render_success_banner(result: SizingResult) -> None:
    """Render success / partial-success banner with tag and case name."""
    tag = result.tag_number or ""
    case = result.case_name or ""
    title = " | ".join(filter(None, [tag, case])) or "Sizing Results"

    phase_icon = {"Liquid": "💧", "Gas": "💨", "Steam": "♨️"}.get(
        result.fluid_phase.value, "🔧"
    )
    choked_label = " 🔴 CHOKED" if result.is_choked else ""
    viscous_label = " 🟡 VISCOUS" if result.is_viscous_corrected else ""

    status_color = "#375623" if not result.is_choked else "#c00000"

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#e8f4fd,#f5f7fa);
             border:1px solid #2e75b6;border-radius:12px;
             padding:0.9rem 1.4rem;margin-bottom:0.8rem;">
            <h3 style="color:#1f4e79;margin:0 0 0.3rem 0;">
                {phase_icon} {title}
            </h3>
            <span style="color:{status_color};font-size:0.88rem;font-weight:600;">
                ✅ Sizing Complete
                {choked_label}{viscous_label}
                &nbsp;|&nbsp; Flow Regime: {result.flow_regime}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_primary_metrics(result: SizingResult, unit_system: str) -> None:
    """Render the 4 primary key metrics as metric cards."""
    st.markdown(section_header_html("Primary Sizing Results"), unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    # Cv Required
    cv_req = result.Cv_required
    cv_margin = result.Cv_margin
    with col1:
        if cv_req is not None:
            st.metric(
                "Cv Required",
                f"{cv_req:.3f}",
                delta=f"With margin: {cv_margin:.3f}" if cv_margin else None,
            )
        else:
            st.metric("Cv Required", "—")

    # Kv Required
    kv_req = result.Kv_required
    with col2:
        st.metric(
            "Kv Required",
            f"{kv_req:.3f}" if kv_req else "—",
            help="Kv = Cv × 0.8646",
        )

    # Sizing Ratio
    with col3:
        if result.sizing_ratio is not None:
            ratio_pct = result.sizing_ratio * 100.0
            status = "normal" if result.sizing_ratio <= 0.85 else "inverse"
            delta_label = "✅ OK" if result.sizing_ratio <= 0.85 else "⚠ Oversized" if result.sizing_ratio > 1.0 else "🟡 Near limit"
            st.metric("Sizing Ratio", f"{result.sizing_ratio:.3f}", delta=delta_label)
        else:
            st.metric("Sizing Ratio", "—", help="Enter Rated Cv to compute")

    # Opening %
    with col4:
        if result.opening_pct is not None:
            st.metric(
                "Opening %",
                f"{result.opening_pct:.1f} %",
                delta="Optimal: 40–80%" if 40 <= result.opening_pct <= 80 else "Outside optimal range",
            )
        else:
            st.metric("Opening %", "—")

    # Noise summary strip
    if result.noise and result.noise.overall_Lpe_dba is not None:
        noise_val = result.noise.overall_Lpe_dba
        noise_limit = result.noise.limit_dba
        noise_color = "#c00000" if noise_val > noise_limit else "#375623"
        noise_icon = "🔴" if noise_val > noise_limit else "✅"
        st.markdown(
            f'<div style="background:#f5f7fa;border-radius:8px;padding:0.5rem 1rem;'
            f'font-size:0.88rem;border-left:4px solid {noise_color};">'
            f'{noise_icon} Predicted Noise: <b>{noise_val:.1f} dB(A)</b> '
            f'(limit: {noise_limit:.0f} dB(A))</div>',
            unsafe_allow_html=True,
        )


def _render_secondary_metrics(result: SizingResult, unit_system: str) -> None:
    """Render secondary process metrics — pressure, flow, cavitation."""
    p_unit  = "bar a" if unit_system == "SI" else "psia"
    dp_unit = "bar"   if unit_system == "SI" else "psi"

    p_factor = 1.0 if unit_system == "SI" else BAR_TO_PSI

    st.markdown(section_header_html("Process & Valve Conditions"), unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        if result.P1_bar and result.P2_bar:
            dp = result.P1_bar - result.P2_bar
            st.markdown(
                metric_card_html(
                    "ΔP Available",
                    f"{dp * p_factor:.3f}",
                    dp_unit,
                    status="ok",
                ),
                unsafe_allow_html=True,
            )
        if result.delta_P_max_bar:
            st.markdown(
                metric_card_html(
                    "ΔP Max (Choked)",
                    f"{result.delta_P_max_bar * p_factor:.3f}",
                    dp_unit,
                    status="warn" if result.is_choked else "info",
                ),
                unsafe_allow_html=True,
            )

    with col_b:
        if result.Fp and result.Fp != 1.0:
            st.markdown(
                metric_card_html(
                    "Fp (Piping Factor)",
                    f"{result.Fp:.4f}",
                    "",
                    delta="Reducers detected" if result.Fp < 0.99 else "",
                    status="warn" if result.Fp < 0.95 else "ok",
                ),
                unsafe_allow_html=True,
            )

        if result.fluid_phase == FluidPhase.GAS:
            if result.Y_expansion:
                st.markdown(
                    metric_card_html(
                        "Y (Expansion Factor)",
                        f"{result.Y_expansion:.4f}",
                        "",
                        status="ok",
                    ),
                    unsafe_allow_html=True,
                )
            if result.Fk:
                st.markdown(
                    metric_card_html("Fk = γ/1.4", f"{result.Fk:.4f}", "", status="info"),
                    unsafe_allow_html=True,
                )

    # Cavitation metrics (liquid only)
    if result.fluid_phase == FluidPhase.LIQUID and result.cavitation:
        cav = result.cavitation
        st.markdown(section_header_html("Cavitation Analysis"), unsafe_allow_html=True)

        regime = cav.regime
        regime_colours = {
            CavitationRegime.NONE:      ("#375623", "✅"),
            CavitationRegime.INCIPIENT: ("#7f6000", "🟡"),
            CavitationRegime.CONSTANT:  ("#c55a11", "🟠"),
            CavitationRegime.CHOKED:    ("#c00000", "🔴"),
            CavitationRegime.FLASHING:  ("#c00000", "🔴"),
        }
        colour, icon = regime_colours.get(regime, ("#000", "ℹ"))

        st.markdown(
            f'<div style="background:#f5f7fa;border:1px solid {colour};'
            f'border-left:5px solid {colour};border-radius:8px;padding:0.7rem 1rem;">'
            f'<b>{icon} Cavitation Regime: {cav.regime.value.upper()}</b><br>'
            f'<span style="font-size:0.85rem;color:#444;">{cav.severity_label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if cav.sigma is not None:
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("σ (Cavitation Index)", f"{cav.sigma:.3f}")
            with col_s2:
                if cav.sigma_incipient:
                    st.metric("σ Incipient", f"{cav.sigma_incipient:.3f}")
            with col_s3:
                if cav.sigma_choked:
                    st.metric("σ Choked", f"{cav.sigma_choked:.3f}")

        if cav.recommendation:
            st.info(cav.recommendation)

    # Viscosity correction
    if result.is_viscous_corrected and result.FR:
        st.markdown(section_header_html("Viscous Correction"), unsafe_allow_html=True)
        col_rev, col_fr = st.columns(2)
        with col_rev:
            st.metric("Valve Reynolds Number Rev", f"{result.Rev:,.0f}" if result.Rev else "—")
        with col_fr:
            st.metric("Viscosity Correction FR", f"{result.FR:.4f}" if result.FR else "—")
        if result.FR and result.FR < 0.9:
            st.warning(
                "⚠ Significant viscous correction (FR < 0.9). "
                "The effective Cv is reduced by the FR factor. "
                "Verify selection with manufacturer's viscous flow data."
            )


def _render_detailed_table(result: SizingResult, unit_system: str) -> None:
    """Render a detailed tabular summary of all calculated values."""
    st.markdown(section_header_html("Detailed Calculation Summary"), unsafe_allow_html=True)

    p_unit  = "bar a" if unit_system == "SI" else "psia"
    dp_unit = "bar"   if unit_system == "SI" else "psi"
    p_factor = 1.0 if unit_system == "SI" else BAR_TO_PSI

    rows: list[dict] = []

    def _add(param: str, value: str, unit: str = "", note: str = "") -> None:
        rows.append({"Parameter": param, "Value": value, "Unit": unit, "Note": note})

    _add("Fluid Phase", result.fluid_phase.value)
    _add("Flow Regime", result.flow_regime)

    if result.Cv_required:
        _add("Cv Required", f"{result.Cv_required:.4f}", "", "At design conditions")
    if result.Cv_margin:
        _add("Cv with Margin", f"{result.Cv_margin:.4f}", "", f"+{result.sizing_ratio and 0:.0f}% margin")
    if result.Kv_required:
        _add("Kv Required", f"{result.Kv_required:.4f}", "", "Kv = Cv × 0.8646")
    if result.sizing_ratio:
        _add("Sizing Ratio", f"{result.sizing_ratio:.4f}", "", "Cv_req / Cv_rated")
    if result.opening_pct:
        _add("Opening %", f"{result.opening_pct:.1f}", "%", "Estimated from inherent char.")

    if result.P1_bar:
        _add("P1 (absolute)", f"{result.P1_bar * p_factor:.4f}", p_unit)
    if result.P2_bar:
        _add("P2 (absolute)", f"{result.P2_bar * p_factor:.4f}", p_unit)
    if result.P1_bar and result.P2_bar:
        _add("ΔP Available", f"{(result.P1_bar - result.P2_bar) * p_factor:.4f}", dp_unit)
    if result.delta_P_max_bar:
        _add("ΔP Max (Choked)", f"{result.delta_P_max_bar * p_factor:.4f}", dp_unit)

    if result.Fp and result.Fp != 1.0:
        _add("Fp (Piping Factor)", f"{result.Fp:.5f}", "", "IEC 60534-2-1 §6.1")
    if result.fluid_phase == FluidPhase.LIQUID and result.FLP:
        _add("FLP", f"{result.FLP:.5f}", "", "Combined FL·Fp factor")
    if result.fluid_phase == FluidPhase.GAS and result.xTP:
        _add("xTP", f"{result.xTP:.5f}", "", "Gas choked-flow ratio with piping")

    if result.Y_expansion:
        _add("Y (Gas Expansion Factor)", f"{result.Y_expansion:.5f}")
    if result.Fk:
        _add("Fk = γ/1.4", f"{result.Fk:.4f}")
    if result.x_pressure_ratio:
        _add("x = ΔP/P1", f"{result.x_pressure_ratio:.5f}")

    if result.rho1_kgm3:
        _add("ρ1 (Inlet Density)", f"{result.rho1_kgm3:.4f}", "kg/m³")
    if result.mu_cP:
        _add("μ (Viscosity)", f"{result.mu_cP:.4f}", "cP")
    if result.Rev:
        _add("Rev (Valve Reynolds No.)", f"{result.Rev:,.0f}")
    if result.FR:
        _add("FR (Viscosity Correction)", f"{result.FR:.5f}")

    if result.v_inlet_ms:
        _add("v Inlet", f"{result.v_inlet_ms:.2f}", "m/s")
    if result.v_outlet_ms:
        _add("v Outlet", f"{result.v_outlet_ms:.2f}", "m/s")

    if result.cavitation:
        cav = result.cavitation
        if cav.sigma is not None:
            _add("σ (Cavitation Index)", f"{cav.sigma:.4f}")
        if cav.FL:
            _add("FL Used", f"{cav.FL:.4f}")
        if cav.FF:
            _add("FF (Critical Pressure Ratio)", f"{cav.FF:.4f}")

    if result.noise and result.noise.overall_Lpe_dba is not None:
        n = result.noise
        _add("Lpe [dB(A)]", f"{n.overall_Lpe_dba:.1f}", "dB(A)", "External SPL at 1 m")
        if n.Lpi_db:
            _add("Lpi [dB]", f"{n.Lpi_db:.1f}", "dB re 1pW", "Internal sound power level")
        if n.TL_db:
            _add("TL [dB]", f"{n.TL_db:.1f}", "dB", "Pipe wall transmission loss")
        if n.Mvc:
            _add("Mvc (Mach at VC)", f"{n.Mvc:.4f}")
        if n.eta_acoustic:
            _add("η_a (Acoustic Efficiency)", f"{n.eta_acoustic:.2e}", "", "Baumann (1987) / IEC 8-3")

    import pandas as pd
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True, height=450)
