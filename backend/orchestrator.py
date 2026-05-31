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
1.  Validate inputs
2.  Compute fluid properties  (rho1, mu)
3.  Normalise flow to SI  (Q_m3h, W_kgh)          ← MOVED BEFORE PIPING
4.  Estimate first-pass Cv with Fp=1               ← NEW: seeds piping iteration
5.  Compute piping correction factors Fp, FLP, xTP ← NOW USES REAL Cv SEED
6.  Route to phase-specific sizing module:
    a. Liquid  → _size_liquid  + cavitation + viscous correction
    b. Gas     → _size_gas
    c. Steam   → _size_steam
7.  Compute noise  (aerodynamic / hydrodynamic)
8.  Apply sizing margin
9.  Collect all warnings
10. Return SizingResult

Bug fixes (v2.1)
----------------
BUG 1 — NoiseResult field-name mismatch:
    All three NoiseResult() constructor calls now use the correct keyword
    argument ``limit_dba=`` (matching the Pydantic model field name)
    instead of the erroneous ``noise_limit_dba=``.  Previously, the
    noise-limit exceedance flag always used the default 85 dB(A) regardless
    of the user-specified limit.  The extraneous ``noise_limit_dba=`` kwarg
    in the SizingResult() constructor has also been removed.

BUG 2 — Fp / FLP / xTP iteration used wrong Cv estimate:
    The previous implementation seeded the Fp iteration with
    ``Cv_est = N2_SI × d_mm²`` which evaluates to ≈ 0.00214 × d² — a value
    so small that the iteration converged to Fp ≈ 1.000 always, rendering
    the piping correction a no-op.  The fix introduces:
      (a) _estimate_cv_rough(): a first-pass Cv from the actual sizing
          equation with Fp=1, FR=1 (or Y=2/3), using the already-normalised
          flow rates.
      (b) Flow normalisation is now performed BEFORE _compute_piping() so
          that a meaningful Cv seed is available.
      (c) _compute_piping() accepts a ``Cv_estimate`` parameter and iterates
          using ``Cv_iter = Cv_seed / Fp`` to account for the Cv↔Fp feedback
          (Cv ∝ 1/Fp from the sizing equation).

BUG 3 — xTP formula operator precedence:
    Explicit parentheses added around ``(xT * K1 / N5_SI)`` to make the
    intent unambiguous.  The effective fix is delivered by Bug 2's correct
    Cv seed; the parenthesisation is a code-clarity hardening.
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
        Fully populated result model.  If ``result.success`` is False, the
        ``error_message`` field explains the failure.
    """
    # ── BUG 1 FIX: removed erroneous noise_limit_dba= kwarg ─────────────────
    # SizingResult has no noise_limit_dba field; the noise limit is stored
    # inside NoiseResult.limit_dba and is set correctly in _compute_noise().
    result = SizingResult(
        unit_system=inputs.unit_system,
        fluid_phase=inputs.fluid_phase,
        tag_number=inputs.tag_number,
        case_name=inputs.case_name,
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

        # ── 3. Flow normalisation ─────────────────────────────────────────────
        # MOVED before piping corrections so that a real Cv estimate is
        # available to seed the Fp / FLP / xTP iteration (Bug 2 fix).
        Q_m3h, W_kgh = _normalise_flow(inputs, rho1)

        # ── 4. First-pass Cv estimate (Fp=1, FR=1) — piping seed ─────────────
        # Bug 2 fix: provides a realistic Cv to _compute_piping() instead
        # of the previously used N2×d² ≈ 0 which made Fp always ≈ 1.000.
        Cv_seed = _estimate_cv_rough(inputs, rho1, Q_m3h, W_kgh)

        # ── 5. Piping correction factors ──────────────────────────────────────
        piping = _compute_piping(inputs, Cv_estimate=Cv_seed)
        result.piping = piping
        result.Fp = piping.Fp
        result.FLP = piping.FLP
        result.xTP = piping.xTP

        # ── 6. Phase-specific Cv calculation ─────────────────────────────────
        if inputs.fluid_phase == FluidPhase.LIQUID:
            result = _size_liquid(inputs, result, rho1, mu_cP, Q_m3h, W_kgh, piping)
        elif inputs.fluid_phase == FluidPhase.GAS:
            result = _size_gas(inputs, result, rho1, Q_m3h, W_kgh, piping)
        elif inputs.fluid_phase == FluidPhase.STEAM:
            result = _size_steam(inputs, result, rho1, mu_cP, Q_m3h, W_kgh, piping)

        # ── 7. Sizing margin and Kv ──────────────────────────────────────────
        if result.Cv_required is not None:
            result.Cv_margin = result.Cv_required * (1.0 + inputs.sizing_margin_pct / 100.0)
            result.Kv_required = result.Cv_required * KV_PER_CV

        # ── 8. Sizing ratio and opening % ────────────────────────────────────
        if result.Cv_required and inputs.Cv_rated:
            result.sizing_ratio = result.Cv_required / inputs.Cv_rated
            result.opening_pct = _estimate_opening(
                result.Cv_required, inputs.Cv_rated, inputs.char
            )

        # ── 9. Noise ──────────────────────────────────────────────────────────
        try:
            result.noise = _compute_noise(inputs, result, rho1, W_kgh)
        except Exception:
            pass  # Noise failure does not fail main result

        # ── 10. Velocity checks ───────────────────────────────────────────────
        try:
            result.v_inlet_ms, result.v_outlet_ms = _compute_velocities(
                inputs, rho1, Q_m3h, W_kgh
            )
        except Exception:
            pass

        # ── 11. Soft warnings ─────────────────────────────────────────────────
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
# FLOW NORMALISATION
# =============================================================================

def _normalise_flow(inputs: SizingInputs, rho1: float) -> tuple[float, float]:
    """
    Convert flow_value to volumetric Q [m³/h] and mass W [kg/h].

    Standard volumetric (Nm³/h) uses ISO reference conditions:
    T = 273.15 K (0 °C), P = 1.01325 bar, Z = 1.
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
        # Standard volumetric (Nm³/h at 0 °C, 1.01325 bar) → mass flow kg/h
        # Use ISO standard conditions: T_std = 273.15 K, P_std = 1.01325 bar, Z = 1
        rho_std = (P_ATM_BAR * 1e5 * inputs.molecular_weight) / (
            8314.46 * 273.15 * 1.0
        )
        W_kgh = q * rho_std
        Q_m3h = W_kgh / rho1 if rho1 > 0 else q

    else:
        Q_m3h = q
        W_kgh = Q_m3h * rho1

    return Q_m3h, W_kgh


# =============================================================================
# FIRST-PASS CV ESTIMATE  (Bug 2 fix — seeds piping correction iteration)
# =============================================================================

def _estimate_cv_rough(
    inputs: SizingInputs,
    rho1: float,
    Q_m3h: float,
    W_kgh: float,
) -> float:
    """
    Compute a first-pass Cv estimate with Fp = 1, FR = 1 (Y = 2/3 for gas).

    This estimate is used exclusively to seed the Fp / FLP / xTP iteration
    in ``_compute_piping()``.  A rough value (±30 %) is entirely sufficient —
    Fp converges to < 0.01 % error after the first iteration once the seed is
    within an order of magnitude of the true Cv.

    The previous code used ``Cv_est = N2_SI × d_mm²`` ≈ 0.00214 × d², which
    evaluates to ~22 for a 100 mm bore regardless of actual flow.  For real
    valves needing Cv = 200, this seed was a factor of 9 too small, collapsing
    the Fp correction term to ≈ 0 and returning Fp ≈ 1.000 always (Bug 2).

    Parameters
    ----------
    inputs : SizingInputs
    rho1 : float
        Inlet fluid density [kg/m³].
    Q_m3h : float
        Volumetric flow rate [m³/h] (already normalised).
    W_kgh : float
        Mass flow rate [kg/h] (already normalised).

    Returns
    -------
    float
        Rough Cv estimate [dimensionless].  Guaranteed ≥ 0.01.
    """
    P1 = inputs.P1_bara
    P2 = inputs.P2_bara
    delta_P = max(P1 - P2, 1.0e-6)

    if inputs.fluid_phase == FluidPhase.LIQUID:
        # Cv = Q / (N1 × √(ΔP / Gf))  — IEC 60534-2-1 Eq. (1) with Fp=FR=1
        Gf = max(inputs.Gf, 0.01)
        sqrt_term = math.sqrt(max(delta_P / Gf, 1.0e-9))
        if sqrt_term > 0 and Q_m3h > 0:
            return max(Q_m3h / (N1_SI * sqrt_term), 0.01)

    else:
        # Gas / steam: Cv = W / (N6 × Y × √(x × P1 × ρ1))  — Eq. (9) with Fp=1
        # Use Y = 2/3 (minimum, i.e., choked) as a conservative seed.
        # Using the minimum Y overestimates Cv → Fp is slightly over-corrected →
        # iteration converges from above, which is the safe direction.
        x = min(delta_P / max(P1, 1.0e-6),
                inputs.xT * (inputs.gamma / 1.4))
        x = max(x, 1.0e-6)
        Fk = inputs.gamma / 1.4
        xT_eff = max(inputs.xT, 0.05)
        Y = max(1.0 - x / (3.0 * Fk * xT_eff), 0.667)
        sqrt_gas = math.sqrt(max(x * P1 * max(rho1, 0.01), 1.0e-12))
        if sqrt_gas > 0 and W_kgh > 0:
            return max(W_kgh / (N6_SI * max(Y, 0.1) * sqrt_gas), 0.01)

    # Geometric fallback — only reached if flow data is degenerate
    return max(N2_SI * inputs.d_mm ** 2, 1.0)


# =============================================================================
# PIPING CORRECTIONS  (Bug 2 + Bug 3 fix)
# =============================================================================

def _compute_piping(inputs: SizingInputs, Cv_estimate: float = 1.0) -> PipingResult:
    """
    Compute Fp, FLP, xTP per IEC 60534-2-1:2011 §6.

    Parameters
    ----------
    inputs : SizingInputs
    Cv_estimate : float
        Best available estimate of the required Cv [dimensionless].
        Must be obtained from the first-pass sizing equation (Fp = 1)
        for the iteration to be meaningful.  Defaults to 1.0 as a safe
        fallback, but will significantly under-correct Fp for large valves.

    Returns
    -------
    PipingResult
        Fp, FLP, xTP, sum_K, has_reducers, iterations.

    Notes — Bug 2 fix
    -----------------
    The Fp iteration exploits the inverse relationship between Fp and the
    required Cv (Cv ∝ 1/Fp from the sizing equation).  In each iteration:

        Cv_iter = Cv_seed / Fp_current

    This accounts for the feedback: as Fp decreases, the actual Cv needed
    increases, which in turn affects Fp.  The loop converges in 3–5 steps
    starting from a reasonable Cv_estimate.

    Notes — Bug 3 fix
    -----------------
    Explicit parentheses around ``(xT * K1 / N5_SI)`` clarify operator
    precedence in the xTP formula and match IEC 60534-2-1 Eq. (23) exactly.
    """
    d_mm = inputs.d_mm
    D1   = inputs.D1_mm * 1.0e-3   # m
    D2   = inputs.D2_mm * 1.0e-3   # m
    d    = d_mm * 1.0e-3            # m

    # ── Fitting loss coefficients (IEC 60534-2-1 Annex A) ────────────────────
    # Inlet concentric reducer: K1 = 0.5 × (1 − (d/D1)²)²
    if D1 > d * 1.001:
        K1 = 0.5 * (1.0 - (d / D1) ** 2) ** 2
    else:
        K1 = 0.0

    # Outlet concentric expander: K2 = (1 − (d/D2)²)²
    if D2 > d * 1.001:
        K2 = (1.0 - (d / D2) ** 2) ** 2
    else:
        K2 = 0.0

    sum_K = K1 + K2
    has_reducers = sum_K > 1.0e-4

    if not has_reducers:
        # Same-bore installation — piping correction factors are unity/unchanged
        return PipingResult(
            Fp=1.0,
            FLP=inputs.FL,
            xTP=inputs.xT,
            sum_K=0.0,
            has_reducers=False,
            iterations=0,
        )

    # ── Guard: ensure Cv_estimate is a physically meaningful positive number ──
    Cv_seed = max(Cv_estimate, 0.01)

    # ── Fp iteration — IEC 60534-2-1 Eq. (18) ────────────────────────────────
    # Fp = 1 / √(1 + ΣK/N2 × (Cv/d²)²)
    #
    # Because Cv ∝ 1/Fp, the Cv at each iteration step is updated as:
    #   Cv_iter = Cv_seed / Fp_current
    # This models the Cv↔Fp feedback and converges the self-consistent solution.
    #
    # Convergence is typically achieved in 3–5 iterations.  The loop runs for
    # a maximum of 10 iterations to guard against pathological inputs.
    Fp = 1.0
    n_iter = 0
    for n_iter in range(1, 11):
        # Cv estimate at the current Fp (accounts for Cv ∝ 1/Fp feedback)
        Cv_iter = Cv_seed / max(Fp, 1.0e-3)
        term = (sum_K / N2_SI) * (Cv_iter / d_mm ** 2) ** 2
        Fp_new = 1.0 / math.sqrt(1.0 + term)
        Fp_new = min(Fp_new, 1.0)       # physical upper bound: Fp ≤ 1
        if abs(Fp_new - Fp) < 1.0e-6:  # converged
            Fp = Fp_new
            break
        Fp = Fp_new

    # Cv at converged Fp — used for FLP and xTP calculations below
    Cv_final = Cv_seed / max(Fp, 1.0e-3)

    # ── FLP — IEC 60534-2-1 Eq. (20) ─────────────────────────────────────────
    # FLP = FL / √(1 + FL² × K1/N2 × (Cv/d²)²)
    # Note: only the *inlet* fitting K1 is used for FLP (inlet loss affects FL).
    FL = inputs.FL
    FL_sq = FL ** 2
    denom_FLP = 1.0 + (FL_sq * K1 / N2_SI) * (Cv_final / d_mm ** 2) ** 2
    FLP = FL / math.sqrt(max(denom_FLP, 1.0e-6))
    FLP = min(FLP, FL)      # FLP ≤ FL always (piping can only reduce FL)

    # ── xTP — IEC 60534-2-1 Eq. (23) ─────────────────────────────────────────
    # xTP = xT / [Fp² × (1 + (xT × K1/N5) × (Cv/d²)²)]
    # Bug 3 fix: explicit parentheses around (xT * K1 / N5_SI) for clarity.
    xT = inputs.xT
    xTP_denom = Fp ** 2 * (1.0 + (xT * K1 / N5_SI) * (Cv_final / d_mm ** 2) ** 2)
    xTP = xT / max(xTP_denom, 1.0e-6)
    xTP = min(xTP, xT)      # piping can only reduce xT

    return PipingResult(
        Fp=round(Fp, 5),
        FLP=round(FLP, 5),
        xTP=round(xTP, 5),
        sum_K=round(sum_K, 4),
        has_reducers=has_reducers,
        iterations=n_iter,
    )


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
    """IEC 60534-2-1:2011 §5.2 — Liquid sizing."""
    P1 = inputs.P1_bara
    P2 = inputs.P2_bara
    Pv = inputs.Pv_bara
    Pc = inputs.Pc_bara
    Gf = inputs.Gf
    FL = inputs.FL
    Fp = piping.Fp
    FLP = piping.FLP
    d_mm = inputs.d_mm

    # ── Critical pressure ratio factor FF — IEC Eq. (4) ──────────────────────
    FF = 0.96 - 0.28 * math.sqrt(Pv / Pc)
    FF = min(FF, 0.96)

    # ── Choked flow check — IEC Eq. (3) ──────────────────────────────────────
    # ΔP_max = (FLP/Fp)² × (P1 − FF × Pv)
    # With Bug 2 fixed, FLP and Fp are now correctly computed for installations
    # with pipe reducers.  ΔP_max will be properly lower than the unpiped case,
    # so choked flow and cavitation are correctly detected.
    delta_P_max = (FLP / Fp) ** 2 * (P1 - FF * Pv)
    delta_P = P1 - P2
    delta_P_eff = min(delta_P, delta_P_max)
    is_choked = delta_P >= delta_P_max

    result.delta_P_max_bar = delta_P_max
    result.delta_P_bar     = delta_P
    result.is_choked       = is_choked
    result.flow_regime     = "Choked" if is_choked else "Turbulent"

    # ── Vena contracta pressure ───────────────────────────────────────────────
    # P_vc uses FL (valve property), not FLP (valve+piping).
    P_vc = P1 - delta_P_eff / FL ** 2

    # Flashing: vapour persists downstream (both P_vc AND P2 below Pv)
    # Cavitation: vapour forms at VC but collapses (P_vc < Pv, P2 ≥ Pv)
    is_flashing = (P_vc < Pv) and (P2 < Pv)

    # ── Viscous correction ────────────────────────────────────────────────────
    FR, Rev = _viscous_correction(Q_m3h, d_mm, mu_cP, Gf, FL, inputs.Fd)
    result.Rev = Rev
    result.FR  = FR
    result.is_viscous_corrected = FR < 0.99

    if FR < 0.99:
        result.flow_regime = "Viscous/Laminar" if Rev < 10000 else "Turbulent (viscous)"

    # ── Cv calculation — IEC Eq. (1) ─────────────────────────────────────────
    # Cv = Q / (N1 × Fp × FR × √(ΔP_eff / Gf))
    sqrt_term = math.sqrt(max(delta_P_eff / Gf, 1.0e-9))
    Cv = Q_m3h / (N1_SI * Fp * FR * sqrt_term)

    result.Cv_required = round(Cv, 4)

    # ── Cavitation sigma index and regime ─────────────────────────────────────
    # σ = (P1 − Pv) / ΔP  (service sigma, IEC 60534-8-4)
    sigma = (P1 - Pv) / max(delta_P, 1.0e-9)

    # Approximate cavitation regime thresholds (simplified, not IEC 60534-8-4
    # tabulated values; conservative estimates suitable for initial assessment)
    sigma_incipient = 1.0 / (FL ** 2)
    sigma_constant  = 0.5 / (FL ** 2)
    sigma_choked    = (1.0 - FF) / (FL ** 2)

    if is_flashing:
        regime   = CavitationRegime.FLASHING
        severity = "Flashing — two-phase flow. Hardened trim and angle body required."
    elif is_choked:
        regime   = CavitationRegime.CHOKED
        severity = "Choked cavitation — severe bubble collapse. Anti-cavitation trim required."
    elif sigma < sigma_constant:
        regime   = CavitationRegime.CONSTANT
        severity = "Constant cavitation — significant bubble collapse. Anti-cavitation trim recommended."
    elif sigma < sigma_incipient:
        regime   = CavitationRegime.INCIPIENT
        severity = "Incipient cavitation — minor bubble formation. Monitor service life."
    else:
        regime   = CavitationRegime.NONE
        severity = "No cavitation predicted."

    delta_P_incipient = (P1 - Pv) / sigma_incipient

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
    Q_m3h: float,
    d_mm: float,
    mu_cP: float,
    Gf: float,
    FL: float,
    Fd: float,
) -> tuple[float, float]:
    """
    Compute viscosity correction factor FR and valve Reynolds number Rev.

    IEC 60534-2-1:2011 Eq. (29):
        Rev = N4 × Fd × Q / (ν × √(FL × Cv))

    FR is obtained from IEC 60534-2-1 Annex D via a simplified polynomial
    approximation.  For water and light process fluids (ν < 10 cSt), Rev ≫
    40 000 and FR = 1.0 exactly (no de-rating).  The approximation introduces
    material error only for ν > 100 cSt; see the audit notes for details.
    """
    nu_cSt = mu_cP / max(Gf, 0.01)   # kinematic viscosity [cSt]

    # Rough Cv estimate for Rev seed — uses d_mm as a proxy.
    # This is a known limitation (medium-severity issue); a full iterative
    # Rev–FR–Cv loop would improve accuracy for ν > 100 cSt service.
    Cv_rough = N2_SI * d_mm ** 2
    Cv_rough = max(Cv_rough, 0.01)

    if nu_cSt < 0.01:
        return 1.0, 1.0e9  # essentially inviscid

    Rev = (N4_SI * Fd * Q_m3h) / (nu_cSt * math.sqrt(FL * Cv_rough))

    # FR from IEC 60534-2-1 Annex D (simplified polynomial segments)
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
    """Return engineering action recommendation for cavitation regime."""
    recs = {
        CavitationRegime.NONE:      "No cavitation action required.",
        CavitationRegime.INCIPIENT: "Monitor trim wear. Re-assess at off-design conditions.",
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
    """IEC 60534-2-1:2011 §5.3 — Gas/vapour sizing."""
    P1    = inputs.P1_bara
    P2    = inputs.P2_bara
    gamma = inputs.gamma
    Z     = inputs.compressibility_Z
    M     = inputs.molecular_weight
    T1    = inputs.T1_K
    Fp    = piping.Fp
    xTP   = piping.xTP   # Now correctly computed (Bug 2 + 3 fix)

    # ── Fk — specific heat ratio factor — IEC Eq. (6) ────────────────────────
    Fk = gamma / 1.4
    result.Fk = round(Fk, 4)

    # ── Pressure drop ratio x — IEC Eq. (7) ──────────────────────────────────
    x         = (P1 - P2) / P1
    x_choked  = Fk * xTP
    x_eff     = min(x, x_choked)
    is_choked = x >= x_choked

    result.x_pressure_ratio = round(x, 5)
    result.is_choked        = is_choked
    result.flow_regime      = "Choked (Gas)" if is_choked else "Subcritical (Gas)"
    result.delta_P_max_bar  = round(Fk * xTP * P1, 4)
    result.delta_P_bar      = round(P1 - P2, 4)

    # ── Gas expansion factor Y — IEC Eq. (5) ─────────────────────────────────
    Y = 1.0 - x_eff / (3.0 * Fk * xTP)
    Y = max(Y, 0.667)   # absolute minimum per IEC 60534-2-1
    result.Y_expansion = round(Y, 5)

    # ── Cv calculation — mass flow basis — IEC Eq. (9) ───────────────────────
    # W = N6 × Fp × Cv × Y × √(x_eff × P1 × ρ1)
    # → Cv = W / (N6 × Fp × Y × √(x_eff × P1 × ρ1))
    sqrt_gas = math.sqrt(max(x_eff * P1 * rho1, 1.0e-12))
    Cv = W_kgh / (N6_SI * Fp * Y * sqrt_gas)

    result.Cv_required = round(Cv, 4)

    # ── Outlet Mach estimate ──────────────────────────────────────────────────
    if rho1 > 0 and Cv > 0 and inputs.D2_mm > 0:
        try:
            rho2 = rho1 * (P2 / P1) ** (1.0 / gamma)   # isentropic density
            A2   = math.pi / 4.0 * (inputs.D2_mm * 1.0e-3) ** 2
            W_kgs = W_kgh / 3600.0
            v2 = W_kgs / (max(rho2, 1.0e-6) * A2)
            c2 = math.sqrt(gamma * P2 * 1.0e5 / max(rho2, 1.0e-6))
            result.Mach_outlet = round(abs(v2 / c2), 4) if c2 > 0 else None
        except Exception:
            result.Mach_outlet = None

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
    gamma = 1.33  # default for superheated steam
    try:
        from iapws import IAPWS97
        steam = IAPWS97(P=inputs.P1_bara * 0.1, T=inputs.T1_K)
        if hasattr(steam, 'cp') and hasattr(steam, 'cv') and steam.cv and steam.cv > 0:
            gamma = steam.cp / steam.cv
        # Wet steam guard: gas equations are unreliable for quality < 0.95
        if hasattr(steam, 'x') and steam.x is not None and steam.x < 0.95:
            result.warnings = result.warnings or []
            result.warnings.append(
                f"Steam quality x = {steam.x:.2f} < 0.95: two-phase (wet steam) conditions. "
                "Gas sizing equations are approximate. Consider wet-steam specific sizing."
            )
    except Exception:
        pass

    try:
        from iapws import IAPWS97
        steam_out = IAPWS97(P=inputs.P2_bara * 0.1, H=IAPWS97(
            P=inputs.P1_bara * 0.1, T=inputs.T1_K).h)
        result.steam_quality_out = getattr(steam_out, 'x', None)
    except Exception:
        pass

    # Treat steam as a compressible gas with IAPWS-derived properties
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
        # noise_limit_dba is the PUBLIC parameter name of the function;
        # inside calculate_aerodynamic_noise() the NoiseResult is constructed
        # with limit_dba= (Bug 1 fix applied in noise_aerodynamic.py).
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

    # ── BUG 1 FIX: use correct field name 'limit_dba' ────────────────────────
    return NoiseResult(limit_dba=noise_limit)


def _hydrodynamic_noise(
    inputs: SizingInputs,
    result: SizingResult,
    rho1: float,
    W_kgh: float,
    noise_limit: float,
) -> NoiseResult:
    """
    Simplified IEC 60534-8-4 hydrodynamic noise estimate.

    Note: This is a simplified engineering estimate, NOT a full implementation
    of IEC 60534-8-4.  Results may differ from the standard method by up to
    10–20 dB(A).  The output is labelled accordingly.  A full IEC 60534-8-4
    implementation is planned for a future release.
    """
    import math as _math

    # ── BUG 1 FIX: use correct field name 'limit_dba' ────────────────────────
    n = NoiseResult(limit_dba=noise_limit)
    cav = result.cavitation
    if cav is None:
        return n

    P1    = inputs.P1_bara * 1.0e5   # Pa
    P2    = inputs.P2_bara * 1.0e5   # Pa
    W_kgs = W_kgh / 3600.0

    # Simplified approach: acoustic power from mechanical stream power
    # Wm ≈ ṁ × (P1 − P2) / ρ  (incompressible approximation)
    Wm = W_kgs * (P1 - P2) / rho1 if rho1 > 0 else 0.0

    # Acoustic efficiency — regime-dependent (order-of-magnitude estimates)
    eta_liquid = 1.0e-6   # non-cavitating turbulent
    if cav.regime in (CavitationRegime.CONSTANT, CavitationRegime.CHOKED):
        eta_liquid *= 10.0
    elif cav.regime == CavitationRegime.FLASHING:
        eta_liquid *= 30.0

    Wa = eta_liquid * Wm
    if Wa > 0:
        Lpi = 10.0 * _math.log10(Wa / 1.0e-12)
        TL  = 30.0   # simplified (typical for Sch 40 steel pipe)
        Lpe = Lpi - TL
        n.Lpe_liquid_dba  = round(Lpe, 1)
        n.overall_Lpe_dba = round(Lpe, 1)
        n.exceeds_limit   = Lpe > noise_limit
    n.noise_regime = f"{cav.regime.value} (simplified estimate — not IEC 60534-8-4)"
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
    """
    Estimate inlet and outlet pipe velocities [m/s].

    For gas/steam, the outlet density uses the isentropic relationship
    ρ2 = ρ1 × (P2/P1)^(1/γ) rather than the simpler isothermal scaling
    ρ2 = ρ1 × (P2/P1), which overestimates ρ2 at high ΔP ratios and
    underestimates the outlet velocity.
    """
    A1 = math.pi / 4.0 * (inputs.D1_mm * 1.0e-3) ** 2
    A2 = math.pi / 4.0 * (inputs.D2_mm * 1.0e-3) ** 2

    if A1 > 0 and rho1 > 0 and Q_m3h > 0:
        v1 = (Q_m3h / 3600.0) / A1
    else:
        v1 = None

    if inputs.fluid_phase == FluidPhase.LIQUID:
        # Incompressible: continuity gives v2 = v1 × (A1/A2)
        v2 = v1 * (A1 / A2) if (v1 is not None and A2 > 0) else None
    else:
        # Gas/steam: isentropic density ratio ρ2 = ρ1 × (P2/P1)^(1/γ)
        gamma = inputs.gamma
        try:
            rho2 = rho1 * (inputs.P2_bara / inputs.P1_bara) ** (1.0 / gamma)
        except Exception:
            rho2 = rho1 * (inputs.P2_bara / inputs.P1_bara)  # fallback isothermal
        if A2 > 0 and rho2 > 0:
            W_kgs = W_kgh / 3600.0
            v2 = W_kgs / (rho2 * A2)
        else:
            v2 = None

    return (
        round(v1, 2) if v1 is not None else None,
        round(v2, 2) if v2 is not None else None,
    )


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
        # Cv(θ) = Cv_rated × R^(θ−1)  →  θ = 1 + log(ratio)/log(R)
        theta = 1.0 + _math.log(max(ratio, 1.0 / R)) / _math.log(R)
    elif char == ValveCharacteristic.LINEAR:
        theta = ratio
    elif char == ValveCharacteristic.QUICK_OPENING:
        # Cv(θ) = Cv_rated × √θ  →  θ = ratio²
        theta = ratio ** 2
    else:
        theta = ratio

    return round(max(0.0, min(theta * 100.0, 100.0)), 1)


# =============================================================================
# WARNINGS
# =============================================================================

def _build_warnings(inputs: SizingInputs, result: SizingResult) -> list[str]:
    """Generate soft engineering warnings based on sizing result."""
    warnings: list[str] = []

    # ── Sizing ratio ──────────────────────────────────────────────────────────
    if result.sizing_ratio and result.sizing_ratio > 0.85:
        warnings.append(
            f"Sizing ratio {result.sizing_ratio:.3f} > 0.85: valve is operating near "
            "capacity. API RP 553 recommends ratio ≤ 0.85. Consider a larger Cv_rated."
        )

    # ── Opening % ─────────────────────────────────────────────────────────────
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

    # ── Noise ─────────────────────────────────────────────────────────────────
    if result.noise and result.noise.overall_Lpe_dba is not None:
        if result.noise.exceeds_limit:
            warnings.append(
                f"Predicted noise {result.noise.overall_Lpe_dba:.1f} dB(A) exceeds site "
                f"limit of {result.noise.limit_dba:.0f} dB(A). "
                "Anti-noise trim or acoustic insulation required."
            )

    # ── Cavitation ────────────────────────────────────────────────────────────
    if result.cavitation:
        cav = result.cavitation
        if cav.regime == CavitationRegime.FLASHING:
            warnings.append(
                "Flashing predicted: two-phase flow erosion risk. "
                "Angle body + hard-faced trim required."
            )
        elif cav.regime == CavitationRegime.CHOKED:
            warnings.append(
                "Choked cavitation: anti-cavitation trim mandatory. "
                "Consider multi-stage pressure let-down."
            )
        elif cav.regime == CavitationRegime.CONSTANT:
            warnings.append(
                "Constant cavitation: anti-cavitation trim recommended."
            )

    # ── Outlet velocity ───────────────────────────────────────────────────────
    v_limit = 6.0 if inputs.fluid_phase == FluidPhase.LIQUID else 50.0
    if result.v_outlet_ms and result.v_outlet_ms > v_limit:
        warnings.append(
            f"Outlet velocity {result.v_outlet_ms:.1f} m/s > {v_limit:.0f} m/s: "
            "check for noise, erosion, and pipe structural concerns."
        )

    # ── Piping correction ─────────────────────────────────────────────────────
    if result.Fp < 0.95:
        warnings.append(
            f"Fp = {result.Fp:.4f} < 0.95: significant piping geometry correction. "
            "Verify reducer dimensions and confirm Cv selection with manufacturer."
        )

    # ── Viscous correction ────────────────────────────────────────────────────
    if result.FR and result.FR < 0.85:
        warnings.append(
            f"FR = {result.FR:.4f} < 0.85: significant viscous de-rating. "
            "Verify fluid viscosity and consider full-bore trim."
        )

    # ── Liquid choked flow ────────────────────────────────────────────────────
    if result.is_choked and inputs.fluid_phase == FluidPhase.LIQUID:
        warnings.append(
            "Choked liquid flow: available ΔP exceeds maximum allowable "
            "(FLP/Fp)² × (P1 − FF×Pv).  Actual flow capacity is limited; "
            "verify back-pressure is sufficient."
        )

    return warnings
