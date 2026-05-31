"""
backend/models.py
=================
Pydantic v2 data models for the Control Valve Sizer application.

All models are pure data containers with no Streamlit or I/O dependencies.
They are used across the backend sizing engine, new feature modules, and the
frontend UI (for serialisation / deserialisation of save/load files).

Standards reference
-------------------
IEC 60534-2-1:2011  — variable names and sizing parameters
ANSI/ISA-75.01.01   — cross-referenced N-factors
IEC 60534-8-3:2011  — aerodynamic noise result fields
IEC 60534-8-4:2015  — hydrodynamic noise result fields
IEC 60534-4:2006    — leakage class definitions
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class FluidPhase(str, Enum):
    """Fluid phase selection."""
    LIQUID = "Liquid"
    GAS    = "Gas"
    STEAM  = "Steam"


class UnitSystem(str, Enum):
    """Measurement unit system."""
    SI = "SI"
    US = "US"


class FlowBasis(str, Enum):
    """Basis on which flow is expressed."""
    VOLUMETRIC = "Volumetric"   # m³/h or GPM
    MASS       = "Mass"         # kg/h or lb/h
    STANDARD   = "Standard"     # Nm³/h or SCFH (gas only)


class ValveCharacteristic(str, Enum):
    """Inherent valve flow characteristic."""
    EQUAL_PERCENTAGE = "Equal Percentage"
    LINEAR           = "Linear"
    QUICK_OPENING    = "Quick Opening"


class CavitationRegime(str, Enum):
    """Five-tier IEC 60534-8-4 cavitation regime classification."""
    NONE      = "none"
    INCIPIENT = "incipient"
    CONSTANT  = "constant"
    CHOKED    = "choked"
    FLASHING  = "flashing"


class FailPosition(str, Enum):
    """Valve fail-safe position (for actuator guidance)."""
    FAIL_OPEN   = "Fail Open"
    FAIL_CLOSED = "Fail Closed"


class ActuatorType(str, Enum):
    """Actuator technology type."""
    PNEUMATIC_DIAPHRAGM = "Pneumatic Diaphragm"
    PNEUMATIC_PISTON    = "Pneumatic Piston"
    ELECTRIC            = "Electric"


class ValveBodyStyle(str, Enum):
    """Recommended valve body style."""
    GLOBE_SINGLE    = "Globe (Single-Seat)"
    GLOBE_DOUBLE    = "Globe (Double-Seat)"
    ANGLE           = "Angle Body"
    BALL            = "Ball Valve"
    BUTTERFLY_HP    = "High-Performance Butterfly"
    CAGE_GLOBE      = "Cage-Guided Globe"


class TrimType(str, Enum):
    """Recommended valve trim type."""
    CONTOURED        = "Contoured Parabolic"
    CHARACTERISED    = "Characterised Cage"
    MULTISTAGE       = "Multi-Stage / Tortuous Path"
    ANTI_CAVITATION  = "Anti-Cavitation Trim"
    ANTI_NOISE       = "Anti-Noise Trim"
    HARD_FACING      = "Hard-Facing (Stellite)"


# ---------------------------------------------------------------------------
# Sub-result models
# ---------------------------------------------------------------------------

class CavitationResult(BaseModel):
    """Cavitation analysis results (IEC 60534-8-4)."""

    regime: CavitationRegime = CavitationRegime.NONE

    sigma: Optional[float] = Field(None, description="Cavitation index σ = (P1-Pv)/(P1-P2)")
    sigma_incipient: Optional[float] = Field(None, description="σ at incipient cavitation")
    sigma_constant: Optional[float] = Field(None, description="σ at constant cavitation")
    sigma_mv: Optional[float] = Field(None, description="σ at maximum vibration")
    sigma_choked: Optional[float] = Field(None, description="σ at choked cavitation")

    delta_P_max: Optional[float] = Field(None, description="Choked ΔP [bar or psi]")
    delta_P_incipient: Optional[float] = Field(None, description="Incipient cavitation ΔP [bar or psi]")
    P_vc: Optional[float] = Field(None, description="Vena contracta pressure [bar a]")

    FL: Optional[float] = Field(None, description="Liquid pressure recovery factor used")
    FF: Optional[float] = Field(None, description="Critical pressure ratio factor FF")

    is_flashing: bool = False
    is_choked: bool = False

    severity_label: str = "No Cavitation"
    recommendation: str = ""


class NoiseResult(BaseModel):
    """Noise prediction results (IEC 60534-8-3 and 8-4)."""

    # Gas / steam (aerodynamic — IEC 60534-8-3)
    Lpi_db: Optional[float] = Field(None, description="Internal sound power level [dB re 1pW]")
    TL_db: Optional[float] = Field(None, description="Pipe wall transmission loss [dB]")
    Lpe_dba: Optional[float] = Field(None, description="External SPL at 1m [dB(A)]")

    # Gas regime
    Mvc: Optional[float] = Field(None, description="Vena contracta Mach number")
    eta_acoustic: Optional[float] = Field(None, description="Acoustic efficiency factor η_a")
    Wm_watts: Optional[float] = Field(None, description="Mechanical stream power [W]")
    Wa_watts: Optional[float] = Field(None, description="Acoustic power [W]")
    is_sonic: bool = False

    # Liquid (hydrodynamic — IEC 60534-8-4)
    Lpe_liquid_dba: Optional[float] = Field(None, description="Liquid hydrodynamic SPL at 1m [dB(A)]")
    noise_regime: str = "N/A"

    # Combined (whichever applies)
    overall_Lpe_dba: Optional[float] = Field(None, description="Final external SPL [dB(A)]")
    exceeds_limit: bool = False
    limit_dba: float = 85.0


class PipingResult(BaseModel):
    """Piping geometry correction factors (IEC 60534-2-1 §6)."""

    Fp: float = Field(1.0, description="Piping geometry factor")
    FLP: float = Field(1.0, description="Combined FL·Fp for liquid choked-flow")
    xTP: float = Field(0.0, description="Differential pressure ratio with piping, gas")
    sum_K: float = Field(0.0, description="Sum of inlet + outlet fitting loss coefficients K")
    has_reducers: bool = False
    iterations: int = 0


# ---------------------------------------------------------------------------
# Primary input model
# ---------------------------------------------------------------------------

class SizingInputs(BaseModel):
    """
    Complete sizing input specification.

    All pressures are stored in absolute SI units internally (bar a).
    All temperatures are in Kelvin internally.
    All flows are in SI units (m³/h volumetric, kg/h mass).
    The unit_system field records what the user entered for display purposes.
    """

    # ── Identity ────────────────────────────────────────────────────────────
    tag_number: str = Field("", description="Instrument tag / valve tag")
    case_name: str = Field("", description="User-defined case description")
    unit_system: UnitSystem = UnitSystem.SI
    fluid_phase: FluidPhase = FluidPhase.LIQUID

    # ── Process conditions (SI internal) ────────────────────────────────────
    P1_bara: float = Field(..., description="Upstream absolute pressure [bar a]", gt=0)
    P2_bara: float = Field(..., description="Downstream absolute pressure [bar a]", gt=0)
    T1_K: float = Field(..., description="Inlet temperature [K]", gt=0)

    # ── Flow ────────────────────────────────────────────────────────────────
    flow_value: float = Field(..., description="Flow rate (SI unit, volumetric or mass)", gt=0)
    flow_basis: FlowBasis = FlowBasis.VOLUMETRIC

    # ── Liquid fluid properties ──────────────────────────────────────────────
    Gf: float = Field(1.0, description="Specific gravity relative to water at 15.6°C")
    Pv_bara: float = Field(0.023, description="Vapour pressure [bar a]", ge=0)
    Pc_bara: float = Field(220.9, description="Critical pressure [bar a]", gt=0)
    viscosity_cP: float = Field(1.0, description="Dynamic viscosity [cP]", gt=0)

    # ── Gas / vapour properties ──────────────────────────────────────────────
    molecular_weight: float = Field(29.0, description="Molecular weight [g/mol]", gt=0)
    gamma: float = Field(1.4, description="Specific heat ratio Cp/Cv")
    compressibility_Z: float = Field(1.0, description="Compressibility factor Z at inlet")
    rho1_kgm3: Optional[float] = Field(None, description="Inlet gas density [kg/m³] (overrides ideal gas)")

    # ── Steam ────────────────────────────────────────────────────────────────
    steam_quality: float = Field(1.0, description="Steam quality x (1=superheated/dry, 0-1=wet)")

    # ── Valve parameters ─────────────────────────────────────────────────────
    FL: float = Field(0.9, description="Liquid pressure recovery factor", gt=0, le=1.0)
    xT: float = Field(0.72, description="Pressure drop ratio factor (gas)", gt=0, le=1.0)
    Fd: float = Field(1.0, description="Valve style modifier for noise", gt=0, le=1.0)

    d_mm: float = Field(50.0, description="Valve bore diameter [mm]", gt=0)
    D1_mm: float = Field(50.0, description="Upstream pipe internal diameter [mm]", gt=0)
    D2_mm: float = Field(50.0, description="Downstream pipe internal diameter [mm]", gt=0)

    Cv_rated: Optional[float] = Field(None, description="Rated valve Cv at full open", gt=0)
    pipe_schedule: str = Field("Sch 40", description="Pipe schedule (for noise transmission loss)")

    valve_type: str = Field("Globe Single-Seat", description="Valve type for presets and guides")
    char: ValveCharacteristic = ValveCharacteristic.EQUAL_PERCENTAGE

    # ── Sizing control ────────────────────────────────────────────────────────
    sizing_margin_pct: float = Field(10.0, description="Sizing margin [%]", ge=0, le=50)
    noise_limit_dba: float = Field(85.0, description="Site noise limit [dB(A)]", gt=0)

    # ── Actuator inputs ───────────────────────────────────────────────────────
    actuator_type: ActuatorType = ActuatorType.PNEUMATIC_DIAPHRAGM
    supply_pressure_bar: float = Field(5.5, description="Actuator supply pressure [bar g]", gt=0)
    fail_position: FailPosition = FailPosition.FAIL_CLOSED
    packing_type: str = Field("PTFE", description="Stem packing material")

    # ── Installed characteristic inputs ──────────────────────────────────────
    system_dp_fraction: float = Field(
        0.5,
        description="Valve ΔP / total system ΔP at design flow (β)",
        gt=0, le=1.0
    )

    @field_validator("P2_bara")
    @classmethod
    def p2_lt_p1(cls, v: float, info: Any) -> float:
        """Validate P2 < P1 (positive differential pressure)."""
        p1 = info.data.get("P1_bara", None)
        if p1 is not None and v >= p1:
            raise ValueError(f"P2 ({v} bar a) must be less than P1 ({p1} bar a)")
        return v

    @model_validator(mode="after")
    def validate_valve_geometry(self) -> "SizingInputs":
        """Validate valve bore does not exceed pipe diameter."""
        if self.d_mm > self.D1_mm + 0.5:  # 0.5 mm tolerance
            raise ValueError(
                f"Valve bore d ({self.d_mm} mm) cannot exceed upstream pipe ID D1 ({self.D1_mm} mm)"
            )
        return self


# ---------------------------------------------------------------------------
# Primary result model
# ---------------------------------------------------------------------------

class SizingResult(BaseModel):
    """
    Complete sizing result from orchestrator.run_sizing().

    All values are in SI units unless _bar/_mm/_dba suffix indicates otherwise.
    The unit_system field is carried from inputs for display conversion.
    """

    # ── Status ───────────────────────────────────────────────────────────────
    success: bool = False
    error_message: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    hard_violations: list[str] = Field(default_factory=list)

    # ── Identity (mirrored from inputs) ──────────────────────────────────────
    unit_system: UnitSystem = UnitSystem.SI
    fluid_phase: FluidPhase = FluidPhase.LIQUID
    tag_number: str = ""
    case_name: str = ""

    # ── Primary sizing outputs ────────────────────────────────────────────────
    Cv_required: Optional[float] = Field(None, description="Required flow coefficient Cv")
    Cv_margin: Optional[float] = Field(None, description="Cv with sizing margin applied")
    Kv_required: Optional[float] = Field(None, description="Required Kv (Cv × 0.865)")
    sizing_ratio: Optional[float] = Field(None, description="Cv_required / Cv_rated")
    opening_pct: Optional[float] = Field(None, description="Estimated valve opening [%]")

    # ── Process conditions (SI) ───────────────────────────────────────────────
    P1_bar: Optional[float] = Field(None, description="Inlet absolute pressure [bar a]")
    P2_bar: Optional[float] = Field(None, description="Outlet absolute pressure [bar a]")
    T1_K: Optional[float] = Field(None, description="Inlet temperature [K]")
    delta_P_bar: Optional[float] = Field(None, description="Available ΔP [bar]")
    delta_P_max_bar: Optional[float] = Field(None, description="Choked/max allowable ΔP [bar]")

    # ── Flow regime ───────────────────────────────────────────────────────────
    flow_regime: str = "Turbulent"
    is_choked: bool = False
    is_viscous_corrected: bool = False
    Rev: Optional[float] = Field(None, description="Valve Reynolds number")
    FR: Optional[float] = Field(None, description="Viscosity correction factor FR")

    # ── Fluid properties at inlet ────────────────────────────────────────────
    rho1_kgm3: Optional[float] = Field(None, description="Inlet density [kg/m³]")
    mu_cP: Optional[float] = Field(None, description="Dynamic viscosity [cP]")

    # ── Gas specific ──────────────────────────────────────────────────────────
    Y_expansion: Optional[float] = Field(None, description="Gas expansion factor Y")
    x_pressure_ratio: Optional[float] = Field(None, description="ΔP/P1 pressure ratio x")
    Fk: Optional[float] = Field(None, description="Ratio of specific heats factor Fk")
    Mach_outlet: Optional[float] = Field(None, description="Estimated outlet Mach number")

    # ── Piping correction factors ─────────────────────────────────────────────
    piping: Optional[PipingResult] = None
    Fp: float = 1.0
    FLP: float = 1.0
    xTP: float = 0.0

    # ── Sub-results ───────────────────────────────────────────────────────────
    cavitation: Optional[CavitationResult] = None
    noise: Optional[NoiseResult] = None

    # ── Velocity checks ───────────────────────────────────────────────────────
    v_inlet_ms: Optional[float] = Field(None, description="Inlet pipe velocity [m/s]")
    v_outlet_ms: Optional[float] = Field(None, description="Outlet pipe velocity [m/s]")

    # ── Steam specific ────────────────────────────────────────────────────────
    steam_rho: Optional[float] = None
    steam_quality_out: Optional[float] = None


# ---------------------------------------------------------------------------
# New feature result models
# ---------------------------------------------------------------------------

class InstalledCharPoint(BaseModel):
    """Single point on inherent / installed characteristic curves."""
    opening_pct: float
    Cv_inherent: float
    Cv_installed: float
    flow_fraction_inherent: float
    flow_fraction_installed: float


class InstalledCharResult(BaseModel):
    """Installed characteristic curve results."""
    beta: float = Field(..., description="ΔP_valve / ΔP_total at design flow")
    char: ValveCharacteristic = ValveCharacteristic.EQUAL_PERCENTAGE
    Cv_rated: float = Field(..., description="Rated Cv at full open")
    rangeability_inherent: float = Field(50.0, description="Rangeability R of inherent char")

    points: list[InstalledCharPoint] = Field(default_factory=list)
    design_opening_pct: Optional[float] = None

    # Controllability assessment
    is_controllable: bool = True
    gain_at_design: Optional[float] = None
    gain_variability_pct: Optional[float] = None
    recommendation: str = ""


class RangeabilityResult(BaseModel):
    """Rangeability and turndown analysis result."""
    Cv_max: float
    Cv_min: float
    effective_rangeability: float
    turndown_ratio: float
    min_controllable_flow_fraction: float
    recommended_leakage_class: str
    leakage_class_description: str
    rangeability_adequate: bool
    recommendation: str


class SensitivityPoint(BaseModel):
    """Single parameter variation point in sensitivity sweep."""
    parameter_name: str
    parameter_value: float
    parameter_pct_change: float
    Cv_required: Optional[float] = None
    sizing_ratio: Optional[float] = None
    noise_dba: Optional[float] = None
    cavitation_sigma: Optional[float] = None
    flow_regime: str = ""
    is_choked: bool = False


class SensitivityResult(BaseModel):
    """Results of a sensitivity / what-if parametric sweep."""
    swept_parameter: str
    base_value: float
    sweep_range_pct: float
    n_steps: int
    points: list[SensitivityPoint] = Field(default_factory=list)
    dominant_output: str = ""
    sensitivity_summary: dict[str, float] = Field(default_factory=dict)


class ActuatorResult(BaseModel):
    """Actuator sizing guidance result."""
    actuator_type: ActuatorType = ActuatorType.PNEUMATIC_DIAPHRAGM
    fail_position: FailPosition = FailPosition.FAIL_CLOSED
    supply_pressure_bar: float = 5.5

    # Forces / torques
    unbalanced_force_N: float = 0.0
    packing_friction_N: float = 0.0
    seat_load_N: float = 0.0
    required_thrust_N: float = 0.0
    required_thrust_N_with_contingency: float = 0.0

    # For pneumatic diaphragm
    diaphragm_area_cm2: Optional[float] = None
    spring_range_bar: Optional[str] = None
    bench_set_bar: Optional[str] = None

    # For rotary valves
    break_torque_Nm: Optional[float] = None
    run_torque_Nm: Optional[float] = None
    end_torque_Nm: Optional[float] = None
    required_torque_Nm: Optional[float] = None

    # Electric
    required_power_W: Optional[float] = None
    recommended_motor_kW: Optional[float] = None

    # Recommendations
    notes: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "These are preliminary estimates for actuator selection guidance only. "
        "Final sizing must be confirmed with the valve and actuator manufacturer."
    )


class ValveSelectionResult(BaseModel):
    """Valve body and trim selection recommendation."""
    # Recommended body style (ranked list)
    recommended_body: ValveBodyStyle = ValveBodyStyle.GLOBE_SINGLE
    body_alternatives: list[ValveBodyStyle] = Field(default_factory=list)
    body_rationale: str = ""

    # Recommended trim
    recommended_trim: TrimType = TrimType.CONTOURED
    trim_alternatives: list[TrimType] = Field(default_factory=list)
    trim_rationale: str = ""

    # Material guidance
    body_material: str = "Carbon Steel (ASTM A216 WCB)"
    trim_material: str = "316 SS / Stellite-faced seats"

    # Additional notes
    notes: list[str] = Field(default_factory=list)
    end_connection: str = "ASME B16.5 RF Flanged"


class ComparisonCase(BaseModel):
    """A single case stored in the multi-case comparison table."""
    case_id: int
    case_name: str = ""
    tag_number: str = ""
    inputs: SizingInputs
    result: SizingResult
    timestamp: str = ""


class SavedCalculation(BaseModel):
    """
    Top-level container for save/load of a complete calculation.

    Serialised as JSON for file download / upload.
    """
    app_version: str = "2.0.0"
    schema_version: str = "2"
    saved_at: str = ""
    case_name: str = ""
    tag_number: str = ""
    inputs: SizingInputs
    result: SizingResult

    # Optional extended results (computed on save)
    installed_char: Optional[InstalledCharResult] = None
    rangeability: Optional[RangeabilityResult] = None
    actuator: Optional[ActuatorResult] = None
    valve_selection: Optional[ValveSelectionResult] = None
