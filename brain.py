import re

# ---------- FALLBACK SKILLS ----------
def extract_skills(text):
    text = text.lower()

    skills_map = {
        "sales": ["sales", "lead", "revenue", "client"],
        "crm": ["crm", "salesforce", "hubspot"],
        "communication": ["communication", "presentation", "negotiation"],
        "python": ["python"],
        "sql": ["sql"],
        "excel": ["excel"],
        "power bi": ["power bi"],
        "tableau": ["tableau"],
        "machine learning": ["machine learning"]
    }

    found = []
    for skill, keywords in skills_map.items():
        if any(k in text for k in keywords):
            found.append(skill)

    return found


# ---------- EXPERIENCE ----------
def extract_experience(text):
    match = re.search(r'(\d+)\s*year', text.lower())
    return int(match.group(1)) if match else 2


# ---------- ROLE ----------
def detect_role(text):
    text = text.lower()

    if "data" in text:
        return "Data Analyst"
    if "sales" in text:
        return "Sales Executive"
    if "hr" in text:
        return "HR"
    
    return "General Role"


# ---------- REQUIREMENTS ----------
def extract_requirements(jd):
    skills = extract_skills(jd)
    exp = extract_experience(jd)
    role = detect_role(jd)

    return skills, (exp, exp+2), role


# ---------- SCORING ----------
def analyze(jd_text, resume_text):

    req_skills, exp_range, role = extract_requirements(jd_text)

    cand_skills = extract_skills(resume_text)
    cand_exp = extract_experience(resume_text)

    matched = [s for s in cand_skills if s in req_skills]
    missing = [s for s in req_skills if s not in cand_skills]

    skill_score = (len(matched) / max(len(req_skills),1)) * 70
    exp_score = 30 if cand_exp >= exp_range[0] else 15

    total = round(skill_score + exp_score, 2)

    return {
        "match_score": total,
        "matched": matched,
        "missing": missing,
        "role": role,
        "experience": cand_exp
    }


# ---------- INTEREST ----------
def interest_score(answer):
    a = answer.lower()

    if "yes" in a:
        return 80
    if "no" in a:
        return 20
    if "maybe" in a:
        return 50
    return 40
