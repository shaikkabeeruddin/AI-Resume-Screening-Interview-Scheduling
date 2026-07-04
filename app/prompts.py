RESUME_PARSE_PROMPT = """
You are an AI resume parser.

Extract candidate details from the resume text and return ONLY one valid JSON object.
Do not return markdown.
Do not return explanation text.
Do not add comments.
Do not add trailing commas.

Return this exact JSON structure:
{
  "Candidate Name": "",
  "Email": "",
  "Phone": "",
  "Location": "",
  "Experience": "",
  "Current Role": "",
  "Current Company": "",
  "Education": "",
  "Technical Skills": [],
  "Soft Skills": [],
  "Certifications": [],
  "Languages": [],
  "Projects": [],
  "AI Summary": ""
}

Rules:
- Use empty string for missing text values.
- Use empty arrays for missing list values.
- "Technical Skills", "Soft Skills", "Certifications", "Languages", and "Projects" must always be arrays.
- "Phone" must be a plain string.
- "Experience" should be a short readable string like "2 years", "3.5 years", or "Fresher".
- "AI Summary" should be a short 2-3 sentence summary of the candidate profile based only on the resume.
- Return exactly one JSON object.
"""

MATCH_PROMPT_TEMPLATE = """
You are an AI recruitment evaluator.

Given the job description and candidate profile, evaluate the match and return ONLY one valid JSON object.

Job Description:
{job_description}

Candidate Profile JSON:
{candidate_json}

Return this exact JSON structure:
{{
  "Match Score": 0,
  "Matching Skills": [],
  "Missing Skills": [],
  "Recommendation": "",
  "Recruiter Notes": ""
}}

Rules:
- "Match Score" must be an integer from 0 to 100.
- "Matching Skills" and "Missing Skills" must always be arrays.
- "Recommendation" must be exactly one of: "Shortlist", "Review", "Reject".
- "Recruiter Notes" should be a short optional note for recruiter review, otherwise use empty string.
- Do not return markdown.
- Do not return explanation text.
- Do not return extra keys.
- Return exactly one JSON object.
"""