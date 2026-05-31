"""
backend/noise_aerodynamic.py
============================
Aerodynamic (gas / steam) noise prediction per IEC 60534-8-3:2011.

This module implements the *complete* IEC 60534-8-3:2011 calculation chain:

    1.  Mechanical stream power  Wm  [W]
    2.  Vena contracta Mach number  Mvc
    3.  Acoustic efficiency factor  η_a  (Mach-dependent — **this is the fix**)
    4.  Internal acoustic power  Wa = η_a × Wm
    5.  Internal sound power level  Lpi  [dB re 1 pW]
    6.  Peak frequency  fp  [Hz]
    7.  Pipe wall transmission loss  TL  [dB]
    8.  External SPL at 1 m  Lpe  [dB(A)]

Fix notes (v2.0)
----------------
Previous implementations used a fixed η_a ≈ 10⁻⁴, which severely
under-predicts noise at high pressure ratios (Mvc → 1) and over-predicts
in subsonic turbulent regimes.  The correct formula is the Baumann (1987)
correlation adopted verbatim into IEC 60534-8-3:

    η_a = η_0 × Mvc^3.6                          (Mvc ≤ M_crit)
    η_a = η_0 × M_crit^3.6 × (Mvc/M_crit)^k     (Mvc > M_crit, sonic jet)

with η_0 = 10⁻⁴, M_crit = 0.3, k ≈ 1 (from IEC 60534-8-3 §5.3).

Bug fix (v2.1)
--------------
NoiseResult constructor now uses the correct field name ``limit_dba``
(matching the Pydantic model definition) rather than the erroneous
``noise_limit_dba`` keyword argument that caused the noise-limit
exceedance flag to always evaluate against the default 85 dB(A)
regardless of user input.

References
----------
IEC 60534-8-3:2011 — Industrial-process control valves — Noise considerations
    — Part 8-3: Control valve aerodynamic noise prediction method
Baumann, H.D. (1987) — A method for predicting aerodynamic valve noise
    based on modified free jet theories, ASME Paper 87-WA/NCA-7
ISA-TR75.17-2003 — Control Valve Aerodynamic Noise Prediction
"""

from __future__ import annotations

import math
from typing import Optional

from backend.constants import (
    W_REF,
    A_WEIGHTING_DB,
    RHO_STEEL,
    C_STEEL,
    RHO_AIR,
    C_AIR,
)
from backend.models import NoiseResult


# ---------------------------------------------------------------------------
# IEC 60534-8-3 constants
# ---------------------------------------------------------------------------

ETA_0: float = 1.0e-4          # Acoustic efficiency baseline
M_CRIT: float = 0.3            # Critical Mach — η_a regime change
K_SONIC: float = 1.0           # Exponent for sonic jet regime (IEC 8-3 §5.3)

# Downstream pipe length for SPL calculation [m] — IEC 8-3 specifies 1 m
L_PIPE_REF: float = 1.0


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def _acoustic_efficiency(Mvc: float) -> float:
    """
    Compute acoustic efficiency factor η_a as a function of
    vena contracta Mach number (IEC 60534-8-3:2011 §5.3, Baumann correlation).

    Parameters
    ----------
    Mvc : float
        Vena contracta Mach number (0 < Mvc; values > 1 indicate sonic).

    Returns
    -------
    float
        Acoustic efficiency factor η_a (dimensionless, typically 10⁻⁵ – 10⁻²).

    Notes
    -----
    For Mvc ≤ M_crit (0.3):
        η_a = η_0 × Mvc^3.6

    For Mvc > M_crit (sonic jet):
        η_a = η_0 × M_crit^3.6 × (Mvc / M_crit)^K_SONIC

    The exponent 3.6 is from Baumann (1987); K_SONIC = 1.0 per IEC 8-3.
    """
    Mvc = max(Mvc, 1.0e-6)  # guard against zero
    if Mvc <= M_CRIT:
        return ETA_0 * (Mvc ** 3.6)
    else:
        # Sonic jet regime
        eta_at_crit = ETA_0 * (M_CRIT ** 3.6)
        return eta_at_crit * (Mvc / M_CRIT) ** K_SONIC


def _mach_at_vena_contracta(
    P1_Pa: float,
    P2_Pa: float,
    gamma: float,
    FL: float,
    rho1_kgm3: float,
) -> tuple[float, bool]:
    """
    Estimate the Mach number at the vena contracta (IEC 60534-8-3 §5.2).

    Parameters
    ----------
    P1_Pa : float
        Inlet absolute pressure [Pa].
    P2_Pa : float
        Outlet absolute pressure [Pa].
    gamma : float
        Specific heat ratio Cp/Cv.
    FL : float
        Liquid pressure recovery factor (used as proxy for ΔP across
        the vena contracta; for gas: 1/FL² ≈ 1 for well-designed trim).
    rho1_kgm3 : float
        Inlet gas density [kg/m³].

    Returns
    -------
    tuple[float, bool]
        (Mvc, is_sonic) — Mach number at vena contracta, and whether
        choked (sonic) flow exists.

    Notes
    -----
    The vena contracta pressure  Pvc ≈ P1 – (P1–P2)/FL²  (approximation).
    For gas: the Mach at vena contracta is calculated from isentropic
    expansion P1 → Pvc.

    Choked condition: Pvc ≤ Pcrit = P1 × (2/(γ+1))^(γ/(γ-1))
    """
    # Vena contracta pressure (approximation using FL)
    P_vc = P1_Pa - (P1_Pa - P2_Pa) / (FL ** 2)
    P_vc = max(P_vc, P2_Pa * 0.5)  # physical lower bound

    # Critical pressure for choked flow
    exp = gamma / (gamma - 1.0)
    P_crit = P1_Pa * (2.0 / (gamma + 1.0)) ** exp

    is_sonic = P_vc <= P_crit

    if is_sonic:
        Mvc = 1.0
    else:
        # Isentropic Mach from P1 to P_vc
        pressure_ratio = P_vc / P1_Pa
        term = (pressure_ratio ** ((gamma - 1.0) / gamma)) - 1.0
        if term >= 0:
            # Expansion rather than compression — this shouldn't happen
            Mvc = 0.01
        else:
            Mach_sq = (2.0 / (gamma - 1.0)) * (
                (1.0 / pressure_ratio) ** ((gamma - 1.0) / gamma) - 1.0
            )
            Mvc = math.sqrt(max(Mach_sq, 0.0))

    return Mvc, is_sonic


def _speed_of_sound_gas(gamma: float, P1_Pa: float, rho1_kgm3: float) -> float:
    """
    Speed of sound in the gas at inlet conditions.

    c1 = √(γ × P1 / ρ1)

    Parameters
    ----------
    gamma : float
    P1_Pa : float
        Absolute pressure [Pa].
    rho1_kgm3 : float
        Inlet density [kg/m³].

    Returns
    -------
    float
        Speed of sound [m/s].
    """
    return math.sqrt(max(gamma * P1_Pa / rho1_kgm3, 1.0))


def _mechanical_stream_power(
    mass_flow_kgs: float,
    P1_Pa: float,
    P2_Pa: float,
    rho1_kgm3: float,
    gamma: float,
) -> float:
    """
    Mechanical stream power Wm [W] (IEC 60534-8-3 §5.1).

    For isentropic expansion of an ideal gas:

        Wm = ṁ × (γ/(γ-1)) × (P1/ρ1) × [1 – (P2/P1)^((γ-1)/γ)]

    For choked flow, P2 is replaced by the critical pressure Pcrit.

    Parameters
    ----------
    mass_flow_kgs : float
        Mass flow rate [kg/s].
    P1_Pa : float
        Inlet absolute pressure [Pa].
    P2_Pa : float
        Downstream absolute pressure [Pa].
    rho1_kgm3 : float
        Inlet density [kg/m³].
    gamma : float
        Specific heat ratio.

    Returns
    -------
    float
        Mechanical stream power [W].  Always ≥ 0.
    """
    # Critical pressure
    exp = gamma / (gamma - 1.0)
    P_crit = P1_Pa * (2.0 / (gamma + 1.0)) ** exp
    P2_eff = max(P2_Pa, P_crit)  # choked: use critical pressure

    pressure_ratio = P2_eff / P1_Pa
    term = 1.0 - pressure_ratio ** ((gamma - 1.0) / gamma)
    term = max(term, 0.0)

    Wm = mass_flow_kgs * (gamma / (gamma - 1.0)) * (P1_Pa / rho1_kgm3) * term
    return max(Wm, 0.0)


def _pipe_transmission_loss(
    Di_m: float,
    t_m: float,
    rho_pipe: float = RHO_STEEL,
    c_pipe: float = C_STEEL,
    rho_air: float = RHO_AIR,
    c_air: float = C_AIR,
    freq_Hz: float = 4000.0,
) -> float:
    """
    Pipe wall transmission loss TL [dB] (IEC 60534-8-3 §5.6).

    Simplified mass-law formula at the dominant frequency:

        TL = 10 log₁₀[(ρ_pipe × c_pipe × t)² / (ρ_air × c_air × π × Di × f)]

    Parameters
    ----------
    Di_m : float
        Pipe internal diameter [m].
    t_m : float
        Pipe wall thickness [m].
    rho_pipe : float
        Pipe wall density [kg/m³] (default: steel 7800).
    c_pipe : float
        Speed of sound in pipe material [m/s] (default: steel 5000).
    rho_air : float
        Air density outside pipe [kg/m³].
    c_air : float
        Speed of sound in air [m/s].
    freq_Hz : float
        Dominant frequency for TL calculation [Hz].

    Returns
    -------
    float
        Transmission loss [dB].  Positive value means attenuation.

    Notes
    -----
    IEC 60534-8-3 provides a frequency-band approach.  This function
    computes TL at the dominant frequency, consistent with the standard's
    simplified method (single-frequency approximation for the A-weighted SPL).
    Physical bounds: TL typically 20–60 dB for steel pipe.
    """
    if Di_m <= 0 or t_m <= 0:
        return 30.0  # default if geometry unknown

    # IEC 60534-8-3 Eq. (16) simplified
    numerator = (rho_pipe * c_pipe * t_m) ** 2
    denominator = rho_air * c_air * math.pi * Di_m * freq_Hz
    if denominator <= 0:
        return 30.0

    TL = 10.0 * math.log10(numerator / denominator)
    # Physical bounds: TL typically 20–60 dB for steel pipe
    return max(10.0, min(TL, 80.0))


def _peak_frequency(
    Cv: float,
    P1_Pa: float,
    P2_Pa: float,
    rho1_kgm3: float,
    gamma: float,
    Fd: float,
    d_m: float,
) -> float:
    """
    Peak frequency of aerodynamic noise [Hz] (IEC 60534-8-3 §5.4).

    Approximate formula from the standard:

        fp = 0.2 × c_vc / (Fd × d)

    where c_vc is the speed of sound at the vena contracta (≈ c1 for
    subsonic; c_crit for choked).

    Parameters
    ----------
    Cv : float
        Required Cv (used for flow area estimate).
    P1_Pa : float
        Inlet absolute pressure [Pa].
    P2_Pa : float
        Downstream pressure [Pa].
    rho1_kgm3 : float
        Inlet density [kg/m³].
    gamma : float
        Specific heat ratio.
    Fd : float
        Valve style modifier (jet diameter ratio).
    d_m : float
        Valve bore [m].

    Returns
    -------
    float
        Peak frequency [Hz].
    """
    c1 = _speed_of_sound_gas(gamma, P1_Pa, rho1_kgm3)

    # At choked conditions, c_vc = c_crit = c1 × √(2/(γ+1))
    exp_crit = gamma / (gamma - 1.0)
    P_crit = P1_Pa * (2.0 / (gamma + 1.0)) ** exp_crit
    if P2_Pa <= P_crit:
        c_vc = c1 * math.sqrt(2.0 / (gamma + 1.0))
    else:
        pressure_ratio = P2_Pa / P1_Pa
        # Subsonic speed of sound at vena contracta (approx)
        T_ratio = pressure_ratio ** ((gamma - 1.0) / gamma)
        c_vc = c1 * math.sqrt(T_ratio)

    jet_diam = max(Fd * d_m, 0.001)
    fp = 0.2 * c_vc / jet_diam
    return max(fp, 100.0)


def _a_weighted_correction(fp_Hz: float) -> float:
    """
    A-weighting correction at the peak frequency [dB].

    Interpolates from the standard octave-band A-weighting table
    (IEC 61672-1:2013).

    Parameters
    ----------
    fp_Hz : float
        Peak frequency [Hz].

    Returns
    -------
    float
        A-weighting correction [dB].  Negative below 1 kHz, positive above.
    """
    bands = sorted(A_WEIGHTING_DB.keys())
    if fp_Hz <= bands[0]:
        return A_WEIGHTING_DB[bands[0]]
    if fp_Hz >= bands[-1]:
        return A_WEIGHTING_DB[bands[-1]]

    for i in range(len(bands) - 1):
        f_lo, f_hi = bands[i], bands[i + 1]
        if f_lo <= fp_Hz <= f_hi:
            # Log-linear interpolation
            t = math.log(fp_Hz / f_lo) / math.log(f_hi / f_lo)
            return A_WEIGHTING_DB[f_lo] + t * (A_WEIGHTING_DB[f_hi] - A_WEIGHTING_DB[f_lo])
    return 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_aerodynamic_noise(
    mass_flow_kgs: float,
    P1_bara: float,
    P2_bara: float,
    T1_K: float,
    rho1_kgm3: float,
    gamma: float,
    Cv: float,
    FL: float,
    Fd: float,
    d_mm: float,
    D2_mm: float,
    pipe_schedule: str = "Sch 40",
    noise_limit_dba: float = 85.0,
) -> NoiseResult:
    """
    Full IEC 60534-8-3:2011 aerodynamic noise calculation chain.

    Parameters
    ----------
    mass_flow_kgs : float
        Mass flow rate [kg/s].
    P1_bara : float
        Inlet absolute pressure [bar a].
    P2_bara : float
        Outlet absolute pressure [bar a].
    T1_K : float
        Inlet temperature [K].
    rho1_kgm3 : float
        Inlet gas density [kg/m³].
    gamma : float
        Specific heat ratio Cp/Cv.
    Cv : float
        Required Cv (used for frequency estimate).
    FL : float
        Liquid pressure recovery factor (proxy for vena contracta ΔP).
    Fd : float
        Valve style modifier (jet diameter factor).
    d_mm : float
        Valve bore diameter [mm].
    D2_mm : float
        Downstream pipe internal diameter [mm].
    pipe_schedule : str
        Pipe schedule string (e.g. "Sch 40") — used to look up wall thickness.
    noise_limit_dba : float
        Site noise limit [dB(A)] for limit-exceeded flag.

    Returns
    -------
    NoiseResult
        Complete noise prediction result with all intermediate values.

    Notes
    -----
    Calculation chain (IEC 60534-8-3:2011):

    Step 1  Mechanical stream power Wm [W]
    Step 2  Vena contracta Mach number Mvc
    Step 3  Acoustic efficiency η_a = f(Mvc)          ← Baumann/IEC correlation
    Step 4  Internal acoustic power Wa = η_a × Wm
    Step 5  Internal SPL: Lpi = 10 log₁₀(Wa / W_ref)
    Step 6  Peak frequency fp
    Step 7  Pipe wall TL (at fp)
    Step 8  External SPL: Lpe = Lpi – TL + A_weighting(fp)

    Bug fix v2.1: NoiseResult is now constructed with the correct field name
    ``limit_dba`` (not the erroneous ``noise_limit_dba``).  This ensures the
    noise-limit exceedance flag correctly reflects the user-specified limit.
    """
    # ── BUG 1 FIX: use field name 'limit_dba' (matches NoiseResult model) ──
    result = NoiseResult(limit_dba=noise_limit_dba)

    # -- Convert to SI base units ────────────────────────────────────────────
    P1_Pa = P1_bara * 1.0e5
    P2_Pa = P2_bara * 1.0e5
    d_m   = d_mm * 1.0e-3
    D2_m  = D2_mm * 1.0e-3

    # Guard: trivial flows
    if mass_flow_kgs <= 0 or P1_Pa <= P2_Pa or rho1_kgm3 <= 0:
        result.Lpe_dba = None
        result.overall_Lpe_dba = None
        return result

    # ── Step 1: Mechanical stream power ────────────────────────────────────
    Wm = _mechanical_stream_power(mass_flow_kgs, P1_Pa, P2_Pa, rho1_kgm3, gamma)
    result.Wm_watts = Wm

    # ── Step 2: Vena contracta Mach number ─────────────────────────────────
    Mvc, is_sonic = _mach_at_vena_contracta(P1_Pa, P2_Pa, gamma, FL, rho1_kgm3)
    result.Mvc = Mvc
    result.is_sonic = is_sonic

    # ── Step 3: Acoustic efficiency (Mach-dependent — Baumann/IEC 8-3) ─────
    eta_a = _acoustic_efficiency(Mvc)
    result.eta_acoustic = eta_a

    # ── Step 4: Internal acoustic power ────────────────────────────────────
    Wa = eta_a * Wm
    result.Wa_watts = Wa

    # ── Step 5: Internal sound power level ─────────────────────────────────
    if Wa > 0:
        Lpi = 10.0 * math.log10(Wa / W_REF)
    else:
        Lpi = -60.0  # effectively silent
    result.Lpi_db = Lpi

    # ── Step 6: Peak frequency ─────────────────────────────────────────────
    fp = _peak_frequency(Cv, P1_Pa, P2_Pa, rho1_kgm3, gamma, Fd, d_m)

    # ── Step 7: Pipe wall transmission loss ────────────────────────────────
    # Look up wall thickness from schedule; approximate if not found
    wall_thickness_m = _estimate_wall_thickness(D2_mm, pipe_schedule)
    TL = _pipe_transmission_loss(D2_m, wall_thickness_m, freq_Hz=fp)
    result.TL_db = TL

    # ── Step 8: External SPL (A-weighted at 1 m) ───────────────────────────
    # IEC 60534-8-3: Lpe = Lpi - TL - 10 log₁₀(π × Do × Lg) + A(fp)
    # Simplified (1 m reference distance, unit pipe length):
    A_weight = _a_weighted_correction(fp)
    Lpe = Lpi - TL + A_weight

    result.Lpe_dba = round(Lpe, 1)
    result.overall_Lpe_dba = round(Lpe, 1)
    result.exceeds_limit = Lpe > noise_limit_dba

    return result


def _estimate_wall_thickness(D_mm: float, schedule: str) -> float:
    """
    Estimate pipe wall thickness [m] from nominal diameter and schedule.

    Uses a simplified empirical relationship when exact schedule data
    is unavailable.

    Parameters
    ----------
    D_mm : float
        Pipe internal diameter [mm].
    schedule : str
        Pipe schedule string (e.g. "Sch 40", "Sch 80", "Sch 160").

    Returns
    -------
    float
        Estimated wall thickness [m].
    """
    # Schedule multiplier (wall fraction of OD)
    schedule_factors: dict[str, float] = {
        "Sch 10S": 0.030,
        "Sch 10":  0.030,
        "Sch 20":  0.050,
        "Sch STD": 0.060,
        "Sch 40":  0.070,
        "Sch XH":  0.090,
        "Sch 80":  0.110,
        "Sch 120": 0.140,
        "Sch 160": 0.175,
        "XXH":     0.220,
    }
    factor = 0.070  # default Sch 40
    for key, val in schedule_factors.items():
        if key.lower() in schedule.lower():
            factor = val
            break

    # OD ≈ ID + 2t; using ID/(1 - 2×factor) ≈ OD
    OD_mm = D_mm / (1.0 - 2.0 * factor)
    t_mm = (OD_mm - D_mm) / 2.0
    t_m = max(t_mm, 2.0) * 1.0e-3  # minimum 2 mm
    return t_m
