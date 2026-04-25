import streamlit as st
import json
import docx
from PyPDF2 import PdfReader
from brain import analyze, extract_requirements

st.set_page_config(layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
.stApp {background: linear-gradient(to right,#0f172a,#1e293b);}
h1,h2,h3,p {color:white;}
textarea {background:#111827;color:white;border-radius:10px;}
.stButton>button {
    background:#2563eb;
    color:white;
    border-radius:10px;
    font-weight:600;
}
[data-testid="stFileUploader"] small {display:none;}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")
st.markdown("JD → AI Parsing → Matching → Ranking")

# ---------- FILE READER ----------
def read_file(file):
    if file is None:
        return ""

    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        return " ".join([p.extract_text() or "" for p in reader.pages])

    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return " ".join([p.text for p in doc.paragraphs])

    elif file.name.endswith(".txt"):
        return file.read().decode()

    return ""

# ---------- LAYOUT ----------
col1, col2 = st.columns(2)

# =========================================================
# 🔵 LEFT: FIND CANDIDATES (JD ONLY)
# =========================================================
with col1:
    st.subheader("🔍 Find Candidates")

    jd_file = st.file_uploader(
        "Upload JD", ["pdf","docx","txt"], key="jd_left"
    )
    jd_text = st.text_area("Paste JD", key="jd_text_left")

    jd = read_file(jd_file) if jd_file else jd_text

    if st.button("Find Candidates", key="find_btn"):

        if not jd.strip():
            st.warning("Please provide JD")
            st.stop()

        skills, exp, role = extract_requirements(jd)

        st.success(f"{role} | Exp: {exp[0]}–{exp[1]} yrs")

        with open("candidates.json") as f:
            data = json.load(f)

        results = []

        for c in data:
            text = " ".join(c["skills"]) + f" {c['experience']} years"
            res = analyze(jd, text)

            results.append({
                "name": c["name"],
                "score": res["score"]
            })

        results = sorted(results, key=lambda x: x["score"], reverse=True)

        for r in results:
            st.write(f"{r['name']} — {r['score']}%")

# =========================================================
# 🟢 RIGHT: EVALUATE CANDIDATE (RESUME ONLY)
# =========================================================
with col2:
    st.subheader("🎯 Evaluate Candidate")

    resume_file = st.file_uploader(
        "Upload Resume", ["pdf","docx","txt"], key="resume_upload"
    )
    resume_text = st.text_area("Paste Resume", key="resume_text")

    resume = read_file(resume_file) if resume_file else resume_text

    if st.button("Evaluate Candidate", key="eval_btn"):

        if not resume.strip():
            st.warning("Please provide Resume")
            st.stop()

        if not jd.strip():
            st.warning("Please provide JD on left side")
            st.stop()

        result = analyze(jd, resume)

        st.success("Evaluation Complete")

        st.write(f"🎯 Score: {result['score']}%")
        st.write(f"📌 Decision: {result['decision']}")

        st.write("✅ Matched Skills:", result["matched"])
        st.write("❌ Missing Skills:", result["missing"])
        st.write("🧠 Reason:", result["reason"])
