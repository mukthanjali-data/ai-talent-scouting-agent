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
        "target achievement","client handling","screening","interviewing",
        "b2b","b2c","inside sales","outbound","inbound","cold calling",
        "account management","pipeline management","forecasting"
    ]
    tl = text.lower()
    return [s for s in known if s in tl]

def _fallback_exp(text):
    for pat in [
        r'(\d+)\+?\s*years?\s*of\s*experience',
        r'(\d+)\+?\s*years?\s*experience',
        r'minimum\s*(\d+)\+?\s*years?',
        r'at\s*least\s*(\d+)\+?\s*years?',
        r'(\d+)\s*[-–]\s*(\d+)\s*years?',
        r'(\d+)\+?\s*years?',
    ]:
        m = re.search(pat, text.lower())
        if m:
            v  = int(m.group(1))
            v2 = int(m.group(2)) if len(m.groups()) > 1 and m.group(2) else v + 2
            return (v, v2)
    return (2, 5)

def _fallback_role(text):
    """Try to guess role from common keywords in the text."""
    tl = text.lower()
    roles = [
        ("sales executive",      ["sales executive", "sales exec"]),
        ("sales manager",        ["sales manager"]),
        ("business development", ["business development", "bdm", "bde"]),
        ("data analyst",         ["data analyst"]),
        ("data scientist",       ["data scientist"]),
        ("machine learning engineer", ["machine learning engineer", "ml engineer"]),
        ("software engineer",    ["software engineer", "software developer"]),
        ("marketing executive",  ["marketing executive", "marketing manager"]),
        ("hr executive",         ["hr executive", "human resources", "hr manager"]),
        ("recruiter",            ["recruiter", "talent acquisition"]),
        ("business analyst",     ["business analyst"]),
        ("product manager",      ["product manager"]),
        ("operations manager",   ["operations manager"]),
    ]
    for role_name, keywords in roles:
        if any(k in tl for k in keywords):
            return role_name.title()
    # Try to find "for a/an <Role>" or "hiring a/an <Role>" pattern
    m = re.search(r'(?:for\s+a[n]?\s+|hiring\s+a[n]?\s+|position\s+of\s+|role\s+of\s+)([A-Za-z\s]+?)(?:\s+to|\s+with|\s+who|\.|,)', text, re.IGNORECASE)
    if m:
        return m.group(1).strip().title()
    return None

# ─────────────────────────────────────────
# AI: Extract JD Requirements
# ─────────────────────────────────────────
def extract_requirements(jd_text):
    fallback_skills = _fallback_skills(jd_text)
    fallback_exp    = _fallback_exp(jd_text)
    fallback_role   = _fallback_role(jd_text) or "Unknown Role"

    prompt = f"""
You are a recruitment assistant. Carefully read this job description.

Extract:
1. The exact job title/role (e.g. "Sales Executive", "Data Analyst", "Marketing Manager")
2. Required skills — both technical and domain-specific (max 8)
3. Minimum and maximum years of experience required

Return ONLY this JSON with no explanation, no markdown:
{{
    "role": "exact job title here",
    "skills": ["skill1", "skill2", "skill3"],
    "exp_min": 2,
    "exp_max": 5
}}

Important:
- role must be a specific job title, not generic like "Unknown" or "N/A"
- If experience is "3+ years", set exp_min=3, exp_max=6
- skills must be relevant to this specific role

Job Description:
{jd_text[:2000]}
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={{"response_mime_type": "application/json"}}
        )
        d = json.loads(response.text)
        skills  = d.get("skills") or fallback_skills
        exp_min = int(d.get("exp_min") or fallback_exp[0])
        exp_max = int(d.get("exp_max") or fallback_exp[1])
        role    = d.get("role") or ""

        # Reject generic/bad role values
        bad_roles = ["unknown", "n/a", "na", "none", "job", "role", "position", ""]
        if not role or role.lower().strip() in bad_roles:
            role = fallback_role

        if not skills:
            skills = fallback_skills

        return skills[:8], (exp_min, exp_max), role

    except Exception:
        return fallback_skills[:8], fallback_exp, fallback_role

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

    exp_min, _ = exp_range
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
# AI: Recruiter Note
# ─────────────────────────────────────────
def _ai_note(role, req_skills, candidate_name, candidate_skills, candidate_exp, match_score):
    prompt = f"""
You are a senior recruiter writing a concise hiring note.
Role: {role}
Required Skills: {', '.join(req_skills)}
Candidate: {candidate_name}
Candidate Skills: {', '.join(candidate_skills)}
Experience: {candidate_exp} years
Match Score: {match_score}%

Write exactly 2 short sentences:
1. Specific fit/gap analysis — mention actual skill names.
2. One concrete action (e.g. "Schedule a technical interview", "Strong hire", "Skip — missing core skills").
Be direct and professional.
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        if text and len(text) > 20:
            return text
        raise ValueError("Too short")
    except Exception:
        fit  = "strong" if match_score >= 70 else "partial" if match_score >= 50 else "weak"
        top3 = ", ".join(candidate_skills[:3]) if candidate_skills else "general skills"
        action = "Recommend for interview." if match_score >= 60 else "Consider for future openings."
        return (f"{candidate_name} shows a {fit} fit ({match_score}%) with experience in {top3}. {action}")

# ─────────────────────────────────────────
# Analyze structured candidate
# ─────────────────────────────────────────
def analyze_candidate(jd_text, candidate, required_skills=None, exp_range=None, role=None):
    try:
        if required_skills is None:
            required_skills, exp_range, role = extract_requirements(jd_text)

        match_score, matched, missing = _score(
            required_skills, exp_range,
            candidate["skills"], candidate["experience"]
        )
        note = _ai_note(role, required_skills, candidate["name"],
                        candidate["skills"], candidate["experience"], match_score)

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
        note = _ai_note(role, required_skills, "Candidate",
                        candidate_skills, candidate_exp, match_score)

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
    "ai_followup": "<1 warm natural sentence>",
    "sentiment": "<positive/neutral/negative>"
}}
- Very enthusiastic: +15 to +20
- Open/willing: +5 to +10
- Vague: 0 to +5
- Hesitant: -10 to -5
- Negative: -20 to -10
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
# Simple interest score
# ─────────────────────────────────────────
def interest_score(answer):
    prompt = f"""
Rate candidate interest from response (0-100).
Response: "{answer}"
Return ONLY JSON: {{"score": <0-100>}}
- Enthusiastic: 80-100, Open: 60-79, Vague: 40-59, Hesitant: 20-39, Negative: 0-19
"""
    try:
        r = client.models.generate_content(
            model="gemini-1.5-flash", contents=prompt,
            config={{"response_mime_type": "application/json"}}
        )
        return int(json.loads(r.text).get("score", 50))
    except Exception:
        ans = answer.lower()
        if any(w in ans for w in ["yes","sure","interested","open","excited","love","happy"]):
            return 75
        elif any(w in ans for w in ["no","not","busy","settled"]):
            return 20
        return 50
