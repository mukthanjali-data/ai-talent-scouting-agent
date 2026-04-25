import streamlit as st
import json
import docx
from PyPDF2 import PdfReader
from brain import *

st.set_page_config(layout="wide")

# ---------- UI ----------
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")

# ---------- FILE READER ----------
def read_file(file):
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

    jd_file = st.file_uploader("Upload JD", ["pdf","docx","txt"], key="jd1")
    jd_text = st.text_area("Paste JD", key="jd_text1")

    jd = read_file(jd_file) if jd_file else jd_text

    if st.button("Find Candidates"):

        skills, exp, role = extract_requirements(jd)

        st.success(f"{role} | Exp: {exp[0]}–{exp[1]} yrs")

        with open("candidates.json") as f:
            data = json.load(f)

        for c in data:

            text = " ".join(c["skills"]) + f" {c['experience']} years"
            res = analyze(jd, text)

            with st.expander(f"{c['name']} — {res['match_score']}%"):

                st.write("Match Score:", res["match_score"])
                st.write("Matched:", res["matched"])
                st.write("Missing:", res["missing"])

                # CHAT
                ans = st.text_input(
                    f"💬 Ask {c['name']}: Are you interested?",
                    key=c["name"]
                )

                if ans:
                    i_score = interest_score(ans)
                    final = round(0.7*res["match_score"] + 0.3*i_score,2)

                    st.write("Interest Score:", i_score)
                    st.write("Final Score:", final)

# ---------- RIGHT ----------
with col2:
    st.subheader("🎯 Evaluate Candidate")

    resume_file = st.file_uploader("Upload Resume", ["pdf","docx","txt"], key="res1")
    resume_text = st.text_area("Paste Resume", key="res_text")

    resume = read_file(resume_file) if resume_file else resume_text

    if st.button("Evaluate Candidate"):

        res = analyze(jd, resume)

        st.success("Evaluation Complete")

        st.write("Match Score:", res["match_score"])
        st.write("Matched:", res["matched"])
        st.write("Missing:", res["missing"])
