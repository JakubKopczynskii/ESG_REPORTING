"""
Web Scraper Agent
─────────────────
Searches real-time news, NGO reports, and databases for ESG controversies
related to the company's supply chain, emissions, and governance.
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime

import httpx
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from agents.state import AgentState, Controversy

# ─── News sources to query ────────────────────────────────────────────────────
NEWS_SOURCES = [
    "https://newsapi.org/v2/everything",          # NewsAPI (needs key)
    "https://serpapi.com/search",                  # SerpAPI (needs key)
]

CONTROVERSY_KEYWORDS = [
    "greenwashing lawsuit",
    "emissions fraud",
    "supply chain violation",
    "child labor supply chain",
    "deforestation",
    "carbon offset fraud",
    "ESG controversy",
    "environmental fine",
    "human rights violation",
    "forced labor",
]

SYSTEM_PROMPT = """You are an investigative ESG journalist assessing corporate controversies.
Given a news article or snippet, extract ESG-relevant controversy details.

Return ONLY valid JSON:
{
  "is_esg_controversy": true/false,
  "title": "concise title",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "category": "EMISSIONS|SUPPLY_CHAIN|LABOR|GOVERNANCE|BIODIVERSITY|OTHER",
  "summary": "one sentence summary of the controversy",
  "greenwashing_indicators": ["list of specific greenwashing red flags if any"]
}"""


async def _fetch_duckduckgo(company: str, keyword: str, client: httpx.AsyncClient) -> list[dict]:
    """Use DuckDuckGo Instant Answer API (no key required) as fallback."""
    results = []
    try:
        query = f"{company} {keyword}"
        resp = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            # RelatedTopics contains snippets
            for item in data.get("RelatedTopics", [])[:3]:
                if isinstance(item, dict) and item.get("Text"):
                    results.append({
                        "title": item.get("Text", "")[:100],
                        "snippet": item.get("Text", ""),
                        "url": item.get("FirstURL", ""),
                        "source": "DuckDuckGo",
                    })
    except Exception as e:
        print(f"  [scraper] DuckDuckGo error: {e}")
    return results


async def _fetch_serpapi(company: str, keyword: str, client: httpx.AsyncClient, api_key: str) -> list[dict]:
    """Use SerpAPI for richer Google News results."""
    results = []
    try:
        resp = await client.get(
            "https://serpapi.com/search",
            params={
                "q": f"{company} {keyword}",
                "tbm": "nws",
                "api_key": api_key,
                "num": 5,
            },
            timeout=15.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("news_results", [])[:5]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "source": item.get("source", "Google News"),
                    "date": item.get("date", ""),
                })
    except Exception as e:
        print(f"  [scraper] SerpAPI error: {e}")
    return results


async def _search_controversies(company: str, serpapi_key: str | None) -> list[dict]:
    """Aggregate raw search results from all available sources."""
    raw_results = []
    # Use a focused subset of keywords to stay within rate limits
    keywords_to_search = CONTROVERSY_KEYWORDS[:5]

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = []
        for kw in keywords_to_search:
            if serpapi_key:
                tasks.append(_fetch_serpapi(company, kw, client, serpapi_key))
            else:
                tasks.append(_fetch_duckduckgo(company, kw, client))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                raw_results.extend(r)

    # Deduplicate by URL
    seen = set()
    deduped = []
    for item in raw_results:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            deduped.append(item)

    return deduped


def _classify_controversy(llm: ChatOllama, item: dict) -> dict | None:
    """Ask LLM to classify whether the article is an ESG controversy."""
    text = f"TITLE: {item.get('title', '')}\nSNIPPET: {item.get('snippet', '')}"
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=text),
    ]
    try:
        resp = llm.invoke(messages)
        raw = re.sub(r"```json\s*|\s*```", "", resp.content.strip()).strip()
        result = json.loads(raw)
        if result.get("is_esg_controversy"):
            return result
    except Exception:
        pass
    return None


def run_scraper_agent(state: AgentState) -> AgentState:
    """Main LangGraph entry point for the Web Scraper Agent."""
    print("[ScraperAgent] Searching for controversies...")
    state["current_step"] = "scraper"

    company = state["company_name"]
    serpapi_key = os.getenv("SERPAPI_KEY") or None

    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen2:1.5b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.1,
    )

    # Run async search in sync context
    raw_results = asyncio.run(_search_controversies(company, serpapi_key))
    print(f"  Found {len(raw_results)} raw results")

    controversies: list[Controversy] = []
    for item in raw_results[:20]:  # Cap LLM calls
        classified = _classify_controversy(llm, item)
        if classified:
            controversies.append(Controversy(
                title=classified.get("title") or item.get("title", "Unknown"),
                url=item.get("url", ""),
                snippet=classified.get("summary") or item.get("snippet", ""),
                source=item.get("source", "Web"),
                severity=classified.get("severity", "MEDIUM"),
                category=classified.get("category", "OTHER"),
                date=item.get("date", datetime.now().strftime("%Y-%m")),
            ))

    state["controversies"] = controversies
    print(f"[ScraperAgent] Found {len(controversies)} ESG controversies.")
    return state