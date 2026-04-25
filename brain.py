import json
import os
import re
from dotenv import load_dotenv
from google import genai
import streamlit as st

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)


# -------- EXPERIENCE -------- #
def extract_experience(jd):
    jd = jd.lower()

    m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*year', jd)
    if m:
        return (int(m.group(1)), int(m.group(2)))

    m = re.search(r'(\d+)\+?\s*year', jd)
    if m:
        val = int(m.group(1))
        return (val, val)

    return (2, 5)


def safe_json(text):
    try:
        return json.loads(text)
    except:
        return None


# -------- JD PARSING -------- #
def ai_extract_requirements(jd):
    fallback_exp = extract_experience(jd)

    prompt = f"""
Extract role, skills, experience.

Return JSON:
{{"role":"","skills":[],"experience":[min,max]}}

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
        exp = tuple(data.get("experience", fallback_exp))

    except:
        pass

    # fallback logic
    text = jd.lower()

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


# -------- SCORING -------- #
def rule_score(candidate, req_skills, req_exp):

    c_skills = [s.lower() for s in candidate["skills"]]
    matched = [s for s in c_skills if s in req_skills]

    skill_ratio = len(matched) / max(len(req_skills), 1)
    skill_score = skill_ratio * 70

    if len(matched) >= 3:
        skill_score += 10

    min_exp, max_exp = req_exp

    if candidate["experience"] < min_exp:
        exp_score = 10
    elif min_exp <= candidate["experience"] <= max_exp:
        exp_score = 30
    else:
        exp_score = 20

    total = skill_score + exp_score
    return round(min(total, 100), 2), matched


# -------- INTEREST -------- #
def ai_assess_interest(ans):
    a = ans.lower()
    if "yes" in a:
        return 10
    elif "no" in a:
        return -10
    elif "maybe" in a:
        return 5
    return 0


# -------- MAIN -------- #
def analyze_job_and_match(jd, candidate, skills=None, exp=None, role=None):

    if skills is None:
        skills, exp, role = ai_extract_requirements(jd)

    score, matched = rule_score(candidate, skills, exp)

    missing = [s for s in skills if s not in matched]

    if score >= 70:
        level = "Strong Fit"
    elif score >= 55:
        level = "Good Fit"
    else:
        level = "Weak Fit"

    reason = (
        f"{candidate['name']} has {candidate['experience']} years experience. "
        f"Matches: {matched if matched else 'few skills'}. "
        f"Missing: {missing[:2] if missing else 'none'}. "
        f"Overall: {level}."
    )

    return {
        "match_score": score,
        "matched_skills": matched if matched else [],
        "missing_skills": missing,
        "reason": reason,
        "role": role
    }
