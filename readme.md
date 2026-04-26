# 🌿 ESG Integrity Auditor

**Multi-Agent Greenwashing Detection System · Powered by Local LLMs on Docker**

> **100% local** — no data leaves your infrastructure.  
> Five specialized AI agents audit corporate sustainability reports against SASB/GRI frameworks, real-time news, and NASA/ESA satellite data.

---

## 🚀 Quick Start (2 minutes)

```bash
# 1. Navigate to project
cd "C:\Users\jakub\Documents\python projects\ESG_REPORTING"

# 2. Create environment configuration
copy env.example .env

# 3. Create Docker volume for LLM models
docker volume create ollama

# 4. Start all services (Ollama + Backend + UI)
docker compose up -d

# 5. Wait 5-10 minutes (first run downloads LLM model)

# 6. Open dashboard
# Browser → http://localhost:8501
```

---

## 📚 Full Documentation

**For a complete step-by-step guide, see:** [SETUP_GUIDE.md](SETUP_GUIDE.md)

That guide includes:
- ✅ Prerequisites & system requirements
- ✅ Detailed setup instructions
- ✅ Three ways to run your first audit
- ✅ Understanding how each agent works
- ✅ Complete API reference
- ✅ Troubleshooting common issues
- ✅ Advanced configuration options

---

## Architecture Overview

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         ESG INTEGRITY AUDITOR PIPELINE           │
│                                                 │
│  User Input (ESG Report)                        │
│         ↓                                       │
│  1. Materiality Agent (SASB/GRI analysis)      │
│         ↓                                       │
│  2. Web Scraper (News & controversies)         │
│         ↓                                       │
│  3. Scientific Verifier (Satellite data)       │
│         ↓                                       │
│  4. Synthesizer (Compute weighted scores)      │
│         ↓                                       │
│  5. PDF Generator (Create report)              │
│         ↓                                       │
│  Output: ESG Integrity Score + PDF Report      │
└─────────────────────────────────────────────────┘
```

**Overall Score = 40% Materiality + 35% Controversy + 25% Scientific Verification**

| Score | Grade | Rating |
|-------|-------|--------|
| 90-100 | A | Strong integrity, low greenwashing risk |
| 75-89 | B | Good practices, minor gaps |
| 60-74 | C | Fair progress, material issues |
| 45-59 | D | Poor practices, significant flags |
| 0-44 | F | Critical concerns, likely greenwashing |

---

## What Each Agent Does

### 1. Materiality Agent
Evaluates ESG report against 10 SASB topics (GHG, Energy, Water, Waste, Biodiversity, Labor, Supply Chain, Ethics, Governance, Climate Risk) and GRI standards. Identifies missing or weak disclosures.

### 2. Web Scraper Agent
Searches for ESG controversies and flags (using DuckDuckGo or SerpAPI). Classifies severity: LOW → MEDIUM → HIGH → CRITICAL.

### 3. Scientific Verifier
Fetches real satellite data (NASA FIRMS, NOAA GML) and compares against company claims. Detects greenwashing through data discrepancies.

### 4. Synthesizer
Combines results from all agents, computes weighted ESG Integrity Score, generates executive summary and recommendations.

### 5. PDF Generator
Creates professional, downloadable PDF scorecard with charts, evidence, and recommendations.

---

## How to Use

### Option 1: Web Dashboard (Easiest)
```
1. Open http://localhost:8501
2. Upload ESG report
3. Click "Start Audit"
4. View results & download PDF
```

### Option 2: REST API (Automation)
```powershell
# Start audit
$jobId = (Invoke-WebRequest -Uri http://localhost:8000/audit/start `
    -Method POST -ContentType "application/json" `
    -Body (@{company_name="Acme"; report_text="..."; report_year="2024"; industry_sector="Energy"} | ConvertTo-Json) `
    ).Content | ConvertFrom-Json | Select-Object -ExpandProperty job_id

# Poll results
Invoke-WebRequest -Uri "http://localhost:8000/audit/$jobId" -Method GET

# Download PDF
Invoke-WebRequest -Uri "http://localhost:8000/report/$jobId" -OutFile "report.pdf"
```

### Option 3: Swagger API Explorer
```
http://localhost:8000/docs
```

---

## System Requirements

- **Docker Desktop** 24.0+ ([Download](https://www.docker.com/products/docker-desktop/))
- **RAM:** 16 GB recommended (8 GB minimum)
- **Disk:** 20+ GB for images and LLM models
- **Internet:** Required for first LLM download (~3 GB)
- **GPU:** (Optional) NVIDIA with CUDA for 3-10× speedup

---

## Stopping the System

```bash
# Stop all services
docker compose down

# Stop and remove volumes (deletes cached LLM models)
docker compose down -v

# Restart specific service
docker compose restart esg-backend
```

---

## Troubleshooting

### Common Issues

**"Connection refused on port 11434"**  
→ Ollama not running: `docker logs -f esg_ollama`

**"502 Bad Gateway"**  
→ Backend crashed: `docker compose restart esg-backend`

**"TimeoutError waiting for LLM"**  
→ Model still loading (first run takes 5-10 min) or reduce LLM model size

**"ModuleNotFoundError"**  
→ Rebuild: `docker compose down && docker compose up --build`

**For more troubleshooting:** See [SETUP_GUIDE.md - Troubleshooting](SETUP_GUIDE.md#troubleshooting)

---

## Advanced Configuration

### Change LLM Model
Edit `.env`:
```env
OLLAMA_MODEL=mistral:7b          # Better reasoning (7GB)
OLLAMA_MODEL=phi3:medium         # Very fast (3GB)
OLLAMA_MODEL=llama3:8b           # High quality (8GB)
```

### Enable SerpAPI (Richer Web Search)
1. Sign up at [serpapi.com](https://serpapi.com) (free 100 searches/month)
2. Add key to `.env`: `SERPAPI_KEY=your_key`

### Enable NASA Satellite Data
1. Get key from [api.nasa.gov](https://api.nasa.gov)
2. Add key to `.env`: `NASA_API_KEY=your_key`

**For more configuration:** See [SETUP_GUIDE.md - Advanced Configuration](SETUP_GUIDE.md#advanced-configuration)

---

## Project Structure

```
ESG_REPORTING/
├── main.py                       # FastAPI application
├── docker-compose.yml            # Service orchestration
├── SETUP_GUIDE.md                # ← COMPREHENSIVE SETUP & OPERATIONS GUIDE
├── readme.md                     # This file
│
├── agents/
│   ├── materiality_agent.py      # SASB/GRI analysis
│   ├── scraper_agent.py          # Web controversy detection
│   ├── scientific_verifier.py    # Satellite data verification
│   ├── synthesizer.py            # Score computation
│   └── state.py                  # Shared state definitions
│
├── frameworks/
│   └── pipeline.py                # LangGraph pipeline orchestration
│
├── tools/
│   └── pdf_generator.py          # PDF report generation
│
├── config/
│   └── esg_frameworks.py         # SASB & GRI frameworks data
│
├── ui/
│   └── app.py                    # Streamlit dashboard
│
└── data/
    └── acme_esg_2024/            # Sample ESG report for testing
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Check if backend is running |
| POST | `/audit/start` | Start a new audit |
| GET | `/audit/{job_id}` | Poll audit status & results |
| GET | `/report/{job_id}` | Download PDF report |

Full API docs: http://localhost:8000/docs

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_MODEL` | `qwen2.5:3b` | LLM to use (fast, 3GB) |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama server URL (Docker) |
| `SERPAPI_KEY` | (empty) | Optional: for richer web search |
| `NASA_API_KEY` | (empty) | Optional: for satellite data |
| `REPORTS_DIR` | `/app/reports` | Where to save PDFs (Docker path) |

---

## Scoring Methodology

### Materiality Score (40% weight)
- Evaluates SASB topic coverage (0-100%)
- Cross-references GRI standards
- Scores missing/incomplete disclosures

### Controversy Score (35% weight)
- Weighted by severity: CRITICAL (100 pts) → HIGH (50) → MEDIUM (25) → LOW (5)
- Adjusted for recency and credibility
- Flags pattern of violations

### Scientific Verification Score (25% weight)
- Compares reported claims vs. satellite/atmospheric data
- NASA FIRMS data for deforestation & fire activity
- NOAA GML data for CO₂/methane levels
- Confidence scores for all comparisons

---

## License

MIT — use freely, attribution appreciated

---

## Getting Started

👉 **[START HERE: Complete Setup Guide →](SETUP_GUIDE.md)**

For questions, issues, or insights:
1. Check the [SETUP_GUIDE.md](SETUP_GUIDE.md) troubleshooting section
2. Review Docker logs: `docker compose logs -f`
3. Test health: `curl http://localhost:8000/health`

**Happy auditing!** 🌍