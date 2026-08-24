# AMRRA Agent Architecture

## Design invariant

The LLM may **propose meaning**; deterministic code owns **calculation and validation**.

AMRRA has one production LLM provider: **Groq**, using `openai/gpt-oss-20b` by default through Groq's OpenAI-compatible Chat Completions endpoint. There is no secondary-model/provider fallback.

Groq retired `llama-3.1-8b-instant` for free/developer tiers on 2026-08-16 and recommends `openai/gpt-oss-20b` as its replacement. AMRRA recognizes that one legacy model ID and maps it to the replacement so an older local `.env` cannot keep sending dead-model requests. The worker logs the migration and all traces use the effective model ID.

### 1. Ingestion

PDFs are parsed at the API boundary and normalized into text so workers do not depend on a local upload filesystem. Public URLs are materialized by the worker with SSRF checks on the initial URL and every redirect.

### 2. Retrieval

Documents are chunked into bounded evidence units. Deterministic lexical relevance generates a constrained shortlist. GPT-OSS may then rerank only the supplied chunk IDs and attach a relevance score/reason; unknown IDs are ignored. If Groq is temporarily unavailable during reranking, retrieval degrades to the lexical shortlist instead of switching to another provider.

### 3. Extractor Agent

GPT-OSS extracts hypotheses and semantic observations. `openai/gpt-oss-20b` supports Groq strict Structured Outputs, so AMRRA converts each Pydantic model schema into Groq's strict JSON Schema subset before generation. Every object is closed with `additionalProperties: false`, every field is required, and optional values remain nullable. Pydantic validates the generated payload again at the trust boundary.

Each hypothesis and observation must cite one or more supplied chunk IDs. Unknown references are removed.

### 4. Experiment Planner

The Planner is deterministic. It converts semantic observations into a tool invocation only when tool preconditions are met. For example, a t-test requires two actual groups with raw observations or two explicit mean/SD/n summaries. This prevents years, p-values and page numbers from accidentally becoming sample observations.

### 5. Statistical Toolbox

The toolbox never calls an LLM. It runs SciPy/NumPy calculations and emits a typed `ExperimentResult`. Invalid inputs become typed failed/insufficient results instead of exceptions leaking into the report.

### 6. Judge Agent

GPT-OSS sees immutable deterministic outputs and evidence chunks. It synthesizes significance, practical meaning and limitations but cannot alter the stored statistical results. Unknown citations are filtered.

### 7. Provider boundary

The backend sends OpenAI-compatible `POST /chat/completions` requests to `LLM_BASE_URL` (default `https://api.groq.com/openai/v1`) with `LLM_API_KEY` as a Bearer token. Runtime configuration is explicit:

- `LLM_PROVIDER=groq`
- `LLM_API_STYLE=openai_chat`
- `LLM_MODEL=openai/gpt-oss-20b`
- `LLM_MAX_COMPLETION_TOKENS=4096`

The provider fails configuration if a different provider or API style is supplied, which prevents an accidental silent provider switch.

Permanent authorization/request/model failures fail fast. Retryable transport, rate-limit and server failures use bounded exponential backoff. API keys are redacted from surfaced provider errors, and diagnostics expose only a SHA-256 fingerprint for configuration comparison.

### 8. Observability

Each stage persists:

- `run_id` / `event_id`
- stage and status
- start/end timestamps and latency
- effective model and prompt version where applicable
- provider metadata for probabilistic stages
- stable input/output hashes
- retry count
- error code/message
- stage-specific metadata, including retrieval rerank metadata and statistical tool calls

This makes failures attributable to a specific stage instead of evaluating only the final prose.
