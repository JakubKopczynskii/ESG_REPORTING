"""
ESG Integrity Auditor — Streamlit Dashboard
"""

import time
import json
import os
from pathlib import Path

import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def _backend_healthy() -> bool:
    """Check if the backend is reachable (server-side call)."""
    try:
        r = httpx.get(f"{BACKEND_URL}/health", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ESG Integrity Auditor",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
  }

  .stApp {
    background: #0D1117;
    color: #E6EDF3;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #161B22 !important;
    border-right: 1px solid #21262D;
  }

  /* Score card */
  .score-card {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 12px;
    padding: 24px 20px;
    text-align: center;
    transition: border-color 0.2s;
  }
  .score-card:hover { border-color: #00C896; }
  .score-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 3.2rem;
    font-weight: 600;
    line-height: 1;
  }
  .score-label {
    font-size: 0.78rem;
    color: #8B949E;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 6px;
  }
  .score-grade {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.0rem;
    margin-top: 4px;
  }

  /* Risk badge */
  .risk-LOW    { color: #00C896; }
  .risk-MEDIUM { color: #F5A623; }
  .risk-HIGH   { color: #E05C5C; }
  .risk-CRITICAL { color: #FF4D4F; }

  /* Flag item */
  .flag-item {
    background: rgba(224,92,92,0.08);
    border-left: 3px solid #E05C5C;
    padding: 8px 14px;
    border-radius: 0 6px 6px 0;
    margin: 6px 0;
    font-size: 0.88rem;
    color: #E05C5C;
  }

  /* Section header */
  .section-header {
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #00C896;
    border-bottom: 1px solid #21262D;
    padding-bottom: 8px;
    margin: 20px 0 14px;
  }

  /* Agent step */
  .agent-step {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 8px;
    margin: 6px 0;
    font-size: 0.85rem;
    background: #161B22;
    border: 1px solid #21262D;
  }
  .step-dot { width: 10px; height: 10px; border-radius: 50%; }
  .step-done { background: #00C896; }
  .step-active { background: #F5A623; animation: pulse 1s infinite; }
  .step-wait { background: #30363D; }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  /* Override Streamlit button */
  .stButton > button {
    background: #00C896 !important;
    color: #0D1117 !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 0.5rem 2rem !important;
  }
  .stButton > button:hover {
    background: #00A87E !important;
  }

  /* Upload zone */
  [data-testid="stFileUploader"] {
    border: 1px dashed #30363D !important;
    border-radius: 8px;
    background: #161B22;
  }

  /* Expander */
  [data-testid="stExpander"] {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 8px;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    background: #161B22;
    border-radius: 8px 8px 0 0;
    gap: 0;
  }
  .stTabs [data-baseweb="tab"] {
    color: #8B949E !important;
    padding: 10px 20px;
  }
  .stTabs [aria-selected="true"] {
    color: #00C896 !important;
    border-bottom: 2px solid #00C896 !important;
  }

  div[data-testid="metric-container"] {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 12px;
  }

  h1, h2, h3 { color: #E6EDF3 !important; }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def grade(score: float) -> str:
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    if score >= 35: return "D"
    return "F"

def score_color(score: float) -> str:
    if score >= 70: return "#00C896"
    if score >= 45: return "#F5A623"
    return "#E05C5C"

def risk_color(risk: str) -> str:
    return {"LOW": "#00C896", "MEDIUM": "#F5A623", "HIGH": "#E05C5C", "CRITICAL": "#FF4D4F"}.get(risk, "#F5A623")

def api_post(path: str, **kwargs):
    try:
        r = httpx.post(f"{BACKEND_URL}{path}", timeout=60, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        st.error(
            f"❌ Cannot reach the backend at **{BACKEND_URL}**\n\n"
            "**Troubleshooting:**\n"
            "- Run `docker compose ps` — is `esg-backend` healthy?\n"
            "- Run `docker compose logs esg-backend` for errors\n"
            "- Wait 30s after `docker compose up` for Ollama model to load"
        )
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def api_get(path: str):
    try:
        r = httpx.get(f"{BACKEND_URL}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# ─── Gauge chart ──────────────────────────────────────────────────────────────

def gauge_chart(value: float, title: str, height: int = 180) -> go.Figure:
    col = score_color(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "", "font": {"size": 28, "color": col, "family": "IBM Plex Mono"}},
        title={"text": title, "font": {"size": 11, "color": "#8B949E", "family": "IBM Plex Sans"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#30363D",
                     "tickfont": {"size": 9, "color": "#8B949E"}},
            "bar": {"color": col, "thickness": 0.3},
            "bgcolor": "#161B22",
            "bordercolor": "#21262D",
            "steps": [
                {"range": [0, 35],  "color": "rgba(224,92,92,0.08)"},
                {"range": [35, 65], "color": "rgba(245,166,35,0.08)"},
                {"range": [65, 100],"color": "rgba(0,200,150,0.08)"},
            ],
            "threshold": {"line": {"color": col, "width": 2}, "value": value},
        },
    ))
    fig.update_layout(
        height=height, margin={"l": 20, "r": 20, "t": 40, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "IBM Plex Sans"},
    )
    return fig


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 8px 0 20px">
      <div style="font-size:1.4rem;font-weight:700;color:#00C896">🌿 ESG Auditor</div>
      <div style="font-size:0.75rem;color:#8B949E;margin-top:2px">Integrity · Transparency · Accountability</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Navigation")
    page = st.radio("Navigate", ["🔍 New Audit", "📊 Results Dashboard", "📋 Job History"],
                    label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### Agent Pipeline")
    steps = [
        ("📄", "Materiality Agent", "SASB + GRI analysis"),
        ("🔎", "Web Scraper Agent", "News + controversies"),
        ("🛰️", "Scientific Verifier", "NASA/ESA cross-ref"),
        ("📊", "Synthesizer", "Score + PDF report"),
    ]
    for icon, name, desc in steps:
        st.markdown(f"""
        <div style="padding:8px 10px;margin:4px 0;border-radius:8px;
                    background:#0D1117;border:1px solid #21262D;font-size:0.82rem">
          <span style="margin-right:8px">{icon}</span>
          <b style="color:#E6EDF3">{name}</b><br>
          <span style="color:#8B949E;font-size:0.75rem;padding-left:20px">{desc}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.72rem;color:#8B949E">
      Powered by <b style="color:#00C896">Ollama + LangGraph</b><br>
      Local LLMs · No data leaves your infra
    </div>
    """, unsafe_allow_html=True)


# ─── Backend status banner ────────────────────────────────────────────────────
if not _backend_healthy():
    st.warning(
        "⚠️ **Backend not reachable** — the ESG agent service is unavailable.  \n"
        f"Trying: `{BACKEND_URL}`  \n\n"
        "**To fix:** run `docker compose up` in your project folder, then wait ~30 seconds for Ollama to load.",
        icon="🔌",
    )

# ─── Page: New Audit ──────────────────────────────────────────────────────────

if "🔍 New Audit" in page:
    st.markdown("## Start a New ESG Audit")
    st.markdown('<div style="color:#8B949E;margin-bottom:24px">Upload or paste a corporate sustainability report to begin multi-agent analysis.</div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        tab_paste, tab_upload = st.tabs(["✏️ Paste Report Text", "📁 Upload PDF / TXT"])

        sample_text = st.session_state.get("sample_text", "")

        with tab_paste:
            report_text = st.text_area(
                "Sustainability report content",
                value=sample_text,
                key="report_text",
                height=340,
                placeholder="Paste the full text of the corporate sustainability / ESG report here...\n\nThe longer and more complete the report, the more accurate the analysis.",
                label_visibility="collapsed",
            )

        with tab_upload:
            uploaded = st.file_uploader(
                "Drop PDF or TXT file",
                type=["pdf", "txt"],
                label_visibility="collapsed",
            )
            if uploaded:
                st.success(f"✓ Loaded: {uploaded.name} ({uploaded.size/1024:.1f} KB)")

    with col_right:
        st.markdown('<div class="section-header">Audit Configuration</div>', unsafe_allow_html=True)

        company_name = st.text_input("Company Name", placeholder="e.g. Acme Corporation")
        report_year = st.selectbox("Report Year", ["2024", "2023", "2022", "2021"], index=0)
        industry_sector = st.selectbox(
            "Industry Sector",
            ["General", "Energy & Utilities", "Materials & Mining",
             "Consumer Goods", "Technology", "Financial Services",
             "Healthcare", "Transportation", "Real Estate", "Agriculture"],
        )

        st.markdown('<div class="section-header">Analysis Modules</div>', unsafe_allow_html=True)
        do_materiality = st.checkbox("Materiality Agent (SASB/GRI)", value=True)
        do_scraper     = st.checkbox("Web Scraper Agent (News/Controversies)", value=True)
        do_scientific  = st.checkbox("Scientific Verifier (NASA/ESA)", value=True)

        st.markdown("")
        run_btn = st.button("🚀 Run Full Audit", use_container_width=True)

    if run_btn:
        # Validate
        if not company_name.strip():
            st.error("Please enter a company name.")
            st.stop()

        text_to_audit = ""
        if uploaded:
            text_to_audit = "__uploaded__"  # signal to use upload endpoint
        elif report_text and len(report_text.strip()) > 50:
            text_to_audit = report_text
        else:
            st.error("Please provide report text or upload a file.")
            st.stop()

        # Submit
        with st.spinner("Submitting audit job..."):
            if uploaded:
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                data = {
                    "company_name": company_name,
                    "report_year": report_year,
                    "industry_sector": industry_sector,
                }
                try:
                    r = httpx.post(f"{BACKEND_URL}/audit/upload",
                                   data=data, files=files, timeout=30)
                    r.raise_for_status()
                    result = r.json()
                except Exception as e:
                    st.error(f"Upload failed: {e}")
                    st.stop()
            else:
                result = api_post(
                    "/audit/start",
                    json={
                        "company_name": company_name,
                        "report_text": text_to_audit,
                        "report_year": report_year,
                        "industry_sector": industry_sector,
                    },
                )

        if result:
            st.session_state["current_job_id"] = result["job_id"]
            st.session_state["current_company"] = company_name
            st.success(f"✓ Audit started! Job ID: `{result['job_id']}`")
            st.info("Switch to **📊 Results Dashboard** to monitor progress.")

    # Show demo hint
    if not st.session_state.get("current_job_id"):
        st.markdown("---")
        with st.expander("💡 Try a sample report (click to expand)"):
            sample = """Acme Global Corp Sustainability Report 2024

Greenhouse Gas Emissions:
Our total Scope 1 emissions were 2.3 million metric tons CO2e in 2024, a 5% reduction from 2023.
Scope 2 (market-based) emissions totaled 890,000 metric tons CO2e.
We have set a net-zero target for 2045 across all scopes.

Energy Management:
Total energy consumption: 8.4 TWh. Renewable energy share: 34%.
We are investing in 500MW of new solar capacity by 2026.

Supply Chain:
We conducted ESG audits on 67% of Tier 1 suppliers in 2024.
A zero-tolerance policy for child labor is enforced through annual audits.

Labor Practices:
Total recordable incident rate: 0.42 per 200,000 hours worked.
Employee turnover rate: 12.3%. Gender pay gap: 4.2% (in favour of men, being addressed).

Board & Governance:
Board composition: 40% women, 60% independent directors.
ESG committee meets quarterly.

Water:
Total water withdrawal: 12.4 million cubic metres.
Water in high-stress regions: 23%."""

            st.code(sample, language="text")
            if st.button("Use this sample"):
                st.session_state["sample_text"] = sample
                st.rerun()

    if st.session_state.get("sample_text"):
        st.info("Sample loaded — fill in 'Company Name' and click Run Full Audit.")


# ─── Page: Results Dashboard ──────────────────────────────────────────────────

elif "📊 Results Dashboard" in page:
    job_id = st.session_state.get("current_job_id")

    if not job_id:
        st.info("No active audit. Start one from **🔍 New Audit**.")
        st.stop()

    company = st.session_state.get("current_company", "Company")
    st.markdown(f"## Audit Results — {company}")

    # Poll status
    status_placeholder = st.empty()
    job = api_get(f"/audit/{job_id}")

    if not job:
        st.error("Could not connect to backend.")
        st.stop()

    status = job.get("status", "unknown")

    # ── Running state ─────────────────────────────────────────────────────
    if status in ("queued", "running"):
        with status_placeholder.container():
            st.markdown("### 🔄 Analysis in Progress")

            steps_state = {
                "queued":  [0, 0, 0, 0],
                "running": [1, 0, 0, 0],
            }.get(status, [1, 1, 1, 0])

            labels = ["Materiality Agent", "Web Scraper Agent", "Scientific Verifier", "Synthesizer & PDF"]
            icons = ["📄", "🔎", "🛰️", "📊"]
            descs = [
                "Evaluating SASB/GRI disclosure gaps...",
                "Searching news for controversies...",
                "Cross-referencing satellite data...",
                "Computing score & generating PDF...",
            ]
            step_status = ["done", "active", "wait", "wait"]

            cols = st.columns(4)
            for i, col in enumerate(cols):
                with col:
                    dot_cls = step_status[i]
                    bg = {"done": "rgba(0,200,150,0.08)", "active": "rgba(245,166,35,0.08)", "wait": "#161B22"}.get(dot_cls)
                    border = {"done": "#00C896", "active": "#F5A623", "wait": "#21262D"}.get(dot_cls)
                    st.markdown(f"""
                    <div style="background:{bg};border:1px solid {border};border-radius:10px;
                                padding:16px;text-align:center">
                      <div style="font-size:1.8rem">{icons[i]}</div>
                      <div style="font-size:0.85rem;font-weight:600;color:#E6EDF3;margin:8px 0 4px">{labels[i]}</div>
                      <div style="font-size:0.75rem;color:#8B949E">{descs[i]}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("")
            progress_bar = st.progress(0.3 if status == "running" else 0.05)
            st.caption(f"Job ID: `{job_id}` · Status: **{status}**")

        time.sleep(4)
        st.rerun()

    elif status == "failed":
        st.error(f"Audit failed: {job.get('error', 'Unknown error')}")
        st.stop()

    elif status == "completed":
        status_placeholder.empty()
        scorecard = job.get("scorecard", {})

        if not scorecard:
            st.warning("Audit completed but no scorecard found.")
            st.stop()

        overall = scorecard.get("overall_score", 0)
        risk = scorecard.get("risk_level", "MEDIUM")
        rc = risk_color(risk)

        # ── Hero banner ────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:#161B22;border:1px solid #21262D;border-radius:14px;
                    padding:24px 28px;margin-bottom:24px;display:flex;
                    align-items:center;justify-content:space-between">
          <div>
            <div style="font-size:0.75rem;color:#8B949E;text-transform:uppercase;letter-spacing:.1em">
              Overall Integrity Score
            </div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:3.8rem;
                        font-weight:700;color:{score_color(overall)};line-height:1">
              {overall:.1f}<span style="font-size:1.5rem;color:#8B949E">/100</span>
            </div>
            <div style="font-size:0.85rem;color:#8B949E;margin-top:4px">
              Grade: <b style="color:{score_color(overall)}">{grade(overall)}</b>
              &nbsp;·&nbsp;
              Risk Level: <b style="color:{rc}">{risk}</b>
            </div>
          </div>
          <div style="text-align:right">
            <div style="font-size:0.75rem;color:#8B949E">Report Year</div>
            <div style="font-size:1.5rem;color:#E6EDF3;font-weight:600">
              {scorecard.get('report_year','—')}
            </div>
            <div style="margin-top:12px">
              <span style="background:{rc};color:#000;padding:4px 14px;border-radius:20px;
                           font-size:0.8rem;font-weight:700">{risk} RISK</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Three gauge charts ─────────────────────────────────────────────
        gc1, gc2, gc3 = st.columns(3)
        with gc1:
            st.plotly_chart(gauge_chart(
                scorecard.get("materiality_score", 0), "Materiality Coverage"),
                use_container_width=True)
        with gc2:
            st.plotly_chart(gauge_chart(
                scorecard.get("controversy_score", 0), "Controversy Score"),
                use_container_width=True)
        with gc3:
            st.plotly_chart(gauge_chart(
                scorecard.get("scientific_alignment_score", 0), "Scientific Alignment"),
                use_container_width=True)

        # ── Summary + flags ────────────────────────────────────────────────
        col_sum, col_flags = st.columns([3, 2], gap="large")

        with col_sum:
            st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color:#C9D1D9;line-height:1.7;font-size:0.9rem">{scorecard.get("summary","")}</div>',
                       unsafe_allow_html=True)

        with col_flags:
            flags = scorecard.get("greenwashing_flags", [])
            st.markdown(f'<div class="section-header">⚠ Greenwashing Flags ({len(flags)})</div>', unsafe_allow_html=True)
            if flags:
                for f in flags:
                    st.markdown(f'<div class="flag-item">{f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#00C896;font-size:0.88rem">✓ No greenwashing flags detected</div>',
                           unsafe_allow_html=True)

        # ── Detailed tabs ─────────────────────────────────────────────────
        st.markdown("")
        t1, t2, t3, t4 = st.tabs(["📋 Materiality", "📰 Controversies", "🛰 Scientific Data", "✅ Recommendations"])

        with t1:
            mat_results = scorecard.get("materiality_results", [])
            if mat_results:
                df = pd.DataFrame([{
                    "Topic": r["topic"].replace("_", " ").title(),
                    "Present": "✓" if r["present"] else "✗",
                    "Coverage %": f"{r['coverage_score']*100:.0f}%",
                    "Missing": ", ".join(r["missing_disclosures"][:2]) + (
                        f" (+{len(r['missing_disclosures'])-2})" if len(r['missing_disclosures']) > 2 else ""),
                } for r in mat_results])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No materiality results available.")

        with t2:
            controversies = scorecard.get("controversies", [])
            if controversies:
                df = pd.DataFrame([{
                    "Severity": c["severity"],
                    "Category": c["category"],
                    "Title": c["title"][:80],
                    "Source": c.get("source", "")[:30],
                    "Date": c.get("date", ""),
                } for c in controversies])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.success("✓ No controversies found in real-time search.")

        with t3:
            sci_data = scorecard.get("scientific_data", [])
            if sci_data:
                df = pd.DataFrame([{
                    "Metric": d["metric"],
                    "Reported": d.get("reported_value") or "Not disclosed",
                    "Satellite/Scientific": d.get("satellite_value") or "—",
                    "Discrepancy": d.get("discrepancy") or "—",
                    "Risk %": f"{d['discrepancy_score']*100:.0f}%",
                    "Source": d.get("data_source", ""),
                } for d in sci_data])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No scientific comparison data.")

        with t4:
            recs = scorecard.get("recommendations", [])
            if recs:
                for i, rec in enumerate(recs, 1):
                    st.markdown(f"""
                    <div style="background:#161B22;border:1px solid #21262D;border-left:3px solid #00C896;
                                border-radius:0 8px 8px 0;padding:12px 16px;margin:8px 0;font-size:0.88rem;color:#E6EDF3">
                      <b style="color:#00C896">{i:02d}.</b> {rec}
                    </div>
                    """, unsafe_allow_html=True)

        # ── PDF Download ───────────────────────────────────────────────────
        st.markdown("---")
        if job.get("has_pdf"):
            st.markdown('<div class="section-header">📄 Download Report</div>', unsafe_allow_html=True)
            try:
                pdf_resp = httpx.get(f"{BACKEND_URL}/report/{job_id}", timeout=20)
                if pdf_resp.status_code == 200:
                    st.download_button(
                        label="⬇️ Download Integrity Scorecard PDF",
                        data=pdf_resp.content,
                        file_name=f"ESG_Audit_{company.replace(' ','_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            except Exception as e:
                st.warning(f"Could not fetch PDF: {e}")


# ─── Page: Job History ────────────────────────────────────────────────────────

elif "📋 Job History" in page:
    st.markdown("## Job History")
    jobs = api_get("/jobs")

    if not jobs:
        st.info("No jobs found. Run an audit first.")
    else:
        df = pd.DataFrame(jobs)
        df.columns = ["Job ID", "Company", "Status", "Created"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("### Load a Previous Result")
        selected = st.selectbox(
            "Select job",
            [j["job_id"] for j in jobs],
            format_func=lambda jid: next(
                (f"{j['company_name']} — {j['status']} ({j['created_at'][:10]})"
                 for j in jobs if j["job_id"] == jid), jid)
        )
        if st.button("Load Selected Job"):
            st.session_state["current_job_id"] = selected
            st.session_state["current_company"] = next(
                (j["company_name"] for j in jobs if j["job_id"] == selected), "")
            st.success("Job loaded. Switch to Results Dashboard.")