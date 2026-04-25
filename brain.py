from google import genai
import json
import os
import re
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

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
        "seo","social media","hr","recruitment","talent acquisition",
        "business analysis","stakeholder management","operations",
        "campaign management","statistics","data visualization","reporting",
        "target achievement","client handling","screening","interviewing"
    ]
    tl = text.lower()
    return [s for s in known if s in tl]

def _fallback_exp(text):
    for pat in [
        r'(\d+)\+?\s*years?\s*of\s*experience',
        r'(\d+)\+?\s*years?\s*experience',
        r'minimum\s*(\d+)\+?\s*years?',
        r'at\s*least\s*(\d+)\+?\s*years?',
        r'(\d+)\s*-\s*(\d+)\s*years?',
        r'(\d+)\+?\s*years?',
    ]:
        m = re.search(pat, text.lower())
        if m:
            v  = int(m.group(1))
            v2 = int(m.group(2)) if len(m.groups()) > 1 and m.group(2) else v + 2
            return (v, v2)
    return (2, 5)

# ─────────────────────────────────────────
# AI: Extract JD Requirements
# ─────────────────────────────────────────
def extract_requirements(jd_text):
    fallback_skills = _fallback_skills(jd_text)
    fallback_exp    = _fallback_exp(jd_text)

    prompt = f"""
Read this job description and extract:
1. Required technical/domain skills (max 8, most important only, no generic soft skills)
2. Experience range as min and max years
3. Job role/title

Return ONLY valid JSON, no markdown, no explanation:
{{
    "skills": ["skill1", "skill2"],
    "exp_min": 2,
    "exp_max": 5,
    "role": "Job Title"
}}

Job Description:
{jd_text}
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={{"response_mime_type": "application/json"}}
        )
        d = json.loads(response.text)
        skills  = d.get("skills", fallback_skills) or fallback_skills
        exp_min = int(d.get("exp_min", fallback_exp[0]) or fallback_exp[0])
        exp_max = int(d.get("exp_max", fallback_exp[1]) or fallback_exp[1])
        role    = d.get("role", "") or ""

        if not skills:
            skills = fallback_skills
        if not exp_min:
            exp_min = fallback_exp[0]
        if not role:
            role = "Unknown Role"

        return skills[:8], (exp_min, exp_max), role

    except Exception:
        return fallback_skills[:8], fallback_exp, "Unknown Role"

# ─────────────────────────────────────────
# Scoring Engine
# ─────────────────────────────────────────
def _score(required_skills, exp_range, candidate_skills, candidate_exp):
    req_lower = [s.lower() for s in required_skills]
    can_lower = [s.lower() for s in candidate_skills]

    matched = [s for s in candidate_skills if s.lower() in req_lower]
    missing = [s for s in required_skills  if s.lower() not in can_lower]

    skill_ratio  = len(matched) / len(required_skills) if required_skills else 1.0
    skill_points = skill_ratio * 70

    exp_min, exp_max = exp_range
    ref = exp_min if exp_min > 0 else 2
    if candidate_exp >= exp_min:
        exp_score = 1.0
    elif candidate_exp >= exp_min * 0.75:
        exp_score = 0.80
    elif candidate_exp >= exp_min * 0.5:
        exp_score = 0.60
    else:
        exp_score = max(candidate_exp / ref, 0.3) if ref > 0 else 0.5
    exp_points = exp_score * 20

    exp_bonus = min((candidate_exp - exp_min) * 1.2, 10.0) if candidate_exp > exp_min else 0.0

    total = round(min(100.0, max(0.0, skill_points + exp_points + exp_bonus)), 2)
    return total, matched, missing

# ─────────────────────────────────────────
# AI: Recruiter Note  ← FIXED
# ─────────────────────────────────────────
def _ai_note(jd_summary, candidate_name, candidate_skills, candidate_exp, match_score):
    prompt = f"""
You are a senior recruiter writing a hiring note.
Job Requirements: {jd_summary}
Candidate: {candidate_name}, Skills: {candidate_skills}, Experience: {candidate_exp} years, Match Score: {match_score}%

Write exactly 2 short sentences:
1. Whether this candidate is a good fit and why (mention specific skills by name).
2. One concrete recommendation (interview, skip, assess further, etc.).
Keep it professional and specific. No generic phrases.
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        if text:
            return text
        raise ValueError("Empty response")
    except Exception:
        fit = "strong" if match_score >= 70 else "partial" if match_score >= 50 else "weak"
        top3 = ", ".join(candidate_skills[:3]) if candidate_skills else "general skills"
        return (f"{candidate_name} shows a {fit} fit with {match_score}% match, "
                f"bringing experience in {top3}. "
                f"{'Recommend for interview.' if match_score >= 60 else 'Consider for future openings.'}")

# ─────────────────────────────────────────
# Analyze structured candidate (JSON profile)
# ─────────────────────────────────────────
def analyze_candidate(jd_text, candidate, required_skills=None, exp_range=None, role=None):
    try:
        if required_skills is None:
            required_skills, exp_range, role = extract_requirements(jd_text)

        match_score, matched, missing = _score(
            required_skills, exp_range,
            candidate["skills"], candidate["experience"]
        )

        jd_summary = f"Role: {role}, Skills: {', '.join(required_skills)}, Exp: {exp_range[0]}-{exp_range[1]} yrs"
        note = _ai_note(jd_summary, candidate["name"], candidate["skills"], candidate["experience"], match_score)

        return {
            "match_score":     match_score,
            "matched":         matched,
            "missing":         missing,
            "recruiter_note":  note,
            "required_skills": required_skills,
            "exp_range":       exp_range,
            "role":            role or "Unknown"
        }
    except Exception as e:
        return {
            "match_score": 0, "matched": [], "missing": [],
            "recruiter_note": f"Error: {str(e)}",
            "required_skills": [], "exp_range": (0, 0), "role": "Unknown"
        }

# ─────────────────────────────────────────
# Analyze free-text resume
# ─────────────────────────────────────────
def analyze(jd_text, candidate_text, required_skills=None, exp_range=None, role=None):
    try:
        if required_skills is None:
            required_skills, exp_range, role = extract_requirements(jd_text)

        candidate_skills = _fallback_skills(candidate_text)
        exp_match        = re.search(r'(\d+)\s*year', candidate_text.lower())
        candidate_exp    = int(exp_match.group(1)) if exp_match else 2

        match_score, matched, missing = _score(required_skills, exp_range, candidate_skills, candidate_exp)

        jd_summary = f"Role: {role}, Skills: {', '.join(required_skills)}, Exp: {exp_range[0]}-{exp_range[1]} yrs"
        note = _ai_note(jd_summary, "Candidate", candidate_skills, candidate_exp, match_score)

        return {
            "match_score":     match_score,
            "matched":         matched,
            "missing":         missing,
            "recruiter_note":  note,
            "required_skills": required_skills,
            "exp_range":       exp_range,
            "role":            role or "Unknown"
        }
    except Exception as e:
        return {
            "match_score": 0, "matched": [], "missing": [],
            "recruiter_note": f"Error: {str(e)}",
            "required_skills": [], "exp_range": (0, 0), "role": "Unknown"
        }

# ─────────────────────────────────────────
# AI: Multi-turn interest assessment
# ─────────────────────────────────────────
def ai_assess_interest(candidate_name, question, answer, history):
    prompt = f"""
Assess job candidate interest from their answer.
Candidate: {candidate_name}
Question: {question}
Answer: {answer}

Return ONLY JSON:
{{
    "interest_delta": <integer -20 to 20>,
    "ai_followup": "<1 warm natural sentence acknowledging their answer>",
    "sentiment": "<positive/neutral/negative>"
}}

Rules:
- Very enthusiastic/positive: +15 to +20
- Open/willing: +5 to +10
- Vague/unclear: 0 to +5
- Hesitant/conditional: -10 to -5
- Negative/not interested: -20 to -10
"""
    try:
        r = client.models.generate_content(
            model="gemini-1.5-flash", contents=prompt,
            config={{"response_mime_type": "application/json"}}
        )
        result = json.loads(r.text)
        if not result.get("ai_followup"):
            result["ai_followup"] = "Thank you for sharing that!"
        return result
    except Exception:
        delta = 10 if "yes" in answer.lower() else -10 if "no" in answer.lower() else 0
        return {"interest_delta": delta, "ai_followup": "Thank you for sharing that!", "sentiment": "neutral"}

# ─────────────────────────────────────────
# Simple interest score (single answer)
# ─────────────────────────────────────────
def interest_score(answer):
    prompt = f"""
Rate this candidate's interest level from their response (0-100).
Response: "{answer}"
Return ONLY JSON: {{"score": <0-100>, "sentiment": "<positive/neutral/negative>"}}
- Enthusiastic: 80-100
- Open: 60-79
- Vague: 40-59
- Hesitant: 20-39
- Negative: 0-19
"""
    try:
        r = client.models.generate_content(
            model="gemini-1.5-flash", contents=prompt,
            config={{"response_mime_type": "application/json"}}
        )
        d = json.loads(r.text)
        return int(d.get("score", 50))
    except Exception:
        ans = answer.lower()
        if any(w in ans for w in ["yes", "sure", "interested", "open", "excited", "love", "happy"]):
            return 75
        elif any(w in ans for w in ["no", "not", "busy", "settled"]):
            return 20
        return 50
