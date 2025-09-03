import json
import re

class ExtractionUtils:
    # Regex to match integers or floats
    NUMERIC_REGEX = re.compile(r"[-+]?\d*\.\d+|\b\d+\b")

    @staticmethod
    def safe_parse_json(raw_text: str):
        if not raw_text:
            return None
        # Remove code block delimiters if present
        clean_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError as e:
            print("JSON parsing failed:", e)
            print("Raw text was:", clean_text[:500])
            return None

    @staticmethod
    def extract_numbers_from_text(text: str):
        # Remove citations like [45], [3], etc.
        text = re.sub(r"\[\d+\]", "", text)
        # Extract numbers
        nums = ExtractionUtils.NUMERIC_REGEX.findall(text)
        # Convert to float or int
        converted = [float(n) if '.' in n else int(n) for n in nums]
        # Filter out obviously irrelevant numbers (e.g., page numbers, huge numbers)
        filtered = [n for n in converted if 0 < n < 1000]
        return filtered

    @staticmethod
    def detect_test_type(numeric_map: dict) -> str:
        # Only include non-empty numeric arrays
        arrays = [v for v in numeric_map.values() if v]
        if not arrays:
            return "descriptive"  # fallback when no numeric data exists
        elif len(arrays) == 2 and all(len(v) > 1 for v in arrays):
            return "ttest"
        elif len(arrays) > 2 and all(len(v) > 1 for v in arrays):
            return "anova"
        elif any(len(v) == 1 for v in arrays):
            return "chi2"
        elif len(arrays) == 2:
            return "regression"
        else:
            return "descriptive"
