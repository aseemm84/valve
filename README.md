# 🔧 Control Valve Sizer v2.0

**Professional control valve sizing application** implementing international
standards for liquid, gas, and steam service. Built with Python and Streamlit.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32%2B-red)](https://streamlit.io)
[![Standards](https://img.shields.io/badge/standard-IEC%2060534--2--1-green)](https://iec.ch)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Aseem%20Mehrotra-0077B5?logo=linkedin)](https://www.linkedin.com/in/aseem-mehrotra/)

> **Live App:** [control-valve-sizing.streamlit.app](https://control-valve-sizing.streamlit.app/)
> **Developer:** [Aseem Mehrotra](https://www.linkedin.com/in/aseem-mehrotra/)

---

## 📐 Standards Implemented

| Standard | Scope |
|---|---|
| **IEC 60534-2-1:2011** | Primary sizing equations — liquid, gas, steam (turbulent, choked, viscous) |
| **ANSI/ISA-75.01.01-2012** | US equivalent — cross-validated N-factors and worked examples |
| **IEC 60534-8-3:2011** | Aerodynamic noise prediction (gas and steam service) |
| **IEC 60534-8-4:2015** | Hydrodynamic noise prediction (liquid — 5 cavitation regimes) |
| **IEC 60534-4:2006** | Leakage classification (Classes I–VI) |
| **IAPWS-IF97** | Steam/water thermodynamic properties (via `iapws` library) |
| **ASME B16.34-2017** | Pressure-temperature rating check |
| **ASME B36.10M** | Pipe schedule dimensions (for noise transmission loss) |
| **API RP 553** | Sizing margin recommendations and velocity limits |

---

## 🚀 Features

### Core Sizing Engine (v1.x)
- **Fluid phases:** Liquid (all regimes), Gas/Vapour (subcritical + choked), Superheated / Saturated / Wet Steam
- **Flow conditions:** Turbulent, Laminar/Viscous (FR correction), Choked, Cavitating (5-tier), Flashing
- **Piping corrections:** Fp, FLP, xTP for reducers/expanders (iterative IEC solver)
- **Noise prediction:** Full IEC 60534-8-3 and 8-4 calculation chains with A-weighting
- **Unit systems:** SI (bar, m³/h, mm, °C) and US Customary (psi, GPM, in, °F)
- **Interactive charts:** Cv characteristic, pressure profiles, cavitation maps, noise gauges
- **Reports:** Downloadable PDF and Excel engineering calculation sheets
- **Validation:** Hard constraint checks + soft engineering warnings

### New in v2.0 (11 features)

#### 1. 💾 Save & Load Calculations
Save any calculation to a portable, human-readable **JSON file** (Pydantic v2 schema v2).
Reload any saved file to restore all inputs and results instantly. Files are git-trackable
and suitable for calculation registers and document management systems.

#### 2. 🗂 Multi-Case Comparison Table
Run multiple operating scenarios (min/normal/max flow, different fluids, future expansion)
and add each to an interactive **side-by-side comparison table**. Export to CSV.

#### 3. 📈 Installed Characteristic Curve
Plot both the **inherent** (lab, constant ΔP) and **installed** (real system, variable ΔP)
flow characteristic curves. Adjustable valve authority β slider. Controllability assessment
with gain variability analysis. Background theory expander (Driskell/ISA-75.11.01).

#### 4. 📋 Fluid Library (60+ Fluids)
Dropdown preset selector with **60+ common process fluids** across 6 categories:
- **Utilities:** Water, Air, N₂, CO₂, O₂, H₂, Steam, Cooling Water, Brine, Glycol
- **Hydrocarbons (Liquid):** Crude Oil, Diesel, Propane, LNG, Benzene, Toluene, Xylene, MEG…
- **Hydrocarbons (Gas):** Natural Gas, Methane, Ethane, Propane Gas, Butane, H₂S…
- **Refrigerants:** R-134a, R-410A, R-22, Ammonia, CO₂ (R-744)
- **Cryogenics:** LN₂, LOX, LNG, Liquid Argon
- **Process Chemicals:** H₂SO₄, HCl, NaOH, Methanol, Chlorine, VCM, Phosgene…

Auto-populates all fluid property fields; user can override any value.

#### 5. 🔩 Actuator Sizing Guidance
Preliminary actuator sizing for **linear** (globe/angle) and **rotary** (ball/butterfly) valves:
- Unbalanced stem force, packing friction, seat load calculation
- Required thrust/torque with 10% engineering contingency
- Pneumatic diaphragm area and spring range estimation
- Electric motor power and standard motor kW recommendation
- Fail-safe action analysis (FO/FC) with supply pressure sensitivity

#### 6. 🔍 Sensitivity / What-If Analysis
Parametric sweep engine: vary any one input ±N% in configurable steps and track:
- Cv required, Sizing ratio, Noise [dB(A)], Cavitation σ
- Normalised **sensitivity index** (|∂Output/∂Input|) for each output
- **Tornado chart** and **line charts** for visual analysis
- Full data table download

Swept parameters: P1, P2, T1, Flow Rate, Gf/M, Viscosity, FL, xT.

#### 7. 🔊 Aerodynamic Noise Fix (Acoustic Efficiency η_a)
**Critical correction** to the IEC 60534-8-3 calculation chain:

| | v1.x (incorrect) | v2.0 (correct) |
|---|---|---|
| Acoustic efficiency η_a | Constant 10⁻⁴ | Mach-dependent: η_a = 10⁻⁴ × Mvc³·⁶ (Baumann 1987) |
| Validity | Overestimates at low Mvc, underestimates at high Mvc | Full Mvc range; sonic-jet extension for Mvc > 0.3 |

This fix affects all gas and steam noise predictions, particularly at high ΔP ratios.

#### 8. 📉 Rangeability & Turndown Analysis
- Effective rangeability = Cv_rated / Cv_min (by valve type)
- Required turndown from design vs minimum flow conditions
- Adequacy check with 10% engineering margin
- **Leakage class recommendation** (IEC 60534-4:2006 Classes I–VI)
- Visual Cv range bar chart

#### 9. 🔧 Valve Body & Trim Selection Guide
Rule-based advisor covering 9 body selection rules and 7 trim type rules:
- Body style recommendation (Globe, Angle, Ball, Butterfly, Cage-guided, Multi-stage)
- Trim type recommendation (Contoured, Anti-cav, Anti-noise, Multi-stage, Hard-facing)
- Material guidance (body and trim alloys)
- End connection recommendation

Driven by: fluid phase, pressure drop ratio, cavitation regime, noise level, temperature,
flashing, viscosity, sizing ratio.

#### 10. 🔗 LinkedIn Branding
- Developer badge in app header with LinkedIn link
- Sidebar strip with name and LinkedIn button
- Persistent footer on every page (name | LinkedIn | GitHub | Live App)

#### 11. 📖 In-App User Guide
Comprehensive 13-section guide covering:
Quick Start, Process Inputs, Sizing Results, Noise Analysis, Installed Characteristic,
Sensitivity Analysis, Rangeability, Actuator Sizing, Valve Selection, Save/Load,
Comparison Table, Standards Reference, Troubleshooting, About.

---

## 📦 Installation

### Prerequisites
- Python ≥ 3.10
- pip

### Quick Start

```bash
# 1. Clone
git clone https://github.com/aseemm84/Control-Valve.git
cd Control-Valve

# 2. Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
.venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch
streamlit run app.py
```

The app will open at `http://localhost:8501`.

### Development

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v
```

---

## 🗂 Directory Structure

```
Control-Valve/
├── app.py                        ← Streamlit entry point (13-tab layout)
├── requirements.txt              ← Production dependencies
├── requirements-dev.txt          ← Dev/test dependencies
├── README.md
│
├── .streamlit/
│   └── config.toml               ← Theme and server configuration
│
├── backend/                      ← Math engine (zero Streamlit)
│   ├── constants.py              ← N-factors (IEC Table 1), pipe schedules, conversions
│   ├── models.py                 ← Pydantic v2 data models (inputs + results)
│   ├── orchestrator.py           ← Master coordinator — run_sizing() public API
│   ├── noise_aerodynamic.py      ← IEC 60534-8-3 aerodynamic noise (v2.0 η_a fix)
│   ├── installed_characteristic.py ← Inherent vs installed curves (β analysis)
│   ├── rangeability.py           ← Rangeability, turndown, leakage class
│   ├── sensitivity.py            ← Parametric sweep engine
│   ├── actuator_guidance.py      ← Force/torque + actuator sizing
│   └── valve_selection.py        ← Rule-based body & trim advisor
│
├── frontend/                     ← Streamlit UI (zero math)
│   ├── ui_styles.py              ← CSS, LinkedIn branding, header, footer
│   ├── ui_inputs.py              ← Input widgets (with fluid library presets)
│   ├── ui_results.py             ← Primary sizing results display
│   ├── ui_charts.py              ← Plotly charts (original + v2.0 new)
│   ├── ui_noise.py               ← Noise analysis display
│   ├── ui_warnings.py            ← Engineering warnings panel
│   ├── ui_report.py              ← PDF / Excel report generation
│   ├── ui_save_load.py           ← JSON save / load panel
│   ├── ui_comparison.py          ← Multi-case comparison table
│   ├── ui_installed_char.py      ← Installed characteristic tab
│   ├── ui_sensitivity.py         ← Sensitivity / what-if tab
│   ├── ui_rangeability.py        ← Rangeability & turndown tab
│   ├── ui_actuator.py            ← Actuator sizing guidance tab
│   ├── ui_valve_guide.py         ← Valve body & trim selection tab
│   └── ui_user_guide.py          ← In-app user guide tab
│
├── data/
│   └── fluid_presets.json        ← 60+ fluid property presets (6 categories)
│
├── tests/
│   ├── conftest.py
│   └── test_*.py
│
└── docs/
    ├── engineering_basis.md
    └── user_guide.md
```

---

## 🔧 Usage Guide

### 5-Step Quick Start

1. **Select unit system** (SI or US) and **fluid phase** in the sidebar.
2. In **📋 Process Inputs**:
   - Enter P1, P2, T1, and flow rate (all **gauge** pressures)
   - Select a fluid from the **Fluid Library** dropdown (auto-fills properties)
   - Enter valve bore `d`, pipe IDs `D1`/`D2`, and valve factors `FL`/`xT`/`Fd`
3. Optionally enter **Rated Cv** (enables sizing ratio and opening %)
4. Click **🔬 CALCULATE** in the sidebar
5. Review results in **📊 Sizing Results**, **🔊 Noise Analysis**, and **⚠ Warnings**

### New Feature Workflow

| Feature | Tab | Prerequisite |
|---|---|---|
| Installed Characteristic | 📈 Installed Char | Successful calculation + Rated Cv |
| Sensitivity Analysis | 🔍 Sensitivity | Successful calculation |
| Rangeability | 📉 Rangeability | Successful calculation + Rated Cv |
| Valve Selection | 🔧 Valve Guide | Successful calculation |
| Actuator Sizing | 🔩 Actuator | Successful calculation |
| Save Calculation | 💾 Save / Load | Any state |
| Load Calculation | 💾 Save / Load | Previously saved `.json` file |
| Compare Cases | 🗂 Compare | Add cases after each calculation |

---

## 📋 Input Conventions

| Parameter | Convention |
|---|---|
| Pressures | Enter as **gauge** pressure; atmospheric (1.01325 bar / 14.696 psia) added automatically |
| Temperature | °C for SI, °F for US; converted to K internally |
| Gas flow | **Mass flow (kg/h or lb/h)** recommended to avoid standard-condition ambiguity |
| Steam | All properties from IAPWS-IF97; only specify quality x for wet steam |
| Cv_rated | Optional; required for sizing ratio, opening %, rangeability, installed curve |
| β (valve authority) | β = ΔP_valve / ΔP_total at design flow; used for installed characteristic |

---

## 🧪 Running Tests

```bash
pytest tests/ -v                         # All tests
pytest tests/ --cov=backend              # With coverage
pytest tests/ -k "not steam"             # Skip steam (if iapws not installed)
pytest tests/test_orchestrator.py -v     # Single module
```

---

## ⚙ Configuration

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor       = "#1f4e79"
backgroundColor    = "#ffffff"
secondaryBackgroundColor = "#f5f7fa"
textColor          = "#1a1a2e"
font               = "sans serif"

[server]
maxUploadSize = 10       # MB
enableCORS    = false
```

---

## 📄 Licence

MIT Licence — see [LICENSE](LICENSE).

---

## 👤 Developer

**Aseem Mehrotra**
- 🔗 [LinkedIn](https://www.linkedin.com/in/aseem-mehrotra/)
- 💻 [GitHub](https://github.com/aseemm84/Control-Valve)
- 🌐 [Live App](https://control-valve-sizing.streamlit.app/)

---

## 🏭 Standards References

- IEC 60534-2-1:2011, *Industrial-process control valves — Flow capacity — Sizing equations for fluid flow under installed conditions*
- ANSI/ISA-75.01.01-2012, *Flow Equations for Sizing Control Valves*
- IEC 60534-8-3:2011, *Control valve aerodynamic noise prediction*
- IEC 60534-8-4:2015, *Prediction of noise generated by hydrodynamic flow*
- IEC 60534-4:2006, *Inspection and test procedures — Leakage classification*
- IAPWS-IF97, *Industrial Formulation for Thermodynamic Properties of Water and Steam*
- ASME B16.34-2017, *Valves — Flanged, Threaded, and Welding End*
- ASME B36.10M-2018, *Welded and Seamless Wrought Steel Pipe*
- API RP 553, *Refinery Control Valves*
- Baumann, H.D. (1987), *On the prediction of aerodynamically created sound pressure levels of control valves*

---

## 📋 Version History

| Version | Date | Changes |
|---|---|---|
| **v2.0.0** | 2025 | 11 new features: Save/Load, Comparison, Installed Char, 60+ Fluid Library, Actuator Guidance, Sensitivity Analysis, Aerodynamic Noise Fix (Baumann η_a), Rangeability, Valve Selection, LinkedIn branding, User Guide |
| v1.x | 2024 | Initial release: Liquid/Gas/Steam sizing, IEC noise, Warnings, PDF/Excel reports |
