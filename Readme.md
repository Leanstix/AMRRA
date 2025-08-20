Overview

The Retriever Agent is a backend service for ingesting, indexing, and retrieving text chunks from PDFs and URLs. It supports hybrid retrieval using vector embeddings (Cohere) and BM25 keyword scoring, and ensures separation of content sources for consistency.

PDF chunks and URL chunks are always handled separately.

Deduplication is based on doc_id.

Supports persistence (FAISS index + metadata).

Features

Ingest text from PDFs or URLs.

Automatically chunk large texts (default 500 tokens, 100 overlap).

Generate embeddings using Cohere Embeddings.

Hybrid retrieval (BM25 + vector similarity).

Deduplicate by doc_id.

Support queries with section filtering (pdf or url).

Save/load FAISS index + metadata for fast restarts.

Requirements

Python 3.10+

faiss-cpu

numpy

cohere

rank_bm25

python-dotenv

fastapi, uvicorn

Utilities for PDF and URL extraction (utils.py)


Setup

Clone repo:

git clone <your_repo_url>
cd <your_repo>


Install dependencies:

pip install -r requirements.txt


Create .env:

COHERE_API_KEY=<your_cohere_api_key>
EMBEDDING_MODEL=embed-english-v3.0
RETRIEVER_PERSIST_DIR=./persist


Start server:

uvicorn main:app --reload

API Endpoints
1. Ingest PDF
POST /ingest
Content-Type: multipart/form-data

{
  "type": "pdf",
  "doc_id": "ml_pdf_01",
  "title": "Machine Learning PDF Sample",
  "file": "<file.pdf>"
}

2. Ingest URL
POST /ingest
Content-Type: application/json

{
  "type": "url",
  "doc_id": "ml_url_01",
  "title": "ML Article from Web",
  "url": "https://arxiv.org/abs/2306.00001"
}

3. Retrieve
POST /retrieve
Content-Type: application/json

{
  "query": "Supervised Machine Learning",
  "k": 5,
  "alpha": 0.5,
  "section_filter": "pdf"   # "pdf" or "url"
}


Response:

{
  "query": "...",
  "results": [
    {
      "chunk_id": "ml_pdf_01_23",
      "doc_id": "ml_pdf_01",
      "title": "...",
      "text": "...",
      "score_bm25": 0.98,
      "score_vec": 0.91,
      "score_hybrid": 0.95,
      "meta": { "source_type": "pdf", "file": "thebook.pdf", "chunk_index": 23 }
    }
  ],
  "provenance": {
    "k": 5,
    "alpha": 0.5,
    "embedding_model": "embed-english-v3.0",
    "chunks_indexed": 3
  }
}

Doc ID & Chunk Management

Each document must have a unique doc_id.

Multiple PDFs/URLs are allowed as long as doc_id differs.

Chunks are never mixed between PDFs and URLs; section_filter ensures separation.

Deduplication occurs per doc_id, not per topic — identical topics in different PDFs are fine.

Recommended doc_id convention:

<type>_<topic>_<increment>
Examples:
- pdf_ml_01
- pdf_ml_02
- url_tinyml_01

Chunking & Indexing

Default chunk size: 500 tokens

Default overlap: 100 tokens

Uses chunk_text utility for splitting text

BM25 tokenization is simple whitespace + lowercase

Vector embeddings are normalized for cosine similarity

Hybrid Retrieval

Vector Similarity (Cohere)

BM25 Keyword Matching

Hybrid score = alpha * vector_score + (1-alpha) * BM25_score

Deduplication option to avoid returning multiple chunks from the same doc.

Persistence

FAISS index: <RETRIEVER_PERSIST_DIR>/faiss.index

Metadata pickle: <RETRIEVER_PERSIST_DIR>/meta.pkl

Reloads automatically on startup (if files exist).

Best Practices

Always assign unique doc_ids per PDF/URL.

Keep PDFs/URLs separate to maintain retrieval consistency.

Use section_filter to query only the source you want.

Regularly save index after ingestion for persistence.

When multiple topics are uploaded, queries may return chunks from multiple topics — that’s normal.