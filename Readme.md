# Retriever → Extractor Workflow

## Overview

This module handles the **retrieval of relevant content** and **generation of hypotheses** from that content. The workflow is designed to process multiple data sources (`pdf`, `url`) and produce structured hypotheses with evidence.

---

## Workflow

1. **User submits a query**:

- Example: `"machine learning optimization techniques"`  
- Optional filters for source: `"pdf"`, `"url"`  
- Number of top chunks: `k` (e.g., 5)  

2. **Retriever Agent**:

- Searches the database of embedded content for chunks that **match the query**.  
- Retrieves the **top `k` most relevant chunks** per source or globally.  
- Handles multiple sources and ensures chunks are **related to the same topic**.  

**Output from Retriever**:

```json
{
  "run_id": "unique-run-id",
  "chunks": [
    {
      "source": "pdf",
      "chunk_id": "pdf_chunk_1",
      "text": "Relevant excerpt from PDF...",
      "similarity_score": 0.92
    },
    {
      "source": "url",
      "chunk_id": "url_chunk_1",
      "text": "Relevant excerpt from URL...",
      "similarity_score": 0.88
    }
  ]
}
Extractor Agent:

Receives top chunks from Retriever.

Generates hypotheses based on content.

Extracts key variables and supporting evidence from the chunks.

Output from Extractor:

{
  "run_id": "unique-run-id",
  "hypotheses": [
    {
      "hypothesis": "Kernelized ML algorithms achieve higher accuracy than non-kernelized algorithms.",
      "variables": ["classification_accuracy", "algorithm_type"],
      "evidence": [
        "Excerpt from PDF chunk 1...",
        "Excerpt from URL chunk 1..."
      ]
    },
    {
      "hypothesis": "Stochastic optimization converges faster than batch optimization on large datasets.",
      "variables": ["convergence_time", "optimization_method"],
      "evidence": [
        "Excerpt from PDF chunk 2...",
        "Excerpt from URL chunk 2..."
      ]
    }
  ],
  "provenance": {
    "chunks_used": 5
  }
}
Key Notes
The Retriever ensures that only top relevant chunks are sent to the Extractor to reduce noise.

The Extractor does not modify the original chunks; it only extracts information and builds hypotheses.

k controls how many chunks per source are retrieved.

Evidence is returned as text snippets that directly support the hypotheses.