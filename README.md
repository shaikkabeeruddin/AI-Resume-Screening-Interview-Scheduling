# AI Resume Screening & Interview Scheduling

An end-to-end recruitment automation system that ingests resumes, extracts and evaluates candidate information with AI, stores structured records in NocoDB, enables recruiter review through a Streamlit dashboard, and automates interview scheduling for shortlisted candidates.

## Project overview

This project was built to satisfy the Task 3 assignment: monitor job applications, process PDF and DOCX resumes, parse candidate details with an LLM, compare candidates against a job description, store structured data, apply shortlisting logic, schedule interviews, and keep recruiters in control of the final decision.

The solution combines four parts:
- **n8n workflow** for email ingestion, orchestration, automation, notifications, and interview scheduling.
- **FastAPI backend** for resume processing, parsing, validation, scoring, and database integration.
- **NocoDB** as the candidate database and review layer.
- **Streamlit frontend** as the recruiter dashboard for resume upload, candidate review, filtering, status management, and manual actions.

## Repository structure

```text
ai-resume-screening/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── prompts.py
│   ├── schemas.py
│   └── services/
│       ├── extractor.py
│       ├── llm.py
│       └── nocodb.py
│
├── uploads/
├── .env
├── requirements.txt
└── README.md
```

## Architecture

### 1. n8n workflow

The n8n workflow acts as the automation backbone of the system. Its job is to monitor the recruitment inbox, accept incoming job application emails, detect supported attachments, pass resume files and metadata into the backend, receive the processed candidate result, write or update records in NocoDB, and trigger interview actions for shortlisted candidates.

The workflow covers these assignment steps:
- Monitor the recruitment inbox.
- Ignore emails without supported PDF or DOCX attachments.
- Capture sender name, sender email, email subject, and received timestamp.
- Send resume + metadata for processing.
- Receive structured AI output and match results.
- Store the candidate record in NocoDB.
- Apply shortlisting logic.
- Send interview email.
- Create a Google Calendar event.
- Update application status to `Interview Scheduled`.
- Handle errors and invalid cases gracefully.

### 2. FastAPI backend

The backend is responsible for all core business logic. It accepts the uploaded resume, extracts text, sends the extracted content to the LLM using carefully designed prompts, validates and normalizes the AI response, calculates or finalizes hiring evaluation fields, and stores the structured output in NocoDB.

The backend exposes the resume-processing API used by both n8n and the Streamlit application. This keeps the parsing and scoring logic centralized so the same processing pipeline is used whether the resume comes from email automation or manual upload.

### 3. NocoDB database

NocoDB stores the structured candidate record and acts as the source of truth for recruiter operations. The system stores the extracted profile, JD match analysis, recruiter notes, application status, metadata from the original email, and the original resume attachment as required by the assignment.

### 4. Streamlit recruiter dashboard

The frontend provides a recruiter-friendly review interface. Recruiters can upload resumes manually, inspect parsed candidate details, review AI-generated summaries and scores, filter candidates, and update the recruitment status without touching the automation layer directly.

## End-to-end workflow

### Automated flow from email

1. A candidate sends an application email to the recruitment inbox.
2. n8n detects the new email and checks for supported PDF or DOCX attachments.
3. Emails without supported attachments are ignored safely.
4. n8n captures sender name, sender email, email subject, and received timestamp.
5. The attachment and metadata are sent to the FastAPI backend.
6. The backend extracts text from the resume.
7. The backend sends the text and job description to the LLM.
8. The LLM returns structured candidate information and evaluation data.
9. The backend validates and normalizes the result.
10. The candidate record is created in NocoDB with default status `New`.
11. Shortlisting logic evaluates the match score.
12. Based on the score, the candidate is marked as `Shortlist`, `Review`, or `Reject` according to the documented rule set.
13. If shortlisted, the system sends an interview invitation email, creates a calendar event, and updates the candidate status to `Interview Scheduled`.
14. Recruiters can later review and override the final decision from the dashboard.

### Manual flow from dashboard

1. A recruiter opens the Streamlit dashboard.
2. The recruiter uploads a PDF or DOCX resume manually.
3. The frontend sends the file and metadata to the FastAPI backend.
4. The backend processes the resume through the same extraction and AI parsing pipeline.
5. The structured result is stored in NocoDB.
6. The candidate appears in the dashboard for review and status management.

## Backend details

### `app/main.py`

This is the FastAPI entry point. It defines the API endpoints, receives incoming requests from n8n or Streamlit, coordinates resume processing, and returns the final JSON response to the caller.

Typical responsibilities include:
- Accept multipart file uploads.
- Receive optional email metadata such as subject, sender email, and received timestamp.
- Call the extraction, LLM, validation, and NocoDB service layers.
- Return success or structured error responses.

### `app/config.py`

This file centralizes configuration and environment variables. It keeps secrets and deployment-specific values outside the application code, such as API keys, model names, backend URLs, NocoDB connection details, and email/calendar integration settings.

### `app/prompts.py`

This file stores the AI prompts used for:
- Resume parsing.
- Candidate evaluation against the job description.
- JSON output formatting.
- Missing-field handling and response standardization.

Keeping prompts in a dedicated module makes the AI layer easier to maintain, test, and improve.

### `app/schemas.py`

This file defines the request and response data models. It ensures the backend works with predictable structured payloads and helps validate the candidate record before saving it.

Typical schema coverage includes:
- Candidate profile fields.
- Match result fields.
- Validation-ready output shape.
- API response contracts.

### `app/services/extractor.py`

This service handles document text extraction from supported resume formats.

Expected responsibilities:
- Detect PDF and DOCX files.
- Extract raw text from each file.
- Return a clean string for downstream AI processing.
- Handle unsupported or corrupted files safely.

### `app/services/llm.py`

This service manages all LLM interactions. It sends the extracted resume text and job description to the AI model, receives structured output, and separates parsing from business logic.

Typical responsibilities include:
- Calling the selected LLM provider.
- Injecting parsing and scoring prompts.
- Forcing or encouraging valid JSON output.
- Returning parsed candidate data and evaluation results.

### `app/services/nocodb.py`

This service encapsulates all NocoDB API communication.

Typical responsibilities:
- Create candidate records.
- Update candidate status.
- Attach the original resume.
- Save recruiter notes and manual edits.
- Retrieve candidate records for dashboard display.

## AI processing features

The AI layer extracts structured fields required by the assignment, including candidate name, email, phone number, location, total experience, current role, current company, education, technical skills, soft skills, certifications, languages, projects, and LinkedIn profile when available.

It also performs job description matching and produces the required evaluation outputs: match score, matching skills, missing skills, relevant experience, potential concerns, AI summary, and hiring recommendation.

## Validation and data cleaning

The project includes a validation and normalization stage to make AI output production-safe. This stage is designed to satisfy the assignment’s data validation requirements.

Validation responsibilities include:
- Safe JSON parsing.
- Graceful handling of missing values.
- Deduplication of repeated skills.
- Standardization of date and experience formats.
- Email format validation.
- Phone number format validation.

## Candidate scoring and shortlisting logic

The project implements automated shortlisting based on match score. The default rule set follows the assignment guidance:

- **Match Score >= 80** → `Shortlist`
- **Match Score 60–79** → `Review`
- **Match Score < 60** → `Reject`

These values can be adjusted later if required, but the default implementation follows the suggested criteria from the assignment.

## NocoDB schema

The solution uses a candidate table containing the fields required by the assignment.

Required fields:
- Candidate Name
- Email
- Phone
- Location
- Current Role
- Current Company
- Experience
- Education
- Technical Skills
- Soft Skills
- Certifications
- Languages
- Projects
- Match Score
- Matching Skills
- Missing Skills
- AI Summary
- Recommendation
- Recruiter Notes
- Application Status
- Resume Attachment
- Email Subject
- Sender Email
- Received At

Suggested additional operational fields:
- Id
- LinkedIn Profile
- Relevant Experience
- Potential Concerns
- Interview Event ID
- Interview Scheduled At
- Last Updated At

## Frontend features

The Streamlit frontend is the recruiter-facing dashboard for operating the system after automation has created candidate records.

Key features:
- Manual resume upload.
- Candidate list view.
- Search by candidate name, email, or role.
- Filter by application status.
- Candidate detail panel.
- Display of AI summary, skills, match data, and recruiter notes.
- Manual status updates.
- Recruiter review actions such as shortlist, reject, review, and interview scheduling state transitions.
- Refresh and re-fetch candidate data from NocoDB.

## Recruiter review capabilities

The assignment requires recruiters to remain in control of the final hiring decision. The dashboard supports that operational model by allowing recruiters to:
- Review AI-generated candidate information.
- Inspect AI recommendation and score.
- Add recruiter notes.
- Change application status manually.
- Override workflow-driven decisions when needed.

## API endpoints

### `POST /process_resume`

Processes an uploaded resume and stores the parsed candidate record.

**Form fields:**
- `resume_file`: uploaded PDF or DOCX
- `email_subject`: optional
- `sender_email`: optional
- `received_at`: optional

**High-level behavior:**
- Extracts resume text.
- Sends extracted content to the AI model.
- Validates and normalizes output.
- Stores the result in NocoDB.
- Returns the structured candidate JSON.

Additional endpoints can be added later for health checks, manual updates, schema inspection, or direct candidate operations if needed.

## Setup instructions

### 1. Clone the project

```bash
git clone <your-repository-url>
cd ai-resume-screening
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

Add all required environment variables to a `.env` file.

Example:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_model_name
BACKEND_BASE_URL=http://127.0.0.1:8000
NOCODB_BASE_URL=https://app.nocodb.com
NOCODB_TABLE_ID=your_table_id
NOCODB_TOKEN=your_nocodb_token
GOOGLE_CALENDAR_ID=your_calendar_id
GOOGLE_CREDENTIALS_JSON=your_google_credentials_json_or_reference
RECRUITMENT_EMAIL=your_inbox_address
JOB_DESCRIPTION_PATH=./job_description.txt
UPLOAD_DIR=./uploads
```

Update the variable names to match the actual implementation in `config.py`.

### 4. Run the backend

```bash
uvicorn app.main:app --reload
```

### 5. Run the frontend

```bash
streamlit run frontend/app.py
```

### 6. Configure n8n

In n8n, configure the workflow with:
- Email trigger or inbox polling node.
- Attachment filtering logic.
- HTTP Request node calling the FastAPI backend.
- NocoDB update/create actions as needed.
- Email send node for interview invitation.
- Google Calendar node for interview scheduling.
- Error handling branches and logging.

## How n8n works in this project

The workflow is designed as an orchestration layer around the backend.

### Main stages

1. **Inbox monitoring**
   - Watches the recruitment mailbox for new job applications.

2. **Attachment validation**
   - Checks whether the email contains PDF or DOCX resumes.
   - Ignores unsupported emails safely.

3. **Metadata capture**
   - Extracts sender name, sender email, subject, and received time.

4. **Backend processing call**
   - Sends the resume file and metadata to the FastAPI `/process_resume` endpoint.

5. **Candidate persistence**
   - Uses the backend/NocoDB integration to create the final candidate record.

6. **Decision routing**
   - Reads the resulting score and recommendation.
   - Routes candidates into shortlist, review, or reject.

7. **Interview automation**
   - For shortlisted candidates, sends an interview invitation email.
   - Creates a Google Calendar event.
   - Updates status to `Interview Scheduled`.

8. **Failure handling**
   - Routes bad inputs, extraction failures, parsing issues, or scheduling failures into controlled error paths.

## How the backend works in this project

The backend follows a service-oriented flow:

1. Receive resume and metadata.
2. Save or buffer the uploaded file.
3. Detect file type and extract resume text.
4. Load the job description.
5. Send the resume text and job description to the LLM using the prompts module.
6. Parse the AI response.
7. Validate fields and normalize formats.
8. Apply or confirm match scoring and hiring recommendation.
9. Store the result in NocoDB.
10. Return a structured JSON response to the caller.

This separation makes the code easier to maintain, debug, and extend.

## Error handling

The project includes error handling across all layers because the assignment explicitly requires support for real-world edge cases and a demo of error handling.

Typical handled scenarios:
- Email without attachment.
- Unsupported file type.
- Empty or corrupted resume.
- Text extraction failure.
- Invalid AI JSON response.
- Missing candidate fields.
- NocoDB write failure.
- Email sending failure.
- Calendar event creation failure.
- Manual dashboard/API errors surfaced clearly to the user.

## Security and privacy considerations

The assignment evaluates security and privacy considerations, so the project documents the following operational practices:

- Secrets are stored in environment variables instead of hardcoded application logic.
- Candidate data is processed only for recruitment workflow purposes.
- Access to NocoDB, inbox credentials, and model APIs should be restricted.
- The `.env` file must never be committed to version control.
- Resume files in `uploads/` should be protected and cleaned according to retention policy.
- Logging should avoid exposing sensitive personal information unless operationally necessary.

## Assumptions made

- A job description is available and used consistently for candidate scoring.
- The LLM returns JSON in the required structure most of the time, with backend safeguards for invalid output.
- NocoDB is the primary candidate database.
- Google Calendar is used for interview scheduling, though Outlook could also satisfy the assignment.
- Recruiters may either use the automated email pipeline or the manual dashboard upload path.
- The shortlisting thresholds follow the assignment’s suggested score bands unless changed intentionally and documented.

## Mapping to assignment requirements

| Assignment requirement | Implementation in this project |
|---|---|
| Monitor recruitment inbox | Implemented through n8n email trigger/polling workflow. |
| Process PDF and DOCX resumes | Implemented in extraction service and workflow validation. |
| Capture email metadata | Sender, subject, and timestamp captured and stored. |
| AI parsing of resume | Implemented through LLM service and prompts. |
| Job description matching | Implemented through AI evaluation against JD. |
| Data validation | Implemented in schemas and post-processing logic. |
| Store candidate in NocoDB | Implemented through NocoDB service. |
| Default status = New | Applied at candidate creation stage. |
| Shortlisting logic | Implemented using score-based routing. |
| Interview scheduling | Implemented through email + Google Calendar automation. |
| Manual recruiter review | Implemented in Streamlit dashboard. |
| Recruiter notes and status updates | Implemented in dashboard and NocoDB update flow. |

## Deliverables included for submission

This project is designed to support all deliverables requested in the assignment.

Submission package should include:
1. Exported n8n workflow JSON.
2. Database schema from NocoDB.
3. AI prompts used for parsing and evaluation.
4. Sample resumes and sample job description used for testing.
5. This README with setup instructions, environment variables, workflow explanation, and assumptions.
6. A 5–10 minute screen recording showing ingestion, extraction, scoring, database creation, interview scheduling, and error handling.

## Demo checklist

Use this checklist when recording the submission video:

- Show the recruitment inbox trigger or sample email event.
- Show PDF and DOCX processing.
- Show AI extraction output.
- Show JD match score and recommendation.
- Show the created NocoDB candidate record.
- Show the Streamlit recruiter dashboard.
- Show status updates and recruiter review.
- Show interview invitation email.
- Show Google Calendar event creation.
- Show at least one error-handling path.

## Future improvements

Potential extensions aligned with the bonus section of the assignment include duplicate candidate detection, embedding-based semantic matching, AI-generated interview questions, candidate ranking views, recruiter approval gates before scheduling, retry mechanisms, and structured monitoring or test coverage.

## License

This project was built as part of a technical assignment submission.