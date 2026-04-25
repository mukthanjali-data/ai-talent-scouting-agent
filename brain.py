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
# Extract experience
# ─────────────────────────────────────────
def extract_experience(jd):
    match = re.search(r'(\d+)\+?\s*year', jd.lower())
    return int(match.group(1)) if match else 2


# ─────────────────────────────────────────
# Safe JSON
# ─────────────────────────────────────────
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
Extract role, skills, experience.

Return JSON:
{{"role":"","skills":[],"experience":number}}

JD:
{jd}
"""

    role, skills, exp = "", [], fallback_exp

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        data = safe_json(response.text) or {}

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
# Improved rule scoring
# ─────────────────────────────────────────
def rule_score(candidate, req_skills, req_exp):

    c_skills = [s.lower() for s in candidate["skills"]]
    matched = [s for s in c_skills if s in req_skills]

    # Skill score (weighted)
    skill_score = (len(matched) / max(len(req_skills), 1)) * 60 if matched else 25

    # Experience score
    exp_ratio = candidate["experience"] / max(req_exp, 1)
    exp_score = min(exp_ratio * 25, 25)

    # Experience bonus (key differentiator)
    exp_bonus = max(candidate["experience"] - req_exp, 0) * 2

    total = skill_score + exp_score + exp_bonus

    return round(min(total, 100), 2), matched


# ─────────────────────────────────────────
# AI semantic matching
# ─────────────────────────────────────────
def ai_match(jd, candidate):

    prompt = f"""
You are a recruiter.

JD:
{jd}

Candidate:
Skills: {candidate['skills']}
Experience: {candidate['experience']} years

Evaluate semantically (consider related tools and real-world relevance).

Return JSON:
{{"score":number,"reason":""}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        data = safe_json(response.text)

        if data:
            return data.get("score"), data.get("reason")

    except:
        pass

    return None, None


# ─────────────────────────────────────────
# Interest scoring
# ─────────────────────────────────────────
def ai_assess_interest(ans):

    a = ans.lower()

    if "yes" in a or "interested" in a:
        return 15
    elif "no" in a:
        return -15
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

    # Hybrid scoring
    if ai_s:
        final = round(0.65 * ai_s + 0.35 * rule_s, 2)
    else:
        final = rule_s

    # 🔥 Strong recruiter-style reasoning
    if matched:
        skill_text = ", ".join(matched[:2])
        gap = "minor skill gaps"
    else:
        skill_text = "limited matching skills"
        gap = "significant skill gaps"

    reason = (
        f"{candidate['name']} has {candidate['experience']} years experience and matches {skill_text}. "
        f"However, there are {gap}. This candidate is a "
        f"{'strong' if final > 70 else 'moderate'} fit."
    )

    return {
        "match_score": final,
        "matched_skills": matched if matched else ["None"],
        "reason": reason,
        "role": role
    }
