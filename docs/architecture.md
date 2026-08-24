# AMRRA Agent Architecture

## Design invariant

The LLM may **propose meaning**; deterministic code owns **calculation and validation**.

AMRRA has one production LLM: **GPT-5.6 Sol**, routed exclusively through AgentRouter's OpenAI-compatible endpoint. There is no Cohere/OpenAI-direct/secondary-model fallback.

### 1. Ingestion

PDFs are parsed at the API boundary and normalized into text so workers do not depend on a local upload filesystem. Public URLs are materialized by the worker with SSRF checks on the initial URL and every redirect.

### 2. Retrieval

Documents are chunked into bounded evidence units. Deterministic lexical relevance generates a constrained shortlist. GPT-5.6 Sol may then rerank only the supplied chunk IDs and attach a relevance score/reason; unknown IDs are ignored. If AgentRouter is temporarily unavailable during reranking, retrieval degrades to the lexical shortlist instead of switching to another model.

### 3. Extractor Agent

GPT-5.6 Sol extracts hypotheses and semantic observations through AgentRouter. The request includes the target JSON schema, and every response is Pydantic-validated before entering trusted domain state. Each hypothesis and observation must cite one or more supplied chunk IDs. Unknown references are removed.

### 4. Experiment Planner

The Planner is deterministic. It converts semantic observations into a tool invocation only when tool preconditions are met. For example, a t-test requires two actual groups with raw observations or two explicit mean/SD/n summaries. This prevents years, p-values and page numbers from accidentally becoming sample observations.

### 5. Statistical Toolbox

The toolbox never calls an LLM. It runs SciPy/NumPy calculations and emits a typed `ExperimentResult`. Invalid inputs become typed failed/insufficient results instead of exceptions leaking into the report.

### 6. Judge Agent

GPT-5.6 Sol sees immutable deterministic outputs and evidence chunks. It synthesizes significance, practical meaning and limitations but cannot alter the stored statistical results. Unknown citations are filtered.

### 7. Provider boundary

The backend sends OpenAI-compatible `POST /chat/completions` requests to `AGENTROUTER_BASE_URL` (default `https://co.agentrouter.org/v1`) with `AGENTROUTER_API_KEY`. The model defaults to `gpt-5.6-sol` and is overrideable through `AGENTROUTER_MODEL` because AgentRouter model IDs can be resource-pool specific. The backend does not use an OpenAI SDK or an `api.openai.com` endpoint.

### 8. Observability

Each stage persists:

- `run_id` / `event_id`
- stage and status
- start/end timestamps and latency
- model and prompt version where applicable
- stable input/output hashes
- retry count
- error code/message
- stage-specific metadata, including retrieval rerank metadata and statistical tool calls

This makes failures attributable to a specific stage instead of evaluating only the final prose.
