import streamlit as st
import json
import docx
from PyPDF2 import PdfReader
from brain import analyze, analyze_candidate, extract_requirements, interest_score, ai_assess_interest

st.set_page_config(page_title="TalentAI Scout", layout="wide", page_icon="🤖")

# ───────────────── CSS ─────────────────
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg,#eef2ff,#f8fafc); }

/* Text */
h1,h2,h3,h4,p,label { color:#0f172a !important; }

/* Inputs */
.stTextArea textarea, .stTextInput input {
    background:white !important;
    border-radius:12px !important;
    border:1px solid #cbd5e1 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border:1px solid #6366f1 !important;
    box-shadow:0 0 0 2px rgba(99,102,241,0.2);
}

/* Button */
.stButton > button {
    background:linear-gradient(135deg,#4f46e5,#6366f1) !important;
    color:white !important;
    border-radius:12px;
    font-weight:600;
}
.stButton > button:hover {
    transform:translateY(-2px);
    box-shadow:0 8px 20px rgba(79,70,229,0.3);
}

/* Cards */
.stMetric,.stExpander {
    background:white !important;
    border-radius:14px !important;
    padding:12px !important;
    box-shadow:0 8px 20px rgba(0,0,0,0.05);
}

/* Badges */
.badge {
    background:#e0e7ff;
    color:#3730a3;
    padding:5px 12px;
    border-radius:999px;
}
.badge-missing {
    background:#fee2e2;
    color:#991b1b;
}

/* Chat */
.chat-ai {
    background:#eef2ff;
    padding:10px;
    border-radius:12px 12px 12px 0;
}
.chat-user {
    background:#dcfce7;
    padding:10px;
    border-radius:12px 12px 0 12px;
    text-align:right;
}

/* JD parsed */
.jd-parsed {
    background:linear-gradient(to right,#4f46e5,#6366f1);
    color:white;
    padding:12px;
    border-radius:10px;
}

/* Eval */
.eval-result {
    background:linear-gradient(to right,#10b981,#059669);
    color:white;
    padding:12px;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# ───────────── Session ─────────────
for k,v in {
    "results":None,"chat_step":{},"chat_history":{},
    "interest_scores":{},"active_chat":None,
    "eval_result":None,"eval_interest":None
}.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ───────────── File Reader ─────────────
def read_file(file):
    if not file: return ""
    try:
        if file.name.endswith(".pdf"):
            return " ".join([p.extract_text() or "" for p in PdfReader(file).pages])
        elif file.name.endswith(".docx"):
            return " ".join([p.text for p in docx.Document(file).paragraphs])
        return file.read().decode()
    except:
        return ""

# ───────────── Header ─────────────
st.markdown("# 🤖 TalentAI Scout")

st.markdown("""
<div style="background:linear-gradient(to right,#4f46e5,#6366f1);
padding:14px;border-radius:12px;color:white;text-align:center;font-weight:600;">
🚀 AI Hiring Agent — Automating Recruitment End-to-End
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 Find & Rank", "🎯 Evaluate"])

# ═════════════ TAB 1 ═════════════
with tab1:

    col1,col2=st.columns([2,1])
    with col1:
        jd_file=st.file_uploader("Upload JD",["pdf","docx","txt"])
        jd_text=st.text_area("Or paste JD")
        jd=read_file(jd_file) if jd_file else jd_text

    with col2:
        top_n=st.slider("Top N",3,20,10)
        min_score=st.slider("Min Match %",0,70,0)

    if st.button("🔍 Find Candidates"):
        if not jd.strip():
            st.warning("Add JD first")
        else:
            with st.spinner("🤖 AI analyzing candidates..."):
                req_skills,req_exp,req_role=extract_requirements(jd)
                with open("candidates.json") as f:
                    data=json.load(f)

                results=[]
                for c in data:
                    res=analyze_candidate(jd,c,req_skills,req_exp,req_role)
                    interest=50
                    final=round(0.65*res["match_score"]+0.35*interest,2)
                    results.append({
                        "name":c["name"],
                        "experience":c["experience"],
                        "location":c["location"],
                        "match_score":res["match_score"],
                        "interest_score":interest,
                        "final_score":final,
                        "matched":res["matched"],
                        "missing":res["missing"],
                        "note":res["recruiter_note"]
                    })

                st.session_state.results=sorted(results,key=lambda x:x["final_score"],reverse=True)

    # RESULTS
    if st.session_state.results:
        st.subheader("🏆 Ranked Candidates")

        for i,r in enumerate(st.session_state.results[:top_n],1):

            if r["final_score"]>=75: color="green"
            elif r["final_score"]>=50: color="orange"
            else: color="red"

            with st.expander(f"{i}. {r['name']} | {r['final_score']}%"):
                st.markdown(f"<h3 style='color:{color}'>Final Score: {r['final_score']}%</h3>",unsafe_allow_html=True)

                st.progress(r["match_score"]/100)
                st.progress(r["interest_score"]/100)

                st.success(r["note"])

                st.write("📍",r["location"],"| Exp:",r["experience"])

                st.markdown("**Matched Skills**")
                st.write(", ".join(r["matched"]) or "None")

                st.markdown("**Missing Skills**")
                st.write(", ".join(r["missing"]) or "None")

# ═════════════ TAB 2 ═════════════
with tab2:

    jd=read_file(st.file_uploader("Upload JD"))
    resume=read_file(st.file_uploader("Upload Resume"))

    if st.button("🎯 Evaluate", type="primary"):
        if jd and resume:
            with st.spinner("Analyzing..."):
                result=analyze(jd,resume)
                st.session_state.eval_result=result

    if st.session_state.eval_result:
        r=st.session_state.eval_result

        st.metric("Match Score",f"{r['match_score']}%")
        st.markdown(f"<div class='eval-result'>{r['recruiter_note']}</div>",unsafe_allow_html=True)

        st.progress(r["match_score"]/100)

        ans=st.text_input("Candidate interest response")

        if ans:
            i=interest_score(ans)
            final=round(0.65*r["match_score"]+0.35*i,2)

            st.metric("Interest",f"{i}%")
            st.metric("Final Score",f"{final}%")

# Footer
st.markdown("---")
st.markdown("Built by Muktha 🚀")
