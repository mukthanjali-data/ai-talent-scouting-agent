import streamlit as st
import json
from PyPDF2 import PdfReader
import docx
from brain import *

st.set_page_config(layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#0f172a,#1e293b);
}

h1,h2,h3,p,label {
    color:#f8fafc !important;
}

.stTextArea textarea {
    background:#111827 !important;
    color:white !important;
    border-radius:10px;
}

.stButton>button {
    background: linear-gradient(to right,#3b82f6,#2563eb);
    color:white;
    border-radius:10px;
    font-weight:600;
}

[data-testid="stFileUploader"] {
    background:#111827;
    border-radius:10px;
    padding:10px;
    border:1px solid #374151;
}

[data-testid="stExpander"] {
    background:#111827;
    border-radius:10px;
    border:1px solid #374151;
}

</style>
""", unsafe_allow_html=True)

# ---------- FILE READER ----------
def read_file(file):
    if file is None:
        return ""

    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        return "".join([p.extract_text() or "" for p in reader.pages])

    elif file.name.endswith(".txt"):
        return file.read().decode("utf-8")

    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    return ""

# ---------- LOAD DATA ----------
with open("candidates.json") as f:
    candidates = json.load(f)

# ---------- HEADER ----------
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")

st.info("JD → AI Parsing → Matching → Chat → Interest → Ranking")

# ---------- LAYOUT ----------
col1, col2 = st.columns(2)

# =========================================================
# LEFT: FIND CANDIDATES
# =========================================================
with col1:
    st.subheader("🔍 Find Candidates")

    jd_file = st.file_uploader("Upload JD", ["pdf","txt","docx"])
    jd_text = st.text_area("Paste JD")

    jd = read_file(jd_file) if jd_file else jd_text

    if st.button("Find Candidates"):

        if not jd.strip():
            st.warning("Enter JD")
            st.stop()

        skills, exp, role = ai_extract_requirements(jd)

        st.success(f"Role: {role} | Exp: {exp[0]}–{exp[1]} yrs")

        results = []

        for c in candidates:
            r = analyze_job_and_match(jd, c, skills, exp, role)

            score = r["match_score"]
            decision = "Recommended" if score>=70 else "Consider" if score>=55 else "Reject"

            results.append({
                "name":c["name"],
                "score":score,
                "decision":decision,
                "matched":r["matched_skills"],
                "missing":r["missing_skills"]
            })

        results = sorted(results,key=lambda x:x["score"],reverse=True)

        for r in results:
            with st.expander(f"{r['name']} — {r['score']}%"):
                st.write("Decision:",r["decision"])
                st.write("Matched:",r["matched"])
                st.write("Missing:",r["missing"][:3])

# =========================================================
# RIGHT: EVALUATE SINGLE CANDIDATE
# =========================================================
with col2:
    st.subheader("🎯 Evaluate Candidate")

    jd_file2 = st.file_uploader("Upload JD", ["pdf","txt","docx"], key="jd2")
    jd_text2 = st.text_area("Paste JD", key="jd_text2")

    resume_file = st.file_uploader("Upload Resume", ["pdf","txt","docx"])
    linkedin_text = st.text_area("Paste LinkedIn/Profile")

    jd2 = read_file(jd_file2) if jd_file2 else jd_text2

    if st.button("Evaluate Candidate"):

        if not jd2.strip():
            st.warning("Enter JD")
            st.stop()

        profile = linkedin_text if linkedin_text else read_file(resume_file)

        if not profile:
            st.warning("Provide Resume or LinkedIn")
            st.stop()

        candidate = extract_candidate_profile(profile)

        skills, exp, role = ai_extract_requirements(jd2)

        r = analyze_job_and_match(jd2, candidate, skills, exp, role)

        score = r["match_score"]

        decision = "Recommended" if score>=70 else "Consider" if score>=55 else "Reject"

        st.success("Evaluation Complete")

        st.write(f"Score: {score}%")
        st.write(f"Decision: {decision}")
        st.write("Matched:",r["matched_skills"])
        st.write("Missing:",r["missing_skills"][:3])
