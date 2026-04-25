import json
import re
import os
from dotenv import load_dotenv
from google import genai
import streamlit as st

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# ---------- EXPERIENCE ----------
def extract_experience(jd):
    jd = jd.lower()

    m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*year', jd)
    if m:
        return (int(m.group(1)), int(m.group(2)))

    m = re.search(r'(\d+)\+?\s*year', jd)
    if m:
        val = int(m.group(1))
        return (val, val+2)

    return (2, 5)

# ---------- SAFE JSON ----------
def safe_json(text):
    try:
        return json.loads(text)
    except:
        return None

# ---------- JD PARSER ----------
def ai_extract_requirements(jd):

    fallback_exp = extract_experience(jd)

    prompt = f"""
Extract job role, skills, experience.

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

    text = jd.lower()

    if "data" in text:
        role = role or "Data Analyst"
        skills = skills or ["python","sql","excel","power bi","tableau"]

    elif "sales" in text:
        role = role or "Sales Executive"
        skills = skills or ["sales","communication","crm"]

    else:
        role = role or "General Role"
        skills = skills or ["communication"]

    return [s.lower() for s in skills[:6]], exp, role

# ---------- PROFILE PARSER ----------
def extract_candidate_profile(text):

    text = text.lower()

    skill_db = [
        "python","sql","excel","power bi","tableau",
        "sales","crm","communication","machine learning"
    ]

    skills = [s for s in skill_db if s in text]

    m = re.search(r'(\d+)\+?\s*year', text)
    exp = int(m.group(1)) if m else 2

    return {
        "name": "Candidate",
        "skills": skills,
        "experience": exp
    }

# ---------- SCORING ----------
def rule_score(candidate, req_skills, req_exp):

    matched = [s for s in candidate["skills"] if s in req_skills]

    skill_score = (len(matched)/max(len(req_skills),1))*70

    min_exp, max_exp = req_exp

    if candidate["experience"] < min_exp:
        exp_score = 10
    elif min_exp <= candidate["experience"] <= max_exp:
        exp_score = 30
    else:
        exp_score = 20

    return round(skill_score + exp_score,2), matched

# ---------- FINAL ----------
def analyze_job_and_match(jd, candidate, skills=None, exp=None, role=None):

    if skills is None:
        skills, exp, role = ai_extract_requirements(jd)

    score, matched = rule_score(candidate, skills, exp)

    missing = [s for s in skills if s not in matched]

    return {
        "match_score": score,
        "matched_skills": matched if matched else ["None"],
        "missing_skills": missing,
        "role": role
    }
