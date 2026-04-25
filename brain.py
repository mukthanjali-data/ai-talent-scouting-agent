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
        "campaign management","statistics","data visualization","reporting"
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
            v = int(m.group(1))
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
1. Required technical/domain skills (max 8, most important only)
2. Experience range as min and max years
3. Job role/title

Return ONLY valid JSON, no markdown:
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
        role    = d.get("role", "Unknown Role") or "Unknown Role"
        return skills[:8], (exp_min, exp_max), role
    except Exception:
        return fallback_skills[:8], fallback_exp, "Unknown Role"

# ─────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────
def _score(required_skills, exp_range, candidate_skills, candidate_exp):
    req_lower = [s.lower() for s in required_skills]
    can_lower = [s.lower() for s in candidate_skills]

    matched = [s for s in candidate_skills if s.lower() in req_lower]
    missing = [s for s in required_skills  if s.lower() not in can_lower]

    # Skill score: 0-70
    skill_ratio  = len(matched) / len(required_skills) if required_skills else 1.0
    skill_points = skill_ratio * 70

    # Experience score: 0-20
    exp_min, exp_max = exp_range
    mid_exp = (exp_min + exp_max) / 2
    if candidate_exp >= exp_min:
        exp_score = min(candidate_exp / mid_exp, 1.0)
    else:
        exp_score = max(candidate_exp / exp_min, 0.3) if exp_min > 0 else 0.5
    exp_points = exp_score * 20

    # Bonus: extra experience (unique per candidate)
    exp_bonus = min((candidate_exp - exp_min) * 1.2, 10) if candidate_exp > exp_min else 0

    total = round(min(100.0, max(0.0, skill_points + exp_points + exp_bonus)), 2)
    return total, matched, missing

# ─────────────────────────────────────────
# AI: Analyze JD vs candidate text
# ─────────────────────────────────────────
def analyze(jd_text, candidate_text, required_skills=None, exp_range=None, role=None):
    try:
        if required_skills is None:
            required_skills, exp_range, role = extract_requirements(jd_text)

        # Parse candidate skills from free text if needed
        candidate_skills = _fallback_skills(candidate_text)
        # Try to extract experience from text
        exp_match = re.search(r'(\d+)\s*year', candidate_text.lower())
        candidate_exp = int(exp_match.group(1)) if exp_match else 2

        match_score, matched, missing = _score(required_skills, exp_range, candidate_skills, candidate_exp)

        # AI recruiter note
        note = _ai_note(jd_text, candidate_text, match_score)

        return {
            "match_score":    match_score,
            "matched":        matched,
            "missing":        missing,
            "recruiter_note": note,
            "required_skills":required_skills,
            "exp_range":      exp_range,
            "role":           role or "Unknown"
        }
    except Exception as e:
        return {
            "match_score": 0, "matched": [], "missing": [],
            "recruiter_note": f"Error: {str(e)}",
            "required_skills": [], "exp_range": (0,0), "role": "Unknown"
        }

# ─────────────────────────────────────────
# Analyze structured candidate (from JSON)
# ─────────────────────────────────────────
def analyze_candidate(jd_text, candidate, required_skills=None, exp_range=None, role=None):
    try:
        if required_skills is None:
            required_skills, exp_range, role = extract_requirements(jd_text)

        match_score, matched, missing = _score(
            required_skills, exp_range,
            candidate["skills"], candidate["experience"]
        )
        note = _ai_note(jd_text, str(candidate), match_score)

        return {
            "match_score":    match_score,
            "matched":        matched,
            "missing":        missing,
            "recruiter_note": note,
            "required_skills":required_skills,
            "exp_range":      exp_range,
            "role":           role or "Unknown"
        }
    except Exception as e:
        return {
            "match_score": 0, "matched": [], "missing": [],
            "recruiter_note": f"Error: {str(e)}",
            "required_skills": [], "exp_range": (0,0), "role": "Unknown"
        }

# ─────────────────────────────────────────
# AI: Recruiter note
# ─────────────────────────────────────────
def _ai_note(jd_text, candidate_text, match_score):
    prompt = f"""
You are a senior recruiter. Evaluate fit in 2 sentences.
Job: {jd_text[:200]}
Candidate: {candidate_text[:200]}
Match Score: {match_score}%
Sentence 1: Specific skill fit/gap.
Sentence 2: Recommendation.
"""
    try:
        r = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        return r.text.strip()
    except Exception:
        return f"Match score: {match_score}%. Review candidate profile manually."

# ─────────────────────────────────────────
# AI: Interest Score from chat response
# ─────────────────────────────────────────
def interest_score(answer):
    prompt = f"""
Rate candidate interest from their response (0-100).
Response: "{answer}"
Return ONLY a JSON: {{"score": <0-100>, "sentiment": "<positive/neutral/negative>"}}
Rules: enthusiastic=80-100, open=60-79, vague=40-59, hesitant=20-39, negative=0-19
"""
    try:
        r = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={{"response_mime_type": "application/json"}}
        )
        d = json.loads(r.text)
        return int(d.get("score", 50))
    except Exception:
        ans = answer.lower()
        if any(w in ans for w in ["yes","sure","interested","open","excited","love"]):
            return 75
        elif any(w in ans for w in ["no","not","busy","happy","settled"]):
            return 20
        return 50

# ─────────────────────────────────────────
# AI: Multi-turn chat assessment
# ─────────────────────────────────────────
def ai_assess_interest(candidate_name, question, answer, history):
    prompt = f"""
Assess candidate interest delta from their answer.
Candidate: {candidate_name}
Question: {question}
Answer: {answer}

Return ONLY JSON:
{{
    "interest_delta": <-20 to 20>,
    "ai_followup": "<1 natural sentence>",
    "sentiment": "<positive/neutral/negative>"
}}
- Enthusiastic: +15 to +20
- Open: +5 to +10
- Vague: 0 to +5
- Hesitant: -10 to -5
- Negative: -20 to -10
"""
    try:
        r = client.models.generate_content(
            model="gemini-1.5-flash", contents=prompt,
            config={{"response_mime_type": "application/json"}}
        )
        return json.loads(r.text)
    except Exception:
        delta = 10 if "yes" in answer.lower() else -10 if "no" in answer.lower() else 0
        return {"interest_delta": delta, "ai_followup": "Thank you!", "sentiment": "neutral"}
