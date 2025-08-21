Multi-Agent Retrieval & Extraction API

This API supports a Retriever → Extractor → Hypothesis generation workflow, allowing the frontend to query sources (PDFs, URLs), retrieve relevant chunks, and automatically generate testable hypotheses with numeric/statistical context.

1. Workflow Overview

Step 1: Ingest content (Retriever)

PDF files or URLs are sent to the Retriever.

Text is extracted and cached in Redis for future retrieval.

Chunks are split, normalized, and stored in memory for fast retrieval.

Step 2: Query and retrieve (Retriever)

Frontend sends a query (e.g., "machine learning").

Retriever searches all relevant sources (pdf, url) and returns top-k most relevant chunks.

Chunks are truncated, cleaned, and passed to Extractor.

Step 3: Extract hypotheses (Extractor)

Extractor receives evidence chunks with text content.

GPT-5 Mini or Groq LLM generates three distinct, testable hypotheses.

Numeric data is automatically extracted from text for each variable.

Statistical test type is inferred (ttest, anova, regression, chi2) based on numeric data arrays.

Final output contains:

hypotheses with variables and numeric data

evidence used

test type (if numeric data exists)

groups_raw for experimental groups (for testing/analysis)

Step 4 (optional): Experimentation & Judge Agent

The frontend or backend can use groups_raw and numeric_data to perform statistical tests.

Judge agent can evaluate hypothesis strength, effect sizes, and reproducibility.

2. Endpoints
A. Retriever Endpoints
1. Health Check
GET /retriever/health


Response

{
  "ok": true,
  "sources": {"pdf": 10, "url": 5},
  "model": "embed-english-v3.0"
}

2. Ingest content
POST /retriever/ingest
Content-Type: application/json


Body (PDF or URL only)

{
  "items": [
    {"doc_id": "doc1", "file_path": "path/to/file.pdf", "title": "PDF Example"},
    {"doc_id": "doc2", "url": "https://example.com/article", "title": "URL Example"}
  ]
}


Response

{"status": "processing"}


Backend extracts text and stores in memory/Redis asynchronously.

B. Extractor Endpoint
POST /extractor/run
Content-Type: application/json


Body

{
  "run_id": "test_run_001",
  "query": "machine learning",
  "evidence_chunks": [
    {
      "chunk_id": "c1",
      "doc_id": "doc1",
      "text": "Model achieved 85% accuracy with 100 labeled examples.",
      "title": "ML Experiment 1",
      "meta": {"source_type": "pdf"}
    },
    {
      "chunk_id": "c2",
      "doc_id": "doc2",
      "text": "Regression analysis shows MSE decreased from 0.35 to 0.12 as training increased.",
      "title": "ML Experiment 2",
      "meta": {"source_type": "url", "url": "https://example.com/ml_exp"}
    }
  ],
  "provenance": {"chunks_used": 2}
}


Response (success)

{
  "run_id": "test_run_001",
  "hypotheses": [
    {
      "hypothesis": "Model accuracy increases with number of labeled training samples.",
      "variables": ["training_data_size", "model_accuracy"],
      "numeric_data": {
        "training_data_size": [100, 150],
        "model_accuracy": [85, 88]
      },
      "evidence": ["Model achieved 85% accuracy with 100 labeled examples.", "Regression analysis shows MSE decreased from 0.35 to 0.12 as training increased."],
      "groups_raw": [
        {"name": "Group A", "data": [100]},
        {"name": "Group B", "data": [150]}
      ],
      "test": "ttest"
    },
    ...
  ],
  "notes": "",
  "provenance": {"chunks_used": 2}
}


numeric_data: parsed numeric values from evidence.

groups_raw: for statistical testing (e.g., t-test, ANOVA).

test: inferred test type.

C. Pipeline Endpoint
POST /pipeline/run
Content-Type: application/json


Body

{
  "query": "machine learning",
  "k": 5,
  "alpha": 0.7,
  "section_filter": "pdf,url"
}


Workflow

Retrieve top-k chunks from pdf and url.

Clean, truncate, remove repeated headers.

Send to Extractor.

Return structured hypotheses with numeric data + test type.

Response

{
  "run_id": "pipeline_run_001",
  "hypotheses": [...],
  "notes": "",
  "provenance": {"chunks_used": 5}
}


section_filter ensures only PDF/URL sources are queried.

Suitable for frontend query box integration.

3. Frontend Integration

Fetch top-k hypotheses:

async function getHypotheses(query) {
  const response = await fetch("http://127.0.0.1:8000/pipeline/run", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      query: query,
      k: 5,
      alpha: 0.7,
      section_filter: "pdf,url"
    })
  });
  const data = await response.json();
  return data.hypotheses;
}


Each hypothesis object has:

hypothesis: text

variables: list of variables

numeric_data: numbers extracted

evidence: original chunks

groups_raw: raw numeric groups

test: suggested statistical test

Use groups_raw + test in frontend analytics charts or experimental modules.

4. Notes

Minimum evidence chunks: 3 (otherwise extractor returns MISSING_DATA).

Numeric detection: if evidence contains numbers → statistical test inferred.

Cache: Redis avoids re-parsing PDFs/URLs repeatedly.

Frontend focus: use pipeline/run for end-to-end retrieval + extraction.

5. Example Frontend Output
[
  {
    "hypothesis": "Model accuracy increases with number of labeled samples",
    "variables": ["training_data_size", "model_accuracy"],
    "numeric_data": {"training_data_size": [100,150], "model_accuracy": [85,88]},
    "evidence": [...],
    "groups_raw": [{"name":"Group A","data":[100]}, {"name":"Group B","data":[150]}],
    "test": "ttest"
  }
]
