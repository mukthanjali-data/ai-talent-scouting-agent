import streamlit as st
import json
import pandas as pd
from PyPDF2 import PdfReader
from brain import analyze_job_and_match, ai_extract_requirements, ai_assess_interest

st.set_page_config(layout="wide")

# ---------- LOAD ----------
with open("candidates.json") as f:
    candidates = json.load(f)

# ---------- SIDEBAR ----------
st.sidebar.header("⚙️ Recruiter Settings")

match_weight = st.sidebar.slider("Match Weight", 0.5, 1.0, 0.8)
interest_weight = 1 - match_weight

min_exp = st.sidebar.slider("Min Experience", 0, 10, 0)
max_exp = st.sidebar.slider("Max Experience", 0, 10, 10)

top_n = st.sidebar.slider("Top Candidates", 1, 10, 5)
threshold = st.sidebar.slider("Min Score %", 0, 100, 40)

strict_mode = st.sidebar.checkbox("Strict Skill Match")

# ---------- HELPERS ----------
def read_file(file):
    if file is None:
        return ""
    if file.type == "application/pdf":
        reader = PdfReader(file)
        return "".join([p.extract_text() or "" for p in reader.pages])
    return file.read().decode("utf-8")

# ---------- UI ----------
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")

st.markdown("### 🚀 Intelligent AI Recruitment Agent")
st.info("JD → AI Parsing → Matching → Chat → Interest → Ranking")

uploaded = st.file_uploader("Upload JD", ["pdf", "txt"])
jd_input = st.text_area("Paste JD", height=180)

jd = read_file(uploaded) if uploaded else jd_input

linkedin = st.text_input("🔗 LinkedIn Profile (optional)")

# ---------- MAIN ----------
if st.button("🔍 Find Candidates", use_container_width=True):

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

        if strict_mode and len(r["matched_skills"]) == 0:
            continue

        interest = 50 + c["experience"] * 2

        final = round(
            match_weight * r["match_score"] + interest_weight * interest, 2
        )

        if r["match_score"] >= 70:
            decision = "Recommended"
        elif r["match_score"] >= 55:
            decision = "Consider"
        else:
            decision = "Reject"

        results.append({
            "name": c["name"],
            "match": r["match_score"],
            "final": final,
            "skills": r["matched_skills"],
            "missing": r["missing_skills"],
            "decision": decision
        })

    results = sorted(results, key=lambda x: x["final"], reverse=True)
    results = [r for r in results if r["final"] >= threshold][:top_n]

    if not results:
        st.warning("No candidates match filters")
        st.stop()

    st.success(f"🏆 Top Candidate: {results[0]['name']} ({results[0]['final']}%)")

    for r in results:
        with st.expander(f"{r['name']} — {r['final']}%"):

            st.write(f"🎯 Hiring Decision: {r['decision']}")
            st.write("✅ Matched Skills:", r["skills"])
            st.write("❌ Missing Skills:", r["missing"][:3])

            if linkedin:
                st.markdown(f"[🔗 LinkedIn]({linkedin})")

    df = pd.DataFrame(results)
    st.download_button("📥 Download Results", df.to_csv(index=False), "results.csv")
