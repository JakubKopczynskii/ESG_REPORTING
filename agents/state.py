"""
Shared state definitions for the ESG Auditor LangGraph pipeline.
All agents read from and write to this state object.
"""

from typing import TypedDict, Optional, Annotated, Callable
from langgraph.graph.message import add_messages


# ─── Evidence item (one fact + its source) ───────────────────────────────────
class EvidenceItem(TypedDict):
    source: str          # URL, doc name, or API name
    excerpt: str         # Supporting text or data snippet
    confidence: float    # 0.0–1.0
    category: str        # e.g. "GHG_EMISSIONS", "SUPPLY_CHAIN"


# ─── Per-topic materiality result ────────────────────────────────────────────
class MaterialityResult(TypedDict):
    topic: str
    present: bool
    coverage_score: float      # 0.0–1.0 (how well the topic is covered)
    missing_disclosures: list[str]
    found_disclosures: list[str]
    evidence: list[EvidenceItem]


# ─── Controversy found by the scraper ────────────────────────────────────────
class Controversy(TypedDict):
    title: str
    url: str
    snippet: str
    source: str
    severity: str          # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    category: str          # "SUPPLY_CHAIN" | "EMISSIONS" | "LABOR" | ...
    date: str


class ContradictionPair(TypedDict):
    report_claim: str      # The "fact" found in the PDF
    external_evidence: str # The news controversy or satellite data
    source_url: str        # URL to the news item
    reasoning: str         # Why the LLM thinks they clash
    severity: str          # LOW | MEDIUM | HIGH


# ─── Scientific data point from ESA/NASA ─────────────────────────────────────
class ScientificDataPoint(TypedDict):
    metric: str            # e.g. "CH4 concentration", "forest cover loss"
    reported_value: Optional[str]
    satellite_value: Optional[str]
    discrepancy: Optional[str]   # human-readable diff
    discrepancy_score: float     # 0.0 = match, 1.0 = total mismatch
    data_source: str       # "ESA Sentinel-5P", "NASA FIRMS", etc.
    region: str
    evidence: EvidenceItem


# ─── Final integrity scorecard ───────────────────────────────────────────────
class IntegrityScorecard(TypedDict):
    company_name: str
    report_year: str
    overall_score: float           # 0–100
    materiality_score: float
    controversy_score: float
    scientific_alignment_score: float
    risk_level: str                # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    summary: str
    materiality_results: list[MaterialityResult]
    controversies: list[Controversy]
    scientific_data: list[ScientificDataPoint]
    contradictions: list[ContradictionPair]
    all_evidence: list[EvidenceItem]
    recommendations: list[str]
    greenwashing_flags: list[str]


# ─── LangGraph Agent State ───────────────────────────────────────────────────
class AgentState(TypedDict):
    # Input
    company_name: str
    report_text: str
    report_year: str
    industry_sector: str

    # Agent outputs (populated in sequence)
    materiality_results: list[MaterialityResult]
    controversies: list[Controversy]
    scientific_data: list[ScientificDataPoint]

    # Intermediate
    messages: Annotated[list, add_messages]
    current_step: str
    errors: list[str]

    # Final output
    scorecard: Optional[IntegrityScorecard]
    pdf_path: Optional[str]

    # Logging
    logger: Optional[Callable[[str], None]]  # callable for logging
    job_id: Optional[str]