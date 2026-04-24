import streamlit as st
import json
import re
import random

# Load candidates
with open("candidates.json", "r") as f:
    candidates = json.load(f)

# ---------------- FUNCTIONS ---------------- #

def extract_skills(jd):
    skills_list = ["Python", "SQL", "Excel", "Power BI", "Tableau", "Machine Learning"]
    return [skill for skill in skills_list if skill.lower() in jd.lower()]

def extract_experience(jd):
    match = re.search(r'(\d+)\s*years', jd)
    return int(match.group(1)) if match else 0

def calculate_match_score(candidate, required_skills, required_exp):
    matched_skills = set(candidate["skills"]) & set(required_skills)
    
    skill_score = len(matched_skills) / len(required_skills) if required_skills else 0
    exp_score = min(candidate["experience"] / required_exp, 1) if required_exp > 0 else 1
    
    match_score = (skill_score + exp_score) / 2
    
    return round(match_score * 100, 2), matched_skills

def calculate_interest_score():
    return random.randint(50, 100)

# ---------------- UI ---------------- #

st.title("🤖 AI Talent Scouting Agent")
st.markdown("### 🚀 Smart AI Recruiter Dashboard")

jd = st.text_area("Paste Job Description")

if st.button("Find Candidates"):
    
    required_skills = extract_skills(jd)
    required_exp = extract_experience(jd)

    results = []

    for candidate in candidates:
        match_score, matched_skills = calculate_match_score(candidate, required_skills, required_exp)

        interest_score = calculate_interest_score()

        final_score = round((0.7 * match_score) + (0.3 * interest_score), 2)

        results.append({
            "name": candidate["name"],
            "match_score": match_score,
            "interest_score": interest_score,
            "final_score": final_score,
            "matched_skills": list(matched_skills),
            "reason": f"Matched {len(matched_skills)} out of {len(required_skills)} skills"
        })

    # Sort by FINAL score
    results = sorted(results, key=lambda x: x["final_score"], reverse=True)

    st.subheader("📊 Ranked Candidates")

    for r in results:
        st.write(f"### {r['name']}")
        st.write(f"✅ Match Score: {r['match_score']}%")
        st.write(f"💬 Interest Score: {r['interest_score']}%")
        st.write(f"🏆 Final Score: {r['final_score']}%")
        st.write(f"🧠 Matched Skills: {r['matched_skills']}")
        st.write(f"📌 Reason: {r['reason']}")
        st.write("---")