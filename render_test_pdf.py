#!/usr/bin/env python3
"""Standalone PDF renderer for scorecard layout testing.

Run this script to generate a PDF directly from a sample scorecard without
starting the full audit pipeline.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.pdf_generator import generate_pdf_report

DEFAULT_SCORECARD = {
    "company_name": "Meta Reporting 2025",
    "report_year": "2025",
    "overall_score": 88.2,
    "materiality_score": 82.0,
    "controversy_score": 76.0,
    "scientific_alignment_score": 69.0,
    "risk_level": "LOW",
    "summary": "This is a sample scorecard used to preview PDF layout and font/color formatting.",
    "materiality_results": [
        {
            "topic": "GHG_EMISSIONS",
            "present": True,
            "coverage_score": 0.85,
            "missing_disclosures": [],
            "found_disclosures": ["Scope 1 and 2 emissions disclosed"],
            "evidence": [],
        },
        {
            "topic": "WATER_MANAGEMENT",
            "present": False,
            "coverage_score": 0.4,
            "missing_disclosures": ["Water withdrawal by region", "Water recycling targets"],
            "found_disclosures": [],
            "evidence": [],
        },
    ],
    "controversies": [
        {
            "title": "Recent supply chain pollution incident",
            "url": "https://example.com/news/controversy",
            "snippet": "Local NGO reported a factory discharge incident...",
            "source": "Example News",
            "severity": "HIGH",
            "category": "SUPPLY_CHAIN",
            "date": "2025-12-01",
        }
    ],
    "scientific_data": [
        {
            "metric": "CO2 emissions",
            "reported_value": "6.2 MtCO2",
            "satellite_value": "7.1 MtCO2",
            "discrepancy": "Reported value appears understated by ~14%.",
            "discrepancy_score": 0.72,
            "data_source": "ESA Sentinel-5P",
            "region": "Europe",
            "evidence": {
                "source": "ESA Sentinel-5P",
                "excerpt": "Satellite-derived CO2 emissions indicate higher levels than reported.",
                "confidence": 0.9,
                "category": "EMISSIONS",
            },
        }
    ],
    "contradictions": [
        {
            "report_claim": "We achieved 100% renewable electricity in 2024.",
            "external_evidence": "News reported the plant still uses coal-fired backup generation.",
            "source_url": "https://example.com/renewable-claim",
            "reasoning": "The news item conflicts with the company claim about backup generation.",
            "severity": "MEDIUM",
        }
    ],
    "all_evidence": [
        {
            "source": "Example News",
            "excerpt": "Local NGO reported a factory discharge incident...",
            "confidence": 0.82,
            "category": "SUPPLY_CHAIN",
        },
        {
            "source": "ESA Sentinel-5P",
            "excerpt": "Satellite-derived CO2 emissions indicate higher levels than reported.",
            "confidence": 0.9,
            "category": "EMISSIONS",
        },
    ],
    "recommendations": [
        "Clarify Scope 3 emission accounting and publish methodology.",
        "Strengthen water stewardship disclosures with quantitative targets.",
        "Validate controversy claims with third-party assurance.",
    ],
    "greenwashing_flags": [
        "Overly broad renewable energy claim",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a sample PDF without running the full audit pipeline."
    )
    parser.add_argument(
        "--output",
        default="report_test/ESG_Audit_Test_Render.pdf",
        help="Output PDF path",
    )
    parser.add_argument(
        "--scorecard-file",
        type=Path,
        help="Optional JSON file containing a scorecard object to render",
    )
    parser.add_argument(
        "--company-name",
        default=None,
        help="Override the company name in the sample scorecard",
    )
    parser.add_argument(
        "--report-year",
        default=None,
        help="Override the report year in the sample scorecard",
    )
    parser.add_argument(
        "--overall-score",
        type=float,
        default=None,
        help="Override the overall score in the sample scorecard",
    )
    parser.add_argument(
        "--risk-level",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        default=None,
        help="Override the risk level in the sample scorecard",
    )
    parser.add_argument(
        "--recommendations",
        nargs="*",
        default=None,
        help="Override the recommendations list",
    )
    return parser.parse_args()


def load_scorecard(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Scorecard JSON must contain an object at the top level.")
    return data


def main() -> None:
    args = parse_args()

    if args.scorecard_file:
        scorecard = load_scorecard(args.scorecard_file)
    else:
        scorecard = DEFAULT_SCORECARD.copy()

    if args.company_name:
        scorecard["company_name"] = args.company_name
    if args.report_year:
        scorecard["report_year"] = args.report_year
    if args.overall_score is not None:
        scorecard["overall_score"] = args.overall_score
    if args.risk_level:
        scorecard["risk_level"] = args.risk_level
    if args.recommendations is not None:
        scorecard["recommendations"] = args.recommendations

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating PDF to: {output_path}")
    pdf_path = generate_pdf_report(scorecard, output_path)
    print(f"Done. PDF saved at: {pdf_path}")


if __name__ == "__main__":
    main()
