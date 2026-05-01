"""
Scorecard Synthesizer
──────────────────────
Runs after all three analysis agents to compute the final Integrity Scorecard.
Uses the LLM to generate a coherent summary, recommendations, and greenwashing flags.
"""

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, cast

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from agents.state import AgentState, IntegrityScorecard, EvidenceItem, ContradictionPair
from config.esg_frameworks import MATERIALITY_WEIGHTS


SYSTEM_PROMPT = """You are a senior ESG auditor writing an executive summary.
Based on the analysis results provided, write a concise integrity assessment.

Return ONLY valid JSON:
{
  "summary": "3-4 sentence executive summary",
  "greenwashing_flags": ["list of specific greenwashing concerns"],
  "recommendations": ["list of 5-7 actionable recommendations"],
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"
}"""

CROSS_REF_PROMPT = """Find contradictions between company claims and news.

Claims: {claims}

News: {news}

Return JSON array of contradictions, each with report_claim, external_evidence, source_url, reasoning, severity.

Only JSON, no other text."""


def _compute_materiality_score(state: AgentState) -> float:
    """Weighted average of topic coverage scores."""
    results = state.get("materiality_results", [])
    if not results:
        return 0.0
    total_weight = 0.0
    weighted_score = 0.0
    for r in results:
        topic = r["topic"]
        weight = MATERIALITY_WEIGHTS.get(topic, 0.05)
        weighted_score += r["coverage_score"] * weight
        total_weight += weight
    return round((weighted_score / total_weight) * 100, 1) if total_weight > 0 else 0.0


def _compute_controversy_score(state: AgentState) -> float:
    """Higher controversies → lower score."""
    controversies = state.get("controversies", [])
    if not controversies:
        return 100.0
    severity_penalties = {"LOW": 5, "MEDIUM": 15, "HIGH": 30, "CRITICAL": 50}
    total_penalty = sum(severity_penalties.get(c["severity"], 10) for c in controversies)
    return max(0.0, round(100.0 - total_penalty, 1))


def _compute_scientific_score(state: AgentState) -> float:
    """Average alignment with satellite data (inverse of discrepancy)."""
    data = state.get("scientific_data", [])
    if not data:
        return 50.0  # Unknown → neutral
    avg_discrepancy = sum(d["discrepancy_score"] for d in data) / len(data)
    return round((1 - avg_discrepancy) * 100, 1)


def _gather_all_evidence(state: AgentState) -> list[EvidenceItem]:
    all_evidence = []
    for r in state.get("materiality_results", []):
        all_evidence.extend(r.get("evidence", []))
    for dp in state.get("scientific_data", []):
        if dp.get("evidence"):
            all_evidence.append(dp["evidence"])
    return all_evidence


def _normalize_llm_response(resp: Any) -> str:
    content = getattr(resp, 'content', resp)
    if isinstance(content, list):
        return "\n".join(str(item) for item in content)
    return str(content)


def _invoke_llm_with_timeout(llm: ChatOllama, messages: list, timeout: int = 90):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(llm.invoke, messages)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            future.cancel()
            raise TimeoutError(f"LLM invocation timed out after {timeout} seconds")
        except Exception:
            raise


def _find_contradictions(llm: ChatOllama, state: AgentState) -> list[ContradictionPair]:
    print("[Synthesizer] Starting contradiction detection...")
    claims = []
    for r in state.get("materiality_results", []):
        claims.extend(r.get("found_disclosures", []))

    # Limit to top 5 claims to avoid overly long prompts
    claims = claims[:5]
    
    news = [f"{c['title']}: {c.get('snippet','')} (Source: {c.get('url','')})"
            for c in state.get("controversies", [])]
    
    # Limit to top 5 news items
    news = news[:5]
    
    if not claims or not news:
        print("[Synthesizer] No claims or news for contradiction check.")
        return []

    user_msg = CROSS_REF_PROMPT.format(claims=json.dumps(claims), news=json.dumps(news))
    messages = [HumanMessage(content=user_msg)]
    try:
        print("[Synthesizer] Calling LLM for contradictions...")
        resp = _invoke_llm_with_timeout(llm, messages, timeout=90)
        print("[Synthesizer] LLM response received for contradictions.")
        raw = re.sub(r"```json\s*|\s*```", "", _normalize_llm_response(resp).strip())
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            contradictions = cast(list[ContradictionPair], parsed)
            print(f"[Synthesizer] Found {len(contradictions)} contradictions.")
            return contradictions
    except Exception as e:
        print(f"[Synthesizer] Error in contradiction detection: {e}")
    return []


def _call_llm_summary(llm: ChatOllama, state: AgentState,
                       scores: dict) -> dict:
    """Generate executive summary using the LLM."""
    print("[Synthesizer] Generating LLM summary...")
    # Build concise brief for the LLM
    missing_topics = [
        r["topic"] for r in state.get("materiality_results", []) if not r["present"]
    ]
    controversy_titles = [c["title"] for c in state.get("controversies", [])[:5]]
    discrepancies = [
        d["discrepancy"] for d in state.get("scientific_data", [])
        if d.get("discrepancy")
    ]

    brief = f"""COMPANY: {state['company_name']}
SCORES: Materiality={scores['materiality']}/100, Controversies={scores['controversy']}/100, Scientific={scores['scientific']}/100

MISSING DISCLOSURES (topics): {', '.join(missing_topics) or 'None'}
CONTROVERSIES FOUND: {', '.join(controversy_titles) or 'None'}
SCIENTIFIC DISCREPANCIES: {'; '.join(filter(None, discrepancies)) or 'None found'}

Generate an ESG integrity assessment. Return JSON only."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=brief),
    ]
    try:
        resp = _invoke_llm_with_timeout(llm, messages, timeout=90)
        raw = re.sub(r"```json\s*|\s*```", "", _normalize_llm_response(resp).strip()).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[Synthesizer] LLM summary fallback due to error: {e}")
        return {
            "summary": f"ESG analysis completed for {state['company_name']}. Review individual sections for details.",
            "greenwashing_flags": [],
            "recommendations": [
                "Improve Scope 3 emissions disclosure",
                "Conduct third-party audit of supply chain",
                "Publish TCFD-aligned climate risk assessment",
                "Increase board diversity disclosure",
                "Provide externally assured sustainability data",
            ],
            "risk_level": "MEDIUM",
        }


def run_synthesizer(state: AgentState) -> AgentState:
    """Final LangGraph node: builds the Integrity Scorecard."""
    print("[Synthesizer] Computing final scorecard...")
    state["current_step"] = "synthesizer"

    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen2:1.5b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.3,
        num_predict=500,  # Limit response length to speed up
    )

    # ── Compute numeric scores ─────────────────────────────────────────────
    mat_score = _compute_materiality_score(state)
    cont_score = _compute_controversy_score(state)
    sci_score = _compute_scientific_score(state)

    overall = round(
        mat_score * 0.40 + cont_score * 0.35 + sci_score * 0.25,
        1
    )

    scores = {"materiality": mat_score, "controversy": cont_score, "scientific": sci_score}

    # ── LLM narrative ─────────────────────────────────────────────────────
    llm_result = _call_llm_summary(llm, state, scores)

    # ── Risk level (override LLM if scores are extreme) ───────────────────
    risk_level = llm_result.get("risk_level", "MEDIUM")
    if overall < 30:
        risk_level = "CRITICAL"
    elif overall < 50:
        risk_level = "HIGH"
    elif overall < 70:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # ── Assemble scorecard ────────────────────────────────────────────────
    contradictions = _find_contradictions(llm, state)

    scorecard = IntegrityScorecard(
        company_name=state["company_name"],
        report_year=state["report_year"],
        overall_score=overall,
        materiality_score=mat_score,
        controversy_score=cont_score,
        scientific_alignment_score=sci_score,
        risk_level=risk_level,
        summary=llm_result.get("summary", ""),
        materiality_results=state.get("materiality_results", []),
        controversies=state.get("controversies", []),
        scientific_data=state.get("scientific_data", []),
        contradictions=contradictions,
        all_evidence=_gather_all_evidence(state),
        recommendations=llm_result.get("recommendations", []),
        greenwashing_flags=llm_result.get("greenwashing_flags", []),
    )

    state["scorecard"] = scorecard
    print(f"[Synthesizer] Overall score: {overall}/100  Risk: {risk_level}")
    return state