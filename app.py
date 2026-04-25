import streamlit as st
import json
import docx
from PyPDF2 import PdfReader
from brain import analyze, analyze_candidate, extract_requirements, interest_score, ai_assess_interest

st.set_page_config(page_title="TalentAI Scout", layout="wide", page_icon="🤖")

# ─────────────────────────────────────────
# CSS — Dark Theme
# ─────────────────────────────────────────
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
h1,h2,h3,h4,p,label,.stMarkdown { color: white !important; }
.stTextArea textarea { background: #111827 !important; color: white !important; border-radius: 10px !important; border: 1px solid #334155 !important; }
.stTextInput input { background: #111827 !important; color: white !important; border-radius: 8px !important; border: 1px solid #334155 !important; }
.stButton > button {
    background: linear-gradient(to right, #2563eb, #3b82f6) !important;
    color: white !important; border-radius: 10px !important;
    padding: 10px 20px !important; font-weight: 600 !important;
    border: none !important; width: 100%;
}
.stButton > button:hover { background: linear-gradient(to right, #1d4ed8, #2563eb) !important; }
.stExpander { background: #1e293b !important; border: 1px solid #334155 !important; border-radius: 12px !important; }
.stMetric { background: #1e293b !important; border-radius: 10px !important; padding: 8px !important; border: 1px solid #334155; }
.stProgress > div > div { background: linear-gradient(to right, #2563eb, #3b82f6) !important; }
.badge {
    display: inline-block; background: #1e40af; color: #bfdbfe;
    border-radius: 20px; padding: 3px 12px; font-size: 12px;
    margin: 2px; font-weight: 500;
}
.badge-missing { background: #7f1d1d; color: #fecaca; }
.badge-neutral { background: #1e3a5f; color: #93c5fd; }
.chat-ai {
    background: #1e3a5f; border-radius: 12px 12px 12px 0;
    padding: 10px 16px; margin: 6px 0; max-width: 75%;
    color: #e2e8f0; font-size: 14px;
}
.chat-user {
    background: #14532d; border-radius: 12px 12px 0 12px;
    padding: 10px 16px; margin: 6px 0; max-width: 75%;
    margin-left: auto; color: #dcfce7; font-size: 14px; text-align: right;
}
.verdict-box {
    border-radius: 12px; padding: 16px 20px;
    font-size: 16px; font-weight: 600; margin-top: 12px;
}
.score-bar-bg {
    background: #334155; border-radius: 8px; height: 10px; margin: 4px 0;
}
.jd-parsed {
    background: #0f2744; border-left: 4px solid #3b82f6;
    border-radius: 8px; padding: 12px 16px; margin: 10px 0; color: #bfdbfe;
}
div[data-testid="stFileUploader"] label { color: white !important; }
div[data-testid="stFileUploader"] { border: 1px dashed #334155 !important; border-radius: 10px !important; padding: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# Session State
# ─────────────────────────────────────────
for k, v in {
    "results": None, "jd_cache": "", "req_skills": None,
    "req_exp": None, "req_role": None,
    "chat_step": {}, "chat_history": {}, "interest_scores": {}
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────
# File Reader
# ─────────────────────────────────────────
def read_file(file):
    if file is None:
        return ""
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        return " ".join([p.extract_text() or "" for p in reader.pages])
    elif file.name.endswith(".docx"):
        d = docx.Document(file)
        return " ".join([p.text for p in d.paragraphs])
    elif file.name.endswith(".txt"):
        return file.read().decode()
    return ""

# ─────────────────────────────────────────
# Header
# ─────────────────────────────────────────
st.markdown("# 🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")
st.markdown(
    '<p style="color:#94a3b8; font-size:14px;">📄 JD → 🧠 AI Parsing → 🎯 Matching → 💬 Chat → 📊 Interest → 🏆 Ranking</p>',
    unsafe_allow_html=True
)
st.markdown("---")

# ─────────────────────────────────────────
# Tab Layout
# ─────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 Find & Rank Candidates", "🎯 Evaluate Single Candidate"])

# ══════════════════════════════════════════
# TAB 1 — Find Candidates
# ══════════════════════════════════════════
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📄 Job Description")
        jd_file = st.file_uploader("Upload JD (PDF / DOCX / TXT)", ["pdf", "docx", "txt"], key="jd_upload")
        jd_text = st.text_area("Or paste JD here", height=180, key="jd_paste",
                               placeholder="e.g. Looking for a Data Analyst with 3+ years in Python, SQL, Power BI...")
        jd = read_file(jd_file) if jd_file else jd_text

    with col2:
        st.subheader("⚙️ Settings")
        top_n    = st.slider("Top N candidates", 3, 20, 10)
        min_score = st.slider("Min Match Score (%)", 0, 70, 0)
        st.markdown('<p style="color:#64748b; font-size:13px;">💡 Upload a PDF/DOCX JD or paste it directly</p>', unsafe_allow_html=True)

    if st.button("🔍 Find & Rank Candidates", key="find_btn"):
        if not jd.strip():
            st.warning("⚠️ Please provide a Job Description first!")
        else:
            with st.spinner("🧠 AI parsing JD and scoring candidates..."):
                req_skills, req_exp, req_role = extract_requirements(jd)

                st.session_state.req_skills = req_skills
                st.session_state.req_exp    = req_exp
                st.session_state.req_role   = req_role
                st.session_state.jd_cache   = jd

                st.markdown(
                    f'<div class="jd-parsed">✅ <b>JD Parsed</b> — '
                    f'Role: <b>{req_role}</b> | '
                    f'Exp: <b>{req_exp[0]}–{req_exp[1]} yrs</b> | '
                    f'Skills: <b>{", ".join(req_skills)}</b></div>',
                    unsafe_allow_html=True
                )

                with open("candidates.json") as f:
                    candidates = json.load(f)

                results = []
                prog = st.progress(0)
                for i, c in enumerate(candidates):
                    res = analyze_candidate(jd, c, req_skills, req_exp, req_role)
                    interest = st.session_state.interest_scores.get(c["name"], 50)
                    final    = round(0.65 * res["match_score"] + 0.35 * interest, 2)
                    results.append({
                        "name":          c["name"],
                        "experience":    c["experience"],
                        "location":      c.get("location", "N/A"),
                        "notice_period": c.get("notice_period", "N/A"),
                        "expected_ctc":  c.get("expected_ctc", "N/A"),
                        "match_score":   res["match_score"],
                        "interest_score":interest,
                        "final_score":   final,
                        "matched":       res["matched"],
                        "missing":       res["missing"],
                        "note":          res["recruiter_note"]
                    })
                    prog.progress((i + 1) / len(candidates))

                st.session_state.results = sorted(results, key=lambda x: x["final_score"], reverse=True)
                prog.empty()

            st.success(f"✅ Ranked {len(results)} candidates!")

    # ── Results ──
    if st.session_state.results:
        filtered = [r for r in st.session_state.results if r["match_score"] >= min_score][:top_n]

        st.markdown("---")
        st.subheader(f"🏆 Ranked Shortlist ({len(filtered)} shown)")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Analyzed", len(st.session_state.results))
        m2.metric("Top Match",      f"{filtered[0]['match_score']}%" if filtered else "N/A")
        avg = round(sum(r["match_score"] for r in filtered) / len(filtered), 1) if filtered else 0
        m3.metric("Avg Match",      f"{avg}%")
        m4.metric(">70% Match",     sum(1 for r in filtered if r["match_score"] > 70))

        st.markdown("")

        for rank, r in enumerate(filtered, 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"

            with st.expander(f"{medal} {r['name']}  |  Final: {r['final_score']}%  |  Match: {r['match_score']}%  |  Interest: {r['interest_score']}%"):
                c1, c2, c3 = st.columns(3)
                c1.metric("🎯 Match Score",    f"{r['match_score']}%")
                c2.metric("💡 Interest Score", f"{r['interest_score']}%")
                c3.metric("🏆 Final Score",    f"{r['final_score']}%")

                st.markdown(f"**🧠 Recruiter Insight:** {r['note']}")
                st.markdown(
                    f"📅 **Exp:** {r['experience']} yrs &nbsp;|&nbsp; "
                    f"📍 **Location:** {r['location']} &nbsp;|&nbsp; "
                    f"⏱ **Notice:** {r['notice_period']} &nbsp;|&nbsp; "
                    f"💰 **CTC:** {r['expected_ctc']}",
                    unsafe_allow_html=True
                )

                sc1, sc2 = st.columns(2)
                with sc1:
                    st.markdown("**✅ Matched Skills:**")
                    b = " ".join([f'<span class="badge">{s}</span>' for s in r["matched"]])
                    st.markdown(b or "<span class='badge-neutral'>None</span>", unsafe_allow_html=True)
                with sc2:
                    st.markdown("**❌ Missing Skills:**")
                    b = " ".join([f'<span class="badge badge-missing">{s}</span>' for s in r["missing"]])
                    st.markdown(b or "🎉 All matched!", unsafe_allow_html=True)

                # ── Chat Section ──
                st.markdown("---")
                st.markdown(f"**💬 Engage {r['name']}**")

                name = r["name"]
                if name not in st.session_state.chat_step:
                    st.session_state.chat_step[name]    = 0
                if name not in st.session_state.chat_history:
                    st.session_state.chat_history[name] = []
                if name not in st.session_state.interest_scores:
                    st.session_state.interest_scores[name] = 50

                questions = [
                    "Are you currently open to exploring new opportunities?",
                    "Would you be open to relocating for this role?",
                    "What is your current CTC and expected package?",
                    "What is your notice period / earliest joining date?",
                    "What excites you most about this kind of role?"
                ]

                # Show history
                for msg in st.session_state.chat_history[name]:
                    css = "chat-ai" if msg["role"] == "ai" else "chat-user"
                    lbl = "🤖 Recruiter" if msg["role"] == "ai" else f"👤 {name}"
                    st.markdown(f'<div class="{css}"><b>{lbl}:</b> {msg["text"]}</div>', unsafe_allow_html=True)

                step = st.session_state.chat_step[name]
                if step < len(questions):
                    q = questions[step]
                    st.markdown(f'<div class="chat-ai">🤖 <b>Recruiter:</b> {q}</div>', unsafe_allow_html=True)
                    ans = st.text_input("Response:", key=f"ans_{name}_{step}", placeholder="Type response...")
                    if st.button("Send ➤", key=f"send_{name}_{step}") and ans.strip():
                        result = ai_assess_interest(name, q, ans, st.session_state.chat_history[name])
                        delta  = result.get("interest_delta", 0)
                        followup = result.get("ai_followup", "Thank you!")
                        new_score = max(0, min(100, st.session_state.interest_scores[name] + delta))
                        st.session_state.interest_scores[name] = new_score
                        st.session_state.chat_history[name].append({"role": "ai",   "text": q})
                        st.session_state.chat_history[name].append({"role": "user", "text": ans})
                        st.session_state.chat_history[name].append({"role": "ai",   "text": followup})
                        st.session_state.chat_step[name] += 1
                        # Update result scores
                        for res in st.session_state.results:
                            if res["name"] == name:
                                res["interest_score"] = new_score
                                res["final_score"]    = round(0.65 * res["match_score"] + 0.35 * new_score, 2)
                                break
                        st.rerun()
                else:
                    score = st.session_state.interest_scores[name]
                    if score >= 75:
                        vt, bg, bd = "🔥 Highly Interested — Fast-track!", "#052e16", "#16a34a"
                    elif score >= 50:
                        vt, bg, bd = "✅ Moderately Interested — Follow up", "#1c1917", "#d97706"
                    else:
                        vt, bg, bd = "❌ Low Interest — Consider others",   "#1f1215", "#dc2626"
                    st.markdown(
                        f'<div class="verdict-box" style="background:{bg};border-left:5px solid {bd};">'
                        f'Interest Score: <b>{score}%</b> — {vt}</div>',
                        unsafe_allow_html=True
                    )

# ══════════════════════════════════════════
# TAB 2 — Evaluate Single Candidate
# ══════════════════════════════════════════
with tab2:
    st.subheader("🎯 Evaluate a Single Candidate / Resume")

    ecol1, ecol2 = st.columns(2)
    with ecol1:
        st.markdown("**📄 Job Description**")
        jd2_file = st.file_uploader("Upload JD", ["pdf","docx","txt"], key="jd2_upload")
        jd2_text = st.text_area("Or paste JD", height=160, key="jd2_paste",
                                placeholder="Paste job description here...")
        jd2 = read_file(jd2_file) if jd2_file else jd2_text

    with ecol2:
        st.markdown("**📋 Candidate Resume**")
        res_file = st.file_uploader("Upload Resume", ["pdf","docx","txt"], key="res_upload")
        res_text = st.text_area("Or paste Resume", height=160, key="res_paste",
                                placeholder="Paste resume / candidate profile here...")
        resume = read_file(res_file) if res_file else res_text

    if st.button("🎯 Evaluate Now", key="eval_btn"):
        if not jd2.strip() or not resume.strip():
            st.warning("⚠️ Please provide both JD and Resume!")
        else:
            with st.spinner("🧠 AI evaluating candidate..."):
                result = analyze(jd2, resume)

            st.success("✅ Evaluation Complete!")

            e1, e2 = st.columns(2)
            e1.metric("🎯 Match Score", f"{result['match_score']}%")
            e2.metric("🎭 Role Detected", result.get("role", "Unknown"))

            st.markdown(f"**🧠 Recruiter Insight:** {result['recruiter_note']}")

            ec1, ec2 = st.columns(2)
            with ec1:
                st.markdown("**✅ Matched Skills:**")
                b = " ".join([f'<span class="badge">{s}</span>' for s in result["matched"]])
                st.markdown(b or "<span class='badge-neutral'>None detected</span>", unsafe_allow_html=True)
            with ec2:
                st.markdown("**❌ Missing Skills:**")
                b = " ".join([f'<span class="badge badge-missing">{s}</span>' for s in result["missing"]])
                st.markdown(b or "🎉 All matched!", unsafe_allow_html=True)

            # Interest chat
            st.markdown("---")
            st.markdown("**💬 Quick Interest Check**")
            quick_ans = st.text_input("Ask: Are you open to this opportunity?", key="quick_ans",
                                      placeholder="Type candidate's response...")
            if quick_ans:
                i = interest_score(quick_ans)
                final = round(0.65 * result["match_score"] + 0.35 * i, 2)
                st.metric("📊 Interest Score", f"{i}%")
                st.metric("🏆 Final Score",    f"{final}%")

# ─────────────────────────────────────────
# Footer
# ─────────────────────────────────────────
st.markdown("---")
st.markdown('<p style="color:#475569; text-align:center; font-size:13px;">Built for Catalyst Hackathon by Mukthanjali Bonala | Powered by Google Gemini AI 🤖</p>', unsafe_allow_html=True)
