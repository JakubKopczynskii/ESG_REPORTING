"""
PDF Integrity Scorecard Generator
───────────────────────────────────
Generates a professional multi-page PDF report using ReportLab.
Includes score gauges, evidence tables, controversy log, and recommendations.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import KeepTogether

if TYPE_CHECKING:
    from agents.state import IntegrityScorecard

REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "/app/reports"))
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


def _build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "title", fontSize=28, textColor=WHITE, fontName="Helvetica-Bold",
            spaceAfter=6, alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontSize=13, textColor=ACCENT, fontName="Helvetica",
            spaceAfter=4, alignment=TA_LEFT,
        ),
        "section": ParagraphStyle(
            "section", fontSize=14, textColor=BLACK, fontName="Helvetica-Bold",
            spaceBefore=14, spaceAfter=6, borderPadding=(0, 0, 4, 0),
        ),
        "body": ParagraphStyle(
            "body", fontSize=9, textColor=BLACK, fontName="Helvetica",
            leading=14, spaceAfter=4,
        ),
        "evidence": ParagraphStyle(
            "evidence", fontSize=8, textColor=MID_GRAY, fontName="Helvetica-Oblique",
            leading=12,
        ),
        "score_big": ParagraphStyle(
            "score_big", fontSize=42, textColor=ACCENT, fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
        "score_label": ParagraphStyle(
            "score_label", fontSize=9, textColor=MID_GRAY, fontName="Helvetica",
            alignment=TA_CENTER,
        ),
        "flag": ParagraphStyle(
            "flag", fontSize=9, textColor=DANGER, fontName="Helvetica-Bold",
            leading=13, leftIndent=10,
        ),
        "recommendation": ParagraphStyle(
            "recommendation", fontSize=9, textColor=BLACK, fontName="Helvetica",
            leading=14, leftIndent=12, spaceAfter=3,
        ),
    }
    return styles


def _score_to_grade(score: float) -> str:
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    if score >= 35: return "D"
    return "F"


def _draw_cover_background(canvas, doc):
    """Dark header stripe on every page."""
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, A4[1] - 5.5*cm, A4[0], 5.5*cm, fill=1, stroke=0)
    # Footer
    canvas.setFillColor(LIGHT_GRAY)
    canvas.rect(0, 0, A4[0], 1.0*cm, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(2*cm, 0.35*cm, "ESG Integrity Auditor — Confidential")
    canvas.drawRightString(A4[0] - 2*cm, 0.35*cm,
                           f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    canvas.restoreState()


def _score_table(scorecard: "IntegrityScorecard", styles: dict) -> Table:
    """Three-column score summary table."""
    def cell(score, label):
        grade = _score_to_grade(score)
        return [
            Paragraph(f"{score:.0f}", styles["score_big"]),
            Paragraph(f"Grade {grade}", ParagraphStyle(
                "g", fontSize=12, textColor=ACCENT, fontName="Helvetica-Bold",
                alignment=TA_CENTER)),
            Paragraph(label, styles["score_label"]),
        ]

    data = [[
        cell(scorecard["materiality_score"],          "Materiality\nCoverage"),
        cell(scorecard["controversy_score"],           "Controversy\nRisk Score"),
        cell(scorecard["scientific_alignment_score"],  "Scientific\nAlignment"),
    ]]

    t = Table(data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_GRAY),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [LIGHT_GRAY]),
        ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#DDE2E8")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#DDE2E8")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    return t


def _materiality_table(results: list, styles: dict) -> Table:
    header = ["Topic", "Present", "Coverage", "Missing Disclosures"]
    rows = [header]
    for r in results:
        missing = "; ".join(r["missing_disclosures"][:2])
        if len(r["missing_disclosures"]) > 2:
            missing += f" (+{len(r['missing_disclosures'])-2} more)"
        rows.append([
            Paragraph(r["topic"].replace("_", " ").title(), styles["body"]),
            "✓" if r["present"] else "✗",
            f"{r['coverage_score']*100:.0f}%",
            Paragraph(missing or "—", styles["evidence"]),
        ])

    t = Table(rows, colWidths=[4.5*cm, 1.5*cm, 2.0*cm, 9.0*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK_BG),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("ALIGN", (1,0), (2,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDE2E8")),
    ]))
    # Colour ✓ / ✗ cells
    for i, r in enumerate(results, start=1):
        colour = ACCENT if r["present"] else DANGER
        t.setStyle(TableStyle([("TEXTCOLOR", (1,i), (1,i), colour)]))
    return t


def _controversy_table(controversies: list, styles: dict) -> Table:
    if not controversies:
        return Paragraph("No controversies identified.", styles["body"])

    header = ["Severity", "Category", "Title", "Source"]
    rows = [header]
    for c in controversies[:15]:
        rows.append([
            c["severity"],
            c["category"],
            Paragraph(c["title"][:80], styles["body"]),
            Paragraph(c.get("source", "Web")[:30], styles["evidence"]),
        ])

    t = Table(rows, colWidths=[2.0*cm, 3.0*cm, 10.0*cm, 3.0*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK_BG),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("ALIGN", (0,0), (1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDE2E8")),
    ]))
    for i, c in enumerate(controversies[:15], start=1):
        bg = SEVERITY_COLORS.get(c["severity"], WHITE)
        t.setStyle(TableStyle([("BACKGROUND", (0,i), (0,i), bg)]))
    return t


def _scientific_table(data_points: list, styles: dict) -> Table:
    if not data_points:
        return Paragraph("No scientific data comparison performed.", styles["body"])

    header = ["Metric", "Reported", "Satellite Data", "Discrepancy", "Risk"]
    rows = [header]
    for dp in data_points:
        rows.append([
            Paragraph(dp["metric"], styles["body"]),
            Paragraph(dp.get("reported_value") or "Not disclosed", styles["evidence"]),
            Paragraph(dp.get("satellite_value") or "—", styles["evidence"]),
            Paragraph(dp.get("discrepancy") or "—", styles["evidence"]),
            f"{dp['discrepancy_score']*100:.0f}%",
        ])

    t = Table(rows, colWidths=[3.5*cm, 3.0*cm, 4.5*cm, 4.5*cm, 1.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK_BG),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("ALIGN", (4,0), (4,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDE2E8")),
    ]))
    return t


def generate_pdf_report(scorecard: "IntegrityScorecard") -> str:
    """Generate the full PDF and return its file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = scorecard["company_name"].replace(" ", "_")[:30]
    filename = REPORTS_DIR / f"ESG_Audit_{safe_name}_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        topMargin=6.5*cm,
        bottomMargin=2.0*cm,
        leftMargin=2.0*cm,
        rightMargin=2.0*cm,
        onFirstPage=_draw_cover_background,
        onLaterPages=_draw_cover_background,
    )

    styles = _build_styles()
    story = []

    # ── Cover Header (inside top stripe area) ─────────────────────────────
    risk_col = RISK_COLORS.get(scorecard["risk_level"], WARNING)
    story.append(Paragraph(
        f"ESG Integrity Scorecard", styles["title"]
    ))
    story.append(Paragraph(
        f"{scorecard['company_name']}  ·  Reporting Year {scorecard['report_year']}", styles["subtitle"]
    ))
    story.append(Spacer(1, 0.3*cm))

    # Overall score pill
    overall = scorecard["overall_score"]
    grade = _score_to_grade(overall)
    story.append(Table(
        [[
            Paragraph(f"Overall Score: <b>{overall:.1f}/100</b>", ParagraphStyle(
                "os", fontSize=14, textColor=WHITE, fontName="Helvetica",
            )),
            Paragraph(f"Grade: <b>{grade}</b>", ParagraphStyle(
                "og", fontSize=14, textColor=ACCENT, fontName="Helvetica-Bold",
            )),
            Paragraph(f"Risk: <b>{scorecard['risk_level']}</b>", ParagraphStyle(
                "or", fontSize=14, textColor=risk_col, fontName="Helvetica-Bold",
            )),
        ]],
        colWidths=[6*cm, 4*cm, 4*cm],
        style=TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,-1), 4),
        ])
    ))
    story.append(Spacer(1, 0.5*cm))

    # ── Sub-score cards ────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDE2E8")))
    story.append(Spacer(1, 0.4*cm))
    story.append(_score_table(scorecard, styles))
    story.append(Spacer(1, 0.5*cm))

    # ── Executive Summary ──────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(scorecard["summary"], styles["body"]))
    story.append(Spacer(1, 0.4*cm))

    # ── Greenwashing Flags ─────────────────────────────────────────────────
    if scorecard["greenwashing_flags"]:
        story.append(Paragraph("⚠ Greenwashing Flags", styles["section"]))
        story.append(HRFlowable(width="100%", thickness=1, color=DANGER))
        story.append(Spacer(1, 0.2*cm))
        for flag in scorecard["greenwashing_flags"]:
            story.append(Paragraph(f"• {flag}", styles["flag"]))
        story.append(Spacer(1, 0.4*cm))

    # ── Materiality Analysis ───────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("1. Materiality Analysis (SASB/GRI)", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Coverage score: <b>{scorecard['materiality_score']:.1f}/100</b> — "
        f"Evaluated against {len(MATERIALITY_HEADINGS)} SASB topic areas.",
        styles["body"]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(_materiality_table(scorecard["materiality_results"], styles))
    story.append(Spacer(1, 0.5*cm))

    # ── Controversy Log ────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("2. Controversy & Reputational Risk Log", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Found <b>{len(scorecard['controversies'])} ESG controversies</b> in real-time news and databases.",
        styles["body"]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(_controversy_table(scorecard["controversies"], styles))
    story.append(Spacer(1, 0.5*cm))

    # ── Scientific Verification ────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("3. Scientific Data Cross-Reference", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Reported metrics compared against NASA FIRMS, NOAA GML atmospheric data, and ESA satellite datasets.",
        styles["body"]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(_scientific_table(scorecard["scientific_data"], styles))
    story.append(Spacer(1, 0.5*cm))

    # ── Recommendations ────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4. Recommendations", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.2*cm))
    for i, rec in enumerate(scorecard["recommendations"], 1):
        story.append(Paragraph(f"{i}. {rec}", styles["recommendation"]))
    story.append(Spacer(1, 0.5*cm))

    # ── Evidence Trail ─────────────────────────────────────────────────────
    story.append(Paragraph("5. Evidence Trail", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.2*cm))
    for ev in scorecard["all_evidence"][:30]:
        story.append(Paragraph(
            f"[{ev['category']}] <i>{ev['source']}</i> — {ev['excerpt'][:200]}",
            styles["evidence"]
        ))
        story.append(Spacer(1, 0.15*cm))

    doc.build(story)
    return str(filename)


# Used in the PDF table to show topic count
MATERIALITY_HEADINGS = [
    "GHG_EMISSIONS", "ENERGY_MANAGEMENT", "WATER_MANAGEMENT",
    "WASTE_HAZARDOUS", "BIODIVERSITY", "LABOR_PRACTICES",
    "SUPPLY_CHAIN", "BUSINESS_ETHICS", "BOARD_DIVERSITY", "CLIMATE_RISK",
]