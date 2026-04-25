import streamlit as st
import json
from PyPDF2 import PdfReader
from brain import analyze_job_and_match, ai_extract_requirements, ai_assess_interest

st.set_page_config(layout="wide")

# Load candidates
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

st.markdown("""
### 🚀 AI Agent Workflow:
JD → AI Parsing → Hybrid Matching → Chat → Interest → Final Ranking
""")

uploaded = st.file_uploader("📄 Upload Job Description (PDF/TXT)", ["pdf", "txt"])
jd_input = st.text_area("📋 Or paste Job Description")

jd = read_file(uploaded) if uploaded else jd_input


# ---------------- FIND CANDIDATES ---------------- #
if st.button("Find Candidates"):

    if not jd.strip():
        st.warning("Please upload or paste a Job Description")
        st.stop()

    skills, exp, role = ai_extract_requirements(jd)

    st.success(f"🎯 Role: {role} | ⏳ Exp: {exp} yrs | 🧠 Skills: {', '.join(skills)}")

    results = []

    for c in candidates:
        r = analyze_job_and_match(jd, c, skills, exp, role)

        # 🔥 Stable base interest (no randomness)
        base_interest = min(70, 50 + c["experience"] * 2)

        interest = st.session_state.interest_scores.get(c["name"], base_interest)

        # 🔥 FINAL FIX: skill dominance
        final = round(0.8 * r["match_score"] + 0.2 * interest, 2)

        if r["match_score"] < 50:
            final *= 0.9

        results.append({
            "name": c["name"],
            "exp": c["experience"],
            "match": r["match_score"],
            "interest": interest,
            "final": round(final, 2),
            "reason": r["reason"]
        })

    st.session_state.results = sorted(results, key=lambda x: x["final"], reverse=True)

    st.success("✅ AI Agent completed analysis")


# ---------------- DISPLAY ---------------- #
if st.session_state.results:
    st.subheader("📊 Ranked Candidates")

    for r in st.session_state.results:
        with st.expander(f"{r['name']} — {r['final']}%"):

            st.markdown("### 🤖 AI Decision Summary")
            decision = (
                "Highly Recommended" if r["final"] > 75 else
                "Good Fit" if r["final"] > 60 else
                "Moderate Fit"
            )
            st.success(decision)

            st.markdown("### 🧠 Recruiter Insight")
            st.write(r["reason"])

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Match Score", f"{r['match']}%")

            with col2:
                st.metric("Interest Score", f"{r['interest']}%")

            with col3:
                confidence = round((r["match"] + r["interest"]) / 2, 2)
                st.metric("Confidence", f"{confidence}%")

            st.progress(r["match"] / 100)

            st.info("📊 Final Score = 80% Match + 20% Interest")

            if st.button(f"💬 Engage {r['name']}", key=f"eng_{r['name']}"):
                st.session_state.active_chat = r["name"]
                st.session_state.chat_step = 0
                st.session_state.interest_scores[r["name"]] = r["interest"]


# ---------------- CHAT ---------------- #
if st.session_state.active_chat:
    st.subheader(f"💬 Chat with {st.session_state.active_chat}")

    questions = [
        "Are you open to new opportunities?",
        "Are you open to relocation?",
        "What is your expected salary?",
        "When can you join?"
    ]

    step = st.session_state.chat_step

    if step < len(questions):
        st.write(questions[step])

        user_input = st.text_input("Your answer", key=f"chat_{step}")

        if st.button("Send", key=f"send_{step}"):
            if user_input.strip():

                delta = ai_assess_interest(user_input)

                name = st.session_state.active_chat
                st.session_state.interest_scores[name] += delta
                st.session_state.interest_scores[name] = max(
                    0, min(100, st.session_state.interest_scores[name])
                )

                st.session_state.chat_step += 1
                st.rerun()

    else:
        name = st.session_state.active_chat
        final_interest = st.session_state.interest_scores[name]

        st.success(f"✅ Final Interest Score: {final_interest}%")

        updated = []

        for r in st.session_state.results:
            interest = st.session_state.interest_scores.get(r["name"], r["interest"])
            final = round(0.8 * r["match"] + 0.2 * interest, 2)

            if r["match"] < 50:
                final *= 0.9

            r["final"] = round(final, 2)
            updated.append(r)

        st.session_state.results = sorted(updated, key=lambda x: x["final"], reverse=True)

        st.session_state.active_chat = None
        st.rerun()
