import streamlit as st
import json
import pandas as pd
from PyPDF2 import PdfReader
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
.stButton>button {
    background: linear-gradient(to right,#3b82f6,#2563eb);
    color:white;
    border-radius:10px;
    padding:10px;
    font-weight:600;
}
[data-testid="stExpander"] {
    background:#111827;
    border-radius:12px;
    border:1px solid #374151;
}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- LOAD ----------
with open("candidates.json") as f:
    candidates = json.load(f)

# ---------- SIDEBAR ----------
st.sidebar.header("⚙️ Recruiter Settings")

match_weight = st.sidebar.slider("Match Weight", 0.5, 1.0, 0.8)
min_exp = st.sidebar.slider("Min Experience", 0, 10, 0)
max_exp = st.sidebar.slider("Max Experience", 0, 10, 10)
top_n = st.sidebar.slider("Top Candidates", 1, 10, 5)
threshold = st.sidebar.slider("Min Score %", 0, 100, 40)

# ---------- HEADER ----------
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")

st.info("JD → AI Parsing → Matching → Chat → Interest → Ranking")

# ---------- INPUT ----------
uploaded = st.file_uploader("Upload JD", ["pdf","txt"])
jd_text = st.text_area("Paste JD", height=180)

def read_pdf(file):
    if file:
        reader = PdfReader(file)
        return "".join([p.extract_text() or "" for p in reader.pages])
    return ""

jd = read_pdf(uploaded) if uploaded else jd_text

# ---------- FIND ----------
if st.button("🔍 Find Candidates"):

    if not jd.strip():
        st.warning("Please enter JD")
        st.stop()

    skills, exp, role = ai_extract_requirements(jd)

    st.success(f"🎯 Role: {role} | ⏳ Exp: {exp[0]}–{exp[1]} yrs")

    results = []

    for c in candidates:

        if not (min_exp <= c["experience"] <= max_exp):
            continue

        r = analyze_job_and_match(jd, c, skills, exp, role)

        interest = 50 + c["experience"] * 2

        final = round(match_weight*r["match_score"] + (1-match_weight)*interest,2)

        decision = "Recommended" if r["match_score"]>=70 else "Consider" if r["match_score"]>=55 else "Reject"

        results.append({
            "name":c["name"],
            "score":final,
            "decision":decision,
            "match":r["match_score"],
            "skills":r["matched_skills"],
            "missing":r["missing_skills"]
        })

    results = sorted(results,key=lambda x:x["score"],reverse=True)
    results = [r for r in results if r["score"]>=threshold][:top_n]

    if not results:
        st.warning("No candidates match filters")
        st.stop()

    st.success(f"🏆 Top Candidate: {results[0]['name']} ({results[0]['score']}%)")

    for r in results:
        with st.expander(f"{r['name']} — {r['score']}%"):
            st.write("🎯 Decision:",r["decision"])
            st.write("✅ Matched Skills:",r["skills"])
            st.write("❌ Missing Skills:",r["missing"][:3])

    df = pd.DataFrame(results)
    st.download_button("📥 Download CSV", df.to_csv(index=False), "results.csv")

# ---------- SINGLE EVALUATION ----------
st.markdown("---")
st.subheader("🔍 Evaluate Candidate")

profile = st.text_area("Paste LinkedIn / Resume")

resume_file = st.file_uploader("Upload Resume", ["pdf","txt"])

if st.button("Evaluate Candidate"):

    text = profile if profile else read_pdf(resume_file)

    if not text:
        st.warning("Provide profile or resume")
        st.stop()

    candidate = extract_candidate_profile(text)

    skills, exp, role = ai_extract_requirements(jd)

    r = analyze_job_and_match(jd,candidate,skills,exp,role)

    score = r["match_score"]

    decision = "Recommended" if score>=70 else "Consider" if score>=55 else "Reject"

    st.success("Evaluation Complete")

    st.write(f"🎯 Score: {score}%")
    st.write(f"📌 Decision: {decision}")
    st.write("✅ Matched Skills:",r["matched_skills"])
    st.write("❌ Missing Skills:",r["missing_skills"][:3])
