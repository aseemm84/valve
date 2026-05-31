"""
backend/rangeability.py
=======================
Rangeability and turndown analysis for control valves.

Definitions (ISA-75.11.01 / IEC 60534-2-4)
-------------------------------------------
Rangeability R   = Cv_max / Cv_min (at rated conditions)
Turndown         = Design flow / Minimum controllable flow
Effective rangeability R_eff = Cv_rated / Cv_min (installed conditions)

Leakage class mapping follows IEC 60534-4:2006.
"""

from __future__ import annotations

from backend.constants import LEAKAGE_CLASSES, VALVE_PRESETS
from backend.models import RangeabilityResult, ValveCharacteristic


# Minimum Cv fraction by valve type (empirical, manufacturer-typical)
CV_MIN_FRACTION: dict[str, float] = {
    "Globe Single-Seat":          0.02,   # 2 % of rated Cv
    "Globe Double-Seat":          0.03,
    "Globe Cage-Guided":          0.02,
    "Angle Valve":                0.02,
    "Ball Valve (Full Bore)":     0.05,   # 5 % — poor controllability at very low opening
    "Ball Valve (Reduced Bore)":  0.05,
    "Butterfly (High Performance)": 0.05,
    "Butterfly (Wafer)":          0.07,
    "Eccentric Rotary Plug":      0.03,
    "3-Way Globe":                0.03,
}


def calculate_rangeability(
    Cv_rated: float,
    Cv_required: float,
    valve_type: str,
    char: ValveCharacteristic,
    is_choked: bool = False,
    noise_dba: float | None = None,
) -> RangeabilityResult:
    """
    Compute effective rangeability, turndown, and recommended leakage class.

    Parameters
    ----------
    Cv_rated : float
        Manufacturer's rated Cv at full open.
    Cv_required : float
        Required Cv at design flow.
    valve_type : str
        Valve type string (must match VALVE_PRESETS keys).
    char : ValveCharacteristic
        Inherent characteristic (affects minimum stable Cv).
    is_choked : bool
        True if the design case is at choked flow conditions.
    noise_dba : float | None
        Predicted noise level [dB(A)], used for leakage class guidance.

    Returns
    -------
    RangeabilityResult
    """
    # Minimum controllable Cv fraction
    cv_min_frac = CV_MIN_FRACTION.get(valve_type, 0.03)

    # Quick-opening valves have poor rangeability
    if char == ValveCharacteristic.QUICK_OPENING:
        cv_min_frac = max(cv_min_frac, 0.08)

    Cv_min = Cv_rated * cv_min_frac
    Cv_max = Cv_rated

    effective_rangeability = Cv_max / Cv_min if Cv_min > 0 else 0.0

    # Turndown = design flow / min controllable flow
    # Flow ∝ Cv × √ΔP → if ΔP is constant: turndown = Cv_required / Cv_min
    turndown_ratio = Cv_required / Cv_min if Cv_min > 0 else 0.0

    # Minimum controllable flow as fraction of design flow
    min_flow_fraction = Cv_min / Cv_required if Cv_required > 0 else 0.0

    # Rangeability adequacy: R_eff >= turndown + 10 % margin
    rangeability_adequate = effective_rangeability >= (turndown_ratio * 1.1)

    # ── Leakage class recommendation ────────────────────────────────────────
    leakage_class, leakage_desc = _recommend_leakage_class(
        valve_type=valve_type,
        is_choked=is_choked,
        noise_dba=noise_dba,
        effective_rangeability=effective_rangeability,
    )

    # ── Recommendation text ──────────────────────────────────────────────────
    recommendation = _build_recommendation(
        effective_rangeability=effective_rangeability,
        turndown_ratio=turndown_ratio,
        rangeability_adequate=rangeability_adequate,
        valve_type=valve_type,
        char=char,
        cv_min_frac=cv_min_frac,
    )

    return RangeabilityResult(
        Cv_max=round(Cv_max, 3),
        Cv_min=round(Cv_min, 3),
        effective_rangeability=round(effective_rangeability, 1),
        turndown_ratio=round(turndown_ratio, 1),
        min_controllable_flow_fraction=round(min_flow_fraction, 3),
        recommended_leakage_class=leakage_class,
        leakage_class_description=leakage_desc,
        rangeability_adequate=rangeability_adequate,
        recommendation=recommendation,
    )


def _recommend_leakage_class(
    valve_type: str,
    is_choked: bool,
    noise_dba: float | None,
    effective_rangeability: float,
) -> tuple[str, str]:
    """
    Recommend IEC 60534-4 leakage class based on service conditions.

    Returns
    -------
    tuple[str, str]
        (class_name, description)
    """
    # Base class by valve type
    if "Globe" in valve_type or "Angle" in valve_type:
        base_class = "Class IV"
    elif "Ball" in valve_type or "Eccentric" in valve_type:
        base_class = "Class IV"
    elif "Butterfly" in valve_type:
        base_class = "Class III"
    else:
        base_class = "Class II"

    # Upgrade for tight rangeability or noise
    final_class = base_class

    if effective_rangeability > 50.0:
        # Need better shutoff for wide-range control
        final_class = "Class V"

    if noise_dba and noise_dba > 90.0:
        # Anti-noise trims typically achieve Class V
        final_class = "Class V"

    if is_choked:
        # Choked flow → hard seat damage risk → upgrade trim
        final_class = "Class IV"

    # Override to VI for tight-shutoff service
    # (not auto-detected; engineering judgement required)

    desc = LEAKAGE_CLASSES.get(final_class, {}).get("description", "")
    typical = LEAKAGE_CLASSES.get(final_class, {}).get("typical_use", "")
    full_desc = f"{desc} — {typical}"

    return final_class, full_desc


def _build_recommendation(
    effective_rangeability: float,
    turndown_ratio: float,
    rangeability_adequate: bool,
    valve_type: str,
    char: ValveCharacteristic,
    cv_min_frac: float,
) -> str:
    """Build a human-readable rangeability recommendation."""
    lines: list[str] = []

    if rangeability_adequate:
        lines.append(
            f"✓ Effective rangeability ({effective_rangeability:.1f}:1) is sufficient "
            f"for the required turndown ({turndown_ratio:.1f}:1)."
        )
    else:
        lines.append(
            f"⚠ Effective rangeability ({effective_rangeability:.1f}:1) is INSUFFICIENT "
            f"for the required turndown ({turndown_ratio:.1f}:1). "
            f"The valve cannot control flow down to the minimum process requirement."
        )
        lines.append(
            "Recommendations: (a) Select a valve with higher inherent rangeability, "
            "(b) Use characterised cage trim, "
            "(c) Consider split-range arrangement with a smaller trim, "
            "or (d) Review minimum flow process requirement."
        )

    if char == ValveCharacteristic.QUICK_OPENING:
        lines.append(
            "ℹ Quick-opening characteristic reduces rangeability. "
            "Equal-percentage or linear characteristic is preferred for wide rangeability."
        )

    if effective_rangeability > 100.0:
        lines.append(
            f"ℹ Very high rangeability ({effective_rangeability:.0f}:1) stated. "
            "Verify with the valve manufacturer — characterised cage or split-range "
            "may be needed to achieve this in practice."
        )

    lines.append(
        f"The minimum controllable Cv for a {valve_type} is approximately "
        f"{cv_min_frac*100:.1f}% of rated Cv."
    )

    return "  ".join(lines)
