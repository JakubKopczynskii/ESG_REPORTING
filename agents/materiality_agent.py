"""
Materiality Agent
─────────────────
Evaluates a corporate sustainability report against SASB and GRI frameworks.
Identifies missing disclosures, scores coverage per topic, and flags gaps.
"""

import json
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from config.esg_frameworks import SASB_GENERAL_TOPICS, GRI_STANDARDS, MATERIALITY_WEIGHTS
from agents.state import AgentState, MaterialityResult, EvidenceItem


SYSTEM_PROMPT = """You are an expert ESG analyst specializing in SASB and GRI framework compliance.
Your task is to evaluate a sustainability report excerpt against specific disclosure requirements.

ALWAYS respond with valid JSON only. No prose, no markdown fences.
Return a JSON object with these exact keys:
{
  "present": true/false,
  "coverage_score": 0.0-1.0,
  "found_disclosures": ["list of disclosures that ARE present"],
  "missing_disclosures": ["list of required disclosures that are ABSENT or vague"],
  "evidence_excerpt": "the most relevant quote or data point from the text (max 200 chars)",
  "confidence": 0.0-1.0
}"""


def _chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks for LLM context windows."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def _topic_present_in_text(text_lower: str, keywords: list[str]) -> bool:
    """Quick keyword scan before sending to LLM (saves tokens)."""
    return any(kw.lower() in text_lower for kw in keywords)


def _call_llm(llm: ChatOllama, topic_name: str, required_disclosures: list[str],
              chunk: str) -> dict:
    """Ask the LLM to evaluate one topic against one text chunk."""
    required_str = "\n".join(f"- {d}" for d in required_disclosures)
    user_msg = f"""TOPIC: {topic_name}

REQUIRED DISCLOSURES:
{required_str}

REPORT EXCERPT:
{chunk}

Evaluate whether these disclosures are present in the excerpt. Return JSON only."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_msg),
    ]
    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        # Strip any accidental markdown fences
        raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
        return json.loads(raw)
    except (json.JSONDecodeError, Exception):
        return {
            "present": False,
            "coverage_score": 0.0,
            "found_disclosures": [],
            "missing_disclosures": required_disclosures,
            "evidence_excerpt": "",
            "confidence": 0.1,
        }


def run_materiality_agent(state: AgentState) -> AgentState:
    """
    Main entry point for LangGraph.
    Evaluates each SASB topic against the report text.
    """
    print("[MaterialityAgent] Starting analysis...")
    state["current_step"] = "materiality"

    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "mistral:7b-instruct"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.1,
    )

    report_text = state["report_text"]
    text_lower = report_text.lower()
    chunks = _chunk_text(report_text)

    results: list[MaterialityResult] = []

    for topic_key, topic_info in SASB_GENERAL_TOPICS.items():
        print(f"  → Evaluating: {topic_info['name']}")

        # Skip if not even mentioned (fast path)
        if not _topic_present_in_text(text_lower, topic_info["keywords"]):
            results.append(MaterialityResult(
                topic=topic_key,
                present=False,
                coverage_score=0.0,
                missing_disclosures=topic_info["required_disclosures"],
                found_disclosures=[],
                evidence=[EvidenceItem(
                    source="text_scan",
                    excerpt=f"No keywords found for {topic_info['name']}",
                    confidence=0.95,
                    category=topic_key,
                )],
            ))
            continue

        # Find most relevant chunk(s)
        best_chunk = max(
            chunks,
            key=lambda c: sum(kw.lower() in c.lower() for kw in topic_info["keywords"])
        )

        llm_result = _call_llm(
            llm,
            topic_info["name"],
            topic_info["required_disclosures"],
            best_chunk,
        )

        evidence = []
        if llm_result.get("evidence_excerpt"):
            evidence.append(EvidenceItem(
                source="report_text",
                excerpt=llm_result["evidence_excerpt"][:300],
                confidence=llm_result.get("confidence", 0.5),
                category=topic_key,
            ))

        results.append(MaterialityResult(
            topic=topic_key,
            present=llm_result.get("present", False),
            coverage_score=float(llm_result.get("coverage_score", 0.0)),
            missing_disclosures=llm_result.get("missing_disclosures", topic_info["required_disclosures"]),
            found_disclosures=llm_result.get("found_disclosures", []),
            evidence=evidence,
        ))

    state["materiality_results"] = results

    covered = sum(1 for r in results if r["present"])
    print(f"[MaterialityAgent] Done. {covered}/{len(results)} topics covered.")
    return state