"""
frontend/ui_charts.py
=====================
Plotly chart generation for the Control Valve Sizer.

All functions return go.Figure objects — no Streamlit calls in this module.
The caller (app.py or feature tabs) uses st.plotly_chart() or _safe_chart().

v2.0 additions
--------------
- plot_installed_characteristic()  — inherent vs installed curves
- plot_sensitivity_tornado()       — sensitivity bar chart
- plot_rangeability_bar()          — Cv range bar chart
- plot_sensitivity_line()          — multi-output sensitivity line chart

Existing charts (unchanged API)
-------------------------------
- plot_cv_characteristic()
- plot_sizing_gauge()
- plot_pressure_profile()
- plot_cavitation_map()
- plot_noise_gauge()
"""

from __future__ import annotations

import math
from typing import Optional

import plotly.graph_objects as go

from backend.models import InstalledCharResult, SensitivityResult, ValveCharacteristic

# ── Brand colours ─────────────────────────────────────────────────────────

PRIMARY   = "#1f4e79"
SECONDARY = "#2e75b6"
ACCENT    = "#c55a11"
SUCCESS   = "#375623"
WARNING   = "#c9a227"
DANGER    = "#c00000"
MIDGREEN  = "#70ad47"
GOLD      = "#ffd700"


def _base_layout(
    title: str,
    xaxis_title: str = "",
    yaxis_title: str = "",
    showlegend: bool = True,
) -> dict:
    """Return a consistent plotly layout dict.

    Parameters
    ----------
    showlegend : bool
        Pass False for charts that have no traces requiring a legend
        (e.g. single-series tornado bar).  Default True.
        Accepting this here avoids passing `showlegend` as *both* a
        keyword argument AND inside **_base_layout(), which would raise
        a duplicate-keyword TypeError in Python.
    """
    return dict(
        title=dict(text=title, font=dict(size=14, color=PRIMARY), x=0.5),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        plot_bgcolor="#fafbfc",
        paper_bgcolor="#ffffff",
        font=dict(family="Segoe UI, Arial, sans-serif", size=12),
        margin=dict(l=50, r=30, t=50, b=50),
        showlegend=showlegend,
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#d1d9e0",
            borderwidth=1,
            font=dict(size=11),
        ),
    )


# =============================================================================
# ORIGINAL CHARTS (v1.x — unchanged public API)
# =============================================================================

def plot_cv_characteristic(
    Cv_rated: float,
    Cv_required: float,
    R_inherent: float = 50.0,
    char: Optional[ValveCharacteristic] = None,
    opening_pct: Optional[float] = None,
) -> go.Figure:
    """
    Plot the valve inherent Cv characteristic curve.

    Parameters
    ----------
    Cv_rated : float
        Rated Cv at full travel.
    Cv_required : float
        Required Cv — shown as a horizontal dashed line.
    R_inherent : float
        Inherent rangeability.
    char : ValveCharacteristic | None
        Characteristic type (equal-%, linear, quick-opening).
    opening_pct : float | None
        Design opening — shown as a vertical marker.
    """
    if char is None:
        char = ValveCharacteristic.EQUAL_PERCENTAGE

    n = 51
    thetas = [i / (n - 1) for i in range(n)]
    Cv_min = Cv_rated / R_inherent

    def cv_at(theta: float) -> float:
        theta = max(theta, 1e-9)
        if char == ValveCharacteristic.EQUAL_PERCENTAGE:
            return Cv_rated * (R_inherent ** (theta - 1.0))
        elif char == ValveCharacteristic.LINEAR:
            return Cv_min + (Cv_rated - Cv_min) * theta
        else:  # Quick-opening
            return Cv_rated * math.sqrt(theta)

    cv_vals = [cv_at(t) for t in thetas]
    theta_pct = [t * 100 for t in thetas]

    fig = go.Figure()

    # Characteristic curve
    fig.add_trace(go.Scatter(
        x=theta_pct, y=cv_vals,
        mode="lines",
        name=f"Cv Characteristic ({char.value})",
        line=dict(color=SECONDARY, width=2.5),
    ))

    # Cv required line
    fig.add_hline(
        y=Cv_required,
        line_dash="dash", line_color=ACCENT, line_width=2,
        annotation_text=f"Cv req = {Cv_required:.2f}",
        annotation_position="top left",
        annotation_font=dict(color=ACCENT, size=11),
    )

    # Design opening marker
    if opening_pct is not None:
        fig.add_vline(
            x=opening_pct,
            line_dash="dot", line_color=SUCCESS, line_width=2,
            annotation_text=f"{opening_pct:.1f}%",
            annotation_position="top right",
            annotation_font=dict(color=SUCCESS, size=11),
        )

    # Cv rated dashed line
    fig.add_hline(
        y=Cv_rated, line_dash="dash", line_color="#999999", line_width=1,
        annotation_text=f"Cv rated = {Cv_rated:.1f}",
        annotation_position="bottom right",
    )

    fig.update_layout(
        **_base_layout(
            f"Valve Inherent Cv Characteristic ({char.value})",
            "Valve Opening [%]",
            "Flow Coefficient Cv",
        )
    )
    fig.update_xaxes(range=[0, 100], dtick=20)
    fig.update_yaxes(range=[0, Cv_rated * 1.1])
    return fig


def plot_sizing_gauge(
    sizing_ratio: float,
    Cv_required: float,
    Cv_rated: float,
) -> go.Figure:
    """Gauge chart showing Cv_required / Cv_rated (sizing ratio)."""
    ratio_pct = sizing_ratio * 100.0

    colour = DANGER if ratio_pct > 100 else WARNING if ratio_pct > 85 else SUCCESS

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=ratio_pct,
        delta={"reference": 75, "suffix": "%", "valueformat": ".1f"},
        title={"text": "Sizing Ratio<br><span style='font-size:0.85em'>Cv_req / Cv_rated</span>"},
        number={"suffix": "%", "valueformat": ".1f"},
        gauge={
            "axis": {"range": [0, 120], "dtick": 20, "ticksuffix": "%"},
            "bar": {"color": colour, "thickness": 0.28},
            "bgcolor": "#f5f7fa",
            "bordercolor": "#d1d9e0",
            "steps": [
                {"range": [0, 70],  "color": "#e8f5e9"},
                {"range": [70, 85], "color": "#fff8e1"},
                {"range": [85, 100],"color": "#fff3e0"},
                {"range": [100, 120],"color": "#fce4ec"},
            ],
            "threshold": {
                "line": {"color": DANGER, "width": 3},
                "thickness": 0.85,
                "value": 100,
            },
        },
    ))

    fig.add_annotation(
        x=0.5, y=-0.08, xref="paper", yref="paper",
        text=f"Cv required: {Cv_required:.2f} | Cv rated: {Cv_rated:.2f}",
        showarrow=False, font=dict(size=11, color="#555"),
    )

    fig.update_layout(
        paper_bgcolor="#ffffff", height=320,
        margin=dict(l=30, r=30, t=60, b=50),
    )
    return fig


def plot_pressure_profile(
    P1_bar: float,
    P_vc_bar: Optional[float],
    P2_bar: float,
    Pv_bar: float,
    delta_P_max_bar: Optional[float] = None,
) -> go.Figure:
    """
    Pressure profile through the valve (upstream → vena contracta → downstream).
    """
    positions = [0.0, 0.35, 0.65, 1.0]
    labels = ["P1 (Upstream)", "P_vc (Vena Contracta)", "Throat/Trim", "P2 (Downstream)"]

    P_vc = P_vc_bar if P_vc_bar else (P1_bar + P2_bar) / 2
    pressures = [P1_bar, P_vc, P_vc * 0.98 + P2_bar * 0.02, P2_bar]

    fig = go.Figure()

    # Main pressure trace
    fig.add_trace(go.Scatter(
        x=positions, y=pressures,
        mode="lines+markers",
        name="Pressure",
        line=dict(color=SECONDARY, width=3),
        marker=dict(size=8, color=SECONDARY),
        hovertext=labels,
        hoverinfo="text+y",
    ))

    # Vapour pressure line
    fig.add_hline(
        y=Pv_bar,
        line_dash="dash", line_color=DANGER, line_width=2,
        annotation_text=f"Pv = {Pv_bar:.4f} bar a",
        annotation_position="bottom right",
        annotation_font=dict(color=DANGER, size=11),
    )

    # Delta P max line
    if delta_P_max_bar and P1_bar:
        P2_choked = P1_bar - delta_P_max_bar
        if P2_choked > 0:
            fig.add_hline(
                y=P2_choked,
                line_dash="dot", line_color=WARNING, line_width=2,
                annotation_text=f"ΔP max = {delta_P_max_bar:.3f} bar",
                annotation_position="top right",
                annotation_font=dict(color=WARNING, size=11),
            )

    # Cavitation / flashing zone fill
    if P_vc and P_vc < Pv_bar * 1.2:
        fig.add_hrect(
            y0=0, y1=Pv_bar * 1.05,
            fillcolor="rgba(255,0,0,0.07)",
            line_width=0,
            annotation_text="Cavitation/Flash Zone",
            annotation_position="top left",
        )

    fig.update_layout(
        **_base_layout(
            "Pressure Profile Through Control Valve",
            "Position Along Flow Path",
            "Pressure [bar a]",
        )
    )
    fig.update_xaxes(
        tickvals=positions,
        ticktext=["Upstream", "Vena Contracta", "Throat", "Downstream"],
    )
    return fig


def plot_cavitation_map(
    P1_bar: float,
    P2_bar: float,
    Pv_bar: float,
    FL: float,
    delta_P_max: Optional[float],
    delta_P_incipient: Optional[float],
) -> go.Figure:
    """
    Cavitation regime map: operating ΔP vs the cavitation threshold boundaries.
    """
    delta_P = P1_bar - P2_bar

    # Thresholds in bar
    dp_inc = delta_P_incipient or (delta_P * 0.3)
    dp_max = delta_P_max or (FL ** 2 * (P1_bar - Pv_bar))

    dp_range = [0, max(dp_max, delta_P) * 1.3]

    fig = go.Figure()

    # Regime bands
    fig.add_hrect(y0=0, y1=dp_inc, fillcolor="rgba(55,86,35,0.08)", line_width=0)
    fig.add_hrect(y0=dp_inc, y1=dp_max * 0.7, fillcolor="rgba(201,162,39,0.10)", line_width=0)
    fig.add_hrect(y0=dp_max * 0.7, y1=dp_max, fillcolor="rgba(197,90,17,0.10)", line_width=0)
    fig.add_hrect(y0=dp_max, y1=dp_range[1], fillcolor="rgba(192,0,0,0.10)", line_width=0)

    # Threshold lines
    fig.add_hline(y=dp_inc, line_dash="dash", line_color=WARNING, line_width=2,
                  annotation_text="Incipient", annotation_position="right")
    fig.add_hline(y=dp_max * 0.7, line_dash="dash", line_color=ACCENT, line_width=2,
                  annotation_text="Constant Cavitation", annotation_position="right")
    fig.add_hline(y=dp_max, line_dash="dash", line_color=DANGER, line_width=2,
                  annotation_text="Choked Flow", annotation_position="right")

    # Operating point
    fig.add_trace(go.Scatter(
        x=[0.5], y=[delta_P],
        mode="markers",
        name="Design ΔP",
        marker=dict(size=16, color=PRIMARY, symbol="diamond", line=dict(color="white", width=2)),
    ))

    fig.update_layout(
        **_base_layout("Cavitation Regime Map", "", "ΔP [bar]")
    )
    fig.update_xaxes(showticklabels=False, showgrid=False)
    fig.update_yaxes(range=dp_range)
    return fig


def plot_noise_gauge(
    Lpe_dba: Optional[float],
    limit_dba: float = 85.0,
) -> go.Figure:
    """Gauge chart showing predicted noise vs site limit."""
    val = Lpe_dba if Lpe_dba is not None else 0.0
    colour = DANGER if val > limit_dba else WARNING if val > limit_dba - 5 else SUCCESS

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        title={"text": "Predicted Noise<br><span style='font-size:0.85em'>Lpe [dB(A)] at 1 m</span>"},
        number={"suffix": " dB(A)", "valueformat": ".1f"},
        gauge={
            "axis": {"range": [40, 120], "dtick": 10},
            "bar": {"color": colour, "thickness": 0.28},
            "bgcolor": "#f5f7fa",
            "steps": [
                {"range": [40, 75],  "color": "#e8f5e9"},
                {"range": [75, 85],  "color": "#fff8e1"},
                {"range": [85, 95],  "color": "#fff3e0"},
                {"range": [95, 120], "color": "#fce4ec"},
            ],
            "threshold": {
                "line": {"color": DANGER, "width": 3},
                "thickness": 0.85,
                "value": limit_dba,
            },
        },
    ))

    fig.add_annotation(
        x=0.5, y=-0.08, xref="paper", yref="paper",
        text=f"Site limit: {limit_dba:.0f} dB(A)",
        showarrow=False, font=dict(size=11, color="#555"),
    )

    fig.update_layout(paper_bgcolor="#ffffff", height=320,
                      margin=dict(l=30, r=30, t=60, b=50))
    return fig


# =============================================================================
# NEW CHARTS (v2.0)
# =============================================================================

def plot_installed_characteristic(
    result: InstalledCharResult,
) -> go.Figure:
    """
    Plot inherent and installed Cv / flow-fraction characteristic curves.

    Parameters
    ----------
    result : InstalledCharResult
        From backend.installed_characteristic.calculate_installed_characteristic()
    """
    openings   = [p.opening_pct for p in result.points]
    q_inh      = [p.flow_fraction_inherent  * 100 for p in result.points]
    q_inst     = [p.flow_fraction_installed  * 100 for p in result.points]

    fig = go.Figure()

    # Ideal linear reference
    fig.add_trace(go.Scatter(
        x=openings, y=openings,
        mode="lines",
        name="Ideal Linear",
        line=dict(color="#cccccc", width=1.5, dash="dot"),
    ))

    # Inherent characteristic
    fig.add_trace(go.Scatter(
        x=openings, y=q_inh,
        mode="lines",
        name=f"Inherent ({result.char.value})",
        line=dict(color=SECONDARY, width=2.5),
    ))

    # Installed characteristic
    fig.add_trace(go.Scatter(
        x=openings, y=q_inst,
        mode="lines",
        name=f"Installed (β = {result.beta:.2f})",
        line=dict(color=ACCENT, width=2.5),
    ))

    # Design point
    if result.design_opening_pct:
        fig.add_vline(
            x=result.design_opening_pct,
            line_dash="dash", line_color=SUCCESS, line_width=2,
            annotation_text=f"Design: {result.design_opening_pct:.1f}%",
            annotation_font=dict(color=SUCCESS, size=11),
        )

    # Beta annotation
    fig.add_annotation(
        x=5, y=95, xref="x", yref="y",
        text=f"β = {result.beta:.2f} | R = {result.rangeability_inherent:.0f}:1",
        showarrow=False, bgcolor="rgba(255,255,255,0.85)",
        bordercolor=SECONDARY, borderwidth=1, font=dict(size=11),
        align="left",
    )

    controllability_colour = SUCCESS if result.is_controllable else DANGER
    fig.add_annotation(
        x=5, y=88, xref="x", yref="y",
        text="✅ Controllable" if result.is_controllable else "⚠ Poor Controllability",
        showarrow=False,
        font=dict(size=10, color=controllability_colour),
        align="left",
    )

    fig.update_layout(
        **_base_layout(
            "Inherent vs Installed Flow Characteristic",
            "Valve Opening [%]",
            "Relative Flow [%]",
        )
    )
    fig.update_xaxes(range=[0, 100], dtick=20)
    fig.update_yaxes(range=[0, 110], dtick=20)
    return fig


def plot_sensitivity_tornado(
    sensitivity_summary: dict[str, float],
    swept_parameter: str,
) -> go.Figure:
    """
    Horizontal tornado bar chart of sensitivity indices.

    Parameters
    ----------
    sensitivity_summary : dict[str, float]
        {output_name: max_sensitivity_index} from SensitivityResult.
    swept_parameter : str
        Parameter that was swept (for chart title).
    """
    if not sensitivity_summary:
        fig = go.Figure()
        fig.add_annotation(text="No sensitivity data", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False)
        return fig

    labels = list(sensitivity_summary.keys())
    values = list(sensitivity_summary.values())

    colours = [DANGER if v > 1.5 else WARNING if v > 0.7 else MIDGREEN for v in values]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colours,
        text=[f"{v:.3f}" for v in values],
        textposition="outside",
    ))

    fig.update_layout(
        **_base_layout(
            f"Sensitivity to: {swept_parameter}",
            "Normalised Sensitivity Index |dOutput/dInput|",
            "",
            showlegend=False,
        )
    )
    fig.update_xaxes(range=[0, max(values) * 1.25 if values else 2.0])
    return fig


def plot_sensitivity_line(
    sens_result: SensitivityResult,
    output_key: str = "Cv_required",
) -> go.Figure:
    """
    Line chart of a single output vs swept parameter across the sweep range.

    Parameters
    ----------
    sens_result : SensitivityResult
        Full sensitivity result from run_sensitivity().
    output_key : str
        Which output to plot: "Cv_required", "noise_dba", "sizing_ratio",
        "cavitation_sigma".
    """
    output_attr = {
        "Cv_required": ("Cv_required", "Cv Required", SECONDARY),
        "noise_dba":   ("noise_dba",   "Noise [dB(A)]", DANGER),
        "sizing_ratio":("sizing_ratio","Sizing Ratio",   ACCENT),
        "cavitation_sigma": ("cavitation_sigma", "σ (Cavitation)", SUCCESS),
    }.get(output_key, ("Cv_required", "Cv Required", SECONDARY))

    attr, label, colour = output_attr

    xs, ys = [], []
    for pt in sens_result.points:
        val = getattr(pt, attr, None)
        if val is not None:
            xs.append(round(pt.parameter_value, 4))
            ys.append(val)

    fig = go.Figure()

    if xs:
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="lines+markers",
            name=label,
            line=dict(color=colour, width=2.5),
            marker=dict(size=6, color=colour),
        ))

    # Mark base value
    base_x = sens_result.base_value
    if xs:
        base_y = None
        closest_idx = min(range(len(xs)), key=lambda i: abs(xs[i] - base_x))
        base_y = ys[closest_idx] if closest_idx < len(ys) else None
        if base_y:
            fig.add_trace(go.Scatter(
                x=[base_x], y=[base_y],
                mode="markers",
                name="Base Case",
                marker=dict(size=12, color=PRIMARY, symbol="star"),
            ))

    fig.update_layout(
        **_base_layout(
            f"{label} vs {sens_result.swept_parameter}",
            sens_result.swept_parameter,
            label,
        )
    )
    return fig


def plot_rangeability_bar(
    Cv_rated: float,
    Cv_required: float,
    Cv_min: float,
    turndown_ratio: float,
    rangeability: float,
) -> go.Figure:
    """
    Horizontal stacked bar showing Cv range vs turndown requirement.
    """
    fig = go.Figure()

    # Controllable band (Cv_min → Cv_rated)
    fig.add_trace(go.Bar(
        y=["Valve Cv Range"],
        x=[Cv_min],
        name="Below Controllable",
        orientation="h",
        marker_color="#dddddd",
    ))
    fig.add_trace(go.Bar(
        y=["Valve Cv Range"],
        x=[Cv_required - Cv_min],
        name="Controllable Range",
        orientation="h",
        marker_color=MIDGREEN,
        base=Cv_min,
    ))
    fig.add_trace(go.Bar(
        y=["Valve Cv Range"],
        x=[Cv_rated - Cv_required],
        name="Margin to Rated",
        orientation="h",
        marker_color=SECONDARY,
        base=Cv_required,
    ))

    # Design Cv marker
    fig.add_vline(
        x=Cv_required,
        line_dash="dash", line_color=ACCENT, line_width=2,
        annotation_text=f"Cv req = {Cv_required:.2f}",
        annotation_font=dict(color=ACCENT),
    )

    fig.add_annotation(
        x=Cv_rated * 0.5, y=1.2, xref="x", yref="y",
        text=f"Rangeability: {rangeability:.0f}:1 | Turndown: {turndown_ratio:.1f}:1",
        showarrow=False, bgcolor="rgba(255,255,255,0.9)",
        bordercolor=PRIMARY, borderwidth=1, font=dict(size=11),
    )

    fig.update_layout(
        **_base_layout("Valve Cv Rangeability Analysis", "Flow Coefficient Cv", "",
                       showlegend=True),
        barmode="stack",
        height=250,
    )
    fig.update_yaxes(showticklabels=False)
    return fig
