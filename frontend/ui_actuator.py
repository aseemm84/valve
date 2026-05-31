"""
frontend/ui_actuator.py  — Actuator Sizing Guidance tab
"""
from __future__ import annotations
import streamlit as st
from backend.actuator_guidance import calculate_actuator_guidance
from backend.models import SizingInputs, SizingResult
from frontend.ui_styles import section_header_html


def render_actuator(result: SizingResult, inputs: SizingInputs) -> None:
    st.markdown("## 🔩 Actuator Sizing Guidance")
    st.markdown(
        "Preliminary actuator sizing based on unbalanced stem force, packing friction, "
        "and seat load. These are **estimates** for selection guidance only — confirm with "
        "the valve and actuator manufacturer."
    )

    if not result.success or result.Cv_required is None:
        st.info("ℹ Run a successful calculation first.")
        return

    # ── Override inputs ──────────────────────────────────────────────────────
    with st.expander("⚙️ Actuator Input Overrides", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            from backend.models import ActuatorType
            act_labels = {
                "Pneumatic Diaphragm": ActuatorType.PNEUMATIC_DIAPHRAGM,
                "Pneumatic Piston": ActuatorType.PNEUMATIC_PISTON,
                "Electric": ActuatorType.ELECTRIC,
            }
            act_label = st.selectbox("Actuator Type",
                list(act_labels.keys()),
                index=list(act_labels.values()).index(inputs.actuator_type),
                key="act_type_override")
            actuator_type = act_labels[act_label]
        with col2:
            from backend.models import FailPosition
            fail_labels = {"Fail Closed": FailPosition.FAIL_CLOSED, "Fail Open": FailPosition.FAIL_OPEN}
            fail_label = st.selectbox("Fail Position",
                list(fail_labels.keys()),
                index=0, key="act_fail_override")
            fail_position = fail_labels[fail_label]
        with col3:
            supply_pressure = st.number_input("Supply Pressure [bar g]",
                1.0, 15.0, float(inputs.supply_pressure_bar), 0.5, key="act_sp_override")

    try:
        act = calculate_actuator_guidance(
            Cv_required=result.Cv_required,
            d_mm=inputs.d_mm,
            valve_type=inputs.valve_type,
            P1_bara=result.P1_bar or inputs.P1_bara,
            P2_bara=result.P2_bar or inputs.P2_bara,
            actuator_type=actuator_type,
            supply_pressure_bar=supply_pressure,
            fail_position=fail_position,
            packing_type=inputs.packing_type,
        )
    except Exception as exc:
        st.error(f"Actuator calculation error: {exc}")
        return

    # ── Force / torque metrics ────────────────────────────────────────────────
    st.markdown(section_header_html("Force / Thrust Calculation"), unsafe_allow_html=True)

    is_rotary = any(k in inputs.valve_type for k in ["Ball", "Butterfly", "Rotary", "Eccentric"])

    if not is_rotary:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Unbalanced Force", f"{act.unbalanced_force_N:,.0f} N")
        with col2:
            st.metric("Packing Friction", f"{act.packing_friction_N:,.0f} N")
        with col3:
            st.metric("Seat Load", f"{act.seat_load_N:,.0f} N")
        with col4:
            st.metric("Required Thrust (incl. contingency)",
                      f"{act.required_thrust_N_with_contingency:,.0f} N",
                      delta=f"×1.10 contingency")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Break Torque", f"{act.break_torque_Nm:.1f} N·m")
        with col2:
            st.metric("Running Torque", f"{act.run_torque_Nm:.1f} N·m")
        with col3:
            st.metric("Required Torque (with contingency)",
                      f"{act.required_torque_Nm:.1f} N·m")

    # ── Actuator specification ────────────────────────────────────────────────
    st.markdown(section_header_html("Actuator Specification"), unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        if act.diaphragm_area_cm2:
            st.metric("Required Diaphragm / Cylinder Area",
                      f"{act.diaphragm_area_cm2:.0f} cm²")
        if act.spring_range_bar:
            st.metric("Spring Range", f"{act.spring_range_bar} bar g")
        if act.bench_set_bar:
            st.metric("Bench Set", act.bench_set_bar)

    with col_b:
        if act.required_power_W:
            st.metric("Required Motor Power", f"{act.required_power_W:.0f} W")
        if act.recommended_motor_kW:
            st.metric("Recommended Standard Motor", f"{act.recommended_motor_kW:.2f} kW")

    # ── Notes ────────────────────────────────────────────────────────────────
    st.markdown(section_header_html("Engineering Notes"), unsafe_allow_html=True)
    for note in act.notes:
        st.markdown(f"- {note}")
    st.caption(f"⚠ {act.disclaimer}")
