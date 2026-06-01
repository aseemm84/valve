# Control Valve Engineering Handbook

## A Complete Technical Reference for Sizing, Selection, and Analysis

**Based on IEC 60534-2-1:2011 · ANSI/ISA-75.01.01-2012 · IEC 60534-8-3:2011 · IEC 60534-8-4:2015 · IEC 60534-4:2006 · IAPWS-IF97 · API RP 553**

*Companion reference for the Control Valve Sizer v2.0 application*

---

> **How to use this handbook**
> Each chapter builds on the previous one. A reader new to valve sizing should work sequentially from Chapter 1 through Chapter 12. Practising engineers can use the detailed table of contents to jump directly to a topic. Every major equation is numbered, cross-referenced to its source standard, and linked to the app feature that implements it.

---

## Table of Contents

1. [Fundamentals of Control Valves](#1-fundamentals-of-control-valves)
2. [Fluid Mechanics Foundations](#2-fluid-mechanics-foundations)
3. [The Flow Coefficient Cv and Kv](#3-the-flow-coefficient-cv-and-kv)
4. [IEC 60534-2-1 N-Factor System](#4-iec-60534-2-1-n-factor-system)
5. [Liquid Service Sizing](#5-liquid-service-sizing)
6. [Gas and Vapour Service Sizing](#6-gas-and-vapour-service-sizing)
7. [Steam Service Sizing](#7-steam-service-sizing)
8. [Piping Geometry Corrections](#8-piping-geometry-corrections)
9. [Cavitation and Flashing](#9-cavitation-and-flashing)
10. [Noise Prediction](#10-noise-prediction)
11. [Valve Flow Characteristics](#11-valve-flow-characteristics)
12. [Rangeability and Turndown](#12-rangeability-and-turndown)
13. [Valve Body and Trim Selection](#13-valve-body-and-trim-selection)
14. [Actuator Sizing](#14-actuator-sizing)
15. [Sensitivity Analysis](#15-sensitivity-analysis)
16. [Case Studies](#16-case-studies)
17. [Standards Reference](#17-standards-reference)
18. [Glossary](#18-glossary)

---

## 1. Fundamentals of Control Valves

### 1.1 Purpose and Role in Process Control

A **control valve** is a power-operated device that modulates the flow of a fluid to control a process variable — most commonly pressure, temperature, level, or flow rate. It is the final control element in a control loop, receiving a signal from a controller (typically 4–20 mA or digital) and converting it to a mechanical position that restricts or permits fluid flow.

The control valve is distinguished from a block valve or on/off valve by its ability to take a continuously variable position between fully open and fully closed. This modulating capability, combined with characterised trim, allows precise regulation of flow coefficients across a wide operating range.

```
Process Variable ──► Transmitter ──► Controller ──► I/P Converter ──► Positioner ──► Actuator ──► Valve
        ▲                                                                                           │
        └───────────────────────────── Process ◄────────────────────────────────────────────────────┘
```

### 1.2 Control Valve Anatomy

A control valve assembly consists of the following primary components:

**Body** — The pressure-retaining shell through which fluid passes. Rated to ASME B16.34 pressure-temperature classes. Common materials: carbon steel (ASTM A216 WCB), stainless steel (CF8M), and alloy steels for high-temperature or corrosive service.

**Trim** — The internal wetted components that actually control flow: the plug (or ball/disc), seat ring, stem, and cage. The trim geometry defines the flow characteristic and determines FL, xT, and Fd.

**Packing** — The stem seal that prevents process fluid from escaping along the stem. Materials: PTFE (low friction, moderate temperature), graphite (high temperature, fugitive emission control), live-loaded composites (stringent emission standards, LDAR compliance).

**Bonnet** — The pressure boundary that connects the body to the actuator and houses the stem. Extended bonnets are used for cryogenic service (cold box) or high-temperature service (finned for heat dissipation).

**Actuator** — The power device that moves the stem. Types: pneumatic diaphragm (most common, spring-return, simple fail-safe), pneumatic piston (high thrust, adjustable stroke), electric (precise positioning, no instrument air required), electrohydraulic (very high thrust).

**Positioner** — A high-gain controller that compares the demanded position signal to the actual stem position and drives the actuator to reduce the error. Modern digital positioners (DVC, HART, FOUNDATION Fieldbus, PROFIBUS) also provide diagnostics, partial stroke testing, and asset management data.

### 1.3 Valve Body Styles — Overview

| Body Style | Typical FL | Typical xT | Best Application |
|---|---|---|---|
| Globe, single-seat | 0.90 | 0.72 | General service, tight shutoff |
| Globe, double-seat | 0.85 | 0.70 | Large flow, lower shutoff class |
| Globe, cage-guided | 0.90 | 0.75 | Erosive, noisy, high-cycle |
| Angle valve | 0.90 | 0.72 | Flashing, slurry, high ΔP |
| Ball, full bore | 0.60 | 0.25 | Low ΔP, viscous, slurry |
| Ball, reduced bore | 0.75 | 0.40 | Moderate ΔP, wide rangeability |
| High-performance butterfly | 0.55 | 0.35 | Large bore, moderate ΔP |
| Wafer butterfly | 0.50 | 0.30 | Low ΔP, low cost |
| Eccentric rotary plug | 0.85 | 0.60 | Moderate ΔP, erosive, good shutoff |

*App feature: Valve type presets auto-populate FL, xT, and Fd in the Input panel.*

### 1.4 International Standards Framework

The control valve engineering community operates under a dual-standard framework:

**IEC 60534 series** (International Electrotechnical Commission) — The global standard used in Europe, Asia-Pacific, and most international projects. The sizing equations are in SI units (bar, m³/h, kg/h, mm).

**ANSI/ISA-75 series** (International Society of Automation) — The North American standard used predominantly in the USA and Canada. Equations use US customary units (psia, GPM, lb/h, inches). The underlying physics is identical; only the N-factors differ.

The Control Valve Sizer implements both systems. All internal calculations are performed in SI units (bar absolute, m³/h, kg/h, mm, Kelvin), and US customary display is achieved by applying conversion factors at the UI layer.

---

## 2. Fluid Mechanics Foundations

### 2.1 Bernoulli's Equation and Pressure-Flow Relationship

The flow through a control valve is governed by conservation of energy (Bernoulli's principle) modified for real fluid behaviour. For an incompressible, frictionless fluid flowing between two points:

$$P_1 + \frac{1}{2}\rho v_1^2 + \rho g z_1 = P_2 + \frac{1}{2}\rho v_2^2 + \rho g z_2 \quad \text{(Eq. 2.1)}$$

For control valve applications, elevation differences are typically negligible, and the equation reduces to:

$$Q \propto \sqrt{\frac{\Delta P}{\rho}} \quad \text{(Eq. 2.2)}$$

This square-root relationship between flow and pressure drop is the physical basis for the Cv equation.

### 2.2 The Vena Contracta

When a fluid flows through a restriction (the valve trim), it accelerates into the narrow passage and continues to accelerate beyond it — reaching minimum pressure and maximum velocity at a point called the **vena contracta** (Latin: "contracted vein"), located slightly downstream of the mechanical restriction.

```
Flow direction →

   ┌────────────────────────────────────────┐
   │     ●●●●●●●●                           │
 ══╡   ●         ●   Vena Contracta         ╞══
   │  ●    VC     ●──────────────→           │
 ══╡   ●         ●   P_min, V_max           ╞══
   │     ●●●●●●●●                           │
   └────────────────────────────────────────┘
   P1 (high)     P_vc (lowest)    P2 (recovery)
```

The vena contracta is critical because:
1. If P_vc drops below the fluid vapour pressure (Pv), bubbles form — this is the onset of cavitation
2. If P_vc drops below Pv and P2 also remains below Pv, flashing occurs (vapour does not collapse)
3. The ratio of P_vc to P1 determines the liquid pressure recovery factor FL

### 2.3 Liquid Pressure Recovery Factor FL

The liquid pressure recovery factor FL (also written as Fl or FL) characterises how much of the kinetic energy at the vena contracta is recovered as static pressure downstream of the valve. It is defined as:

$$F_L = \sqrt{\frac{P_1 - P_2}{P_1 - P_{vc}}} \quad \text{(Eq. 2.3)}$$

Rearranging:

$$P_{vc} = P_1 - \frac{P_1 - P_2}{F_L^2} \quad \text{(Eq. 2.4)}$$

**Physical meaning of FL:**
- High FL (0.85–0.95): Globe valves —  low pressure recovery; the vena contracta pressure is close to the outlet pressure. Cavitation occurs at high $\Delta P$. The pressure does not bounce back much; $P_2$ stays very close to $P_{vc}$. Because the overall pressure drop is almost as large as the vena contracta drop, the ratio results in a high $F_L$ (closer to 1.0). Tortuous-path valves like globe valves fall into this category. 
- Low FL (0.50–0.65): Ball and butterfly valves — good pressure recovery; the vena contracta pressure is much lower than the outlet pressure. Cavitation can occur at moderate $\Delta P$. Because $P_2$ recovers to a level relatively close to $P_1$, the overall pressure drop ($P_1 - P_2$) is small compared to the deep pressure drop at the vena contracta ($P_1 - P_{vc}$). This ratio results in a low $F_L$. Streamlined valves like ball and butterfly valves fall into this category.

FL is determined experimentally by the valve manufacturer per IEC 60534-2-3 (flow laboratory testing) and is a function of valve type, trim style, and opening position. The values at rated (full open) conditions are tabulated in the app's valve presets.

### 2.4 Pressure Drop Ratio Factor xT

For gas and vapour service, the equivalent of FL is the **pressure drop ratio factor xT**, which characterises the pressure drop ratio at which choked (sonic) flow occurs in the valve without upstream/downstream piping:

$$x_T = \left(\frac{\Delta P}{P_1}\right)_{\text{choked}} \quad \text{(Eq. 2.5)}$$

Like FL, xT is measured in a laboratory test (IEC 60534-2-3) and is specific to the valve style and trim. Valves with poor pressure recovery (globe) have high xT (0.65–0.80); valves with good pressure recovery (butterfly, ball) have low xT (0.25–0.40).

### 2.5 Valve Style Modifier Fd

The valve style modifier Fd is used in the Reynolds number calculation for viscous flow correction and in the aerodynamic noise prediction (IEC 60534-8-3). It represents the ratio of the hydraulic diameter of a single flow passage to the total valve bore diameter, and is related to the number and geometry of flow paths:

$$F_d = \frac{d_j}{d} \quad \text{(Eq. 2.6)}$$

where $d_j$ is the equivalent jet diameter and $d$ is the valve bore. For a single-seated globe valve with a single circular orifice, Fd ≈ 1.0. For a multi-hole cage with many small holes, Fd < 1.0.

### 2.6 Reynolds Number in Valve Flow

For Newtonian fluids, the dimensionless **valve Reynolds number** Rev determines whether flow through the valve is turbulent (FR = 1.0, standard sizing applies) or in the viscous/laminar transition (FR < 1.0, Cv must be increased):

$$Re_v = \frac{N_4 \cdot F_d \cdot Q}{\nu \cdot \sqrt{F_L \cdot C_v}} \quad \text{(Eq. 2.7, IEC 60534-2-1 Eq. 29)}$$

where:
- N4 = 334 620 (SI: Q in m³/h, ν in cSt) or 76 000 (US: Q in GPM)
- Fd = valve style modifier
- Q = volumetric flow [m³/h or GPM]
- ν = kinematic viscosity [cSt = mm²/s]
- FL = liquid pressure recovery factor
- Cv = required flow coefficient

For Rev > 40 000: fully turbulent, FR = 1.0.
For Rev < 10 000: viscous correction significant.

---

## 3. The Flow Coefficient Cv and Kv

### 3.1 Definition of Cv

The **flow coefficient Cv** is the defining sizing parameter for a control valve. It is defined as:

> The flow in US gallons per minute of water at 60°F (15.6°C) that will pass through the valve at a pressure differential of 1 psia.

This empirical definition avoids the need to model the complex internal geometry of a valve — the entire hydraulic resistance of the body, trim, and seat is captured in a single dimensionless number.

**Mathematically, for liquid service:**

$$C_v = \frac{Q}{\sqrt{\Delta P / G_f}} \quad \text{[US: Q in GPM, ΔP in psia]} \quad \text{(Eq. 3.1)}$$

### 3.2 Definition of Kv

In SI units, the equivalent coefficient is **Kv**, defined as:

> The flow in cubic metres per hour of water at 5–40°C that will pass through the valve at a pressure differential of 1 bar.

$$K_v = \frac{Q}{\sqrt{\Delta P}} \quad \text{[Q in m³/h, ΔP in bar]} \quad \text{(Eq. 3.2)}$$

**Conversion between Cv and Kv:**

$$K_v = C_v \times 0.8646 \quad \text{(Eq. 3.3)}$$
$$C_v = K_v \times 1.1561 \quad \text{(Eq. 3.4)}$$

The app displays both Cv and Kv in all results panels.

### 3.3 Physical Interpretation of Cv

A Cv of 1 means the valve passes 1 GPM of water at 1 psi differential. Larger Cv values mean less restriction. Some physical scale reference points:

| Situation | Approximate Cv |
|---|---|
| 1" globe valve, fully open | 8–15 |
| 2" globe valve, fully open | 30–50 |
| 4" butterfly valve, 60° open | 200–400 |
| 6" ball valve, fully open | 800–1500 |
| 12" butterfly valve, fully open | 4000–8000 |

### 3.4 Sizing Margin

Because process conditions have uncertainty and because operating at exactly 100% of Cv_rated leaves no safety margin, the app applies a **sizing margin** (default 10%) to compute the required installed Cv:

$$C_{v,\text{margin}} = C_{v,\text{required}} \times \left(1 + \frac{\text{margin\%}}{100}\right) \quad \text{(Eq. 3.5)}$$

Per API RP 553, the valve should operate between 20% and 80% of its rated travel at normal conditions, and the Cv at normal conditions should not exceed 85% of the rated Cv:

$$\frac{C_{v,\text{required}}}{C_{v,\text{rated}}} \leq 0.85 \quad \text{(API RP 553)} \quad \text{(Eq. 3.6)}$$

The **sizing ratio** (Cv_required / Cv_rated) is displayed in the app results. A warning is issued when it exceeds 0.85.

### 3.5 Valve Opening Percentage

Given the required Cv and the rated Cv, the approximate valve opening (travel) is estimated by inverting the inherent characteristic equation:

**Equal-percentage characteristic:**
$$\theta = 1 + \frac{\ln(C_{v,\text{req}} / C_{v,\text{rated}})}{\ln R} \quad \text{(Eq. 3.7)}$$

**Linear characteristic:**
$$\theta = \frac{C_{v,\text{req}}}{C_{v,\text{rated}}} \quad \text{(Eq. 3.8)}$$

**Quick-opening characteristic:**
$$\theta = \left(\frac{C_{v,\text{req}}}{C_{v,\text{rated}}}\right)^2 \quad \text{(Eq. 3.9)}$$

where R = 50:1 (standard rangeability per ISA-75.01.01) and θ is expressed as a fraction of full travel (0 to 1).

---

## 4. IEC 60534-2-1 N-Factor System

### 4.1 Purpose of N-Factors

The IEC 60534-2-1 and ANSI/ISA-75.01.01 standards use a set of **numerical constants (N-factors)** that absorb unit conversions, allowing the same general equation forms to be applied with either SI or US customary units by simply substituting the appropriate N value.

### 4.2 Complete N-Factor Table

The following table reproduces the N-factor values as implemented in the app (`constants.py`), showing both the IEC standard bar-pressure row and the US customary row, with derivation notes.

| N-Factor | SI (bar) | US (psia/GPM) | Variables | Derivation note |
|---|---|---|---|---|
| N1 | **0.865** | 1.00 | Q [m³/h or GPM], ΔP [bar or psia] | N1_kPa = 0.0865; N1_bar = 0.0865 × √100 = 0.865 |
| N2 | **0.00214** | 890.0 | d [mm or in], Fp piping | Direct from IEC Table 1 |
| N4 | **334 620** | 76 000 | Rev, Q [m³/h or GPM], ν [cSt] | N4_US × 4.4029 m³/h·GPM⁻¹ = 334 612 |
| N5 | **0.00241** | 1000.0 | d [mm or in], xTP piping | Direct from IEC Table 1 |
| N6 | **27.3** | 63.3 | W [kg/h or lb/h], P1 [bar or psia], ρ1 [kg/m³ or lb/ft³] | N6_kPa = 2.73; N6_bar = 2.73 × 10 = 27.3 |
| N7 | **417.0** | 1360.0 | Q_std [m³/h or SCFH], P1 [bar or psia] | N7_kPa = 4.17; N7_bar = 4.17 × 100 = 417 |
| N8 | **94.8** | 19.3 | W [kg/h or lb/h], P1 [bar or psia], T [K or °R], M [g/mol] | N8_kPa = 0.948; N8_bar = 0.948 × 100 = 94.8 |
| N9 | **2120.0** | 7320.0 | Q_std [m³/h or SCFH], P1 [bar or psia], T [K or °R] | N9_kPa = 21.2; N9_bar = 21.2 × 100 = 2120 |

**Why N7, N8, N9 scale by 100 (not √100)?**
These N-factors appear in equations where P1 enters linearly (not under a square root). Converting from kPa to bar means P1_bar = P1_kPa / 100. To keep the equation balance, N must increase by a factor of 100.

**Why N1, N6 scale by √100 = 10?**
N1 and N6 appear in equations where ΔP or (x × P1) is under a square root. The square root of the pressure unit conversion factor √100 = 10 is absorbed into the N-factor.

**Why N4 = 334 620?**
The IEC Table 1 lists N4 = 0.0713 for a formulation that includes d² explicitly. For the formulation used in the app (Rev = N4 × Fd × Q / (ν × √(FL × Cv))), the equivalent SI coefficient is N4_US × conversion = 76 000 × 4.4029 = 334 612 ≈ 334 620. Using the IEC raw value of 0.0713 in the app's formula would give Rev ≈ 0 for typical conditions, inflating FR correction by 20× — a critical error that is guarded against in the implementation.

### 4.3 Unit Conversion Reference

| Quantity | SI → US | Factor |
|---|---|---|
| Pressure | bar → psia | × 14.5038 |
| Volumetric flow | m³/h → GPM | × 4.4029 |
| Mass flow | kg/h → lb/h | × 2.20462 |
| Diameter | mm → inch | × 0.03937 |
| Temperature | °C → °F | × 9/5 + 32 |
| Temperature | K → °R | × 9/5 |
| Kv → Cv | — | × 1.1561 |
| Cv → Kv | — | × 0.8646 |

### 4.4 Standard Reference Conditions

The app uses two standard reference conditions for gas flow:

- **ISO Nm³/h**: T_std = 273.15 K (0°C), P_std = 1.01325 bar — used for converting standard volumetric gas flows per ISO conventions.
- **SCFH**: T_std = 288.71 K (60°F), P_std = 14.696 psia — used in the US customary system per ISA conventions.

When the user enters flow as "Standard" volumetric (Nm³/h or SCFH), the app converts to mass flow using:

$$W = Q_{\text{std}} \times \rho_{\text{std}} \quad \text{(Eq. 4.1)}$$

where $\rho_{\text{std}}$ is the gas density at the applicable standard conditions.

---

## 5. Liquid Service Sizing

### 5.1 Overview

Liquid sizing is governed by IEC 60534-2-1:2011 §5.2. Three regimes are addressed:
1. **Turbulent non-choked flow** — the standard regime for most liquid applications
2. **Choked flow** — when ΔP exceeds the maximum allowable value, flow is limited by vaporisation at the vena contracta
3. **Viscous/laminar flow** — when the valve Reynolds number is below 10 000, a correction factor FR < 1.0 must be applied

### 5.2 Critical Pressure Ratio Factor FF

Before computing ΔP_max or Cv, the **critical pressure ratio factor FF** must be calculated. FF accounts for the fact that even a perfectly efficient valve cannot suppress all vaporisation — there is always some reduction in available driving pressure due to the presence of vapour:

$$F_F = 0.96 - 0.28 \sqrt{\frac{P_v}{P_c}} \quad \text{(Eq. 5.1, IEC Eq. 4)}$$

where:
- Pv = fluid vapour pressure at inlet temperature [bar a]
- Pc = fluid critical pressure [bar a]
- FF is bounded: 0.70 ≤ FF ≤ 0.96

For water at 20°C: Pv = 0.023 bar, Pc = 220.64 bar → FF = 0.96 − 0.28√(0.023/220.64) = 0.957

For light hydrocarbons near their critical point, FF can drop to 0.70–0.80, significantly reducing the available ΔP for flow.

### 5.3 Maximum Allowable Pressure Drop (Choked Flow Limit)

The maximum ΔP that can be usefully applied across a liquid-service valve (without entering choked flow) is:

$$\Delta P_{\max} = \left(\frac{F_{LP}}{F_p}\right)^2 \left(P_1 - F_F \cdot P_v\right) \quad \text{(Eq. 5.2, IEC Eq. 3)}$$

where:
- FLP = combined piping-corrected liquid pressure recovery factor (see §8)
- Fp = piping geometry factor (see §8)
- P1 = inlet absolute pressure [bar a]
- FF = critical pressure ratio factor (Eq. 5.1)
- Pv = vapour pressure at inlet temperature [bar a]

**When no pipe reducers are present** (Fp = 1.0, FLP = FL):

$$\Delta P_{\max} = F_L^2 \left(P_1 - F_F \cdot P_v\right) \quad \text{(Eq. 5.3)}$$

**Physical meaning:** ΔP_max is the pressure drop at which the vena contracta pressure equals FF × Pv — the threshold for sustained vapour formation. Beyond this ΔP, the flow does not increase further (choked flow condition).

**Choked flow flag:** if ΔP_available ≥ ΔP_max, the flow is choked. In the app, the effective ΔP used for Cv calculation is capped at ΔP_max:

$$\Delta P_{\text{eff}} = \min(\Delta P, \Delta P_{\max}) \quad \text{(Eq. 5.4)}$$

### 5.4 Liquid Cv Equation

The primary liquid Cv sizing equation is (IEC 60534-2-1 Eq. 1):

$$C_v = \frac{Q}{N_1 \cdot F_p \cdot F_R \cdot \sqrt{\Delta P_{\text{eff}} / G_f}} \quad \text{(Eq. 5.5)}$$

where:
- Q = volumetric flow [m³/h (SI) or GPM (US)]
- N1 = 0.865 (SI, bar) or 1.00 (US, psia)
- Fp = piping geometry factor (= 1.0 if no reducers)
- FR = viscosity correction factor (= 1.0 for turbulent flow)
- ΔP_eff = effective pressure drop [bar (SI) or psia (US)]
- Gf = specific gravity relative to water at 15.6°C

**For mass flow input** (W in kg/h), first convert:

$$Q = \frac{W}{\rho_1} \quad \text{[m³/h]} \quad \text{(Eq. 5.6)}$$

where ρ1 = Gf × 999.0 kg/m³ is the liquid density.

**Sizing example (water, no reducers):**
- Q = 100 m³/h, P1 = 10 bar a, P2 = 8 bar a, T = 20°C, Gf = 0.998
- Pv = 0.023 bar, Pc = 220.64 bar
- FF = 0.96 − 0.28√(0.023/220.64) = 0.957
- ΔP_max = 0.90² × (10 − 0.957 × 0.023) = 0.81 × 9.978 = 8.082 bar
- ΔP = 2 bar < ΔP_max → not choked; ΔP_eff = 2 bar
- Cv = 100 / (0.865 × 1.0 × 1.0 × √(2/0.998)) = 100 / (0.865 × 1.414) = **81.7**

### 5.5 Viscosity Correction Factor FR

When the valve Reynolds number Rev is below 40 000, the flow is no longer fully turbulent and the Cv equation overestimates the actual flow. A correction factor FR (0 < FR ≤ 1.0) is applied:

**Valve Reynolds number (IEC 60534-2-1 Eq. 29):**
$$Re_v = \frac{N_4 \cdot F_d \cdot Q}{\nu \cdot \sqrt{F_L \cdot C_v}} \quad \text{(Eq. 5.7)}$$

where ν = kinematic viscosity in cSt (= μ/Gf, with μ in cP).

**FR approximation (IEC Annex D):**

| Reynolds Number | Flow Regime | FR approximation |
|---|---|---|
| Rev ≥ 40 000 | Fully turbulent | FR = 1.0 |
| 10 000 ≤ Rev < 40 000 | Transition | FR = 0.026 ln(Rev) + 0.65 |
| 100 ≤ Rev < 10 000 | Viscous | FR = 1.0 − 0.33 log₁₀(40000/Rev) |
| Rev < 100 | Laminar | FR = 0.019 × Rev^0.667 |

The corrected Cv equation becomes:

$$C_v = \frac{Q}{N_1 \cdot F_p \cdot F_R \cdot \sqrt{\Delta P_{\text{eff}} / G_f}} \quad \text{(Eq. 5.8, same as 5.5)}$$

Note that Rev depends on Cv, making this an **implicit equation** requiring iteration. The standard procedure is:
1. Assume FR = 1.0, compute Cv_turb
2. Compute Rev from Cv_turb (Eq. 5.7)
3. Compute FR from Rev
4. Compute Cv_visc = Cv_turb / FR
5. Recompute Rev from Cv_visc, repeat until convergence

**Practical significance:** For water (ν ≈ 1 cSt) and light hydrocarbons, viscous correction is negligible. For heavy fuel oil (ν = 500–1000 cSt), glycol solutions, or polymer melts, FR can be as low as 0.3, meaning the actual Cv must be 3× the turbulent estimate.

### 5.6 Specific Gravity Correction

Gf corrects for the fluid density relative to water. Since Cv is defined for water (Gf = 1.0):

- **Gf > 1.0** (denser than water, e.g., sulfuric acid Gf = 1.84): A larger Cv is needed to pass the same volumetric flow at the same ΔP. Because Gf is in the denominator of the fraction under the square root in Eq. 5.5 ($\sqrt{\Delta P_{\text{eff}} / G_f}$), it algebraically means $C_v \propto \sqrt{G_f}$. Denser fluids require more energy to accelerate, so for Gf = 1.84, the required Cv increases by a factor of $\sqrt{1.84} \approx 1.35$. (Note: If sizing is based on a fixed mass flow rate instead, the higher density results in a lower volumetric flow Q, which ultimately reduces the overall required Cv.)

- **Gf < 1.0** (lighter than water, e.g., LNG Gf ≈ 0.43): A smaller Cv is needed to pass the same volumetric flow at the same ΔP. The required Cv decreases by a factor of $\sqrt{0.43} \approx 0.66$.

The app's fluid preset library automatically provides the correct Gf for 60+ fluids.

---

## 6. Gas and Vapour Service Sizing

### 6.1 Overview

Gas and vapour sizing is fundamentally different from liquid sizing because:
1. Gases are compressible — density changes with pressure
2. Flow can reach sonic conditions (choked flow) at the vena contracta
3. A gas expansion factor Y must be applied to account for the density change as the gas expands through the valve
4. The relevant limit is expressed as a **pressure drop ratio x** rather than absolute ΔP

The governing equations are from IEC 60534-2-1:2011 §5.3.

### 6.2 Pressure Drop Ratio x and Fk

The **pressure drop ratio** x is defined as:

$$x = \frac{\Delta P}{P_1} = \frac{P_1 - P_2}{P_1} \quad \text{(Eq. 6.1)}$$

The **specific heat ratio factor** Fk normalises the choked flow condition relative to air (γ = 1.4):

$$F_k = \frac{\gamma}{1.4} \quad \text{(Eq. 6.2, IEC Eq. 6)}$$

For air: Fk = 1.0. For diatomic gases (N2, H2, O2): Fk ≈ 1.0. For steam and CO2: Fk < 1.0. For refrigerants: Fk can be as low as 0.85.

### 6.3 Choked Flow Condition (Gas)

Choked (sonic) flow occurs at the vena contracta when x reaches the limiting value:

$$x_{\text{choked}} = F_k \cdot x_{TP} \quad \text{(Eq. 6.3)}$$

where xTP is the pressure drop ratio factor with piping corrections (xT when no reducers are present). The effective pressure drop ratio used in sizing is:

$$x_{\text{eff}} = \min(x, x_{\text{choked}}) \quad \text{(Eq. 6.4)}$$

**Physical interpretation:** Once the pressure ratio at the vena contracta reaches the critical (sonic) value, increasing upstream pressure or decreasing downstream pressure provides no additional flow — the flow is choked. The choked condition corresponds to Mach = 1 at the vena contracta.

### 6.4 Gas Expansion Factor Y

The **expansion factor Y** accounts for the change in gas density as it expands through the valve:

$$Y = 1 - \frac{x_{\text{eff}}}{3 \cdot F_k \cdot x_{TP}} \quad \text{(Eq. 6.5, IEC Eq. 5)}$$

with the constraint:

$$Y \geq \frac{2}{3} \approx 0.667 \quad \text{(Eq. 6.6)}$$

The minimum Y = 2/3 corresponds to fully choked (sonic) flow and is independent of fluid properties. Y = 1.0 represents zero pressure drop (no expansion). For typical control valve applications with x = 0.3–0.5, Y = 0.76–0.90.

### 6.5 Gas Cv Equations

**Mass flow basis** (preferred for accuracy — IEC 60534-2-1 Eq. 9):

$$C_v = \frac{W}{N_6 \cdot F_p \cdot Y \cdot \sqrt{x_{\text{eff}} \cdot P_1 \cdot \rho_1}} \quad \text{(Eq. 6.7)}$$

where:
- W = mass flow [kg/h (SI) or lb/h (US)]
- N6 = 27.3 (SI: bar, kg/h, kg/m³) or 63.3 (US: psia, lb/h, lb/ft³)
- P1 = inlet absolute pressure [bar a or psia]
- ρ1 = inlet gas density [kg/m³ or lb/ft³]

**Volumetric flow at standard conditions** (IEC Eq. 12, Nm³/h basis):

$$C_v = \frac{Q_{\text{std}}}{N_9 \cdot F_p \cdot Y \cdot P_1} \cdot \sqrt{\frac{T_1 \cdot Z}{x_{\text{eff}}}} \quad \text{(Eq. 6.8)}$$

where:
- Q_std = standard volumetric flow [Nm³/h or SCFH]
- N9 = 2120 (SI) or 7320 (US)
- T1 = inlet temperature [K or °R]
- Z = compressibility factor at inlet conditions

**Molecular weight basis** (IEC Eq. 11):

$$C_v = \frac{W}{N_8 \cdot F_p \cdot P_1 \cdot Y} \cdot \sqrt{\frac{T_1 \cdot Z}{x_{\text{eff}} \cdot M}} \quad \text{(Eq. 6.9)}$$

where:
- N8 = 94.8 (SI) or 19.3 (US)
- M = molecular weight [g/mol]

The app uses Eq. 6.7 (mass flow) as the primary gas sizing equation, which requires knowledge of ρ1. For an ideal gas:

$$\rho_1 = \frac{P_1 \times 10^5 \times M}{R_u \times T_1 \times Z} \quad \text{(Eq. 6.10)}$$

where Ru = 8314.46 J/(kmol·K). For real gases, the user can enter a measured density directly or specify Z.

### 6.6 Gas Inlet Density

For an **ideal gas** (Z = 1.0):

$$\rho_1 = \frac{P_1[\text{bar}] \times 10^5 \times M[\text{g/mol}] \times 10^{-3}}{8.31446 \times T_1[\text{K}]} \quad \text{[kg/m}^3\text{]} \quad \text{(Eq. 6.11)}$$

For **real gases**, the compressibility factor Z is applied:

$$\rho_1 = \frac{P_1 \times 10^5 \times M \times 10^{-3}}{8.31446 \times T_1 \times Z} \quad \text{(Eq. 6.12)}$$

Z can be obtained from the Peng-Robinson or Soave-Redlich-Kwong equation of state, from gas chromatography correlations, or from published tables. The app's fluid library provides representative Z values for common gases at near-ambient conditions.

### 6.7 Gas Sizing Example

**Natural gas (M = 18.0 g/mol, γ = 1.27, Z = 0.92) through a globe valve:**
- Flow: W = 5000 kg/h
- P1 = 30 bar a, P2 = 20 bar a, T1 = 60°C = 333.15 K
- Valve: FL = 0.90, xT = 0.72, Fd = 1.0
- Pipe: d = D1 = D2 = 100 mm (no reducers, Fp = 1.0)

**Step 1:** Compute ρ1:
$$\rho_1 = \frac{30 \times 10^5 \times 0.018}{8.31446 \times 333.15 \times 0.92} = \frac{54000}{2554.0} = 21.14 \text{ kg/m}^3$$

**Step 2:** Compute Fk:
$$F_k = \frac{1.27}{1.4} = 0.907$$

**Step 3:** Compute x and check choked:
$$x = \frac{30 - 20}{30} = 0.333$$
$$x_{\text{choked}} = 0.907 \times 0.72 = 0.653$$
$$x_{\text{eff}} = \min(0.333, 0.653) = 0.333 \quad \text{(not choked)}$$

**Step 4:** Compute Y:
$$Y = 1 - \frac{0.333}{3 \times 0.907 \times 0.72} = 1 - \frac{0.333}{1.959} = 0.830$$

**Step 5:** Compute Cv:
$$C_v = \frac{5000}{27.3 \times 1.0 \times 0.830 \times \sqrt{0.333 \times 30 \times 21.14}}$$
$$= \frac{5000}{27.3 \times 0.830 \times \sqrt{211.3}} = \frac{5000}{27.3 \times 0.830 \times 14.54} = \frac{5000}{329.3} = \mathbf{15.2}$$

---

## 7. Steam Service Sizing

### 7.1 Steam as a Compressible Fluid

Steam (whether superheated, saturated, or wet) is sized using the **gas equations** (§6) with thermodynamic properties obtained from the **IAPWS-IF97 international steam tables**, which the app accesses via the `iapws` Python library.

The key steam properties needed for sizing are:
- Density ρ1 [kg/m³] at inlet P1, T1
- Specific heat ratio γ = Cp/Cv at inlet conditions
- Dynamic viscosity μ [mPa·s] (= cP) for Reynolds number
- Steam quality x [0–1] for wet steam assessment

### 7.2 IAPWS-IF97 Property Calculation

The app queries IAPWS-IF97 as follows:

```python
from iapws import IAPWS97
steam = IAPWS97(P=P1_MPa, T=T1_K)
rho1  = 1.0 / steam.v        # density [kg/m³]
gamma = steam.cp / steam.cv  # specific heat ratio
mu    = steam.mu * 1000      # dynamic viscosity [cP]
x     = steam.x              # quality (None for superheated)
```

where P1_MPa = P1_bara × 0.1 (IAPWS-IF97 uses MPa).

### 7.3 Steam Cv Equation

Using the gas mass-flow equation (Eq. 6.7) with IAPWS-derived properties:

$$C_v = \frac{W}{N_6 \cdot F_p \cdot Y \cdot \sqrt{x_{\text{eff}} \cdot P_1 \cdot \rho_{\text{steam}}}} \quad \text{(Eq. 7.1)}$$

This is identical in form to the gas equation; the only difference is that ρ_steam is obtained from steam tables rather than the ideal gas law.

### 7.4 Saturated vs. Superheated Steam

| Condition | T1 relative to T_sat(P1) | Typical γ | Typical ρ1 (10 bar g) |
|---|---|---|---|
| Wet steam | T1 < T_sat | 1.1–1.2 | High (approaching water) |
| Saturated (dry) | T1 = T_sat | 1.13 | ~5 kg/m³ |
| Superheated (low superheat) | T1 = T_sat + 20°C | 1.30 | ~4.5 kg/m³ |
| Superheated (high superheat) | T1 > T_sat + 100°C | 1.35 | ~4.0 kg/m³ |

The app's steam sizing is valid for superheated and dry saturated steam. For wet steam (quality x < 0.95), a warning is issued because the gas equations are approximate — two-phase flow is thermodynamically complex and can cause erosion, water hammer, and measurement errors.

### 7.5 Default Steam γ

When IAPWS-IF97 is unavailable or returns an invalid γ, the app defaults to γ = 1.33 — a conservative mid-range value for superheated steam widely used in preliminary sizing.

### 7.6 Steam Specific Gravity (for reference)

Some older steam sizing methods use a specific gravity concept. For the mass-flow equation, this is unnecessary. For reference, the effective specific gravity of steam relative to air (M = 28.97) is:

$$G_g = \frac{M_{\text{steam}}}{M_{\text{air}}} = \frac{18.015}{28.97} = 0.622 \quad \text{(Eq. 7.2)}$$

This value appears in some older US-customary steam sizing charts but is not used in the app's IEC-based calculation engine.

---

## 8. Piping Geometry Corrections

### 8.1 Why Piping Corrections Are Necessary

In the real world, valves are rarely installed in a pipe of exactly the same bore as the valve body. Reducers (upstream) and expanders (downstream) introduce additional pressure losses and change the effective pressure recovery characteristics of the valve. Ignoring these corrections can lead to Cv under-estimation of 4–12% for typical reduced-bore installations.

The three piping correction factors are:
- **Fp** — Piping geometry factor (affects Cv directly)
- **FLP** — Combined liquid pressure recovery + piping factor (affects choked flow limit)
- **xTP** — Pressure drop ratio factor with piping (affects gas choked flow)

### 8.2 Fitting Loss Coefficients

The inlet and outlet fitting loss coefficients are calculated from the area ratio (IEC 60534-2-1 Annex A):

**Inlet concentric reducer:**
$$K_1 = 0.5 \left(1 - \frac{d^2}{D_1^2}\right)^2 \quad \text{(Eq. 8.1)}$$

**Outlet concentric expander:**
$$K_2 = \left(1 - \frac{d^2}{D_2^2}\right)^2 \quad \text{(Eq. 8.2)}$$

where d = valve bore [mm], D1 = upstream pipe ID [mm], D2 = downstream pipe ID [mm].

These are Borda-Carnot loss coefficients for sudden contraction (K1) and sudden expansion (K2). They represent conservative estimates; for gradual (conical) reducers, actual loss coefficients are lower by a factor of 0.5–0.8.

$$\Sigma K = K_1 + K_2 \quad \text{(Eq. 8.3)}$$

### 8.3 Piping Geometry Factor Fp

Fp corrects the Cv for the additional restriction introduced by the pipe reducers:

$$F_p = \frac{1}{\sqrt{1 + \frac{\Sigma K}{N_2}\left(\frac{C_v}{d^2}\right)^2}} \quad \text{(Eq. 8.4, IEC Eq. 18)}$$

where:
- N2 = 0.00214 (SI: d in mm, Cv dimensionless)
- d = valve bore [mm]
- Cv = required flow coefficient (unknown — requires iteration)

**Iteration procedure (IEC 60534-2-1 Annex C):**
1. Estimate Cv_rough using the sizing equation with Fp = 1.0
2. Compute Fp from Cv_rough using Eq. 8.4
3. Update Cv_iter = Cv_rough / Fp (since Cv ∝ 1/Fp)
4. Recompute Fp from Cv_iter
5. Repeat until |Fp_new − Fp| < 10⁻⁶ (typically 3–5 iterations)

**Fp values for a 4" globe valve (102 mm bore) in various pipe sizes (Cv = 200):**

| Pipe ID (mm) | d/D ratio | ΣK | Fp |
|---|---|---|---|
| 102 (same bore) | 1.00 | 0.000 | 1.000 |
| 154 (6" Sch 40) | 0.662 | 0.474 | 0.962 |
| 202 (8" Sch 40) | 0.505 | 0.769 | 0.939 |
| 255 (10" Sch 40) | 0.400 | 0.895 | 0.928 |

### 8.4 Combined Factor FLP (Liquid Choked Flow)

For liquid service, the piping correction modifies the maximum allowable ΔP through FLP:

$$F_{LP} = \frac{F_L}{\sqrt{1 + \frac{F_L^2 \cdot K_1}{N_2}\left(\frac{C_v}{d^2}\right)^2}} \quad \text{(Eq. 8.5, IEC Eq. 20)}$$

Note: **only K1 (inlet)** is used for FLP, not ΣK. This is because the inlet restriction affects the pressure available at the valve inlet and thus the choked-flow threshold, while the outlet restriction affects pressure recovery but not the onset of vaporisation.

FLP ≤ FL always. When piping reducers are present, FLP < FL, meaning choked flow occurs at a lower ΔP than without reducers.

### 8.5 Pressure Drop Ratio with Piping xTP (Gas Choked Flow)

For gas service, the piping correction modifies the choked flow pressure ratio:

$$x_{TP} = \frac{x_T}{F_p^2 \left[1 + \frac{x_T \cdot K_1}{N_5}\left(\frac{C_v}{d^2}\right)^2\right]} \quad \text{(Eq. 8.6, IEC Eq. 23)}$$

where N5 = 0.00241 (SI, d in mm).

Again, only K1 (inlet) appears. xTP ≤ xT always — piping reducers reduce the pressure ratio at which gas flow becomes choked.

### 8.6 Effect on Cv Calculation

The corrected Cv equations become:

**Liquid (with piping):**
$$C_v = \frac{Q}{N_1 \cdot F_p \cdot F_R \cdot \sqrt{\Delta P_{\text{eff}} / G_f}}$$

where $\Delta P_{\text{eff}} = \min\!\left(\Delta P,\, \left(\frac{F_{LP}}{F_p}\right)^2 (P_1 - F_F P_v)\right)$

**Gas (with piping):**
$$C_v = \frac{W}{N_6 \cdot F_p \cdot Y \cdot \sqrt{x_{\text{eff}} \cdot P_1 \cdot \rho_1}}$$

where $x_{\text{eff}} = \min(x,\; F_k \cdot x_{TP})$

### 8.7 Fp Warning Threshold

The app issues a warning when Fp < 0.95, indicating that piping corrections are significant (>5% effect on Cv) and that the valve-pipe geometry should be verified with the manufacturer.

---

## 9. Cavitation and Flashing

### 9.1 Physical Mechanisms

**Cavitation** and **flashing** are both two-phase phenomena that occur in liquid service when local pressure drops below the vapour pressure. They are related but distinct:

**Cavitation:**
1. As liquid accelerates through the valve restriction, pressure drops
2. At the vena contracta, pressure falls below Pv → vapour bubbles form (cavitation inception)
3. Downstream of the vena contracta, pressure recovers above Pv → bubbles collapse violently
4. Bubble collapse generates shock waves, high localised temperatures, and micro-jets
5. These cause **pitting erosion** of trim and body, vibration, and noise

**Flashing:**
1. Same initial process — bubbles form at vena contracta
2. Downstream pressure P2 remains below Pv → bubbles **do not collapse**
3. Two-phase mixture exits the valve
4. The downstream piping carries a vapour-liquid mixture
5. Causes **erosion** on downstream piping and equipment, two-phase flow measurement problems

**Distinction in the app:**
```
P_vc < Pv  AND  P2 ≥ Pv  →  CAVITATION  (bubbles collapse)
P_vc < Pv  AND  P2 < Pv  →  FLASHING    (bubbles persist)
```

### 9.2 Vena Contracta Pressure

The vena contracta pressure is estimated from FL and the effective ΔP:

$$P_{vc} = P_1 - \frac{\Delta P_{\text{eff}}}{F_L^2} \quad \text{(Eq. 9.1, from IEC Eq. 4)}$$

The FL factor describes how much the pressure drops at the vena contracta relative to the overall ΔP. A low FL valve (butterfly, ball) concentrates more ΔP at the vena contracta, making cavitation more likely at moderate overall ΔP.

### 9.3 Cavitation Index σ

The **cavitation index** (or sigma) provides a dimensionless measure of the tendency for cavitation:

$$\sigma = \frac{P_1 - P_v}{\Delta P} = \frac{P_1 - P_v}{P_1 - P_2} \quad \text{(Eq. 9.2, IEC 60534-8-4)}$$

Larger σ means less tendency to cavitate (high inlet pressure relative to ΔP). Smaller σ means higher risk. The critical sigma values are:

| Regime | Condition | Approximate threshold |
|---|---|---|
| No cavitation | σ > σ_i | σ > 1/FL² |
| Incipient cavitation | σ ≈ σ_i | σ_i ≈ 1/FL² |
| Constant cavitation | σ < σ_c | σ_c ≈ 0.5/FL² |
| Choked cavitation | σ ≤ σ_ch | σ_ch ≈ (1−FF)/FL² |
| Flashing | P2 < Pv | — |

These threshold values are engineering approximations. IEC 60534-8-4 specifies more precise values derived from laboratory testing of specific valve types. The app uses the above simplified thresholds as conservative indicators suitable for initial design assessment.

### 9.4 Five-Tier Cavitation Regime Classification

The app implements a five-tier cavitation regime classification per IEC 60534-8-4:

**Regime 1 — No Cavitation (σ > σ_i):**
No vapour formation. Normal liquid flow. No action required.

**Regime 2 — Incipient Cavitation (σ_c < σ ≤ σ_i):**
Small bubbles form momentarily at the vena contracta. Minor noise increase. Acceptable for short-term or infrequent operation. Trim wear monitoring recommended.

**Regime 3 — Constant Cavitation (σ_ch < σ ≤ σ_c):**
Sustained bubble formation and collapse. Significant noise (crackling, like gravel in the pipe), vibration, and accelerated trim erosion. Anti-cavitation trim recommended.

**Regime 4 — Choked Cavitation (P_vc ≤ FF·Pv, ΔP ≥ ΔP_max):**
Flow is limited by vapour formation. Severe bubble collapse. Rapid metal loss from trim and body. Anti-cavitation trim with hardened materials (Stellite, tungsten carbide) is mandatory.

**Regime 5 — Flashing (P_vc < Pv, P2 < Pv):**
Sustained two-phase flow. Angle valve body required to direct the erosive stream away from the body wall. Hard-faced trim is essential. Downstream piping must be designed for two-phase flow.

### 9.5 Engineering Responses to Cavitation

**For Incipient cavitation:**
- Accept if service is clean, non-erosive, and the valve is not the primary control valve
- Upgrade trim to hardened materials as a precaution

**For Constant cavitation:**
- Select anti-cavitation trim (stacked-disk, tortuous-path, or cage with anti-cavitation holes)
- Consider back-pressure control (raise P2 by throttling downstream)
- Split the ΔP across two valves in series

**For Choked cavitation:**
- Anti-cavitation trim is mandatory
- Multi-stage pressure let-down with two or more valves in series
- Select body material resistant to cavitation damage (stainless steel, Hastelloy, Duplex)

**For Flashing:**
- Angle body to direct flow away from body wall
- Hard-faced trim (Stellite grade 6 or equivalent, HRC > 45)
- Downstream piping in Schedule 80 or higher, with erosion-resistant liner if severe
- Vent or separator downstream to remove vapour phase
- Two-phase flow metering downstream

### 9.6 Anti-Cavitation Trim Principles

Anti-cavitation trim uses one of three principles to prevent cavitation damage:

1. **Multi-stage pressure reduction:** The pressure drop is distributed across multiple stages (2 to 20+), so no single stage has a ΔP large enough to cause P_vc to fall below Pv. Each stage has its own small restriction. The app's valve selection advisor recommends multi-stage trim when the choked cavitation regime is detected.

2. **Tortuous path:** Flow follows a long, winding path of constant cross-section, dissipating energy as friction heat rather than kinetic energy. No vena contracta is formed. Used in very high ΔP services.

3. **Characterised cage with cavitation-resistant geometry:** Special cage holes designed to control flow area and prevent high local velocities. More compact than tortuous path but less effective at extreme ΔP.

---

## 10. Noise Prediction

### 10.1 Overview and Regulatory Context

Valve noise is an occupational health issue (OSHA PEL: 90 dB(A) over 8 hours; ACGIH TLV: 85 dB(A)), an environmental issue (many plant permits specify ≤ 85 dB(A) at the fence line), and a process integrity issue (noise implies energy dissipation and potential vibration fatigue).

IEC 60534-8 provides noise prediction methods:
- **IEC 60534-8-3:2011** — Aerodynamic noise (gas and steam service)
- **IEC 60534-8-4:2015** — Hydrodynamic noise (liquid service, including cavitation)

The app implements the full IEC 60534-8-3 chain and a simplified IEC 60534-8-4 estimate.

### 10.2 Aerodynamic Noise — IEC 60534-8-3:2011

Aerodynamic noise is generated by turbulent jets and shock structures in the gas flow through the valve trim. The IEC 60534-8-3 calculation chain has eight steps:

**Step 1 — Mechanical Stream Power Wm [W]**

The mechanical stream power is the kinetic energy per unit time available for conversion to sound. For isentropic gas expansion:

$$W_m = \dot{m} \cdot \frac{\gamma}{\gamma - 1} \cdot \frac{P_1}{\rho_1} \cdot \left[1 - \left(\frac{P_{2,\text{eff}}}{P_1}\right)^{(\gamma-1)/\gamma}\right] \quad \text{(Eq. 10.1, IEC 8-3 §5.1)}$$

where P2,eff = max(P2, P_crit) and $P_{\text{crit}} = P_1 \left(\frac{2}{\gamma+1}\right)^{\gamma/(\gamma-1)}$.

**Step 2 — Vena Contracta Mach Number Mvc**

$$P_{vc} \approx P_1 - \frac{P_1 - P_2}{F_L^2} \quad \text{(approximation)}$$

$$M_{vc} = \sqrt{\frac{2}{\gamma - 1}\left[\left(\frac{P_1}{P_{vc}}\right)^{(\gamma-1)/\gamma} - 1\right]} \quad \text{(Eq. 10.2)}$$

For $P_{vc} \leq P_{\text{crit}}$: Mvc = 1.0 (choked, sonic jet).

**Step 3 — Acoustic Efficiency Factor η_a (Baumann/IEC 8-3 §5.3)**

This is the key step that determines what fraction of Wm is converted to acoustic power. The app implements the Mach-dependent Baumann (1987) correlation:

$$\eta_a = \eta_0 \cdot M_{vc}^{3.6} \quad \text{for } M_{vc} \leq M_{\text{crit}} = 0.3 \quad \text{(Eq. 10.3a)}$$

$$\eta_a = \eta_0 \cdot M_{\text{crit}}^{3.6} \cdot \left(\frac{M_{vc}}{M_{\text{crit}}}\right)^{k} \quad \text{for } M_{vc} > 0.3 \quad \text{(Eq. 10.3b)}$$

where η₀ = 10⁻⁴, M_crit = 0.3, k = 1.0 (sonic jet exponent, IEC 8-3 §5.3).

**Why this matters:** The previous (incorrect) constant efficiency η_a = 10⁻⁴ overestimates noise at low Mvc (subsonic, low ΔP) and underestimates at high Mvc (near-sonic). The Mach-dependent correlation provides physically consistent predictions across the full operating range.

**Step 4 — Internal Acoustic Power Wa:**
$$W_a = \eta_a \cdot W_m \quad \text{(Eq. 10.4)}$$

**Step 5 — Internal Sound Power Level Lpi:**
$$L_{pi} = 10 \log_{10}\left(\frac{W_a}{W_{\text{ref}}}\right) \quad \text{[dB re 1 pW]} \quad \text{(Eq. 10.5)}$$

where W_ref = 10⁻¹² W (acoustic reference power).

**Step 6 — Peak Frequency fp:**
$$f_p = \frac{0.2 \cdot c_{vc}}{F_d \cdot d} \quad \text{[Hz]} \quad \text{(Eq. 10.6, IEC 8-3 §5.4)}$$

where c_vc = speed of sound at the vena contracta, Fd = valve style modifier, d = valve bore [m].

**Step 7 — Pipe Wall Transmission Loss TL:**

The pipe wall attenuates the internal sound before it reaches the outside:

$$TL = 10 \log_{10}\left[\frac{(\rho_{\text{steel}} \cdot c_{\text{steel}} \cdot t)^2}{\rho_{\text{air}} \cdot c_{\text{air}} \cdot \pi \cdot D_i \cdot f_p}\right] \quad \text{[dB]} \quad \text{(Eq. 10.7, mass law)}$$

where: t = pipe wall thickness [m], Di = pipe internal diameter [m], ρ_steel = 7800 kg/m³, c_steel = 5000 m/s, ρ_air = 1.2 kg/m³, c_air = 343 m/s.

Typical TL values: 25–45 dB for Sch 40 steel pipe at valve-noise frequencies.

**Step 8 — External A-weighted SPL Lpe:**
$$L_{pe} = L_{pi} - TL + A(f_p) \quad \text{[dB(A) at 1 m]} \quad \text{(Eq. 10.8)}$$

where A(fp) is the A-weighting correction at the peak frequency:

| Octave Centre Frequency [Hz] | A-weighting [dB] |
|---|---|
| 63 | −26.2 |
| 125 | −16.1 |
| 250 | −8.6 |
| 500 | −3.2 |
| 1000 | 0.0 |
| 2000 | +1.2 |
| 4000 | +1.0 |
| 8000 | −1.1 |
| 16000 | −6.6 |

*(Source: IEC 61672-1:2013 Table 1)*

### 10.3 Hydrodynamic Noise — IEC 60534-8-4

Liquid service noise is generated by turbulence and, more severely, by bubble collapse in cavitating flow. The full IEC 60534-8-4 procedure involves:
1. Identifying the cavitation regime (§9.4)
2. Computing the peak pressure in the cavitation zone
3. Applying regime-specific internal SPL equations
4. Computing pipe TL at the dominant frequency
5. Converting to external A-weighted SPL

The app implements a simplified estimate based on the mechanical stream power and regime-dependent acoustic efficiency:

$$W_a = \eta_{\text{liquid}} \cdot W_m$$

where η_liquid ≈ 10⁻⁶ (no cavitation), 10⁻⁵ (constant cavitation), 3×10⁻⁵ (choked/flashing). This estimate may differ from the full IEC 60534-8-4 result by ±10–20 dB(A).

### 10.4 Noise Reduction Strategies

**Anti-noise trim:** Multi-hole cages, stacked-disk trims, or tortuous-path trim reduce fp to lower frequencies where A-weighting correction is more negative and the human ear is less sensitive. They also split the flow into smaller jets, reducing Wm per jet.

**Downstream silencer:** An in-line reactive or absorptive silencer on the downstream pipe can add 15–30 dB(A) of attenuation. Placed 5–10 pipe diameters downstream of the valve.

**Pipe lagging/insulation:** Acoustic blankets around the downstream pipe increase TL by 5–15 dB(A). Simple, low-cost, and effective for existing installations.

**Valve body selection:** Globe valves (high Fd = 1.0) generate noise at higher frequencies than cage-guided valves (lower Fd). For noise-critical applications, select trim with low Fd.

**Staging:** Two valves in series, each taking half the total ΔP, reduce total noise by approximately 5 log₁₀(2) ≈ 1.5 dB — modest. However, staging primarily addresses cavitation.

---

## 11. Valve Flow Characteristics

### 11.1 Inherent vs. Installed Characteristic

The **inherent characteristic** is the relationship between valve opening (travel θ, 0–100%) and flow coefficient Cv measured in a laboratory under **constant pressure differential**. It describes the valve's intrinsic hydraulic property independent of the system.

The **installed characteristic** is what the valve actually delivers in a real piping system, where the pressure differential across the valve varies with flow. As flow increases, more ΔP is consumed by piping friction and static head, leaving less for the valve.

The installed characteristic is what determines **control quality** — a non-linear installed characteristic causes variable gain in the control loop, leading to instability or sluggish response at certain operating points.

### 11.2 Standard Inherent Characteristics

**Equal-percentage (the most common for process control):**
$$C_v(\theta) = C_{v,\text{rated}} \cdot R^{(\theta - 1)} \quad \text{(Eq. 11.1, IEC 60534-2-4 Eq. 1)}$$

A fixed incremental change in valve opening produces a fixed *percentage* change in Cv. For R = 50:

| Opening θ | Cv / Cv_rated |
|---|---|
| 0% | 1/R = 2.0% |
| 25% | 3.4% |
| 50% | 14.1% |
| 75% | 59.5% |
| 100% | 100% |

**Linear:**
$$C_v(\theta) = C_{v,\text{rated}} \cdot \theta \quad \text{(Eq. 11.2)}$$

Equal incremental changes in opening produce equal incremental changes in Cv. Simple but rarely gives a linear installed characteristic.

**Quick-opening:**
$$C_v(\theta) = C_{v,\text{rated}} \cdot \sqrt{\theta} \quad \text{(Eq. 11.3)}$$

Most of the Cv is achieved in the first 20–30% of opening. Used for on/off applications or where an immediate large flow change is needed.

### 11.3 Installed Characteristic Calculation

For a system with a fixed total ΔP (pump head minus static head) and valve authority β:

$$\frac{q}{q_{\text{design}}} = \frac{C_v(\theta)}{C_{v,\text{design}}} \cdot \sqrt{\frac{\beta}{1 - \beta + \beta \cdot (C_v(\theta)/C_{v,\text{design}})^2}} \quad \text{(Eq. 11.4)}$$

where **valve authority β** is defined as:

$$\beta = \frac{\Delta P_{\text{valve}}}{\Delta P_{\text{total}}} \bigg|_{\text{design flow}} \quad \text{(Eq. 11.5)}$$

**β = 1.0:** All pressure drop is across the valve (system with no piping losses). Installed characteristic = inherent characteristic.

**β = 0.5:** Valve and system share pressure drop equally. Modest distortion of installed characteristic.

**β < 0.2:** Most ΔP is in the piping. Severe distortion — even an equal-percentage valve will have a quick-opening installed characteristic.

### 11.4 Gain and Controllability

The installed valve gain (dimensionless) at any operating point is:

$$G(\theta) = \frac{d(q/q_d)}{d\theta} \bigg|_{\text{installed}} \quad \text{(Eq. 11.6)}$$

**Good control:** G is approximately constant over the operating range. Gain variability < 50%.

**Poor control:** G varies widely. At low openings, the loop gain may be too low (sluggish); at high openings, too high (instability risk).

**Rule of thumb for characteristic selection:**
- β > 0.5: Linear characteristic gives approximately linear installed characteristic
- 0.25 < β < 0.5: Equal-percentage characteristic partially compensates for system non-linearity, giving near-linear installed characteristic
- β < 0.25: Equal-percentage is usually still preferred; consider split-range or digital valve positioner with characterisation

*App feature: The Installed Characteristic tab plots both curves and reports the gain variability percentage. A warning is issued when gain variability exceeds 50%.*

### 11.5 Rangeability

**Inherent rangeability** R is the ratio of the maximum to minimum controllable Cv at rated pressure drop:

$$R = \frac{C_{v,\text{rated}}}{C_{v,\text{min}}} \quad \text{(Eq. 11.7, ISA-75.11.01)}$$

Standard inherent rangeability:
- Globe valves (single-seat, cage-guided): R = 50:1
- Ball valves, rotary plug: R = 25–50:1
- Butterfly valves: R = 10–25:1

**Effective (installed) rangeability** is always lower than inherent rangeability due to system interaction. See §12.

---

## 12. Rangeability and Turndown

### 12.1 Definitions

**Rangeability R** (IEC 60534-2-4, ISA-75.11.01): The ratio of the maximum to minimum Cv that can be controlled within the stated accuracy at rated conditions (constant ΔP).

**Turndown**: The ratio of maximum to minimum *controllable flow* in an actual installed system. Turndown ≤ rangeability due to system ΔP variation.

**Effective rangeability** R_eff: The Cv range actually available in the installed system:

$$R_{\text{eff}} = \frac{C_{v,\text{rated}}}{C_{v,\text{min}}} \quad \text{(Eq. 12.1)}$$

where Cv_min is the minimum Cv that can be reliably controlled (typ. 2–7% of Cv_rated, depending on valve type).

### 12.2 Minimum Controllable Cv

The minimum controllable Cv (below which the valve becomes mechanically or hydraulically unstable) depends on valve type:

| Valve Type | Cv_min (% of Cv_rated) | Effective R |
|---|---|---|
| Globe single-seat | 2% | 50:1 |
| Globe cage-guided | 2% | 50:1 |
| Angle valve | 2% | 50:1 |
| Eccentric rotary plug | 3% | 33:1 |
| Ball valve | 5% | 20:1 |
| Butterfly (HP) | 5% | 20:1 |
| Butterfly (wafer) | 7% | 14:1 |

For quick-opening characteristic valves: Cv_min ≈ 8% (poor inherent rangeability).

### 12.3 Required Turndown

The required process turndown is determined by the maximum and minimum flow conditions:

$$TD_{\text{required}} = \frac{Q_{\text{max}}}{Q_{\text{min}}} \quad \text{(Eq. 12.2)}$$

For constant ΔP, this translates directly to a Cv ratio:

$$TD = \frac{C_{v,\text{design}}}{C_{v,\text{min,process}}} \quad \text{(Eq. 12.3)}$$

**Adequacy check (with 10% margin):**

$$R_{\text{eff}} \geq 1.1 \times TD_{\text{required}} \quad \text{(Eq. 12.4)}$$

### 12.4 Leakage Class Selection

Valve seat leakage becomes significant when the valve is in the fully closed position. ANSI/FCI 70-2 (IEC 60534-4) defines six leakage classes:

| Class | Maximum Leakage | Typical Application |
|---|---|---|
| Class I | No test required | On/off service |
| Class II | 0.5% of rated Cv | Standard process control |
| Class III | 0.1% of rated Cv | Improved control |
| Class IV | 0.01% of rated Cv | Tight shutoff (metal seats) |
| Class V | 5×10⁻⁴ ml/min·bar·mm seat dia | Very tight (metal seats, high ΔP) |
| Class VI | Bubble-tight per table | Soft seats, safety/isolation |

Class V leakage test uses water at rated ΔP; Class VI uses air or nitrogen at 3.5 bar g (50 psig). The app's rangeability module recommends a leakage class based on valve type, cavitation regime, and noise level.

---

## 13. Valve Body and Trim Selection

### 13.1 Body Style Selection Logic

The app's valve selection advisor applies a rule-based decision tree. The following summarises the logic:

**Flashing service:**
- → Angle valve body (directs stream away from body wall)
- → Hard-faced trim mandatory (Stellite or ceramic)

**Choked cavitation:**
- → Globe or angle body with anti-cavitation trim
- → Consider multi-stage trim or staged valve arrangement

**Noise > 95 dB(A) (gas/steam):**
- → Cage-guided globe with anti-noise trim
- → Consider in-line silencer

**Large bore (d > 200 mm) with low ΔP:**
- → High-performance butterfly
- → Ball valve (full bore)

**High pressure drop ratio x > 0.5 (gas):**
- → Globe cage-guided
- → Consider two-stage pressure let-down

**Viscous liquid (μ > 200 cP):**
- → Ball valve (full bore) to minimise viscous losses
- → Avoid globe with characterised cage (high pressure drop)

**Standard process control (liquid, moderate ΔP):**
- → Globe single-seat (best all-around)
- → Cage-guided globe (for erosive or high-cycling)

### 13.2 Trim Type Selection

| Service Condition | Recommended Trim | Why |
|---|---|---|
| General service | Contoured parabolic plug | Low cost, good rangeability |
| Characterised flow profile | Characterised cage | Precise Cv characteristic, replaceable |
| Cavitating service | Anti-cavitation trim | Multi-stage ΔP reduction |
| Noisy gas service | Anti-noise trim | Low Fd, low fp |
| Severe pressure drop | Multi-stage / tortuous path | Distributes energy without cavitation |
| Erosive service | Hard-facing (Stellite) | Hardness > HRC 40 |
| High temperature (>450°C) | Inconel / Hastelloy trim | Oxidation resistance |

### 13.3 Material Selection

**Body materials (per ASTM):**

| Material | Grade | Max Temp | Application |
|---|---|---|---|
| Carbon steel | A216 WCB | 425°C | General service |
| Low-temp carbon steel | A352 LCB | −46°C | Cold service |
| 304 Stainless | A351 CF8 | 540°C | Corrosive, food-grade |
| 316 Stainless | A351 CF8M | 540°C | Chloride environments |
| Duplex SS | A890 4A | 315°C | Sour service (with NACE) |
| Hastelloy C | — | 540°C | Highly corrosive |
| Inconel 625 | — | 815°C | High temperature |

**Trim materials:**
- Standard: 316 SS (plug) / 316 SS (seat ring)
- Erosive service: Stellite-6 hard-facing (55+ HRC, Co-Cr-W alloy)
- Cavitating: Stellite-6 or NACE-compliant grades
- Abrasive slurry: Tungsten carbide (WC) inserts

### 13.4 Pressure-Temperature Ratings (ASME B16.34)

Valve body material and design must meet ASME B16.34 pressure-temperature ratings for the specified pressure class:

| ANSI Class | Approx. Max Pressure at 38°C | Typical Application |
|---|---|---|
| 150 | 19.6 bar g (285 psig) | Low pressure utilities |
| 300 | 51.1 bar g (740 psig) | Moderate pressure |
| 600 | 102.1 bar g (1480 psig) | High pressure |
| 900 | 153.0 bar g (2220 psig) | Refinery high pressure |
| 1500 | 255.0 bar g (3705 psig) | Very high pressure |
| 2500 | 425.0 bar g (6170 psig) | Extreme pressure |

*The app's valve selection guide notes the appropriate pressure class in the recommendations.*

---

## 14. Actuator Sizing

### 14.1 Overview

The actuator must overcome all forces opposing valve movement:
1. **Unbalanced force** — net pressure force acting on the plug
2. **Packing friction** — stem seal resistance
3. **Seat load** — force required for tight shutoff
4. A **contingency factor** (typically 10–25%) is added to the sum

### 14.2 Linear (Globe/Angle) Valve Actuator

**Unbalanced stem force:**

For a single-seated globe valve (unbalanced plug), the net pressure force at shutoff is:

$$F_{\text{unbal}} = \frac{\pi}{4} \cdot d_{\text{seat}}^2 \cdot \Delta P_{\text{shutoff}} \quad \text{(Eq. 14.1)}$$

where d_seat ≈ 0.95 × d (valve bore) for globe single-seat, and ΔP_shutoff = P1 (one port blocked, maximum at shutoff).

For a **balanced plug** (cage-guided with balance holes), the unbalanced force is 10–20% of the unbalanced case.

**Packing friction:**

$$F_{\text{pack}} = C_{\text{friction}} \cdot \pi \cdot d_{\text{stem}} \cdot L_{\text{packing}} \cdot P_{\text{gland}} \quad \text{(Eq. 14.2)}$$

In practice, the app uses empirical per-unit-stem-diameter values:

| Packing Type | Base force [N/mm stem dia.] |
|---|---|
| PTFE | 50 |
| PTFE/Graphite composite | 80 |
| Live-loaded PTFE | 70 |
| Graphite | 120 |

**Required seat load for shutoff (ANSI/FCI 70-2):**

$$F_{\text{seat}} = S_L \cdot \pi \cdot d_{\text{seat}} \quad \text{(Eq. 14.3)}$$

where SL = seat load factor [N/mm of seat circumference]:
- Class II: 15 N/mm
- Class III: 25 N/mm
- Class IV: 40 N/mm
- Class V: 55 N/mm
- Class VI: 70 N/mm

**Total required thrust with contingency:**

$$F_{\text{req}} = (F_{\text{unbal}} + F_{\text{pack}} + F_{\text{seat}}) \times 1.10 \quad \text{(Eq. 14.4)}$$

**Pneumatic diaphragm area:**

$$A_d = \frac{F_{\text{req}}}{P_{\text{supply}} \times \eta} \quad \text{[cm}^2\text{]} \quad \text{(Eq. 14.5)}$$

where η = 0.80 (diaphragm mechanical efficiency), P_supply in bar g.

### 14.3 Rotary Valve Actuator (Torque)

For ball, butterfly, and eccentric rotary plug valves, the actuator must provide torque rather than linear thrust:

**Break torque** (to unseat the disc/ball from closed position):

$$T_{\text{break}} = C_T \cdot d_{\text{trim}}^3 \cdot \Delta P_{\text{shutoff}} \quad \text{(Eq. 14.6)}$$

where d_trim is the trim/ball diameter [m] and CT is an empirical torque coefficient:

| Valve Type | CT |
|---|---|
| Ball valve (full bore) | 0.075 |
| Ball valve (reduced bore) | 0.065 |
| Butterfly (high performance) | 0.040 |
| Butterfly (wafer) | 0.035 |
| Eccentric rotary plug | 0.050 |

**Running torque** (to continue moving past 5°): T_run ≈ 0.50 × T_break

**End torque** (to re-seat at open end): T_end ≈ 0.75 × T_break

**Required actuator torque:**

$$T_{\text{req}} = T_{\text{break}} \times 1.10 \quad \text{(Eq. 14.7)}$$

### 14.4 Fail-Safe Action

**Fail-closed (FC) / Air-to-open (ATO):**
- Spring opposes air pressure; supply air opens valve
- On air failure: spring returns to closed
- Used for: safety shutoff, feed valves (prevent process runaway)
- Actuator sized for: spring force must exceed F_req at zero air pressure

**Fail-open (FO) / Air-to-close (ATC):**
- Spring opposes air pressure; supply air closes valve
- On air failure: spring returns to open
- Used for: cooling water, vent valves (prevent overpressure)
- Actuator sized for: spring + air must exceed F_req (closing) AND spring alone must hold open against process forces

**Fail-in-place (FIP):**
- Used with lock-up systems, double-acting pistons, or electric actuators
- Not inherently safe — requires SIS analysis

### 14.5 Electric Actuator Sizing

$$P_{\text{motor}} = \frac{F_{\text{req}} \cdot v_{\text{stem}}}{1000 \cdot \eta_{\text{gear}}} \quad \text{[kW]} \quad \text{(Eq. 14.8)}$$

where v_stem = typical stem velocity [mm/s], η_gear = gearbox efficiency (typically 0.70–0.85).

Standard motor sizes: 0.1, 0.25, 0.55, 1.1, 2.2, 4.0, 7.5 kW. The app recommends the next standard size above the calculated requirement.

*App feature: The Actuator Sizing tab provides preliminary guidance for all three actuator types with fail-safe analysis and spring range recommendation. Results include a disclaimer that final sizing must be confirmed with the manufacturer.*

---

## 15. Sensitivity Analysis

### 15.1 Purpose

A sensitivity analysis answers: "How sensitive is the sizing result to uncertainty in the input parameters?" This is critical because:
- Process conditions have measurement and uncertainty tolerances
- Future debottlenecking may require higher flows or pressures
- Off-design conditions (startup, upset, minimum flow) differ from design
- Fluid properties (especially for natural gas mixtures) have composition uncertainty

### 15.2 Sensitivity Index

For each input parameter x_i, the normalised sensitivity index Si quantifies the fractional change in output y per unit fractional change in input:

$$S_i = \left|\frac{\partial y / y}{\partial x_i / x_i}\right| = \left|\frac{x_i}{y} \cdot \frac{\partial y}{\partial x_i}\right| \quad \text{(Eq. 15.1)}$$

A sensitivity index of 1.0 means a 1% change in the parameter causes a 1% change in the output. Si > 1 indicates amplification.

**Analytical sensitivity of Cv to key parameters (liquid, turbulent, no reducers):**

$$C_v = \frac{Q}{N_1 \sqrt{\Delta P / G_f}}$$

$$S_{Q} = 1.0 \quad \text{(flow)} \quad \text{(Eq. 15.2)}$$
$$S_{\Delta P} = 0.5 \quad \text{(pressure drop)} \quad \text{(Eq. 15.3)}$$
$$S_{G_f} = 0.5 \quad \text{(specific gravity)} \quad \text{(Eq. 15.4)}$$

A 10% uncertainty in flow leads to 10% uncertainty in Cv. A 10% uncertainty in ΔP leads to only 5% uncertainty in Cv.

### 15.3 Parameters Swept by the App

The app's sensitivity module sweeps ±N% (user-configurable, typically ±30%) in configurable steps (default 5) around the base value for:

- **P1** — Upstream pressure: affects x (gas), ρ1, ΔP, choked condition
- **P2** — Downstream pressure: affects ΔP directly
- **T1** — Temperature: affects ρ1, Pv, steam properties
- **Flow rate** — Direct proportional effect on Cv
- **Gf or M** — Specific gravity / molecular weight: density effect
- **Viscosity** — FR correction for viscous flow
- **FL** — Liquid pressure recovery: affects ΔP_max and cavitation thresholds
- **xT** — Gas pressure drop ratio: affects choked flow and Y

### 15.4 Tornado Chart Interpretation

The tornado chart ranks parameters by their sensitivity index (largest bar at top). Parameters with Si > 0.5 are dominant contributors to Cv uncertainty and should be measured or specified with higher precision.

*App feature: The Sensitivity tab generates both tornado charts and line plots, with a downloadable full data table.*

---

---

## 16. Case Studies

The following case studies are fully worked examples using the equations presented in this handbook. Each corresponds to a scenario that can be reproduced exactly in the Control Valve Sizer app.

---

### Case Study 1 — Boiler Feed Water Control Valve (Liquid, Cavitation Risk)

**Service:** Boiler feed water pump discharge to steam drum

**Process data:**

| Parameter | Value | Unit |
|---|---|---|
| Fluid | Boiler feed water | — |
| Inlet pressure P1 | 45 bar a | bar absolute |
| Outlet pressure P2 | 38 bar a | bar absolute |
| Temperature T1 | 145°C | °C |
| Flow (normal) | 120 m³/h | m³/h |
| Flow (max) | 150 m³/h | m³/h |
| Specific gravity Gf | 0.921 | — |
| Vapour pressure Pv | 3.69 bar a | bar a (at 145°C) |
| Critical pressure Pc | 220.64 bar a | bar a |
| Viscosity μ | 0.20 cP | cP |
| Valve type | Globe single-seat | — |
| FL | 0.90 | — |
| Pipe ID (inlet/outlet) | 154 mm | mm (6" Sch 40) |
| Valve bore d | 102 mm | mm (4" body) |

**Step 1: FF factor**
$$F_F = 0.96 - 0.28\sqrt{\frac{3.69}{220.64}} = 0.96 - 0.28\sqrt{0.01673} = 0.96 - 0.28 \times 0.1293 = 0.924$$

**Step 2: Rough Cv estimate (Fp = 1, seed for piping iteration)**
$$\Delta P = 45 - 38 = 7 \text{ bar}$$
$$C_{v,\text{rough}} = \frac{120}{0.865 \times \sqrt{7/0.921}} = \frac{120}{0.865 \times 2.759} = \frac{120}{2.387} = 50.3$$

**Step 3: Piping correction factors (4" valve in 6" pipe)**

Fitting loss coefficients:
$$K_1 = 0.5\left(1 - \frac{102^2}{154^2}\right)^2 = 0.5\left(1 - 0.438\right)^2 = 0.5 \times 0.316 = 0.158$$
$$K_2 = \left(1 - \frac{102^2}{154^2}\right)^2 = 0.316$$
$$\Sigma K = 0.474$$

Fp iteration (start with Cv_rough = 50.3):
$$\text{Iter 1: } C_{v,1} = 50.3 / 1.0 = 50.3$$
$$\text{term} = \frac{0.474}{0.00214} \times \left(\frac{50.3}{102^2}\right)^2 = 221.5 \times (0.004835)^2 = 221.5 \times 2.338 \times 10^{-5} = 0.00518$$
$$F_{p,1} = \frac{1}{\sqrt{1.00518}} = 0.9974$$

$$\text{Iter 2: } C_{v,2} = 50.3 / 0.9974 = 50.4$$
$$F_{p,2} = 0.9974 \quad \text{(converged)}$$

*Fp ≈ 0.997 — piping correction is negligible at this Cv-to-bore ratio*

FLP (using K1 only):
$$F_{LP} = \frac{0.90}{\sqrt{1 + \frac{0.90^2 \times 0.158}{0.00214} \times (0.004835)^2}} = \frac{0.90}{\sqrt{1 + 0.00243}} \approx 0.899$$

**Step 4: ΔP_max (choked flow check)**
$$\Delta P_{\max} = \left(\frac{0.899}{0.997}\right)^2 \times (45 - 0.924 \times 3.69) = (0.902)^2 \times (45 - 3.410)$$
$$= 0.814 \times 41.59 = 33.85 \text{ bar}$$

Available ΔP = 7 bar < ΔP_max = 33.85 bar → **not choked** ✓

**Step 5: Cavitation check**
$$P_{vc} = 45 - \frac{7}{0.90^2} = 45 - 8.64 = 36.36 \text{ bar a}$$
$$\sigma = \frac{45 - 3.69}{7} = \frac{41.31}{7} = 5.90$$
$$\sigma_{\text{incipient}} = \frac{1}{0.90^2} = 1.235$$

σ = 5.90 >> σ_incipient = 1.235 → **No cavitation** ✓

*P_vc = 36.4 bar >> Pv = 3.69 bar — excellent margin from vapour formation*

**Step 6: Reynolds number and viscous correction**
$$\nu = \frac{0.20}{0.921} = 0.217 \text{ cSt}$$
$$Re_v = \frac{334620 \times 1.0 \times 120}{0.217 \times \sqrt{0.90 \times 50.4}} = \frac{40154400}{0.217 \times 6.74} = \frac{40154400}{1.463} = 27.45 \times 10^6$$

Rev >> 40 000 → FR = 1.0 (fully turbulent) ✓

**Step 7: Final Cv**
$$C_v = \frac{120}{0.865 \times 0.997 \times 1.0 \times \sqrt{7/0.921}} = \frac{120}{0.865 \times 0.997 \times 2.759} = \frac{120}{2.381} = \mathbf{50.4}$$

**Step 8: Max flow Cv**
$$C_{v,\max} = 50.4 \times \frac{150}{120} = \mathbf{63.0}$$

**Sizing summary:**
| Parameter | Normal | Maximum |
|---|---|---|
| Cv required | 50.4 | 63.0 |
| Cv with 10% margin | 55.4 | 69.3 |
| Recommended rated Cv | **80** (standard trim) | — |
| Sizing ratio (Cv_req / Cv_rated) | 0.63 | 0.79 |
| Estimated opening (EP char.) | 57% | 68% |
| Cavitation regime | None | None |

**Valve selection:** 4" globe single-seat, ASTM A216 WCB body, 316 SS trim, Class IV leakage, FL = 0.90, ASME Class 300 flanges (rated to 51 bar at temperature).

---

### Case Study 2 — Fuel Gas Letdown Valve (Gas, Choked Flow)

**Service:** Natural gas pressure letdown from high-pressure transmission line to plant fuel gas header

**Process data:**

| Parameter | Value | Unit |
|---|---|---|
| Gas | Natural gas | — |
| Molecular weight M | 17.5 g/mol | g/mol |
| Specific heat ratio γ | 1.31 | — |
| Compressibility Z | 0.88 | — |
| Inlet pressure P1 | 60 bar a | bar a |
| Outlet pressure P2 | 10 bar a | bar a |
| Temperature T1 | 25°C = 298.15 K | K |
| Mass flow W | 8000 kg/h | kg/h |
| Valve type | Globe cage-guided | — |
| FL = (for noise) | 0.90 | — |
| xT | 0.75 | — |
| Fd | 0.90 | — |
| Pipe ID | 154 mm | mm (6" Sch 40) |
| Valve bore d | 102 mm | mm (4" body) |

**Step 1: Gas density at inlet**
$$\rho_1 = \frac{60 \times 10^5 \times 0.0175}{8.31446 \times 298.15 \times 0.88} = \frac{105000}{2181.4} = 48.14 \text{ kg/m}^3$$

**Step 2: Fk and x**
$$F_k = \frac{1.31}{1.40} = 0.936$$
$$x = \frac{60 - 10}{60} = 0.833$$
$$x_{\text{choked}} = F_k \times x_T = 0.936 \times 0.75 = 0.702$$
$$x_{\text{eff}} = \min(0.833, 0.702) = 0.702 \quad \Rightarrow \textbf{CHOKED FLOW}$$

**Step 3: Y factor (at choked condition)**
$$Y = \max\left(1 - \frac{0.702}{3 \times 0.936 \times 0.75}, 0.667\right) = \max\left(1 - \frac{0.702}{2.106}, 0.667\right) = \max(0.667, 0.667) = 0.667$$

Y = 0.667 confirms choked flow (minimum Y reached).

**Step 4: Piping correction (4" valve in 6" pipe)**

Using same K1, K2 as Case Study 1 but now Cv is much larger. First rough Cv:
$$C_{v,\text{rough}} = \frac{8000}{27.3 \times 1.0 \times 0.667 \times \sqrt{0.702 \times 60 \times 48.14}}$$
$$= \frac{8000}{27.3 \times 0.667 \times \sqrt{2026.2}} = \frac{8000}{27.3 \times 0.667 \times 45.01} = \frac{8000}{820.0} = 9.76$$

With Cv ≈ 9.76 in 102 mm bore:
$$\text{term} = \frac{0.474}{0.00214} \times \left(\frac{9.76}{102^2}\right)^2 = 221.5 \times (9.38 \times 10^{-4})^2 = 221.5 \times 8.80 \times 10^{-7} \approx 0.000195$$

Fp ≈ 1/√1.000195 ≈ 0.9999 ≈ **1.000** (no significant piping correction at this Cv)

xTP: same near-unity correction → xTP ≈ xT = 0.75

**Step 5: Final Cv**
$$C_v = \frac{8000}{27.3 \times 1.0 \times 0.667 \times \sqrt{0.702 \times 60 \times 48.14}} = \frac{8000}{27.3 \times 0.667 \times 45.01} = \frac{8000}{820} = \mathbf{9.76}$$

**Step 6: Noise prediction**

*Mechanical stream power:*
$$P_{\text{crit}} = 60 \times \left(\frac{2}{1.31+1}\right)^{1.31/0.31} = 60 \times \left(0.862\right)^{4.226} = 60 \times 0.534 = 32.0 \text{ bar}$$

Since P2 = 10 bar < P_crit = 32 bar → sonic jet at vena contracta

$$W_m = \frac{8000}{3600} \times \frac{1.31}{0.31} \times \frac{60 \times 10^5}{48.14} \times \left[1 - \left(\frac{32.0}{60}\right)^{0.31/1.31}\right]$$

$$= 2.222 \times 4.226 \times 124686 \times \left[1 - (0.533)^{0.237}\right]$$

$$= 2.222 \times 4.226 \times 124686 \times [1 - 0.838] = 2.222 \times 4.226 \times 124686 \times 0.162$$

$$= 2.222 \times 4.226 \times 20199 = 189,700 \text{ W} \approx 190 \text{ kW}$$

*Mach at vena contracta:* P_vc ≤ P_crit → Mvc = 1.0 (sonic)

*Acoustic efficiency:* Mvc = 1.0 > M_crit = 0.3
$$\eta_a = 10^{-4} \times 0.3^{3.6} \times \left(\frac{1.0}{0.3}\right)^{1.0} = 10^{-4} \times 9.93 \times 10^{-3} \times 3.333 = 3.31 \times 10^{-6}$$

*Acoustic power:*
$$W_a = 3.31 \times 10^{-6} \times 189700 = 0.628 \text{ W}$$

*Internal SPL:*
$$L_{pi} = 10\log_{10}\left(\frac{0.628}{10^{-12}}\right) = 10\log_{10}(6.28 \times 10^{11}) = 10 \times 11.80 = 118 \text{ dB}$$

*Peak frequency (fp = 0.2 × c_vc / (Fd × d)):*
$$c_1 = \sqrt{\frac{1.31 \times 60 \times 10^5}{48.14}} = \sqrt{1.633 \times 10^5} = 404 \text{ m/s}$$
$$c_{vc} = c_1\sqrt{\frac{2}{1.31+1}} = 404 \times \sqrt{0.862} = 404 \times 0.929 = 375 \text{ m/s}$$
$$f_p = \frac{0.2 \times 375}{0.90 \times 0.102} = \frac{75}{0.0918} = 817 \text{ Hz}$$

*Transmission loss (6" Sch 40 pipe, t ≈ 7.11 mm):*
$$TL = 10\log_{10}\left[\frac{(7800 \times 5000 \times 0.00711)^2}{1.2 \times 343 \times \pi \times 0.154 \times 817}\right]$$
$$= 10\log_{10}\left[\frac{(277290)^2}{411.7 \times \pi \times 0.154 \times 817}\right] = 10\log_{10}\left[\frac{7.69 \times 10^{10}}{162,763}\right]$$
$$= 10\log_{10}(472,400) = 10 \times 5.674 = 56.7 \text{ dB}$$

*A-weighting at 817 Hz ≈ −1.5 dB (interpolated between 500 Hz: −3.2 and 1000 Hz: 0.0)*

*External SPL:*
$$L_{pe} = 118 - 56.7 + (-1.5) = \mathbf{59.8 \text{ dB(A)}}$$

This value is well below the 85 dB(A) site limit. The choked condition is the only concern.

**Sizing summary:**

| Parameter | Value |
|---|---|
| Flow condition | **Choked** |
| x_eff / x_choked | 0.702 / 0.702 = 100% (at limit) |
| Y | 0.667 (minimum) |
| Cv required | 9.76 |
| Cv with 10% margin | 10.7 |
| Recommended rated Cv | **12** (next standard size) |
| Predicted noise Lpe | 59.8 dB(A) |
| Valve bore (4") | 102 mm |

**Note on choked flow:** The downstream pressure of 10 bar is well below the critical pressure P_crit ≈ 32 bar. Reducing P2 further (even to atmospheric) will not increase mass flow — it is permanently limited by sonic conditions at the trim. To increase flow, P1 must be raised or a larger Cv valve must be selected.

**Valve selection:** 4" globe cage-guided, carbon steel body, ASME Class 600, 316 SS cage and plug. Cage trim type recommended for noise control and erosion resistance.

---

### Case Study 3 — Steam Control Valve (Saturated Steam, High ΔP)

**Service:** Saturated steam let-down for process heating — turbine bypass / pressure reducing station

**Process data:**

| Parameter | Value | Unit |
|---|---|---|
| Fluid | Saturated steam | — |
| Inlet pressure P1 | 40 bar a | bar a |
| Outlet pressure P2 | 4 bar a | bar a |
| Inlet temperature T1 | 250.4°C (T_sat at 40 bar) | °C |
| Mass flow W | 15 000 kg/h | kg/h |
| Valve type | Globe cage-guided | — |
| xT | 0.72 | — |
| FL | 0.90 | — |

**IAPWS-IF97 properties at P1 = 40 bar, T1 = 250.4°C (saturated vapour):**
- ρ_steam = 20.1 kg/m³
- γ = Cp/Cv ≈ 1.30 (saturated)
- μ = 0.016 cP

**Step 1: Fk and choked flow check**
$$F_k = \frac{1.30}{1.40} = 0.929$$
$$x = \frac{40 - 4}{40} = 0.900$$
$$x_{\text{choked}} = 0.929 \times 0.72 = 0.669$$
$$x_{\text{eff}} = \min(0.900, 0.669) = 0.669 \quad \Rightarrow \textbf{CHOKED}$$

**Step 2: Y factor**
$$Y = \max\left(1 - \frac{0.669}{3 \times 0.929 \times 0.72}, 0.667\right) = 0.667$$

**Step 3: Cv calculation**
$$C_v = \frac{15000}{27.3 \times 1.0 \times 0.667 \times \sqrt{0.669 \times 40 \times 20.1}}$$
$$= \frac{15000}{27.3 \times 0.667 \times \sqrt{537.5}} = \frac{15000}{27.3 \times 0.667 \times 23.18}$$
$$= \frac{15000}{421.8} = \mathbf{35.6}$$

**Step 4: Noise check**
P_crit at 40 bar = 40 × (2/2.30)^(1.30/0.30) = 40 × (0.869)^4.333 = 40 × 0.561 = 22.4 bar
P2 = 4 bar < P_crit = 22.4 bar → sonic jet

The noise calculation follows the same chain as Case Study 2. At this flow rate and pressure ratio, Lpe is expected in the range 75–90 dB(A) depending on pipe size. A cage with anti-noise trim holes is recommended.

**Sizing summary:**

| Parameter | Value |
|---|---|
| Cv required | 35.6 |
| Cv with 10% margin | 39.2 |
| Recommended rated Cv | **50** (next standard cage size) |
| Sizing ratio | 35.6/50 = 0.71 |
| Choked flow | Yes |
| Recommended trim | Anti-noise cage trim |
| Steam quality at outlet | ~0.93 (some condensate formation — monitor for wet steam erosion) |

---

### Case Study 4 — Pump Recirculation Valve (Liquid, Cavitation-Critical, Viscous)

**Service:** Centrifugal pump minimum flow recirculation, viscous crude oil

**Process data:**

| Parameter | Value | Unit |
|---|---|---|
| Fluid | Crude oil (medium gravity) | — |
| Inlet pressure P1 | 35 bar a | bar a |
| Outlet pressure P2 | 3 bar a | bar a |
| Temperature T1 | 60°C | °C |
| Gf | 0.870 | — |
| Vapour pressure Pv | 0.45 bar a | bar a |
| Critical pressure Pc | 25.5 bar a | bar a |
| Viscosity μ | 50 cP | cP |
| Flow (min recirculation) | 25 m³/h | m³/h |
| Valve type | Globe single-seat | — |
| FL | 0.90 | — |
| Valve bore d | 50 mm | mm |
| Pipe ID | 77.9 mm | mm (3" Sch 40) |

**Step 1: FF factor**
$$F_F = 0.96 - 0.28\sqrt{\frac{0.45}{25.5}} = 0.96 - 0.28\sqrt{0.01765} = 0.96 - 0.028 \times 0.133 = 0.923$$

**Step 2: ΔP_max (no reducers assumed — valve bore = pipe bore is not equal, check)**
d = 50 mm, D = 77.9 mm → reducers present.

$$K_1 = 0.5\left(1 - \frac{50^2}{77.9^2}\right)^2 = 0.5\left(1 - 0.412\right)^2 = 0.5 \times 0.345 = 0.173$$
$$K_2 = 0.345; \quad \Sigma K = 0.518$$

Rough Cv (Fp = 1):
$$C_{v,\text{rough}} = \frac{25}{0.865 \times \sqrt{32/0.870}} = \frac{25}{0.865 \times 6.066} = \frac{25}{5.247} = 4.77$$

Fp iteration:
$$\text{term} = \frac{0.518}{0.00214} \times \left(\frac{4.77}{50^2}\right)^2 = 242.1 \times (0.001908)^2 = 242.1 \times 3.64 \times 10^{-6} = 8.81 \times 10^{-4}$$
$$F_p = \frac{1}{\sqrt{1.000881}} = 0.9996 \approx 1.000$$

*Again, piping correction negligible at low Cv-to-bore ratio.*

$$\Delta P_{\max} = 0.90^2 \times (35 - 0.923 \times 0.45) = 0.81 \times (35 - 0.415) = 0.81 \times 34.585 = 28.0 \text{ bar}$$

Available ΔP = 32 bar > ΔP_max = 28.0 bar → **CHOKED FLOW** (cavitating)

$$\Delta P_{\text{eff}} = 28.0 \text{ bar}$$

**Step 3: Cavitation check**
$$P_{vc} = 35 - \frac{28.0}{0.90^2} = 35 - 34.6 = 0.40 \text{ bar a}$$
$$P_{vc} = 0.40 < P_v = 0.45 \text{ bar a} \quad \Rightarrow \text{Vapour forms at VC}$$
$$P_2 = 3 \text{ bar} > P_v = 0.45 \text{ bar} \quad \Rightarrow \text{Bubbles collapse (not flashing)}$$

**→ CHOKED CAVITATION — Anti-cavitation trim mandatory**

$$\sigma = \frac{35 - 0.45}{32} = \frac{34.55}{32} = 1.08$$
$$\sigma_{\text{choked}} = \frac{1-0.923}{0.81} = \frac{0.077}{0.81} = 0.095$$

σ = 1.08 >> σ_choked → choked flow confirmed.

**Step 4: Viscous correction**
$$\nu = \frac{50}{0.870} = 57.5 \text{ cSt}$$
$$Re_v = \frac{334620 \times 1.0 \times 25}{57.5 \times \sqrt{0.90 \times 4.77}} = \frac{8365500}{57.5 \times 2.072} = \frac{8365500}{119.1} = 70200$$

Rev = 70 200 > 40 000 → FR = 1.0 (marginally turbulent — viscosity important!)

At 50 cP, this service is on the boundary. For lower flows or higher viscosity, FR < 1 would apply.

**Step 5: Cv calculation**
$$C_v = \frac{25}{0.865 \times 1.0 \times 1.0 \times \sqrt{28.0/0.870}} = \frac{25}{0.865 \times 5.671} = \frac{25}{4.905} = \mathbf{5.10}$$

**Sizing summary and recommendations:**

| Parameter | Value | Comment |
|---|---|---|
| Cv required | 5.10 | At choked/cavitation limit |
| Cv with 10% margin | 5.61 | — |
| Recommended rated Cv | **8** | Standard trim size |
| Cavitation regime | **Choked cavitation** | Severe |
| ΔP across valve | 32 bar available; 28 bar effective | 4 bar "wasted" by choked limit |
| Anti-cav trim required | **Yes — mandatory** | Stellite-faced, tortuous path |
| Sizing ratio | 5.10/8 = 0.64 | OK |
| Valve body | Angle (for erosive service) | Cast stainless |

**Engineering note:** The 4 bar ΔP "wasted" (ΔP_available − ΔP_eff = 32 − 28 = 4 bar) is real energy that cannot be usefully employed to push flow through the valve — it is absorbed by the choked cavitation process. This is a strong argument for staging: two valves in series, each taking ~16 bar of ΔP, will each operate at σ >> σ_incipient and completely avoid cavitation.

---

### Case Study 5 — Cooling Water Control Valve (Liquid, Large Bore, Butterfly)

**Service:** Cooling water supply to heat exchanger, modulating control

**Process data:**

| Parameter | Value |
|---|---|
| Fluid | Cooling water (return from tower) |
| Inlet pressure P1 | 6 bar a |
| Outlet pressure P2 | 4 bar a |
| Temperature T1 | 28°C |
| Gf | 0.996 |
| Pv | 0.037 bar a |
| Pc | 220.64 bar a |
| Viscosity μ | 0.83 cP |
| Flow (design) | 800 m³/h |
| Valve type | Butterfly (high performance) |
| FL | 0.55 |
| Pipe ID | 387.4 mm (16" Sch STD) |
| Valve bore d | 355.6 mm (14" bore) |

**Step 1: FF and ΔP_max**
$$F_F = 0.96 - 0.28\sqrt{\frac{0.037}{220.64}} = 0.96 - 0.28 \times 0.01295 = 0.957$$
$$\Delta P_{\max} = 0.55^2 \times (6 - 0.957 \times 0.037) = 0.3025 \times 5.965 = 1.804 \text{ bar}$$

Available ΔP = 2 bar > ΔP_max = 1.804 bar → **marginally choked**

$$\Delta P_{\text{eff}} = 1.804 \text{ bar}$$

*Note: Low FL of the butterfly valve makes it susceptible to choked flow even at moderate ΔP!*

**Step 2: Piping correction**
d = 355.6 mm, D = 387.4 mm (16" pipe); d/D = 0.918 — nearly same bore, small correction

$$K_1 = 0.5\left(1 - 0.918^2\right)^2 = 0.5\left(1 - 0.843\right)^2 = 0.5 \times 0.0247 = 0.0123$$
$$K_2 = 0.0247; \quad \Sigma K = 0.0370$$

Rough Cv: ≈ 800 / (0.865 × √(1.804/0.996)) = 800 / (0.865 × 1.346) = 686

Fp: term = (0.037/0.00214) × (686/355.6²)² = 17.3 × (5.424×10⁻³)² = 17.3 × 2.942×10⁻⁵ = 5.09×10⁻⁴
Fp ≈ 1.000 (negligible — large bore, same-bore installation)

**Step 3: Cv**
$$C_v = \frac{800}{0.865 \times 1.0 \times 1.0 \times \sqrt{1.804/0.996}} = \frac{800}{0.865 \times 1.346} = \frac{800}{1.164} = \mathbf{687}$$

**Step 4: Cavitation check**
$$P_{vc} = 6 - \frac{1.804}{0.55^2} = 6 - 5.96 = 0.04 \text{ bar a}$$
$$P_{vc} = 0.04 < P_v = 0.037 \text{ bar a} \quad \approx \text{On the cavitation boundary!}$$

σ = (6 − 0.037) / 2.0 = 2.98; σ_incipient = 1/0.55² = 3.31

σ = 2.98 < σ_incipient = 3.31 → **Incipient cavitation**

*The butterfly's low FL makes it vulnerable even in what appears to be a gentle cooling water service.*

**Sizing summary:**

| Parameter | Value |
|---|---|
| Cv required | 687 |
| Cv with 10% margin | 756 |
| Recommended rated Cv | **800** (14" HP butterfly fully open) |
| Cavitation | Incipient — monitor closely |
| Recommended action | Consider globe or HP butterfly with higher FL |

*App insight: The Sensitivity tab would show that a ΔP change of +0.2 bar takes the service into Constant Cavitation. This highlights the importance of range-checking across all operating conditions.*

---

### Case Study 6 — Hydrogen Service (Gas, Low MW, High Velocity)

**Service:** Hydrogen compressor bypass / surge control

**Process data:**

| Parameter | Value |
|---|---|
| Gas | Hydrogen (H₂) |
| M | 2.016 g/mol |
| γ | 1.41 |
| Z | 1.001 |
| P1 | 50 bar a |
| P2 | 45 bar a |
| T1 | 80°C = 353.15 K |
| W | 2000 kg/h |
| xT | 0.72 |

**Step 1: Gas density**
$$\rho_1 = \frac{50 \times 10^5 \times 0.002016}{8.31446 \times 353.15 \times 1.001} = \frac{10080}{2938.5} = 3.43 \text{ kg/m}^3$$

**Step 2: Fk and x check**
$$F_k = \frac{1.41}{1.40} = 1.007$$
$$x = \frac{50 - 45}{50} = 0.100$$
$$x_{\text{choked}} = 1.007 \times 0.72 = 0.725 \gg 0.100 \quad \Rightarrow \text{Subcritical}$$

**Step 3: Y factor**
$$Y = 1 - \frac{0.100}{3 \times 1.007 \times 0.72} = 1 - \frac{0.100}{2.175} = 1 - 0.046 = 0.954$$

**Step 4: Cv**
$$C_v = \frac{2000}{27.3 \times 1.0 \times 0.954 \times \sqrt{0.100 \times 50 \times 3.43}}$$
$$= \frac{2000}{27.3 \times 0.954 \times \sqrt{17.15}} = \frac{2000}{27.3 \times 0.954 \times 4.142}$$
$$= \frac{2000}{107.9} = \mathbf{18.5}$$

**Key note on hydrogen:** The very low molecular weight means:
1. **High velocity** — even at low mass flow, volumetric flow is very high. Check outlet velocity.
2. **High speed of sound** — c = √(γRT/M) ≈ √(1.41×8314×353.15/2.016) ≈ 1432 m/s. Much higher than air (343 m/s).
3. **Material compatibility** — hydrogen embrittlement of high-strength steels. Body: SS 316L or Duplex; gaskets: PTFE-encapsulated; no copper alloys.
4. **Fire and explosion risk** — leak detection, area classification, and ATEX-compliant instrumentation.

---

## 17. Standards Reference

### 17.1 Primary Sizing Standards

**IEC 60534-2-1:2011 — Industrial-process control valves — Part 2-1: Flow capacity — Sizing equations for fluid flow under installed conditions**
- The governing international standard for control valve sizing
- Defines Cv equations for liquid (turbulent, viscous, choked), gas (subcritical, choked), and steam
- Defines N-factor tables for SI and US customary units
- Annex A: Fitting loss coefficients K1, K2
- Annex B: Examples
- Annex C: Fp iteration procedure
- Annex D: Viscosity correction FR (valve Reynolds number)

**ANSI/ISA-75.01.01-2012 — Flow Equations for Sizing Control Valves**
- North American equivalent of IEC 60534-2-1
- Identical equations; US customary N-factors
- Includes the same worked examples for cross-validation
- Referenced by most North American engineering specifications and data sheets

### 17.2 Noise Standards

**IEC 60534-8-3:2011 — Noise considerations — Part 8-3: Control valve aerodynamic noise prediction method**
- Gas and steam service noise prediction
- Baumann (1987) acoustic efficiency correlation for η_a
- Mechanical stream power Wm calculation
- Pipe wall transmission loss TL
- A-weighted external SPL Lpe

**IEC 60534-8-4:2015 — Noise considerations — Part 8-4: Prediction of noise generated by hydrodynamic flow**
- Liquid service noise prediction
- Five cavitation regime SPL equations
- Coupling between cavitation intensity and noise level
- Test method for measuring hydrodynamic noise

### 17.3 Cavitation Standards

**ANSI/ISA-75.23-1995 — Considerations for Evaluating Control Valve Cavitation**
- Engineering guidance (not a test standard) on evaluating cavitation severity
- Sigma (σ) index framework
- Service life estimation
- Anti-cavitation trim selection criteria

### 17.4 Flow Characteristics

**IEC 60534-2-4:2009 — Inherent flow characteristics and rangeability**
- Defines equal-percentage, linear, and quick-opening characteristics mathematically
- Defines rangeability R
- Test method for characterising valves in the laboratory

### 17.5 Leakage Standards

**ANSI/FCI 70-2-2006 / IEC 60534-4:2006 — Control valve seat leakage**
- Defines leakage Classes I through VI
- Specifies test fluid, test pressure, and maximum allowable leakage for each class
- Class V test: water at rated ΔP (up to 50 bar)
- Class VI test: air or nitrogen at 3.5 bar g (50 psig)

### 17.6 Pressure-Temperature Ratings

**ASME B16.34-2017 — Valves — Flanged, Threaded and Welding End**
- Pressure-temperature rating tables for carbon steel, stainless steel, and alloy materials
- Defines ANSI Classes 150, 300, 600, 900, 1500, 2500
- Special Class ratings for fully radiographed bodies

**ASME B16.5-2017 — Pipe Flanges and Flanged Fittings**
- Flange pressure-temperature ratings
- Flange face types: RF (raised face), RTJ (ring joint), FF (flat face)
- Referenced for end connection specification

### 17.7 Pipe Schedules

**ASME B36.10M-2018 — Welded and Seamless Wrought Steel Pipe**
- Wall thickness and internal diameter tables for NPS ½" through 80"
- Defines nominal pipe schedules: 10, 20, 30, 40, 60, 80, 100, 120, 140, 160
- Defines STD (standard = 3/8" wall for NPS ≥ 12") and XH (extra heavy = 1/2" wall for NPS ≥ 12")

**ASME B36.19M-2018 — Stainless Steel Pipe**
- Defines Sch 10S, 40S, 80S for stainless steel pipe
- Thinner walls than B36.10M for same nominal size

### 17.8 Industrial Good Practice

**API RP 553 — Refinery Valves and Accessories for Control Service**
- Sizing ratio recommendations (Cv_req/Cv_rated ≤ 0.85)
- Operating range (20–80% of rated travel)
- Velocity limits in inlet and outlet piping
- Valve selection guidance for refinery service

**API RP 554 — Process Instrumentation and Control**
- General guidance on control valve application in refinery plants
- Fail-safe action philosophy
- SIL considerations for safety valves

**ISA-TR75.17-2003 — Control Valve Aerodynamic Noise Prediction**
- Technical report companion to IEC 60534-8-3
- Extended examples and validation data
- Discusses limitations of the standard method

---

## 18. Glossary

**A-weighting (dB(A)):** A frequency-dependent filter applied to sound pressure level measurements to approximate the frequency response of human hearing. Widely used in occupational noise standards.

**Actuator:** The power device (pneumatic, electric, or hydraulic) that moves the valve stem in response to a control signal.

**Anti-cavitation trim:** Valve trim designed with multiple pressure-reducing stages so that cavitation does not occur within the valve. See §9.5.

**Bare stem:** A valve stem configuration without a handwheel or declutchable handwheel. Used where manual override is not required.

**Bench set:** The spring force pre-load adjustment of a pneumatic actuator, determining at what air pressure the valve begins to move and at what pressure it reaches full stroke. Usually expressed as a pressure range, e.g., 0.4–1.2 bar.

**β (valve authority):** The fraction of total system pressure drop that appears across the valve at design flow. β = ΔP_valve / ΔP_system. See Eq. 11.5.

**Cv:** Flow coefficient — the flow in US GPM of water at 60°F through the valve at 1 psi differential. The primary sizing parameter. See §3.

**Cavitation:** The formation and violent collapse of vapour bubbles in a liquid flow when local pressure falls below and then recovers above the vapour pressure. See §9.

**Choked flow:** The condition where increasing the pressure differential across the valve does not increase the mass flow rate. In liquid service: caused by vapour formation at the vena contracta. In gas service: caused by sonic conditions (Mach = 1) at the vena contracta.

**Control loop:** A feedback control system consisting of a sensor, transmitter, controller, and final control element (the control valve). The valve is the "muscle" of the loop.

**Critical pressure Pc:** The pressure above which gas and liquid phases are indistinguishable (supercritical fluid). Used in the FF formula. See Eq. 5.1.

**dB(A):** Decibels with A-weighting. See A-weighting.

**Equal-percentage characteristic:** An inherent valve characteristic where a fixed change in valve travel produces a fixed percentage change in Cv. The most common characteristic for process control. See Eq. 11.1.

**Expansion factor Y:** A factor (0.667 ≤ Y ≤ 1.0) that corrects the Cv equation for gas compressibility and density change during expansion. Y = 1.0 at zero ΔP; Y = 0.667 at choked flow. See Eq. 6.5.

**Fail-closed (FC):** A valve that returns to the fully closed position on loss of actuating medium (air or power). Also: Air-to-open (ATO). See §14.4.

**Fail-open (FO):** A valve that returns to the fully open position on loss of actuating medium. Also: Air-to-close (ATC). See §14.4.

**FF (Critical pressure ratio factor):** A factor (typically 0.70–0.96) that accounts for vapour formation effects in liquid choked flow. See Eq. 5.1.

**Fd (Valve style modifier):** The ratio of the hydraulic jet diameter to the valve bore diameter. Used in Reynolds number calculation (Eq. 5.7) and aerodynamic noise prediction (Eq. 10.6).

**FL (Liquid pressure recovery factor):** A valve-specific parameter (0 < FL ≤ 1.0) that characterises the degree of pressure recovery between the vena contracta and the valve outlet. See §2.3.

**FLP (Combined factor):** The product of the piping-corrected FL and Fp for liquid choked flow conditions. See Eq. 8.5.

**Fk (Specific heat ratio factor):** The ratio of the gas specific heat ratio γ to 1.4 (reference for air). See Eq. 6.2.

**Fp (Piping geometry factor):** A correction factor (0 < Fp ≤ 1.0) accounting for the additional restriction of pipe reducers and expanders upstream and downstream of the valve. See Eq. 8.4.

**FR (Viscosity correction factor):** A correction factor (0 < FR ≤ 1.0) applied when flow through the valve is not fully turbulent. FR < 1 means the Cv requirement is higher than the turbulent prediction. See §5.5.

**Gf (Specific gravity):** The density of the process liquid relative to water at 15.6°C (60°F). Dimensionless.

**Globe valve:** A linear-motion control valve with a disc (plug) that moves perpendicularly to the flow stream seat. The most common body style for process control. See §1.3.

**Hydrodynamic noise:** Noise generated by turbulence and bubble collapse in liquid-service control valves. Governed by IEC 60534-8-4.

**IAPWS-IF97:** International Association for the Properties of Water and Steam — Industrial Formulation 1997. The international standard for steam and water thermodynamic properties. Implemented in the app via the `iapws` Python library. See §7.2.

**Inherent characteristic:** The relationship between valve opening and Cv measured at constant ΔP in a laboratory test. See §11.1.

**Installed characteristic:** The relationship between valve opening and flow in an actual piping system where ΔP varies with flow. See §11.1.

**K1, K2 (Fitting loss coefficients):** Dimensionless coefficients characterising the additional pressure loss of inlet reducer (K1) and outlet expander (K2) relative to an equivalent length of straight pipe. See Eqs. 8.1 and 8.2.

**Kv:** Metric flow coefficient — the flow in m³/h of water through the valve at 1 bar differential. Kv = 0.8646 × Cv. See §3.2.

**Leakage class:** The maximum allowable seat leakage when the valve is fully closed, per ANSI/FCI 70-2. Classes I through VI. See §12.4.

**Linear characteristic:** An inherent valve characteristic where Cv increases linearly with valve travel. See Eq. 11.2.

**Lpe:** External sound pressure level at 1 metre from the pipe, A-weighted, measured in dB(A). The primary output of the noise prediction calculation. See Eq. 10.8.

**Lpi:** Internal sound power level at the pipe wall, in dB re 1 pW. See Eq. 10.5.

**Mvc (Vena contracta Mach number):** The Mach number at the vena contracta. Mvc = 1.0 for choked (sonic) gas flow. Key parameter in aerodynamic noise prediction. See Eq. 10.2.

**N-factors:** Numerical constants that absorb unit conversions in the IEC 60534-2-1 sizing equations, allowing the same equation form to be used with SI or US customary units. See §4.

**Noise limit:** The maximum allowable sound pressure level at a specified distance, set by site or regulatory requirements. Typically 85 dB(A) at 1 m. Configurable in the app.

**NPSHR/NPSHA (Cavitation):** Net Positive Suction Head Required/Available — primarily a pump concept, but the same physics (vapour pressure margin) governs valve cavitation.

**Positioner:** A high-gain controller mounted on the valve actuator that precisely positions the valve stem in response to the control signal, compensating for friction, hysteresis, and dead band.

**Pv (Vapour pressure):** The absolute pressure at which a liquid begins to vaporise at a given temperature. A key input for cavitation analysis.

**Quick-opening characteristic:** An inherent valve characteristic where Cv increases rapidly at low openings. Poor rangeability. Used for on/off applications. See Eq. 11.3.

**R (Rangeability):** The ratio of maximum to minimum controllable Cv at rated conditions. Typically 50:1 for globe valves, 25:1 for rotary valves. See Eq. 11.7.

**Rev (Valve Reynolds number):** A dimensionless parameter that quantifies whether flow through the valve is turbulent or viscous. See Eq. 5.7.

**Sizing margin:** An engineering safety factor added to the calculated Cv to account for uncertainty in process data and future expansion. Default 10% in the app. See Eq. 3.5.

**Sizing ratio:** The ratio of required Cv to rated Cv (Cv_required / Cv_rated). Should be ≤ 0.85 per API RP 553.

**SPL:** Sound Pressure Level — the logarithmic measure of sound pressure relative to a reference (20 μPa in air). Expressed in decibels (dB) or dB(A) when A-weighted.

**Stellite:** A family of cobalt-chromium-tungsten alloys with exceptional hardness (HRC 45–55) and wear resistance. Used for valve seat and plug hard-facing in cavitating, erosive, or high-temperature service.

**TL (Transmission Loss):** The attenuation of internal sound as it passes through the pipe wall to the outside. A function of pipe material, wall thickness, and sound frequency. See Eq. 10.7.

**Trim:** The internal wetted components of a control valve (plug, seat ring, cage, stem) that control the flow characteristic, capacity, and shutoff class.

**Turndown:** The ratio of maximum to minimum controllable flow in an actual piping system. See §12.1.

**Vena contracta:** The point of minimum cross-sectional area and minimum pressure in a fluid jet downstream of a restriction. Latin for "contracted vein." See §2.2.

**Wm (Mechanical stream power):** The kinetic energy per unit time in the gas stream after expansion through the valve, available for conversion to acoustic energy. See Eq. 10.1.

**x (Pressure drop ratio, gas):** The ratio of valve ΔP to inlet absolute pressure. x = (P1−P2)/P1. See Eq. 6.1.

**xT (Pressure drop ratio factor):** The value of x at which gas flow becomes choked (sonic) without upstream/downstream piping. See Eq. 2.5.

**xTP (Pressure drop ratio with piping):** The value of x at which gas flow becomes choked when pipe reducers are present. xTP ≤ xT. See Eq. 8.6.

**Y (Gas expansion factor):** See Expansion factor Y.

**Z (Compressibility factor):** A dimensionless factor that corrects the ideal gas law for real gas behaviour. Z = 1.0 for ideal gas; Z < 1.0 for most gases at elevated pressure. See Eq. 6.12.

---

## Appendix A: Quick Reference — Sizing Equation Summary

### Liquid Service (IEC 60534-2-1 §5.2)

$$F_F = 0.96 - 0.28\sqrt{\frac{P_v}{P_c}} \quad \text{(A.1)}$$

$$\Delta P_{\max} = \left(\frac{F_{LP}}{F_p}\right)^2(P_1 - F_F P_v) \quad \text{(A.2)}$$

$$\Delta P_{\text{eff}} = \min(\Delta P, \Delta P_{\max}) \quad \text{(A.3)}$$

$$C_v = \frac{Q}{N_1 \cdot F_p \cdot F_R \cdot \sqrt{\Delta P_{\text{eff}}/G_f}} \quad \text{(A.4)}$$

### Gas Service (IEC 60534-2-1 §5.3)

$$F_k = \gamma / 1.4 \quad \text{(A.5)}$$

$$x_{\text{eff}} = \min\left(\frac{\Delta P}{P_1},\, F_k \cdot x_{TP}\right) \quad \text{(A.6)}$$

$$Y = \max\left(1 - \frac{x_{\text{eff}}}{3 F_k x_{TP}},\, 0.667\right) \quad \text{(A.7)}$$

$$C_v = \frac{W}{N_6 \cdot F_p \cdot Y \cdot \sqrt{x_{\text{eff}} \cdot P_1 \cdot \rho_1}} \quad \text{(A.8)}$$

### Piping Corrections (IEC 60534-2-1 §6)

$$K_1 = 0.5\left(1 - d^2/D_1^2\right)^2, \quad K_2 = \left(1 - d^2/D_2^2\right)^2 \quad \text{(A.9)}$$

$$F_p = \frac{1}{\sqrt{1 + (\Sigma K / N_2)(C_v/d^2)^2}} \quad \text{(A.10)}$$

$$F_{LP} = \frac{F_L}{\sqrt{1 + (F_L^2 K_1 / N_2)(C_v/d^2)^2}} \quad \text{(A.11)}$$

$$x_{TP} = \frac{x_T}{F_p^2\left[1 + (x_T K_1/N_5)(C_v/d^2)^2\right]} \quad \text{(A.12)}$$

### Aerodynamic Noise (IEC 60534-8-3)

$$W_m = \dot{m} \cdot \frac{\gamma}{\gamma-1} \cdot \frac{P_1}{\rho_1}\left[1 - (P_{2,\text{eff}}/P_1)^{(\gamma-1)/\gamma}\right] \quad \text{(A.13)}$$

$$\eta_a = \begin{cases} 10^{-4} M_{vc}^{3.6} & M_{vc} \leq 0.3 \\ 10^{-4}(0.3)^{3.6}(M_{vc}/0.3) & M_{vc} > 0.3 \end{cases} \quad \text{(A.14)}$$

$$L_{pi} = 10\log_{10}(\eta_a W_m / 10^{-12}) \quad \text{(A.15)}$$

$$L_{pe} = L_{pi} - TL + A(f_p) \quad \text{(A.16)}$$

---

## Appendix B: N-Factor Quick Reference

| Factor | SI (bar) | US | Used In |
|---|---|---|---|
| N1 | 0.865 | 1.00 | Liquid Cv (volumetric) |
| N2 | 0.00214 | 890.0 | Fp, FLP piping |
| N4 | 334 620 | 76 000 | Valve Reynolds number |
| N5 | 0.00241 | 1000.0 | xTP piping |
| N6 | 27.3 | 63.3 | Gas Cv (mass flow) |
| N7 | 417.0 | 1360.0 | Gas Cv (standard volumetric) |
| N8 | 94.8 | 19.3 | Gas Cv (molecular weight) |
| N9 | 2120.0 | 7320.0 | Gas Cv (Nm³/h with T, Z) |

---

## Appendix C: App Feature Map

| Chapter / Topic | App Tab / Panel |
|---|---|
| Process inputs, fluid properties | **Inputs** — Process Conditions + Fluid Properties |
| Cv, Kv, sizing ratio, opening % | **Results** — Primary Sizing Results |
| Cavitation analysis | **Results** — Cavitation tab |
| Noise prediction (IEC 8-3/8-4) | **Noise Analysis** tab |
| Piping Fp, FLP, xTP | **Results** — Piping Corrections section |
| Inherent vs. installed curves | **Installed Characteristic** tab |
| Sensitivity / what-if sweep | **Sensitivity Analysis** tab |
| Rangeability, turndown | **Rangeability** tab |
| Actuator sizing guidance | **Actuator Sizing** tab |
| Valve body/trim recommendation | **Valve Selection** tab |
| Save calculation to JSON | **Save / Load** tab |
| Multi-case comparison | **Comparison** tab |
| PDF / Excel report | **Results** → Download Report |
| Fluid library presets (60+) | **Inputs** → Fluid Preset dropdown |
| Engineering warnings | **Results** → Warnings panel (auto) |

---

## Appendix D: Typical Fluid Property Data

| Fluid | Phase | Gf | Pv (bar a, 20°C) | Pc (bar a) | μ (cP) | M (g/mol) | γ |
|---|---|---|---|---|---|---|---|
| Water | L | 0.998 | 0.023 | 220.64 | 1.002 | 18.02 | — |
| Boiler feed water (145°C) | L | 0.921 | 3.69 | 220.64 | 0.20 | 18.02 | — |
| Light crude oil | L | 0.850 | 0.05 | 22.1 | 10 | — | — |
| Diesel | L | 0.845 | 0.001 | 23.5 | 3.2 | 170 | — |
| Propane (liquid) | L | 0.508 | 8.45 | 42.5 | 0.11 | 44.1 | — |
| Air | G | — | — | 37.7 | 0.018 | 28.97 | 1.40 |
| Nitrogen | G | — | — | 33.9 | 0.018 | 28.01 | 1.40 |
| Natural gas (typical) | G | — | — | — | 0.012 | 17.5 | 1.27 |
| Hydrogen | G | — | — | 13.1 | 0.009 | 2.016 | 1.41 |
| CO₂ | G | — | — | 73.8 | 0.015 | 44.01 | 1.30 |
| Steam (superheated, 10 bar, 250°C) | V | — | — | 220.64 | 0.016 | 18.02 | 1.33 |
| Ammonia | L/G | 0.610 | 8.57 | 113.5 | 0.23 | 17.03 | 1.31 |

---

## Appendix E: Recommended Reading and References

1. **IEC 60534-2-1:2011** — Primary sizing equations. Available from IEC.ch.
2. **ANSI/ISA-75.01.01-2012** — US equivalent. Available from ISA.org.
3. **IEC 60534-8-3:2011** — Aerodynamic noise. Available from IEC.ch.
4. **IEC 60534-8-4:2015** — Hydrodynamic noise. Available from IEC.ch.
5. **Driskell, L.R. (1983)** — *Control Valve Selection and Sizing*. ISA Press. The foundational engineering text for practitioners.
6. **Baumann, H.D. (1987)** — "A method for predicting aerodynamic valve noise based on modified free jet theories." ASME Paper 87-WA/NCA-7. Source of the Mach-dependent η_a correlation.
7. **Fisher Controls (Emerson) — Control Valve Handbook, 5th Edition (2019).** Freely available at emerson.com. Comprehensive practical reference.
8. **Masoneilan — Handbook for Control Valve Sizing, 10th Edition.** Available from Baker Hughes. Includes worked examples in both unit systems.
9. **Crane TP-410 — Flow of Fluids Through Valves, Fittings, and Pipe.** Classic reference for pipe fitting losses (K1, K2 values).
10. **API RP 553 — Refinery Valves and Accessories for Control Service.** Available from API.org.
11. **ASME B36.10M-2018** — Pipe schedule dimensions. Available from ASME.org.
12. **IAPWS-IF97 (2012)** — *Revised Release on the IAPWS Industrial Formulation 1997 for the Thermodynamic Properties of Water and Steam.* Available at iapws.org. Implemented in the app via the `iapws` Python library.
13. **ISA-TR75.17-2003** — Control Valve Aerodynamic Noise Prediction. Technical report. Available from ISA.org.

---

*End of handbook*

---

**Document information:**

| Field | Value |
|---|---|
| Title | Control Valve Engineering Handbook |
| Subtitle | Complete Technical Reference for Sizing, Selection, and Analysis |
| Companion application | Control Valve Sizer v2.0 |
| Standards basis | IEC 60534-2-1:2011, ANSI/ISA-75.01.01-2012, IEC 60534-8-3:2011, IEC 60534-8-4:2015, IEC 60534-4:2006, IAPWS-IF97, ASME B36.10M, API RP 553 |
| Equation count | 80+ numbered equations |
| Case studies | 6 complete worked examples |
| Glossary entries | 55+ technical terms |
| Scope | Liquid, gas, steam; turbulent, viscous, choked, cavitating, flashing; noise; actuators; installed characteristic; sensitivity |
