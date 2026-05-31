"""
frontend/ui_styles.py
=====================
CSS injection, app header HTML, section headers, and LinkedIn branding.

All styling is centralised here so the rest of the frontend never
contains inline CSS.

v2.0 additions
--------------
- LinkedIn profile badge (sidebar + persistent footer)
- Improved metric card styles
- Tab style overrides for better contrast
"""

from __future__ import annotations

import streamlit as st

# ── Developer identity ─────────────────────────────────────────────────────

DEVELOPER_NAME: str  = "Aseem Mehrotra"
LINKEDIN_URL: str    = "https://www.linkedin.com/in/aseem-mehrotra/"
GITHUB_URL: str      = "https://github.com/aseemm84/valve"
APP_URL: str         = "https://sizing.streamlit.app/"
APP_VERSION: str     = "2.0.0"

# ── Colour palette ─────────────────────────────────────────────────────────

PRIMARY:    str = "#1f4e79"     # Deep engineering blue
SECONDARY:  str = "#2e75b6"     # Mid blue
ACCENT:     str = "#c55a11"     # Engineering amber / orange
SUCCESS:    str = "#375623"     # Dark green
WARNING:    str = "#7f6000"     # Amber
DANGER:     str = "#c00000"     # Red
BG_LIGHT:   str = "#f5f7fa"
BG_CARD:    str = "#ffffff"
BORDER:     str = "#d1d9e0"
TEXT_DARK:  str = "#1a1a2e"

LINKEDIN_BLUE: str = "#0077B5"


def inject_custom_css() -> None:
    """
    Inject all application CSS into the Streamlit page.

    Called once from app.py at startup (before any widgets).
    """
    css = f"""
    <style>
    /* ── Base typography ──────────────────────────────────────────── */
    html, body, [class*="css"] {{
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    }}

    /* ── App header ───────────────────────────────────────────────── */
    .app-header {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {SECONDARY} 100%);
        border-radius: 12px;
        padding: 1.4rem 2rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 16px rgba(31,78,121,0.18);
    }}
    .app-header h1 {{
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.5px;
    }}
    .app-header p {{
        color: rgba(255,255,255,0.88);
        font-size: 0.92rem;
        margin: 0;
        line-height: 1.5;
    }}
    .app-header .badge-row {{
        margin-top: 0.7rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }}
    .app-header .badge {{
        background: rgba(255,255,255,0.18);
        color: #fff;
        border-radius: 20px;
        padding: 0.2rem 0.75rem;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid rgba(255,255,255,0.30);
    }}

    /* ── Section headers ──────────────────────────────────────────── */
    .section-header {{
        background: {BG_LIGHT};
        border-left: 4px solid {SECONDARY};
        border-radius: 0 8px 8px 0;
        padding: 0.55rem 1rem;
        margin: 1.2rem 0 0.8rem 0;
        font-size: 1.0rem;
        font-weight: 600;
        color: {PRIMARY};
    }}

    /* ── Metric cards ─────────────────────────────────────────────── */
    .metric-card {{
        background: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        margin-bottom: 0.6rem;
    }}
    .metric-card .label {{
        font-size: 0.78rem;
        font-weight: 600;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }}
    .metric-card .value {{
        font-size: 1.55rem;
        font-weight: 700;
        color: {PRIMARY};
        line-height: 1.2;
    }}
    .metric-card .unit {{
        font-size: 0.80rem;
        color: #6c757d;
        font-weight: 400;
    }}
    .metric-card .delta {{
        font-size: 0.80rem;
        margin-top: 0.25rem;
    }}

    /* Status variants */
    .metric-card.ok    {{ border-left: 4px solid {SUCCESS}; }}
    .metric-card.warn  {{ border-left: 4px solid {WARNING}; }}
    .metric-card.error {{ border-left: 4px solid {DANGER};  }}
    .metric-card.info  {{ border-left: 4px solid {SECONDARY}; }}

    /* ── Result summary panel ─────────────────────────────────────── */
    .result-panel {{
        background: linear-gradient(135deg, #e8f4fd 0%, #f0f8ff 100%);
        border: 1px solid {SECONDARY};
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.8rem 0;
    }}
    .result-panel h3 {{
        color: {PRIMARY};
        margin: 0 0 0.8rem 0;
        font-size: 1.05rem;
        font-weight: 700;
    }}

    /* ── Warning / alert boxes ────────────────────────────────────── */
    .alert-hard {{
        background: #fff5f5;
        border: 1px solid #f5c6cb;
        border-left: 5px solid {DANGER};
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin: 0.5rem 0;
        color: #721c24;
    }}
    .alert-soft {{
        background: #fffbf0;
        border: 1px solid #ffd966;
        border-left: 5px solid #c9a227;
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin: 0.5rem 0;
        color: {WARNING};
    }}
    .alert-ok {{
        background: #f0fff4;
        border: 1px solid #c3e6cb;
        border-left: 5px solid {SUCCESS};
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin: 0.5rem 0;
        color: {SUCCESS};
    }}
    .alert-info {{
        background: #e8f4fd;
        border: 1px solid #b8d8f5;
        border-left: 5px solid {SECONDARY};
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin: 0.5rem 0;
        color: {PRIMARY};
    }}

    /* ── LinkedIn badge ──────────────────────────────────────────── */
    .linkedin-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: {LINKEDIN_BLUE};
        color: #fff !important;
        text-decoration: none !important;
        border-radius: 6px;
        padding: 0.45rem 0.9rem;
        font-size: 0.82rem;
        font-weight: 600;
        transition: background 0.2s;
    }}
    .linkedin-badge:hover {{
        background: #005f8a;
        color: #fff !important;
    }}
    .linkedin-badge svg {{
        width: 16px;
        height: 16px;
        fill: #fff;
    }}

    /* ── Footer ──────────────────────────────────────────────────── */
    .app-footer {{
        background: {BG_LIGHT};
        border-top: 1px solid {BORDER};
        border-radius: 8px;
        padding: 0.9rem 1.5rem;
        margin-top: 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.5rem;
    }}
    .app-footer .left {{
        font-size: 0.80rem;
        color: #6c757d;
    }}
    .app-footer .right {{
        display: flex;
        gap: 0.8rem;
        align-items: center;
    }}

    /* ── Comparison table ────────────────────────────────────────── */
    .compare-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }}
    .compare-table th {{
        background: {PRIMARY};
        color: #fff;
        padding: 0.5rem 0.8rem;
        text-align: left;
        font-weight: 600;
    }}
    .compare-table td {{
        padding: 0.45rem 0.8rem;
        border-bottom: 1px solid {BORDER};
    }}
    .compare-table tr:nth-child(even) td {{
        background: {BG_LIGHT};
    }}
    .cell-ok   {{ color: {SUCCESS}; font-weight: 600; }}
    .cell-warn {{ color: {WARNING}; font-weight: 600; }}
    .cell-err  {{ color: {DANGER};  font-weight: 600; }}

    /* ── Sidebar LinkedIn strip ──────────────────────────────────── */
    .sidebar-brand {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {SECONDARY} 100%);
        border-radius: 8px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.5rem;
        text-align: center;
    }}
    .sidebar-brand .name {{
        color: #fff;
        font-size: 0.88rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }}
    .sidebar-brand .title {{
        color: rgba(255,255,255,0.80);
        font-size: 0.75rem;
    }}

    /* ── Sensitivity chart caption ───────────────────────────────── */
    .sensitivity-label {{
        font-size: 0.80rem;
        color: #6c757d;
        text-align: center;
        margin-top: 0.3rem;
    }}

    /* ── Tab styling overrides ───────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.5rem 0.9rem;
    }}
    .stTabs [aria-selected="true"] {{
        background: {PRIMARY} !important;
        color: #fff !important;
    }}

    /* ── Responsive: narrow screens ─────────────────────────────── */
    @media (max-width: 768px) {{
        .app-header h1 {{ font-size: 1.4rem; }}
        .app-footer {{ flex-direction: column; }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# HTML component builders
# ---------------------------------------------------------------------------

def app_header_html() -> str:
    """
    Return the full application header HTML string.

    Includes app title, subtitle, standard badges, and LinkedIn link.
    """
    linkedin_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        '<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 '
        '0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 '
        '3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 '
        '0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 '
        '0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 '
        '23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>'
        '</svg>'
    )
    return f"""
    <div class="app-header">
        <h1>🔧 Control Valve Sizer</h1>
        <p>
            Professional control valve sizing per <strong>IEC 60534-2-1:2011</strong> &amp;
            <strong>ANSI/ISA-75.01.01-2012</strong> &nbsp;|&nbsp;
            Noise: <strong>IEC 60534-8-3 &amp; 8-4</strong> &nbsp;|&nbsp;
            Steam: <strong>IAPWS-IF97</strong>
        </p>
        <div class="badge-row">
            <span class="badge">v{APP_VERSION}</span>
            <span class="badge">IEC 60534</span>
            <span class="badge">ISA-75.01</span>
            <span class="badge">IAPWS-IF97</span>
            <span class="badge">ASME B16.34</span>
            <a href="{LINKEDIN_URL}" target="_blank" class="linkedin-badge">
                {linkedin_svg}&nbsp;{DEVELOPER_NAME}
            </a>
        </div>
    </div>
    """


def section_header_html(title: str) -> str:
    """Return a styled section header HTML div."""
    return f'<div class="section-header">📌 {title}</div>'


def render_sidebar_branding() -> None:
    """
    Render the developer LinkedIn branding block in the sidebar.

    Called from app.py after sidebar global settings are rendered.
    """
    linkedin_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'style="width:14px;height:14px;fill:#fff;vertical-align:middle;">'
        '<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 '
        '0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 '
        '3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 '
        '0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 '
        '0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 '
        '23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>'
        '</svg>'
    )
    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand">
            <div class="name">🔧 Control Valve Sizer</div>
            <div class="title">v{APP_VERSION}</div>
        </div>
        <div style="text-align:center;margin-bottom:0.5rem;">
            <a href="{LINKEDIN_URL}" target="_blank"
               style="display:inline-flex;align-items:center;gap:0.4rem;
                      background:{LINKEDIN_BLUE};color:#fff;text-decoration:none;
                      border-radius:5px;padding:0.35rem 0.75rem;font-size:0.78rem;
                      font-weight:600;">
                {linkedin_svg}&nbsp;{DEVELOPER_NAME}
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """
    Render the persistent application footer with LinkedIn and GitHub links.

    Called at the bottom of app.py main().
    """
    linkedin_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'style="width:14px;height:14px;fill:{c};vertical-align:middle;">'.format(c=LINKEDIN_BLUE) +
        '<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 '
        '0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 '
        '3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 '
        '0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 '
        '0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 '
        '23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>'
    )

    st.markdown(
        f"""
        <div class="app-footer">
            <div class="left">
                © 2025 {DEVELOPER_NAME} &nbsp;|&nbsp; MIT License &nbsp;|&nbsp;
                Implements IEC 60534-2-1:2011, ISA-75.01.01, IEC 60534-8-3/8-4, IAPWS-IF97
            </div>
            <div class="right">
                <a href="{LINKEDIN_URL}" target="_blank"
                   style="display:inline-flex;align-items:center;gap:0.35rem;
                          background:{LINKEDIN_BLUE};color:#fff;text-decoration:none;
                          border-radius:5px;padding:0.3rem 0.7rem;font-size:0.78rem;
                          font-weight:600;">
                    {linkedin_svg}&nbsp;LinkedIn
                </a>
                <a href="{GITHUB_URL}" target="_blank"
                   style="display:inline-flex;align-items:center;gap:0.35rem;
                          background:#24292e;color:#fff;text-decoration:none;
                          border-radius:5px;padding:0.3rem 0.7rem;font-size:0.78rem;
                          font-weight:600;">
                    ⭐ GitHub
                </a>
                <a href="{APP_URL}" target="_blank"
                   style="display:inline-flex;align-items:center;gap:0.35rem;
                          background:#ff4b4b;color:#fff;text-decoration:none;
                          border-radius:5px;padding:0.3rem 0.7rem;font-size:0.78rem;
                          font-weight:600;">
                    🚀 Live App
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card_html(
    label: str,
    value: str,
    unit: str = "",
    delta: str = "",
    status: str = "info",  # ok | warn | error | info
) -> str:
    """Return an HTML metric card string for use with st.markdown."""
    delta_html = f'<div class="delta">{delta}</div>' if delta else ""
    return (
        f'<div class="metric-card {status}">'
        f'  <div class="label">{label}</div>'
        f'  <div class="value">{value} <span class="unit">{unit}</span></div>'
        f'  {delta_html}'
        f'</div>'
    )
