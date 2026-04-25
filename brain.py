import re

# -------- EXPERIENCE --------
def extract_experience(text):
    text = text.lower()

    m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*year', text)
    if m:
        return (int(m.group(1)), int(m.group(2)))

    m = re.search(r'(\d+)\+?\s*year', text)
    if m:
        val = int(m.group(1))
        return (val, val + 2)

    return (1, 3)

# -------- JD PARSER --------
def extract_requirements(jd):
    jd = jd.lower()

    if "sales" in jd:
        role = "Sales Executive"
        skills = ["sales", "communication", "crm"]

    elif "data" in jd:
        role = "Data Analyst"
        skills = ["python", "sql", "excel", "power bi"]

    else:
        role = "General Role"
        skills = ["communication"]

    exp = extract_experience(jd)

    return skills, exp, role

# -------- RESUME PARSER --------
def extract_candidate_profile(text):
    text = text.lower()
    skills = []

    if "sales" in text:
        skills.append("sales")

    if "crm" in text or "salesforce" in text:
        skills.append("crm")

    if "python" in text:
        skills.append("python")

    if "sql" in text:
        skills.append("sql")

    if "excel" in text:
        skills.append("excel")

    if any(w in text for w in [
        "client", "customer", "relationship",
        "negotiation", "presentation"
    ]):
        skills.append("communication")

    matches = re.findall(r'(\d+)\+?\s*year', text)
    exp = sum(map(int, matches)) if matches else 1

    return {
        "skills": list(set(skills)),
        "experience": exp
    }

# -------- MATCH SCORE --------
def match_score(candidate, req_skills, req_exp):
    matched = [s for s in candidate["skills"] if s in req_skills]

    skill_score = (len(matched) / len(req_skills)) * 70

    min_exp, max_exp = req_exp

    if candidate["experience"] < min_exp:
        exp_score = 10
    elif min_exp <= candidate["experience"] <= max_exp:
        exp_score = 30
    else:
        exp_score = 20

    return round(skill_score + exp_score, 2), matched

# -------- INTEREST SCORE --------
def interest_score(answer):
    a = answer.lower()
    if "yes" in a:
        return 90
    elif "maybe" in a:
        return 60
    else:
        return 30

# -------- FINAL ANALYSIS --------
def analyze(jd, resume_text):
    req_skills, req_exp, role = extract_requirements(jd)
    candidate = extract_candidate_profile(resume_text)

    m_score, matched = match_score(candidate, req_skills, req_exp)
    missing = [s for s in req_skills if s not in matched]

    return {
        "match_score": m_score,
        "matched": matched,
        "missing": missing,
        "role": role
    }
