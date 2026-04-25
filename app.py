st.markdown("""
<style>
body {
    background-color: #0f172a;
}

h1, h2, h3 {
    color: #f8fafc;
}

.stApp {
    background: linear-gradient(to right, #0f172a, #1e293b);
    color: #e2e8f0;
}

.stButton>button {
    background-color: #3b82f6;
    color: white;
    border-radius: 8px;
    padding: 8px 16px;
}

.stMetric {
    background-color: #1e293b;
    padding: 10px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)
import streamlit as st
import json
from PyPDF2 import PdfReader
from brain import analyze_job_and_match, ai_extract_requirements, ai_assess_interest

st.set_page_config(layout="wide")

with open("candidates.json") as f:
    candidates = json.load(f)

# Session state
for k, v in {
    "results": [],
    "chat_step": 0,
    "active_chat": None,
    "interest_scores": {}
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


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


st.title("🤖 AI Talent Scouting Agent")

uploaded = st.file_uploader("📄 Upload JD (PDF/TXT)", ["pdf", "txt"])
jd_input = st.text_area("📋 Or paste JD")

jd = read_file(uploaded) if uploaded else jd_input


# ---------- FIND ---------- #
if st.button("Find Candidates"):

    if not jd.strip():
        st.warning("Provide JD")
        st.stop()

    skills, exp, role = ai_extract_requirements(jd)

    st.success(f"Role: {role} | Exp: {exp[0]}–{exp[1]} yrs | Skills: {', '.join(skills)}")

    results = []

    for c in candidates:
        r = analyze_job_and_match(jd, c, skills, exp, role)

        base_interest = min(70, 50 + c["experience"] * 2)
        interest = st.session_state.interest_scores.get(c["name"], base_interest)

        final = round(0.8 * r["match_score"] + 0.2 * interest, 2)

        if r["match_score"] < 50:
            final *= 0.9

        results.append({
            "name": c["name"],
            "match": r["match_score"],
            "interest": interest,
            "final": round(final, 2),
            "reason": r["reason"]
        })

    st.session_state.results = sorted(results, key=lambda x: x["final"], reverse=True)


# ---------- DISPLAY ---------- #
if st.session_state.results:

    for r in st.session_state.results:

        with st.expander(f"{r['name']} — {r['final']}%"):

            if r["match"] > 65:
                st.success("Strong Fit")
            elif r["match"] > 50:
                st.info("Good Fit")
            else:
                st.warning("Needs Improvement")

            st.write(r["reason"])

            st.metric("Match", f"{r['match']}%")
            st.metric("Interest", f"{r['interest']}%")

            if st.button(f"Engage {r['name']}", key=r["name"]):
                st.session_state.active_chat = r["name"]
                st.session_state.chat_step = 0
                st.session_state.interest_scores[r["name"]] = r["interest"]


# ---------- CHAT ---------- #
if st.session_state.active_chat:

    questions = [
        "Are you open to this role?",
        "Are you open to relocation?",
        "Expected salary?",
        "Notice period?"
    ]

    step = st.session_state.chat_step

    if step < len(questions):
        st.write(questions[step])
        ans = st.text_input("Answer", key=f"chat_{step}")

        if st.button("Send"):
            delta = ai_assess_interest(ans)
            name = st.session_state.active_chat

            st.session_state.interest_scores[name] += delta
            st.session_state.chat_step += 1
            st.rerun()

    else:
        st.success("Chat completed")
        st.session_state.active_chat = None
