"""
ESG Auditor FastAPI Backend
────────────────────────────
Endpoints:
  POST /audit/start     — kick off async audit job
  GET  /audit/{job_id}  — poll job status & get results
  GET  /report/{job_id} — download PDF
  GET  /health          — liveness probe
"""

import asyncio
import io
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import sys
sys.path.append("/app")
from frameworks.pipeline import run_audit

app = FastAPI(
    title="ESG Integrity Auditor API",
    description="Multi-agent ESG greenwashing detection powered by local LLMs",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-memory job store (use Redis for production) ──────────────────────────
_jobs: dict[str, dict] = {}
_executor = ThreadPoolExecutor(max_workers=2)


def _record_job_log(job_id: str, message: str, level: str = "info") -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
    }
    job = _jobs.get(job_id)
    if job is not None:
        job.setdefault("pipeline_logs", []).append(entry)


class AuditRequest(BaseModel):
    company_name: str
    report_text: str
    report_year: str = "5"
    industry_sector: str = "General"


def _run_in_thread(
    job_id: str,
    company_name: str,
    raw_content: bytes,
    filename: str,
    report_year: str,
    industry_sector: str,
):
    """Execute the LangGraph pipeline in a background thread."""
    try:
        _jobs[job_id]["status"] = "running"
        _record_job_log(job_id, "Audit started: preparing report text and AI agents.")
        
        # 1. Parse the PDF in the background thread
        text = ""
        if filename.endswith(".pdf"):
            import pdfplumber
            with pdfplumber.open(io.BytesIO(raw_content)) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
        else:
            text = raw_content.decode("utf-8", errors="ignore")

        if len(text.strip()) < 100:
            raise ValueError("Report text too short or empty")

        _record_job_log(job_id, f"Loaded report text ({len(text.splitlines())} lines).")

        report_lower = text.lower()
        if any(kw in report_lower for kw in ["emissions", "co2", "carbon", "methane"]):
            pass  # Will be logged by pipeline
        else:
            pass  # Will be logged by pipeline

        _record_job_log(job_id, "Running the full multi-agent ESG audit pipeline.")

        # 2. Run the audit pipeline
        def logger_func(message: str):
            _record_job_log(job_id, message)
        
        result = run_audit(
            company_name=company_name,
            report_text=text,
            report_year=report_year,
            industry_sector=industry_sector,
            logger=logger_func,
            job_id=job_id,
        )
        _record_job_log(job_id, "AI agents completed analysis and generated results.")
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["scorecard"] = result.get("scorecard")
        _jobs[job_id]["pdf_path"] = result.get("pdf_path")
        _jobs[job_id]["errors"] = result.get("errors", [])
        _jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
        _record_job_log(job_id, f"Audit failed: {e}", level="error")


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/audit/start")
async def start_audit(request: AuditRequest):
    """Start an audit job and return a job_id to poll."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "company_name": request.company_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scorecard": None,
        "pdf_path": None,
        "errors": [],
        "pipeline_logs": [],
    }
    _record_job_log(job_id, "Audit queued and awaiting execution.")

    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        _executor,
        _run_in_thread,
        job_id,
        request.company_name,
        request.report_text.encode("utf-8"),
        "text.txt",
        request.report_year,
        request.industry_sector,
    )

    return {"job_id": job_id, "status": "queued"}


@app.post("/audit/upload")
async def start_audit_with_file(
    company_name: str = Form(...),
    report_year: str = Form("2025"),
    industry_sector: str = Form("General"),
    file: UploadFile = File(...),
):
    """Start an audit by uploading a PDF or TXT sustainability report."""
    content = await file.read()  # Just read the bytes, don't parse yet
    filename = str(file.filename or "uploaded_report")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "company_name": company_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scorecard": None,
        "pdf_path": None,
        "errors": [],
        "pipeline_logs": [],
    }
    _record_job_log(job_id, "Audit queued and awaiting execution.")

    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        _executor,
        _run_in_thread,
        job_id,
        company_name,
        content,
        filename,
        report_year,
        industry_sector,
    )

    return {"job_id": job_id, "status": "queued"}


@app.get("/audit/{job_id}")
def get_audit_status(job_id: str):
    """Poll audit job status and retrieve results when done."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    response = {
        "job_id": job_id,
        "status": job["status"],
        "company_name": job["company_name"],
        "created_at": job["created_at"],
        "completed_at": job.get("completed_at"),
        "errors": job.get("errors", []),
        "pdf_path": job.get("pdf_path"),
        "has_pdf": bool(job.get("pdf_path")),
        "pipeline_logs": job.get("pipeline_logs", []),
    }

    if job["status"] == "completed" and job.get("scorecard"):
        response["scorecard"] = job["scorecard"]

    if job["status"] == "failed":
        response["error"] = job.get("error", "Unknown error")

    if job.get("errors"):
        response["pdf_error"] = next(
            (err for err in job["errors"] if "PDF generation failed" in err), None
        )

    return response


@app.get("/report/{job_id}")
def download_report(job_id: str):
    """Download the generated PDF report."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] != "completed":
        raise HTTPException(400, f"Audit not complete (status: {job['status']})")
    if not job.get("pdf_path"):
        raise HTTPException(404, "PDF not generated")

    pdf_path = Path(job["pdf_path"])
    if not pdf_path.exists():
        raise HTTPException(404, "PDF file not found on disk")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
    )


@app.get("/jobs")
def list_jobs():
    """List all recent audit jobs (last 20)."""
    recent = sorted(_jobs.values(), key=lambda j: j["created_at"], reverse=True)[:20]
    return [
        {
            "job_id": j["job_id"],
            "company_name": j["company_name"],
            "status": j["status"],
            "created_at": j["created_at"],
        }
        for j in recent
    ]