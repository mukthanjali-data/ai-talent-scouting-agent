import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv

# Load env
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Model
model = genai.GenerativeModel("gemini-pro")

# ─────────────────────────────────────────
# Fallback extractors
# ─────────────────────────────────────────
def _fallback_skills(text):
    known = [
        "python","sql","excel","power bi","tableau","machine learning",
        "deep learning","nlp","java","javascript","react","node.js","aws",
        "docker","kubernetes","mongodb","postgresql","data analysis",
        "communication","leadership","project management","sales","crm",
        "lead generation","negotiation","field sales","digital marketing",
        "seo","social media","hr","recruitment","talent acquisition"
    ]
    tl = text.lower()
    return [s for s in known if s in tl]

def _fallback_exp(text):
    match = re.search(r'(\d+)\s*year', text.lower())
    return (int(match.group(1)), int(match.group(1)) + 2) if match else (2, 5)

def _fallback_role(text):
    if "data analyst" in text.lower():
        return "Data Analyst"
    if "sales" in text.lower():
        return "Sales Executive"
    return "Unknown Role"

# ─────────────────────────────────────────
# Extract JD Requirements
# ─────────────────────────────────────────
def extract_requirements(jd_text):
    fallback_skills = _fallback_skills(jd_text)
    fallback_exp    = _fallback_exp(jd_text)
    fallback_role   = _fallback_role(jd_text)

    prompt = f"""
Extract role, skills and experience.

Return JSON:
{{
 "role": "",
 "skills": [],
 "exp_min": 2,
 "exp_max": 5
}}

JD:
{jd_text[:2000]}
"""

    try:
        response = model.generate_content(prompt)
        data = json.loads(response.text)

        skills = data.get("skills", fallback_skills)
        exp_min = int(data.get("exp_min", fallback_exp[0]))
        exp_max = int(data.get("exp_max", fallback_exp[1]))
        role = data.get("role", fallback_role)

        return skills[:8], (exp_min, exp_max), role

    except Exception:
        return fallback_skills[:8], fallback_exp, fallback_role

# ─────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────
def _score(required_skills, exp_range, candidate_skills, candidate_exp):
    req = [s.lower() for s in required_skills]
    can = [s.lower() for s in candidate_skills]

    matched = [s for s in candidate_skills if s.lower() in req]
    missing = [s for s in required_skills if s.lower() not in can]

    skill_score = (len(matched) / len(required_skills)) * 70 if required_skills else 70
    exp_score = 20 if candidate_exp >= exp_range[0] else 10

    total = round(min(100, skill_score + exp_score), 2)

    return total, matched, missing

# ─────────────────────────────────────────
# Recruiter Note
# ─────────────────────────────────────────
def _ai_note(role, req_skills, candidate_name, candidate_skills, candidate_exp, match_score):
    prompt = f"""
Role: {role}
Required Skills: {', '.join(req_skills)}
Candidate: {candidate_name}
Skills: {', '.join(candidate_skills)}
Experience: {candidate_exp}
Score: {match_score}

Write 2 short sentences: fit + action.
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        if text and len(text) > 20:
            return text
        raise ValueError

    except Exception:
        fit = "strong" if match_score >= 70 else "partial" if match_score >= 50 else "weak"
        return f"{candidate_name} shows {fit} fit. Recommend interview."

# ─────────────────────────────────────────
# Analyze structured candidate
# ─────────────────────────────────────────
def analyze_candidate(*args):
    """
    Handles both:
    1) analyze_candidate(jd_text, candidate)
    2) analyze_candidate(candidate, skills, exp, role)
    3) analyze_candidate(jd, candidate, skills, exp, role)
    """

    # Case 1: Full 5 args (your current app call)
    if len(args) == 5:
        _, candidate, skills, exp_range, role = args

    # Case 2: Clean 4 args
    elif len(args) == 4:
        candidate, skills, exp_range, role = args

    # Case 3: Only JD + candidate
    elif len(args) == 2:
        jd_text, candidate = args
        skills, exp_range, role = extract_requirements(jd_text)

    else:
        raise ValueError("Invalid arguments passed to analyze_candidate")

    # Scoring
    score, matched, missing = _score(
        skills,
        exp_range,
        candidate.get("skills", []),
        candidate.get("experience", 0)
    )

    # AI note (safe fallback)
    try:
        note = _ai_note(
            role,
            skills,
            candidate.get("name", "Candidate"),
            candidate.get("skills", []),
            candidate.get("experience", 0),
            score
        )
    except:
        note = f"{candidate.get('name','Candidate')} shows a {score}% match."

    return {
        "match_score": score,
        "matched": matched,
        "missing": missing,
        "recruiter_note": note,
        "role": role
    }

# ─────────────────────────────────────────
# Analyze free text
# ─────────────────────────────────────────
def analyze(jd_text, resume_text):
    skills, exp_range, role = extract_requirements(jd_text)

    candidate_skills = _fallback_skills(resume_text)
    exp_match = re.search(r'(\d+)\s*year', resume_text.lower())
    candidate_exp = int(exp_match.group(1)) if exp_match else 2

    score, matched, missing = _score(
        skills, exp_range,
        candidate_skills, candidate_exp
    )

    note = _ai_note(role, skills, "Candidate",
                    candidate_skills, candidate_exp, score)

    return {
        "match_score": score,
        "matched": matched,
        "missing": missing,
        "recruiter_note": note,
        "role": role
    }

# ─────────────────────────────────────────
# Interest Assessment
# ─────────────────────────────────────────
def ai_assess_interest(name, question, answer, history):
    try:
        response = model.generate_content(answer)

        try:
            result = json.loads(response.text)
        except:
            result = {
                "interest_delta": 0,
                "ai_followup": "Thank you for sharing that!",
                "sentiment": "neutral"
            }

        return result

    except Exception:
        return {
            "interest_delta": 0,
            "ai_followup": "Thank you for sharing that!",
            "sentiment": "neutral"
        }

# ─────────────────────────────────────────
# Simple interest score
# ─────────────────────────────────────────
def interest_score(answer):
    ans = answer.lower()

    if any(w in ans for w in ["yes","sure","interested","open","excited","love"]):
        return 75
    elif any(w in ans for w in ["no","not","busy"]):
        return 20
    else:
        return 50
