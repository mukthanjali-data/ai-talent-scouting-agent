try:
    from google import genai
except:
    genai = None
import json
import os
import re
from dotenv import load_dotenv
load_dotenv()

client = None
if genai:
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
    return list(set([s for s in known if s in tl]))  # ✅ remove duplicates


# ─────────────────────────────────────────
# EXPERIENCE
# ─────────────────────────────────────────
def _fallback_exp(text):
    text = text.lower()

    m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*years?', text)
    if m:
        return (int(m.group(1)), int(m.group(2)))

    m = re.search(r'(\d+)\+?\s*years?', text)
    if m:
        val = int(m.group(1))
        return (val, val + 2)

    m = re.search(r'(minimum|at least)\s*(\d+)\+?\s*years?', text)
    if m:
        val = int(m.group(2))
        return (val, val + 2)

    return (2, 5)


# ─────────────────────────────────────────
# ROLE
# ─────────────────────────────────────────
def _fallback_role(text):
    tl = text.lower()

    if "sales" in tl:
        return "Sales Executive"
    if "business development" in tl:
        return "Business Development Executive"
    if "data analyst" in tl:
        return "Data Analyst"
    if "data scientist" in tl:
        return "Data Scientist"
    if "machine learning" in tl:
        return "Machine Learning Engineer"
    if "software" in tl:
        return "Software Engineer"
    if "marketing" in tl:
        return "Marketing Executive"
    if "hr" in tl:
        return "HR Executive"
    if "recruiter" in tl:
        return "Recruiter"
    if "business analyst" in tl:
        return "Business Analyst"

    return "General Role"


# ─────────────────────────────────────────
# AI: Extract JD
# ─────────────────────────────────────────
def extract_requirements(jd_text):
    fallback_skills = _fallback_skills(jd_text)
    fallback_exp    = _fallback_exp(jd_text)
    fallback_role   = _fallback_role(jd_text)

    prompt = f"""
Extract role, skills, and experience from JD.

Return JSON only:
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
    if client:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        d = json.loads(response.text)
    else:
        raise Exception("No API")

    # ✅ MUST BE OUTSIDE ELSE
    skills = d.get("skills") or fallback_skills
    exp_min = int(d.get("exp_min") or fallback_exp[0])
    exp_max = int(d.get("exp_max") or fallback_exp[1])

    role = d.get("role", "").strip()
    if not role or role.lower() in ["unknown", "n/a", ""]:
        role = fallback_role

    return normalize_skills(skills[:8]), (exp_min, exp_max), role

except:
    return normalize_skills(fallback_skills[:8]), (fallback_exp[0], fallback_exp[1]), fallback_role
        exp_max = int(d.get("exp_max") or fallback_exp[1])

        role = d.get("role", "").strip()
        if not role or role.lower() in ["unknown", "n/a", ""]:
            role = fallback_role

        return normalize_skills(skills[:8]), (exp_min, exp_max), role  # ✅ normalized

    except:
        return normalize_skills(fallback_skills[:8]), fallback_exp, fallback_role


# ─────────────────────────────────────────
# SKILL NORMALIZATION
# ─────────────────────────────────────────
SKILL_SYNONYMS = {
    "communication": ["communication", "client handling", "presentation", "verbal"],
    "crm": ["crm", "salesforce", "hubspot"],
    "sales": ["sales", "b2b", "b2c", "negotiation", "target achievement", "client"],
    "lead generation": ["lead generation", "prospecting"],
    "field sales": ["field sales"],
    "excel": ["excel"],
    "python": ["python"],
    "sql": ["sql"],
}

def normalize_skills(skills):
    normalized = set()
    for skill in skills:
        s = skill.lower()
        for main, variants in SKILL_SYNONYMS.items():
            if any(v in s for v in variants):
                normalized.add(main)
    return list(normalized)


# ─────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────
def _score(required_skills, exp_range, candidate_skills, candidate_exp):

    req = normalize_skills(required_skills)
    cand = normalize_skills(candidate_skills)

    matched = [s for s in req if s in cand]
    missing = [s for s in req if s not in cand]

    skill_score = (len(matched) / len(req)) * 80 if req else 80

    exp_min, _ = exp_range
    exp_score = 20 if candidate_exp >= exp_min else 10

    total = round(skill_score + exp_score, 2)

    return min(total, 100), matched, missing


# ─────────────────────────────────────────
# ANALYZE
# ─────────────────────────────────────────
def analyze(jd_text, candidate_text, required_skills=None, exp_range=None, role=None):

    if required_skills is None:
        required_skills, exp_range, role = extract_requirements(jd_text)

    candidate_skills = normalize_skills(_fallback_skills(candidate_text))  # ✅ FIXED
    exp_match = re.search(r'(\d+)\s*year', candidate_text.lower())
    candidate_exp = int(exp_match.group(1)) if exp_match else 2

    score, matched, missing = _score(required_skills, exp_range, candidate_skills, candidate_exp)

    return {
        "match_score": score,
        "matched": matched,
        "missing": missing,
        "role": role or "General Role"
    }


# ─────────────────────────────────────────
# INTEREST
# ─────────────────────────────────────────
def interest_score(answer):
    ans = answer.lower()

    if "yes" in ans:
        return 75
    if "no" in ans:
        return 20
    return 50
def analyze_candidate(jd_text, candidate):
    return analyze(
        jd_text,
        " ".join(candidate.get("skills", [])) + f" {candidate.get('experience', 0)} years"
    )
