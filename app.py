import streamlit as st
import json
import docx
from PyPDF2 import PdfReader
from brain import analyze, analyze_candidate, extract_requirements, interest_score, ai_assess_interest

st.set_page_config(page_title="TalentAI Scout", layout="wide", page_icon="🤖")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .badge { background: #1e293b; color: #38bdf8; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; margin: 2px; display: inline-block; border: 1px solid #334155; }
    .badge-missing { color: #f87171; border-color: #7f1d1d; }
    .chat-ai { background: #1e293b; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #6366f1; }
    .chat-user { background: #064e3b; padding: 15px; border-radius: 10px; margin: 10px 0; text-align: right; border-right: 4px solid #10b981; }
    button[kind="primary"] { background: linear-gradient(135deg, #6366f1, #4f46e5) !important; color: white !important; width: 100%; border: none !important; padding: 10px !important; }
    .jd-parsed { background: #1e293b; padding: 10px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
for k, v in {"results": None, "chat_step": {}, "chat_history": {}, "interest_scores": {}, "active_chat": None, "eval_result": None, "eval_interest": None}.items():
    if k not in st.session_state: st.session_state[k] = v

def read_file(file):
    if not file: return ""
    try:
        if file.name.endswith(".pdf"): return " ".join([p.extract_text() or "" for p in PdfReader(file).pages])
        if file.name.endswith(".docx"): return " ".join([p.text for p in docx.Document(file).paragraphs])
        return file.read().decode()
    except: return ""

# --- HEADER ---
st.title("🤖 TalentAI Scout")
st.caption("AI-powered intelligent hiring system | Catalyst Hackathon")
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 Find & Rank Candidates", "🎯 Evaluate Single Candidate"])

# --- TAB 1: RANKING & CHAT ---
with tab1:
    if st.session_state.active_chat:
        name = st.session_state.active_chat
        st.button("⬅️ Back to Results", on_click=lambda: st.session_state.update({"active_chat": None}))
        st.subheader(f"💬 Chatting with {name}")
        
        if name not in st.session_state.chat_step: st.session_state.chat_step[name] = 0
        if name not in st.session_state.chat_history: st.session_state.chat_history[name] = []
        
        questions = ["Are you currently open to exploring new opportunities?", "Would you be open to relocating for this role?", "What is your notice period / earliest joining date?", "What excites you most about this kind of role?"]
        
        for msg in st.session_state.chat_history[name]:
            div = "chat-ai" if msg["role"] == "ai" else "chat-user"
            st.markdown(f'<div class="{div}">{msg["text"]}</div>', unsafe_allow_html=True)
            
        step = st.session_state.chat_step[name]
        if step < len(questions):
            q = questions[step]
            st.markdown(f'<div class="chat-ai"><b>Recruiter:</b> {q}</div>', unsafe_allow_html=True)
            with st.form(key=f"f_{name}_{step}", clear_on_submit=True):
                ans = st.text_input("Type response:")
                if st.form_submit_button("Send ➤") and ans:
                    res = ai_assess_interest(name, q, ans, [])
                    st.session_state.chat_history[name].extend([{"role":"ai", "text":q}, {"role":"user", "text":ans}, {"role":"ai", "text":res['ai_followup']}])
                    st.session_state.chat_step[name] += 1
                    # Update interest score in results
                    for r in st.session_state.results:
                        if r['name'] == name:
                            r['interest_score'] = max(0, min(100, r['interest_score'] + res['interest_delta']))
                            r['final_score'] = round(0.65 * r['match_score'] + 0.35 * r['interest_score'], 2)
                    st.rerun()
        else: st.success("✅ Engagement Complete!")

    else:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("📄 Job Description")
            jd_file = st.file_uploader("Upload JD", type=["pdf", "docx", "txt"])
            jd_text = st.text_area("Or paste JD", height=150)
            jd = read_file(jd_file) if jd_file else jd_text
        with c2:
            st.subheader("⚙️ Settings")
            top_n = st.slider("Top N candidates", 1, 10, 4)
            min_score = st.slider("Min Match Score", 0, 100, 0)
            if st.button("🔍 Find & Rank", type="primary"):
                if not jd.strip(): st.warning("Please provide a JD")
                else:
                    with st.spinner("Analyzing..."):
                        req_skills, exp_range, role = extract_requirements(jd)
                        with open("candidates.json") as f:
                            cands = json.load(f)
                        res_list = []
                        for c in cands:
                            r = analyze_candidate(jd, c, req_skills, exp_range, role)
                            r['interest_score'] = 50
                            r['final_score'] = round(0.65 * r['match_score'] + 0.35 * 50, 2)
                            res_list.append(r)
                        st.session_state.results = sorted([r for r in res_list if r['match_score'] >= min_score], key=lambda x: x['final_score'], reverse=True)[:top_n]
        
        if st.session_state.results:
            st.markdown("---")
            st.subheader(f"🏆 Ranked Shortlist")
            for r in st.session_state.results:
                with st.expander(f"👤 {r['name']} | Final: {r['final_score']}% | Match: {r['match_score']}%"):
                    st.markdown(f"**Insight:** {r['recruiter_note']}")
                    st.write(f"📅 {r['experience']} yrs | 📍 {r['location']} | 💰 {r['expected_ctc']}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Matched:** " + "".join([f'<span class="badge">{s}</span>' for s in r['matched']]), unsafe_allow_html=True)
                    with col_b:
                        st.markdown("**Missing:** " + "".join([f'<span class="badge badge-missing">{s}</span>' for s in r['missing']]), unsafe_allow_html=True)
                    if st.button(f"💬 Chat with {r['name']}", key=f"chat_{r['name']}"):
                        st.session_state.active_chat = r['name']
                        st.rerun()

# --- TAB 2: SINGLE EVAL ---
with tab2:
    st.subheader("🎯 Single Candidate Evaluator")
    e1, e2 = st.columns(2)
    with e1: jd_single = st.text_area("Paste JD", key="js")
    with e2: res_single = st.file_uploader("Upload Resume", type=["pdf", "docx"], key="rs")
    
    if st.button("Evaluate Now", type="primary"):
        res_txt = read_file(res_single)
        if jd_single and res_txt:
            st.session_state.eval_result = analyze(jd_single, res_txt)
    
    if st.session_state.eval_result:
        er = st.session_state.eval_result
        st.metric("Match Score", f"{er['match_score']}%", er['role'])
        st.info(er['recruiter_note'])
        with st.form("quick_interest"):
            ans = st.text_input("Quick interest check response:")
            if st.form_submit_button("📊 Score Interest") and ans:
                i = interest_score(ans)
                st.session_state.eval_interest = i
        if st.session_state.eval_interest:
            st.metric("Interest Score", f"{st.session_state.eval_interest}%")
