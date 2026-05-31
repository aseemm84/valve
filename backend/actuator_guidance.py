"""
backend/actuator_guidance.py
=============================
Preliminary actuator sizing guidance for control valves.

Methods
-------
For **globe / linear** valves:
  - Unbalanced stem force  F_unbal = π/4 × d_seat² × ΔP_shutoff
  - Packing friction       F_pack  = empirical per stem diameter
  - Required seat load     F_seat  = ISA leakage class factor × π × d_seat
  - Total thrust           F_req   = F_unbal + F_pack + F_seat (with contingency)
  - Diaphragm area         A_d     = F_req / (P_supply × η_eff)

For **rotary** valves (ball, butterfly, eccentric plug):
  - Break torque    T_break = d_trim³ × ΔP × C_T_break
  - Running torque  T_run   = 0.5 × T_break  (approximate)
  - End torque      T_end   = 0.75 × T_break

References
----------
ISA-S75.19-1989 — Hydrostatic Testing of Control Valves
Emerson / Fisher Engineering Manual — Actuator Sizing (public domain sections)
ANSI/ISA-75.25-2000 — Control Valve Response Measurement
Masoneilan — Valve Sizing and Selection Engineering Guide
"""

from __future__ import annotations

import math

from backend.constants import PACKING_FRICTION, VALVE_PRESETS
from backend.models import (
    ActuatorResult,
    ActuatorType,
    FailPosition,
)

# Actuator mechanical efficiency (fraction)
PNEUMATIC_DIAPHRAGM_EFF: float = 0.80
PNEUMATIC_PISTON_EFF: float = 0.90

# Contingency factor on required thrust
THRUST_CONTINGENCY: float = 1.10

# Seat load factors per leakage class (N/mm of seat circumference)
SEAT_LOAD_N_PER_MM: dict[str, float] = {
    "Class II":  15.0,
    "Class III": 25.0,
    "Class IV":  40.0,
    "Class V":   55.0,
    "Class VI":  70.0,  # soft-seat; typically lower actual but higher design margin
}

# Rotary valve torque coefficients (empirical — dim-less)
# T = C_T × d_trim³ × ΔP_shutoff  where d in metres, ΔP in Pa → N·m
ROTARY_TORQUE_COEFF: dict[str, float] = {
    "Ball Valve (Full Bore)":       0.075,
    "Ball Valve (Reduced Bore)":    0.065,
    "Butterfly (High Performance)": 0.040,
    "Butterfly (Wafer)":            0.035,
    "Eccentric Rotary Plug":        0.050,
}


def calculate_actuator_guidance(
    Cv_required: float,
    d_mm: float,
    valve_type: str,
    P1_bara: float,
    P2_bara: float,
    actuator_type: ActuatorType,
    supply_pressure_bar: float,
    fail_position: FailPosition,
    packing_type: str = "PTFE",
    leakage_class: str = "Class IV",
) -> ActuatorResult:
    """
    Compute preliminary actuator sizing parameters.

    Parameters
    ----------
    Cv_required : float
        Required Cv at design conditions.
    d_mm : float
        Valve bore diameter [mm].
    valve_type : str
        Valve type string (from VALVE_PRESETS keys).
    P1_bara : float
        Inlet absolute pressure [bar a].
    P2_bara : float
        Outlet absolute pressure [bar a].
    actuator_type : ActuatorType
        Pneumatic diaphragm, pneumatic piston, or electric.
    supply_pressure_bar : float
        Actuator supply pressure [bar g].
    fail_position : FailPosition
        Fail-open or fail-closed.
    packing_type : str
        Stem packing material (from PACKING_FRICTION keys).
    leakage_class : str
        Required IEC 60534-4 leakage class (for seat load).

    Returns
    -------
    ActuatorResult
        Structured preliminary actuator sizing result.

    Notes
    -----
    All results are **preliminary estimates** intended for actuator
    selection guidance only.  Refer to valve and actuator manufacturer
    data for final sizing.

    Shutoff ΔP is taken as P1 at maximum allowable conditions; since
    exact shut-off pressure class is not specified, P1_bara × 1.1 is
    used as a conservative estimate.
    """
    result = ActuatorResult(
        actuator_type=actuator_type,
        fail_position=fail_position,
        supply_pressure_bar=supply_pressure_bar,
    )

    # ── Shutoff differential pressure ────────────────────────────────────────
    # Conservative: maximum ΔP = full P1 (valve closed against full upstream pressure)
    dP_shutoff_Pa = P1_bara * 1.0e5   # [Pa]

    # ── Seat / trim geometry estimate ─────────────────────────────────────────
    preset = VALVE_PRESETS.get(valve_type, {})
    seat_ratio = preset.get("seat_diam_ratio", 0.95)
    d_seat_mm = d_mm * seat_ratio
    d_seat_m  = d_seat_mm * 1.0e-3
    d_trim_m  = d_seat_m

    # Stem diameter estimate: approximately 10-15% of bore for globe valves
    d_stem_mm = max(d_mm * 0.12, 8.0)  # minimum 8 mm

    # ── Rotary vs linear decision ─────────────────────────────────────────────
    is_rotary = any(kw in valve_type for kw in ["Ball", "Butterfly", "Rotary", "Eccentric"])

    if is_rotary:
        result = _size_rotary_actuator(
            result, valve_type, d_trim_m, dP_shutoff_Pa,
            actuator_type, supply_pressure_bar,
        )
    else:
        result = _size_linear_actuator(
            result, d_seat_mm, d_seat_m, d_stem_mm, dP_shutoff_Pa,
            actuator_type, supply_pressure_bar, packing_type, leakage_class,
        )

    # ── General notes ─────────────────────────────────────────────────────────
    result.notes = _build_notes(
        valve_type=valve_type,
        actuator_type=actuator_type,
        fail_position=fail_position,
        supply_pressure_bar=supply_pressure_bar,
        packing_type=packing_type,
        leakage_class=leakage_class,
        P1_bara=P1_bara,
    )

    return result


def _size_linear_actuator(
    result: ActuatorResult,
    d_seat_mm: float,
    d_seat_m: float,
    d_stem_mm: float,
    dP_shutoff_Pa: float,
    actuator_type: ActuatorType,
    supply_pressure_bar: float,
    packing_type: str,
    leakage_class: str,
) -> ActuatorResult:
    """Size a linear (globe / angle) valve actuator."""

    # ── Unbalanced stem force ────────────────────────────────────────────────
    seat_area_m2 = math.pi / 4.0 * d_seat_m ** 2
    F_unbal = seat_area_m2 * dP_shutoff_Pa          # [N]
    result.unbalanced_force_N = round(F_unbal, 1)

    # ── Packing friction ─────────────────────────────────────────────────────
    pack_data = PACKING_FRICTION.get(packing_type, PACKING_FRICTION["PTFE"])
    F_pack = pack_data["base_N_per_mm"] * d_stem_mm  # [N]
    result.packing_friction_N = round(F_pack, 1)

    # ── Seat load (for leakage class shutoff) ────────────────────────────────
    seat_circumference_mm = math.pi * d_seat_mm
    seat_load_factor = SEAT_LOAD_N_PER_MM.get(leakage_class, 40.0)
    F_seat = seat_load_factor * seat_circumference_mm   # [N]
    result.seat_load_N = round(F_seat, 1)

    # ── Total required thrust ─────────────────────────────────────────────────
    F_req = F_unbal + F_pack + F_seat
    F_req_cont = F_req * THRUST_CONTINGENCY
    result.required_thrust_N = round(F_req, 1)
    result.required_thrust_N_with_contingency = round(F_req_cont, 1)

    # ── Actuator sizing ───────────────────────────────────────────────────────
    if actuator_type == ActuatorType.PNEUMATIC_DIAPHRAGM:
        supply_Pa = supply_pressure_bar * 1.0e5
        eff = PNEUMATIC_DIAPHRAGM_EFF
        diaphragm_area_m2 = F_req_cont / (supply_Pa * eff)
        diaphragm_area_cm2 = diaphragm_area_m2 * 1.0e4
        result.diaphragm_area_cm2 = round(diaphragm_area_cm2, 1)

        # Spring range (typical 0.2 – 1.0 bar = 3–15 psi)
        # For fail-closed: spring extends on air loss
        if result.fail_position == FailPosition.FAIL_CLOSED:
            result.spring_range_bar = "0.3 – 1.0"
            result.bench_set_bar    = "0.3 / 1.0 (3 / 15 psig)"
        else:
            result.spring_range_bar = "0.2 – 0.6"
            result.bench_set_bar    = "0.2 / 0.6 (3 / 9 psig)"

    elif actuator_type == ActuatorType.PNEUMATIC_PISTON:
        supply_Pa = supply_pressure_bar * 1.0e5
        eff = PNEUMATIC_PISTON_EFF
        piston_area_m2 = F_req_cont / (supply_Pa * eff)
        piston_area_cm2 = piston_area_m2 * 1.0e4
        result.diaphragm_area_cm2 = round(piston_area_cm2, 1)

    elif actuator_type == ActuatorType.ELECTRIC:
        # Electric actuator: thrust rating in N, motor power estimate
        # Motor power ≈ F × stroke_speed / η_mech
        # Assume 25 mm/s stem speed, 0.65 motor efficiency
        stroke_speed_ms = 0.025
        motor_efficiency = 0.65
        required_power_W = (F_req_cont * stroke_speed_ms) / motor_efficiency
        result.required_power_W = round(required_power_W, 0)
        # Round up to nearest standard motor size
        result.recommended_motor_kW = _next_standard_motor_kW(required_power_W / 1000.0)

    return result


def _size_rotary_actuator(
    result: ActuatorResult,
    valve_type: str,
    d_trim_m: float,
    dP_shutoff_Pa: float,
    actuator_type: ActuatorType,
    supply_pressure_bar: float,
) -> ActuatorResult:
    """Size a rotary (ball / butterfly / eccentric) valve actuator."""

    C_T = ROTARY_TORQUE_COEFF.get(valve_type, 0.060)

    T_break = C_T * (d_trim_m ** 3) * dP_shutoff_Pa  # [N·m]
    T_run   = 0.5 * T_break
    T_end   = 0.75 * T_break
    T_req   = T_break * THRUST_CONTINGENCY

    result.break_torque_Nm    = round(T_break, 2)
    result.run_torque_Nm      = round(T_run, 2)
    result.end_torque_Nm      = round(T_end, 2)
    result.required_torque_Nm = round(T_req, 2)

    if actuator_type == ActuatorType.ELECTRIC:
        # Electric quarter-turn: power ≈ T × ω / η
        # Assume 90°/s angular speed, 0.70 efficiency
        omega_rad_s = math.radians(90.0)  # rad/s
        motor_efficiency = 0.70
        required_power_W = (T_req * omega_rad_s) / motor_efficiency
        result.required_power_W = round(required_power_W, 0)
        result.recommended_motor_kW = _next_standard_motor_kW(required_power_W / 1000.0)
    else:
        # Pneumatic: cylinder area from rack-and-pinion or scotch-yoke geometry
        supply_Pa = supply_pressure_bar * 1.0e5
        # Approximate scotch-yoke moment arm ≈ d_trim / 2
        moment_arm_m = d_trim_m / 2.0
        if moment_arm_m > 0:
            F_cyl = T_req / moment_arm_m
            A_cyl_m2 = F_cyl / (supply_Pa * PNEUMATIC_PISTON_EFF)
            result.diaphragm_area_cm2 = round(A_cyl_m2 * 1.0e4, 1)

    return result


def _next_standard_motor_kW(required_kW: float) -> float:
    """Return the next standard IEC motor rating above required_kW [kW]."""
    standard_kW = [0.09, 0.12, 0.18, 0.25, 0.37, 0.55, 0.75, 1.1, 1.5,
                   2.2, 3.0, 4.0, 5.5, 7.5, 11.0, 15.0, 18.5, 22.0,
                   30.0, 37.0, 45.0, 55.0, 75.0, 90.0, 110.0, 132.0]
    for kW in standard_kW:
        if kW >= required_kW:
            return kW
    return required_kW * 1.25  # larger than table


def _build_notes(
    valve_type: str,
    actuator_type: ActuatorType,
    fail_position: FailPosition,
    supply_pressure_bar: float,
    packing_type: str,
    leakage_class: str,
    P1_bara: float,
) -> list[str]:
    """Generate engineering guidance notes."""
    notes: list[str] = []

    notes.append(
        f"Fail position: {fail_position.value}. "
        "Verify with process safety review (SIL/HAZOP)."
    )

    if supply_pressure_bar < 3.0:
        notes.append(
            f"⚠ Low supply pressure ({supply_pressure_bar:.1f} bar g): "
            "available thrust may be insufficient. Consider higher pressure supply "
            "or piston actuator."
        )

    if supply_pressure_bar > 7.0:
        notes.append(
            f"ℹ High supply pressure ({supply_pressure_bar:.1f} bar g): "
            "ensure actuator body and diaphragm are rated for this pressure."
        )

    if packing_type == "Graphite" and "Steam" in valve_type:
        notes.append(
            "ℹ Graphite packing selected — suitable for high-temperature steam service. "
            "Verify packing consolidation after first thermal cycle."
        )

    if P1_bara > 100.0:
        notes.append(
            f"⚠ High inlet pressure ({P1_bara:.1f} bar a): "
            "unbalanced force is significant. Consider pressure-balanced trim "
            "or double-acting piston actuator to reduce required thrust."
        )

    if actuator_type == ActuatorType.ELECTRIC:
        notes.append(
            "ℹ Electric actuator: confirm thrust/torque duty cycle with manufacturer. "
            "Consider battery backup or manual override for fail-safe operation."
        )

    notes.append(
        f"Leakage class {leakage_class} assumed for seat load calculation "
        "(IEC 60534-4:2006)."
    )

    return notes
