#from openai import OpenAI
from back_end.settings import settings
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
