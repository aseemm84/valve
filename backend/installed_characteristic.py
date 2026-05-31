"""
backend/installed_characteristic.py
=====================================
Inherent and installed valve characteristic curve computation.

Theory
------
The *inherent* characteristic relates Cv to valve opening (travel θ)
under constant ΔP conditions (laboratory test).  The *installed*
characteristic is what the valve actually delivers in a real piping
system where ΔP across the valve changes with flow.

For a system with fixed total ΔP and a valve that absorbs fraction β
at design flow:

    q/q_design = Cv(θ) / Cv_design × √(β / (1 – β + β × (Cv(θ)/Cv_design)²))

Equivalently:
    Cv_installed(θ) = Cv_design × q/q_design

This module computes both curves at 51 equally-spaced travel points
(0 % to 100 %) and returns a structured result for plotting.

References
----------
Driskell, L. (1983) — Control-Valve Selection and Sizing, ISA
ISA-75.11.01-1985 — Inherent flow characteristic and rangeability
IEC 60534-2-4:2009 — Inherent flow characteristics
"""

from __future__ import annotations

import math
from typing import Optional

from backend.models import (
    InstalledCharPoint,
    InstalledCharResult,
    ValveCharacteristic,
)

# Number of points on each curve
N_POINTS: int = 51


def _inherent_cv(
    theta_frac: float,
    Cv_rated: float,
    char: ValveCharacteristic,
    R: float = 50.0,
) -> float:
    """
    Compute inherent Cv at travel fraction θ ∈ [0, 1].

    Parameters
    ----------
    theta_frac : float
        Valve travel as fraction of full travel [0, 1].
    Cv_rated : float
        Rated Cv at full open (θ = 1).
    char : ValveCharacteristic
        Inherent characteristic type.
    R : float
        Rangeability (Cv_max / Cv_min at rated conditions).
        Default 50:1 per ISA-75.01.01.

    Returns
    -------
    float
        Cv at travel θ.

    Notes
    -----
    Equal-percentage:
        Cv(θ) = Cv_rated × R^(θ – 1)   [IEC 60534-2-4 Eq. 1]

    Linear:
        Cv(θ) = Cv_rated × θ

    Quick-opening:
        Cv(θ) = Cv_rated × √θ          (parabolic approximation)
    """
    theta_frac = max(0.0, min(theta_frac, 1.0))
    if theta_frac == 0.0:
        return Cv_rated / R  # minimum controllable Cv (not zero)

    if char == ValveCharacteristic.EQUAL_PERCENTAGE:
        return Cv_rated * (R ** (theta_frac - 1.0))

    elif char == ValveCharacteristic.LINEAR:
        return Cv_rated * theta_frac

    elif char == ValveCharacteristic.QUICK_OPENING:
        return Cv_rated * math.sqrt(theta_frac)

    return Cv_rated * theta_frac  # fallback: linear


def _installed_flow_fraction(
    Cv_theta: float,
    Cv_design: float,
    beta: float,
) -> float:
    """
    Compute installed flow fraction q/q_design for a given Cv.

    From the system equation (series pressure drops):

        (q/q_d)² = (Cv(θ)/Cv_d)² × β / [1 – β + β × (Cv(θ)/Cv_d)²]

    Parameters
    ----------
    Cv_theta : float
        Cv at valve travel θ.
    Cv_design : float
        Cv at design operating point (Cv_required).
    beta : float
        Fraction of total system ΔP across the valve at design flow.

    Returns
    -------
    float
        Flow fraction q/q_design ∈ [0, 1+].
    """
    if Cv_design <= 0:
        return 0.0
    r = Cv_theta / Cv_design
    denom = 1.0 - beta + beta * r * r
    if denom <= 0:
        return 0.0
    return r * math.sqrt(beta / denom)


def calculate_installed_characteristic(
    Cv_rated: float,
    Cv_required: float,
    char: ValveCharacteristic,
    beta: float,
    R_inherent: float = 50.0,
) -> InstalledCharResult:
    """
    Generate inherent and installed Cv curves for a control valve.

    Parameters
    ----------
    Cv_rated : float
        Manufacturer's rated Cv at full open.
    Cv_required : float
        Required Cv at design flow (operating point).
    char : ValveCharacteristic
        Inherent characteristic type.
    beta : float
        ΔP_valve / ΔP_total at design flow (system pressure-drop fraction).
        Range: 0 < beta ≤ 1.  beta = 1 → pure valve-controlled system.
    R_inherent : float
        Inherent rangeability of the valve (default 50:1 for globe).

    Returns
    -------
    InstalledCharResult
        Complete curve data with 51 points and controllability assessment.

    Raises
    ------
    ValueError
        If Cv_rated ≤ 0 or Cv_required ≤ 0 or beta outside (0, 1].
    """
    if Cv_rated <= 0:
        raise ValueError(f"Cv_rated must be positive, got {Cv_rated}")
    if Cv_required <= 0:
        raise ValueError(f"Cv_required must be positive, got {Cv_required}")
    if not (0.0 < beta <= 1.0):
        raise ValueError(f"beta must be in (0, 1], got {beta}")

    # Design travel fraction (where Cv_required sits on the inherent curve)
    design_theta = _find_travel_for_cv(Cv_required, Cv_rated, char, R_inherent)
    design_opening_pct = design_theta * 100.0

    points: list[InstalledCharPoint] = []
    flow_fracs_installed: list[float] = []

    for i in range(N_POINTS):
        theta = i / (N_POINTS - 1)  # 0.0 to 1.0
        theta_pct = theta * 100.0

        Cv_inh = _inherent_cv(theta, Cv_rated, char, R_inherent)
        q_inh = Cv_inh / Cv_rated  # inherent flow fraction (constant ΔP)

        q_inst = _installed_flow_fraction(Cv_inh, Cv_required, beta)
        # Cv equivalent for installed curve
        Cv_inst = q_inst * Cv_required

        flow_fracs_installed.append(q_inst)

        points.append(InstalledCharPoint(
            opening_pct=round(theta_pct, 1),
            Cv_inherent=round(Cv_inh, 4),
            Cv_installed=round(Cv_inst, 4),
            flow_fraction_inherent=round(q_inh, 6),
            flow_fraction_installed=round(q_inst, 6),
        ))

    # ── Controllability assessment ─────────────────────────────────────────

    # Gain at design point (dq/dθ at θ_design)
    gain_at_design = _compute_gain(design_theta, Cv_required, Cv_rated, char, beta, R_inherent)

    # Gain variation: compute over 20 % – 80 % travel range
    gains = []
    for i in range(N_POINTS):
        theta = i / (N_POINTS - 1)
        if 0.2 <= theta <= 0.8:
            g = _compute_gain(theta, Cv_required, Cv_rated, char, beta, R_inherent)
            if g > 0:
                gains.append(g)

    gain_variability_pct: Optional[float] = None
    if gains:
        g_max, g_min = max(gains), min(gains)
        if g_min > 0:
            gain_variability_pct = (g_max / g_min - 1.0) * 100.0

    # Controllability: installed gain should not vary by more than 4:1
    is_controllable = True
    recommendation = ""

    if beta < 0.25:
        is_controllable = False
        recommendation = (
            "⚠ Low valve authority (β = {:.2f} < 0.25): the installed characteristic "
            "is severely distorted. The valve absorbs less than 25% of system ΔP at "
            "design flow. Consider re-evaluating the system design, increasing valve "
            "ΔP allocation, or switching to an equal-percentage characteristic.".format(beta)
        )
    elif gain_variability_pct and gain_variability_pct > 300:
        is_controllable = False
        recommendation = (
            "⚠ High installed gain variability ({:.0f}%): control loop stability "
            "may be compromised across the operating range. "
            "Consider anti-surge or characterised positioner cam correction.".format(
                gain_variability_pct)
        )
    elif char == ValveCharacteristic.QUICK_OPENING and beta < 0.5:
        recommendation = (
            "ℹ Quick-opening characteristic with β < 0.5: "
            "this combination gives very high installed gain at low openings. "
            "Linear or equal-percentage is recommended for better controllability."
        )
    elif char == ValveCharacteristic.LINEAR and beta >= 0.7:
        recommendation = (
            "✓ Linear characteristic with high valve authority (β ≥ 0.70): "
            "good installed linearity expected."
        )
    elif char == ValveCharacteristic.EQUAL_PERCENTAGE:
        if 0.25 <= beta <= 0.50:
            recommendation = (
                "✓ Equal-percentage characteristic with β ∈ [0.25, 0.50]: "
                "installed characteristic will be approximately linear — ideal for PID control."
            )
        else:
            recommendation = (
                "ℹ Equal-percentage characteristic: well-suited for systems "
                "where valve ΔP varies significantly with flow."
            )
    else:
        recommendation = "✓ Installed characteristic appears acceptable for this operating point."

    return InstalledCharResult(
        beta=beta,
        char=char,
        Cv_rated=Cv_rated,
        rangeability_inherent=R_inherent,
        points=points,
        design_opening_pct=round(design_opening_pct, 1),
        is_controllable=is_controllable,
        gain_at_design=round(gain_at_design, 4) if gain_at_design else None,
        gain_variability_pct=round(gain_variability_pct, 1) if gain_variability_pct else None,
        recommendation=recommendation,
    )


def _find_travel_for_cv(
    Cv_target: float,
    Cv_rated: float,
    char: ValveCharacteristic,
    R: float = 50.0,
    n_iter: int = 50,
) -> float:
    """
    Binary search for travel fraction θ that gives Cv_target on the
    inherent characteristic.

    Returns
    -------
    float
        Travel fraction ∈ [0, 1].
    """
    lo, hi = 0.0, 1.0
    for _ in range(n_iter):
        mid = (lo + hi) / 2.0
        cv_mid = _inherent_cv(mid, Cv_rated, char, R)
        if cv_mid < Cv_target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _compute_gain(
    theta: float,
    Cv_design: float,
    Cv_rated: float,
    char: ValveCharacteristic,
    beta: float,
    R: float,
    delta: float = 0.01,
) -> float:
    """
    Numerical derivative dq_inst/dθ at travel fraction θ.

    Parameters
    ----------
    theta : float
        Travel fraction [0, 1].
    Cv_design : float
        Cv at design operating point.
    Cv_rated : float
        Rated Cv.
    char : ValveCharacteristic
        Inherent characteristic.
    beta : float
        Valve authority.
    R : float
        Rangeability.
    delta : float
        Step size for numerical differentiation.

    Returns
    -------
    float
        Installed gain dq/dθ at the given travel point.
    """
    theta_lo = max(theta - delta, 0.0)
    theta_hi = min(theta + delta, 1.0)

    Cv_lo = _inherent_cv(theta_lo, Cv_rated, char, R)
    Cv_hi = _inherent_cv(theta_hi, Cv_rated, char, R)

    q_lo = _installed_flow_fraction(Cv_lo, Cv_design, beta)
    q_hi = _installed_flow_fraction(Cv_hi, Cv_design, beta)

    dtheta = theta_hi - theta_lo
    if dtheta <= 0:
        return 0.0
    return (q_hi - q_lo) / dtheta
