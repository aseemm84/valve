"""
backend/constants.py
====================
Physical constants, IEC 60534-2-1 N-factors, and reference tables.

All N-factors sourced from IEC 60534-2-1:2011 Table 1 and
ANSI/ISA-75.01.01-2012 Table 1.

Unit conventions
----------------
SI  : bar, m³/h (volumetric), kg/h (mass), mm, °C/K, cSt
US  : psia, GPM (liquid volumetric), lb/h (mass), inches, °F/°R
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# IEC 60534-2-1 N-factors (Table 1)
# ---------------------------------------------------------------------------
# IMPORTANT: Two sets exist — one for pressure in kPa, one for pressure in bar.
# This application stores all pressures in bar a internally, so the bar-based
# N-factors are used throughout the sizing engine.
#
# Cross-check: N1_bar = N1_kPa × √100 = N1_kPa × 10
#              N6_bar = N6_kPa × √100 = N6_kPa × 10
# ---------------------------------------------------------------------------

# N-factors for LIQUID sizing  (Q in m³/h, W in kg/h)
N1_SI: float = 0.865    # Q [m³/h], ΔP [bar],  Cv  — IEC 60534-2-1 Table 1 (bar row)
N1_US: float = 1.00     # Q [GPM],  ΔP [psia]

N2_SI: float = 0.00214  # Fp piping correction  (d in mm)
N2_US: float = 890.0    # Fp piping correction  (d in inches)

N4_SI: float = 0.0713   # Reynolds number  (Q in m³/h, ν in cSt, d in mm)
N4_US: float = 76000.0  # Reynolds number  (Q in GPM,  ν in cSt, d in inches)

N5_SI: float = 0.00241  # Fp piping correction — pipe diameter term (d in mm)
N5_US: float = 1000.0   # Fp piping correction — pipe diameter term (d in in)

# N-factors for GAS / VAPOUR sizing  (W in kg/h, Q in m³/h)
N6_SI: float = 27.3     # mass flow W [kg/h],  P1 [bar a], rho1 [kg/m³]
N6_US: float = 63.3     # mass flow W [lb/h],  P1 [psia],  rho1 [lb/ft³]

N7_SI: float = 417.0    # volumetric Q [m³/h at std], P1 [bar a]
N7_US: float = 1360.0   # volumetric Q [SCFH],        P1 [psia]

N8_SI: float = 94.8     # mass W [kg/h], P1 [bar a], T1 [K], M [g/mol]
N8_US: float = 19.3     # mass W [lb/h], P1 [psia],  T1 [°R]

N9_SI: float = 2120.0   # standard volumetric Q [m³/h], P1 [bar a], T1 [K]
N9_US: float = 7320.0   # standard volumetric Q [SCFH],  P1 [psia],  T1 [°R]

# N-factor for STEAM sizing
N6_STEAM_SI: float = 27.3   # Same N6 applies; density from IAPWS-IF97

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

P_ATM_BAR: float = 1.01325   # Standard atmosphere [bar]
P_ATM_PSI: float = 14.696    # Standard atmosphere [psia]

T_STD_K: float  = 288.15     # Standard temperature 15 °C [K]
T_REF_K: float  = 273.15     # 0 °C in Kelvin

R_UNIVERSAL: float = 8314.46 # Universal gas constant [J/kmol·K]

RHO_WATER: float = 999.0     # Water density at 15.6 °C [kg/m³]

# Speed of sound in air (for noise reference)
C_AIR: float = 343.0         # [m/s] at 20 °C
RHO_AIR: float = 1.2         # [kg/m³] at 20 °C

# Steel pipe properties (for noise transmission loss)
C_STEEL: float = 5000.0      # Speed of sound in steel [m/s]
RHO_STEEL: float = 7800.0    # Steel density [kg/m³]

# Acoustic reference power
W_REF: float = 1.0e-12       # 1 picowatt [W] — acoustic reference power

# Cv / Kv conversion
KV_PER_CV: float = 0.8646    # Kv = Cv × 0.8646  (or Kv = Cv / 1.156)

# ---------------------------------------------------------------------------
# Unit conversion factors
# ---------------------------------------------------------------------------

BAR_TO_PSI: float    = 14.5038
PSI_TO_BAR: float    = 1.0 / BAR_TO_PSI
M3H_TO_GPM: float    = 4.4029
GPM_TO_M3H: float    = 1.0 / M3H_TO_GPM
MM_TO_INCH: float    = 0.03937
INCH_TO_MM: float    = 25.4
KGH_TO_LBH: float    = 2.20462
LBH_TO_KGH: float    = 1.0 / KGH_TO_LBH
CELSIUS_TO_K: float  = 273.15
FAHRENHEIT_OFFSET: float = 459.67   # °F + 459.67 = °R

# ---------------------------------------------------------------------------
# ASME B36.10M Pipe Schedule Data  (ID in mm)
# Key: (NPS_inches, schedule) → {"OD_mm": ..., "ID_mm": ..., "t_mm": ...}
# ---------------------------------------------------------------------------

PIPE_SCHEDULE: dict[tuple[str, str], dict[str, float]] = {
    # NPS 1"
    ("1",  "Sch 40"): {"OD_mm": 33.4,  "ID_mm": 26.6,  "t_mm": 3.38},
    ("1",  "Sch 80"): {"OD_mm": 33.4,  "ID_mm": 24.3,  "t_mm": 4.55},
    ("1",  "Sch 160"):{"OD_mm": 33.4,  "ID_mm": 20.7,  "t_mm": 6.35},
    # NPS 1.5"
    ("1.5","Sch 40"): {"OD_mm": 48.3,  "ID_mm": 40.9,  "t_mm": 3.68},
    ("1.5","Sch 80"): {"OD_mm": 48.3,  "ID_mm": 38.1,  "t_mm": 5.08},
    ("1.5","Sch 160"):{"OD_mm": 48.3,  "ID_mm": 33.9,  "t_mm": 7.14},
    # NPS 2"
    ("2",  "Sch 40"): {"OD_mm": 60.3,  "ID_mm": 52.5,  "t_mm": 3.91},
    ("2",  "Sch 80"): {"OD_mm": 60.3,  "ID_mm": 49.2,  "t_mm": 5.54},
    ("2",  "Sch 160"):{"OD_mm": 60.3,  "ID_mm": 42.8,  "t_mm": 8.74},
    # NPS 3"
    ("3",  "Sch 40"): {"OD_mm": 88.9,  "ID_mm": 77.9,  "t_mm": 5.49},
    ("3",  "Sch 80"): {"OD_mm": 88.9,  "ID_mm": 73.7,  "t_mm": 7.62},
    ("3",  "Sch 160"):{"OD_mm": 88.9,  "ID_mm": 66.6,  "t_mm": 11.13},
    # NPS 4"
    ("4",  "Sch 40"): {"OD_mm": 114.3, "ID_mm": 102.3, "t_mm": 6.02},
    ("4",  "Sch 80"): {"OD_mm": 114.3, "ID_mm": 97.2,  "t_mm": 8.56},
    ("4",  "Sch 160"):{"OD_mm": 114.3, "ID_mm": 87.3,  "t_mm": 13.49},
    # NPS 6"
    ("6",  "Sch 40"): {"OD_mm": 168.3, "ID_mm": 154.1, "t_mm": 7.11},
    ("6",  "Sch 80"): {"OD_mm": 168.3, "ID_mm": 146.3, "t_mm": 11.0},
    ("6",  "Sch 160"):{"OD_mm": 168.3, "ID_mm": 131.7, "t_mm": 18.26},
    # NPS 8"
    ("8",  "Sch 40"): {"OD_mm": 219.1, "ID_mm": 202.7, "t_mm": 8.18},
    ("8",  "Sch 80"): {"OD_mm": 219.1, "ID_mm": 193.7, "t_mm": 12.7},
    ("8",  "Sch 160"):{"OD_mm": 219.1, "ID_mm": 174.6, "t_mm": 22.23},
    # NPS 10"
    ("10", "Sch 40"): {"OD_mm": 273.0, "ID_mm": 254.5, "t_mm": 9.27},
    ("10", "Sch 80"): {"OD_mm": 273.0, "ID_mm": 247.7, "t_mm": 12.7},
    ("10", "Sch 160"):{"OD_mm": 273.0, "ID_mm": 222.3, "t_mm": 25.4},
    # NPS 12"
    ("12", "Sch 40"): {"OD_mm": 323.8, "ID_mm": 303.2, "t_mm": 10.31},
    ("12", "Sch 80"): {"OD_mm": 323.8, "ID_mm": 292.1, "t_mm": 14.27},
    ("12", "Sch 160"):{"OD_mm": 323.8, "ID_mm": 257.2, "t_mm": 33.32},
}

# ---------------------------------------------------------------------------
# Valve type preset data (FL, xT, Fd, Cv_max_per_d2, R_inherent)
# Sources: ISA-75.01.01-2012 and typical manufacturer data
# ---------------------------------------------------------------------------

VALVE_PRESETS: dict[str, dict[str, float]] = {
    "Globe Single-Seat": {
        "FL": 0.90, "xT": 0.72, "Fd": 1.00,
        "Cv_d2": 11.5,      # Cv per (d in mm)^2 × 10^-3 — rough sizing
        "R_inherent": 50.0, # Rangeability at rated conditions
        "seat_diam_ratio": 0.95,  # seat diameter / bore ratio
    },
    "Globe Double-Seat": {
        "FL": 0.85, "xT": 0.70, "Fd": 0.90,
        "Cv_d2": 12.0, "R_inherent": 50.0, "seat_diam_ratio": 0.95,
    },
    "Globe Cage-Guided": {
        "FL": 0.90, "xT": 0.75, "Fd": 0.90,
        "Cv_d2": 11.0, "R_inherent": 50.0, "seat_diam_ratio": 0.95,
    },
    "Angle Valve": {
        "FL": 0.90, "xT": 0.72, "Fd": 1.00,
        "Cv_d2": 12.0, "R_inherent": 50.0, "seat_diam_ratio": 0.95,
    },
    "Ball Valve (Full Bore)": {
        "FL": 0.60, "xT": 0.25, "Fd": 0.98,
        "Cv_d2": 30.0, "R_inherent": 30.0, "seat_diam_ratio": 1.00,
    },
    "Ball Valve (Reduced Bore)": {
        "FL": 0.75, "xT": 0.40, "Fd": 0.90,
        "Cv_d2": 20.0, "R_inherent": 30.0, "seat_diam_ratio": 0.80,
    },
    "Butterfly (High Performance)": {
        "FL": 0.55, "xT": 0.35, "Fd": 0.57,
        "Cv_d2": 25.0, "R_inherent": 30.0, "seat_diam_ratio": 1.00,
    },
    "Butterfly (Wafer)": {
        "FL": 0.50, "xT": 0.30, "Fd": 0.57,
        "Cv_d2": 30.0, "R_inherent": 30.0, "seat_diam_ratio": 1.00,
    },
    "Eccentric Rotary Plug": {
        "FL": 0.85, "xT": 0.60, "Fd": 0.42,
        "Cv_d2": 18.0, "R_inherent": 50.0, "seat_diam_ratio": 0.90,
    },
    "3-Way Globe": {
        "FL": 0.90, "xT": 0.72, "Fd": 1.00,
        "Cv_d2": 10.0, "R_inherent": 50.0, "seat_diam_ratio": 0.95,
    },
}

# ---------------------------------------------------------------------------
# Packing friction coefficients (approximate, for actuator guidance)
# ---------------------------------------------------------------------------

PACKING_FRICTION: dict[str, dict[str, float]] = {
    "PTFE": {
        "coeff": 0.05,     # Force = coeff × π × d_stem × L_packing × P_gland
        "base_N_per_mm": 50.0,   # Approximate N per mm stem diameter
    },
    "Graphite": {
        "coeff": 0.12,
        "base_N_per_mm": 120.0,
    },
    "PTFE/Graphite Composite": {
        "coeff": 0.08,
        "base_N_per_mm": 80.0,
    },
    "Live-Loaded PTFE": {
        "coeff": 0.07,
        "base_N_per_mm": 70.0,
    },
}

# ---------------------------------------------------------------------------
# IEC 60534-4 Leakage Classes
# ---------------------------------------------------------------------------

LEAKAGE_CLASSES: dict[str, dict] = {
    "Class I":   {
        "description": "No test required",
        "max_leakage_pct": None,
        "typical_use": "On-off service, tight shutoff not required",
    },
    "Class II":  {
        "description": "0.5% of rated Cv",
        "max_leakage_pct": 0.5,
        "typical_use": "Standard control service",
    },
    "Class III": {
        "description": "0.1% of rated Cv",
        "max_leakage_pct": 0.1,
        "typical_use": "Improved control / tight shutoff",
    },
    "Class IV":  {
        "description": "0.01% of rated Cv",
        "max_leakage_pct": 0.01,
        "typical_use": "Soft-seat valves, stringent shutoff",
    },
    "Class V":   {
        "description": "5×10⁻⁴ ml/min·bar·mm seat dia",
        "max_leakage_pct": 0.001,
        "typical_use": "Metal seats, high shutoff requirement",
    },
    "Class VI":  {
        "description": "Bubble-tight per table",
        "max_leakage_pct": 0.0001,
        "typical_use": "Soft seats, safety or isolation service",
    },
}

# ---------------------------------------------------------------------------
# A-weighting correction at octave-band centre frequencies (IEC 60534-8-3)
# ---------------------------------------------------------------------------

A_WEIGHTING_DB: dict[int, float] = {
    63:    -26.2,
    125:   -16.1,
    250:    -8.6,
    500:    -3.2,
    1000:   0.0,
    2000:   1.2,
    4000:   1.0,
    8000:  -1.1,
    16000: -6.6,
}
