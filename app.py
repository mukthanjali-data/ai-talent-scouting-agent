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
h1,h2,h3,p {color:white;}
textarea,input {background:#111827;color:white;}
.stButton>button {background:#2563eb;color:white;border-radius:8px;}
.badge {background:#1e40af;color:white;padding:5px 10px;border-radius:10px;margin:3px;}
.badge-red {background:#7f1d1d;color:white;padding:5px 10px;border-radius:10px;margin:3px;}
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

# ---------- STATE ----------
if "results" not in st.session_state:
    st.session_state.results = None

if "chat_index" not in st.session_state:
    st.session_state.chat_index = 0

if "interest" not in st.session_state:
    st.session_state.interest = 50


# ---------- INPUT ----------
jd_file = st.file_uploader("Upload JD", ["pdf","docx","txt"], key="jd1")
jd_text = st.text_area("Paste JD")

resume_file = st.file_uploader("Upload Resume", ["pdf","docx","txt"], key="res1")
resume_text = st.text_area("Paste Resume")


# ---------- BUTTONS ----------
col1, col2 = st.columns(2)

with col1:
    find_btn = st.button("🔍 Find Candidates")

with col2:
    eval_btn = st.button("🎯 Evaluate Candidate")


# =====================================================
# FIND CANDIDATES
# =====================================================
if find_btn:

    if jd_file:
        jd_text = read_file(jd_file)

    if not jd_text:
        st.warning("Upload or paste JD")
    else:
        skills, exp, role = extract_requirements(jd_text)

        st.success(f"{role} | Exp: {exp[0]}–{exp[1]} yrs")

        with open("candidates.json") as f:
            data = json.load(f)

        results = []

        for c in data:
            text = " ".join(c["skills"])
            res = analyze(jd_text, text)

            results.append({
                "name": c["name"],
                "score": res["match_score"],
                "matched": res["matched"],
                "missing": res["missing"]
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        st.session_state.results = results


# ---------- SHOW RESULTS ----------
if st.session_state.results:

    for c in st.session_state.results:

        with st.expander(f"{c['name']} — {c['score']}%"):

            st.write("### Matched Skills")
            for s in c["matched"]:
                st.markdown(f'<span class="badge">{s}</span>', unsafe_allow_html=True)

            st.write("### Missing Skills")
            for s in c["missing"]:
                st.markdown(f'<span class="badge-red">{s}</span>', unsafe_allow_html=True)

            # CHAT
            questions = [
                "Are you open to this job?",
                "Are you okay with location?",
                "Expected salary?"
            ]

            if st.session_state.chat_index < len(questions):

                st.write("### 💬 Chat")

                q = questions[st.session_state.chat_index]
                st.write(q)

                ans = st.text_input("Your Answer", key=f"chat_{c['name']}_{st.session_state.chat_index}")

                if st.button("Send", key=f"send_{c['name']}"):

                    if ans:
                        score = interest_score(ans)
                        st.session_state.interest = score
                        st.session_state.chat_index += 1
                        st.rerun()


# =====================================================
# EVALUATE
# =====================================================
if eval_btn:

    if resume_file:
        resume_text = read_file(resume_file)

    if jd_file:
        jd_text = read_file(jd_file)

    if not resume_text or not jd_text:
        st.warning("Provide JD + Resume")
    else:
        result = analyze(jd_text, resume_text)

        st.success("Evaluation Complete")

        st.metric("Match Score", f"{result['match_score']}%")
        st.metric("Role", result["role"])

        st.write("### Matched Skills")
        for s in result["matched"]:
            st.markdown(f'<span class="badge">{s}</span>', unsafe_allow_html=True)

        st.write("### Missing Skills")
        for s in result["missing"]:
            st.markdown(f'<span class="badge-red">{s}</span>', unsafe_allow_html=True)

        ans = st.text_input("Interest Check")

        if st.button("Check Interest"):
            score = interest_score(ans)
            final = (0.7 * result["match_score"]) + (0.3 * score)

            st.metric("Interest", score)
            st.metric("Final Score", round(final,2))
