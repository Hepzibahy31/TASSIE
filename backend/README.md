# Tassie — AI-Powered Secure Software Engineering Platform (Backend)

Tassie analyzes source code and flags security vulnerabilities as they're
written, then uses AI to explain each issue in plain English and suggest
a fix — instead of catching problems only after testing or release.

## How the pipeline works

```
Code submitted
      |
      v
security_scanner.py   ->  rule-based pattern matching (regex) finds vulnerabilities
      |
      v
rag_engine.py          ->  retrieves the relevant secure-coding guideline
                            (bag-of-words embeddings + cosine similarity, pure Python)
      |
      v
ai_explainer.py         ->  builds a prompt (system + few-shot + retrieved context)
                            and calls an LLM to explain the issue in plain English
      |
      v
database.py            ->  saves the scan to SQLite
      |
      v
report_generator.py     ->  exports the scan as a PDF or Excel report on demand
```

## Gen AI concepts this project demonstrates

This backend is intentionally built with **plain Python only** — no
pandas/numpy — to match a Gen AI course that hasn't reached the Machine
Learning stage yet. Every "AI" concept here is visible and hand-implemented
instead of hidden inside a library:

| Concept | Where it's used |
|---|---|
| Rule-based / expert systems | `security_scanner.py` — regex pattern matching |
| Tokenization | `rag_engine.py` — splitting text into words |
| Embeddings | `rag_engine.py` — bag-of-words vectors (`to_vector`) |
| Vector similarity | `rag_engine.py` — cosine similarity, computed by hand |
| Retrieval-Augmented Generation (RAG) | `rag_engine.py` + `ai_explainer.py` together |
| Prompt engineering | `ai_explainer.py` — `SYSTEM_PROMPT`, `build_prompt()` |
| Few-shot prompting | `ai_explainer.py` — `FEW_SHOT_EXAMPLE` |
| LLM API usage | `ai_explainer.py` — `_client.chat.completions.create()` |
| Temperature | `ai_explainer.py` — controls output randomness |

When you reach the Machine Learning part of your course, the natural next
upgrade is to replace the bag-of-words vectors in `rag_engine.py` with real
embeddings (e.g. `text-embedding-3-small`) stored in a vector database like
Pinecone or pgvector — the retrieval logic stays conceptually identical.

## Running it

```bash
cd tassie-backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# optional — enables real LLM explanations instead of the template fallback
cp .env.example .env
# edit .env and add your OPENAI_API_KEY

uvicorn app.main:app --reload --port 8000
```

Then open **http://localhost:8000/docs** for the interactive API docs
(FastAPI generates this automatically).

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` | Demo login |
| POST | `/api/scan` | Scan code (JSON body: filename, code) |
| POST | `/api/scan/upload` | Scan an uploaded file (for drag-and-drop) |
| GET | `/api/history` | List past scans |
| GET | `/api/scan/{id}` | Get one scan's full detail |
| GET | `/api/stats` | Dashboard summary stats |
| GET | `/api/scan/{id}/report/pdf` | Download PDF report |
| GET | `/api/scan/{id}/report/excel` | Download Excel report |

## Connecting to the frontend

In your dashboard's JavaScript, replace the simulated scan with a real call:

```js
const res = await fetch("http://localhost:8000/api/scan", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ filename: "auth_service.py", code: yourCodeString })
});
const result = await res.json();
```

## Try it without any frontend

```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.py", "code": "query = \"SELECT * FROM users WHERE id=\" + user_id\nAPI_KEY = \"sk_live_12345678\""}'
```
