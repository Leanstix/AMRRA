# optimized_extraction_chain_full.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Union
import os, json, re
from dotenv import load_dotenv

load_dotenv()

from model.extractor_model import Evidence, ExtractionError, ExtractionOutput, RetrievalOutput
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate

@dataclass
class ExtractionState:
    run_id: str
    evidence_chunks: List[Evidence]
    usable: List[Evidence] = field(default_factory=list)
    structured_hypotheses: List[Dict] = field(default_factory=list)

class OptimizedExtractionChainFull:

    TOP_EVIDENCE = 8
    MIN_EVIDENCE = 3

    PROMPT_TEMPLATE = """
You are a research scientist analyzing multiple evidence chunks from different sources.

Generate **three distinct, testable, and falsifiable hypotheses** using the combined evidence.

Each hypothesis must include:
- Hypothesis statement
- Key variables with their type (numeric, categorical, binary)
- Reference at least two evidence chunks
- Extract numeric data points from the evidence

Text:
{text}

Respond strictly in JSON format as follows:
{{
  "hypotheses": [
    {{
      "hypothesis": "<string>",
      "variables": {{"variable_name": "type"}},
      "numeric_data": {{"variable_name": [numbers found]}},
      "provenance": ["list of chunk_ids referenced"]
    }},
    ... (3 items)
  ]
}}
"""

    NUMERIC_REGEX = re.compile(r"[-+]?\d*\.\d+|\d+")

    @staticmethod
    def safe_parse_json(raw_text: str):
        if not raw_text:
            return None
        clean_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError as e:
            print("JSON parsing failed:", e)
            print("Raw text was:", clean_text[:500])
            return None

    @staticmethod
    def extract_numbers_from_text(text: str) -> List[Union[int, float]]:
        nums = OptimizedExtractionChainFull.NUMERIC_REGEX.findall(text)
        return [float(n) if '.' in n else int(n) for n in nums]

    def detect_test_type(self, numeric_map: Dict[str, List[float]]) -> str:
        arrays = [v for v in numeric_map.values() if v]
        if len(arrays) == 2 and all(len(v) > 1 for v in arrays):
            return "ttest"
        elif len(arrays) > 2:
            return "anova"
        elif any(len(v) == 1 for v in arrays):
            return "chi2"
        elif len(arrays) == 2:
            return "regression"
        else:
            return "unknown"

    def run(self, input_data: RetrievalOutput) -> List[Dict] | ExtractionError:
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
        combined_text = "\n\n".join(ev.text[:2000] for ev in top_evidence)  # limit per chunk to avoid overflow

        # Extract numeric data
        numeric_map = {ev.chunk_id: self.extract_numbers_from_text(ev.text) for ev in top_evidence}

        # ---------------- GPT-5 ----------------
        data = None
        prompt = PromptTemplate(input_variables=["text"], template=self.PROMPT_TEMPLATE)
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

        # ---------------- Build structured output ----------------
        structured_hypotheses = []
        test_type = self.detect_test_type(numeric_map)
        for h in data.get("hypotheses", []):
            structured_hypotheses.append({
                "hypothesis": h.get("hypothesis", ""),
                "variables": list(h.get("variables", {}).keys()),
                "numeric_data": h.get("numeric_data", {}),
                "evidence": [ev.text[:500] for ev in top_evidence[:5]],  # top 5 evidence snippets
                "test": test_type
            })

            # Additional fields based on test type
            if test_type in ["ttest", "anova"]:
                groups_raw = []
                for idx, (chunk_id, nums) in enumerate(numeric_map.items()):
                    groups_raw.append({"name": f"Group {chr(65+idx)}", "data": nums})
                structured_hypotheses[-1]["groups_raw"] = groups_raw
            elif test_type == "chi2":
                structured_hypotheses[-1]["data"] = [v[0] if v else 0 for v in numeric_map.values()]
                structured_hypotheses[-1]["expected"] = [sum(v)/len(v) if v else 0 for v in numeric_map.values()]
            elif test_type == "regression":
                arrays = list(numeric_map.values())
                structured_hypotheses[-1]["groups_raw"] = [
                    {"name": "X", "values": arrays[0]},
                    {"name": "Y", "values": arrays[1]}
                ]
            elif test_type == "logistic":
                structured_hypotheses[-1]["groups_raw"] = [
                    {"name": f"Var{idx+1}", "values": nums} for idx, nums in enumerate(numeric_map.values())
                ]

        return structured_hypotheses


def run_extraction(input_data: RetrievalOutput) -> ExtractionOutput | ExtractionError:
    result = OptimizedExtractionChainFull().run(input_data)

    if isinstance(result, ExtractionError):
        return result

    hypotheses = []
    for h in result:
        hypotheses.append({
            "hypothesis": h.get("hypothesis", ""),
            "variables": h.get("variables", []),
            "numeric_data": h.get("numeric_data", {}),
            "evidence": h.get("evidence", []),
            "groups_raw": h.get("groups_raw", None),
            "data": h.get("data", None),
            "expected": h.get("expected", None),
            "test": h.get("test", None),
        })

    return ExtractionOutput(
        run_id=input_data.run_id,
        hypotheses=hypotheses,
        notes="",
        provenance={"chunks_used": len(input_data.evidence_chunks)}
    )
