import streamlit as st
import json
import pandas as pd
from PyPDF2 import PdfReader
from brain import analyze_job_and_match, ai_extract_requirements, ai_assess_interest

st.set_page_config(layout="wide")

# ---------- THEME (LIGHT + DARK) ----------
st.markdown("""
<style>
.stApp { font-family: 'Segoe UI', sans-serif; }

/* LIGHT MODE */
@media (prefers-color-scheme: light) {
    .stApp { background: #f8fafc; }
    h1,h2,h3,p,label { color:#0f172a !important; }
    textarea,input {
        background:#ffffff !important;
        color:#0f172a !important;
        border:1px solid #cbd5e1 !important;
        border-radius:10px !important;
    }
}

/* DARK MODE */
@media (prefers-color-scheme: dark) {
    .stApp { background: linear-gradient(to right,#0f172a,#1e293b); }
    h1,h2,h3,p,label { color:#f8fafc !important; }
    textarea,input {
        background:#111827 !important;
        color:#f9fafb !important;
        border:1px solid #374151 !important;
        border-radius:10px !important;
    }
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(to right,#2563eb,#3b82f6);
    color:white;
    border-radius:10px;
    padding:12px;
    font-weight:600;
    width:100%;
}

/* SHADOW */
textarea { box-shadow:0 4px 12px rgba(0,0,0,0.15); }

/* HIDE FOOTER */
footer { visibility:hidden; }

</style>
""", unsafe_allow_html=True)

# ---------- LOAD DATA ----------
with open("candidates.json") as f:
    candidates = json.load(f)

# ---------- SESSION ----------
if "interest_scores" not in st.session_state:
    st.session_state.interest_scores = {}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "chat_step" not in st.session_state:
    st.session_state.chat_step = 0

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

# ---------- HEADER ----------
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")

st.markdown("### 🚀 Intelligent AI Recruitment Agent")
st.info("JD → AI Parsing → Matching → Chat → Interest → Ranking")

# ---------- INPUT ----------
uploaded = st.file_uploader("Upload JD", ["pdf", "txt"])
jd_input = st.text_area("Paste JD", height=180)
jd = read_file(uploaded) if uploaded else jd_input

linkedin = st.text_input("🔗 LinkedIn Profile (optional)")
resume = st.file_uploader("Upload Resume (optional)", ["pdf", "txt"])

# ---------- FIND ----------
if st.button("🔍 Find Candidates"):

    if not jd.strip():
        st.warning("Please enter Job Description")
        st.stop()

    skills, exp, role = ai_extract_requirements(jd)

    st.success(f"🎯 Role: {role} | ⏳ Experience: {exp[0]}–{exp[1]} yrs")

    results = []

    for c in candidates:

        # experience filter
        if not (min_exp <= c["experience"] <= max_exp):
            continue

        r = analyze_job_and_match(jd, c, skills, exp, role)

        # strict skill filter
        if strict_mode and len(r["matched_skills"]) == 0:
            continue

        # base interest
        interest = st.session_state.interest_scores.get(
            c["name"], 50 + c["experience"] * 2
        )

        # scoring
        final = round(
            match_weight * r["match_score"] + interest_weight * interest, 2
        )

        # decision
        if r["match_score"] >= 70:
            decision = "Recommended"
        elif r["match_score"] >= 55:
            decision = "Consider"
        else:
            decision = "Reject"

        results.append({
            "name": c["name"],
            "match": r["match_score"],
            "interest": interest,
            "final": final,
            "skills": r["matched_skills"],
            "missing": r["missing_skills"],
            "decision": decision
        })

    # sort + filter
    results = sorted(results, key=lambda x: x["final"], reverse=True)
    results = [r for r in results if r["final"] >= threshold][:top_n]

    if not results:
        st.warning("No candidates match filters")
        st.stop()

    st.success(f"🏆 Top Candidate: {results[0]['name']} ({results[0]['final']}%)")

    # ---------- DISPLAY ----------
    for r in results:
        with st.expander(f"{r['name']} — {r['final']}%"):

            st.write(f"🎯 Decision: {r['decision']}")
            st.write("🧠 Matched Skills:", r["skills"])
            st.write("❌ Missing Skills:", r["missing"][:3])

            if linkedin:
                st.markdown(f"[🔗 View LinkedIn]({linkedin})")

            if st.button(f"💬 Engage {r['name']}", key=r["name"]):
                st.session_state.active_chat = r["name"]
                st.session_state.chat_step = 0
                st.session_state.interest_scores[r["name"]] = r["interest"]

    # ---------- DOWNLOAD ----------
    df = pd.DataFrame(results)
    st.download_button("📥 Download Results", df.to_csv(index=False), "results.csv")

# ---------- CHAT ----------
if st.session_state.active_chat:

    st.markdown("---")
    st.subheader(f"💬 Chat with {st.session_state.active_chat}")

    questions = [
        "Are you open to this role?",
        "Are you open to relocation?",
        "Expected salary?",
        "Notice period?"
    ]

    step = st.session_state.chat_step

    if step < len(questions):

        st.write(questions[step])

        ans = st.text_input("Your answer", key=f"chat_{step}")

        if st.button("Send"):
            if ans.strip():
                delta = ai_assess_interest(ans)
                name = st.session_state.active_chat

                st.session_state.interest_scores[name] += delta
                st.session_state.chat_step += 1

                st.rerun()

    else:
        st.success("✅ Chat completed")
        st.session_state.active_chat = None
