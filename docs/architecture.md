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

Extractor roles and value types are constrained to AMRRA's domain vocabulary during generation rather than being accepted as arbitrary strings and silently discarded later. Runtime evidence IDs are still validated against the Retriever's actual chunk set, and extraction traces record raw/grounded/dropped hypothesis and observation counts.

A hypothesis may be qualitative and remain useful even when the source does not expose enough structured numerical observations for an inferential test. AMRRA therefore preserves grounded qualitative hypotheses with empty observations instead of forcing the model to manufacture numbers.

If the primary extraction produces zero grounded hypotheses, AMRRA performs one focused recovery pass over the highest-ranked evidence with a smaller output budget. The recovery pass is allowed to return an empty list again; it exists to recover overly conservative or poorly grounded model output, not to fabricate a hypothesis.

If both passes remain empty, that is treated as a research outcome rather than an infrastructure failure. Planning and experimentation continue with empty collections and the Judge produces an evidence-only assessment that explicitly states no inferential hypothesis/test was supported by the available evidence.

### 4. Experiment Planner

The Planner is deterministic. It converts semantic observations into a tool invocation only when tool preconditions are met. For example, a t-test requires two actual groups with raw observations or two explicit mean/SD/n summaries. This prevents years, p-values and page numbers from accidentally becoming sample observations.

An empty hypothesis list is valid: the Planner returns no tool calls rather than raising an exception.

### 5. Statistical Toolbox

The toolbox never calls an LLM. It runs SciPy/NumPy calculations and emits a typed `ExperimentResult`. Invalid inputs become typed failed/insufficient results instead of exceptions leaking into the report. An empty experiment plan is also valid and produces no fabricated computation.

### 6. Judge Agent

GPT-OSS sees immutable deterministic outputs and evidence chunks. It synthesizes significance, practical meaning and limitations but cannot alter the stored statistical results. Unknown citations are filtered.

When no experiment exists, the Judge receives a compact evidence-only envelope and must state that AMRRA could not support an inferential hypothesis/test from the available material. This allows a run to complete honestly instead of failing merely because the evidence is descriptive or insufficiently structured.

### 7. Provider boundary

The backend sends OpenAI-compatible `POST /chat/completions` requests to `LLM_BASE_URL` (default `https://api.groq.com/openai/v1`) with `LLM_API_KEY` as a Bearer token. Runtime configuration is explicit:

- `LLM_PROVIDER=groq`
- `LLM_API_STYLE=openai_chat`
- `LLM_MODEL=openai/gpt-oss-20b`
- `LLM_MAX_COMPLETION_TOKENS=4096`
- stage-specific completion budgets for reranking, extraction, and judging

The provider fails configuration if a different provider or API style is supplied, which prevents an accidental silent provider switch.

Strict JSON Schema is the preferred output path. AMRRA still treats Groq as an external probabilistic service rather than assuming its strict-generation implementation can never fail. If Groq returns its provider-side `400 Generated JSON does not match the expected schema` / `failed_generation` error, the provider performs one compatibility recovery using JSON Object Mode for that same typed request. The returned JSON is then validated locally by the original Pydantic model before it can cross the trust boundary. A locally invalid recovery response is repaired only within the configured retry budget; it is never accepted as trusted state.

This fallback is transport-level compatibility handling, not a second LLM/provider fallback: the model and Groq endpoint remain unchanged. Unrelated HTTP 400 errors remain permanent failures and are not retried blindly.

Permanent authorization/request/model failures fail fast. Retryable transport, rate-limit and server failures use bounded backoff; Groq `retry-after` is honored for rate limits, and TPM-specific 413 responses can reduce the output reservation before retrying. API keys are redacted from surfaced provider errors, and diagnostics expose only a SHA-256 fingerprint for configuration comparison.

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
- extraction grounding counters and whether a focused recovery pass ran
- `evidence_only_fallback` on extraction/planning/experimentation/judging when no inferential path is supported

This makes failures and non-failure fallbacks attributable to a specific stage instead of evaluating only the final prose.
