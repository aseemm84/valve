"""
frontend/ui_comparison.py  — Multi-Case Comparison Table
"""
from __future__ import annotations
from datetime import datetime
import streamlit as st
from backend.models import ComparisonCase, SizingInputs, SizingResult
from frontend.ui_styles import section_header_html


def render_comparison(
    current_result: SizingResult | None,
    current_inputs: SizingInputs | None,
) -> None:
    st.markdown("## 📊 Multi-Case Comparison Table")
    st.markdown(
        "Add the current calculation to a comparison table. "
        "Run different scenarios (e.g. min/normal/max flow) and compare them side-by-side."
    )

    if "comparison_cases" not in st.session_state:
        st.session_state["comparison_cases"] = []

    cases: list[ComparisonCase] = st.session_state["comparison_cases"]

    # ── Add current case ─────────────────────────────────────────────────────
    col_add, col_clear = st.columns([2, 1])
    with col_add:
        case_label = st.text_input(
            "Case Label",
            value=f"Case {len(cases) + 1}",
            key="comp_case_label",
            placeholder="e.g. Normal Flow, Max Flow, Turn-Down",
        )
    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑 Clear All Cases", key="btn_comp_clear"):
            st.session_state["comparison_cases"] = []
            st.rerun()

    if st.button("➕ Add Current Calculation to Comparison", type="primary", key="btn_comp_add"):
        if current_result is None or not current_result.success:
            st.warning("⚠ Run a successful calculation first before adding to comparison.")
        elif current_inputs is None:
            st.warning("⚠ No inputs available.")
        else:
            new_case = ComparisonCase(
                case_id=len(cases) + 1,
                case_name=case_label or f"Case {len(cases) + 1}",
                tag_number=current_inputs.tag_number or "",
                inputs=current_inputs,
                result=current_result,
                timestamp=datetime.now().strftime("%H:%M:%S"),
            )
            st.session_state["comparison_cases"].append(new_case)
            st.success(f"✅ Case '{new_case.case_name}' added to comparison table.")
            st.rerun()

    if not cases:
        st.info(
            "ℹ No cases in table yet. Run a calculation, then click "
            "**➕ Add Current Calculation** to start comparing."
        )
        return

    st.markdown(section_header_html(f"Comparison Table — {len(cases)} Case(s)"), unsafe_allow_html=True)

    # ── Build comparison dataframe ───────────────────────────────────────────
    import pandas as pd

    def _fmt(val, fmt=".3f", fallback="—"):
        if val is None:
            return fallback
        try:
            return format(val, fmt)
        except Exception:
            return str(val)

    rows = []
    for c in cases:
        r = c.result
        i = c.inputs
        row = {
            "Case": c.case_name,
            "Tag": c.tag_number or "—",
            "Time": c.timestamp,
            "Phase": r.fluid_phase.value,
            "P1 [bar a]": _fmt(r.P1_bar),
            "P2 [bar a]": _fmt(r.P2_bar),
            "ΔP [bar]": _fmt((r.P1_bar - r.P2_bar) if r.P1_bar and r.P2_bar else None),
            "Cv Required": _fmt(r.Cv_required),
            "Cv Rated": _fmt(i.Cv_rated),
            "Sizing Ratio": _fmt(r.sizing_ratio),
            "Opening [%]": _fmt(r.opening_pct, ".1f"),
            "Noise [dB(A)]": _fmt(r.noise.overall_Lpe_dba if r.noise else None, ".1f"),
            "Choked": "Yes" if r.is_choked else "No",
            "Flow Regime": r.flow_regime,
            "Cavitation": r.cavitation.regime.value if r.cavitation else "—",
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True, height=250 + len(cases) * 35)

    # ── Download comparison ──────────────────────────────────────────────────
    csv = df.to_csv(index=False).encode("utf-8")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        "⬇ Download Comparison CSV",
        data=csv,
        file_name=f"cv_comparison_{ts}.csv",
        mime="text/csv",
        use_container_width=False,
    )

    # ── Remove individual cases ──────────────────────────────────────────────
    with st.expander("🗑 Remove Individual Cases", expanded=False):
        case_labels = [f"Case {c.case_id}: {c.case_name}" for c in cases]
        remove_idx = st.selectbox("Select case to remove", options=range(len(cases)),
                                  format_func=lambda i: case_labels[i], key="comp_remove_sel")
        if st.button("Remove Selected Case", key="btn_comp_remove"):
            st.session_state["comparison_cases"].pop(remove_idx)
            st.rerun()
