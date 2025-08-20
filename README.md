# AMRRA
a reproducibility copilot for ML research. It ingests papers, extracts gaps, generates falsifiable hypotheses, auto-designs minimal experiments, executes them in a sandbox, evaluates results with statistical rigor, and outputs clean, shareable reports.

## Extractor Agent

- Run API: `uvicorn main_extractor:app --reload`
- Run CLI: `python cli_extractor.py < input.json`
- Run tests: `pytest -q`
