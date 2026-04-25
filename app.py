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
textarea {background:#111827;color:white;}
.stButton>button {background:#2563eb;color:white;}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")

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


col1, col2 = st.columns(2)

# ---------- LEFT ----------
with col1:
    st.subheader("🔍 Find Candidates")

    jd_file = st.file_uploader("Upload JD", ["pdf","docx","txt"])
    jd_text = st.text_area("Paste JD")

    if st.button("Find Candidates"):
        if jd_file:
            jd_text = read_file(jd_file)

        if not jd_text:
            st.warning("Provide JD")
        else:
            skills, exp, role = extract_requirements(jd_text)

            st.success(f"{role} | Exp: {exp[0]}–{exp[1]}")

            with open("candidates.json") as f:
                data = json.load(f)

            results = []

            for c in data:
                text = " ".join(c["skills"]) + f" {c['experience']} years"
                res = analyze(jd_text, text)
                results.append((c["name"], res["score"]))

            results.sort(key=lambda x: x[1], reverse=True)

            for name, score in results:
                st.write(f"{name} — {score}%")


# ---------- RIGHT ----------
with col2:
    st.subheader("🎯 Evaluate Candidate")

    resume_file = st.file_uploader("Upload Resume", ["pdf","docx","txt"])
    resume_text = st.text_area("Paste Resume")

    jd_file2 = st.file_uploader("Upload JD", ["pdf","docx","txt"])
    jd_text2 = st.text_area("Paste JD")

    if st.button("Evaluate Candidate"):

        if resume_file:
            resume_text = read_file(resume_file)

        if jd_file2:
            jd_text2 = read_file(jd_file2)

        if not resume_text or not jd_text2:
            st.warning("Provide JD + Resume")
        else:
            result = analyze(jd_text2, resume_text)

            st.success("Evaluation Complete")

            st.write(f"Score: {result['score']}%")
            st.write(f"Decision: {result['decision']}")

            st.write("Matched:", result["matched"])
            st.write("Missing:", result["missing"])
            st.write(result["reason"])
