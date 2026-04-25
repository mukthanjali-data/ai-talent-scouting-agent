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


# Read uploaded file
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


# UI
st.title("🤖 AI Talent Scouting Agent")

st.markdown("""
### 🚀 AI Agent Workflow:
JD → AI Parsing → Hybrid Matching → Chat → Interest → Final Ranking
""")

uploaded = st.file_uploader("📄 Upload Job Description (PDF/TXT)", ["pdf", "txt"])
jd_input = st.text_area("📋 Or paste Job Description")

jd = read_file(uploaded) if uploaded else jd_input


# Find candidates
if st.button("Find Candidates"):

    if not jd.strip():
        st.warning("Please upload or paste a Job Description")
        st.stop()

    skills, exp, role = ai_extract_requirements(jd)

    st.success(f"🎯 Role: {role} | ⏳ Exp: {exp} yrs | 🧠 Skills: {', '.join(skills)}")

    results = []

    for c in candidates:
        r = analyze_job_and_match(jd, c, skills, exp, role)

        interest = st.session_state.interest_scores.get(c["name"], 50)
        final = round(0.7 * r["match_score"] + 0.3 * interest, 2)

        results.append({
            "name": c["name"],
            "exp": c["experience"],
            "match": r["match_score"],
            "interest": interest,
            "final": final,
            "reason": r["reason"]
        })

    st.session_state.results = sorted(results, key=lambda x: x["final"], reverse=True)

    st.success("✅ AI Agent completed analysis")


# Display results
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

            interest = st.session_state.interest_scores.get(r["name"], 50)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Match Score", f"{r['match']}%")

            with col2:
                st.metric("Interest Score", f"{interest}%")

            with col3:
                confidence = round((r["match"] + interest) / 2, 2)
                st.metric("Confidence", f"{confidence}%")

            st.progress(r["match"] / 100)

            st.markdown("### 📊 Why Ranked Here")
            st.write(
                f"Ranking based on match ({r['match']}%) and interest ({interest}%)."
            )

            st.info("📊 Final Score = 70% Match + 30% Interest")

            if st.button(f"💬 Engage {r['name']}", key=r["name"]):
                st.session_state.active_chat = r["name"]
                st.session_state.chat_step = 0
                st.session_state.interest_scores[r["name"]] = 50


# Chat section
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

        if st.button("Send"):
            if user_input:
                st.info("🤖 AI analyzing response...")

                delta = ai_assess_interest(user_input)

                st.session_state.interest_scores[st.session_state.active_chat] += delta
                st.session_state.chat_step += 1
                st.rerun()

    else:
        final_interest = st.session_state.interest_scores[st.session_state.active_chat]
        st.success(f"✅ Final Interest Score: {final_interest}%")

        updated = []

        for r in st.session_state.results:
            interest = st.session_state.interest_scores.get(r["name"], 50)
            final = round(0.7 * r["match"] + 0.3 * interest, 2)

            r["interest"] = interest
            r["final"] = final
            updated.append(r)

        st.session_state.results = sorted(updated, key=lambda x: x["final"], reverse=True)

        st.session_state.active_chat = None
        st.rerun()
