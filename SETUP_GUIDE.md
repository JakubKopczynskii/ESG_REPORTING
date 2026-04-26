# 🌿 ESG Integrity Auditor - Complete Step-by-Step Setup Guide

## Quick Navigation
1. **[System Requirements](#system-requirements)** — What you need
2. **[Initial Setup (5 minutes)](#initial-setup-5-minutes)** — Configure your environment
3. **[Starting the System](#starting-the-system)** — Launch the stack
4. **[Running Your First Audit](#running-your-first-audit)** — Three ways to run it
5. **[Understanding the Architecture](#understanding-the-architecture)** — How it works
6. **[API Reference](#api-reference)** — All available endpoints
7. **[Troubleshooting](#troubleshooting)** — Common issues & fixes

---

## System Requirements

### Minimum Setup
- **OS:** Windows 10+, macOS, or Linux
- **Docker Desktop:** v24.0+ ([Download](https://www.docker.com/products/docker-desktop/))
- **Docker Compose:** v2 (included in Docker Desktop)
- **RAM:** 16 GB recommended; 8 GB minimum (slower)
- **Disk Space:** 20+ GB for Docker images and LLM models
- **Internet:** Required for first LLM model download (~3GB)

### Optional
- **GPU:** NVIDIA with CUDA for 3-10× faster inference
- **SerpAPI Key:** For richer web search (free 100 searches/month)
- **NASA API Key:** For satellite data verification (free)

### Test Your Docker Installation

```powershell
# Open PowerShell and run these commands:
docker --version
docker compose --version
docker run hello-world
```

You should see version numbers without errors.

---

## Initial Setup (5 minutes)

### Step 1a: Open Project Directory

```powershell
# Navigate to your project:
cd "C:\Users\jakub\Documents\python projects\ESG_REPORTING"

# Verify you see these files:
dir
# You should see: docker-compose.yml, Dockerfile.backend, main.py, env.example, etc.
```

### Step 1b: Create Environment Configuration

```powershell
# Copy the example environment file:
copy env.example .env

# Open .env in your editor (Notepad, VSCode, etc.)
notepad .env
```

**Review the .env file content:**

```env
OLLAMA_BASE_URL=http://ollama:11434     # Keep as-is (internal Docker URL)
OLLAMA_MODEL=qwen2.5:3b                 # Fast LLM (~3GB). Options:
                                         # - llama3:8b (better reasoning)
                                         # - phi3:medium (very fast)
                                         # - mistral:7b (balanced)

OLLAMA_EMBED_MODEL=nomic-embed-text     # Keep as-is (for similarity search)

# OPTIONAL: For better web search (instead of DuckDuckGo)
SERPAPI_KEY=                             # Leave blank or add key from serpapi.com

# OPTIONAL: For NASA satellite data
NASA_API_KEY=                            # Leave blank or add key from api.nasa.gov

REPORTS_DIR=/app/reports                # Keep as-is (Docker container path)
```

Save and close the file.

### Step 1c: Create Docker Volume for LLM Models

```powershell
# Check if the ollama volume exists:
docker volume ls | findstr ollama

# If it doesn't exist, create it:
docker volume create ollama

# Verify it was created:
docker volume ls | findstr ollama
```

This volume persists your downloaded LLM models, so you don't re-download them each time.

### Step 1d: Create Required Directories

```powershell
# Create directories for reports and sample data:
mkdir reports -ErrorAction SilentlyContinue
mkdir data -ErrorAction SilentlyContinue

dir   # You should now see reports/ and data/ folders
```

---

## Starting the System

### ▶️ Option A: Full Stack (Recommended for First Time)

This starts **all three services**: Ollama (LLM), Backend (API), and UI (Dashboard).

```powershell
# Make sure you're in the project directory:
cd "C:\Users\jakub\Documents\python projects\ESG_REPORTING"

# Start all services in the background:
docker compose up -d

# Monitor startup progress (press Ctrl+C to stop watching):
docker compose logs -f
```

**⏱️ First Startup Timeline:**
- **0-30 seconds:** Containers start
- **30-60 seconds:** Ollama connects
- **1-5 minutes:** LLM model downloads (~3GB for qwen2.5:3b)
- **5-10 minutes:** Model loads into memory
- **✅ Ready** when you see no more error messages

**Subsequent Startups:** 30-60 seconds (models already cached)

### Verify All Services Are Running

```powershell
# Check which containers are running:
docker ps

# You should see three containers:
# - esg_ollama (port 11434)
# - esg_backend (port 8000)
# - esg_ui (port 8501)

# If any are missing, check logs:
docker logs esg_backend
docker logs esg_ollama
docker logs esg_ui
```

### 🌐 Access the UI

Open your browser to:
```
http://localhost:8501
```

You should see the **ESG Integrity Auditor Dashboard** with dark theme.

---

### ▶️ Option B: Backend Only (For API Integration)

If you only need the headless API without the dashboard:

```powershell
docker compose up -d ollama esg-backend

# Test the backend is running:
curl http://localhost:8000/health
# Should return: {"status": "ok", "timestamp": "..."}
```

---

### ▶️ Option C: Manual Development (For Debugging)

If you want to run components locally without Docker:

```powershell
# Install Python dependencies:
pip install -r requirements.backend.txt

# Start Ollama on port 11434 separately (must be running)
# Then run the backend directly:
python main.py
# Server starts at http://localhost:8000
```

---

## Running Your First Audit

### 🎯 Method 1: Web Dashboard (Easiest)

**Step 1:** Open http://localhost:8501

**Step 2:** Fill out the form:
- **Company Name:** `Acme Corporation`
- **ESG Report:** Paste your ESG/sustainability report text here
- **Report Year:** `2024`
- **Industry:** `Energy` (or choose from dropdown)

**Step 3:** Click **"🔍 Start Audit"**

**Step 4:** Monitor Progress
- Real-time agent status updates
- Progress indicators show which step is running
- Results appear automatically

**Step 5:** View Results
- Interactive score breakdown
- Greenwashing flags and controversies
- Recommendation list

**Step 6:** Download PDF
- Click the download button to save professional PDF report

---

### 🎯 Method 2: REST API (For Automation)

#### 2a. Start an Audit

```powershell
# Create the request body:
$body = @{
    company_name    = "Acme Corporation"
    report_text     = "Our sustainability report shows..."  # Paste full ESG report
    report_year     = "2024"
    industry_sector = "Energy"
} | ConvertTo-Json

# Send the request:
$response = Invoke-WebRequest `
    -Uri http://localhost:8000/audit/start `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# Extract the job ID:
$jobId = ($response.Content | ConvertFrom-Json).job_id
Write-Host "✓ Audit started! Job ID: $jobId"
```

#### 2b. Poll for Results

```powershell
$jobId = "550e8400-e29b-41d4-a716-446655440000"  # Use your job ID from above

# Poll status (repeat until status = "completed"):
do {
    Start-Sleep -Seconds 5
    $status = Invoke-WebRequest `
        -Uri "http://localhost:8000/audit/$jobId" `
        -Method GET | ConvertFrom-Json
    Write-Host "Status: $($status.status) | Score: $($status.scorecard.overall_score)"
} while ($status.status -eq "running")

Write-Host "✓ Audit complete!"
```

#### 2c. Download PDF Report

```powershell
$jobId = "550e8400-e29b-41d4-a716-446655440000"

# Download the PDF:
Invoke-WebRequest `
    -Uri "http://localhost:8000/report/$jobId" `
    -OutFile "esg_report_$jobId.pdf" `
    -Method GET

Write-Host "✓ PDF saved: esg_report_$jobId.pdf"
```

---

### 🎯 Method 3: Interactive API Explorer

Visit http://localhost:8000/docs in your browser to see the **Swagger UI** with interactive test fields for all endpoints.

---

## Understanding the Architecture

### System Overview

```
┌────────────────────────────────────────────────────────────────┐
│                      Your Computer                              │
│                                                                 │
│  ┌──────────────┐        ┌──────────────────────────────────┐  │
│  │   Ollama     │        │    ESG Backend (FastAPI)         │  │
│  │  Port 11434  │◄──────►│    Port 8000                     │  │
│  │              │        │                                  │  │
│  │ LLM Models:  │        │  Processes audit requests in     │  │
│  │ qwen2.5:3b   │        │  this order:                     │  │
│  │ nomic-embed  │        │                                  │  │
│  └──────────────┘        │  1. Materiality Agent            │  │
│                           │     (SASB/GRI analysis)         │  │
│  Runs inside Docker       │     ↓                           │  │
│  container               │  2. Web Scraper Agent           │  │
│                           │     (News & controversies)      │  │
│                           │     ↓                           │  │
│                           │  3. Scientific Verifier         │  │
│                           │     (NASA/NOAA satellite data)  │  │
│                           │     ↓                           │  │
│                           │  4. Synthesizer                 │  │
│                           │     (Compute scores)            │  │
│                           │     ↓                           │  │
│                           │  5. PDF Generator               │  │
│                           │     (Create report)             │  │
│                           └──────────┬───────────────────────┘  │
│                                      │                         │
│  ┌──────────────┐                   │                         │
│  │  Streamlit   │                   │                         │
│  │  UI          │◄──────────────────┘                         │
│  │  Port 8501   │                                             │
│  │              │                                             │
│  │  Dashboard:  │                                             │
│  │  • Input ESG │                                             │
│  │  • View      │                                             │
│  │    results   │                                             │
│  │  • Download  │                                             │
│  │    PDF       │                                             │
│  └──────────────┘                                             │
└────────────────────────────────────────────────────────────────┘
```

### What Each Agent Does

#### 1️⃣ Materiality Agent
- **Input:** Full ESG report text
- **Process:** 
  - Extracts claims about SASB topics (GHG, Energy, Water, Waste, etc.)
  - Scores against GRI standards
  - Identifies missing disclosures
- **Output:** Materiality scores per topic + gap analysis
- **Weight in final score:** 40%

#### 2️⃣ Web Scraper Agent
- **Input:** Company name + report year
- **Process:**
  - Searches for ESG controversies and news
  - Uses DuckDuckGo (free) or SerpAPI (optional, richer results)
  - Classifies by severity: LOW → MEDIUM → HIGH → **CRITICAL**
- **Output:** List of controversies with sources and severity ratings
- **Weight in final score:** 35%

#### 3️⃣ Scientific Verifier Agent
- **Input:** Claims from ESG report (emissions, renewable %,deforestation reduction)
- **Process:**
  - Fetches real satellite data (NASA FIRMS + NOAA)
  - Compares reported claims vs. satellite observations
  - Flags discrepancies as greenwashing indicators
- **Output:** Scientific verification results + confidence scores
- **Weight in final score:** 25%

#### 4️⃣ Synthesizer Agent
- **Input:** Results from agents 1-3
- **Process:**
  - Computes weighted overall ESG Integrity Score
  - Generates letter grade (A-F)
  - Lists greenwashing red flags
  - Creates executive summary
- **Output:** Scorecard with overall score, grade, and recommendations

#### 5️⃣ PDF Generator
- **Input:** Scorecard from synthesizer
- **Process:**
  - Creates professional PDF report
  - Includes charts, evidence trail, recommendations
- **Output:** PDF file saved to `/reports/`

---

## API Reference

### Base URL
```
http://localhost:8000
```

### 1. Health Check
**Endpoint:**
```http
GET /health
```

**Purpose:** Verify backend is running

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-04-26T14:30:45.123Z"
}
```

---

### 2. Start Audit
**Endpoint:**
```http
POST /audit/start
Content-Type: application/json
```

**Request Body:**
```json
{
  "company_name": "Acme Corporation",
  "report_text": "Full ESG report text here... [must be at least 1000 characters]",
  "report_year": "2024",
  "industry_sector": "Energy"
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

**Save the `job_id`** — you'll use it to poll for results!

---

### 3. Get Audit Status & Results
**Endpoint:**
```http
GET /audit/{job_id}
```

**Response (while running):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "company_name": "Acme Corporation",
  "created_at": "2024-04-26T14:30:45.123Z",
  "scorecard": null,
  "pdf_path": null,
  "errors": []
}
```

**Response (when complete):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "company_name": "Acme Corporation",
  "created_at": "2024-04-26T14:30:45.123Z",
  "completed_at": "2024-04-26T14:45:30.456Z",
  "scorecard": {
    "overall_score": 68,
    "grade": "C",
    "summary": "Company shows moderate ESG commitment but has material inconsistencies...",
    "materiality": {
      "average_score": 72,
      "topics": [
        { "topic": "GHG Emissions", "score": 85 },
        { "topic": "Water Management", "score": 62 }
      ]
    },
    "controversies": [
      {
        "headline": "Company fined for environmental violation",
        "severity": "HIGH",
        "source": "Reuters",
        "date": "2024-03-15"
      }
    ],
    "scientific_analysis": {
      "findings": [
        { "metric": "Emissions", "verdict": "ACCURATE" },
        { "metric": "Deforestation", "verdict": "DISAGREEMENT" }
      ]
    },
    "greenwashing_flags": 3,
    "recommendations": [
      "Provide Scope 3 emissions breakdown",
      "Address deforestation allegations in supply chain",
      "Increase renewable energy percentage transparency"
    ]
  },
  "pdf_path": "/app/reports/scorecard_2024_acme_corp_550e8400.pdf",
  "errors": []
}
```

---

### 4. Download PDF Report
**Endpoint:**
```http
GET /report/{job_id}
```

**Response:** Binary PDF file (browser downloads automatically)

**PowerShell Example:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/report/$jobId" `
    -OutFile "report.pdf" `
    -Method GET
```

---

### Scoring System

**Overall Score = 40% Materiality + 35% Controversy + 25% Scientific**

| Score | Grade | Meaning |
|-------|-------|---------|
| 90-100 | **A** | Strong ESG integrity, low greenwashing risk |
| 75-89 | **B** | Good practices, minor gaps |
| 60-74 | **C** | Fair progress, material weaknesses |
| 45-59 | **D** | Poor ESG integrity, significant flags |
| 0-44 | **F** | Critical concerns, likely greenwashing |

---

## Troubleshooting

### ❌ Problem: "Connection refused on port 11434"

**Cause:** Ollama container isn't running

**Solution:**
```powershell
# Check if container exists:
docker ps -a | findstr esg_ollama

# Start it:
docker compose restart ollama

# Wait 30 seconds, then check:
docker ps | findstr esg_ollama

# View logs:
docker logs -f esg_ollama
```

---

### ❌ Problem: Backend returns "502 Bad Gateway"

**Cause:** FastAPI crashed or not started yet

**Solution:**
```powershell
# Check backend status:
docker ps | findstr esg_backend

# View logs:
docker logs esg_backend

# Restart:
docker compose restart esg-backend

# Wait 30 seconds for it to connect to Ollama
```

---

### ❌ Problem: "TimeoutError: waiting for LLM response"

**Cause:** Model still loading or system is overloaded

**Solution:**
```powershell
# Check if model is loaded:
docker exec esg_ollama curl http://localhost:11434/api/tags

# Check Ollama logs:
docker logs esg_ollama | tail -50

# If first startup: Wait 3-5 minutes for model download
# If already running: Increase timeout or use smaller model

# Change LLM in .env to smaller/faster model:
# OLLAMA_MODEL=phi3:medium
docker compose restart esg-backend
```

---

### ❌ Problem: "ModuleNotFoundError" in backend

**Cause:** Python dependencies missing or installed incorrectly

**Solution:**
```powershell
# Rebuild backend container:
docker compose down esg-backend
docker compose up --build esg-backend

# If still fails, rebuild everything:
docker compose down
docker compose up --build
```

---

### ❌ Problem: Streamlit UI shows "connection error"

**Cause:** UI can't reach backend

**Solution:**
```powershell
# Test if backend is accessible:
curl http://localhost:8000/health

# Check UI logs:
docker logs esg_ui

# Restart UI:
docker compose restart esg_ui

# Wait 15 seconds for it to connect
```

---

### ❌ Problem: "Docker volume not found"

**Cause:** Ollama volume doesn't exist

**Solution:**
```powershell
# Create the volume:
docker volume create ollama

# Verify:
docker volume ls | findstr ollama

# Restart Ollama:
docker compose down
docker compose up -d ollama
```

---

### ✅ Nuclear Option: Reset Everything

```powershell
# Stop all containers:
docker compose down

# Remove volumes (deletes cached LLM models!):
docker volume rm ollama

# Clean up stale containers:
docker container prune -f

# Rebuild from scratch:
docker volume create ollama
docker compose up --build

# This will take 5-10 minutes on first run
```

---

## Advanced Configuration

### Use a Different LLM Model

Edit `.env` and change:
```env
OLLAMA_MODEL=mistral:7b          # Balanced reasoning + speed
OLLAMA_MODEL=llama2:13b          # Better reasoning (slower)
OLLAMA_MODEL=phi3:medium         # Very fast (less accurate)
OLLAMA_MODEL=gemma2:9b           # Google's model
```

Restart backend:
```powershell
docker compose restart esg-backend
# Ollama will auto-download the new model
```

---

### Enable SerpAPI for Richer Search

1. Sign up at https://serpapi.com (free 100 searches/month)
2. Copy your API key
3. Add to `.env`:
   ```env
   SERPAPI_KEY=abc123def456...
   ```
4. Restart:
   ```powershell
   docker compose restart esg-backend
   ```

---

### Enable NASA Satellite Data

1. Get free API key at https://api.nasa.gov
2. Add to `.env`:
   ```env
   NASA_API_KEY=your_key_here
   ```
3. Restart:
   ```powershell
   docker compose restart esg-backend
   ```

---

### Use GPU for Faster Inference

If you have an NVIDIA GPU:

```powershell
# Check if GPU is detected:
docker exec esg_ollama nvidia-smi

# If GPU found, Ollama uses it automatically!
# You should see GPU memory usage

# If no GPU, Ollama falls back to CPU (slower)
```

---

### Monitor Real-Time Logs

```powershell
# Watch all services:
docker compose logs -f

# Watch specific service:
docker logs -f esg_backend
docker logs -f esg_ollama
docker logs -f esg_ui

# Last 50 lines only:
docker logs --tail 50 esg_backend

# Follow with timestamps:
docker logs -f --timestamps esg_backend
```

---

### Run Multiple Audits Concurrently

```powershell
# Start 3 audits at once (requires sufficient RAM):

$companies = @("Acme", "GlobalCorp", "EcoEnergy")

foreach ($company in $companies) {
    $body = @{
        company_name = $company
        report_text = "Sample report text..."
        report_year = "2024"
        industry_sector = "General"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest `
        -Uri http://localhost:8000/audit/start `
        -Method POST -ContentType "application/json" -Body $body
    
    $jobId = ($response.Content | ConvertFrom-Json).job_id
    Write-Host "Started $company : $jobId"
}

# Now poll all three to completion
```

---

## File Structure Reference

```
ESG_REPORTING/
│
├── 📄 Files (Configuration & Entry Points)
│   ├── main.py                    # FastAPI application
│   ├── docker-compose.yml         # Service orchestration
│   ├── Dockerfile.backend         # Backend container definition
│   ├── Dockerfile.ui              # Streamlit container definition
│   ├── env.example                # Environment template
│   ├── requirements.backend.txt   # Backend Python packages
│   ├── requirements.ui.txt        # Frontend Python packages
│   ├── requirements.txt           # All packages
│   └── readme.md                  # Original README
│
├── 📁 agents/                     # AI agents (LangGraph nodes)
│   ├── __init__.py
│   ├── state.py                   # Shared state definitions
│   ├── materiality_agent.py       # ← SASB/GRI analysis
│   ├── scraper_agent.py           # ← Web search & controversies
│   ├── scientific_verifier.py     # ← NASA/NOAA satellite data
│   ├── synthesizer.py             # ← Score computation
│   └── sytnthesizer.py            # (Note: typo in original)
│
├── 📁 frameworks/
│   ├── __init__.py
│   └── pipeline.py                # ← LangGraph pipeline orchestration
│
├── 📁 tools/
│   ├── __init__.py
│   └── pdf_generator.py           # ← PDF report generation
│
├── 📁 config/
│   ├── __init__py
│   └── esg_frameworks.py          # ← SASB topics & GRI standards data
│
├── 📁 ui/
│   ├── __init__.py
│   └── app.py                     # ← Streamlit dashboard
│
├── 📁 data/
│   └── acme_esg_2024/             # Sample ESG report for testing
│
└── 📁 reports/                    # Generated PDF reports (auto-created)
    └── (PDFs appear here after each audit)
```

---

## Common Workflow Examples

### Example: Batch Audit Multiple Companies

```powershell
# Script to audit companies in a CSV file

$companies = @(
    @{ Name="TechCorp"; Sector="IT" },
    @{ Name="OilGiant"; Sector="Energy" },
    @{ Name="RetailChain"; Sector="Retail" }
)

$results = @()

foreach ($company in $companies) {
    Write-Host "Auditing $($company.Name)..."
    
    $report = Get-Content "data/$($company.Name)_esg.txt" -Raw
    
    $body = @{
        company_name    = $company.Name
        report_text     = $report
        report_year     = "2024"
        industry_sector = $company.Sector
    } | ConvertTo-Json
    
    # Start audit
    $response = Invoke-WebRequest `
        -Uri http://localhost:8000/audit/start `
        -Method POST -ContentType "application/json" -Body $body
    
    $jobId = ($response.Content | ConvertFrom-Json).job_id
    
    # Poll until complete
    do {
        Start-Sleep -Seconds 10
        $status = Invoke-WebRequest -Uri "http://localhost:8000/audit/$jobId" `
            -Method GET | ConvertFrom-Json
    } while ($status.status -eq "running")
    
    # Save result
    $results += [PSCustomObject]@{
        Company  = $company.Name
        Score    = $status.scorecard.overall_score
        Grade    = $status.scorecard.grade
        Flags    = $status.scorecard.greenwashing_flags
        JobId    = $jobId
    }
    
    Write-Host "✓ Completed: $($company.Name) - Score $($status.scorecard.overall_score)"
}

# Export results
$results | Export-Csv "audit_results_$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation
Write-Host "✓ Results exported!"
```

---

## Quick Reference Commands

```powershell
# Start system
docker compose up -d

# Stop system
docker compose down

# View all logs
docker compose logs -f

# Check running containers
docker ps

# Restart specific service
docker compose restart esg-backend

# Rebuild from scratch
docker compose down && docker volume rm ollama && docker volume create ollama && docker compose up --build

# Test API health
curl http://localhost:8000/health

# Open UI
Start-Process "http://localhost:8501"

# Open API docs
Start-Process "http://localhost:8000/docs"
```

---

## Getting Help

**Issue Not Listed?** Try these:

1. **Check logs:**
   ```powershell
   docker compose logs -f
   ```

2. **Restart everything:**
   ```powershell
   docker compose restart
   ```

3. **Check Docker isn't out of disk:**
   ```powershell
   docker system df
   ```

4. **Verify each service individually:**
   ```powershell
   curl http://localhost:11434/api/tags    # Ollama
   curl http://localhost:8000/health       # Backend
   # Browser to http://localhost:8501      # UI
   ```

---

**Last Updated:** April 2026  
**License:** MIT — use freely, attribution appreciated
