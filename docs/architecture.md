# AMRRA Agent Architecture

## Design invariant

The LLM may **propose meaning**; deterministic code owns **calculation and validation**.

### 1. Ingestion

PDFs are parsed at the API boundary and normalized into text so workers do not depend on a local upload filesystem. Public URLs are materialized by the worker with SSRF checks on the initial URL and every redirect.

### 2. Retrieval

Documents are chunked into bounded evidence units. Lexical relevance is always available. When the Cohere embedding endpoint is healthy, semantic similarity is blended into the score. Embedding failure degrades retrieval instead of failing the run.

### 3. Extractor Agent

The Extractor uses schema-constrained JSON generation. Each hypothesis and numerical observation must cite one or more supplied chunk IDs. Unknown references are removed before the result becomes trusted domain data.

### 4. Experiment Planner

The Planner is deterministic. It converts semantic observations into a tool invocation only when tool preconditions are met. For example, a t-test requires two actual groups with raw observations or two explicit mean/SD/n summaries. This prevents years, p-values and page numbers from accidentally becoming sample observations.

### 5. Statistical Toolbox

The toolbox never calls an LLM. It runs SciPy/NumPy calculations and emits a typed `ExperimentResult`. Invalid inputs become typed failed/insufficient results instead of exceptions leaking into the report.

### 6. Judge Agent

The Judge sees immutable deterministic outputs and evidence chunks. It synthesizes significance, practical meaning and limitations but cannot alter the stored statistical results. Unknown citations are filtered.

### 7. Observability

Each stage persists:

- `run_id` / `event_id`
- stage and status
- start/end timestamps and latency
- model and prompt version where applicable
- stable input/output hashes
- retry count
- error code/message
- stage-specific metadata, including statistical tool calls

This makes failures attributable to a specific stage instead of evaluating only the final prose.
