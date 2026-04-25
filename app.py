import streamlit as st
import json
import docx
from PyPDF2 import PdfReader
from brain import analyze, extract_requirements, interest_score

st.set_page_config(layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
.stApp {background: linear-gradient(to right,#0f172a,#1e293b);}
h1,h2,h3,p,label {color:white;}
textarea {background:#111827;color:white;border-radius:10px;}
.stButton>button {
    background: linear-gradient(to right,#2563eb,#3b82f6);
    color:white;
    border-radius:10px;
    padding:10px;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")
st.markdown("JD → AI Parsing → Matching → Chat → Interest → Ranking")

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

# ---------- INPUT ----------
st.subheader("📄 Job Description")

jd_file = st.file_uploader("Upload JD", ["pdf","docx","txt"], key="jd")
jd_text = st.text_area("Paste JD", key="jd_text")

jd = read_file(jd_file) if jd_file else jd_text

# ---------- BUTTONS ----------
col1, col2 = st.columns(2)

find_btn = col1.button("🔍 Find Candidates")
eval_btn = col2.button("🎯 Evaluate Candidate")

# ---------- FIND CANDIDATES ----------
if find_btn:
    if not jd:
        st.warning("Please provide JD")
    else:
        skills, exp, role = extract_requirements(jd)

        st.success(f"🎯 Role: {role} | ⏳ Exp: {exp[0]}–{exp[1]} yrs")

        with open("candidates.json") as f:
            data = json.load(f)

        st.session_state["results"] = []

        for c in data:
            text = " ".join(c["skills"]) + f" {c['experience']} years"
            res = analyze(jd, text)

            st.session_state["results"].append({
                "name": c["name"],
                "res": res
            })

# ---------- DISPLAY RESULTS ----------
if "results" in st.session_state:

    for r in st.session_state["results"]:
        name = r["name"]
        res = r["res"]

        with st.expander(f"{name} — {res['match_score']}%"):

            st.write(f"🎯 Match Score: {res['match_score']}%")

            st.write("✅ Matched Skills:")
            st.markdown(", ".join(res["matched"]) if res["matched"] else "None")

            st.write("❌ Missing Skills:")
            st.markdown(", ".join(res["missing"]) if res["missing"] else "None")

            # ---------- CHAT ----------
            ans = st.text_input(
                f"💬 Ask {name}: Are you interested?",
                key=f"chat_{name}"
            )

            if ans:
                i_score = interest_score(ans)
                final = round(0.7 * res["match_score"] + 0.3 * i_score, 2)

                st.success(f"📊 Interest Score: {i_score}")
                st.success(f"🏆 Final Score: {final}")

# ---------- EVALUATE ----------
if eval_btn:

    st.subheader("🎯 Evaluate Candidate")

    resume_file = st.file_uploader("Upload Resume", ["pdf","docx","txt"], key="resume")
    resume_text = st.text_area("Paste Resume", key="resume_text")

    resume = read_file(resume_file) if resume_file else resume_text

    if resume and jd:
        result = analyze(jd, resume)

        st.success("Evaluation Complete")

        st.write(f"🎯 Match Score: {result['match_score']}%")

        st.write("✅ Matched Skills:")
        st.markdown(", ".join(result["matched"]) if result["matched"] else "None")

        st.write("❌ Missing Skills:")
        st.markdown(", ".join(result["missing"]) if result["missing"] else "None")

    else:
        st.warning("Provide both JD and Resume")
