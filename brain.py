import re

# ---------- EXPERIENCE ----------
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


# ---------- JD PARSER ----------
def extract_requirements(jd):
    jd = jd.lower()

    if "sales" in jd:
        role = "Sales Executive"
        skills = ["sales", "communication", "crm"]

    elif "data" in jd:
        role = "Data Analyst"
        skills = ["python", "sql", "excel", "power bi"]

    elif "business" in jd:
        role = "Business Analyst"
        skills = ["excel", "sql", "analysis"]

    else:
        role = "General Role"
        skills = ["communication"]

    exp = extract_experience(jd)

    return skills, exp, role


# ---------- RESUME PARSER ----------
def extract_candidate_profile(text):
    text = text.lower()
    skills = []

    # direct match
    keywords = ["sales", "crm", "python", "sql", "excel", "power bi"]
    for k in keywords:
        if k in text:
            skills.append(k)

    # smart inference
    if any(w in text for w in ["client", "customer", "relationship", "negotiation", "handling"]):
        skills.append("communication")

    matches = re.findall(r'(\d+)\+?\s*year', text)
    exp = sum(map(int, matches)) if matches else 1

    return {
        "skills": list(set(skills)),
        "experience": exp
    }


# ---------- SCORING ----------
def calculate_score(candidate, req_skills, req_exp):
    matched = [s for s in candidate["skills"] if s in req_skills]

    skill_score = (len(matched) / len(req_skills)) * 70

    min_exp, max_exp = req_exp

    if candidate["experience"] < min_exp:
        exp_score = 10
    elif min_exp <= candidate["experience"] <= max_exp:
        exp_score = 30
    else:
        exp_score = 20

    total = skill_score + exp_score

    return round(min(total, 100), 2), matched


# ---------- FINAL ----------
def analyze(jd, resume_text):
    req_skills, req_exp, role = extract_requirements(jd)
    candidate = extract_candidate_profile(resume_text)

    score, matched = calculate_score(candidate, req_skills, req_exp)

    missing = [s for s in req_skills if s not in matched]

    if score >= 75:
        decision = "Recommended"
    elif score >= 55:
        decision = "Consider"
    else:
        decision = "Reject"

    reason = f"""
    Candidate matches {len(matched)}/{len(req_skills)} skills.
    Experience: {candidate['experience']} years.
    Missing: {', '.join(missing)}
    """

    return {
        "score": score,
        "decision": decision,
        "matched": matched,
        "missing": missing,
        "reason": reason,
        "role": role
    }
