"""
PDF Integrity Scorecard Generator
───────────────────────────────────
Generates a professional multi-page PDF report using ReportLab.
Includes score gauges, evidence tables, controversy log, and recommendations.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING, List, Union

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    Flowable
)

if TYPE_CHECKING:
    from agents.state import IntegrityScorecard

DEFAULT_REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", DEFAULT_REPORTS_DIR))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Colour palette ──────────────────────────────────────────────────────────
DARK_BG    = colors.HexColor("#0F1923")
ACCENT     = colors.HexColor("#00C896")
WARNING    = colors.HexColor("#F5A623")
DANGER     = colors.HexColor("#E05C5C")
LIGHT_GRAY = colors.HexColor("#F0F4F8")
MID_GRAY   = colors.HexColor("#8898AA")
WHITE      = colors.white
BLACK      = colors.HexColor("#1A1A2E")

RISK_COLORS = {
    "LOW":      colors.HexColor("#00C896"),
    "MEDIUM":   colors.HexColor("#F5A623"),
    "HIGH":     colors.HexColor("#E05C5C"),
    "CRITICAL": colors.HexColor("#9B1D1D"),
}

SEVERITY_COLORS = {
    "LOW":      colors.HexColor("#D4EDDA"),
    "MEDIUM":   colors.HexColor("#FFF3CD"),
    "HIGH":     colors.HexColor("#F8D7DA"),
    "CRITICAL": colors.HexColor("#9B1D1D"),
}

MATERIALITY_HEADINGS = [
    "GHG_EMISSIONS", "ENERGY_MANAGEMENT", "WATER_MANAGEMENT",
    "WASTE_HAZARDOUS", "BIODIVERSITY", "LABOR_PRACTICES",
    "SUPPLY_CHAIN", "BUSINESS_ETHICS", "BOARD_DIVERSITY", "CLIMATE_RISK",
]

def _build_styles():
    """Build ParagraphStyles with precise leading (fontSize * 1.2) to prevent overlaps."""
    styles = {
        "title": ParagraphStyle(
            "title", fontSize=28, textColor=BLACK, fontName="Helvetica-Bold",
            leading=33.6, alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontSize=13, textColor=ACCENT, fontName="Helvetica",
            leading=15.6, alignment=TA_LEFT,
        ),
        "section": ParagraphStyle(
            "section", fontSize=14, textColor=BLACK, fontName="Helvetica-Bold",
            leading=16.8, spaceBefore=14, spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body", fontSize=10, textColor=BLACK, fontName="Helvetica",
            leading=12.0, spaceAfter=6,
        ),
        "evidence": ParagraphStyle(
            "evidence", fontSize=8, textColor=MID_GRAY, fontName="Helvetica-Oblique",
            leading=9.6,
        ),
        "score_big": ParagraphStyle(
            "score_big", fontSize=32, textColor=ACCENT, fontName="Helvetica-Bold",
            alignment=TA_CENTER, leading=38.4,
        ),
        "score_label": ParagraphStyle(
            "score_label", fontSize=9, textColor=MID_GRAY, fontName="Helvetica",
            alignment=TA_CENTER, leading=10.8,
        ),
        "flag": ParagraphStyle(
            "flag", fontSize=9, textColor=DANGER, fontName="Helvetica-Bold",
            leading=10.8, leftIndent=10, spaceAfter=4,
        ),
        "recommendation": ParagraphStyle(
            "recommendation", fontSize=10, textColor=BLACK, fontName="Helvetica",
            leftIndent=10, leading=12.0, spaceAfter=6,
        ),
        "header_text": ParagraphStyle(
            "header_text", fontSize=10, textColor=MID_GRAY, 
            fontName="Helvetica", leading=12.0, alignment=TA_LEFT,
        ),
    }
    return styles

def _score_to_grade(score: float) -> str:
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    if score >= 35: return "D"
    return "F"

def _grade_color(grade: str) -> colors.Color:
    if grade in ['A', 'B']: return ACCENT
    elif grade == 'C': return WARNING
    else: return DANGER

def _draw_cover_background(canvas, doc):
    """Draw rigid header and footer backgrounds on every page."""
    canvas.saveState()
    # Top Stripe
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, A4[1] - 5.5*cm, A4[0], 5.5*cm, fill=1, stroke=0)
    # Footer Stripe
    canvas.setFillColor(LIGHT_GRAY)
    canvas.rect(0, 0, A4[0], 1.0*cm, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(2*cm, 0.35*cm, "ESG Integrity Auditor — Confidential")
    canvas.drawRightString(A4[0] - 2*cm, 0.35*cm,
                           f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    canvas.restoreState()

def _score_table(scorecard: "IntegrityScorecard", styles: dict) -> Table:
    """Three-column score summary using Tables to prevent overflow."""
    def cell(score, label):
        grade = _score_to_grade(score)
        color = _grade_color(grade)
        return [
            Paragraph(f"{score:.0f}", styles["score_big"]),
            Paragraph(f"Grade {grade}", ParagraphStyle("gs", fontSize=12, textColor=color, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=14.4)),
            Paragraph(label, styles["score_label"]),
        ]

    data = [[
        cell(scorecard.get("materiality_score", 0), "Materiality\nCoverage"),
        cell(scorecard.get("controversy_score", 0), "Controversy\nRisk Score"),
        cell(scorecard.get("scientific_alignment_score", 0), "Scientific\nAlignment"),
    ]]

    t = Table(data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_GRAY),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#DDE2E8")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#DDE2E8")),
        ("TOPPADDING", (0,0), (-1,-1), 15),
        ("BOTTOMPADDING", (0,0), (-1,-1), 15),
    ]))
    return t

def _materiality_table(results: list, styles: dict) -> Table:
    """Materiality results table with explicit Mixed Type hinting."""
    rows: List[List[Union[Flowable, str]]] = [["Topic", "Present", "Coverage", "Missing Disclosures"]]
    for r in results:
        missing = "; ".join(r.get("missing_disclosures", [])[:2])
        if len(r.get("missing_disclosures", [])) > 2:
            missing += f" (+{len(r['missing_disclosures'])-2} more)"
        
        rows.append([
            Paragraph(r["topic"].replace("_", " ").title(), styles["body"]),
            Paragraph("✓" if r["present"] else "✗", ParagraphStyle("chk", fontSize=10, alignment=TA_CENTER, textColor=(ACCENT if r["present"] else DANGER))),
            f"{r.get('coverage_score', 0)*100:.0f}%",
            Paragraph(missing or "—", styles["evidence"]),
        ])

    t = Table(rows, colWidths=[4.5*cm, 1.8*cm, 2.2*cm, 8.5*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK_BG),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDE2E8")),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    return t

def _controversy_table(controversies: list, styles: dict) -> Table:
    """Controversy log table with explicit Mixed Type hinting."""
    rows: List[List[Union[Flowable, str]]] = [["Severity", "Category", "Title", "Source"]]
    for c in controversies[:15]:
        rows.append([
            Paragraph(c["severity"], ParagraphStyle("sev", fontSize=8, alignment=TA_CENTER, fontName="Helvetica-Bold")),
            Paragraph(c["category"], styles["body"]),
            Paragraph(c["title"][:120], styles["body"]),
            Paragraph(c.get("source", "Web")[:40], styles["evidence"]),
        ])

    t = Table(rows, colWidths=[2.2*cm, 3.5*cm, 8.3*cm, 3.0*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK_BG),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDE2E8")),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    
    for i, c in enumerate(controversies[:15], start=1):
        bg = SEVERITY_COLORS.get(c["severity"], WHITE)
        t.setStyle(TableStyle([("BACKGROUND", (0,i), (0,i), bg)]))
    return t

def _scientific_table(data_points: list, styles: dict) -> Table:
    """Scientific verification table with explicit Mixed Type hinting."""
    rows: List[List[Union[Flowable, str]]] = [["Metric", "Reported", "Satellite Data", "Discrepancy", "Risk"]]
    if not data_points:
        rows.append([Paragraph("No scientific data comparison performed.", styles["body"]), "", "", "", ""])
    else:
        for dp in data_points:
            rows.append([
                Paragraph(dp["metric"], styles["body"]),
                Paragraph(str(dp.get("reported_value") or "N/A"), styles["evidence"]),
                Paragraph(str(dp.get("satellite_value") or "—"), styles["evidence"]),
                Paragraph(str(dp.get("discrepancy") or "—"), styles["evidence"]),
                f"{dp.get('discrepancy_score', 0)*100:.0f}%",
            ])
            
    t = Table(rows, colWidths=[3.5*cm, 3.0*cm, 4.0*cm, 4.5*cm, 2.0*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK_BG),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDE2E8")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    return t

def generate_pdf_report(scorecard: "IntegrityScorecard", output_path: Optional[str] = None) -> str:
    """Generate the full PDF with bulletproof layout and return its file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = scorecard.get("company_name", "Unknown").replace(" ", "_")[:30]
    
    if output_path:
        filename = output_path
    else:
        filename = REPORTS_DIR / f"ESG_Audit_{safe_name}_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        topMargin=6.5*cm,
        bottomMargin=2.0*cm,
        leftMargin=2.0*cm,
        rightMargin=2.0*cm,
    )

    styles = _build_styles()
    story = []

    # 1. Header Text - Fixed 'ń' encoding issue
    story.append(Paragraph("ESG Integrity Report | Generated by Jakub Kopczynski ESG Analysis Tool", styles["header_text"]))
    story.append(Spacer(1, 0.4*cm))

    # 2. Cover Header - Forced inside a Table to PREVENT overlap natively
    header_data: List[List[Flowable]] = [
        [Paragraph("ESG Integrity Scorecard", styles["title"])],
        [Paragraph(f"{scorecard.get('company_name', 'Unknown')}  ·  Reporting Year {scorecard.get('report_year', 'N/A')}", styles["subtitle"])]
    ]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),  # Rigid space between title and subtitle
        ('BOTTOMPADDING', (0,1), (-1,1), 12), # Rigid space below subtitle
    ]))
    story.append(header_table)

    # 3. High-Level Scores
    overall = scorecard.get("overall_score", 0)
    grade = _score_to_grade(overall)
    risk_col = RISK_COLORS.get(scorecard.get("risk_level", "MEDIUM"), WARNING)
    
    score_data: List[List[Flowable]] = [[
        Paragraph(f"Overall Score: <b>{overall:.1f}/100</b>", ParagraphStyle("os", fontSize=14, textColor=BLACK, leading=16.8)),
        Paragraph(f"Grade: <b>{grade}</b>", ParagraphStyle("og", fontSize=14, textColor=ACCENT, fontName="Helvetica-Bold", leading=16.8)),
        Paragraph(f"Risk: <b>{scorecard.get('risk_level', 'MEDIUM')}</b>", ParagraphStyle("or", fontSize=14, textColor=risk_col, fontName="Helvetica-Bold", leading=16.8)),
    ]]
    
    score_table = Table(score_data, colWidths=[6*cm, 4*cm, 4*cm])
    score_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.5*cm))

    # 4. Executive Summary
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDE2E8")))
    story.append(Spacer(1, 0.4*cm))
    story.append(KeepTogether(_score_table(scorecard, styles)))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Executive Summary", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    story.append(Paragraph(scorecard.get("summary", "No summary available."), styles["body"]))

    # 5. Greenwashing Flags
    if scorecard.get("greenwashing_flags"):
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("⚠ Greenwashing Flags", styles["section"]))
        story.append(HRFlowable(width="100%", thickness=1, color=DANGER, spaceAfter=8))
        for flag in scorecard.get("greenwashing_flags"):
            story.append(Paragraph(f"• {flag}", styles["flag"]))

    # 6. Detailed Tables
    story.append(PageBreak())
    story.append(Paragraph("1. Materiality Analysis (SASB/GRI)", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    story.append(_materiality_table(scorecard.get("materiality_results", []), styles))

    story.append(PageBreak())
    story.append(Paragraph("2. Controversy Log", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    story.append(_controversy_table(scorecard.get("controversies", []), styles))

    story.append(PageBreak())
    story.append(Paragraph("3. Scientific Data Cross-Reference", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    story.append(_scientific_table(scorecard.get("scientific_data", []), styles))

    # 7. Recommendations
    story.append(Spacer(1, 1.0*cm))
    story.append(Paragraph("4. Recommendations", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    for i, rec in enumerate(scorecard.get("recommendations", []), 1):
        story.append(Paragraph(f"<b>{i}.</b> {rec}", styles["recommendation"]))

    # 8. Evidence Trail
    story.append(Spacer(1, 1.0*cm))
    story.append(Paragraph("5. Evidence Trail", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    for ev in scorecard.get("all_evidence", [])[:30]:
        story.append(Paragraph(
            f"[{ev.get('category', 'N/A')}] <i>{ev.get('source', 'Unknown')}</i> — {ev.get('excerpt', '')[:200]}",
            styles["evidence"]
        ))
        story.append(Spacer(1, 0.15*cm))

    doc.build(story, onFirstPage=_draw_cover_background, onLaterPages=_draw_cover_background)
    return str(filename)