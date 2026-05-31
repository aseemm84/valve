"""
frontend/ui_warnings.py
=======================
Engineering warnings and hard violation display.
"""

from __future__ import annotations

import streamlit as st

from backend.models import SizingResult
from frontend.ui_styles import section_header_html


def render_warning_panel(result: SizingResult) -> None:
    """
    Render engineering warnings and hard constraint violations.

    Parameters
    ----------
    result : SizingResult
        Completed sizing result.
    """
    st.markdown(section_header_html("Engineering Validation Report"), unsafe_allow_html=True)

    hard = result.hard_violations
    soft = result.warnings

    # ── Hard violations ──────────────────────────────────────────────────────
    if hard:
        st.error(f"🔴 **{len(hard)} Hard Constraint Violation(s)** — Calculation may not be valid!")
        for i, v in enumerate(hard, 1):
            st.markdown(
                f'<div class="alert-hard">🔴 <b>H{i}:</b> {v}</div>',
                unsafe_allow_html=True,
            )

    # ── Soft warnings ────────────────────────────────────────────────────────
    if soft:
        st.warning(f"🟡 **{len(soft)} Engineering Warning(s)** — Review recommended.")
        for i, w in enumerate(soft, 1):
            st.markdown(
                f'<div class="alert-soft">🟡 <b>W{i}:</b> {w}</div>',
                unsafe_allow_html=True,
            )

    # ── All clear ────────────────────────────────────────────────────────────
    if not hard and not soft:
        st.success(
            "✅ **All checks passed.** No hard violations or engineering warnings detected "
            "for these operating conditions."
        )

    # ── Warning guide ────────────────────────────────────────────────────────
    with st.expander("ℹ Warning Severity Guide", expanded=False):
        st.markdown(
            """
            | Symbol | Severity | Action Required |
            |---|---|---|
            | 🔴 Hard | **Constraint violated** | Must resolve before using Cv result |
            | 🟡 Soft | **Engineering concern** | Review and document; may be acceptable |
            | ✅ Pass | No issue | No action needed |

            **Common hard violations:**
            - P2 ≥ P1 (non-positive ΔP)
            - Valve bore exceeds pipe ID
            - Steam phase with negative superheat

            **Common soft warnings:**
            - Sizing ratio > 0.85 (near capacity limit)
            - Opening < 20% or > 85% (outside stable control range)
            - Predicted noise > site limit
            - Severe cavitation (choked or flashing regime)
            - Velocity > 6 m/s in liquid service
            - Very low valve Reynolds number (Rev < 10,000)
            """
        )
