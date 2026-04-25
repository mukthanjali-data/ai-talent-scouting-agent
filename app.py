import streamlit as st
import json
from PyPDF2 import PdfReader
from brain import analyze_job_and_match, ai_extract_requirements, ai_assess_interest

st.set_page_config(layout="wide")

# -------- LOAD -------- #
with open("candidates.json") as f:
    candidates = json.load(f)

# -------- HELPERS -------- #
def read_file(file):
    if file is None:
        return ""
    if file.type == "application/pdf":
        reader = PdfReader(file)
        text = ""
        for p in reader.pages:
            text += p.extract_text() or ""
        return text
    return file.read().decode("utf-8")

# -------- HEADER -------- #
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")

st.markdown("### 🚀 Intelligent AI Recruitment Agent")
st.info("JD → AI Parsing → Matching → Chat → Interest → Ranking")

# -------- INPUT -------- #
uploaded = st.file_uploader("Upload JD", ["pdf", "txt"])
jd_input = st.text_area("Paste JD", height=180)
jd = read_file(uploaded) if uploaded else jd_input

linkedin = st.text_input("🔗 LinkedIn Profile (optional)")
resume = st.file_uploader("Upload Resume (optional)", ["pdf", "txt"])

# -------- PROCESS -------- #
if st.button("🔍 Find Candidates", use_container_width=True):

    if not jd.strip():
        st.warning("Enter JD")
        st.stop()

    skills, exp, role = ai_extract_requirements(jd)
    st.success(f"Role: {role} | Experience: {exp[0]}–{exp[1]} yrs")

    results = []

    for c in candidates:

        r = analyze_job_and_match(jd, c, skills, exp, role)

        interest = 60  # base stable

        final = round(0.8 * r["match_score"] + 0.2 * interest, 2)

        # differentiation
        if r["match_score"] >= 70:
            final += 3
        elif r["match_score"] < 50:
            final -= 3

        results.append({
            "name": c["name"],
            "match": r["match_score"],
            "final": final,
            "reason": r["reason"],
            "skills": r["matched_skills"],
            "missing": r["missing_skills"]
        })

    results = sorted(results, key=lambda x: x["final"], reverse=True)

    top = results[0]
    st.success(f"🏆 Top Candidate: {top['name']} ({top['final']}%)")

    # -------- DISPLAY -------- #
    for r in results:

        with st.expander(f"{r['name']} — {r['final']}%"):

            if r["match"] >= 70:
                decision = "Recommended"
                st.success("Strong Fit")
            elif r["match"] >= 55:
                decision = "Consider"
                st.info("Good Fit")
            else:
                decision = "Reject"
                st.warning("Needs Improvement")

            st.write("🧠 Recruiter Insight:")
            st.write(r["reason"])

            st.write("✅ Matched Skills:", r["skills"])
            st.write("❌ Missing Skills:", r["missing"][:3])

            st.write(f"🎯 Hiring Decision: {decision}")

            if linkedin:
                st.markdown(f"[🔗 View LinkedIn]({linkedin})")
