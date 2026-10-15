# TASSIE — AI-Powered Secure Software Engineering Platform

Catches vulnerabilities while code is being written, not after — continuous
analysis instead of catching issues only during testing or after release.

## Folder structure

```
tassie/
├── backend/          <- FastAPI + AI analysis engine
│   ├── app/
│   │   ├── main.py
│   │   ├── security_scanner.py
│   │   ├── rag_engine.py
│   │   ├── ai_explainer.py
│   │   ├── database.py
│   │   └── report_generator.py
│   ├── data/
│   │   └── guidelines.json
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md      <- full backend docs + concept explanations
│
└── frontend/          <- SaaS-style landing page + dashboard
    ├── index.html
    └── README.md       <- full frontend docs
```

## Quick start (VS Code / PowerShell)

**1. Unzip this file**, then open the resulting `tassie` folder in VS Code
(`File → Open Folder`).

**2. Start the backend** — open a terminal in VS Code:
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```
Leave this terminal running. Check it worked by opening
`http://localhost:8000/docs` in a browser.

**3. Open the frontend** — in File Explorer, go into `tassie/frontend` and
double-click `index.html`. It opens directly in your browser — no server
needed for the frontend itself.

**4. Try it** — click "Start free scan" → log in with any email/password →
in the dashboard, drag a file into the upload box. Since the backend is
running, you'll get a real AI-generated explanation back.

## If PowerShell blocks the venv activation

Run this once, then retry `venv\Scripts\activate`:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Type `Y` when prompted, and only `Y` — nothing else on that line.

## Getting full AI explanations (not just the short template)

By default, without an API key, explanations come from a short built-in
template (a few lines) — this is intentional so the project runs with zero
setup. To get real, detailed AI-generated explanations:

1. Get an API key from https://platform.openai.com/api-keys
2. In `backend/`, copy `.env.example` to a new file named `.env`
3. Open `.env` and set: `OPENAI_API_KEY=your-key-here`
4. Restart the backend (`Ctrl+C` in the terminal, then run `uvicorn` again)

Now every scan calls a real LLM and returns a full, detailed explanation
instead of the short fallback.

## What's live vs. what's fixed

- **Live (updates on every scan):** the AI explanation panel, the severity
  bars, the severity donut chart, the stat cards, and the recent-scans
  table — all pulled from your real backend after each scan.
- **Still fixed (demo data):** the 14-day vulnerability trend line chart,
  since that needs day-by-day historical data the current backend doesn't
  track yet. Everything else reflects your real scan results.

## Notes
- See `backend/README.md` for how each file maps to Gen AI concepts
  (prompt engineering, embeddings, RAG, LLM API calls).
- See `frontend/README.md` for what's animated/interactive and how to
  wire the remaining hardcoded dashboard sections to live API calls.
