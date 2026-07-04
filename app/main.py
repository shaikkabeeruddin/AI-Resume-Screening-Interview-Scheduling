import os
import re
import json
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import ProcessResponse
from app.config import settings
from app.services.extractor import extract_resume_text
from app.services.llm import parse_resume_with_ai, score_candidate_with_ai
from app.services.nocodb import create_candidate_record

from datetime import datetime, timezone, timedelta

app = FastAPI(title="AI Resume Screening API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def clean_list(value):
    if not isinstance(value, list):
        return []
    cleaned = []
    seen = set()
    for item in value:
        item = str(item).strip()
        if item and item.lower() not in seen:
            cleaned.append(item)
            seen.add(item.lower())
    return cleaned


def valid_email(email: str) -> bool:
    if not email:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def valid_phone(phone: str) -> bool:
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 10



@app.get("/")
def home():
    return {"message": "Resume Screening API Running"}


@app.post("/process_resume", response_model=ProcessResponse)
async def process_resume(
    resume_file: UploadFile = File(...),
    email_subject: str = Form(""),
    sender_email: str = Form(""),
    received_at: str = Form("")
):
    ext = os.path.splitext(resume_file.filename)[1].lower()

    if ext not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed."
        )

    file_name = f"{uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(await resume_file.read())

    try:
        resume_text = extract_resume_text(file_path)

        if not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from resume."
            )

        parsed = parse_resume_with_ai(resume_text)

        parsed["Technical Skills"] = clean_list(parsed.get("Technical Skills", []))
        parsed["Soft Skills"] = clean_list(parsed.get("Soft Skills", []))
        parsed["Certifications"] = clean_list(parsed.get("Certifications", []))
        parsed["Languages"] = clean_list(parsed.get("Languages", []))
        parsed["Projects"] = clean_list(parsed.get("Projects", []))

        if not valid_email(parsed.get("Email", "")):
            parsed["Email"] = ""

        if not valid_phone(parsed.get("Phone", "")):
            parsed["Phone"] = ""

        match_result = score_candidate_with_ai(parsed, settings.JOB_DESCRIPTION)

        match_score = int(match_result.get("Match Score", 0))
        recommendation = str(match_result.get("Recommendation", "Review")).strip()

        if recommendation not in ["Shortlist", "Review", "Reject"]:
            if match_score >= 80:
                recommendation = "Shortlist"
            elif match_score >= 60:
                recommendation = "Review"
            else:
                recommendation = "Reject"


        IST = timezone(timedelta(hours=5, minutes=30))
        received_at_value = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

        nocodb_payload = {
            "Candidate Name": parsed.get("Candidate Name", ""),
            "Email": parsed.get("Email", ""),
            "Phone": parsed.get("Phone", ""),
            "Location": parsed.get("Location", ""),
            "Experience": parsed.get("Experience", ""),
            "Current Role": parsed.get("Current Role", ""),
            "Current Company": parsed.get("Current Company", ""),
            "Education": parsed.get("Education", ""),
            "Technical Skills": ", ".join(parsed.get("Technical Skills", [])),
            "Soft Skills": ", ".join(parsed.get("Soft Skills", [])),
            "Certifications": ", ".join(parsed.get("Certifications", [])),
            "Languages": ", ".join(parsed.get("Languages", [])),
            "Projects": ", ".join(parsed.get("Projects", [])),
            "Match Score": match_score,
            "Matching Skills": ", ".join(clean_list(match_result.get("Matching Skills", []))),
            "Missing Skills": ", ".join(clean_list(match_result.get("Missing Skills", []))),
            "AI Summary": parsed.get("AI Summary", ""),
            "Recommendation": recommendation,
            "Recruiter Notes": match_result.get("Recruiter Notes", ""),
            "Application Status": "New",
            "Email Subject": email_subject.strip(),
            "Sender Email": sender_email.strip() if valid_email(sender_email.strip()) else "",
            "Received At": received_at_value
        }

        nocodb_response = create_candidate_record(nocodb_payload)

        candidate_id = str(
            nocodb_response.get("Id")
            or nocodb_response.get("id")
            or nocodb_response.get("ID")
            or ""
        )

        return ProcessResponse(
            success=True,
            message="Resume processed successfully",
            candidate_id=candidate_id,
            match_score=match_score,
            recommendation=recommendation
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))