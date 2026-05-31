"""
backend/valve_selection.py
===========================
Rule-based valve body style and trim type selection advisor.

The rule engine evaluates service conditions and returns a ranked
recommendation list for body style and trim type.

Decision variables used
-----------------------
- Fluid phase (liquid, gas, steam)
- ΔP ratio  x = ΔP / P1
- Cavitation regime (none … flashing)
- Noise level  Lpe [dB(A)]
- Line size (valve bore d)
- Flow coefficient Cv
- Inlet pressure P1
- Viscosity
- Is_choked flag
- Sizing ratio (Cv_req / Cv_rated)

References
----------
Driskell, L. — Control-Valve Selection and Sizing, ISA (1983)
Emerson / Fisher — Control Valve Handbook, 5th ed. (2019)
Metso — Valve Selection Guide (2020)
ANSI/ISA-S75.23-1995 — Considerations for Evaluating Control Valve Cavitation
"""

from __future__ import annotations

from backend.models import (
    CavitationRegime,
    FluidPhase,
    TrimType,
    ValveBodyStyle,
    ValveSelectionResult,
)


def select_valve_body_and_trim(
    fluid_phase: FluidPhase,
    P1_bara: float,
    P2_bara: float,
    Cv_required: float,
    d_mm: float,
    cavitation_regime: CavitationRegime,
    noise_dba: float | None,
    is_choked: bool,
    sizing_ratio: float | None,
    viscosity_cP: float = 1.0,
    is_flashing: bool = False,
    temperature_C: float = 20.0,
) -> ValveSelectionResult:
    """
    Rule-based valve body and trim selection advisor.

    Parameters
    ----------
    fluid_phase : FluidPhase
        Liquid, Gas, or Steam.
    P1_bara : float
        Inlet absolute pressure [bar a].
    P2_bara : float
        Outlet absolute pressure [bar a].
    Cv_required : float
        Required Cv at design conditions.
    d_mm : float
        Valve bore [mm].
    cavitation_regime : CavitationRegime
        Assessed cavitation regime (for liquid service).
    noise_dba : float | None
        Predicted noise level [dB(A)].
    is_choked : bool
        True if flow is choked at design conditions.
    sizing_ratio : float | None
        Cv_required / Cv_rated (None if Cv_rated not provided).
    viscosity_cP : float
        Fluid viscosity [cP].
    is_flashing : bool
        True if liquid flashing is predicted.
    temperature_C : float
        Fluid temperature [°C].

    Returns
    -------
    ValveSelectionResult
        Ranked body and trim recommendations with engineering rationale.
    """
    result = ValveSelectionResult()

    dP_bar = P1_bara - P2_bara
    x = dP_bar / P1_bara if P1_bara > 0 else 0.0   # pressure drop ratio

    # ── Body style selection ──────────────────────────────────────────────────
    body, body_alts, body_rationale = _select_body(
        fluid_phase, P1_bara, x, d_mm, Cv_required,
        cavitation_regime, noise_dba, is_choked, is_flashing,
        viscosity_cP, temperature_C,
    )

    # ── Trim type selection ───────────────────────────────────────────────────
    trim, trim_alts, trim_rationale = _select_trim(
        fluid_phase, x, P1_bara, cavitation_regime,
        noise_dba, is_choked, is_flashing, temperature_C,
    )

    # ── Material guidance ─────────────────────────────────────────────────────
    body_material, trim_material = _select_materials(
        fluid_phase, P1_bara, temperature_C, is_flashing,
        cavitation_regime,
    )

    # ── End connection ────────────────────────────────────────────────────────
    end_connection = _select_end_connection(P1_bara, d_mm, temperature_C)

    # ── Additional notes ──────────────────────────────────────────────────────
    notes = _build_notes(
        fluid_phase, P1_bara, cavitation_regime, is_flashing,
        noise_dba, viscosity_cP, temperature_C, d_mm,
    )

    result.recommended_body   = body
    result.body_alternatives  = body_alts
    result.body_rationale     = body_rationale
    result.recommended_trim   = trim
    result.trim_alternatives  = trim_alts
    result.trim_rationale     = trim_rationale
    result.body_material      = body_material
    result.trim_material      = trim_material
    result.end_connection     = end_connection
    result.notes              = notes

    return result


# ---------------------------------------------------------------------------
# Internal rule functions
# ---------------------------------------------------------------------------

def _select_body(
    phase: FluidPhase,
    P1_bara: float,
    x: float,
    d_mm: float,
    Cv_required: float,
    cav_regime: CavitationRegime,
    noise_dba: float | None,
    is_choked: bool,
    is_flashing: bool,
    viscosity_cP: float,
    temperature_C: float,
) -> tuple[ValveBodyStyle, list[ValveBodyStyle], str]:
    """Select valve body style from service conditions."""

    rationale_parts: list[str] = []
    candidates: list[tuple[int, ValveBodyStyle]] = []  # (score, style)

    noise_high = noise_dba is not None and noise_dba > 85.0
    noise_very_high = noise_dba is not None and noise_dba > 95.0

    # ── Rule R1: Flashing service → Angle body ────────────────────────────
    if is_flashing:
        candidates.append((10, ValveBodyStyle.ANGLE))
        rationale_parts.append(
            "Flashing service: angle body directs two-phase flow away from the valve "
            "body and into the downstream pipe, reducing erosion damage."
        )

    # ── Rule R2: High cavitation risk → Cage-guided globe ────────────────
    if cav_regime in (CavitationRegime.CHOKED, CavitationRegime.CONSTANT):
        candidates.append((9, ValveBodyStyle.CAGE_GLOBE))
        rationale_parts.append(
            f"Cavitation regime '{cav_regime.value}': cage-guided globe with "
            "anti-cavitation trim is required to stage pressure drop and reduce "
            "bubble collapse energy."
        )

    # ── Rule R3: High ΔP gas + high noise → Cage globe ───────────────────
    if phase == FluidPhase.GAS and x > 0.5 and noise_high:
        candidates.append((8, ValveBodyStyle.CAGE_GLOBE))
        rationale_parts.append(
            f"High ΔP ratio (x = {x:.2f}) with elevated noise: cage-guided globe "
            "with multi-stage trim is recommended for pressure staging."
        )

    # ── Rule R4: Very high ΔP (x > 0.7) any fluid → Cage globe ──────────
    if x > 0.70:
        candidates.append((8, ValveBodyStyle.CAGE_GLOBE))
        rationale_parts.append(
            f"Very high pressure-drop ratio (x = {x:.2f} > 0.70): "
            "multi-stage cage-guided globe prevents excessive velocity and erosion."
        )

    # ── Rule R5: Large bore (d > 300 mm) gas → Butterfly ─────────────────
    if d_mm > 300 and phase in (FluidPhase.GAS,) and not noise_high:
        candidates.append((7, ValveBodyStyle.BUTTERFLY_HP))
        rationale_parts.append(
            f"Large line size (d = {d_mm:.0f} mm > 300 mm) gas service: "
            "high-performance butterfly valve offers cost and weight advantages "
            "when noise is not the controlling concern."
        )

    # ── Rule R6: High Cv / low ΔP → Ball valve ────────────────────────────
    if x < 0.20 and phase == FluidPhase.LIQUID and not noise_high:
        candidates.append((6, ValveBodyStyle.BALL))
        rationale_parts.append(
            f"Low pressure-drop ratio (x = {x:.2f}) liquid service: "
            "full-bore ball valve provides high Cv with minimal pressure loss."
        )

    # ── Rule R7: High viscosity → Globe single-seat ───────────────────────
    if viscosity_cP > 50:
        candidates.append((8, ValveBodyStyle.GLOBE_SINGLE))
        rationale_parts.append(
            f"High viscosity fluid ({viscosity_cP:.0f} cP): globe valve with "
            "streamlined contoured plug minimises viscous pressure loss and "
            "allows accurate FR correction."
        )

    # ── Rule R8: Steam service → Globe single-seat ────────────────────────
    if phase == FluidPhase.STEAM:
        candidates.append((9, ValveBodyStyle.GLOBE_SINGLE))
        rationale_parts.append(
            "Steam service: globe single-seat valve with bolted bonnet and "
            "extended-top body for high-temperature insulation / steam tracing."
        )

    # ── Rule R9: General moderate conditions → Globe single-seat (default)
    candidates.append((5, ValveBodyStyle.GLOBE_SINGLE))

    # ── Rank candidates ────────────────────────────────────────────────────
    candidates.sort(key=lambda c: c[0], reverse=True)
    best = candidates[0][1]
    seen = {best}
    alts = []
    for _, style in candidates[1:]:
        if style not in seen:
            alts.append(style)
            seen.add(style)
        if len(alts) >= 2:
            break

    rationale = "  ".join(rationale_parts) or (
        "Standard globe single-seat valve recommended for moderate service conditions."
    )

    return best, alts, rationale


def _select_trim(
    phase: FluidPhase,
    x: float,
    P1_bara: float,
    cav_regime: CavitationRegime,
    noise_dba: float | None,
    is_choked: bool,
    is_flashing: bool,
    temperature_C: float,
) -> tuple[TrimType, list[TrimType], str]:
    """Select valve trim type."""

    rationale_parts: list[str] = []
    candidates: list[tuple[int, TrimType]] = []

    noise_high     = noise_dba is not None and noise_dba > 85.0
    noise_very_high = noise_dba is not None and noise_dba > 95.0

    # ── Trim T1: Flashing → Hard-facing ──────────────────────────────────
    if is_flashing:
        candidates.append((10, TrimType.HARD_FACING))
        rationale_parts.append(
            "Flashing service: Stellite-faced seat rings and plug to resist "
            "erosive vapour-bubble collapse and two-phase flow erosion."
        )

    # ── Trim T2: Severe cavitation → Anti-cavitation ─────────────────────
    if cav_regime in (CavitationRegime.CHOKED, CavitationRegime.CONSTANT):
        candidates.append((10, TrimType.ANTI_CAVITATION))
        rationale_parts.append(
            f"Cavitation regime '{cav_regime.value}': anti-cavitation trim "
            "(multi-orifice cage, tortuous path) stages the pressure drop "
            "to keep local pressure above vapour pressure at every stage."
        )

    # ── Trim T3: Very high noise gas → Anti-noise / multi-stage ──────────
    if noise_very_high and phase in (FluidPhase.GAS, FluidPhase.STEAM):
        candidates.append((9, TrimType.ANTI_NOISE))
        rationale_parts.append(
            f"Predicted noise {noise_dba:.0f} dB(A) > 95 dB(A): "
            "anti-noise trim (drilled-hole cage, whisper trim) required "
            "to shift acoustic energy to higher, more attenuated frequencies."
        )

    # ── Trim T4: High ΔP ratio → Multi-stage ─────────────────────────────
    if x > 0.60 or P1_bara > 100.0:
        candidates.append((8, TrimType.MULTISTAGE))
        rationale_parts.append(
            f"High pressure-drop ratio (x = {x:.2f}) or high inlet pressure "
            f"({P1_bara:.0f} bar a): multi-stage / tortuous-path trim prevents "
            "excessive velocity, erosion, and noise."
        )

    # ── Trim T5: High noise (moderate) → Anti-noise ───────────────────────
    if noise_high and not noise_very_high:
        candidates.append((7, TrimType.ANTI_NOISE))
        rationale_parts.append(
            f"Predicted noise {noise_dba:.0f} dB(A) > 85 dB(A): "
            "anti-noise (low-noise) trim recommended."
        )

    # ── Trim T6: Steam → Hard-facing ─────────────────────────────────────
    if phase == FluidPhase.STEAM:
        candidates.append((7, TrimType.HARD_FACING))
        rationale_parts.append(
            "Steam service: Stellite or hardened 17-4PH trim for resistance "
            "to wire-drawing and high-velocity steam erosion at the seat."
        )

    # ── Trim T7: Default → Contoured parabolic ───────────────────────────
    candidates.append((4, TrimType.CONTOURED))

    # ── Characterised cage for equal-% installed response ────────────────
    if cav_regime == CavitationRegime.NONE and not noise_high:
        candidates.append((3, TrimType.CHARACTERISED))

    # ── Rank ──────────────────────────────────────────────────────────────
    candidates.sort(key=lambda c: c[0], reverse=True)
    best = candidates[0][1]
    seen = {best}
    alts = []
    for _, trim in candidates[1:]:
        if trim not in seen:
            alts.append(trim)
            seen.add(trim)
        if len(alts) >= 2:
            break

    rationale = "  ".join(rationale_parts) or (
        "Contoured parabolic plug trim recommended for general-purpose service."
    )

    return best, alts, rationale


def _select_materials(
    phase: FluidPhase,
    P1_bara: float,
    temperature_C: float,
    is_flashing: bool,
    cav_regime: CavitationRegime,
) -> tuple[str, str]:
    """Return body and trim material guidance strings."""

    # Body material
    if temperature_C > 400 or P1_bara > 100:
        body_material = "Alloy Steel (ASTM A217 WC9 / C12A)"
    elif temperature_C < -20:
        body_material = "Low-Temperature Carbon Steel (ASTM A352 LCB) or Stainless Steel"
    elif phase == FluidPhase.STEAM and temperature_C > 300:
        body_material = "Alloy Steel (ASTM A217 WC6) — Chrome-Moly for high-temp steam"
    else:
        body_material = "Carbon Steel (ASTM A216 WCB)"

    # Trim material
    if is_flashing or cav_regime in (CavitationRegime.CHOKED, CavitationRegime.CONSTANT):
        trim_material = "Hardened 17-4PH SS / Stellite 6 seat rings"
    elif phase == FluidPhase.STEAM and temperature_C > 350:
        trim_material = "Stellite 6 or Colmonoy 6 hard-faced seats; 410 SS plug"
    elif temperature_C < -50:
        trim_material = "316L SS (NACE MR0175) with PTFE or PEEK soft seats"
    else:
        trim_material = "316 SS / Stellite-faced seats for Class IV sealing"

    return body_material, trim_material


def _select_end_connection(P1_bara: float, d_mm: float, temperature_C: float) -> str:
    """Determine recommended end connection type."""
    if P1_bara > 250:
        return "Welding End (BW) — ASME B16.25 (high pressure)"
    elif P1_bara > 100 or temperature_C > 400:
        return "ASME B16.5 RTJ Flanged (high pressure/temperature)"
    elif d_mm > 400:
        return "ASME B16.47 Series A RF Flanged (large bore)"
    else:
        return "ASME B16.5 Class 300 RF Flanged"


def _build_notes(
    phase: FluidPhase,
    P1_bara: float,
    cav_regime: CavitationRegime,
    is_flashing: bool,
    noise_dba: float | None,
    viscosity_cP: float,
    temperature_C: float,
    d_mm: float,
) -> list[str]:
    """Generate supplementary engineering notes."""
    notes: list[str] = []

    if cav_regime == CavitationRegime.FLASHING:
        notes.append(
            "🔴 Flashing service: two-phase flow downstream will cause severe erosion. "
            "Confirm material selection with a corrosion/erosion specialist. "
            "Consider downstream pipe hardening or lined pipe."
        )

    if cav_regime in (CavitationRegime.CONSTANT, CavitationRegime.CHOKED):
        notes.append(
            "🟡 Significant cavitation predicted. Anti-cavitation trim alone may not be "
            "sufficient if σ ≪ σ_choked. Review inlet pressure or consider staged let-down."
        )

    if noise_dba and noise_dba > 110.0:
        notes.append(
            "🔴 Predicted noise exceeds 110 dB(A): valve with low-noise trim alone will "
            "be insufficient. Acoustic insulation lagging on downstream pipe section "
            "and a silencer / diffuser package must be included in the specification."
        )

    if viscosity_cP > 100:
        notes.append(
            f"ℹ High viscosity ({viscosity_cP:.0f} cP): ensure full-bore flow path and "
            "minimum downstream velocity to prevent solidification in cold ambient conditions."
        )

    if phase == FluidPhase.STEAM and temperature_C > 450:
        notes.append(
            "🟡 Very high steam temperature (> 450 °C): verify ASME B31.3 / B16.34 "
            "pressure-temperature rating at this condition for the selected material."
        )

    if P1_bara > 150:
        notes.append(
            f"ℹ Very high inlet pressure ({P1_bara:.0f} bar a): pressure-balanced trim "
            "strongly recommended to reduce actuator thrust requirement."
        )

    if d_mm > 300:
        notes.append(
            f"ℹ Large bore valve (d = {d_mm:.0f} mm): consider split-body or top-and-bottom "
            "guided cage design for ease of maintenance."
        )

    notes.append(
        "⚠ This recommendation is based on general engineering rules. "
        "Final valve specification must be reviewed by a qualified instrumentation engineer "
        "and confirmed with the valve manufacturer."
    )

    return notes
