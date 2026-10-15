"""
main.py
-------
Tassie — AI-Powered Secure Software Engineering Platform
FastAPI backend entry point.

Pipeline for a scan request:
  1. security_scanner.py  -> rule-based pattern matching finds vulnerabilities
  2. rag_engine.py         -> retrieves the relevant secure-coding guideline
                              for each finding (Retrieval)
  3. ai_explainer.py        -> generates a plain-English explanation using an
                              LLM prompt that includes the retrieved guideline
                              (Augmented Generation)
  4. database.py           -> persists the scan so it shows up in history
  5. report_generator.py    -> exports the scan as PDF / Excel on demand
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dataclasses import asdict

from app import database
from app.security_scanner import scan_code, risk_score
from app.rag_engine import RAGEngine, retrieve_guideline_for_category
from app.ai_explainer import explain_finding
from app.report_generator import generate_pdf_report, generate_excel_report

app = FastAPI(title="Tassie API", description="AI-Powered Secure Software Engineering Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this to your frontend's real origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()
rag_engine = RAGEngine()   # index built once at startup


# ---------- request/response models ----------

class ScanRequest(BaseModel):
    filename: str
    code: str


class LoginRequest(BaseModel):
    email: str
    password: str
    role: str = "Developer"


class ResolveRequest(BaseModel):
    resolved: bool = True


# ---------- auth (simple demo auth, no real user DB yet) ----------

@app.post("/api/auth/login")
def login(req: LoginRequest):
    """Demo authentication. In production, replace with hashed-password
    verification against a users table, and issue a real JWT."""
    if not req.email or not req.password:
        raise HTTPException(status_code=400, detail="Email and password required")
    fake_token = f"tassie-demo-token-for-{req.email}"
    return {"token": fake_token, "role": req.role, "email": req.email}


# ---------- core scanning pipeline ----------

@app.post("/api/scan")
def scan(req: ScanRequest):
    findings = scan_code(req.code)
    findings_dicts = []

    for f in findings:
        guideline = retrieve_guideline_for_category(rag_engine, f.category)
        ai_result = explain_finding(f.category, f.line_text, guideline["text"])

        finding_dict = asdict(f)
        finding_dict["guideline"] = guideline["text"]
        finding_dict["ai_explanation"] = ai_result["explanation"]
        finding_dict["explanation_source"] = ai_result["source"]
        findings_dicts.append(finding_dict)

    score = risk_score(findings)
    scan_id = database.save_scan(req.filename, score, findings_dicts)

    return {
        "scan_id": scan_id,
        "filename": req.filename,
        "risk_score": score,
        "findings_count": len(findings_dicts),
        "findings": findings_dicts,
    }


@app.post("/api/scan/upload")
async def scan_upload(file: UploadFile = File(...)):
    """Same pipeline, but accepts a real uploaded file (for the drag-and-drop UI)."""
    contents = await file.read()
    code = contents.decode("utf-8", errors="ignore")
    return scan(ScanRequest(filename=file.filename, code=code))


# ---------- history & stats ----------

@app.get("/api/history")
def history(limit: int = 50):
    return database.list_scans(limit=limit)


@app.get("/api/scan/{scan_id}")
def get_scan(scan_id: int):
    result = database.get_scan(scan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return result


@app.get("/api/stats")
def stats():
    scans = database.list_scans(limit=1000)
    open_issues, resolved_30d = database.get_open_resolved_counts()
    if not scans:
        return {
            "total_scans": 0, "avg_risk": 0, "total_findings": 0,
            "open_issues": open_issues, "resolved_30d": resolved_30d,
        }
    total_findings = sum(s["findings_count"] for s in scans)
    avg_risk = round(sum(s["risk_score"] for s in scans) / len(scans), 2)
    return {
        "total_scans": len(scans),
        "avg_risk": avg_risk,
        "total_findings": total_findings,
        "open_issues": open_issues,
        "resolved_30d": resolved_30d,
    }


@app.get("/api/stats/severity")
def stats_severity():
    """Open findings broken down by severity — powers the Overview donut/bars."""
    return database.get_severity_breakdown()


@app.get("/api/stats/trend")
def stats_trend(days: int = 14):
    """Findings-per-day for the last N days — powers the vulnerability trend chart."""
    return database.get_daily_trend(days)


@app.get("/api/findings/open")
def findings_open(limit: int = 5):
    """The most urgent open critical/high findings across every scan — powers
    the notifications dropdown in the topbar."""
    return database.get_open_findings(limit)


@app.patch("/api/scan/{scan_id}/finding/{finding_index}/resolve")
def resolve_finding(scan_id: int, finding_index: int, req: ResolveRequest):
    """Marks (or unmarks) a single finding as resolved. Called from the
    scan detail modal's "Mark resolved" button."""
    updated = database.update_finding_resolution(scan_id, finding_index, req.resolved)
    if updated is None:
        raise HTTPException(status_code=404, detail="Scan or finding not found")
    return updated


# ---------- report export ----------

@app.get("/api/scan/{scan_id}/report/pdf")
def report_pdf(scan_id: int):
    scan_data = database.get_scan(scan_id)
    if scan_data is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    path = generate_pdf_report(scan_data)
    return FileResponse(path, filename=path.name, media_type="application/pdf")


@app.get("/api/scan/{scan_id}/report/excel")
def report_excel(scan_id: int):
    scan_data = database.get_scan(scan_id)
    if scan_data is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    path = generate_excel_report(scan_data)
    return FileResponse(
        path, filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/")
def root():
    return {"status": "Tassie API is running", "docs": "/docs"}
