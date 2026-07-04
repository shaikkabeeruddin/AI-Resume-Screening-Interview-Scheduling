import json
import re
from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions
from json_repair import repair_json

from app.config import settings
from app.prompts import RESUME_PARSE_PROMPT, MATCH_PROMPT_TEMPLATE

client = genai.Client(
    api_key=settings.GEMINI_API_KEY,
    http_options=HttpOptions(api_version="v1"),
)

def extract_json_block(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    return text

def _safe_json_load(text: str) -> dict:
    cleaned = extract_json_block(text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        repaired = repair_json(cleaned)
        return json.loads(repaired)

def _call_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt,
        config=GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=2048,
        ),
    )
    return response.text or ""

def parse_resume_with_ai(resume_text: str) -> dict:
    prompt = f"""
{RESUME_PARSE_PROMPT}

IMPORTANT:
- Return ONLY valid JSON.
- Do not use markdown.
- Do not include explanation text.
- Ensure all strings are properly escaped.
- Arrays must be valid JSON arrays.

Resume Text:
{resume_text}
"""
    raw = _call_gemini(prompt)
    return _safe_json_load(raw)

def score_candidate_with_ai(candidate_data: dict, job_description: str) -> dict:
    candidate_json = json.dumps(candidate_data, ensure_ascii=False)

    prompt = MATCH_PROMPT_TEMPLATE.format(
        job_description=job_description,
        candidate_json=candidate_json
    ) + """

IMPORTANT:
- Return ONLY valid JSON.
- Do not wrap in markdown.
- Escape quotes properly.
- Match Score must be an integer.
"""

    raw = _call_gemini(prompt)
    return _safe_json_load(raw)