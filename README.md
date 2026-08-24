# AMRRA

**Automated Machine Learning Research Reproducibility Assistant**

AMRRA is an agentic research system that turns a research question and source evidence into a traceable reproducibility assessment. The production workflow deliberately separates probabilistic model reasoning from deterministic statistical computation.

## Agent workflow

```text
Source ingestion
    ↓
Retriever (lexical shortlist + Groq/Llama semantic reranking)
    ↓
Extractor Agent (Groq/Llama, schema-validated evidence + hypotheses)
    ↓
Experiment Planner (deterministic tool precondition checks)
    ↓
Deterministic Statistical Toolbox
    ↓
Judge Agent (Groq/Llama, evidence-cited synthesis)
```

Groq is the **only production LLM provider**, using `llama-3.1-8b-instant` by default through Groq's OpenAI-compatible Chat Completions API. AMRRA does not silently switch to another provider. If LLM reranking is temporarily unavailable, retrieval degrades to deterministic lexical ranking; extraction and judging fail explicitly rather than fabricating output.

Groq JSON Object Mode is used for model responses. The requested Pydantic schema is included in the system instruction, and every response is validated before entering trusted application state. JSON syntax alone is never treated as proof of schema or semantic correctness.

Every stage writes a durable trace containing status, latency, model/prompt version, input/output hashes, errors and tool metadata. Model outputs are treated as untrusted until Pydantic validates them.

### Scientific integrity rules

AMRRA never turns arbitrary numbers in prose into statistical samples. The Extractor must attach semantic type, role, group and evidence chunk IDs to observations. The Planner only invokes a statistical tool when its explicit preconditions are satisfied. Otherwise the run returns an `insufficient_data` result instead of fabricating an experiment.

Supported deterministic tools currently include:

- Welch two-sample t-test from explicit raw groups or mean/SD/n summaries
- one-way ANOVA
- Pearson chi-square test of independence with Cramér's V
- simple linear regression
- descriptive/insufficient-evidence fallback

## Production architecture

- **FastAPI**: run creation, PDF ingestion, status and health endpoints
- **PostgreSQL**: durable run state and stage traces
- **Redis + Celery**: production job dispatch and worker isolation
- **Groq OpenAI-compatible API**: Llama retrieval reranking, extraction and judging
- **Next.js 14**: real workbench wired to the run API
- **Alembic**: database migrations
- **Docker Compose**: reproducible local production topology
- **GitHub Actions**: backend coverage, agent evals and frontend build/test gates

## Quick start

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Configure Groq:

```bash
LLM_PROVIDER=groq
LLM_API_STYLE=openai_chat
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-8b-instant
LLM_API_KEY=your_groq_key
LLM_MAX_COMPLETION_TOKENS=4096
```

Never commit the real key. AMRRA reads it only from the runtime environment or local `.env` file.

3. Verify provider connectivity before starting workers:

```bash
cd back_end
PYTHONPATH=. python -m app.providers.diagnostics
```

The diagnostic checks authentication and confirms that the configured model is visible without printing the API key.

4. Start the production-shaped stack:

```bash
docker compose up --build
```

5. Open:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

## Local backend development

```bash
cd back_end
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

export LLM_PROVIDER=groq
export LLM_API_STYLE=openai_chat
export LLM_BASE_URL=https://api.groq.com/openai/v1
export LLM_MODEL=llama-3.1-8b-instant
export LLM_API_KEY=your_groq_key
export CELERY_BROKER_URL=redis://127.0.0.1:6379/0
```

Start FastAPI:

```bash
uvicorn main:app --reload
```

Start the Celery worker in another terminal:

```bash
celery -A worker.celery_app worker --loglevel=INFO --queues=amrra --concurrency=4
```

The default local database is SQLite. PostgreSQL deployments use Alembic migrations and do not auto-create tables.

Run tests:

```bash
PYTHONPATH=. pytest --cov=app --cov-report=term-missing --cov-fail-under=85 -q
```

Run the offline agent-quality suite:

```bash
PYTHONPATH=. python -m evals.runner
```

Run the same gold cases against the configured Groq model:

```bash
PYTHONPATH=. python -m evals.runner --live
```

## API

### Create a run

`POST /api/v1/runs` uses multipart form data:

- `query` — research question
- `file` — optional PDF, maximum 10 MB
- `url` — optional public HTTP(S) source URL
- `text` — optional pasted source text
- `top_k` — number of evidence chunks retained after retrieval/reranking

At least one source is required. Production returns `202 Accepted`; the client polls the durable run resource.

### Read a run

`GET /api/v1/runs/{run_id}` returns evidence, hypotheses, plans, deterministic experiments, judge report and stage traces.

## Security controls

- URL ingestion rejects non-HTTP schemes, localhost, private, loopback, link-local and reserved IP addresses, including redirects.
- Remote source size and redirect depth are bounded.
- PDF MIME/type, byte size and page count are bounded.
- CORS is explicit and environment-controlled.
- Groq credentials are environment-only and are never exposed to the frontend.
- Provider error messages redact the configured API key.
- 401/403 and other permanent 4xx failures fail fast instead of burning retry budget.
- Agent provider errors are typed run failures; the system never inserts fake hypotheses to keep the pipeline alive.

## Test strategy

Tests cover schema invariants, LLM reranking constraints/fallback, planner tool-selection rules, statistical branches, hallucinated citation filtering, Groq request/response validation, authentication failure semantics, model discovery, SSRF controls, persistence, failed traces, API validation and a full end-to-end agent run using a deterministic fake provider. The fake provider exists only for tests/offline evals; production has one provider: Groq.
