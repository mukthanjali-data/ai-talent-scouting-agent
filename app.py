import streamlit as st
import json
import pandas as pd
from PyPDF2 import PdfReader
from brain import *

st.set_page_config(layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#0f172a,#1e293b);}
h1,h2,h3,p,label {color:#f8fafc !important;}
.stButton>button {
    background: linear-gradient(to right,#3b82f6,#2563eb);
    color:white;border-radius:10px;padding:10px;font-weight:600;
}
[data-testid="stExpander"] {
    background:#111827;border-radius:12px;border:1px solid #374151;
}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- LOAD ----------
with open("candidates.json") as f:
    candidates = json.load(f)

# ---------- HELPERS ----------
def read_pdf(file):
    if file:
        reader = PdfReader(file)
        return "".join([p.extract_text() or "" for p in reader.pages])
    return ""

# ---------- HEADER ----------
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")

st.info("JD → AI Parsing → Matching → Chat → Interest → Ranking")

# ---------- LAYOUT ----------
col1, col2 = st.columns(2)

# =========================================================
# 🔍 LEFT SIDE → FIND CANDIDATES
# =========================================================
with col1:
    st.subheader("🔍 Find Candidates")

    jd_file_left = st.file_uploader("Upload JD", ["pdf","txt"], key="jd_left")
    jd_text_left = st.text_area("Paste JD", key="jd_text_left")

    jd_left = read_pdf(jd_file_left) if jd_file_left else jd_text_left

    if st.button("Find Candidates"):

        if not jd_left.strip():
            st.warning("Enter JD")
            st.stop()

        skills, exp, role = ai_extract_requirements(jd_left)

        st.success(f"Role: {role} | Exp: {exp[0]}–{exp[1]} yrs")

        results = []

        for c in candidates:

            r = analyze_job_and_match(jd_left, c, skills, exp, role)

            interest = 50 + c["experience"] * 2
            final = round(0.8*r["match_score"] + 0.2*interest,2)

            decision = "Recommended" if r["match_score"]>=70 else "Consider" if r["match_score"]>=55 else "Reject"

            results.append({
                "name":c["name"],
                "score":final,
                "decision":decision,
                "skills":r["matched_skills"],
                "missing":r["missing_skills"]
            })

        results = sorted(results,key=lambda x:x["score"],reverse=True)

        for r in results:
            with st.expander(f"{r['name']} — {r['score']}%"):
                st.write("Decision:",r["decision"])
                st.write("Matched:",r["skills"])
                st.write("Missing:",r["missing"][:3])


# =========================================================
# 🎯 RIGHT SIDE → EVALUATE SINGLE CANDIDATE
# =========================================================
with col2:
    st.subheader("🎯 Evaluate Candidate")

    jd_file_right = st.file_uploader("Upload JD", ["pdf","txt"], key="jd_right")
    jd_text_right = st.text_area("Paste JD", key="jd_text_right")

    resume_file = st.file_uploader("Upload Resume", ["pdf","txt"])
    linkedin_text = st.text_area("Paste LinkedIn/Profile")

    jd_right = read_pdf(jd_file_right) if jd_file_right else jd_text_right

    if st.button("Evaluate Candidate"):

        if not jd_right.strip():
            st.warning("Enter JD")
            st.stop()

        profile_text = linkedin_text if linkedin_text else read_pdf(resume_file)

        if not profile_text:
            st.warning("Provide Resume or LinkedIn text")
            st.stop()

        candidate = extract_candidate_profile(profile_text)

        skills, exp, role = ai_extract_requirements(jd_right)

        r = analyze_job_and_match(jd_right, candidate, skills, exp, role)

        score = r["match_score"]

        decision = "Recommended" if score>=70 else "Consider" if score>=55 else "Reject"

        st.success("Evaluation Complete")

        st.write(f"Score: {score}%")
        st.write(f"Decision: {decision}")
        st.write("Matched:",r["matched_skills"])
        st.write("Missing:",r["missing_skills"][:3])
