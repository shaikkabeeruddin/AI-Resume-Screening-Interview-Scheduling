import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Hiring Dashboard",
    page_icon="📋",
    layout="wide"
)

# =========================
# CONFIG
# =========================
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
PROCESS_RESUME_URL = f"{BACKEND_BASE_URL}/process_resume"

NOCODB_BASE_URL = os.getenv("NOCODB_BASE_URL", "https://app.nocodb.com")
TABLE_ID = os.getenv("NOCODB_TABLE_ID", "mly06c09yfevvaj")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN", "nc_pat_T1bbbeJBqRYeJkELpU3GxJTPX7vrNJAEqltHXvnm")

API_URL = f"{NOCODB_BASE_URL}/api/v2/tables/{TABLE_ID}/records"
HEADERS = {
    "xc-token": NOCODB_TOKEN,
    "Content-Type": "application/json"
}

STATUS_OPTIONS = [
    "All",
    "New",
    "Review",
    "Shortlist",
    "Reject",
    "Interview Scheduled"
]

ACTION_STATUSES = [
    "New",
    "Review",
    "Shortlist",
    "Reject",
    "Interview Scheduled"
]

# =========================
# HELPERS
# =========================
def api_get_candidates():
    response = requests.get(API_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict):
        if "list" in data:
            return data["list"]
        if "data" in data:
            return data["data"]
    if isinstance(data, list):
        return data

    return []

def api_update_status(record_id, new_status):
    payload = {
        "Id": int(record_id),
        "Application Status": new_status
    }
    response = requests.patch(API_URL, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()

def api_process_resume(uploaded_file, email_subject="", sender_email="", received_at=""):
    files = {
        "resume_file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type if uploaded_file.type else "application/pdf"
        )
    }

    data = {
        "email_subject": email_subject,
        "sender_email": sender_email,
        "received_at": received_at,
    }

    response = requests.post(
        PROCESS_RESUME_URL,
        data=data,
        files=files,
        timeout=180
    )
    response.raise_for_status()
    return response.json()

def safe_get(row, *keys):
    for key in keys:
        if key in row and row[key] not in [None, ""]:
            return row[key]
    return ""

def normalize_records(records):
    normalized = []
    for row in records:
        normalized.append({
            "Id": safe_get(row, "Id", "id"),
            "Name": safe_get(row, "Candidate Name", "Name", "Full Name"),
            "Email": safe_get(row, "Email", "email"),
            "Phone": safe_get(row, "Phone", "phone"),
            "Role": safe_get(row, "Current Role", "Role", "Position", "Job Role", "Applied Role"),
            "Application Status": safe_get(row, "Application Status", "Status"),
            "Recommendation": safe_get(row, "Recommendation", "AI Recommendation"),
            "Score": safe_get(row, "Match Score", "Score", "ATS Score"),
            "Summary": safe_get(row, "AI Summary", "Summary", "Candidate Summary", "Resume Summary"),
            "Skills": safe_get(row, "Technical Skills", "Skills", "Top Skills"),
            "Experience": safe_get(row, "Experience", "Years of Experience"),
            "Created At": safe_get(row, "Received At", "Created At", "created_at", "CreatedAt"),
            "Location": safe_get(row, "Location"),
            "Current Company": safe_get(row, "Current Company"),
            "Education": safe_get(row, "Education"),
            "Soft Skills": safe_get(row, "Soft Skills"),
            "Certifications": safe_get(row, "Certifications"),
            "Languages": safe_get(row, "Languages"),
            "Projects": safe_get(row, "Projects"),
            "Matching Skills": safe_get(row, "Matching Skills"),
            "Missing Skills": safe_get(row, "Missing Skills"),
            "Recruiter Notes": safe_get(row, "Recruiter Notes"),
            "Email Subject": safe_get(row, "Email Subject"),
            "Sender Email": safe_get(row, "Sender Email"),
        })
    return normalized

def build_dataframe(records):
    df = pd.DataFrame(records)
    if df.empty:
        return df

    expected_cols = [
        "Id", "Name", "Email", "Phone", "Role",
        "Application Status", "Recommendation", "Score",
        "Experience", "Created At", "Summary", "Skills"
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    return df[expected_cols]

def filter_dataframe(df, status_filter, search_text):
    filtered_df = df.copy()

    if status_filter != "All":
        filtered_df = filtered_df[
            filtered_df["Application Status"].fillna("").str.lower() == status_filter.lower()
        ]

    if search_text.strip():
        q = search_text.strip().lower()
        filtered_df = filtered_df[
            filtered_df["Name"].fillna("").str.lower().str.contains(q) |
            filtered_df["Email"].fillna("").str.lower().str.contains(q) |
            filtered_df["Role"].fillna("").str.lower().str.contains(q)
        ]

    return filtered_df

def metric_count(df, status_name):
    return int(
        df["Application Status"].fillna("").str.lower().eq(status_name.lower()).sum()
    )

# =========================
# SESSION STATE
# =========================
if "selected_candidate_id" not in st.session_state:
    st.session_state.selected_candidate_id = None

if "refresh_counter" not in st.session_state:
    st.session_state.refresh_counter = 0

# =========================
# STYLES
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
.metric-card {
    background: #ffffff;
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
}
.metric-title {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
}
.section-card {
    background: #ffffff;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid #e5e7eb;
    margin-bottom: 18px;
}
.sidebar-title {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("## 📋 Hiring Dashboard")
    st.caption("Navigation")
    page = st.radio(
        "Go to",
        ["Upload Resume", "Dashboard"],
        label_visibility="collapsed"
    )

    st.write("")
    if st.button("🔄 Refresh Data", width="stretch"):
        st.session_state.refresh_counter += 1
        st.rerun()

# =========================
# UPLOAD PAGE
# =========================
if page == "Upload Resume":
    st.title("Upload Resume")
    st.caption("Upload resumes to FastAPI and push processed candidate data into NocoDB.")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)

    with st.form("resume_upload_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            email_subject = st.text_input("Email Subject", placeholder="Application for AI Engineer")
            sender_email = st.text_input("Sender Email", placeholder="candidate@example.com")

        with col2:
            received_at = st.text_input(
                "Received At",
                value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                help="Optional; backend currently overwrites with server IST time, but we can still send it."
            )
            uploaded_resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

        upload_submit = st.form_submit_button("Process Resume", width="stretch")

        if upload_submit:
            if uploaded_resume is None:
                st.error("Please upload a resume file.")
            else:
                try:
                    with st.spinner("Processing resume..."):
                        result = api_process_resume(
                            uploaded_file=uploaded_resume,
                            email_subject=email_subject.strip(),
                            sender_email=sender_email.strip(),
                            received_at=received_at.strip(),
                        )
                    st.success("Resume processed successfully.")
                    st.json(result)
                except requests.exceptions.HTTPError as e:
                    try:
                        error_json = e.response.json()
                        st.error(f"Backend error: {error_json}")
                    except Exception:
                        st.error(f"Backend error: {e.response.text}")
                except Exception as e:
                    st.error(f"Failed to process resume: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# DASHBOARD PAGE
# =========================
elif page == "Dashboard":
    st.title("Candidate Dashboard")
    st.caption("Review, filter, and update candidate application statuses.")

    try:
        raw_records = api_get_candidates()
        records = normalize_records(raw_records)
        full_df = pd.DataFrame(records)
        df = build_dataframe(records)
    except Exception as e:
        st.error(f"Failed to load candidates from NocoDB: {e}")
        st.stop()

    total_candidates = len(df)
    review_count = metric_count(df, "Review")
    shortlist_count = metric_count(df, "Shortlist")
    reject_count = metric_count(df, "Reject")
    interview_count = metric_count(df, "Interview Scheduled")

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Candidates</div>
            <div class="metric-value">{total_candidates}</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Under Review</div>
            <div class="metric-value">{review_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Shortlisted</div>
            <div class="metric-value">{shortlist_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Rejected</div>
            <div class="metric-value">{reject_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with k5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Interviews</div>
            <div class="metric-value">{interview_count}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    left, right = st.columns([1.6, 1])

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Candidates")

        f1, f2 = st.columns([1, 1.3])
        with f1:
            status_filter = st.selectbox("Filter by status", STATUS_OPTIONS, index=0)
        with f2:
            search_text = st.text_input("Search by name, email, or role", placeholder="Search candidates...")

        filtered_df = filter_dataframe(df, status_filter, search_text)

        if filtered_df.empty:
            st.info("No candidates found for the current filter.")
        else:
            display_df = filtered_df[[
                "Id", "Name", "Email", "Role",
                "Application Status", "Recommendation", "Score"
            ]].copy()

            st.dataframe(display_df, width="stretch", hide_index=True)

            st.markdown("### Select candidate")
            candidate_options = {
                f"{row['Name'] or 'Unknown'} | {row['Email'] or 'No Email'} | {row['Application Status'] or 'No Status'}": row["Id"]
                for _, row in filtered_df.iterrows()
            }

            selected_label = st.selectbox(
                "Choose a candidate to view details",
                options=list(candidate_options.keys())
            )

            if selected_label:
                st.session_state.selected_candidate_id = candidate_options[selected_label]

        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Candidate details")

        if st.session_state.selected_candidate_id is None:
            st.info("Select a candidate from the list to see details.")
        else:
            selected_rows = full_df[full_df["Id"].astype(str) == str(st.session_state.selected_candidate_id)]

            if selected_rows.empty:
                st.warning("Selected candidate was not found.")
            else:
                row = selected_rows.iloc[0]

                st.markdown(f"**Name:** {row.get('Name', '—') or '—'}")
                st.markdown(f"**Email:** {row.get('Email', '—') or '—'}")
                st.markdown(f"**Phone:** {row.get('Phone', '—') or '—'}")
                st.markdown(f"**Role:** {row.get('Role', '—') or '—'}")
                st.markdown(f"**Current Company:** {row.get('Current Company', '—') or '—'}")
                st.markdown(f"**Location:** {row.get('Location', '—') or '—'}")
                st.markdown(f"**Status:** {row.get('Application Status', '—') or '—'}")
                st.markdown(f"**Recommendation:** {row.get('Recommendation', '—') or '—'}")
                st.markdown(f"**Score:** {row.get('Score', '—') or '—'}")
                st.markdown(f"**Experience:** {row.get('Experience', '—') or '—'}")
                st.markdown(f"**Education:** {row.get('Education', '—') or '—'}")
                st.markdown(f"**Created At:** {row.get('Created At', '—') or '—'}")

                st.write("")
                st.markdown("**AI Summary**")
                st.write(row.get("Summary", "") or "No summary available.")

                st.write("")
                st.markdown("**Technical Skills**")
                st.write(row.get("Skills", "") or "No skills data available.")

                st.write("")
                st.markdown("**Soft Skills**")
                st.write(row.get("Soft Skills", "") or "No soft skills data available.")

                st.write("")
                st.markdown("**Matching Skills**")
                st.write(row.get("Matching Skills", "") or "No matching skills data available.")

                st.write("")
                st.markdown("**Missing Skills**")
                st.write(row.get("Missing Skills", "") or "No missing skills data available.")

                st.write("")
                st.markdown("**Projects**")
                st.write(row.get("Projects", "") or "No project data available.")

                st.write("")
                st.markdown("**Recruiter Notes**")
                st.write(row.get("Recruiter Notes", "") or "No recruiter notes available.")

                st.write("")
                st.markdown("### Update status")

                current_status = row["Application Status"] if row["Application Status"] in ACTION_STATUSES else "New"

                with st.form("update_status_form"):
                    new_status = st.selectbox(
                        "New status",
                        ACTION_STATUSES,
                        index=ACTION_STATUSES.index(current_status)
                    )
                    submitted = st.form_submit_button("Update Status", width="stretch")

                    if submitted:
                        try:
                            api_update_status(row["Id"], new_status)
                            st.success(f"Status updated to '{new_status}' successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update status: {e}")

                st.write("")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Shortlist", width="stretch"):
                        try:
                            api_update_status(row["Id"], "Shortlist")
                            st.success("Candidate shortlisted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Shortlist failed: {e}")

                with c2:
                    if st.button("❌ Reject", width="stretch"):
                        try:
                            api_update_status(row["Id"], "Reject")
                            st.success("Candidate rejected.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Reject failed: {e}")

                c3, c4 = st.columns(2)
                with c3:
                    if st.button("📝 Mark Review", width="stretch"):
                        try:
                            api_update_status(row["Id"], "Review")
                            st.success("Candidate moved to review.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Review update failed: {e}")

                with c4:
                    if st.button("📅 Interview", width="stretch"):
                        try:
                            api_update_status(row["Id"], "Interview Scheduled")
                            st.success("Candidate marked for interview.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Interview update failed: {e}")

        st.markdown('</div>', unsafe_allow_html=True)