# optimized_extraction_chain_clean.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from model.extractor_model import Evidence,ExtractionError, ExtractionOutput, RetrievalOutput
import os, json
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

@dataclass
class ExtractionState:
    run_id: str
    evidence_chunks: List[Evidence]
    usable: List[Evidence] = field(default_factory=list)
    structured_hypotheses: List[dict] = field(default_factory=list)

class OptimizedExtractionChain:

    TOP_EVIDENCE = 8
    MIN_EVIDENCE = 3

    PROMPT_TEMPLATE = """
You are a research scientist analyzing multiple evidence chunks from different sources.

Generate **three distinct, testable, and falsifiable hypotheses** using the combined evidence.

Each hypothesis must include:

- Hypothesis statement
- Key variables and their type (numeric, categorical, binary)
- Reference at least two evidence chunks

Text:
{text}

Respond strictly in JSON format as follows:
{{
  "hypotheses": [
    {{
      "hypothesis": "<string>",
      "variables": {{"variable_name": "type"}},
      "provenance": ["list of chunks referenced"]
    }},
    ... (3 items)
  ]
}}
"""

    @staticmethod
    def safe_parse_json(raw_text: str):
        import re
        if not raw_text:
            return None
        clean_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError as e:
            print("JSON parsing failed:", e)
            print("Raw text was:", clean_text[:500])
            return None

    def run(self, input_data: RetrievalOutput) -> List[dict] | ExtractionError:
        state = ExtractionState(run_id=input_data.run_id, evidence_chunks=input_data.evidence_chunks)

        # Filter usable chunks
        state.usable = [ev for ev in state.evidence_chunks if ev and ev.text.strip()]
        if len(state.usable) < self.MIN_EVIDENCE:
            return ExtractionError(
                run_id=state.run_id,
                reason_code="MISSING_DATA",
                error=f"Need at least {self.MIN_EVIDENCE} non-empty evidence chunks"
            )

        top_evidence = state.usable[:self.TOP_EVIDENCE]
        combined_text = "\n\n".join(ev.text for ev in top_evidence)
        prompt = PromptTemplate(input_variables=["text"], template=self.PROMPT_TEMPLATE)
        parser = StrOutputParser()
        data = None

        # ---------------- GPT-5 ----------------
        if os.getenv("OPENAI_API_KEY"):
            try:
                chat = ChatOpenAI(model_name="gpt-5-mini", temperature=0.0)
                response = chat([HumanMessage(content=prompt.format(text=combined_text))])
                data = self.safe_parse_json(getattr(response, "content", ""))
            except Exception as e:
                print("GPT-5 extraction failed:", e)

        # ---------------- Groq fallback ----------------
        if not data and os.getenv("GROQ_API_KEY"):
            try:
                chat = ChatGroq(model="openai/gpt-oss-20b", api_key=os.getenv("GROQ_API_KEY"), temperature=0.0)
                response = chat([HumanMessage(content=prompt.format(text=combined_text))])
                data = self.safe_parse_json(getattr(response, "content", ""))
            except Exception as e:
                print("Groq extraction failed:", e)

        if not data:
            return ExtractionError(
                run_id=state.run_id,
                reason_code="EXTRACTION_FAILED",
                error="Both GPT-5 and Groq extraction failed",
            )

        # ---------------- Build final minimal output ----------------
        structured_hypotheses = []
        for h in data.get("hypotheses", []):
            structured_hypotheses.append({
                "hypothesis": h.get("hypothesis", ""),
                "variables": list(h.get("variables", {}).keys()),
                "evidence": [ev.text for ev in top_evidence[:5]]  # include actual chunk texts
            })

        return structured_hypotheses

def run_extraction(input_data: RetrievalOutput) -> ExtractionOutput | ExtractionError:
    result = OptimizedExtractionChain().run(input_data)

    if isinstance(result, ExtractionError):
        return result

    # Ensure hypotheses are simple dicts
    hypotheses = []
    for h in result:  # result from your extractor
        hypotheses.append({
            "hypothesis": h.get("hypothesis", ""),
            "variables": h.get("variables", []),
            "evidence": h.get("evidence", [])
        })

    return ExtractionOutput(
        run_id=input_data.run_id,
        hypotheses=hypotheses,
        notes="",  
        provenance={"chunks_used": len(input_data.evidence_chunks)}
    )
