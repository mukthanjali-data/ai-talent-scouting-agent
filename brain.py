import json
import os
import re
from dotenv import load_dotenv
from google import genai
import streamlit as st

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)


# ---------------- HELPERS ---------------- #
def extract_experience(jd):
    m = re.search(r'(\d+)\+?\s*year', jd.lower())
    return int(m.group(1)) if m else 2


def safe_json(text):
    try:
        return json.loads(text)
    except:
        return None


# ---------------- JD PARSING ---------------- #
def ai_extract_requirements(jd):

    fallback_exp = extract_experience(jd)

    prompt = f"""
Extract job role, skills, experience.

Return JSON:
{{"role":"","skills":[],"experience":number}}

JD:
{jd}
"""

    role, skills, exp = "", [], fallback_exp

    try:
        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        data = safe_json(resp.text) or {}

        role = data.get("role", "")
        skills = data.get("skills", [])
        exp = int(data.get("experience", fallback_exp))

    except:
        pass

    text = jd.lower()

    # 🔥 Improved fallback (semantic coverage)
    if "data" in text:
        role = role or "Data Analyst"
        skills = skills or ["python", "sql", "excel", "power bi", "tableau"]

    elif "sales" in text:
        role = role or "Sales Executive"
        skills = skills or ["sales", "communication", "crm"]

    else:
        role = role or "General Role"
        skills = skills or ["communication"]

    return [s.lower() for s in skills[:6]], exp, role


# ---------------- RULE SCORING ---------------- #
def rule_score(candidate, req_skills, req_exp):

    c_skills = [s.lower() for s in candidate["skills"]]
    matched = [s for s in c_skills if s in req_skills]

    skill_score = (len(matched) / max(len(req_skills), 1)) * 60 if matched else 25
    exp_score = min((candidate["experience"] / max(req_exp, 1)) * 25, 25)

    bonus = max(candidate["experience"] - req_exp, 0) * 2

    total = skill_score + exp_score + bonus

    return round(min(total, 100), 2), matched


# ---------------- AI MATCH ---------------- #
def ai_match(jd, candidate):

    prompt = f"""
You are a recruiter.

Evaluate candidate for job using semantic understanding.

JD:
{jd}

Candidate:
Skills: {candidate['skills']}
Experience: {candidate['experience']}

Return JSON:
{{"score":number,"reason":""}}
"""

    try:
        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        data = safe_json(resp.text)

        if data:
            return data.get("score"), data.get("reason")

    except:
        pass

    return None, None


# ---------------- INTEREST ---------------- #
def ai_assess_interest(ans):

    a = ans.lower()

    if "yes" in a or "interested" in a:
        return 8
    elif "no" in a:
        return -10
    elif "maybe" in a:
        return 3
    return 0


# ---------------- MAIN ---------------- #
def analyze_job_and_match(jd, candidate, skills=None, exp=None, role=None):

    if skills is None:
        skills, exp, role = ai_extract_requirements(jd)

    rule_s, matched = rule_score(candidate, skills, exp)

    ai_s, _ = ai_match(jd, candidate)

    if ai_s:
        final = round(0.65 * ai_s + 0.35 * rule_s, 2)
    else:
        final = rule_s

    # 🔥 intelligent explanation
    missing = [s for s in skills if s not in matched]

    if matched:
        skill_text = ", ".join(matched[:2])
    else:
        skill_text = "limited matching skills"

    gap = f"missing skills like {', '.join(missing[:2])}" if missing else "no major gaps"

    reason = (
        f"{candidate['name']} has {candidate['experience']} years experience and matches {skill_text}. "
        f"However, there are {gap}. This candidate is a "
        f"{'strong' if final > 70 else 'moderate'} fit based on skills and experience alignment."
    )

    return {
        "match_score": final,
        "matched_skills": matched if matched else ["None"],
        "reason": reason,
        "role": role
    }
