"""
database.py
-----------
Persistence layer using Python's built-in sqlite3 module.

No pandas/numpy here on purpose — plain SQL + Python dicts, since this
project intentionally stops at the "AI concepts" stage before the ML
stage of the course (where pandas/numpy become the standard tools).
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = Path(__file__).parent.parent / "tassie.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            risk_score REAL NOT NULL,
            findings_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_scan(filename: str, risk_score: float, findings: List[Dict]) -> int:
    # Every finding starts life open (unresolved) so the Reports/History
    # "mark resolved" workflow has something real to toggle.
    for f in findings:
        f.setdefault("resolved", False)
        f.setdefault("resolved_at", None)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO scans (filename, risk_score, findings_json, created_at) VALUES (?, ?, ?, ?)",
        (filename, risk_score, json.dumps(findings), datetime.utcnow().isoformat()),
    )
    conn.commit()
    scan_id = cur.lastrowid
    conn.close()
    return scan_id


def get_scan(scan_id: int) -> Dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "id": row["id"],
        "filename": row["filename"],
        "risk_score": row["risk_score"],
        "findings": json.loads(row["findings_json"]),
        "created_at": row["created_at"],
    }


def list_scans(limit: int = 50) -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "filename": r["filename"],
            "risk_score": r["risk_score"],
            "findings_count": len(json.loads(r["findings_json"])),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def update_finding_resolution(scan_id: int, finding_index: int, resolved: bool) -> Optional[Dict]:
    """Toggle a single finding's resolved status in place inside findings_json.
    Powers the "Mark resolved" button in the scan detail modal."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT findings_json FROM scans WHERE id = ?", (scan_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        return None

    findings = json.loads(row["findings_json"])
    if finding_index < 0 or finding_index >= len(findings):
        conn.close()
        return None

    findings[finding_index]["resolved"] = resolved
    findings[finding_index]["resolved_at"] = datetime.utcnow().isoformat() if resolved else None

    cur.execute("UPDATE scans SET findings_json = ? WHERE id = ?", (json.dumps(findings), scan_id))
    conn.commit()
    conn.close()
    return findings[finding_index]


def get_severity_breakdown() -> Dict[str, int]:
    """Counts every OPEN (unresolved) finding by severity, across all scans.
    Powers the Overview donut chart + severity bars."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT findings_json FROM scans")
    rows = cur.fetchall()
    conn.close()

    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for r in rows:
        for f in json.loads(r["findings_json"]):
            if f.get("resolved"):
                continue
            sev = (f.get("severity") or "").lower()
            if sev in counts:
                counts[sev] += 1
    return counts


def get_open_resolved_counts():
    """Returns (open_issues, resolved_in_last_30_days) across every scan.
    Powers the OPEN ISSUES / RESOLVED (30d) stat cards."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT findings_json FROM scans")
    rows = cur.fetchall()
    conn.close()

    open_count = 0
    resolved_30d = 0
    cutoff = datetime.utcnow() - timedelta(days=30)
    for r in rows:
        for f in json.loads(r["findings_json"]):
            if f.get("resolved"):
                resolved_at = f.get("resolved_at")
                if resolved_at:
                    try:
                        if datetime.fromisoformat(resolved_at) >= cutoff:
                            resolved_30d += 1
                    except ValueError:
                        pass
            else:
                open_count += 1
    return open_count, resolved_30d


def get_daily_trend(days: int = 14) -> List[Dict]:
    """Buckets every finding by the calendar day its scan ran, for the last
    `days` days (including days with zero scans). Powers the vulnerability
    trend line chart on Overview."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT created_at, findings_json FROM scans")
    rows = cur.fetchall()
    conn.close()

    today = datetime.utcnow().date()
    buckets = {(today - timedelta(days=i)): 0 for i in range(days - 1, -1, -1)}
    for r in rows:
        try:
            d = datetime.fromisoformat(r["created_at"]).date()
        except ValueError:
            continue
        if d in buckets:
            buckets[d] += len(json.loads(r["findings_json"]))

    return [{"date": d.strftime("%m/%d"), "count": c} for d, c in buckets.items()]


def get_open_findings(limit: int = 5) -> List[Dict]:
    """Returns the most urgent open (unresolved) critical/high findings
    across all scans, most recent first. Powers the notifications dropdown."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, filename, findings_json FROM scans ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    results = []
    for r in rows:
        for idx, f in enumerate(json.loads(r["findings_json"])):
            if f.get("resolved"):
                continue
            sev = (f.get("severity") or "").lower()
            if sev in ("critical", "high"):
                results.append({
                    "scan_id": r["id"],
                    "finding_index": idx,
                    "filename": r["filename"],
                    "category": f.get("category"),
                    "severity": sev,
                    "line_number": f.get("line_number"),
                })

    severity_order = {"critical": 0, "high": 1}
    results.sort(key=lambda x: severity_order.get(x["severity"], 2))
    return results[:limit]
