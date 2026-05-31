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
#              N7_bar = N7_kPa × 100  (P1 enters linearly in N7 equation)
#              N8_bar = N8_kPa × 100  (P1 enters linearly in N8 equation)
#              N9_bar = N9_kPa × 100  (P1 enters linearly in N9 equation)
# ---------------------------------------------------------------------------

# N-factors for LIQUID sizing  (Q in m³/h, W in kg/h)
N1_SI: float = 0.865    # Q [m³/h], ΔP [bar],  Cv  — IEC 60534-2-1 Table 1 (bar row)
N1_US: float = 1.00     # Q [GPM],  ΔP [psia]

N2_SI: float = 0.00214  # Fp piping correction  (d in mm)
N2_US: float = 890.0    # Fp piping correction  (d in inches)

N4_SI: float = 334620.0 # Reynolds number  (Q in m³/h, ν in cSt)
#   = N4_US × M3H_TO_GPM = 76 000 × 4.4029
#   The IEC table value 0.0713 is for a different formula structure (involves
#   d² explicitly).  For the simplified form used here —
#       Rev = N4 / Fd × Q / (ν × √(FL × Cv))
#   — the correct SI coefficient is N4_US × (m³/h per GPM) = 334 620.
#   Proof: N4=0.0713 gives Rev=1.72 for water at 100 m³/h through a 100 mm
#   valve → FR=0.05 → Cv inflated 20×.  N4=334 620 gives Rev=8 000 000 → FR=1.0 ✓
N4_US: float = 76000.0  # Reynolds number  (Q in GPM,  ν in cSt)

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

T_STD_K: float  = 288.15     # Standard temperature 15 °C [K]  (ISO 13443)
T_STD_NM3H_K: float = 273.15 # Standard temperature  0 °C [K]  (ISO Nm³/h reference)
T_STD_SCFH_K: float = 288.71 # Standard temperature 60 °F [K]  (SCFH / ISA reference)
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
KV_PER_CV: float = 0.8646    # Kv = Cv × 0.8646  (or Kv = Cv / 1.1561)

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
#
# Schedule designations
# ---------------------
# Sch 10S : Thin-wall schedule (ASME B36.19M / B36.10M)
# Sch STD : Standard weight — 0.375" (9.525 mm) wall for NPS ≥ 12";
#            equals Sch 40 for NPS ≤ 10"
# Sch XH  : Extra Heavy    — 0.500" (12.700 mm) wall for NPS ≥ 12";
#            equals Sch 80 for NPS ≤ 8"
# Sch 40  : Equals Sch STD for NPS ≤ 16"; heavier than STD for NPS ≥ 18"
# Sch 80  : Heavier than Sch XH for NPS ≥ 14"
# Sch 160 : Heavy-wall schedule for high-pressure service
# ---------------------------------------------------------------------------

PIPE_SCHEDULE: dict[tuple[str, str], dict[str, float]] = {

    # ── NPS 1" (OD = 33.4 mm) ───────────────────────────────────────────────
    ("1",  "Sch 10S"):  {"OD_mm": 33.4,  "ID_mm": 27.9,  "t_mm": 2.77},
    ("1",  "Sch 40"):   {"OD_mm": 33.4,  "ID_mm": 26.6,  "t_mm": 3.38},
    ("1",  "Sch STD"):  {"OD_mm": 33.4,  "ID_mm": 26.6,  "t_mm": 3.38},  # = Sch 40
    ("1",  "Sch 80"):   {"OD_mm": 33.4,  "ID_mm": 24.3,  "t_mm": 4.55},
    ("1",  "Sch XH"):   {"OD_mm": 33.4,  "ID_mm": 24.3,  "t_mm": 4.55},  # = Sch 80
    ("1",  "Sch 160"):  {"OD_mm": 33.4,  "ID_mm": 20.7,  "t_mm": 6.35},

    # ── NPS 1.5" (OD = 48.3 mm) ─────────────────────────────────────────────
    ("1.5","Sch 10S"):  {"OD_mm": 48.3,  "ID_mm": 42.8,  "t_mm": 2.77},
    ("1.5","Sch 40"):   {"OD_mm": 48.3,  "ID_mm": 40.9,  "t_mm": 3.68},
    ("1.5","Sch STD"):  {"OD_mm": 48.3,  "ID_mm": 40.9,  "t_mm": 3.68},  # = Sch 40
    ("1.5","Sch 80"):   {"OD_mm": 48.3,  "ID_mm": 38.1,  "t_mm": 5.08},
    ("1.5","Sch XH"):   {"OD_mm": 48.3,  "ID_mm": 38.1,  "t_mm": 5.08},  # = Sch 80
    ("1.5","Sch 160"):  {"OD_mm": 48.3,  "ID_mm": 33.9,  "t_mm": 7.14},

    # ── NPS 2" (OD = 60.3 mm) ───────────────────────────────────────────────
    ("2",  "Sch 10S"):  {"OD_mm": 60.3,  "ID_mm": 54.2,  "t_mm": 3.05},
    ("2",  "Sch 40"):   {"OD_mm": 60.3,  "ID_mm": 52.5,  "t_mm": 3.91},
    ("2",  "Sch STD"):  {"OD_mm": 60.3,  "ID_mm": 52.5,  "t_mm": 3.91},  # = Sch 40
    ("2",  "Sch 80"):   {"OD_mm": 60.3,  "ID_mm": 49.2,  "t_mm": 5.54},
    ("2",  "Sch XH"):   {"OD_mm": 60.3,  "ID_mm": 49.2,  "t_mm": 5.54},  # = Sch 80
    ("2",  "Sch 160"):  {"OD_mm": 60.3,  "ID_mm": 42.8,  "t_mm": 8.74},

    # ── NPS 3" (OD = 88.9 mm) ───────────────────────────────────────────────
    ("3",  "Sch 10S"):  {"OD_mm": 88.9,  "ID_mm": 82.8,  "t_mm": 3.05},
    ("3",  "Sch 40"):   {"OD_mm": 88.9,  "ID_mm": 77.9,  "t_mm": 5.49},
    ("3",  "Sch STD"):  {"OD_mm": 88.9,  "ID_mm": 77.9,  "t_mm": 5.49},  # = Sch 40
    ("3",  "Sch 80"):   {"OD_mm": 88.9,  "ID_mm": 73.7,  "t_mm": 7.62},
    ("3",  "Sch XH"):   {"OD_mm": 88.9,  "ID_mm": 73.7,  "t_mm": 7.62},  # = Sch 80
    ("3",  "Sch 160"):  {"OD_mm": 88.9,  "ID_mm": 66.6,  "t_mm": 11.13},

    # ── NPS 4" (OD = 114.3 mm) ──────────────────────────────────────────────
    ("4",  "Sch 10S"):  {"OD_mm": 114.3, "ID_mm": 108.2, "t_mm": 3.05},
    ("4",  "Sch 40"):   {"OD_mm": 114.3, "ID_mm": 102.3, "t_mm": 6.02},
    ("4",  "Sch STD"):  {"OD_mm": 114.3, "ID_mm": 102.3, "t_mm": 6.02},  # = Sch 40
    ("4",  "Sch 80"):   {"OD_mm": 114.3, "ID_mm":  97.2, "t_mm": 8.56},
    ("4",  "Sch XH"):   {"OD_mm": 114.3, "ID_mm":  97.2, "t_mm": 8.56},  # = Sch 80
    ("4",  "Sch 160"):  {"OD_mm": 114.3, "ID_mm":  87.3, "t_mm": 13.49},

    # ── NPS 6" (OD = 168.3 mm) ──────────────────────────────────────────────
    ("6",  "Sch 10S"):  {"OD_mm": 168.3, "ID_mm": 161.5, "t_mm": 3.40},
    ("6",  "Sch 40"):   {"OD_mm": 168.3, "ID_mm": 154.1, "t_mm": 7.11},
    ("6",  "Sch STD"):  {"OD_mm": 168.3, "ID_mm": 154.1, "t_mm": 7.11},  # = Sch 40
    ("6",  "Sch 80"):   {"OD_mm": 168.3, "ID_mm": 146.3, "t_mm": 11.00},
    ("6",  "Sch XH"):   {"OD_mm": 168.3, "ID_mm": 146.3, "t_mm": 11.00}, # = Sch 80
    ("6",  "Sch 160"):  {"OD_mm": 168.3, "ID_mm": 131.7, "t_mm": 18.26},

    # ── NPS 8" (OD = 219.1 mm) ──────────────────────────────────────────────
    ("8",  "Sch 10S"):  {"OD_mm": 219.1, "ID_mm": 211.6, "t_mm": 3.76},
    ("8",  "Sch 40"):   {"OD_mm": 219.1, "ID_mm": 202.7, "t_mm": 8.18},
    ("8",  "Sch STD"):  {"OD_mm": 219.1, "ID_mm": 202.7, "t_mm": 8.18},  # = Sch 40
    ("8",  "Sch 80"):   {"OD_mm": 219.1, "ID_mm": 193.7, "t_mm": 12.70},
    ("8",  "Sch XH"):   {"OD_mm": 219.1, "ID_mm": 193.7, "t_mm": 12.70}, # = Sch 80
    ("8",  "Sch 160"):  {"OD_mm": 219.1, "ID_mm": 174.6, "t_mm": 22.23},

    # ── NPS 10" (OD = 273.0 mm) ─────────────────────────────────────────────
    ("10", "Sch 10S"):  {"OD_mm": 273.0, "ID_mm": 264.6, "t_mm": 4.19},
    ("10", "Sch 40"):   {"OD_mm": 273.0, "ID_mm": 254.5, "t_mm": 9.27},
    ("10", "Sch STD"):  {"OD_mm": 273.0, "ID_mm": 254.5, "t_mm": 9.27},  # = Sch 40
    ("10", "Sch 80"):   {"OD_mm": 273.0, "ID_mm": 247.7, "t_mm": 12.70},
    ("10", "Sch XH"):   {"OD_mm": 273.0, "ID_mm": 247.7, "t_mm": 12.70}, # = Sch 80
    ("10", "Sch 160"):  {"OD_mm": 273.0, "ID_mm": 222.3, "t_mm": 25.40},

    # ── NPS 12" (OD = 323.8 mm) ─────────────────────────────────────────────
    ("12", "Sch 10S"):  {"OD_mm": 323.8, "ID_mm": 314.7, "t_mm": 4.57},
    ("12", "Sch 40"):   {"OD_mm": 323.8, "ID_mm": 303.2, "t_mm": 10.31},
    ("12", "Sch STD"):  {"OD_mm": 323.8, "ID_mm": 303.2, "t_mm": 10.31}, # = Sch 40
    ("12", "Sch 80"):   {"OD_mm": 323.8, "ID_mm": 292.1, "t_mm": 14.27},
    ("12", "Sch XH"):   {"OD_mm": 323.8, "ID_mm": 292.1, "t_mm": 14.27}, # = Sch 80
    ("12", "Sch 160"):  {"OD_mm": 323.8, "ID_mm": 257.2, "t_mm": 33.32},

    # ── NPS 14" (OD = 355.6 mm) ─────────────────────────────────────────────
    # For NPS 14": Sch STD = Sch 40 = 0.375" (9.53 mm); Sch XH = 0.500" (12.70 mm)
    ("14", "Sch 10S"):  {"OD_mm": 355.6, "ID_mm": 342.9, "t_mm":  6.35},
    ("14", "Sch STD"):  {"OD_mm": 355.6, "ID_mm": 336.5, "t_mm":  9.53},
    ("14", "Sch 40"):   {"OD_mm": 355.6, "ID_mm": 336.5, "t_mm":  9.53},  # = STD
    ("14", "Sch XH"):   {"OD_mm": 355.6, "ID_mm": 330.2, "t_mm": 12.70},
    ("14", "Sch 80"):   {"OD_mm": 355.6, "ID_mm": 323.8, "t_mm": 15.88},
    ("14", "Sch 120"):  {"OD_mm": 355.6, "ID_mm": 308.0, "t_mm": 23.83},
    ("14", "Sch 160"):  {"OD_mm": 355.6, "ID_mm": 292.1, "t_mm": 31.75},

    # ── NPS 16" (OD = 406.4 mm) ─────────────────────────────────────────────
    # For NPS 16": Sch STD = Sch 40 = 0.375" (9.53 mm); Sch XH = 0.500" (12.70 mm)
    ("16", "Sch 10S"):  {"OD_mm": 406.4, "ID_mm": 393.7, "t_mm":  6.35},
    ("16", "Sch STD"):  {"OD_mm": 406.4, "ID_mm": 387.4, "t_mm":  9.53},
    ("16", "Sch 40"):   {"OD_mm": 406.4, "ID_mm": 387.4, "t_mm":  9.53},  # = STD
    ("16", "Sch XH"):   {"OD_mm": 406.4, "ID_mm": 381.0, "t_mm": 12.70},
    ("16", "Sch 80"):   {"OD_mm": 406.4, "ID_mm": 369.9, "t_mm": 18.26},
    ("16", "Sch 120"):  {"OD_mm": 406.4, "ID_mm": 355.6, "t_mm": 25.40},
    ("16", "Sch 160"):  {"OD_mm": 406.4, "ID_mm": 339.8, "t_mm": 33.32},

    # ── NPS 18" (OD = 457.2 mm) ─────────────────────────────────────────────
    # For NPS 18": Sch STD = 0.375" (9.53 mm); Sch 40 = 0.438" (11.13 mm);
    #              Sch XH = 0.500" (12.70 mm)
    ("18", "Sch 10S"):  {"OD_mm": 457.2, "ID_mm": 444.5, "t_mm":  6.35},
    ("18", "Sch STD"):  {"OD_mm": 457.2, "ID_mm": 438.2, "t_mm":  9.53},
    ("18", "Sch 40"):   {"OD_mm": 457.2, "ID_mm": 435.0, "t_mm": 11.13},
    ("18", "Sch XH"):   {"OD_mm": 457.2, "ID_mm": 431.8, "t_mm": 12.70},
    ("18", "Sch 80"):   {"OD_mm": 457.2, "ID_mm": 419.1, "t_mm": 19.05},
    ("18", "Sch 120"):  {"OD_mm": 457.2, "ID_mm": 401.6, "t_mm": 27.79},
    ("18", "Sch 160"):  {"OD_mm": 457.2, "ID_mm": 385.8, "t_mm": 35.71},

    # ── NPS 20" (OD = 508.0 mm) ─────────────────────────────────────────────
    # For NPS 20": Sch STD = 0.375" (9.53 mm); Sch XH = 0.500" (12.70 mm);
    #              Sch 40 = 0.594" (15.09 mm) — heavier than XH at this size
    ("20", "Sch 10S"):  {"OD_mm": 508.0, "ID_mm": 495.3, "t_mm":  6.35},
    ("20", "Sch STD"):  {"OD_mm": 508.0, "ID_mm": 489.0, "t_mm":  9.53},
    ("20", "Sch XH"):   {"OD_mm": 508.0, "ID_mm": 482.6, "t_mm": 12.70},
    ("20", "Sch 40"):   {"OD_mm": 508.0, "ID_mm": 477.8, "t_mm": 15.09},
    ("20", "Sch 80"):   {"OD_mm": 508.0, "ID_mm": 466.8, "t_mm": 20.62},
    ("20", "Sch 120"):  {"OD_mm": 508.0, "ID_mm": 442.9, "t_mm": 32.54},
    ("20", "Sch 160"):  {"OD_mm": 508.0, "ID_mm": 419.1, "t_mm": 44.45},

    # ── NPS 22" (OD = 558.8 mm) ─────────────────────────────────────────────
    # For NPS 22": Sch STD = Sch 40 = 0.375" (9.53 mm); Sch XH = 0.500" (12.70 mm)
    # Note: fewer schedule designations are standardised for 22"
    ("22", "Sch 10S"):  {"OD_mm": 558.8, "ID_mm": 546.1, "t_mm":  6.35},
    ("22", "Sch STD"):  {"OD_mm": 558.8, "ID_mm": 539.7, "t_mm":  9.53},
    ("22", "Sch 40"):   {"OD_mm": 558.8, "ID_mm": 539.7, "t_mm":  9.53},  # = STD
    ("22", "Sch XH"):   {"OD_mm": 558.8, "ID_mm": 533.4, "t_mm": 12.70},
    ("22", "Sch 80"):   {"OD_mm": 558.8, "ID_mm": 514.4, "t_mm": 22.23},
    ("22", "Sch 160"):  {"OD_mm": 558.8, "ID_mm": 488.9, "t_mm": 34.93},

    # ── NPS 24" (OD = 609.6 mm) ─────────────────────────────────────────────
    # For NPS 24": Sch STD = 0.375" (9.53 mm); Sch XH = 0.500" (12.70 mm);
    #              Sch 40 = 0.688" (17.48 mm) — heavier than XH at this size
    ("24", "Sch 10S"):  {"OD_mm": 609.6, "ID_mm": 596.9, "t_mm":  6.35},
    ("24", "Sch STD"):  {"OD_mm": 609.6, "ID_mm": 590.5, "t_mm":  9.53},
    ("24", "Sch XH"):   {"OD_mm": 609.6, "ID_mm": 584.2, "t_mm": 12.70},
    ("24", "Sch 40"):   {"OD_mm": 609.6, "ID_mm": 574.6, "t_mm": 17.48},
    ("24", "Sch 80"):   {"OD_mm": 609.6, "ID_mm": 560.4, "t_mm": 24.61},
    ("24", "Sch 120"):  {"OD_mm": 609.6, "ID_mm": 531.8, "t_mm": 38.89},
    ("24", "Sch 160"):  {"OD_mm": 609.6, "ID_mm": 517.6, "t_mm": 46.02},
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
# ANSI/FCI 70-2 / IEC 60534-4 Seat Leakage Classes
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
        "description": "5×10⁻⁴ ml/min·bar·mm seat dia (metal seat)",
        "max_leakage_pct": 0.001,
        "typical_use": "Metal seats, high shutoff requirement",
    },
    "Class VI":  {
        "description": "Bubble-tight per ANSI/FCI 70-2 Table",
        "max_leakage_pct": 0.0001,
        "typical_use": "Soft seats, safety or isolation service",
    },
}

# ---------------------------------------------------------------------------
# A-weighting correction at octave-band centre frequencies
# Source: IEC 61672-1:2013 Table 1
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
