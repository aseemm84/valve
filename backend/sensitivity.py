"""
backend/sensitivity.py
=======================
Parametric sensitivity / what-if analysis engine.

For each swept variable, this module runs the full sizing orchestrator
across a range of values (±N% in n_steps equal steps) and records:
  - Cv_required
  - Sizing ratio (Cv_required / Cv_rated)
  - Noise level [dB(A)]
  - Cavitation sigma

The result is a list of SensitivityPoint objects ready for plotting.

Design notes
------------
The orchestrator is stateless; each call is independent.  This makes
the sweep trivially safe — no shared state between steps.

For production deployments with large n_steps, consider wrapping the
loop in concurrent.futures.ThreadPoolExecutor for parallel execution.
"""

from __future__ import annotations

import copy
import math
from typing import Callable

from backend.models import (
    SensitivityPoint,
    SensitivityResult,
    SizingInputs,
    SizingResult,
)


# Type alias for the orchestrator function signature
OrchestratorFn = Callable[[SizingInputs], SizingResult]


# ---------------------------------------------------------------------------
# Swept parameter definitions
# ---------------------------------------------------------------------------

# Parameter name → (getter, setter) lambdas on SizingInputs
SWEEP_PARAMS: dict[str, tuple[Callable, Callable]] = {
    "Upstream Pressure P1": (
        lambda inp: inp.P1_bara,
        lambda inp, v: inp.model_copy(update={"P1_bara": v}),
    ),
    "Downstream Pressure P2": (
        lambda inp: inp.P2_bara,
        lambda inp, v: inp.model_copy(update={"P2_bara": v}),
    ),
    "Flow Rate": (
        lambda inp: inp.flow_value,
        lambda inp, v: inp.model_copy(update={"flow_value": v}),
    ),
    "Inlet Temperature T1": (
        lambda inp: inp.T1_K,
        lambda inp, v: inp.model_copy(update={"T1_K": v}),
    ),
    "FL Factor": (
        lambda inp: inp.FL,
        lambda inp, v: inp.model_copy(update={"FL": min(v, 0.99)}),
    ),
    "Valve Bore d": (
        lambda inp: inp.d_mm,
        lambda inp, v: inp.model_copy(update={"d_mm": v}),
    ),
    "Specific Gravity Gf": (
        lambda inp: inp.Gf,
        lambda inp, v: inp.model_copy(update={"Gf": max(v, 0.01)}),
    ),
    "Viscosity": (
        lambda inp: inp.viscosity_cP,
        lambda inp, v: inp.model_copy(update={"viscosity_cP": max(v, 0.001)}),
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_sensitivity(
    base_inputs: SizingInputs,
    orchestrator_fn: OrchestratorFn,
    swept_parameter: str,
    sweep_range_pct: float = 20.0,
    n_steps: int = 20,
) -> SensitivityResult:
    """
    Run a parametric sensitivity sweep around the base-case inputs.

    Parameters
    ----------
    base_inputs : SizingInputs
        The baseline sizing input set.
    orchestrator_fn : OrchestratorFn
        The sizing orchestrator function (backend.orchestrator.run_sizing).
        Passed as a dependency to keep this module free of circular imports.
    swept_parameter : str
        Name of the parameter to sweep (must be a key in SWEEP_PARAMS).
    sweep_range_pct : float
        Total sweep range as ±N% of base value (default ±20%).
    n_steps : int
        Number of steps across the sweep range (default 20).

    Returns
    -------
    SensitivityResult
        All sweep points plus a sensitivity summary.

    Raises
    ------
    KeyError
        If `swept_parameter` is not in SWEEP_PARAMS.
    ValueError
        If n_steps < 3 or sweep_range_pct ≤ 0.
    """
    if swept_parameter not in SWEEP_PARAMS:
        raise KeyError(
            f"Unknown sweep parameter: '{swept_parameter}'. "
            f"Valid options: {list(SWEEP_PARAMS.keys())}"
        )
    if n_steps < 3:
        raise ValueError("n_steps must be at least 3")
    if sweep_range_pct <= 0:
        raise ValueError("sweep_range_pct must be positive")

    getter, setter = SWEEP_PARAMS[swept_parameter]
    base_value = getter(base_inputs)

    if base_value == 0:
        raise ValueError(f"Base value of '{swept_parameter}' is zero; cannot sweep.")

    # ── Build sweep values ──────────────────────────────────────────────────
    pct_changes = [
        -sweep_range_pct + i * (2.0 * sweep_range_pct / (n_steps - 1))
        for i in range(n_steps)
    ]

    # ── Run sweep ──────────────────────────────────────────────────────────
    points: list[SensitivityPoint] = []
    Cv_values: list[float] = []
    noise_values: list[float] = []

    for pct in pct_changes:
        new_value = base_value * (1.0 + pct / 100.0)

        # Physical bounds protection
        new_value = _clamp_parameter(swept_parameter, new_value, base_inputs)

        try:
            new_inputs = setter(base_inputs, new_value)
            result = orchestrator_fn(new_inputs)
        except Exception:
            # Skip failed points (e.g. P2 > P1 at extremes)
            points.append(SensitivityPoint(
                parameter_name=swept_parameter,
                parameter_value=new_value,
                parameter_pct_change=pct,
                Cv_required=None,
                flow_regime="Error",
            ))
            continue

        Cv = result.Cv_required
        noise = result.noise.overall_Lpe_dba if result.noise else None
        sigma = (
            result.cavitation.sigma
            if result.cavitation and result.cavitation.sigma is not None
            else None
        )
        sizing_ratio = result.sizing_ratio

        if Cv is not None:
            Cv_values.append(Cv)
        if noise is not None:
            noise_values.append(noise)

        points.append(SensitivityPoint(
            parameter_name=swept_parameter,
            parameter_value=round(new_value, 6),
            parameter_pct_change=round(pct, 2),
            Cv_required=round(Cv, 4) if Cv else None,
            sizing_ratio=round(sizing_ratio, 4) if sizing_ratio else None,
            noise_dba=round(noise, 1) if noise else None,
            cavitation_sigma=round(sigma, 4) if sigma else None,
            flow_regime=result.flow_regime,
            is_choked=result.is_choked,
        ))

    # ── Sensitivity summary ────────────────────────────────────────────────
    summary = _compute_sensitivity_summary(points, base_value)

    # Dominant output (highest sensitivity)
    dominant_output = max(summary, key=lambda k: abs(summary[k])) if summary else "Cv"

    return SensitivityResult(
        swept_parameter=swept_parameter,
        base_value=base_value,
        sweep_range_pct=sweep_range_pct,
        n_steps=n_steps,
        points=points,
        dominant_output=dominant_output,
        sensitivity_summary=summary,
    )


def _clamp_parameter(param: str, value: float, base: SizingInputs) -> float:
    """
    Apply physical bounds to prevent illegal input combinations.

    Parameters
    ----------
    param : str
        Parameter name.
    value : float
        Proposed swept value.
    base : SizingInputs
        Original base inputs (for cross-parameter checks).

    Returns
    -------
    float
        Clamped value.
    """
    if "P2" in param:
        # P2 must remain below P1
        value = min(value, base.P1_bara * 0.99)
        value = max(value, 0.01)
    elif "P1" in param:
        value = max(value, base.P2_bara * 1.01)
        value = max(value, 0.1)
    elif "FL" in param:
        value = max(0.10, min(value, 0.99))
    elif "Bore" in param or "d_mm" in param:
        value = max(5.0, min(value, base.D1_mm * 0.99))
    elif "Flow" in param:
        value = max(value, base.flow_value * 0.001)
    return value


def _compute_sensitivity_summary(
    points: list[SensitivityPoint],
    base_value: float,
) -> dict[str, float]:
    """
    Compute normalised sensitivity indices for each output variable.

    Sensitivity index S = (ΔOutput/Output_base) / (ΔInput/Input_base)

    Returns the maximum absolute sensitivity index across the sweep for each
    output variable, giving a single number showing how "responsive" each
    output is to the swept input.

    Returns
    -------
    dict[str, float]
        Keys: "Cv", "Noise_dBA", "Sizing_Ratio", "Cavitation_Sigma"
        Values: max |S| across sweep (dimensionless).
    """
    summary: dict[str, float] = {}

    # Find base-case point (pct_change closest to 0)
    base_pt = min(points, key=lambda p: abs(p.parameter_pct_change))

    outputs = {
        "Cv": [p.Cv_required for p in points if p.Cv_required is not None],
        "Noise_dBA": [p.noise_dba for p in points if p.noise_dba is not None],
        "Sizing_Ratio": [p.sizing_ratio for p in points if p.sizing_ratio is not None],
        "Cavitation_Sigma": [
            p.cavitation_sigma for p in points if p.cavitation_sigma is not None
        ],
    }

    for output_name, values in outputs.items():
        if len(values) < 3:
            continue
        base_out_attr = {
            "Cv": base_pt.Cv_required,
            "Noise_dBA": base_pt.noise_dba,
            "Sizing_Ratio": base_pt.sizing_ratio,
            "Cavitation_Sigma": base_pt.cavitation_sigma,
        }.get(output_name)

        if base_out_attr is None or base_out_attr == 0:
            continue

        max_s = 0.0
        for pt in points:
            out_val = {
                "Cv": pt.Cv_required,
                "Noise_dBA": pt.noise_dba,
                "Sizing_Ratio": pt.sizing_ratio,
                "Cavitation_Sigma": pt.cavitation_sigma,
            }.get(output_name)

            if out_val is None or pt.parameter_pct_change == 0:
                continue

            inp_pct = pt.parameter_pct_change / 100.0
            out_pct = (out_val - base_out_attr) / base_out_attr

            if abs(inp_pct) > 0:
                s = abs(out_pct / inp_pct)
                max_s = max(max_s, s)

        summary[output_name] = round(max_s, 3)

    return summary
