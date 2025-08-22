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