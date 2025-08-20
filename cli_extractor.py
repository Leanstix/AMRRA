from __future__ import annotations

import json
import sys

from core.contracts import RetrievalOutput
from extractor import run_extraction


def main() -> int:
    data = sys.stdin.read()
    if not data.strip():
        print(json.dumps({"error": "No input"}))
        return 2
    try:
        payload = json.loads(data)
        retrieval = RetrievalOutput.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": f"Invalid input: {exc}"}))
        return 2

    result = run_extraction(retrieval)
    print(result.model_dump_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


