'''import openai
import os
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

async def generate_report_json(data: dict) -> dict:
    """Call GPT-5 to generate a structured statistical report in JSON."""
    prompt = f"""
    Generate a JSON-formatted statistical analysis summary from this data.
    Fields:
    - title: string
    - hypothesis: string
    - test_summary: string
    - effect_size: string
    - coefficients: list of objects with fields term, estimate, ci_95
    - interpretation: string
    - conclusion: string
    - confidence_score: float
    - notes: string

    Data:
    {json.dumps(data, indent=2)}
    """

    response = openai.ChatCompletion.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are a data-to-JSON report generator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message["content"]

    # Ensure output is valid JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: wrap content in a dict if GPT-5 didn't return perfect JSON
        return {"raw_text": content}
'''

import cohere
from settings import settings
import json

cohere_client = cohere.Client(settings.COHERE_API_KEY)

async def generate_report_json(data: dict) -> dict:
    """Call Cohere to generate a structured statistical report in JSON."""
    prompt = f"""
    Generate a JSON-formatted statistical analysis summary from this data also include references and citations and graphs if necessary.
    Make it professional and give an extensive conclusion as well.
    Fields:
    - title: string
    - hypothesis: string
    - test_summary: string
    - effect_size: string
    - coefficients: list of objects with fields term, estimate, ci_95
    - interpretation: string
    - conclusion: string
    - confidence_score: float
    - notes: string

    Data:
    {json.dumps(data, indent=2)}
    """

    try:
        response = cohere_client.chat(
            model="command-r-plus", 
            message=prompt,
            temperature=0,
            max_tokens=500
        )

        content = response.text.strip()

        # Try to parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_text": content}

    except Exception as e:
        return {"error": f"⚠️ Cohere report generation failed: {str(e)}"}