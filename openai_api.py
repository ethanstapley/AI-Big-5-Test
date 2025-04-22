import os
import json
from openai import OpenAI
import re


api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not found. Please set it in your environment.")
client = OpenAI(api_key=api_key)


def extract_json_from_response(text):
    try:
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return None

def analyze_response_dynamic(question, user_response):
    prompt = f"""
        You are a personality psychologist using the Big Five model.

        A user responded to this Big Five statement:
        "{question}"
        The user may or may not give a scale of 1-5
        Their answer was:
        "{user_response}"

        IMPORTANT:
        If the user's answer is very short, vague, unclear, non-explanatory, or non-committal (e.g., "yes", "no", "maybe", "kinda", "sort of", "yeah", etc.), DO NOT interpret the answer. Instead, return a follow-up question asking the user to explain their reasoning, context, or personal experiences.

        Return ONLY ONE of the following:

        1. If the answer needs clarification:
        {{ "followup": "Ask a specific follow-up question here." }}

        2. If the answer is clear and comprehensive:
        {{ "score": 1–5, "insight": "A short, meaningful insight about the user's personality based on their response." }}

        Only return valid JSON. Do not explain the format. Do not include markdown, labels, or commentary. Respond only with the raw JSON object.
        """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )
    content = response.choices[0].message.content.strip()
    parsed = extract_json_from_response(content)
    if parsed:
        return parsed
    else:
        return {"score": 3, "insight": "Follow-up parse failed. Neutral score used."}

def finalize_with_followup(original_question, original_answer, followup_question, followup_answer):
    prompt = f"""
        A user responded to this Big Five question:
        "{original_question}"
        Their original answer: "{original_answer}"

        You followed up with:
        "{followup_question}"
        Their second answer: "{followup_answer}"

        Now combine both answers and provide:
        - A score (1–5)
        - A short personality insight

        Return JSON:
        {{ "score": 1–5, "insight": "A short, meaningful insight about the user's personality based on their response." }}

        Only return valid JSON. Do not explain the format. Do not include markdown, labels, or commentary. Respond only with the raw JSON object.
        """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )

    content = response.choices[0].message.content.strip()
    parsed = extract_json_from_response(content)
    if parsed:
        return parsed
    else:
        return {"score": 3, "insight": "Follow-up parse failed. Neutral score used."}
    

def generate_summary_report(user_results: dict, user_percentile: dict) -> str:
    prompt = f"""
    You are a personality psychologist writing a summary for a client who just completed a Big Five personality assessment.

    Here is the structured data from the user's answers:

    === USER RESPONSES ===
    {json.dumps(user_results, indent=2)}

    === TRAIT PERCENTILES ===
    {json.dumps(user_percentile, indent=2)}

    Your job is to write a 4–6 paragraph report explaining the user's personality.
    Be warm and thoughtful in tone, but still concise and factual.
    Make sure to connect their percentile score to their responses. The data should reflect their responses.

    
    Guidelines:
    - Start with a brief summary of the overall personality pattern.
    - Discuss each of the Big Five traits individually.
    - Highlight interesting insights you discovered in their answers.
    - Reflect on nuances (e.g., low trait scores with high introspection).
    - Do NOT include raw JSON or formatting — only return plain text.

    Provide only the report text. Do not include disclaimers or markdown.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


