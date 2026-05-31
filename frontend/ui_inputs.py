"""
frontend/ui_inputs.py
=====================
All input widgets for the Control Valve Sizer.

This module contains ONLY Streamlit widget code — zero math.
It returns plain Python dicts consumed by build_sizing_inputs(),
which converts them into the SizingInputs Pydantic model.

v2.0 additions
--------------
- Fluid library preset dropdown (60+ fluids from data/fluid_presets.json)
- Auto-fill fluid properties from preset selection
- Tag / case name fields
- System ΔP fraction input for installed characteristic
- Actuator inputs
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import streamlit as st

from backend.constants import (
    BAR_TO_PSI, INCH_TO_MM, KGH_TO_LBH, M3H_TO_GPM, MM_TO_INCH, PSI_TO_BAR,
    VALVE_PRESETS,
)
from backend.models import (
    ActuatorType, FailPosition, FlowBasis, FluidPhase, SizingInputs,
    UnitSystem, ValveCharacteristic,
)
from frontend.ui_styles import section_header_html

# ---------------------------------------------------------------------------
# Load fluid presets from JSON
# ---------------------------------------------------------------------------

_FLUID_JSON_PATH = Path(__file__).parent.parent / "data" / "fluid_presets.json"

@st.cache_data(show_spinner=False)
def _load_fluid_presets() -> dict[str, list[dict]]:
    """Load fluid presets from JSON file (cached)."""
    try:
        with open(_FLUID_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Remove meta keys
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except Exception:
        return {}


def _build_fluid_options(phase: str) -> dict[str, dict]:
    """
    Build {display_name: properties_dict} for fluids matching the given phase.

    Parameters
    ----------
    phase : str
        "Liquid", "Gas", or "Steam".

    Returns
    -------
    dict[str, dict]
        Ordered dict of fluid display names → property dicts.
    """
    presets = _load_fluid_presets()
    options: dict[str, dict] = {"— Select a fluid preset —": {}}

    for category, fluids in presets.items():
        for fluid in fluids:
            if fluid.get("phase", "") == phase:
                display = f"{category.replace('_', ' ')} | {fluid['name']}"
                options[display] = fluid
    return options


# ---------------------------------------------------------------------------
# Sidebar global settings
# ---------------------------------------------------------------------------

def render_sidebar_globals() -> dict[str, Any]:
    """
    Render global application settings in the sidebar.

    Returns
    -------
    dict with keys:
        unit_system, fluid_phase, calculate_clicked,
        sizing_margin_pct, noise_limit_dba
    """
    from frontend.ui_styles import render_sidebar_branding
    render_sidebar_branding()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Global Settings")

    unit_system = st.sidebar.radio(
        "Unit System",
        options=["SI", "US"],
        index=0,
        horizontal=True,
        help=(
            "**SI**: bar, m³/h, mm, °C, kg/h  \n"
            "**US**: psia, GPM, inches, °F, lb/h"
        ),
        key="sb_unit_system",
    )

    fluid_phase = st.sidebar.selectbox(
        "Fluid Phase",
        options=["Liquid", "Gas", "Steam"],
        index=0,
        help="Select the fluid phase for sizing equations",
        key="sb_fluid_phase",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 Sizing Options")

    sizing_margin_pct = st.sidebar.slider(
        "Sizing Margin (%)",
        min_value=0,
        max_value=30,
        value=10,
        step=5,
        help=(
            "Additional Cv margin applied on top of calculated Cv_required. "
            "API RP 553 recommends 10–20% for general service. "
            "Use 0% for minimum-size selection."
        ),
        key="sb_sizing_margin",
    )

    noise_limit_dba = st.sidebar.number_input(
        "Site Noise Limit [dB(A)]",
        min_value=50.0,
        max_value=120.0,
        value=85.0,
        step=5.0,
        help=(
            "Maximum permissible SPL at 1 m from pipe. "
            "Typical limits: 85 dB(A) occupied areas, 90 dB(A) process areas."
        ),
        key="sb_noise_limit",
    )

    st.sidebar.markdown("---")

    calculate_clicked = st.sidebar.button(
        "🔬  CALCULATE",
        type="primary",
        use_container_width=True,
        key="btn_calculate",
        help="Run the full sizing calculation with current inputs.",
    )

    return {
        "unit_system": unit_system,
        "fluid_phase": fluid_phase,
        "calculate_clicked": calculate_clicked,
        "sizing_margin_pct": float(sizing_margin_pct),
        "noise_limit_dba": noise_limit_dba,
    }


# ---------------------------------------------------------------------------
# Process conditions
# ---------------------------------------------------------------------------

def render_process_conditions(unit_system: str, fluid_phase: str) -> dict[str, Any]:
    """
    Render process condition inputs.

    Returns
    -------
    dict with keys: P1_gauge, P2_gauge, T1, flow_value, flow_basis, tag, case_name
    """
    st.markdown(section_header_html("Instrument Identification"), unsafe_allow_html=True)

    col_tag, col_case = st.columns(2)
    with col_tag:
        tag = st.text_input(
            "Tag Number",
            value="FV-101",
            max_chars=30,
            placeholder="FV-101",
            key="inp_tag",
            help="Instrument tag / valve tag for identification in reports.",
        )
    with col_case:
        case_name = st.text_input(
            "Case Name / Description",
            value="Design Case",
            max_chars=80,
            placeholder="e.g. Normal Flow, Max Flow",
            key="inp_case_name",
        )

    st.markdown(section_header_html("Process Conditions"), unsafe_allow_html=True)

    if unit_system == "SI":
        p_unit = "bar g"
        t_unit = "°C"
        flow_vol_unit = "m³/h"
        flow_mass_unit = "kg/h"
        flow_std_unit = "Nm³/h"
    else:
        p_unit = "psig"
        t_unit = "°F"
        flow_vol_unit = "GPM"
        flow_mass_unit = "lb/h"
        flow_std_unit = "SCFH"

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        P1_gauge = st.number_input(
            f"Inlet Pressure P1 [{p_unit}]",
            min_value=0.0,
            max_value=1e6,
            value=10.0,
            step=0.5,
            format="%.3f",
            key="inp_P1",
            help="Upstream valve pressure (gauge). Atmospheric is added internally.",
        )
    with col_p2:
        P2_gauge = st.number_input(
            f"Outlet Pressure P2 [{p_unit}]",
            min_value=0.0,
            max_value=1e6,
            value=8.0,
            step=0.5,
            format="%.3f",
            key="inp_P2",
            help="Downstream valve pressure (gauge). Must be less than P1.",
        )

    if P1_gauge <= P2_gauge:
        st.warning("⚠ P1 must be greater than P2 (positive differential pressure).")

    col_t1, col_flow = st.columns(2)
    with col_t1:
        t_default = 20.0 if unit_system == "SI" else 68.0
        T1 = st.number_input(
            f"Inlet Temperature T1 [{t_unit}]",
            min_value=-200.0 if unit_system == "SI" else -328.0,
            max_value=800.0 if unit_system == "SI" else 1472.0,
            value=t_default,
            step=1.0,
            format="%.1f",
            key="inp_T1",
            help="Fluid temperature at valve inlet.",
        )

    with col_flow:
        if fluid_phase == "Gas":
            flow_basis_opts = [FlowBasis.MASS, FlowBasis.VOLUMETRIC, FlowBasis.STANDARD]
        elif fluid_phase == "Liquid":
            flow_basis_opts = [FlowBasis.VOLUMETRIC, FlowBasis.MASS]
        else:  # Steam
            flow_basis_opts = [FlowBasis.MASS, FlowBasis.VOLUMETRIC]

        basis_labels = {
            FlowBasis.VOLUMETRIC: flow_vol_unit,
            FlowBasis.MASS: flow_mass_unit,
            FlowBasis.STANDARD: flow_std_unit,
        }
        flow_basis = st.selectbox(
            "Flow Basis",
            options=flow_basis_opts,
            format_func=lambda b: f"{b.value} [{basis_labels[b]}]",
            key="inp_flow_basis",
            help=(
                "Select flow rate basis. Mass flow is recommended for gas/steam "
                "to avoid ambiguity in standard conditions."
            ),
        )

    flow_unit_lbl = basis_labels[flow_basis]
    flow_value = st.number_input(
        f"Flow Rate [{flow_unit_lbl}]",
        min_value=1e-6,
        max_value=1e9,
        value=100.0,
        step=1.0,
        format="%.4f",
        key="inp_flow_value",
        help=(
            f"Process flow rate in {flow_unit_lbl}. "
            "This is the design flow condition."
        ),
    )

    return {
        "P1_gauge": P1_gauge,
        "P2_gauge": P2_gauge,
        "T1": T1,
        "flow_value": flow_value,
        "flow_basis": flow_basis,
        "tag": tag,
        "case_name": case_name,
    }


# ---------------------------------------------------------------------------
# Fluid properties
# ---------------------------------------------------------------------------

def render_fluid_properties(unit_system: str, fluid_phase: str) -> dict[str, Any]:
    """
    Render fluid property inputs with optional preset lookup.

    Returns
    -------
    dict with keys: Gf, Pv, Pc, mu (liquid); M, gamma, Z (gas/steam);
    plus: fluid_name, steam_quality
    """
    st.markdown(section_header_html("Fluid Properties"), unsafe_allow_html=True)

    # ── Fluid preset selector ────────────────────────────────────────────────
    if fluid_phase in ("Liquid", "Gas"):
        fluid_options = _build_fluid_options(fluid_phase)
        option_keys = list(fluid_options.keys())

        selected_preset_key = st.selectbox(
            "📋 Fluid Library (optional — auto-fills properties below)",
            options=option_keys,
            index=0,
            key=f"inp_fluid_preset_{fluid_phase}",
            help=(
                "Select a common fluid to auto-populate properties. "
                "You can override any field manually after selection."
            ),
        )
        preset = fluid_options.get(selected_preset_key, {})
        fluid_name = preset.get("name", "")

        if preset and fluid_name:
            st.success(
                f"✅ Preset loaded: **{fluid_name}** "
                f"(ref. T = {preset.get('ref_T_C', '?')} °C). "
                "Verify properties for your actual operating conditions."
            )
            if preset.get("notes"):
                st.info(f"ℹ {preset['notes']}")
    else:
        preset = {}
        fluid_name = "Steam"

    result: dict[str, Any] = {"fluid_name": fluid_name}

    if unit_system == "SI":
        p_unit = "bar a"
        visc_label = "Dynamic Viscosity [cP]"
    else:
        p_unit = "psia"
        visc_label = "Dynamic Viscosity [cP]"

    # ── Liquid properties ────────────────────────────────────────────────────
    if fluid_phase == "Liquid":
        col_gf, col_pv = st.columns(2)

        default_Gf = float(preset.get("Gf", 1.0))
        default_Pv_bara = float(preset.get("Pv_bara", 0.023))
        default_Pc_bara = float(preset.get("Pc_bara", 220.64))
        default_mu = float(preset.get("mu_cP", 1.0))

        # Unit conversion for display
        if unit_system == "US":
            default_Pv = default_Pv_bara * BAR_TO_PSI
            default_Pc = default_Pc_bara * BAR_TO_PSI
        else:
            default_Pv = default_Pv_bara
            default_Pc = default_Pc_bara

        with col_gf:
            Gf = st.number_input(
                "Specific Gravity Gf",
                min_value=0.01,
                max_value=5.0,
                value=round(default_Gf, 4),
                step=0.001,
                format="%.4f",
                key="inp_Gf",
                help="Liquid specific gravity relative to water at 15.6°C (60°F). Gf = ρ_liquid / 999 kg/m³.",
            )
        with col_pv:
            Pv = st.number_input(
                f"Vapour Pressure Pv [{p_unit}]",
                min_value=0.0,
                max_value=1e4,
                value=round(default_Pv, 4),
                step=0.001,
                format="%.4f",
                key="inp_Pv",
                help="Liquid vapour pressure at inlet temperature. Used for cavitation and flashing checks.",
            )

        col_pc, col_mu = st.columns(2)
        with col_pc:
            Pc = st.number_input(
                f"Critical Pressure Pc [{p_unit}]",
                min_value=0.1,
                max_value=1e5,
                value=round(default_Pc, 3),
                step=0.1,
                format="%.3f",
                key="inp_Pc",
                help="Fluid thermodynamic critical pressure. Used to compute FF (critical pressure ratio factor).",
            )
        with col_mu:
            mu = st.number_input(
                visc_label,
                min_value=0.001,
                max_value=1e6,
                value=round(default_mu, 4),
                step=0.001,
                format="%.4f",
                key="inp_mu",
                help=(
                    "Dynamic viscosity at operating temperature [cP = mPa·s]. "
                    "Values > 1 cP trigger viscous correction factor FR calculation."
                ),
            )

        result.update({"Gf": Gf, "Pv": Pv, "Pc": Pc, "mu": mu})

    # ── Gas properties ────────────────────────────────────────────────────────
    elif fluid_phase == "Gas":
        default_M   = float(preset.get("M_gmol", 29.0))
        default_gamma = float(preset.get("gamma", 1.40))
        default_Z   = float(preset.get("Z", 1.00))

        col_m, col_gamma = st.columns(2)
        with col_m:
            M = st.number_input(
                "Molecular Weight M [g/mol]",
                min_value=1.0,
                max_value=300.0,
                value=round(default_M, 3),
                step=0.1,
                format="%.3f",
                key="inp_M",
                help="Molecular weight of the gas. Air = 28.97, methane = 16.04, hydrogen = 2.016.",
            )
        with col_gamma:
            gamma = st.number_input(
                "Specific Heat Ratio γ (Cp/Cv)",
                min_value=1.01,
                max_value=2.0,
                value=round(default_gamma, 3),
                step=0.01,
                format="%.3f",
                key="inp_gamma",
                help="Ratio of specific heats. Diatomic: γ ≈ 1.40; polyatomic: γ < 1.40.",
            )

        col_z, _ = st.columns(2)
        with col_z:
            Z = st.number_input(
                "Compressibility Factor Z",
                min_value=0.1,
                max_value=2.0,
                value=round(default_Z, 4),
                step=0.001,
                format="%.4f",
                key="inp_Z",
                help=(
                    "Real-gas compressibility factor at inlet conditions. "
                    "Z = 1.0 for ideal gas. Use NIST WebBook or process simulator for accurate Z."
                ),
            )

        result.update({"M": M, "gamma": gamma, "Z": Z})

    # ── Steam properties ──────────────────────────────────────────────────────
    elif fluid_phase == "Steam":
        st.info(
            "♨️ **Steam service:** All thermodynamic properties "
            "(ρ, h, s, μ) are computed automatically from **IAPWS-IF97** "
            "at your specified P1 and T1. Only specify steam quality for wet steam."
        )
        steam_quality = st.slider(
            "Steam Quality x (1.0 = dry/superheated, <1.0 = wet steam)",
            min_value=0.50,
            max_value=1.00,
            value=1.00,
            step=0.01,
            key="inp_steam_quality",
            help=(
                "1.0 = superheated or dry saturated steam. "
                "0.85–0.99 = wet steam (use with caution). "
                "< 0.85 = erosive; avoid control valves in this range."
            ),
        )
        if steam_quality < 0.85:
            st.warning(
                "⚠ Steam quality < 0.85 — wet steam is highly erosive. "
                "Hardened trim and angle body are strongly recommended."
            )
        result["steam_quality"] = steam_quality

    return result


# ---------------------------------------------------------------------------
# Valve parameters
# ---------------------------------------------------------------------------

def render_valve_parameters(unit_system: str) -> dict[str, Any]:
    """
    Render valve geometry and characteristic inputs.

    Returns
    -------
    dict with keys: FL, xT, Fd, d, D1, D2, Cv_rated, R_inherent, char,
    pipe_schedule, valve_type, system_dp_fraction, actuator_type,
    supply_pressure_bar, fail_position, packing_type
    """
    st.markdown(section_header_html("Valve Parameters"), unsafe_allow_html=True)

    size_unit = "mm" if unit_system == "SI" else "in"

    # ── Valve type preset ───────────────────────────────────────────────────
    valve_types = list(VALVE_PRESETS.keys())
    valve_type = st.selectbox(
        "Valve Type",
        options=valve_types,
        index=0,
        key="inp_valve_type",
        help=(
            "Select valve type to auto-populate FL, xT, Fd. "
            "You can override individual values below."
        ),
    )
    preset_v = VALVE_PRESETS[valve_type]

    col_fl, col_xt, col_fd = st.columns(3)
    with col_fl:
        FL = st.number_input(
            "FL  (Pressure Recovery)",
            min_value=0.10, max_value=0.99,
            value=float(preset_v["FL"]),
            step=0.01, format="%.3f",
            key="inp_FL",
            help=(
                "Liquid pressure recovery factor. Ranges from ~0.5 (butterfly) "
                "to ~0.9 (globe). Affects choked flow and cavitation limits."
            ),
        )
    with col_xt:
        xT = st.number_input(
            "xT  (Pressure Drop Ratio)",
            min_value=0.10, max_value=0.99,
            value=float(preset_v["xT"]),
            step=0.01, format="%.3f",
            key="inp_xT",
            help=(
                "Terminal pressure drop ratio factor (gas). "
                "xT determines the onset of choked gas flow."
            ),
        )
    with col_fd:
        Fd = st.number_input(
            "Fd  (Valve Style Modifier)",
            min_value=0.10, max_value=1.00,
            value=float(preset_v["Fd"]),
            step=0.01, format="%.3f",
            key="inp_Fd",
            help=(
                "Valve style modifier — ratio of hydraulic diameter of a single "
                "flow passage to the diameter of a circle of equal area. "
                "Used in noise and viscous corrections."
            ),
        )

    st.markdown(section_header_html("Valve and Pipe Geometry"), unsafe_allow_html=True)

    col_d, col_D1, col_D2 = st.columns(3)
    with col_d:
        d_default = 50.0 if unit_system == "SI" else 2.0
        d = st.number_input(
            f"Valve Bore d [{size_unit}]",
            min_value=5.0 if unit_system == "SI" else 0.2,
            max_value=2000.0 if unit_system == "SI" else 80.0,
            value=d_default,
            step=1.0 if unit_system == "SI" else 0.25,
            format="%.1f",
            key="inp_d",
            help="Internal diameter of the valve flow passage (valve bore).",
        )
    with col_D1:
        D1_default = 50.0 if unit_system == "SI" else 2.0
        D1 = st.number_input(
            f"Upstream Pipe ID D1 [{size_unit}]",
            min_value=5.0 if unit_system == "SI" else 0.2,
            max_value=3000.0 if unit_system == "SI" else 120.0,
            value=D1_default,
            step=1.0 if unit_system == "SI" else 0.25,
            format="%.1f",
            key="inp_D1",
            help="Internal diameter of the upstream pipe (for piping correction factor Fp).",
        )
    with col_D2:
        D2_default = 50.0 if unit_system == "SI" else 2.0
        D2 = st.number_input(
            f"Downstream Pipe ID D2 [{size_unit}]",
            min_value=5.0 if unit_system == "SI" else 0.2,
            max_value=3000.0 if unit_system == "SI" else 120.0,
            value=D2_default,
            step=1.0 if unit_system == "SI" else 0.25,
            format="%.1f",
            key="inp_D2",
            help="Internal diameter of the downstream pipe (for piping correction and noise TL).",
        )

    # Reduce: d > D1 warning
    if d > D1 + 0.5:
        st.warning(
            f"⚠ Valve bore ({d:.1f} {size_unit}) cannot exceed pipe ID "
            f"({D1:.1f} {size_unit}). Adjust your geometry."
        )

    col_cv, col_sched = st.columns(2)
    with col_cv:
        cv_rated_enabled = st.checkbox(
            "Enter Rated Cv",
            value=True,
            key="inp_cv_rated_enable",
            help="Check to specify the manufacturer's rated Cv. Enables sizing ratio and opening % calculation.",
        )
        Cv_rated: float | None = None
        if cv_rated_enabled:
            Cv_rated = st.number_input(
                "Rated Cv (at full open)",
                min_value=0.01,
                max_value=1e7,
                value=120.0,
                step=1.0,
                format="%.2f",
                key="inp_Cv_rated",
                help="Valve manufacturer's Cv at 100% travel. Used to compute sizing ratio.",
            )
    with col_sched:
        pipe_schedule = st.selectbox(
            "Pipe Schedule (for noise TL)",
            options=["Sch 10", "Sch 20", "Sch 40", "Sch 80", "Sch 120", "Sch 160", "XXH"],
            index=2,
            key="inp_pipe_sched",
            help="Pipe wall schedule — used to look up wall thickness for noise transmission loss calculation.",
        )

    st.markdown(section_header_html("Flow Characteristic"), unsafe_allow_html=True)

    col_char, col_R = st.columns(2)
    with col_char:
        char_map = {
            "Equal Percentage": ValveCharacteristic.EQUAL_PERCENTAGE,
            "Linear": ValveCharacteristic.LINEAR,
            "Quick Opening": ValveCharacteristic.QUICK_OPENING,
        }
        char_label = st.selectbox(
            "Inherent Characteristic",
            options=list(char_map.keys()),
            index=0,
            key="inp_char",
            help=(
                "Inherent valve flow characteristic (lab conditions). "
                "Equal-percentage is most common for liquid and gas throttling control."
            ),
        )
        char = char_map[char_label]
    with col_R:
        R_inherent = st.number_input(
            "Rangeability R",
            min_value=10.0, max_value=500.0,
            value=float(preset_v.get("R_inherent", 50.0)),
            step=5.0, format="%.0f",
            key="inp_R_inherent",
            help=(
                "Inherent rangeability (Cv_max / Cv_min at rated conditions). "
                "Globe valves: typically 50:1. Ball/butterfly: typically 30:1."
            ),
        )

    # ── Installed characteristic input ──────────────────────────────────────
    st.markdown(section_header_html("System Pressure Split (for Installed Curve)"), unsafe_allow_html=True)

    system_dp_fraction = st.slider(
        "Valve ΔP / Total System ΔP at Design Flow  (β)",
        min_value=0.05,
        max_value=1.00,
        value=0.50,
        step=0.05,
        format="%.2f",
        key="inp_beta",
        help=(
            "β = ΔP_valve / ΔP_system at design flow. "
            "β = 1.0: all ΔP across valve (fully valve-controlled system). "
            "β = 0.5: 50/50 split. "
            "β < 0.25: installed characteristic severely distorted — poor control."
        ),
    )
    if system_dp_fraction < 0.25:
        st.warning(
            "⚠ β < 0.25: Very low valve authority. "
            "Installed characteristic will be significantly distorted from inherent. "
            "Consider increasing valve ΔP allocation."
        )

    # ── Actuator inputs ─────────────────────────────────────────────────────
    with st.expander("🔩 Actuator Inputs (for Actuator Guidance tab)", expanded=False):
        col_act, col_fail = st.columns(2)
        with col_act:
            act_map = {
                "Pneumatic Diaphragm": ActuatorType.PNEUMATIC_DIAPHRAGM,
                "Pneumatic Piston": ActuatorType.PNEUMATIC_PISTON,
                "Electric": ActuatorType.ELECTRIC,
            }
            actuator_label = st.selectbox(
                "Actuator Type",
                options=list(act_map.keys()),
                key="inp_actuator_type",
            )
            actuator_type = act_map[actuator_label]
        with col_fail:
            fail_map = {
                "Fail Closed": FailPosition.FAIL_CLOSED,
                "Fail Open": FailPosition.FAIL_OPEN,
            }
            fail_label = st.selectbox(
                "Fail Position",
                options=list(fail_map.keys()),
                key="inp_fail_pos",
            )
            fail_position = fail_map[fail_label]

        col_sp, col_pack = st.columns(2)
        with col_sp:
            supply_pressure_bar = st.number_input(
                "Supply Pressure [bar g]",
                min_value=1.0, max_value=15.0,
                value=5.5, step=0.5, format="%.1f",
                key="inp_supply_press",
                help="Actuator air/gas supply pressure in bar g. Typical: 4–7 bar g.",
            )
        with col_pack:
            packing_type = st.selectbox(
                "Packing Type",
                options=["PTFE", "Graphite", "PTFE/Graphite Composite", "Live-Loaded PTFE"],
                key="inp_packing",
                help="Stem packing material — affects friction force estimate.",
            )

    return {
        "FL": FL,
        "xT": xT,
        "Fd": Fd,
        "d": d,
        "D1": D1,
        "D2": D2,
        "Cv_rated": Cv_rated,
        "R_inherent": R_inherent,
        "char": char,
        "pipe_schedule": pipe_schedule,
        "valve_type": valve_type,
        "system_dp_fraction": system_dp_fraction,
        "actuator_type": actuator_type,
        "supply_pressure_bar": supply_pressure_bar,
        "fail_position": fail_position,
        "packing_type": packing_type,
    }


# ---------------------------------------------------------------------------
# Build SizingInputs model
# ---------------------------------------------------------------------------

def build_sizing_inputs(
    sidebar_vals: dict[str, Any],
    process_vals: dict[str, Any],
    fluid_vals: dict[str, Any],
    valve_vals: dict[str, Any],
) -> SizingInputs:
    """
    Assemble a SizingInputs Pydantic model from the four input dicts.

    Unit conversions
    ----------------
    All pressures → bar a (SI absolute)
    All temperatures → K
    All lengths → mm
    Flow kept in its native units; the orchestrator handles conversion with N-factors.

    Parameters
    ----------
    sidebar_vals : dict
        From render_sidebar_globals()
    process_vals : dict
        From render_process_conditions()
    fluid_vals : dict
        From render_fluid_properties()
    valve_vals : dict
        From render_valve_parameters()

    Returns
    -------
    SizingInputs
        Validated Pydantic model ready for run_sizing().
    """
    unit_system = sidebar_vals["unit_system"]
    fluid_phase = sidebar_vals["fluid_phase"]

    # ── Pressure (gauge → absolute) ─────────────────────────────────────────
    if unit_system == "SI":
        atm = 1.01325  # bar
        P1_bara = process_vals["P1_gauge"] + atm
        P2_bara = process_vals["P2_gauge"] + atm
    else:
        atm = 14.696   # psia
        P1_psia = process_vals["P1_gauge"] + atm
        P2_psia = process_vals["P2_gauge"] + atm
        P1_bara = P1_psia * PSI_TO_BAR
        P2_bara = P2_psia * PSI_TO_BAR

    # ── Temperature → K ─────────────────────────────────────────────────────
    T1_raw = process_vals["T1"]
    if unit_system == "SI":
        T1_K = T1_raw + 273.15
    else:
        T1_K = (T1_raw - 32.0) * 5.0 / 9.0 + 273.15

    # ── Fluid properties (unit conversion if needed) ─────────────────────────
    if fluid_phase == "Liquid":
        Gf = float(fluid_vals["Gf"])
        if unit_system == "SI":
            Pv_bara = float(fluid_vals["Pv"])
            Pc_bara = float(fluid_vals["Pc"])
        else:
            Pv_bara = float(fluid_vals["Pv"]) * PSI_TO_BAR
            Pc_bara = float(fluid_vals["Pc"]) * PSI_TO_BAR
        mu_cP = float(fluid_vals["mu"])
        M = 18.015
        gamma = 1.0
        Z = 1.0
    elif fluid_phase == "Gas":
        Gf = 1.0
        Pv_bara = 0.0
        Pc_bara = 50.0
        mu_cP = 0.015
        M = float(fluid_vals["M"])
        gamma = float(fluid_vals["gamma"])
        Z = float(fluid_vals["Z"])
    else:  # Steam
        Gf = 1.0
        Pv_bara = P1_bara  # Pv ≈ saturation pressure at T1 for steam
        Pc_bara = 220.64   # Water critical pressure
        mu_cP = 0.025
        M = 18.015
        gamma = 1.33
        Z = 1.0

    # ── Flow (convert to SI native if US) ────────────────────────────────────
    flow_value = float(process_vals["flow_value"])
    flow_basis = process_vals["flow_basis"]
    if unit_system == "US":
        if flow_basis == FlowBasis.VOLUMETRIC:
            flow_value = flow_value / M3H_TO_GPM  # GPM → m³/h
        elif flow_basis == FlowBasis.MASS:
            flow_value = flow_value / KGH_TO_LBH   # lb/h → kg/h
        # Standard volumetric (SCFH) kept as-is; orchestrator handles N9

    # ── Valve geometry (US → mm) ─────────────────────────────────────────────
    d_mm  = valve_vals["d"]  * (INCH_TO_MM if unit_system == "US" else 1.0)
    D1_mm = valve_vals["D1"] * (INCH_TO_MM if unit_system == "US" else 1.0)
    D2_mm = valve_vals["D2"] * (INCH_TO_MM if unit_system == "US" else 1.0)

    # ── Steam quality ────────────────────────────────────────────────────────
    steam_quality = float(fluid_vals.get("steam_quality", 1.0))

    return SizingInputs(
        tag_number=process_vals.get("tag", ""),
        case_name=process_vals.get("case_name", ""),
        unit_system=UnitSystem(unit_system),
        fluid_phase=FluidPhase(fluid_phase),
        P1_bara=P1_bara,
        P2_bara=P2_bara,
        T1_K=T1_K,
        flow_value=flow_value,
        flow_basis=flow_basis,
        # Liquid
        Gf=Gf,
        Pv_bara=Pv_bara,
        Pc_bara=Pc_bara,
        viscosity_cP=mu_cP,
        # Gas
        molecular_weight=M,
        gamma=gamma,
        compressibility_Z=Z,
        # Steam
        steam_quality=steam_quality,
        # Valve
        FL=float(valve_vals["FL"]),
        xT=float(valve_vals["xT"]),
        Fd=float(valve_vals["Fd"]),
        d_mm=d_mm,
        D1_mm=D1_mm,
        D2_mm=D2_mm,
        Cv_rated=float(valve_vals["Cv_rated"]) if valve_vals.get("Cv_rated") else None,
        pipe_schedule=str(valve_vals.get("pipe_schedule", "Sch 40")),
        valve_type=str(valve_vals.get("valve_type", "Globe Single-Seat")),
        char=valve_vals["char"],
        sizing_margin_pct=float(sidebar_vals["sizing_margin_pct"]),
        noise_limit_dba=float(sidebar_vals["noise_limit_dba"]),
        # New feature inputs
        system_dp_fraction=float(valve_vals.get("system_dp_fraction", 0.5)),
        actuator_type=valve_vals.get("actuator_type", ActuatorType.PNEUMATIC_DIAPHRAGM),
        supply_pressure_bar=float(valve_vals.get("supply_pressure_bar", 5.5)),
        fail_position=valve_vals.get("fail_position", FailPosition.FAIL_CLOSED),
        packing_type=str(valve_vals.get("packing_type", "PTFE")),
    )
