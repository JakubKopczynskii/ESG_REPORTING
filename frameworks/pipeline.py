"""
ESG Auditor LangGraph Pipeline
────────────────────────────────
Directed graph:
  START
    └─► materiality_agent
          └─► scraper_agent
                └─► scientific_verifier
                      └─► synthesizer
                            └─► pdf_generator
                                  └─► END
"""

import os
import sys
from typing import Any, Literal, cast

from langgraph.graph import END, START, StateGraph

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from agents.state import AgentState, IntegrityScorecard
from agents.materiality_agent import run_materiality_agent
from agents.scraper_agent import run_scraper_agent
from agents.scientific_verifier import run_scientific_verifier
from agents.synthesizer import run_synthesizer
from tools.pdf_generator import generate_pdf_report


# ─── Wrapper nodes ────────────────────────────────────────────────────────────

def node_materiality(state: AgentState) -> AgentState:
    return run_materiality_agent(state)

def node_scraper(state: AgentState) -> AgentState:
    return run_scraper_agent(state)

def node_scientific(state: AgentState) -> AgentState:
    return run_scientific_verifier(state)

def node_synthesizer(state: AgentState) -> AgentState:
    return run_synthesizer(state)

def node_pdf(state: AgentState) -> AgentState:
    """Generate the final PDF report."""
    if state.get("scorecard"):
        try:
            pdf_path = generate_pdf_report(cast(IntegrityScorecard, state["scorecard"]))
            state["pdf_path"] = pdf_path
            print(f"[PDFGenerator] Report saved to {pdf_path}")
        except Exception as e:
            error_message = f"PDF generation failed: {e}"
            print(f"[PDFGenerator] {error_message}")
            state["errors"] = state.get("errors", []) + [error_message]
            raise
    return state


def should_continue_after_scraper(state: AgentState) -> Literal["scientific", "synthesizer"]:
    """Skip scientific verifier if no emissions data in report (optional shortcut)."""
    report_lower = state.get("report_text", "").lower()
    has_emissions = any(kw in report_lower for kw in ["emissions", "co2", "carbon", "methane"])
    return "scientific" if has_emissions else "synthesizer"


def build_graph() -> Any:
    """Construct and compile the LangGraph pipeline."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("materiality", node_materiality)
    graph.add_node("scraper", node_scraper)
    graph.add_node("scientific", node_scientific)
    graph.add_node("synthesizer", node_synthesizer)
    graph.add_node("pdf_gen", node_pdf)

    # Wire edges
    graph.add_edge(START, "materiality")
    graph.add_edge("materiality", "scraper")
    graph.add_conditional_edges(
        "scraper",
        should_continue_after_scraper,
        {"scientific": "scientific", "synthesizer": "synthesizer"},
    )
    graph.add_edge("scientific", "synthesizer")
    graph.add_edge("synthesizer", "pdf_gen")
    graph.add_edge("pdf_gen", END)

    return graph.compile()


# Singleton compiled graph
_compiled_graph = None

def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_audit(
    company_name: str,
    report_text: str,
    report_year: str = "2025",
    industry_sector: str = "General",
) -> AgentState:
    """
    Public API: run the full ESG audit pipeline.
    Returns the final AgentState including the scorecard and PDF path.
    """
    initial_state = AgentState(
        company_name=company_name,
        report_text=report_text,
        report_year=report_year,
        industry_sector=industry_sector,
        materiality_results=[],
        controversies=[],
        scientific_data=[],
        messages=[],
        current_step="start",
        errors=[],
        scorecard=None,
        pdf_path=None,
    )

    graph = get_graph()
    final_state = graph.invoke(initial_state)  # type: ignore
    return final_state