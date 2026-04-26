import streamlit as st
import json
import docx
from PyPDF2 import PdfReader
from brain import analyze, analyze_candidate, extract_requirements, interest_score, ai_assess_interest

st.set_page_config(page_title="TalentAI Scout", layout="wide", page_icon="🤖")

# ─────────────────────────────────────────
# CSS
# ─────────────────────────────────────────
st.markdown("""
<style>

/* ───────────── EVALUATE BUTTON (SPECIAL STYLE) ───────────── */
button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 600;
    border: none;
}

button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4f46e5, #4338ca) !important;
    box-shadow: 0 8px 20px rgba(79,70,229,0.4);
}


/* ───────────── FILE UPLOADER TEXT FIX ───────────── */
div[data-testid="stFileUploader"] * {
    color: white !important;
}

/* Upload button inside uploader */
div[data-testid="stFileUploader"] button {
    background: #1e293b !important;
    color: white !important;
    border: 1px solid #334155 !important;
}

/* Small helper text (200MB...) */
div[data-testid="stFileUploader"] small {
    color: #cbd5f5 !important;
}


/* ───────────── TEXTAREA BORDER IMPROVEMENT ───────────── */
textarea {
    border: 2px solid #cbd5e1 !important;
}

textarea:focus {
    border: 2px solid #6366f1 !important;
}

</style>
""", unsafe_allow_html=True)
# ─────────────────────────────────────────
# Session State
# ─────────────────────────────────────────
for k, v in {
    "results":         None,
    "jd_cache":        "",
    "req_skills":      None,
    "req_exp":         None,
    "req_role":        None,
    "chat_step":       {},
    "chat_history":    {},
    "interest_scores": {},
    "active_chat":     None,
    "eval_result":     None,
    "eval_interest":   None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────
# File Reader
# ─────────────────────────────────────────
def read_file(file):
    if file is None:
        return ""
    try:
        if file.name.endswith(".pdf"):
            reader = PdfReader(file)
            return " ".join([p.extract_text() or "" for p in reader.pages])
        elif file.name.endswith(".docx"):
            d = docx.Document(file)
            return " ".join([p.text for p in d.paragraphs])
        elif file.name.endswith(".txt"):
            return file.read().decode()
    except Exception:
        pass
    return ""

# ─────────────────────────────────────────
# Header
# ─────────────────────────────────────────
st.markdown("# 🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system")
st.markdown(
    '<p style="color:#94a3b8;font-size:14px;">'
    '📄 JD → 🧠 AI Parsing → 🎯 Matching → 💬 Chat → 📊 Interest → 🏆 Ranking'
    '</p>', unsafe_allow_html=True
)
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 Find & Rank Candidates", "🎯 Evaluate Single Candidate"])

# ══════════════════════════════════════════
# TAB 1
# ══════════════════════════════════════════
with tab1:

    # ── CHAT VIEW (full page, no expanders) ──
    if st.session_state.active_chat:
        name = st.session_state.active_chat
        cand = next((r for r in (st.session_state.results or []) if r["name"] == name), None)

        if cand:
            st.markdown(f"## 💬 Engaging: {name}")
            st.markdown(
                f"🎯 Match: **{cand['match_score']}%** &nbsp;|&nbsp; "
                f"📅 Exp: **{cand['experience']} yrs** &nbsp;|&nbsp; "
                f"📍 {cand['location']} &nbsp;|&nbsp; "
                f"💰 {cand['expected_ctc']}",
                unsafe_allow_html=True
            )
            st.markdown("---")

            questions = [
                "Are you currently open to exploring new opportunities?",
                "Would you be open to relocating for this role?",
                "What is your current CTC and expected package?",
                "What is your notice period / earliest joining date?",
                "What excites you most about this kind of role?"
            ]

            if name not in st.session_state.chat_step:
                st.session_state.chat_step[name]    = 0
            if name not in st.session_state.chat_history:
                st.session_state.chat_history[name] = []
            if name not in st.session_state.interest_scores:
                st.session_state.interest_scores[name] = 50

            # Show history
            for msg in st.session_state.chat_history[name]:
                css = "chat-ai" if msg["role"] == "ai" else "chat-user"
                lbl = "🤖 Recruiter" if msg["role"] == "ai" else f"👤 {name}"
                st.markdown(f'<div class="{css}"><b>{lbl}:</b> {msg["text"]}</div>', unsafe_allow_html=True)

            step = st.session_state.chat_step[name]

            if step < len(questions):
                q = questions[step]
                st.markdown(f'<div class="chat-ai">🤖 <b>Recruiter:</b> {q}</div>', unsafe_allow_html=True)
                st.markdown("")

                # ✅ Use st.form so Enter key submits
                with st.form(key=f"chat_form_{name}_{step}", clear_on_submit=True):
                    ans = st.text_input(
                        f"Q{step+1}/{len(questions)} — Type response:",
                        placeholder="Type here and press Enter or click Send..."
                    )
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        submitted = st.form_submit_button("Send ➤")
                    with c2:
                        back = st.form_submit_button("⬅️ Back to Results")

                if back:
                    st.session_state.active_chat = None
                    st.rerun()

                if submitted and ans.strip():
                    result   = ai_assess_interest(name, q, ans, st.session_state.chat_history[name])
                    delta    = result.get("interest_delta", 0)
                    followup = result.get("ai_followup", "Thank you!")
                    new_score = max(0, min(100, st.session_state.interest_scores[name] + delta))
                    st.session_state.interest_scores[name] = new_score
                    st.session_state.chat_history[name].append({"role": "ai",   "text": q})
                    st.session_state.chat_history[name].append({"role": "user", "text": ans})
                    st.session_state.chat_history[name].append({"role": "ai",   "text": followup})
                    st.session_state.chat_step[name] += 1
                    for r in st.session_state.results:
                        if r["name"] == name:
                            r["interest_score"] = new_score
                            r["final_score"]    = round(0.65 * r["match_score"] + 0.35 * new_score, 2)
                            break
                    st.rerun()

                elif submitted and not ans.strip():
                    st.warning("Please type a response first.")

            else:
                # Chat complete
                score = st.session_state.interest_scores[name]
                if score >= 75:
                    vt, bg, bd = "🔥 Highly Interested — Fast-track!", "#052e16", "#16a34a"
                elif score >= 50:
                    vt, bg, bd = "✅ Moderately Interested — Follow up", "#1c1917", "#d97706"
                else:
                    vt, bg, bd = "❌ Low Interest — Consider others",   "#1f1215", "#dc2626"

                st.success("✅ Engagement complete!")
                st.markdown(
                    f'<div class="verdict-box" style="background:{bg};border-left:5px solid {bd};">'
                    f'Interest Score: <b>{score}%</b><br>{vt}</div>',
                    unsafe_allow_html=True
                )
                for r in st.session_state.results:
                    if r["name"] == name:
                        r["interest_score"] = score
                        r["final_score"]    = round(0.65 * r["match_score"] + 0.35 * score, 2)
                        break
                st.markdown("")
                if st.button("⬅️ Back to Results", key="back_done"):
                    st.session_state.active_chat = None
                    st.rerun()

    else:
        # ── NORMAL VIEW ──
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📄 Job Description")
            jd_file = st.file_uploader("Upload JD (PDF / DOCX / TXT)", ["pdf","docx","txt"], key="jd_upload")
            jd_text = st.text_area("Or paste JD here", height=180, key="jd_paste",
                                   placeholder="e.g. Looking for a Sales Executive with 3+ years in B2B sales, CRM, lead generation...")
            jd = read_file(jd_file) if jd_file else jd_text

        with col2:
            st.subheader("⚙️ Settings")
            top_n     = st.slider("Top N candidates", 3, 20, 10)
            min_score = st.slider("Min Match Score (%)", 0, 70, 0)
            st.markdown('<p style="color:#64748b;font-size:13px;">💡 Upload PDF/DOCX or paste JD text</p>', unsafe_allow_html=True)

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
                        res      = analyze_candidate(jd, c, req_skills, req_exp, req_role)
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

                    st.session_state.results         = sorted(results, key=lambda x: x["final_score"], reverse=True)
                    st.session_state.chat_step       = {}
                    st.session_state.chat_history    = {}
                    st.session_state.interest_scores = {}
                    st.session_state.active_chat     = None
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
                i_done = st.session_state.chat_step.get(r["name"], 0)
                chat_label = f"✅ Chat Done ({r['interest_score']}%)" if i_done >= 5 else f"💬 Chat with {r['name']}"

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

                    st.markdown("")
                    if st.button(chat_label, key=f"chat_btn_{r['name']}"):
                        st.session_state.active_chat = r["name"]
                        st.rerun()

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
                st.session_state.eval_result  = result
                st.session_state.eval_interest = None

    # Persistent result
    if st.session_state.eval_result:
        result = st.session_state.eval_result
        st.success("✅ Evaluation Complete!")

        e1, e2 = st.columns(2)
        e1.metric("🎯 Match Score",   f"{result['match_score']}%")
        e2.metric("🎭 Role Detected", result.get("role", "Unknown"))

        st.markdown(
            f'<div class="eval-result">🧠 <b>Recruiter Insight:</b> {result["recruiter_note"]}</div>',
            unsafe_allow_html=True
        )

        ec1, ec2 = st.columns(2)
        with ec1:
            st.markdown("**✅ Matched Skills:**")
            b = " ".join([f'<span class="badge">{s}</span>' for s in result["matched"]])
            st.markdown(b or "<span class='badge-neutral'>None detected</span>", unsafe_allow_html=True)
        with ec2:
            st.markdown("**❌ Missing Skills:**")
            b = " ".join([f'<span class="badge badge-missing">{s}</span>' for s in result["missing"]])
            st.markdown(b or "🎉 All matched!", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**💬 Quick Interest Check**")

        # ✅ Use form so Enter key works
        with st.form("interest_form"):
            quick_ans = st.text_input(
                "Candidate response to: 'Are you open to this opportunity?'",
                placeholder="Type candidate's response and press Enter..."
            )
            check = st.form_submit_button("📊 Check Interest")

        if check and quick_ans.strip():
            i     = interest_score(quick_ans)
            final = round(0.65 * result["match_score"] + 0.35 * i, 2)
            st.session_state.eval_interest = {"interest": i, "final": final}

        if st.session_state.eval_interest:
            fi1, fi2 = st.columns(2)
            fi1.metric("📊 Interest Score", f"{st.session_state.eval_interest['interest']}%")
            fi2.metric("🏆 Final Score",    f"{st.session_state.eval_interest['final']}%")

        st.markdown("")
        if st.button("🔄 Clear & Start Over", key="clear_eval"):
            st.session_state.eval_result  = None
            st.session_state.eval_interest = None
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    '<p style="color:#475569;text-align:center;font-size:13px;">'
    'Built for Catalyst Hackathon by Mukthanjali Bonala | Powered by Google Gemini AI 🤖'
    '</p>', unsafe_allow_html=True
)
