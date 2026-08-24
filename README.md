# AMRRA

**Automated Machine Learning Research Reproducibility Assistant**

AMRRA is an agentic research system that turns a research question and source evidence into a traceable reproducibility assessment. The production workflow deliberately separates probabilistic model reasoning from deterministic statistical computation.

## Agent workflow

```text
Source ingestion
    ↓
Retriever (lexical + optional Cohere semantic ranking)
    ↓
Extractor Agent (schema-constrained evidence + hypotheses)
    ↓
Experiment Planner (tool precondition checks)
    ↓
Deterministic Statistical Toolbox
    ↓
Judge Agent (evidence-cited synthesis)
```

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
- **Cohere Chat API v2**: structured Extractor and Judge agents
- **Cohere Embed API v2**: optional semantic retrieval score
- **Next.js**: real workbench wired to the run API
- **Alembic**: database migrations
- **Docker Compose**: reproducible local production topology
- **GitHub Actions**: backend coverage and frontend build/test gates

## Quick start

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Set `COHERE_API_KEY`.

3. Start the production-shaped stack:

```bash
docker compose up --build
```

4. Open:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

## Local backend development

```bash
cd back_end
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export COHERE_API_KEY=...
uvicorn main:app --reload
```

The default local database is SQLite. PostgreSQL deployments use Alembic migrations and do not auto-create tables.

Run tests:

```bash
PYTHONPATH=. pytest --cov=app --cov-report=term-missing --cov-fail-under=85 -q
```

## API

### Create a run

`POST /api/v1/runs` uses multipart form data:

- `query` — research question
- `file` — optional PDF, maximum 10 MB
- `url` — optional public HTTP(S) source URL
- `text` — optional pasted source text
- `top_k` — number of evidence chunks to send to the extractor

At least one source is required. Production returns `202 Accepted`; the client polls the durable run resource.

### Read a run

`GET /api/v1/runs/{run_id}` returns evidence, hypotheses, plans, deterministic experiments, judge report and stage traces.

## Security controls

- URL ingestion rejects non-HTTP schemes, localhost, private, loopback, link-local and reserved IP addresses, including redirects.
- Remote source size and redirect depth are bounded.
- PDF MIME/type, byte size and page count are bounded.
- CORS is explicit and environment-controlled.
- Agent provider errors are typed run failures; the system never inserts fake hypotheses to keep the pipeline alive.

## Test strategy

Tests cover schema invariants, planner tool-selection rules, statistical branches, hallucinated citation filtering, provider schema validation, SSRF controls, persistence, failed traces, API validation and a full end-to-end agent run using a deterministic fake provider. The fake provider exists only for tests; production configuration accepts the Cohere provider.
