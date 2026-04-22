# 🌿 ESG Integrity Auditor
### Multi-Agent Greenwashing Detection System · Powered by Local LLMs on Docker

> **100% local** — no data leaves your infrastructure.  
> Three specialized AI agents audit corporate sustainability reports against SASB/GRI frameworks, real-time news, and NASA/ESA satellite data.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose Stack                      │
│                                                                  │
│  ┌──────────────┐    ┌──────────────────────────────────────┐   │
│  │   Ollama     │    │         ESG Backend (FastAPI)         │   │
│  │ :11434       │◄───│                                      │   │
│  │              │    │  LangGraph Pipeline                  │   │
│  │ mistral:7b   │    │  ┌──────────────────────────────┐   │   │
│  │ nomic-embed  │    │  │ START                        │   │   │
│  └──────────────┘    │  │   ↓                          │   │   │
│                       │  │ Materiality Agent            │   │   │
│  ┌──────────────┐    │  │   (SASB + GRI analysis)      │   │   │
│  │  Streamlit   │    │  │   ↓                          │   │   │
│  │  UI :8501    │◄───│  │ Web Scraper Agent            │   │   │
│  │              │    │  │   (News + controversies)     │   │   │
│  │  Dashboard   │    │  │   ↓                          │   │   │
│  │  Results     │    │  │ Scientific Verifier          │   │   │
│  │  PDF Export  │    │  │   (NASA FIRMS + NOAA GML)    │   │   │
│  └──────────────┘    │  │   ↓                          │   │   │
│                       │  │ Synthesizer → PDF Report     │   │   │
│                       │  │   ↓                          │   │   │
│                       │  │ END                          │   │   │
│                       │  └──────────────────────────────┘   │   │
│                       └──────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 24.0
- Docker Compose v2
- 16 GB RAM recommended (8 GB minimum with small model)
- GPU optional but speeds up LLM inference 3–10×

### 1. Clone and configure

```bash
git clone <this-repo>
cd esg-auditor
cp .env.example .env
# Optionally add SERPAPI_KEY and NASA_API_KEY to .env
```

### 2. Launch the full stack

```bash
docker compose up --build
```

First launch downloads the `mistral:7b-instruct` model (~4 GB).  
Subsequent starts are fast.

### 3. Open the UI

```
http://localhost:8501
```

### 4. Access the API directly (optional)

```
http://localhost:8000/docs   ← Swagger UI
```

---

## What Each Agent Does

### 📄 Materiality Agent
- Evaluates report against **10 SASB topic areas** (GHG, Energy, Water, Waste, Biodiversity, Labor, Supply Chain, Ethics, Governance, Climate Risk)
- Cross-checks against **GRI Standards** (GRI 2, 3, 305, 302, 303, 306, 401, 403, 408, 409)
- Scores coverage 0–100% per topic with weighted overall materiality score
- Identifies *exactly* which required disclosures are missing

### 🔎 Web Scraper Agent  
- Searches for ESG controversies using DuckDuckGo (free) or SerpAPI (richer results)
- Classifies each result by **severity** (LOW / MEDIUM / HIGH / CRITICAL) and **category**
- Detects greenwashing indicators from news coverage

### 🛰 Scientific Verifier Agent
- Fetches **NOAA GML** atmospheric CO2 data (Mauna Loa Observatory)
- Fetches **NOAA GML** global methane (CH4) concentration
- Fetches **NASA FIRMS** active fire/deforestation events via VIIRS satellite
- LLM interprets discrepancies between reported and satellite-observed data

### 📊 Synthesizer
- Computes weighted overall score (Materiality 40% · Controversy 35% · Scientific 25%)
- Generates executive summary, greenwashing flags, recommendations
- Produces downloadable **PDF Integrity Scorecard** with full evidence trail

---

## Changing the LLM Model

Edit `.env`:
```env
OLLAMA_MODEL=llama3:8b          # Better reasoning, slower
OLLAMA_MODEL=phi3:medium         # Faster, less accurate
OLLAMA_MODEL=gemma2:9b           # Google's model, strong at analysis
```

Also update `ollama-init` in `docker-compose.yml` to pull the new model.

---

## Using a GPU

The `docker-compose.yml` includes GPU passthrough for NVIDIA cards.  
If you don't have a GPU, remove the `deploy.resources` block from the `ollama` service — it will run on CPU (slower).

```yaml
# Remove this block if no GPU:
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

---

## Adding SerpAPI (Richer Controversy Search)

1. Sign up at [serpapi.com](https://serpapi.com) (100 free searches/month)
2. Add to `.env`:
   ```env
   SERPAPI_KEY=your_key_here
   ```
3. Restart: `docker compose restart esg-backend`

Without a key, the scraper uses DuckDuckGo's free API.

---

## File Structure

```
esg-auditor/
├── docker-compose.yml          # Orchestrates all services
├── Dockerfile.backend          # FastAPI + LangGraph image
├── Dockerfile.ui               # Streamlit image
├── main.py                     # FastAPI app entry point
├── .env.example                # Environment variable template
│
├── agents/
│   ├── state.py                # TypedDicts for LangGraph state
│   ├── materiality_agent.py    # SASB/GRI gap analysis
│   ├── scraper_agent.py        # Web controversy search
│   ├── scientific_verifier.py  # NASA/NOAA data cross-reference
│   └── synthesizer.py          # Score computation + summary
│
├── frameworks/
│   └── pipeline.py             # LangGraph StateGraph definition
│
├── tools/
│   └── pdf_generator.py        # ReportLab PDF report builder
│
├── config/
│   └── esg_frameworks.py       # SASB topics + GRI standards data
│
├── ui/
│   └── app.py                  # Streamlit dashboard
│
└── data/
    └── sample_reports/
        └── acme_esg_2024.txt   # Test report
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/audit/start` | POST | Submit report text for audit |
| `/audit/upload` | POST | Upload PDF/TXT file for audit |
| `/audit/{job_id}` | GET | Poll status & get scorecard |
| `/report/{job_id}` | GET | Download PDF report |
| `/jobs` | GET | List recent jobs |
| `/health` | GET | Service health check |

---

## Extending the System

**Add a new SASB sector:**  
Edit `config/esg_frameworks.py` → `SASB_GENERAL_TOPICS`

**Add a new data source (e.g. ESA Sentinel API):**  
Add a new fetch function in `agents/scientific_verifier.py`

**Add a new agent node:**  
1. Create `agents/my_agent.py`
2. Register in `frameworks/pipeline.py` → `build_graph()`

**Swap the LLM provider:**  
Replace `ChatOllama` with any LangChain-compatible LLM — `ChatOpenAI`, `ChatGroq`, `ChatAnthropic`, etc.

---

## Troubleshooting

**Ollama model not loading:**  
```bash
docker compose logs ollama-init
docker exec esg_ollama ollama list
```

**Backend unhealthy:**  
```bash
docker compose logs esg-backend
# Check if Ollama is reachable:
docker exec esg_backend curl http://ollama:11434/api/tags
```

**UI can't connect to backend:**  
```bash
docker compose logs esg-ui
# Verify backend is healthy:
curl http://localhost:8000/health
```

**Out of memory:**  
Switch to a smaller model: `OLLAMA_MODEL=phi3:mini` in `.env`

---

## License
MIT — use freely, attribution appreciated.