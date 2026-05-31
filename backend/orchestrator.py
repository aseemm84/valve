"""
backend/orchestrator.py
========================
Master sizing coordinator — public API for the frontend.

The single public function is:

    run_sizing(inputs: SizingInputs) -> SizingResult

It calls every backend module in the correct dependency order and
assembles a fully-populated SizingResult.

Architecture rules
------------------
- Zero Streamlit imports anywhere in this file.
- Zero direct I/O — all data passes through SizingInputs/SizingResult.
- All sub-module calls are wrapped in try/except so a bug in one module
  (e.g. noise) does not crash the primary Cv calculation.

Calling order
-------------
1. Validate inputs (backend.validator)
2. Compute fluid properties (backend.fluid_properties)
3. Compute piping correction factors Fp, FLP, xTP (backend.piping_geometry)
4. Route to phase-specific sizing module:
   a. Liquid  → backend.sizing_liquid  + cavitation + viscous correction
   b. Gas     → backend.sizing_gas
   c. Steam   → backend.sizing_steam
5. Compute noise (backend.noise_aerodynamic / noise_hydrodynamic)
6. Apply sizing margin
7. Collect all warnings
8. Return SizingResult
"""

from __future__ import annotations

import math
import traceback
from typing import Optional

from backend.constants import (
    BAR_TO_PSI,
    KV_PER_CV,
    N1_SI, N2_SI, N4_SI, N5_SI, N6_SI, N7_SI, N8_SI, N9_SI,
    P_ATM_BAR,
    RHO_WATER,
)
from backend.models import (
    CavitationRegime,
    CavitationResult,
    FlowBasis,
    FluidPhase,
    NoiseResult,
    PipingResult,
    SizingInputs,
    SizingResult,
    UnitSystem,
)


# =============================================================================
# PUBLIC API
# =============================================================================

def run_sizing(inputs: SizingInputs) -> SizingResult:
    """
    Run the complete valve sizing calculation.

    Parameters
    ----------
    inputs : SizingInputs
        Fully validated sizing input model from frontend.ui_inputs.build_sizing_inputs().

    Returns
    -------
    SizingResult
        Fully populated result model. If `result.success` is False, the
        `error_message` field explains the failure.
    """
    result = SizingResult(
        unit_system=inputs.unit_system,
        fluid_phase=inputs.fluid_phase,
        tag_number=inputs.tag_number,
        case_name=inputs.case_name,
        noise_limit_dba=inputs.noise_limit_dba if hasattr(inputs, 'noise_limit_dba') else 85.0,
    )

    try:
        # ── 1. Hard validation ───────────────────────────────────────────────
        violations = _validate(inputs)
        if violations:
            result.hard_violations = violations
            result.error_message = "Input validation failed: " + "; ".join(violations)
            result.success = False
            return result

        # ── 2. Fluid properties ──────────────────────────────────────────────
        rho1, mu_cP = _get_fluid_properties(inputs)
        result.rho1_kgm3 = rho1
        result.mu_cP = mu_cP
        result.P1_bar = inputs.P1_bara
        result.P2_bar = inputs.P2_bara
        result.T1_K = inputs.T1_K

        # ── 3. Piping corrections ────────────────────────────────────────────
        piping = _compute_piping(inputs)
        result.piping = piping
        result.Fp = piping.Fp
        result.FLP = piping.FLP
        result.xTP = piping.xTP

        # ── 4. Flow rate in SI mass (kg/s) and volumetric (m³/h) ─────────────
        Q_m3h, W_kgh = _normalise_flow(inputs, rho1)

        # ── 5. Phase-specific Cv calculation ─────────────────────────────────
        if inputs.fluid_phase == FluidPhase.LIQUID:
            result = _size_liquid(inputs, result, rho1, mu_cP, Q_m3h, W_kgh, piping)
        elif inputs.fluid_phase == FluidPhase.GAS:
            result = _size_gas(inputs, result, rho1, Q_m3h, W_kgh, piping)
        elif inputs.fluid_phase == FluidPhase.STEAM:
            result = _size_steam(inputs, result, rho1, mu_cP, Q_m3h, W_kgh, piping)

        # ── 6. Sizing margin and Kv ──────────────────────────────────────────
        if result.Cv_required is not None:
            result.Cv_margin = result.Cv_required * (1.0 + inputs.sizing_margin_pct / 100.0)
            result.Kv_required = result.Cv_required * KV_PER_CV

        # ── 7. Sizing ratio and opening % ────────────────────────────────────
        if result.Cv_required and inputs.Cv_rated:
            result.sizing_ratio = result.Cv_required / inputs.Cv_rated
            result.opening_pct = _estimate_opening(
                result.Cv_required, inputs.Cv_rated, inputs.char
            )

        # ── 8. Noise ─────────────────────────────────────────────────────────
        try:
            result.noise = _compute_noise(inputs, result, rho1, W_kgh)
        except Exception:
            pass  # Noise failure does not fail main result

        # ── 9. Velocity checks ────────────────────────────────────────────────
        try:
            result.v_inlet_ms, result.v_outlet_ms = _compute_velocities(
                inputs, rho1, Q_m3h, W_kgh
            )
        except Exception:
            pass

        # ── 10. Soft warnings ─────────────────────────────────────────────────
        result.warnings = _build_warnings(inputs, result)

        result.success = True

    except Exception as exc:
        result.success = False
        result.error_message = f"{type(exc).__name__}: {exc}"
        result.hard_violations = [str(exc)]

    return result


# =============================================================================
# VALIDATION
# =============================================================================

def _validate(inputs: SizingInputs) -> list[str]:
    """Return a list of hard constraint violation strings (empty = OK)."""
    violations: list[str] = []

    if inputs.P2_bara >= inputs.P1_bara:
        violations.append(
            f"P2 ({inputs.P2_bara:.4f} bar a) must be less than P1 ({inputs.P1_bara:.4f} bar a). "
            "Check gauge pressure entries."
        )

    if inputs.d_mm > inputs.D1_mm + 0.5:
        violations.append(
            f"Valve bore d ({inputs.d_mm:.1f} mm) exceeds upstream pipe ID D1 ({inputs.D1_mm:.1f} mm)."
        )

    if inputs.T1_K < 1.0:
        violations.append(f"Inlet temperature {inputs.T1_K:.1f} K is below absolute zero.")

    if inputs.fluid_phase == FluidPhase.STEAM:
        try:
            from iapws import IAPWS97
            steam = IAPWS97(P=inputs.P1_bara * 0.1, T=inputs.T1_K)
            if steam.phase not in ("Vapor", "Supercritical"):
                pass  # Allow; will handle in sizing
        except ImportError:
            violations.append(
                "Steam sizing requires the 'iapws' library. "
                "Install with: pip install iapws==1.5.2"
            )
        except Exception:
            pass

    if inputs.flow_value <= 0:
        violations.append("Flow rate must be positive.")

    if inputs.FL <= 0 or inputs.FL > 1.0:
        violations.append(f"FL ({inputs.FL}) must be in range (0, 1].")

    return violations


# =============================================================================
# FLUID PROPERTIES
# =============================================================================

def _get_fluid_properties(inputs: SizingInputs) -> tuple[float, float]:
    """
    Return (rho1_kgm3, mu_cP) at inlet conditions.
    For steam, uses IAPWS-IF97.
    """
    if inputs.fluid_phase == FluidPhase.STEAM:
        try:
            from iapws import IAPWS97
            steam = IAPWS97(P=inputs.P1_bara * 0.1, T=inputs.T1_K)
            rho = 1.0 / steam.v if steam.v > 0 else 1.0
            mu = (steam.mu * 1000) if steam.mu else 0.025  # Pa·s → cP
            return rho, mu
        except Exception:
            # Fallback to ideal gas approximation
            rho = (inputs.P1_bara * 1e5 * 18.015) / (8314.46 * inputs.T1_K)
            return rho, 0.025

    elif inputs.fluid_phase == FluidPhase.GAS:
        # Ideal gas with Z correction
        if inputs.rho1_kgm3:
            return inputs.rho1_kgm3, inputs.viscosity_cP
        rho = (inputs.P1_bara * 1e5 * inputs.molecular_weight) / (
            8314.46 * inputs.T1_K * inputs.compressibility_Z
        )
        return rho, inputs.viscosity_cP

    else:  # Liquid
        rho = inputs.Gf * RHO_WATER
        return rho, inputs.viscosity_cP


# =============================================================================
# PIPING CORRECTIONS
# =============================================================================

def _compute_piping(inputs: SizingInputs) -> PipingResult:
    """
    Compute Fp, FLP, xTP per IEC 60534-2-1:2011 §6.

    Iterative solver: Fp depends on Cv which is unknown; initial estimate
    from N2 formula, then iterate (typically converges in 2–3 steps).
    """
    d = inputs.d_mm * 1e-3   # m
    D1 = inputs.D1_mm * 1e-3
    D2 = inputs.D2_mm * 1e-3

    # Reducer/expander fitting loss coefficients (Ki)
    # Inlet reducer
    if D1 > d * 1.001:
        K1 = 0.5 * (1.0 - (d / D1) ** 2) ** 2
    else:
        K1 = 0.0

    # Outlet expander
    if D2 > d * 1.001:
        K2 = (1.0 - (d / D2) ** 2) ** 2
    else:
        K2 = 0.0

    sum_K = K1 + K2
    has_reducers = sum_K > 0.001

    if not has_reducers:
        return PipingResult(Fp=1.0, FLP=inputs.FL, xTP=inputs.xT,
                            sum_K=0.0, has_reducers=False, iterations=0)

    # Fp from IEC 60534-2-1 Eq. (18)
    # Fp = 1 / sqrt(1 + sum_K/N2 × (Cv/d²)²)
    # Iterate: start with Cv_est from no-piping case
    # Use the formula directly with N2_SI for valve Cv estimate
    # Since Cv is unknown at this stage, use a conservative estimate
    # Fp_final from the standard requires Cv — we use a 2-pass iteration
    # Pass 1: Fp = 1 (no correction)
    # Pass 2: refine

    N2 = N2_SI  # 0.00214 for d in mm

    # Estimate Cv from the basic liquid equation (rough)
    # Cv_est ≈ Q / (N1 × Fp × sqrt(ΔP/Gf)) ... use Fp=1
    # We don't need a very accurate Cv here — Fp is weakly sensitive to it
    d_mm = inputs.d_mm
    Cv_est = N2 * d_mm ** 2  # ≈ capacity at Fp=1 (order-of-magnitude)
    Cv_est = max(Cv_est, 1.0)

    Fp = 1.0
    for iteration in range(5):
        term = (sum_K / N2_SI) * (Cv_est / d_mm ** 2) ** 2
        Fp_new = 1.0 / math.sqrt(1.0 + term)
        Fp_new = min(Fp_new, 1.0)
        if abs(Fp_new - Fp) < 1e-5:
            Fp = Fp_new
            break
        Fp = Fp_new

    # FLP (combined FL·Fp for liquid choked flow)
    FL = inputs.FL
    Kc = K1  # inlet fitting coefficient only
    FL_sq = FL ** 2
    FLP_sq = FL_sq / (1.0 + (FL_sq * Kc / N2_SI) * (Cv_est / d_mm ** 2) ** 2)
    FLP = math.sqrt(max(FLP_sq, 0.01))

    # xTP (pressure ratio with piping, gas)
    xT = inputs.xT
    xTP = xT / (Fp ** 2 * (1.0 + xT * Kc / N5_SI * (Cv_est / d_mm ** 2) ** 2))
    xTP = min(xTP, xT)  # piping can only reduce xT

    return PipingResult(
        Fp=round(Fp, 5),
        FLP=round(FLP, 5),
        xTP=round(xTP, 5),
        sum_K=round(sum_K, 4),
        has_reducers=has_reducers,
        iterations=5,
    )


# =============================================================================
# FLOW NORMALISATION
# =============================================================================

def _normalise_flow(inputs: SizingInputs, rho1: float) -> tuple[float, float]:
    """
    Convert flow_value to volumetric Q [m³/h] and mass W [kg/h].
    """
    basis = inputs.flow_basis
    q = inputs.flow_value

    if basis == FlowBasis.VOLUMETRIC:
        Q_m3h = q
        W_kgh = Q_m3h * rho1
    elif basis == FlowBasis.MASS:
        W_kgh = q
        Q_m3h = W_kgh / rho1 if rho1 > 0 else q
    elif basis == FlowBasis.STANDARD:
        # Standard volumetric (Nm³/h at 0°C, 1 atm) → actual m³/h
        rho_std = (inputs.P1_bara * 1e5 * inputs.molecular_weight) / (
            8314.46 * 273.15 * inputs.compressibility_Z
        )
        W_kgh = q * rho_std
        Q_m3h = W_kgh / rho1 if rho1 > 0 else q
    else:
        Q_m3h = q
        W_kgh = Q_m3h * rho1

    return Q_m3h, W_kgh


# =============================================================================
# LIQUID SIZING
# =============================================================================

def _size_liquid(
    inputs: SizingInputs,
    result: SizingResult,
    rho1: float,
    mu_cP: float,
    Q_m3h: float,
    W_kgh: float,
    piping: PipingResult,
) -> SizingResult:
    """IEC 60534-2-1:2011 §5 — Liquid sizing."""
    P1 = inputs.P1_bara
    P2 = inputs.P2_bara
    Pv = inputs.Pv_bara
    Pc = inputs.Pc_bara
    Gf = inputs.Gf
    FL = inputs.FL
    Fp = piping.Fp
    FLP = piping.FLP
    d_mm = inputs.d_mm

    # ── Critical pressure ratio factor FF ────────────────────────────────────
    FF = 0.96 - 0.28 * math.sqrt(Pv / Pc)
    FF = min(FF, 0.96)

    # ── Choked flow check ────────────────────────────────────────────────────
    delta_P_max = (FLP / Fp) ** 2 * (P1 - FF * Pv)
    delta_P = P1 - P2
    delta_P_eff = min(delta_P, delta_P_max)
    is_choked = delta_P >= delta_P_max

    result.delta_P_max_bar = delta_P_max
    result.is_choked = is_choked
    result.flow_regime = "Choked" if is_choked else "Turbulent"

    # ── Vena contracta pressure ──────────────────────────────────────────────
    P_vc = P1 - delta_P_eff / FL ** 2
    is_flashing = P_vc < Pv

    # ── Viscous correction ────────────────────────────────────────────────────
    FR, Rev = _viscous_correction(Q_m3h, d_mm, mu_cP, Gf, FL, inputs.Fd)
    result.Rev = Rev
    result.FR = FR
    result.is_viscous_corrected = FR < 0.99

    if FR < 0.99:
        result.flow_regime = "Viscous/Laminar" if Rev < 10000 else "Turbulent (viscous)"

    # ── Cv calculation ────────────────────────────────────────────────────────
    # IEC 60534-2-1 Eq. (1): Q = N1 × Fp × Cv × sqrt(ΔP_eff / Gf)
    # → Cv = Q / (N1 × Fp × FR × sqrt(ΔP_eff / Gf))
    sqrt_term = math.sqrt(max(delta_P_eff / Gf, 1e-9))
    Cv = Q_m3h / (N1_SI * Fp * FR * sqrt_term)

    result.Cv_required = round(Cv, 4)

    # ── Cavitation result ─────────────────────────────────────────────────────
    sigma = (P1 - Pv) / max(delta_P, 1e-9)
    sigma_incipient = 1.0 / (FL ** 2)
    sigma_choked = 1.0 / FL ** 2  # simplified; real value depends on Fd

    if is_flashing:
        regime = CavitationRegime.FLASHING
        severity = "Flashing — two-phase flow. Hardened trim and angle body required."
    elif is_choked:
        regime = CavitationRegime.CHOKED
        severity = "Choked cavitation — severe bubble collapse. Anti-cavitation trim required."
    elif sigma < sigma_incipient * 0.5:
        regime = CavitationRegime.CONSTANT
        severity = "Constant cavitation — significant bubble collapse. Anti-cavitation trim recommended."
    elif sigma < sigma_incipient:
        regime = CavitationRegime.INCIPIENT
        severity = "Incipient cavitation — minor bubble formation. Monitor service life."
    else:
        regime = CavitationRegime.NONE
        severity = "No cavitation predicted."

    delta_P_incipient = (P1 - Pv) * (1.0 - 1.0 / sigma_incipient)

    result.cavitation = CavitationResult(
        regime=regime,
        sigma=round(sigma, 4),
        sigma_incipient=round(sigma_incipient, 4),
        sigma_choked=round(sigma_choked, 4),
        delta_P_max=round(delta_P_max, 4),
        delta_P_incipient=round(max(delta_P_incipient, 0), 4),
        P_vc=round(P_vc, 4),
        FL=FL,
        FF=round(FF, 4),
        is_flashing=is_flashing,
        is_choked=is_choked,
        severity_label=severity,
        recommendation=_cav_recommendation(regime),
    )

    return result


def _viscous_correction(
    Q_m3h: float, d_mm: float, mu_cP: float, Gf: float, FL: float, Fd: float
) -> tuple[float, float]:
    """Compute viscosity correction factor FR and valve Reynolds number Rev."""
    # Valve Reynolds number (IEC 60534-2-1 Eq. 29)
    # Rev = N4 × Fd × Q / (nu × sqrt(FL × Cv))
    # Iterative: Cv not yet known — use approximate Cv
    nu_cSt = mu_cP / Gf   # kinematic viscosity [cSt]

    # Rough Cv estimate (turbulent, Fp=1)
    # Use d_mm as proxy: Cv_rough ≈ N2 × d_mm²
    Cv_rough = N2_SI * d_mm ** 2
    Cv_rough = max(Cv_rough, 0.01)

    if nu_cSt < 0.01:
        return 1.0, 1e9  # essentially inviscid

    Rev = (N4_SI * Fd * Q_m3h) / (nu_cSt * math.sqrt(FL * Cv_rough))

    # FR from IEC 60534-2-1 Annex D (simplified polynomial)
    if Rev >= 40000:
        FR = 1.0
    elif Rev >= 10000:
        FR = 0.026 * math.log(Rev) + 0.65
    elif Rev >= 100:
        FR = 1.0 - 0.33 * math.log10(40000 / max(Rev, 1))
        FR = max(FR, 0.1)
    else:
        # Laminar: FR from IEC full expression (simplified)
        FR = 0.019 * Rev ** 0.667
        FR = max(FR, 0.05)

    FR = min(FR, 1.0)
    return FR, Rev


def _cav_recommendation(regime: CavitationRegime) -> str:
    recs = {
        CavitationRegime.NONE:      "No cavitation action required.",
        CavitationRegime.INCIPIENT: "Monitor trim wear. Check re-assess at off-design conditions.",
        CavitationRegime.CONSTANT:  "Specify anti-cavitation trim. Consider back-pressure control.",
        CavitationRegime.CHOKED:    "Anti-cavitation trim mandatory. Consider multi-stage let-down.",
        CavitationRegime.FLASHING:  "Angle body + hard-faced trim. Two-phase flow downstream — review pipe.",
    }
    return recs.get(regime, "")


# =============================================================================
# GAS SIZING
# =============================================================================

def _size_gas(
    inputs: SizingInputs,
    result: SizingResult,
    rho1: float,
    Q_m3h: float,
    W_kgh: float,
    piping: PipingResult,
) -> SizingResult:
    """IEC 60534-2-1:2011 §5 — Gas/vapour sizing."""
    P1 = inputs.P1_bara
    P2 = inputs.P2_bara
    gamma = inputs.gamma
    Z = inputs.compressibility_Z
    M = inputs.molecular_weight
    T1 = inputs.T1_K
    Fp = piping.Fp
    xTP = piping.xTP

    # ── Fk — specific heat ratio factor ──────────────────────────────────────
    Fk = gamma / 1.4
    result.Fk = round(Fk, 4)

    # ── Pressure drop ratio x ─────────────────────────────────────────────────
    x = (P1 - P2) / P1
    x_choked = Fk * xTP
    x_eff = min(x, x_choked)
    is_choked = x >= x_choked

    result.x_pressure_ratio = round(x, 5)
    result.is_choked = is_choked
    result.flow_regime = "Choked (Gas)" if is_choked else "Subcritical (Gas)"
    result.delta_P_max_bar = round(Fk * xTP * P1, 4)

    # ── Gas expansion factor Y ────────────────────────────────────────────────
    Y = 1.0 - x_eff / (3.0 * Fk * xTP)
    Y = max(Y, 0.667)
    result.Y_expansion = round(Y, 5)

    # ── Cv calculation — mass flow basis (N6) ─────────────────────────────────
    # IEC 60534-2-1 Eq. (9):
    # W = N6 × Fp × Cv × Y × sqrt(x_eff × P1 × rho1)
    # → Cv = W / (N6 × Fp × Y × sqrt(x_eff × P1 × rho1))
    W_kgs = W_kgh / 3600.0  # kg/s
    W_kgh_val = W_kgh
    sqrt_gas = math.sqrt(max(x_eff * P1 * rho1, 1e-12))
    Cv = W_kgh_val / (N6_SI * Fp * Y * sqrt_gas)

    result.Cv_required = round(Cv, 4)

    # ── Outlet Mach estimate ──────────────────────────────────────────────────
    if rho1 > 0 and Cv > 0:
        c_outlet = math.sqrt(gamma * P2 * 1e5 / max(rho1 * (P2 / P1) ** (1.0 / gamma), 1e-3))
        v_outlet = W_kgs / (rho1 * (P2 / P1) ** (1.0 / gamma) * math.pi / 4 * (inputs.D2_mm * 1e-3) ** 2) if inputs.D2_mm > 0 else 0.0
        result.Mach_outlet = round(abs(v_outlet / c_outlet), 4) if c_outlet > 0 else None

    return result


# =============================================================================
# STEAM SIZING
# =============================================================================

def _size_steam(
    inputs: SizingInputs,
    result: SizingResult,
    rho1: float,
    mu_cP: float,
    Q_m3h: float,
    W_kgh: float,
    piping: PipingResult,
) -> SizingResult:
    """Steam sizing — uses gas equations with IAPWS-IF97 properties."""
    # Get steam-specific gamma from IAPWS if available
    gamma = 1.33  # default
    try:
        from iapws import IAPWS97
        steam = IAPWS97(P=inputs.P1_bara * 0.1, T=inputs.T1_K)
        if hasattr(steam, 'cp') and hasattr(steam, 'cv') and steam.cv and steam.cv > 0:
            gamma = steam.cp / steam.cv
    except Exception:
        pass

    inputs_steam = inputs.model_copy(update={"gamma": gamma, "rho1_kgm3": rho1})
    result = _size_gas(inputs_steam, result, rho1, Q_m3h, W_kgh, piping)
    result.fluid_phase = FluidPhase.STEAM
    return result


# =============================================================================
# NOISE
# =============================================================================

def _compute_noise(
    inputs: SizingInputs,
    result: SizingResult,
    rho1: float,
    W_kgh: float,
) -> NoiseResult:
    """Route to aerodynamic or hydrodynamic noise module."""
    noise_limit = getattr(inputs, 'noise_limit_dba', 85.0)

    if inputs.fluid_phase in (FluidPhase.GAS, FluidPhase.STEAM):
        from backend.noise_aerodynamic import calculate_aerodynamic_noise
        W_kgs = W_kgh / 3600.0
        return calculate_aerodynamic_noise(
            mass_flow_kgs=W_kgs,
            P1_bara=inputs.P1_bara,
            P2_bara=inputs.P2_bara,
            T1_K=inputs.T1_K,
            rho1_kgm3=rho1,
            gamma=inputs.gamma,
            Cv=result.Cv_required or 1.0,
            FL=inputs.FL,
            Fd=inputs.Fd,
            d_mm=inputs.d_mm,
            D2_mm=inputs.D2_mm,
            pipe_schedule=inputs.pipe_schedule,
            noise_limit_dba=noise_limit,
        )

    elif inputs.fluid_phase == FluidPhase.LIQUID:
        return _hydrodynamic_noise(inputs, result, rho1, W_kgh, noise_limit)

    return NoiseResult(noise_limit_dba=noise_limit)


def _hydrodynamic_noise(
    inputs: SizingInputs,
    result: SizingResult,
    rho1: float,
    W_kgh: float,
    noise_limit: float,
) -> NoiseResult:
    """Simplified IEC 60534-8-4 hydrodynamic noise estimate."""
    import math as _math
    n = NoiseResult(noise_limit_dba=noise_limit)
    cav = result.cavitation
    if cav is None:
        return n

    P1 = inputs.P1_bara * 1e5
    P2 = inputs.P2_bara * 1e5
    W_kgs = W_kgh / 3600.0

    # Simplified approach: noise from pressure drop energy
    # Wm ≈ W × (P1 - P2) / rho
    Wm = W_kgs * (P1 - P2) / rho1 if rho1 > 0 else 0
    eta_liquid = 1e-6  # typical hydrodynamic efficiency
    if cav.regime in (CavitationRegime.CONSTANT, CavitationRegime.CHOKED):
        eta_liquid *= 10.0
    elif cav.regime == CavitationRegime.FLASHING:
        eta_liquid *= 30.0

    Wa = eta_liquid * Wm
    if Wa > 0:
        Lpi = 10 * _math.log10(Wa / 1e-12)
        TL = 30.0  # simplified
        Lpe = Lpi - TL
        n.Lpe_liquid_dba = round(Lpe, 1)
        n.overall_Lpe_dba = round(Lpe, 1)
        n.exceeds_limit = Lpe > noise_limit
    n.noise_regime = cav.regime.value
    return n


# =============================================================================
# VELOCITY
# =============================================================================

def _compute_velocities(
    inputs: SizingInputs,
    rho1: float,
    Q_m3h: float,
    W_kgh: float,
) -> tuple[float | None, float | None]:
    """Estimate inlet and outlet pipe velocities [m/s]."""
    A1 = math.pi / 4 * (inputs.D1_mm * 1e-3) ** 2
    A2 = math.pi / 4 * (inputs.D2_mm * 1e-3) ** 2

    if A1 > 0 and rho1 > 0:
        v1 = (Q_m3h / 3600.0) / A1
    else:
        v1 = None

    if inputs.fluid_phase == FluidPhase.LIQUID:
        v2 = v1 * (inputs.D1_mm / inputs.D2_mm) ** 2 if v1 and A2 > 0 else None
    else:
        # Gas expands as pressure drops — approximate with density ratio
        rho2 = rho1 * (inputs.P2_bara / inputs.P1_bara)
        if A2 > 0 and rho2 > 0:
            W_kgs = W_kgh / 3600.0
            v2 = W_kgs / (rho2 * A2)
        else:
            v2 = None

    return (round(v1, 2) if v1 else None, round(v2, 2) if v2 else None)


# =============================================================================
# OPENING %
# =============================================================================

def _estimate_opening(
    Cv_required: float,
    Cv_rated: float,
    char,
) -> float | None:
    """Estimate valve opening from inherent characteristic (inverse lookup)."""
    from backend.models import ValveCharacteristic
    import math as _math

    if Cv_rated <= 0:
        return None
    ratio = min(Cv_required / Cv_rated, 1.0)
    if ratio <= 0:
        return 0.0

    if char == ValveCharacteristic.EQUAL_PERCENTAGE:
        R = 50.0
        # Cv(θ) = Cv_rated × R^(θ-1) → θ = 1 + log(ratio)/log(R)
        theta = 1.0 + _math.log(max(ratio, 1.0 / R)) / _math.log(R)
    elif char == ValveCharacteristic.LINEAR:
        theta = ratio
    elif char == ValveCharacteristic.QUICK_OPENING:
        theta = ratio ** 2
    else:
        theta = ratio

    return round(max(0.0, min(theta * 100.0, 100.0)), 1)


# =============================================================================
# WARNINGS
# =============================================================================

def _build_warnings(inputs: SizingInputs, result: SizingResult) -> list[str]:
    """Generate soft engineering warnings."""
    warnings: list[str] = []

    # Sizing ratio
    if result.sizing_ratio and result.sizing_ratio > 0.85:
        warnings.append(
            f"Sizing ratio {result.sizing_ratio:.3f} > 0.85: valve is operating near "
            "capacity. API RP 553 recommends ratio ≤ 0.85. Consider a larger Cv_rated."
        )

    # Opening %
    if result.opening_pct is not None:
        if result.opening_pct < 20:
            warnings.append(
                f"Valve opening {result.opening_pct:.1f}% < 20%: risk of instability, "
                "erosion, and poor control. Select a smaller-capacity trim."
            )
        elif result.opening_pct > 85:
            warnings.append(
                f"Valve opening {result.opening_pct:.1f}% > 85%: near-capacity operation. "
                "Fp and piping losses become significant."
            )

    # Noise
    if result.noise and result.noise.overall_Lpe_dba is not None:
        if result.noise.exceeds_limit:
            warnings.append(
                f"Predicted noise {result.noise.overall_Lpe_dba:.1f} dB(A) exceeds site "
                f"limit of {result.noise.limit_dba:.0f} dB(A). "
                "Anti-noise trim or acoustic measures required."
            )

    # Cavitation
    if result.cavitation:
        cav = result.cavitation
        if cav.regime == CavitationRegime.FLASHING:
            warnings.append("Flashing predicted: two-phase flow erosion risk. Angle body required.")
        elif cav.regime == CavitationRegime.CHOKED:
            warnings.append("Choked cavitation: anti-cavitation trim mandatory.")
        elif cav.regime == CavitationRegime.CONSTANT:
            warnings.append("Constant cavitation: anti-cavitation trim recommended.")

    # Velocity
    v_limit_liquid = 6.0  # m/s
    v_limit_gas    = 50.0
    v_limit = v_limit_liquid if inputs.fluid_phase == FluidPhase.LIQUID else v_limit_gas
    if result.v_outlet_ms and result.v_outlet_ms > v_limit:
        warnings.append(
            f"Outlet velocity {result.v_outlet_ms:.1f} m/s > {v_limit:.0f} m/s: "
            "check for noise, erosion, and pipe structural concerns."
        )

    # Fp
    if result.Fp < 0.95:
        warnings.append(
            f"Fp = {result.Fp:.4f} < 0.95: significant piping correction. "
            "Verify reducer geometry and confirm with manufacturer."
        )

    # Viscous
    if result.FR and result.FR < 0.85:
        warnings.append(
            f"FR = {result.FR:.4f} < 0.85: significant viscous de-rating. "
            "Verify viscosity and consider full-bore trim."
        )

    # Delta-P max
    if result.is_choked and inputs.fluid_phase == FluidPhase.LIQUID:
        warnings.append(
            "Choked liquid flow: available ΔP exceeds maximum allowable (FL² × (P1 − FF×Pv)). "
            "Actual flow may be lower than calculated if back-pressure is insufficient."
        )

    return warnings
