# AMRRA

**Automated Machine Learning Research Reproducibility Assistant**

AMRRA is an agentic research system that turns a research question and source evidence into a traceable reproducibility assessment. The production workflow deliberately separates probabilistic model reasoning from deterministic statistical computation.

## Agent workflow

```text
Source ingestion
    ↓
Retriever (lexical shortlist + GPT-5.6 Sol semantic reranking)
    ↓
Extractor Agent (GPT-5.6 Sol, schema-validated evidence + hypotheses)
    ↓
Experiment Planner (deterministic tool precondition checks)
    ↓
Deterministic Statistical Toolbox
    ↓
Judge Agent (GPT-5.6 Sol, evidence-cited synthesis)
```

GPT-5.6 Sol is the **only production LLM**. All model traffic is sent through AgentRouter's OpenAI-compatible API; AMRRA does not contact OpenAI directly and does not fall back to a second model. If AgentRouter reranking is temporarily unavailable, retrieval degrades to deterministic lexical ranking, while extraction/judging fail explicitly rather than silently switching providers.

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
- **AgentRouter OpenAI-compatible API**: GPT-5.6 Sol retrieval reranking, extraction and judging
- **Next.js 14**: real workbench wired to the run API
- **Alembic**: database migrations
- **Docker Compose**: reproducible local production topology
- **GitHub Actions**: backend coverage, agent evals and frontend build/test gates

## Quick start

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Set your AgentRouter key:

```bash
AGENTROUTER_API_KEY=...
AGENTROUTER_BASE_URL=https://co.agentrouter.org/v1
AGENTROUTER_MODEL=gpt-5.6-sol
```

AgentRouter model availability is account/resource-pool specific. If the model page for your key shows a suffixed or alternate GPT-5.6 Sol ID, use that exact value for `AGENTROUTER_MODEL`.

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
export AGENTROUTER_API_KEY=...
export AGENTROUTER_MODEL=gpt-5.6-sol
uvicorn main:app --reload
```

The default local database is SQLite. PostgreSQL deployments use Alembic migrations and do not auto-create tables.

Run tests:

```bash
PYTHONPATH=. pytest --cov=app --cov-report=term-missing --cov-fail-under=85 -q
```

Run the live agent-quality suite against AgentRouter:

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
- AgentRouter credentials are environment-only and are never exposed to the frontend.
- Agent provider errors are typed run failures; the system never inserts fake hypotheses to keep the pipeline alive.

## Test strategy

Tests cover schema invariants, GPT reranking constraints/fallback, planner tool-selection rules, statistical branches, hallucinated citation filtering, AgentRouter response validation, SSRF controls, persistence, failed traces, API validation and a full end-to-end agent run using a deterministic fake provider. The fake provider exists only for tests/offline evals; production has one provider: GPT-5.6 Sol through AgentRouter.
