import json
import os
import re
from dotenv import load_dotenv
from google import genai
import streamlit as st

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key)

# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def extract_experience(jd):
    m = re.search(r'(\d+)\+?\s*year', jd.lower())
    return int(m.group(1)) if m else 2


def safe_json(text):
    try:
        return json.loads(text)
    except:
        return None


# ─────────────────────────────────────────
# JD Parsing (AI + fallback)
# ─────────────────────────────────────────
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

    if "sales" in text:
        role = role or "Sales Executive"
        skills = skills or ["sales", "communication", "crm"]

    elif "data" in text:
        role = role or "Data Analyst"
        skills = skills or ["python", "sql", "excel"]

    else:
        role = role or "General Role"
        skills = skills or ["communication"]

    return [s.lower() for s in skills[:5]], exp, role


# ─────────────────────────────────────────
# Rule Scoring
# ─────────────────────────────────────────
def rule_score(candidate, req_skills, req_exp):

    c_skills = [s.lower() for s in candidate["skills"]]
    matched = [s for s in c_skills if s in req_skills]

    skill_score = (len(matched) / max(len(req_skills), 1)) * 50 if matched else 20
    exp_score = min((candidate["experience"] / max(req_exp, 1)) * 30, 30)

    return round(skill_score + exp_score, 2), matched


# ─────────────────────────────────────────
# AI Matching (semantic)
# ─────────────────────────────────────────
def ai_match(jd, candidate):

    prompt = f"""
You are a recruiter.

JD:
{jd}

Candidate:
Skills: {candidate['skills']}
Experience: {candidate['experience']} years

Evaluate semantically (consider related tools).

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
        return data.get("score"), data.get("reason")

    except:
        return None, None


# ─────────────────────────────────────────
# Interest Scoring
# ─────────────────────────────────────────
def ai_assess_interest(ans):

    a = ans.lower()

    if "yes" in a or "interested" in a:
        return 10
    elif "no" in a:
        return -10
    elif "maybe" in a:
        return 5
    return 0


# ─────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────
def analyze_job_and_match(jd, candidate, skills=None, exp=None, role=None):

    if skills is None:
        skills, exp, role = ai_extract_requirements(jd)

    rule_s, matched = rule_score(candidate, skills, exp)

    ai_s, ai_reason = ai_match(jd, candidate)

    if ai_s:
        final = round(0.65 * ai_s + 0.35 * rule_s, 2)
        reason = ai_reason
    else:
        final = rule_s
        reason = f"{candidate['name']} matches {matched}"

    return {
        "match_score": final,
        "matched_skills": matched if matched else ["None"],
        "reason": reason,
        "role": role
    }
