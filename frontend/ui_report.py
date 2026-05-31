"""
frontend/ui_report.py
=====================
Report generation — PDF (fpdf2) and Excel (openpyxl).

If either library is unavailable, the report type is gracefully disabled
with an informational message rather than crashing.
"""

from __future__ import annotations

import io
from datetime import datetime

import streamlit as st

from backend.constants import BAR_TO_PSI
from backend.models import FluidPhase, SizingResult
from frontend.ui_styles import DEVELOPER_NAME, GITHUB_URL, LINKEDIN_URL, section_header_html


def render_report_panel(result: SizingResult) -> None:
    """
    Render the report download panel.

    Parameters
    ----------
    result : SizingResult
        Completed sizing result for inclusion in the report.
    """
    st.markdown(section_header_html("Engineering Report"), unsafe_allow_html=True)

    if not result.success:
        st.warning("⚠ Reports are only available for successful calculations. Fix errors first.")
        return

    col_pdf, col_xlsx = st.columns(2, gap="large")

    # ── PDF Report ───────────────────────────────────────────────────────────
    with col_pdf:
        st.markdown("### 📄 PDF Report")
        st.markdown(
            "Formatted engineering calculation sheet with all inputs, "
            "results, noise analysis, and warnings."
        )
        try:
            pdf_bytes = _generate_pdf(result)
            tag = result.tag_number or "valve"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "⬇ Download PDF Report",
                data=pdf_bytes,
                file_name=f"cv_sizing_{tag}_{ts}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
        except ImportError:
            st.info(
                "ℹ PDF generation requires `fpdf2`. "
                "Install with: `pip install fpdf2`\n\n"
                "Use the Excel report or Save/Load JSON as alternatives."
            )
        except Exception as exc:
            st.error(f"PDF generation error: {exc}")

    # ── Excel Report ─────────────────────────────────────────────────────────
    with col_xlsx:
        st.markdown("### 📊 Excel Calculation Sheet")
        st.markdown(
            "Machine-readable Excel workbook with all parameters "
            "in a structured table, suitable for calculation registers."
        )
        try:
            xlsx_bytes = _generate_excel(result)
            tag = result.tag_number or "valve"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "⬇ Download Excel Report",
                data=xlsx_bytes,
                file_name=f"cv_sizing_{tag}_{ts}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )
        except ImportError:
            st.info(
                "ℹ Excel generation requires `openpyxl`. "
                "Install with: `pip install openpyxl`"
            )
        except Exception as exc:
            st.error(f"Excel generation error: {exc}")

    # ── Report preview ────────────────────────────────────────────────────────
    with st.expander("👁 Report Preview (text)", expanded=False):
        st.text(_build_text_report(result))


# ---------------------------------------------------------------------------
# PDF generation (fpdf2)
# ---------------------------------------------------------------------------

def _generate_pdf(result: SizingResult) -> bytes:
    """Generate a PDF report. Raises ImportError if fpdf2 not installed."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Header ────────────────────────────────────────────────────────────────
    pdf.set_fill_color(31, 78, 121)
    pdf.rect(10, 10, 190, 16, "F")
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(12, 13)
    pdf.cell(0, 10, "CONTROL VALVE SIZING CALCULATION SHEET", ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(10, 28)
    pdf.cell(0, 5, f"Standard: IEC 60534-2-1:2011 / ISA-75.01.01-2012", ln=True)
    pdf.cell(0, 5, f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')} | {DEVELOPER_NAME}", ln=True)
    pdf.ln(3)

    # ── Tag / case identification ────────────────────────────────────────────
    _pdf_section(pdf, "Instrument Identification")
    _pdf_row(pdf, "Tag Number", result.tag_number or "—")
    _pdf_row(pdf, "Case Name", result.case_name or "—")
    _pdf_row(pdf, "Fluid Phase", result.fluid_phase.value)
    pdf.ln(2)

    # ── Primary results ──────────────────────────────────────────────────────
    _pdf_section(pdf, "Primary Sizing Results")
    if result.Cv_required:
        _pdf_row(pdf, "Cv Required", f"{result.Cv_required:.4f}")
    if result.Cv_margin:
        _pdf_row(pdf, "Cv with Margin", f"{result.Cv_margin:.4f}")
    if result.Kv_required:
        _pdf_row(pdf, "Kv Required", f"{result.Kv_required:.4f}")
    if result.sizing_ratio:
        _pdf_row(pdf, "Sizing Ratio (Cv_req/Cv_rated)", f"{result.sizing_ratio:.4f}")
    if result.opening_pct:
        _pdf_row(pdf, "Estimated Opening", f"{result.opening_pct:.1f} %")
    _pdf_row(pdf, "Flow Regime", result.flow_regime)
    _pdf_row(pdf, "Choked Flow", "YES" if result.is_choked else "No")
    pdf.ln(2)

    # ── Process conditions ───────────────────────────────────────────────────
    _pdf_section(pdf, "Process Conditions")
    if result.P1_bar:
        _pdf_row(pdf, "P1 (Inlet, absolute)", f"{result.P1_bar:.4f} bar a")
    if result.P2_bar:
        _pdf_row(pdf, "P2 (Outlet, absolute)", f"{result.P2_bar:.4f} bar a")
    if result.P1_bar and result.P2_bar:
        _pdf_row(pdf, "ΔP Available", f"{result.P1_bar - result.P2_bar:.4f} bar")
    if result.T1_K:
        _pdf_row(pdf, "T1 (Inlet)", f"{result.T1_K - 273.15:.1f} °C ({result.T1_K:.2f} K)")
    if result.rho1_kgm3:
        _pdf_row(pdf, "ρ1 (Inlet Density)", f"{result.rho1_kgm3:.4f} kg/m³")
    pdf.ln(2)

    # ── Noise ────────────────────────────────────────────────────────────────
    if result.noise and result.noise.overall_Lpe_dba is not None:
        _pdf_section(pdf, "Noise Analysis")
        n = result.noise
        _pdf_row(pdf, "Lpe (External SPL at 1 m)", f"{n.overall_Lpe_dba:.1f} dB(A)")
        _pdf_row(pdf, "Site Noise Limit", f"{n.limit_dba:.0f} dB(A)")
        _pdf_row(pdf, "Status", "EXCEEDS LIMIT" if n.exceeds_limit else "Within limit")
        if n.Lpi_db:
            _pdf_row(pdf, "Lpi (Internal Sound Power)", f"{n.Lpi_db:.1f} dB re 1pW")
        if n.TL_db:
            _pdf_row(pdf, "TL (Transmission Loss)", f"{n.TL_db:.1f} dB")
        if n.Mvc:
            _pdf_row(pdf, "Mvc (Mach at VC)", f"{n.Mvc:.4f}")
        if n.eta_acoustic:
            _pdf_row(pdf, "η_a (Acoustic Efficiency)", f"{n.eta_acoustic:.3e}")
        pdf.ln(2)

    # ── Warnings ─────────────────────────────────────────────────────────────
    if result.warnings or result.hard_violations:
        _pdf_section(pdf, "Engineering Warnings")
        for v in result.hard_violations:
            pdf.set_text_color(192, 0, 0)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, f"[HARD] {v}", ln=True)
        for w in result.warnings:
            pdf.set_text_color(127, 96, 0)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, f"[WARN] {w}", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    # ── Footer ───────────────────────────────────────────────────────────────
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Control Valve Sizer | {LINKEDIN_URL} | {GITHUB_URL}", ln=True, align="C")

    return bytes(pdf.output())


def _pdf_section(pdf, title: str) -> None:
    pdf.set_fill_color(232, 244, 253)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(31, 78, 121)
    pdf.cell(0, 7, f"  {title}", border=0, fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)


def _pdf_row(pdf, label: str, value: str) -> None:
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(80, 5, f"  {label}", border=0)
    pdf.cell(0, 5, value, border=0, ln=True)


# ---------------------------------------------------------------------------
# Excel generation (openpyxl)
# ---------------------------------------------------------------------------

def _generate_excel(result: SizingResult) -> bytes:
    """Generate an Excel report. Raises ImportError if openpyxl not installed."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CV Sizing"

    # Header
    ws["A1"] = "Control Valve Sizing Calculation Sheet"
    ws["A1"].font = Font(bold=True, size=14, color="1F4E79")
    ws["A2"] = f"Standard: IEC 60534-2-1:2011 | Generated: {datetime.now().strftime('%d %b %Y %H:%M')}"
    ws["A2"].font = Font(italic=True, size=9, color="555555")
    ws.merge_cells("A1:D1")
    ws.merge_cells("A2:D2")

    rows = [
        ("Parameter", "Value", "Unit", "Note"),
        ("TAG NUMBER", result.tag_number or "—", "", ""),
        ("CASE NAME", result.case_name or "—", "", ""),
        ("Fluid Phase", result.fluid_phase.value, "", ""),
        ("Flow Regime", result.flow_regime, "", ""),
    ]

    if result.Cv_required:
        rows.append(("Cv Required", f"{result.Cv_required:.4f}", "", "At design conditions"))
    if result.Cv_margin:
        rows.append(("Cv with Margin", f"{result.Cv_margin:.4f}", "", "Including sizing margin"))
    if result.Kv_required:
        rows.append(("Kv Required", f"{result.Kv_required:.4f}", "", "Kv = Cv × 0.8646"))
    if result.sizing_ratio:
        rows.append(("Sizing Ratio", f"{result.sizing_ratio:.4f}", "", "Cv_req / Cv_rated"))
    if result.opening_pct:
        rows.append(("Opening %", f"{result.opening_pct:.1f}", "%", "Estimated from inherent char."))
    if result.P1_bar:
        rows.append(("P1 Absolute", f"{result.P1_bar:.4f}", "bar a", ""))
    if result.P2_bar:
        rows.append(("P2 Absolute", f"{result.P2_bar:.4f}", "bar a", ""))
    if result.P1_bar and result.P2_bar:
        rows.append(("ΔP Available", f"{result.P1_bar - result.P2_bar:.4f}", "bar", ""))
    if result.noise and result.noise.overall_Lpe_dba is not None:
        rows.append(("Lpe Noise", f"{result.noise.overall_Lpe_dba:.1f}", "dB(A)", "External SPL at 1 m"))

    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(bold=True, color="FFFFFF")

    start_row = 4
    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=start_row + r_idx, column=c_idx, value=val)
            if r_idx == 0:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")
            if r_idx % 2 == 0 and r_idx > 0:
                cell.fill = PatternFill("solid", fgColor="EBF4FD")

    # Column widths
    for col, width in zip(["A", "B", "C", "D"], [35, 20, 12, 40]):
        ws.column_dimensions[col].width = width

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Plain text report
# ---------------------------------------------------------------------------

def _build_text_report(result: SizingResult) -> str:
    """Generate a plain text report for the expander preview."""
    lines = [
        "=" * 60,
        "CONTROL VALVE SIZING CALCULATION",
        f"Standard: IEC 60534-2-1:2011 / ISA-75.01.01-2012",
        f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
        f"Developer: {DEVELOPER_NAME} | {LINKEDIN_URL}",
        "=" * 60,
        f"Tag: {result.tag_number or '—'}",
        f"Case: {result.case_name or '—'}",
        f"Phase: {result.fluid_phase.value}",
        f"Flow Regime: {result.flow_regime}",
        "-" * 40,
    ]
    if result.Cv_required:
        lines.append(f"Cv Required:    {result.Cv_required:.4f}")
    if result.Cv_margin:
        lines.append(f"Cv with Margin: {result.Cv_margin:.4f}")
    if result.Kv_required:
        lines.append(f"Kv Required:    {result.Kv_required:.4f}")
    if result.sizing_ratio:
        lines.append(f"Sizing Ratio:   {result.sizing_ratio:.4f}")
    if result.opening_pct:
        lines.append(f"Opening:        {result.opening_pct:.1f}%")
    if result.P1_bar and result.P2_bar:
        lines.append(f"P1:             {result.P1_bar:.4f} bar a")
        lines.append(f"P2:             {result.P2_bar:.4f} bar a")
        lines.append(f"ΔP:             {result.P1_bar - result.P2_bar:.4f} bar")
    if result.noise and result.noise.overall_Lpe_dba:
        lines.append(f"Noise (Lpe):    {result.noise.overall_Lpe_dba:.1f} dB(A)")
    lines.append("-" * 40)
    if result.hard_violations:
        lines.append("HARD VIOLATIONS:")
        for v in result.hard_violations:
            lines.append(f"  [!] {v}")
    if result.warnings:
        lines.append("WARNINGS:")
        for w in result.warnings:
            lines.append(f"  [W] {w}")
    if not result.hard_violations and not result.warnings:
        lines.append("All checks passed — no violations or warnings.")
    lines.append("=" * 60)
    return "\n".join(lines)
