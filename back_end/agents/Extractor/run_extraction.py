from model.extractor_model import ExtractionOutput, ExtractionError, RetrievalOutput
from .extractor import OptimizedExtractionChainFull

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
