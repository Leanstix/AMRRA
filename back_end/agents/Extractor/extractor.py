import os
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate

from model.extractor_model import Evidence, ExtractionError, RetrievalOutput
from .state import ExtractionState
from .prompt import PROMPT_TEMPLATE
from .utils import ExtractionUtils


class OptimizedExtractionChainFull:
    TOP_EVIDENCE = 8
    MIN_EVIDENCE = 1

    def run(self, input_data: RetrievalOutput):
        state = ExtractionState(run_id=input_data.run_id, evidence_chunks=input_data.evidence_chunks)

        # -------------------- Filter usable chunks --------------------
        state.usable = [ev for ev in state.evidence_chunks if ev and ev.text.strip()]
        if len(state.usable) < self.MIN_EVIDENCE:
            return ExtractionError(
                run_id=state.run_id,
                reason_code="MISSING_DATA",
                error=f"Need at least {self.MIN_EVIDENCE} non-empty evidence chunks"
            )

        top_evidence = state.usable[:self.TOP_EVIDENCE]
        combined_text = "\n\n".join(ev.text[:2000] for ev in top_evidence)

        # -------------------- Extract numeric data --------------------
        numeric_map = {
            ev.chunk_id: ExtractionUtils.extract_numbers_from_text(ev.text)
            for ev in top_evidence
        }

        # Keep only arrays with more than 1 number
        numeric_map = {k: v for k, v in numeric_map.items() if v and len(v) > 1}

        # -------------------- Prepare LLM prompt --------------------
        prompt = PromptTemplate(input_variables=["text"], template=PROMPT_TEMPLATE)
        data = None

        # GPT-5 extraction
        if os.getenv("OPENAI_API_KEY"):
            try:
                chat = ChatOpenAI(model_name="gpt-5-mini", temperature=0.0)
                response = chat([HumanMessage(content=prompt.format(text=combined_text))])
                raw_content = getattr(response, "content", str(response))
                data = ExtractionUtils.safe_parse_json(raw_content)
            except Exception as e:
                print("GPT-5 extraction failed:", e)

        # Groq fallback
        if not data and os.getenv("GROQ_API_KEY"):
            try:
                chat = ChatGroq(model="openai/gpt-oss-20b", api_key=os.getenv("GROQ_API_KEY"), temperature=0.0)
                response = chat([HumanMessage(content=prompt.format(text=combined_text))])
                raw_content = getattr(response, "content", str(response))
                data = ExtractionUtils.safe_parse_json(raw_content)
            except Exception as e:
                print("Groq extraction failed:", e)

        # -------------------- Ensure at least one hypothesis --------------------
        if not data:
            data = {"hypotheses": [{"hypothesis": "Auto-generated", "variables": {}, "numeric_data": {}}]}

        # -------------------- Determine test type based on real numeric evidence --------------------
        test_type = ExtractionUtils.detect_test_type(numeric_map) if numeric_map else "descriptive"

        # -------------------- Build structured hypotheses --------------------
        structured_hypotheses = []
        for h in data.get("hypotheses", []):
            # Keep only numeric data that is actually in evidence
            filtered_numeric = {k: v for k, v in h.get("numeric_data", {}).items() if k in numeric_map}

            structured = {
                "hypothesis": h.get("hypothesis", ""),
                "variables": list(h.get("variables", {}).keys()),
                "numeric_data": filtered_numeric or numeric_map,
                "evidence": [ev.text[:500] for ev in top_evidence[:5]],
                "test": test_type
            }

            # Assign groups/data according to test type
            if test_type in ["ttest", "anova"] and numeric_map:
                structured["groups_raw"] = [
                    {"name": f"Group {chr(65+idx)}", "data": nums}
                    for idx, (chunk_id, nums) in enumerate(numeric_map.items())
                ]
            elif test_type == "chi2" and numeric_map:
                structured["data"] = [v[0] for v in numeric_map.values()]
                structured["expected"] = [sum(v)/len(v) for v in numeric_map.values()]
            elif test_type == "regression" and len(numeric_map) >= 2:
                arrays = list(numeric_map.values())
                structured["groups_raw"] = [{"name": "X", "values": arrays[0]}, {"name": "Y", "values": arrays[1]}]
            elif test_type == "logistic" and numeric_map:
                structured["groups_raw"] = [
                    {"name": f"Var{idx+1}", "values": nums}
                    for idx, nums in enumerate(numeric_map.values())
                ]

            structured_hypotheses.append(structured)

        return structured_hypotheses
