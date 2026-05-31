"""
frontend/ui_user_guide.py  — In-App Step-by-Step User Guide
"""
from __future__ import annotations
import streamlit as st
from frontend.ui_styles import DEVELOPER_NAME, GITHUB_URL, LINKEDIN_URL, section_header_html


def render_user_guide() -> None:
    st.markdown("## 📖 User Guide — Control Valve Sizer v2.0")
    st.markdown(
        f"*By [{DEVELOPER_NAME}]({LINKEDIN_URL}) | "
        f"[GitHub Repository]({GITHUB_URL})*"
    )

    st.info(
        "This guide walks you through every feature of the Control Valve Sizer. "
        "Use the expanders below to navigate to the topic you need."
    )

    # ── QUICK START ───────────────────────────────────────────────────────────
    with st.expander("🚀 Quick Start — 5 Steps to Your First Sizing", expanded=True):
        st.markdown(
            """
            1. **Select Unit System** (SI or US) in the sidebar — left-hand panel.
            2. **Select Fluid Phase** (Liquid / Gas / Steam) in the sidebar.
            3. Go to **📋 Process Inputs** tab:
               - Enter P1, P2, T1, and flow rate
               - Select or enter fluid properties (use the **Fluid Library** dropdown for auto-fill)
               - Enter valve bore d, pipe IDs D1/D2, and FL/xT/Fd
            4. Click **🔬 CALCULATE** in the sidebar.
            5. Review results in the **📊 Sizing Results**, **🔊 Noise Analysis**, and **⚠ Warnings** tabs.

            *That's it. The calculation follows IEC 60534-2-1:2011 and ISA-75.01.01-2012 automatically.*
            """
        )

    # ── INPUTS GUIDE ─────────────────────────────────────────────────────────
    with st.expander("📋 Process Inputs — Detailed Field Guide"):
        st.markdown(
            """
            ### Instrument Identification
            | Field | Description |
            |---|---|
            | Tag Number | Instrument tag (e.g. FV-101). Appears in reports. |
            | Case Name | Description (e.g. "Normal Flow", "Max Flow"). |

            ### Process Conditions
            | Field | Convention | Example |
            |---|---|---|
            | P1 | **Gauge** pressure (atmospheric added automatically) | 10.0 bar g |
            | P2 | **Gauge** pressure, must be < P1 | 8.0 bar g |
            | T1 | Inlet temperature (°C for SI, °F for US) | 20 °C |
            | Flow Rate | In selected flow basis units | 100 m³/h |
            | Flow Basis | Volumetric / Mass / Standard | Volumetric |

            ### Fluid Library (v2.0 New)
            Select a fluid from the dropdown to **auto-populate** all fluid properties.
            60+ fluids across 6 categories:
            - **Utilities**: Water, Air, N₂, CO₂, H₂, Cooling Water…
            - **Hydrocarbons (Liquid)**: Crude Oil, Diesel, Propane, LPG, Benzene…
            - **Hydrocarbons (Gas)**: Natural Gas, Methane, Ethane, Propane Gas…
            - **Refrigerants**: R-134a, R-410A, R-22, Ammonia…
            - **Cryogenics**: LN₂, LOX, LNG, Liquid Argon…
            - **Process Chemicals**: H₂SO₄, HCl, NaOH, Methanol, Chlorine, VCM…

            > ⚠ Always verify preset properties against your process conditions — presets are at reference temperature.

            ### Valve Parameters
            | Field | Description | Typical Range |
            |---|---|---|
            | Valve Type | Select from preset list to auto-fill FL/xT/Fd | Globe, Ball, Butterfly… |
            | FL | Liquid pressure recovery factor | 0.50 (butterfly) – 0.90 (globe) |
            | xT | Terminal pressure drop ratio (gas choked flow) | 0.25 – 0.75 |
            | Fd | Valve style modifier (noise, Reynolds correction) | 0.42 – 1.00 |
            | d | Valve bore [mm or inches] | |
            | D1 / D2 | Upstream / downstream pipe internal diameter | |
            | Rated Cv | Manufacturer's Cv at 100% travel (optional) | |
            | β (System ΔP Fraction) | Valve ΔP / Total system ΔP at design flow | 0.25–1.0 |
            """
        )

    # ── SIZING RESULTS ────────────────────────────────────────────────────────
    with st.expander("📊 Sizing Results — How to Read the Output"):
        st.markdown(
            """
            ### Primary Metrics
            | Metric | Definition | Guidance |
            |---|---|---|
            | **Cv Required** | Flow coefficient at design conditions | Size valve with Cv_rated ≥ Cv_req × (1 + margin/100) |
            | **Kv Required** | Kv = Cv × 0.8646 | Use for valves specified in Kv |
            | **Sizing Ratio** | Cv_req / Cv_rated | Ideal: 0.6–0.8. Max: 0.85 per API RP 553 |
            | **Opening %** | Estimated travel from inherent characteristic | Good control range: 20–80% |

            ### Flow Regimes
            - **Turbulent**: Normal operating regime — equations apply directly.
            - **Laminar/Viscous**: Viscosity correction FR applied. Check FR value.
            - **Choked**: Maximum flow reached — increasing ΔP does not increase flow.
            - **Flashing**: P2 < Pv — two-phase flow. Erosion risk.

            ### Cavitation Assessment (Liquid)
            Five-tier classification (IEC 60534-8-4):

            | Regime | σ vs σ_thresholds | Action |
            |---|---|---|
            | None | σ >> σ_incipient | No action |
            | Incipient | σ near σ_incipient | Monitor; low damage risk |
            | Constant | σ_incipient > σ > σ_mv | Consider anti-cav trim |
            | Choked | σ ≤ σ_choked | Anti-cav trim required |
            | Flashing | P2 ≤ Pv | Angle body + hardened trim |

            ### Gas Expansion Factor Y (Gas service)
            Y = 1 − x/(3Fk·xT) where x = ΔP/P1. At choked conditions, Y = 0.667.

            ### Piping Correction Fp
            Fp < 1.0 when d < D1 or D2 (reducers present). Fp < 0.95 warrants attention.
            """
        )

    # ── NOISE ────────────────────────────────────────────────────────────────
    with st.expander("🔊 Noise Analysis — Understanding the Results"):
        st.markdown(
            """
            ### Standards Applied
            - **Gas/Steam**: IEC 60534-8-3:2011 (aerodynamic noise)
            - **Liquid**: IEC 60534-8-4:2015 (hydrodynamic noise)

            ### Aerodynamic Noise Chain (v2.0 fixed)
            1. **Wm** — Mechanical stream power from isentropic expansion
            2. **Mvc** — Mach number at vena contracta
            3. **η_a** — Acoustic efficiency (Baumann 1987 correlation — **fixed in v2.0**)
               - Old (incorrect): η_a = constant 10⁻⁴
               - New (correct): η_a = 10⁻⁴ × Mvc³·⁶  (subsonic); sonic-jet extension for Mvc > 0.3
            4. **Wa = η_a × Wm** — Acoustic power
            5. **Lpi** — Internal sound power level [dB re 1pW]
            6. **TL** — Pipe wall transmission loss (depends on schedule/thickness)
            7. **Lpe** — External SPL at 1 m [dB(A)] = Lpi − TL + A-weighting

            ### Noise Reduction Options
            | Excess above limit | Primary action |
            |---|---|
            | < 5 dB(A) | Heavier pipe schedule downstream |
            | 5–10 dB(A) | Anti-noise trim (low-noise cage) |
            | 10–20 dB(A) | Anti-noise trim + acoustic lagging |
            | > 20 dB(A) | Multi-stage let-down + silencer |

            ### Site Noise Limits
            Typical limits (check your project specification):
            - 85 dB(A): occupied work areas
            - 90 dB(A): process areas with limited access
            - 110 dB(A): emergency relief absolute maximum (short-term)
            """
        )

    # ── INSTALLED CHARACTERISTIC ──────────────────────────────────────────────
    with st.expander("📈 Installed Characteristic Curve"):
        st.markdown(
            """
            ### Purpose
            Shows how the valve's actual (installed) flow varies with opening in
            a real piping system, compared to the lab (inherent) characteristic.

            ### Key Parameter: β (Valve Authority)
            β = ΔP_valve / ΔP_total at design flow.

            - **β = 1.0**: All system pressure drop across the valve — installed = inherent.
            - **β = 0.5**: 50% of ΔP across valve — equal-% inherent → near-linear installed.
            - **β < 0.25**: Valve authority too low — installed characteristic severely distorted.

            ### Design Rules (Driskell, ISA)
            | Inherent Char | Recommended β | Result |
            |---|---|---|
            | Equal-percentage | 0.25–0.50 | Near-linear installed |
            | Linear | ≥ 0.70 | Near-linear installed |
            | Quick-opening | ≥ 0.80 | Acceptable control |

            ### Gain Variability
            Installed gain = dq/dθ (sensitivity of flow to valve opening).
            If gain varies more than 4:1 across 20–80% travel, a characterised
            positioner cam or different characteristic is needed.
            """
        )

    # ── SENSITIVITY ───────────────────────────────────────────────────────────
    with st.expander("🔍 Sensitivity / What-If Analysis"):
        st.markdown(
            """
            ### How It Works
            1. Select the **parameter** to sweep (e.g. Upstream Pressure P1).
            2. Set the **sweep range** (±N% around the base case).
            3. Set the number of **steps** (10–40).
            4. Click **▶ Run Sensitivity Analysis**.

            The engine re-runs the full sizing orchestrator at each step and records:
            - Cv Required
            - Sizing Ratio
            - Noise [dB(A)]
            - Cavitation σ

            ### Interpreting the Sensitivity Index
            Sensitivity Index S = |∂Output/∂Input| (normalised, dimensionless).

            | S value | Interpretation |
            |---|---|
            | < 0.5 | Low sensitivity — output barely changes |
            | 0.5–1.5 | Moderate sensitivity |
            | > 1.5 | High sensitivity — small input changes cause large output changes |

            ### Typical Use Cases
            - Check if the valve is still adequate at minimum / maximum flow conditions.
            - Determine how sensitive Cv is to pressure uncertainty.
            - Check if noise exceeds limit across the operating range.
            - Understand cavitation risk at reduced P2.
            """
        )

    # ── RANGEABILITY ─────────────────────────────────────────────────────────
    with st.expander("📊 Rangeability & Turndown Analysis"):
        st.markdown(
            """
            ### Definitions
            - **Rangeability** = Cv_max / Cv_min (inherent, at rated conditions)
            - **Effective Rangeability** = Cv_rated / Cv_min (actual, installed)
            - **Turndown** = Design flow / Minimum controllable flow

            ### Minimum Controllable Cv (typical by valve type)
            | Valve Type | Cv_min / Cv_rated |
            |---|---|
            | Globe (single/cage-guided) | 2% |
            | Angle Body | 2% |
            | Ball Valve | 5% |
            | Butterfly (HP) | 5% |
            | Butterfly (Wafer) | 7% |

            ### Rule of Thumb
            Effective Rangeability ≥ Required Turndown × 1.10 (10% margin).

            ### Leakage Classes (IEC 60534-4:2006)
            | Class | Max Leakage | Typical Use |
            |---|---|---|
            | II | 0.5% of Cv_rated | Standard service |
            | III | 0.1% | Improved shutoff |
            | IV | 0.01% | Soft-seat / tight shutoff |
            | V | 5×10⁻⁴ ml/min·bar·mm | Metal seats, high integrity |
            | VI | Bubble-tight | Safety, isolation |
            """
        )

    # ── ACTUATOR ─────────────────────────────────────────────────────────────
    with st.expander("🔩 Actuator Sizing Guidance"):
        st.markdown(
            """
            ### Forces Calculated (Linear Globe / Angle Valves)
            1. **Unbalanced Force** = π/4 × d_seat² × ΔP_shutoff
            2. **Packing Friction** = empirical (depends on packing type and stem diameter)
            3. **Seat Load** = seat circumference × load factor (per leakage class)
            4. **Required Thrust** = (F_unbal + F_pack + F_seat) × 1.10 contingency

            ### For Pneumatic Diaphragm Actuators
            A_diaphragm = F_req / (P_supply × η_eff)
            η_eff ≈ 0.80 for diaphragm, 0.90 for piston.

            ### For Rotary Valves (Ball, Butterfly, Eccentric)
            T_break ≈ C_T × d_trim³ × ΔP_shutoff
            where C_T is a valve-type specific torque coefficient.

            ### For Electric Actuators
            Motor Power ≈ F_req × v_stem / η_mech
            (assuming 25 mm/s stem speed, 0.65 mechanical efficiency)

            > ⚠ These are **preliminary estimates** for actuator selection only.
            > Final sizing must be confirmed with the manufacturer, including:
            > thermal effects, hysteresis, positioner requirements, and SIL requirements.
            """
        )

    # ── VALVE SELECTION ───────────────────────────────────────────────────────
    with st.expander("🔧 Valve Body & Trim Selection Guide"):
        st.markdown(
            """
            ### Body Style Selection Rules
            | Condition | Recommended Body |
            |---|---|
            | Flashing service | Angle body (directs erosive flow away) |
            | Severe cavitation (choked) | Cage-guided globe with anti-cav trim |
            | High ΔP gas (x > 0.5) + noise | Cage-guided globe |
            | Very high ΔP (x > 0.70) | Multi-stage cage globe |
            | Large bore (d > 300 mm) gas, low noise | High-performance butterfly |
            | Low ΔP liquid (x < 0.20) | Full-bore ball valve |
            | High viscosity (> 50 cP) | Globe (streamlined plug) |
            | Steam service | Globe single-seat with bolted bonnet |
            | General service | Globe single-seat |

            ### Trim Type Selection Rules
            | Condition | Recommended Trim |
            |---|---|
            | Flashing | Stellite hard-faced seats/plug |
            | Severe cavitation | Anti-cavitation (multi-orifice, tortuous path) |
            | Noise > 95 dB(A) | Anti-noise (drilled-hole cage, whisper trim) |
            | High ΔP (x > 0.60) or P1 > 100 bar a | Multi-stage / tortuous path |
            | Noise 85–95 dB(A) | Anti-noise (low-noise cage) |
            | Steam, T > 350 °C | Hard-facing (Stellite 6 / Colmonoy 6) |
            | General service | Contoured parabolic plug |

            ### Material Selection Quick Guide
            | Service | Body Material |
            |---|---|
            | Standard (T < 300 °C, P < 100 bar) | Carbon Steel (ASTM A216 WCB) |
            | High temp steam (300–400 °C) | Alloy Steel (WC6) |
            | Very high temp (> 400 °C) | Alloy Steel (WC9 / C12A) |
            | Low temperature (< -20 °C) | ASTM A352 LCB or 316 SS |
            | Extremely high pressure | Welded end connections (BW) |
            """
        )

    # ── SAVE / LOAD ───────────────────────────────────────────────────────────
    with st.expander("💾 Save & Load Calculations"):
        st.markdown(
            """
            ### Saving a Calculation
            1. Run a successful calculation.
            2. Go to the **💾 Save / Load** tab.
            3. Enter a case name and tag number.
            4. Click **⬇ Download Calculation JSON**.
            5. Save the file in your project folder or calculation register.

            ### Loading a Calculation
            1. Go to the **💾 Save / Load** tab.
            2. Click **📂 Upload** and select a previously saved `.json` file.
            3. Review the file preview, then click **✅ Load This Calculation**.
            4. All inputs and results are restored instantly.

            ### File Format
            The file is a human-readable JSON document conforming to the
            `SavedCalculation` Pydantic v2 schema (version 2). It includes:
            - All input parameters (`SizingInputs` model)
            - All results (`SizingResult` model)
            - Metadata: saved timestamp, app version, case name, tag

            Files are git-trackable and suitable for inclusion in document
            management systems (DMS) as calculation records.
            """
        )

    # ── COMPARISON ────────────────────────────────────────────────────────────
    with st.expander("📊 Multi-Case Comparison Table"):
        st.markdown(
            """
            ### Use Case
            Compare multiple operating scenarios for the same valve — for example:
            - Minimum flow / Normal flow / Maximum flow
            - Design case / Future expansion case
            - Different fluid properties (e.g. with / without diluent)

            ### How to Use
            1. Run the first scenario and click **➕ Add to Comparison**.
            2. Modify inputs for the next scenario (change P1, P2, flow, etc.).
            3. Click **🔬 CALCULATE** again.
            4. Click **➕ Add to Comparison** for the new result.
            5. Repeat for all scenarios.
            6. The table shows all cases side-by-side.

            ### Available Columns
            Tag, Phase, P1, P2, ΔP, Cv Required, Cv Rated, Sizing Ratio,
            Opening %, Noise dB(A), Choked, Flow Regime, Cavitation Regime.

            ### Export
            Download the full comparison as a CSV file for inclusion in
            engineering reports or spreadsheets.
            """
        )

    # ── STANDARDS REFERENCE ───────────────────────────────────────────────────
    with st.expander("📐 Standards Reference"):
        st.markdown(
            """
            | Standard | Scope | Key Equations |
            |---|---|---|
            | **IEC 60534-2-1:2011** | Primary liquid/gas/steam sizing | Cv equations, N-factors, Y, FL, xT, Fp |
            | **ANSI/ISA-75.01.01-2012** | US equivalent, cross-validated | Same N-factors in US units |
            | **IEC 60534-8-3:2011** | Aerodynamic noise (gas/steam) | Wm, η_a, Lpi, TL, Lpe chain |
            | **IEC 60534-8-4:2015** | Hydrodynamic noise (liquid) | Cavitation noise, 5-regime |
            | **IEC 60534-4:2006** | Leakage classification | Classes I–VI |
            | **IAPWS-IF97** | Steam thermodynamic properties | ρ, h, s, μ from P, T |
            | **ASME B16.34-2017** | P-T ratings | Body class selection |
            | **ASME B36.10M** | Pipe schedule dimensions | Wall thickness for noise TL |
            | **API RP 553** | Refinery control valve selection | Sizing margin guidance |

            ### N-Factors (IEC 60534-2-1 Table 1)
            | Factor | SI Value | US Value | Application |
            |---|---|---|---|
            | N1 | 0.0865 | 1.00 | Liquid Cv (m³/h, bar) |
            | N2 | 0.00214 | 890 | Fp piping geometry (mm / in) |
            | N4 | 0.0713 | 76000 | Reynolds number (viscous) |
            | N6 | 2.73 | 63.3 | Gas mass flow (kg/h, bar, kg/m³) |
            | N7 | 4.17 | 1360 | Gas volumetric (m³/h, bar) |
            | N9 | 21.2 | 7320 | Standard volumetric (m³/h, bar, K) |
            """
        )

    # ── TROUBLESHOOTING ───────────────────────────────────────────────────────
    with st.expander("🔧 Troubleshooting Common Issues"):
        st.markdown(
            """
            | Problem | Likely Cause | Solution |
            |---|---|---|
            | "P2 must be less than P1" | Gauge pressures entered incorrectly | Check P1 > P2 (both gauge) |
            | Cv = 0 or very small | ΔP is extremely high relative to flow | Check units; confirm gauge vs absolute |
            | Sizing ratio > 1.0 | Cv_rated too small for the service | Select larger valve or increase Cv_rated |
            | Noise >> limit | High ΔP + large flow | Anti-noise trim, multi-stage, or silencer |
            | "Steam unavailable" | iapws not installed | `pip install iapws==1.5.2` |
            | Fp ≪ 1.0 | Large mismatch between d and D | Check valve bore vs pipe ID; use expanders |
            | Flashing predicted | P2 < vapour pressure | Process review; angle body required |
            | FR correction large | Fluid very viscous (> 50 cP) | Verify viscosity; FR < 0.8 → check with mfr |
            | Opening < 20% | Cv_rated too large (oversized valve) | Select smaller Cv_rated; add trim stage |
            | Opening > 85% | Cv_rated too small (undersized) | Select larger valve |
            | Load failed | Old schema or edited JSON | Re-save from current version (v2.0) |

            ### Still Stuck?
            - Check the **⚠ Warnings** tab for specific engineering flags.
            - Open the **🔍 Detailed Calculation Summary** table in the Results tab.
            - Review input units carefully (gauge vs absolute; SI vs US).
            - File an issue on [GitHub]({github}).
            """.format(github=GITHUB_URL)
        )

    # ── ABOUT ─────────────────────────────────────────────────────────────────
    with st.expander("ℹ About This App"):
        st.markdown(
            f"""
            ### Control Valve Sizer v2.0

            **Developer:** [{DEVELOPER_NAME}]({LINKEDIN_URL})
            **Repository:** [{GITHUB_URL}]({GITHUB_URL})
            **License:** MIT

            This tool implements internationally recognised engineering standards for
            control valve sizing and noise prediction. It is intended as a **professional
            engineering aid** and **does not replace** rigorous project-specific calculations,
            manufacturer data, or qualified engineering review.

            #### Disclaimer
            Results are provided for preliminary engineering guidance only. The developer
            accepts no liability for design decisions made solely on the basis of this tool.
            All results must be reviewed by a qualified instrumentation engineer and validated
            against manufacturer data before use in any engineering specification.

            #### Standards Implemented
            IEC 60534-2-1:2011 | ANSI/ISA-75.01.01-2012 | IEC 60534-8-3:2011 |
            IEC 60534-8-4:2015 | IAPWS-IF97 | ASME B16.34-2017 | API RP 553

            #### Version History
            | Version | Changes |
            |---|---|
            | v2.0.0 | Save/Load, Comparison Table, Installed Characteristic, 60+ Fluid Library, Actuator Guidance, Sensitivity Analysis, Aerodynamic Noise Fix (Baumann η_a), Rangeability Analysis, Valve Selection Guide, LinkedIn branding, User Guide |
            | v1.x | Initial release: Liquid/Gas/Steam sizing, IEC 60534 noise, Warnings, PDF/Excel reports |
            """
        )
