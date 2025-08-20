from __future__ import annotations

from typing import List, Tuple

from models import (
	Evidence,
	ExtractionError,
	ExtractionOutput,
	ReasonCode,
	RetrievalOutput,
)


def _non_empty_evidence(evidence_list: List[Evidence]) -> List[Tuple[int, Evidence]]:
	return [
		(idx, ev)
		for idx, ev in enumerate(evidence_list)
		if ev and isinstance(ev.text, str) and ev.text.strip()
	]


def _distinct_sources(evidence_list: List[Evidence]) -> int:
	return len({ev.source for ev in evidence_list if ev.source})


def _detect_variables(evidence_list: List[Evidence]) -> Tuple[List[str], List[str]]:
	# Naive heuristic extraction: pick prominent nouns-like tokens based on simple patterns
	text = "\n".join(ev.text for ev in evidence_list[:8])[:2000]
	candidates: List[str] = []
	triggers = [
		"improves",
		"compared to",
		"versus",
		"vs",
		"increase",
		"decrease",
		"affects",
		"reduces",
		"raises",
	]
	# Basic split by common separators
	tokens = [t.strip(" ,.;:()[]{}\n\t") for t in text.split() if t.strip()]
	# Collect capitalized or domain tokens
	for token in tokens:
		if token.lower() in {"treatment", "control", "baseline"}:
			candidates.append(token.lower())
		elif token.endswith("%"):
			candidates.append("rate")
		elif token.isalpha() and token[0].isupper():
			candidates.append(token)
	# Fallback defaults
	unique = []
	for c in candidates:
		if c.lower() not in [u.lower() for u in unique]:
			unique.append(c)
	if len(unique) < 2:
		unique = ["treatment", "outcome"]
	variables = unique[:3]

	# Type inference: crude detection
	var_types: List[str] = []
	lower_text = text.lower()
	for var in variables:
		if any(k in lower_text for k in ["rate", "score", "mean", "average", "%", "time", "size"]):
			var_types.append("numeric")
		elif any(k in lower_text for k in ["yes", "no", "presence", "absence", "success", "failure"]):
			var_types.append("binary")
		else:
			var_types.append("categorical")

	return variables, var_types


def _build_hypothesis(variables: List[str]) -> str:
	subject = variables[0]
	outcome = variables[1] if len(variables) > 1 else "outcome"
	return f"{subject} improves {outcome} compared to baseline"


def _choose_methods(var_types: List[str]) -> List[str]:
	# Simple mapping: if numeric outcome and categorical/binary predictor -> t-test/ANOVA; else chi-square; else regression for numeric-numeric
	methods: List[str] = []
	if len(var_types) >= 2:
		a, b = var_types[0], var_types[1]
		if (a in {"categorical", "binary"} and b == "numeric") or (
			a == "numeric" and b in {"categorical", "binary"}
		):
			methods = ["t-test", "ANOVA"]
		elif a == "numeric" and b == "numeric":
			methods = ["linear regression", "pearson correlation"]
		else:
			methods = ["chi-square"]
	return methods


def _assumptions_for_methods(methods: List[str]) -> List[str]:
	assumptions: List[str] = ["independent observations"]
	if any(m in {"t-test", "ANOVA"} for m in methods):
		assumptions.append("approximately normal outcome distribution")
		assumptions.append("homogeneity of variances across groups")
	if any("regression" in m for m in methods):
		assumptions.append("linearity between predictors and outcome")
		assumptions.append("residuals approximately normal with constant variance")
	return assumptions


def run_extraction(input_data: RetrievalOutput) -> ExtractionOutput | ExtractionError:
	usable = _non_empty_evidence(input_data.evidence_chunks)
	if len(usable) < 3:
		return ExtractionError(
			run_id=input_data.run_id,
			reason_code=ReasonCode.INSUFFICIENT_EVIDENCE,
			message="Need at least 3 non-empty evidence chunks",
		)

	top_evidence = [ev for _, ev in usable][:8]
	if _distinct_sources(top_evidence) < 2:
		return ExtractionError(
			run_id=input_data.run_id,
			reason_code=ReasonCode.LOW_DIVERSITY,
			message="Evidence lacks source diversity (need >=2 distinct sources)",
		)

	variables, var_types = _detect_variables([ev for _, ev in usable])

	hypothesis = _build_hypothesis(variables)

	# Vague check: ensure contains a comparative verb
	if not any(word in hypothesis for word in ["improve", "increase", "decrease", "reduce", "affect"]):
		return ExtractionError(
			run_id=input_data.run_id,
			reason_code=ReasonCode.TOO_VAGUE,
			message="Hypothesis not falsifiable",
		)

	methods = _choose_methods(var_types)
	if not methods:
		return ExtractionError(
			run_id=input_data.run_id,
			reason_code=ReasonCode.NO_TESTABLE_RELATION,
			message="No compatible statistical method for variable types",
		)

	assumptions = _assumptions_for_methods(methods)

	evidence_refs = [idx for idx, _ in usable][:5]
	if len(evidence_refs) < 2:
		evidence_refs = [0, 1]

	return ExtractionOutput(
		run_id=input_data.run_id,
		hypothesis=hypothesis,
		variables=variables,
		var_types=var_types,
		methods=methods,
		assumptions=assumptions,
		evidence_refs=evidence_refs[:5],
		notes=None,
	)


