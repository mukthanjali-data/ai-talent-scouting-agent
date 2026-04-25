import streamlit as st
import json
from PyPDF2 import PdfReader
from brain import analyze_job_and_match, ai_extract_requirements, ai_assess_interest

st.set_page_config(layout="wide")

# -------- UI THEME -------- #
st.markdown("""
<style>

/* BACKGROUND */
.stApp {
    background: linear-gradient(to right, #0f172a, #1e293b);
}

/* TEXT */
h1, h2, h3, p {
    color: #f8fafc;
}

/* INPUT */
textarea, input {
    background-color: #111827 !important;
    color: #f9fafb !important;
    border-radius: 10px !important;
    border: 1px solid #374151 !important;
}

/* FILE UPLOADER */
[data-testid="stFileUploader"] {
    background-color: #111827;
    border-radius: 12px;
    padding: 15px;
    border: 1px solid #374151;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(to right, #2563eb, #3b82f6);
    color: white;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: 600;
}

/* CARD */
[data-testid="stFileUploader"], textarea {
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

/* EXPANDER */
[data-testid="stExpander"] {
    background-color: #111827;
    border-radius: 12px;
    border: 1px solid #374151;
}

</style>
""", unsafe_allow_html=True)

# -------- LOAD DATA -------- #
with open("candidates.json") as f:
    candidates = json.load(f)

# -------- SESSION -------- #
if "results" not in st.session_state:
    st.session_state.results = []

if "chat_step" not in st.session_state:
    st.session_state.chat_step = 0

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None

if "interest_scores" not in st.session_state:
    st.session_state.interest_scores = {}


# -------- FILE READ -------- #
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
st.markdown("""
<h1 style='font-size:40px;'>🤖 TalentAI Scout</h1>
<p style='color:#94a3b8;'>AI-powered intelligent hiring system</p>
""", unsafe_allow_html=True)

st.markdown("### 🚀 Intelligent AI Recruitment Agent")

st.info("JD → AI Parsing → Matching → Chat → Interest → Ranking")

uploaded = st.file_uploader("Upload JD", ["pdf", "txt"])
jd_input = st.text_area("Paste JD")

jd = read_file(uploaded) if uploaded else jd_input


# -------- FIND -------- #
if st.button("Find Candidates"):

    if not jd.strip():
        st.warning("Please provide a Job Description")
        st.stop()

    skills, exp, role = ai_extract_requirements(jd)

    st.success(f"🎯 Role: {role} | ⏳ Experience: {exp[0]}–{exp[1]} yrs")

    results = []

    for c in candidates:

        r = analyze_job_and_match(jd, c, skills, exp, role)

        # Base interest
        base_interest = min(70, 50 + c["experience"] * 2)

        interest = st.session_state.interest_scores.get(
            c["name"], base_interest
        )

        # Final scoring
        final = round(0.8 * r["match_score"] + 0.2 * interest, 2)

        # Strong differentiation
        if r["match_score"] >= 70:
            final += 3
        elif r["match_score"] < 50:
            final -= 3

        # Penalty
        if r["match_score"] < 50:
            final *= 0.9

        # Tie-breaker
        final += len(r["matched_skills"]) * 0.5

        results.append({
            "name": c["name"],
            "match": r["match_score"],
            "interest": interest,
            "final": round(final, 2),
            "reason": r["reason"],
            "skills": r["matched_skills"]
        })

    st.session_state.results = sorted(
        results, key=lambda x: x["final"], reverse=True
    )


# -------- DISPLAY -------- #
if st.session_state.results:

    top = st.session_state.results[0]

    st.success(
        f"🏆 Top Candidate: {top['name']} ({top['final']}%) — Best skill alignment and experience match"
    )

    for r in st.session_state.results:

        with st.expander(f"{r['name']} — {r['final']}%"):

            if r["match"] >= 70:
                st.success("Strong Fit")
            elif r["match"] >= 55:
                st.info("Good Fit")
            else:
                st.warning("Needs Improvement")

            st.write(r["reason"])

            st.metric("Match Score", f"{r['match']}%")
            st.metric("Interest Score", f"{r['interest']}%")

            st.write(f"🧠 Matched Skills: {r['skills']}")

            st.progress(r["match"] / 100)

            if st.button(f"💬 Engage {r['name']}", key=r["name"]):
                st.session_state.active_chat = r["name"]
                st.session_state.chat_step = 0
                st.session_state.interest_scores[r["name"]] = r["interest"]


# -------- CHAT -------- #
if st.session_state.active_chat:

    st.markdown("---")
    st.subheader(f"💬 Chat with {st.session_state.active_chat}")

    questions = [
        "Are you open to this role?",
        "Are you open to relocation?",
        "What is your expected salary?",
        "What is your notice period?"
    ]

    step = st.session_state.chat_step

    if step < len(questions):

        st.write(f"🤖 {questions[step]}")

        user_input = st.text_input(
            "Your answer",
            key=f"chat_input_{step}"
        )

        if st.button("Send"):

            if user_input.strip():

                delta = ai_assess_interest(user_input)
                name = st.session_state.active_chat

                st.session_state.interest_scores[name] += delta
                st.session_state.chat_step += 1

                st.rerun()

    else:
        st.success("✅ Chat Completed!")
        st.session_state.active_chat = None
