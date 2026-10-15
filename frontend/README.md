# Tassie — Frontend (AI-Powered Secure Software Engineering Platform)

A single-file SaaS-style frontend: animated landing page, login, and a full
interactive dashboard.

## Run it

Just open `index.html` in a browser — no build step, no npm install.
Everything (Chart.js, fonts) loads from a CDN.

## What's included

- **Cinematic page load**: a brief branded loader, then the hero content
  fades/slides in with staggered timing instead of appearing all at once.
- **Scroll-reveal animations**: feature cards, the "how it works" steps, and
  the CTA band animate in as you scroll past them (`IntersectionObserver`).
- **Landing page**: animated scanning-beam visual over a live code sample,
  showing a SQL injection and hardcoded secret being flagged in real time.
- **Login page** with role selection (Developer / Security Lead / Admin).
- **Dashboard**: stat cards, a vulnerability trend line chart, a severity
  donut chart, animated severity bars, drag-and-drop file upload, a progress
  bar, an AI explanation with a typewriter effect, toast notifications, and
  a scan history table.
- **Dark/light theme toggle**, fully responsive down to mobile.
- **Export buttons** (PDF/Excel) — currently trigger a toast; wire these to
  `/api/scan/{id}/report/pdf` and `/api/scan/{id}/report/excel` from the
  backend to make them real downloads.

## Connecting to the real backend

This frontend already **tries the real Tassie backend first**, and only
falls back to the built-in simulated demo if the backend isn't running.

1. Start the backend (see the `tassie-backend` project):
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
2. Open `index.html`. Near the top of the `<script>` block you'll find:
   ```js
   const TASSIE_API_BASE = "http://localhost:8000";
   ```
   Change this if your backend runs on a different host/port.
3. Drop a file into the dashboard's upload zone — it will call
   `POST /api/scan` on the real backend and show the real AI explanation
   if the backend responds, or the demo explanation if it doesn't.

## Making it fully real (next steps)

- Replace the hardcoded scan-history table rows with a `fetch('/api/history')`
  call on dashboard load.
- Replace the hardcoded stat cards with a `fetch('/api/stats')` call.
- Wire the two export buttons to open the PDF/Excel report endpoints.
- Replace the demo login with a real call to `/api/auth/login`.

## File structure

```
tassie-frontend/
  index.html    <- everything: landing page, login, dashboard, all JS/CSS
```

Kept as a single file on purpose so it's easy to open, read top-to-bottom,
and paste into any hosting service (or the `static/` folder of the FastAPI
backend) with zero configuration.
