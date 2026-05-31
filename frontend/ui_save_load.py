"""
frontend/ui_save_load.py
========================
Save and Load calculation UI tab.

Features
--------
- Download current calculation as a self-contained JSON file
  (serialised via Pydantic v2 SavedCalculation model)
- Upload a previously saved JSON file to restore all inputs
  and results into session state

The JSON file is human-readable and can be used for:
  - Audit trail / calculation register
  - Version control (git-trackable)
  - Sharing between engineers
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import streamlit as st

from backend.models import SavedCalculation, SizingInputs, SizingResult


def render_save_load_panel(
    current_inputs: SizingInputs | None,
    current_result: SizingResult | None,
) -> dict[str, Any]:
    """
    Render the Save / Load panel.

    Parameters
    ----------
    current_inputs : SizingInputs | None
        The current sizing inputs from session state.
    current_result : SizingResult | None
        The current sizing result from session state.

    Returns
    -------
    dict[str, Any]
        Keys: 'loaded_inputs', 'loaded_result' — non-None if a file was loaded.
    """
    output: dict[str, Any] = {"loaded_inputs": None, "loaded_result": None}

    st.markdown("## 💾 Save & Load Calculations")
    st.markdown(
        "Save your current calculation to a portable JSON file for archiving, "
        "sharing, or reloading in a future session. Load any previously saved file "
        "to restore all inputs and results instantly."
    )

    col_save, col_load = st.columns(2, gap="large")

    # ── SAVE ────────────────────────────────────────────────────────────────
    with col_save:
        st.markdown("### 💾 Save Current Calculation")

        if current_inputs is None or current_result is None:
            st.info(
                "ℹ Run a calculation first before saving. "
                "Go to **Process Inputs** and click **🔬 CALCULATE**."
            )
        else:
            case_name = st.text_input(
                "Case Name",
                value=current_inputs.case_name or "Sizing Case 1",
                max_chars=120,
                help="Descriptive name for this calculation (stored in the file)",
                key="save_case_name",
            )
            tag_number = st.text_input(
                "Instrument / Tag Number",
                value=current_inputs.tag_number or "",
                max_chars=40,
                placeholder="e.g. FV-101",
                key="save_tag_number",
            )

            # Build SavedCalculation
            saved = SavedCalculation(
                app_version="2.0.0",
                schema_version="2",
                saved_at=datetime.now().isoformat(timespec="seconds"),
                case_name=case_name,
                tag_number=tag_number,
                inputs=current_inputs.model_copy(
                    update={"case_name": case_name, "tag_number": tag_number}
                ),
                result=current_result,
            )

            json_bytes = saved.model_dump_json(indent=2).encode("utf-8")
            filename = _make_filename(tag_number, case_name)

            st.download_button(
                label="⬇ Download Calculation JSON",
                data=json_bytes,
                file_name=filename,
                mime="application/json",
                use_container_width=True,
                type="primary",
            )

            st.markdown(
                f"""
                <div style="font-size:0.80rem;color:#6c757d;margin-top:0.5rem;">
                📄 File: <code>{filename}</code><br>
                🕐 Saved at: {saved.saved_at}<br>
                📦 Schema: v{saved.schema_version}
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("🔍 Preview JSON (first 60 lines)", expanded=False):
                preview_lines = json.dumps(
                    json.loads(json_bytes), indent=2
                ).split("\n")[:60]
                st.code("\n".join(preview_lines) + "\n...", language="json")

    # ── LOAD ────────────────────────────────────────────────────────────────
    with col_load:
        st.markdown("### 📂 Load Saved Calculation")

        uploaded_file = st.file_uploader(
            "Upload a saved JSON calculation file",
            type=["json"],
            key="load_file_uploader",
            help="Select a .json file previously downloaded from this application.",
        )

        if uploaded_file is not None:
            try:
                raw = uploaded_file.read()
                data = json.loads(raw)

                saved_calc = SavedCalculation.model_validate(data)

                # Show a preview of what's in the file
                st.markdown("**File contents:**")
                st.markdown(
                    f"""
                    | Field | Value |
                    |---|---|
                    | Case Name | {saved_calc.case_name or '—'} |
                    | Tag Number | {saved_calc.tag_number or '—'} |
                    | Saved At | {saved_calc.saved_at} |
                    | App Version | {saved_calc.app_version} |
                    | Fluid Phase | {saved_calc.inputs.fluid_phase.value} |
                    | Unit System | {saved_calc.inputs.unit_system.value} |
                    | Cv Required | {saved_calc.result.Cv_required:.3f if saved_calc.result.Cv_required else 'N/A'} |
                    | Noise [dB(A)] | {saved_calc.result.noise.overall_Lpe_dba if saved_calc.result.noise else 'N/A'} |
                    """
                )

                if st.button(
                    "✅ Load This Calculation",
                    type="primary",
                    use_container_width=True,
                    key="btn_load_confirm",
                ):
                    output["loaded_inputs"] = saved_calc.inputs
                    output["loaded_result"] = saved_calc.result
                    st.success(
                        f"✅ Calculation '{saved_calc.case_name}' loaded successfully! "
                        "Navigate to **Sizing Results** to view results, or "
                        "**Process Inputs** to modify and recalculate."
                    )
                    st.rerun()

            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file. Please upload a file exported from this application.")
            except Exception as exc:
                st.error(f"❌ Failed to load file: {exc}")
                st.markdown(
                    "Ensure the file was saved by this application (v2.0+) and has not been "
                    "manually modified."
                )

    # ── Format guide ────────────────────────────────────────────────────────
    with st.expander("ℹ File Format Information", expanded=False):
        st.markdown(
            """
            **JSON Schema (v2)**

            The saved file is a self-contained JSON document conforming to the
            `SavedCalculation` Pydantic v2 schema. Key sections:

            ```json
            {
              "app_version": "2.0.0",
              "schema_version": "2",
              "saved_at": "2025-01-15T14:30:00",
              "case_name": "FV-101 Design Case",
              "tag_number": "FV-101",
              "inputs": { ... all SizingInputs fields ... },
              "result": { ... all SizingResult fields ... }
            }
            ```

            The file is human-readable, version-controllable (git), and suitable
            for inclusion in a project calculation register.

            **Compatibility:** Files saved in v2.0+ can be loaded in any v2.0+ session.
            Files from v1.x are not supported.
            """
        )

    return output


def _make_filename(tag: str, case: str) -> str:
    """Generate a safe, descriptive filename for the saved JSON."""
    import re
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = tag or case or "calculation"
    safe = re.sub(r"[^\w\-]", "_", base)[:30]
    return f"cv_sizing_{safe}_{timestamp}.json"
