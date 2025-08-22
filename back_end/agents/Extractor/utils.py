import json, re

class ExtractionUtils:
    NUMERIC_REGEX = re.compile(r"[-+]?\d*\.\d+|\d+")

    @staticmethod
    def safe_parse_json(raw_text: str):
        if not raw_text:
            return None
        import re
        clean_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError as e:
            print("JSON parsing failed:", e)
            print("Raw text was:", clean_text[:500])
            return None

    @staticmethod
    def extract_numbers_from_text(text: str):
        nums = ExtractionUtils.NUMERIC_REGEX.findall(text)
        return [float(n) if '.' in n else int(n) for n in nums]

    @staticmethod
    def detect_test_type(numeric_map: dict) -> str:
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

