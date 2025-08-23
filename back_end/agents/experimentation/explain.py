#from openai import OpenAI
from settings import settings
import cohere

#client = OpenAI(api_key=settings.OPENAI_API_KEY)
cohere_client = cohere.Client(api_key=settings.COHERE_API_KEY)

def gpt5_explain_results(output: dict) -> str:
    """
    Send statistical results to GPT-5 and get a plain-English interpretation.
    """
    try:
        '''response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert statistics tutor. Explain results clearly and precisely."
                },
                {
                    "role": "user",
                    "content": f"Here are the test results:\n{output}\nExplain what they mean extensively, including interpretation of p-value, effect size, and confidence interval."
                }
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()'''
        
        response = cohere_client.chat(
            model="command-r-plus",  # Recommended Cohere chat model
            message=f"""
            You are an expert statistics tutor.
            Here are the test results:
            {output}

            Explain what they mean extensively, including interpretation of
            p-value, effect size, and confidence interval in simple language.
            """,
            temperature=0.7,
            max_tokens=500
        )
        return response.text.strip()
    except Exception as e:
        return f"⚠️ AI explanation failed: {str(e)}"

def explain_descriptive_tests(output: dict, alpha: float = 0.05) -> dict:
    """
    Explain descriptive test results and return a calibrated summary in a structured format.
    """
    try:
        response = cohere_client.chat(
            model="command-r-plus",
            message=f"""
            You are an expert statistics tutor.
            
            Here are the descriptive statistics results:
            {output}

            1. Identify the most appropriate statistical test name (e.g., "Linear regression", "Descriptive summary", etc.).
            2. Explain the results in simple terms for a non-technical audience.
            3. Do not invent numbers – only interpret what is given.
            4. Output ONLY the test name on the first line, then the explanation on the next line.
            """,
            temperature=0.4,
            max_tokens=400
        )

        gpt_text = response.text.strip().split("\n", 1)
        test_name = gpt_text[0].strip() if len(gpt_text) > 0 else "Descriptive Summary"
        explanation = gpt_text[1].strip() if len(gpt_text) > 1 else "Explanation not available."

        result = {
            "test_used": test_name,
            "p_value": float(output.get("p_value", 0.0)),
            "effect_size": float(output.get("effect_size", 0.0)),
            "confidence_interval": output.get("confidence_interval", []),
            "estimate": output.get("estimate", []),
            "df": output.get("df", []),
            "conclusion": "Significant" if output.get("p_value", 1.0) < alpha else "Not significant",
            "method_notes": output.get("method_notes", "Descriptive statistics"),
            "extra": explanation
        }

        return result

    except Exception as e:
        return {
            "error": f"⚠️ AI explanation failed: {str(e)}",
            "raw_output": output
        }
