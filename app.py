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

/* Text area */
.stTextArea textarea {
    background:#111827 !important;
    color:white !important;
    border-radius:10px;
}

/* Button */
.stButton>button {
    background: linear-gradient(to right,#3b82f6,#2563eb);
    color:white;
    border-radius:10px;
    font-weight:600;
}

/* Upload box */
[data-testid="stFileUploader"] {
    background:#111827;
    border-radius:10px;
    padding:10px;
    border:1px solid #374151;
}

/* Hide file type text */
[data-testid="stFileUploader"] small {
    display: none !important;
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

st.info("JD → AI Parsing → Matching → Ranking")

# ---------- LAYOUT ----------
col1, col2 = st.columns(2)

# =========================================================
# 🔵 LEFT: FIND CANDIDATES (JD)
# =========================================================
with col1:
    st.subheader("🔍 Find Candidates")

    jd_file = st.file_uploader("Upload JD", ["pdf","docx"])
    jd_text = st.text_area("Paste JD")

    jd = read_file(jd_file) if jd_file else jd_text

    if st.button("Find Candidates"):

        if not jd.strip():
            st.warning("Please enter JD")
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
                st.write("Matched Skills:",r["matched"])
                st.write("Missing Skills:",r["missing"][:3])


# =========================================================
# 🟢 RIGHT: EVALUATE CANDIDATE (RESUME ONLY)
# =========================================================
with col2:
    st.subheader("🎯 Evaluate Candidate")

    resume_file = st.file_uploader("Upload Resume", ["pdf","docx"])
    resume_text = st.text_area("Paste Resume")

    resume = read_file(resume_file) if resume_file else resume_text

    if st.button("Evaluate Candidate"):

        if not resume.strip():
            st.warning("Please provide resume")
            st.stop()

        candidate = extract_candidate_profile(resume)

        # 🔥 Use JD from LEFT side (same role)
        if not jd.strip():
            st.warning("Please enter JD in left section first")
            st.stop()

        skills, exp, role = ai_extract_requirements(jd)

        r = analyze_job_and_match(jd, candidate, skills, exp, role)

        score = r["match_score"]

        decision = "Recommended" if score>=70 else "Consider" if score>=55 else "Reject"

        st.success("Evaluation Complete")

        st.write(f"Score: {score}%")
        st.write(f"Decision: {decision}")
        st.write("Matched Skills:",r["matched_skills"])
        st.write("Missing Skills:",r["missing_skills"][:3])
