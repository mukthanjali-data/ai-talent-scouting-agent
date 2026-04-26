import os
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Fallback logic for stability ---
def _fallback_skills(text):
    known = ["python","sql","excel","power bi","tableau","machine learning","nlp","java","javascript","react","node.js","aws","docker","kubernetes","mongodb","postgresql","data analysis","communication","leadership","project management","sales","crm","lead generation","negotiation","field sales","digital marketing","seo","social media","hr","recruitment","talent acquisition","business analysis","stakeholder management","operations","campaign management","statistics","data visualization","reporting","target achievement","client handling","screening","interviewing","b2b","b2c","inside sales","outbound","inbound","cold calling","account management","pipeline management","forecasting"]
    tl = text.lower()
    return [s for s in known if s in tl]

def _fallback_exp(text):
    for pat in [r'(\d+)\+?\s*years?\s*of\s*experience', r'(\d+)\+?\s*years?\s*experience', r'minimum\s*(\d+)\+?\s*years?', r'(\d+)\s*[-–]\s*(\d+)\s*years?', r'(\d+)\+?\s*years?']:
        m = re.search(pat, text.lower())
        if m:
            v = int(m.group(1))
            v2 = int(m.group(2)) if len(m.groups()) > 1 and m.group(2) else v + 2
            return (v, v2)
    return (2, 5)

def _fallback_role(text):
    tl = text.lower()
    roles = [("Sales Executive", ["sales executive"]), ("Data Analyst", ["data analyst"]), ("HR Executive", ["hr"]), ("Software Engineer", ["software"])]
    for name, keys in roles:
        if any(k in tl for k in keys): return name
    return "Candidate"

# --- Core AI Functions ---
def extract_requirements(jd_text):
    prompt = f"Extract Job Title, Top 8 Skills, and Exp Min/Max from this JD. Return ONLY JSON: {{'role': 'string', 'skills': [], 'exp_min': int, 'exp_max': int}}. JD: {jd_text[:2000]}"
    try:
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt, config={"response_mime_type": "application/json"})
        d = json.loads(response.text)
        return d.get("skills")[:8], (d.get("exp_min", 2), d.get("exp_max", 5)), d.get("role", "Role")
    except:
        return _fallback_skills(jd_text)[:8], _fallback_exp(jd_text), _fallback_role(jd_text)

def _score(req_skills, exp_range, cand_skills, cand_exp):
    matched = [s for s in cand_skills if s.lower() in [r.lower() for r in req_skills]]
    missing = [s for s in req_skills if s.lower() not in [c.lower() for c in cand_skills]]
    
    # Skill points (70)
    skill_pts = (len(matched) / len(req_skills) * 70) if req_skills else 70
    
    # Experience points (20) - Graduated scoring
    exp_min = exp_range[0]
    if cand_exp >= exp_min: exp_pts = 20
    elif cand_exp >= exp_min * 0.75: exp_pts = 16
    elif cand_exp >= exp_min * 0.5: exp_pts = 12
    else: exp_pts = max((cand_exp/exp_min * 20) if exp_min > 0 else 10, 6)
    
    # Bonus points (10)
    bonus = min((cand_exp - exp_min) * 1.2, 10.0) if cand_exp > exp_min else 0
    
    total = round(min(100.0, skill_pts + exp_pts + bonus), 2)
    return total, matched, missing

def _ai_note(role, req_skills, name, cand_skills, score):
    prompt = f"Write a 2-sentence hiring note for {name} for {role}. Match Score: {score}%. Mention specific skills. Be direct."
    try:
        res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        return res.text.strip()
    except:
        return f"{name} shows a fit of {score}% with relevant experience."

def analyze_candidate(jd_text, candidate, req_skills=None, exp_range=None, role=None):
    if not req_skills: req_skills, exp_range, role = extract_requirements(jd_text)
    score, matched, missing = _score(req_skills, exp_range, candidate["skills"], candidate["experience"])
    note = _ai_note(role, req_skills, candidate["name"], candidate["skills"], score)
    return {
        "name": candidate["name"], "match_score": score, "matched": matched, "missing": missing, 
        "recruiter_note": note, "role": role, "experience": candidate["experience"],
        "location": candidate.get("location", "N/A"), "notice_period": candidate.get("notice_period", "N/A"),
        "expected_ctc": candidate.get("expected_ctc", "N/A")
    }

def analyze(jd_text, cand_text):
    req_skills, exp_range, role = extract_requirements(jd_text)
    cand_skills = _fallback_skills(cand_text)
    exp_match = re.search(r'(\d+)\s*year', cand_text.lower())
    cand_exp = int(exp_match.group(1)) if exp_match else 2
    return analyze_candidate(jd_text, {"name": "Candidate", "skills": cand_skills, "experience": cand_exp}, req_skills, exp_range, role)

def ai_assess_interest(name, q, a, history):
    prompt = f"Assess interest delta (-20 to 20) and a natural follow-up for {name}. Answer: {a}. Return JSON: {{'interest_delta': int, 'ai_followup': 'string'}}"
    try:
        r = client.models.generate_content(model="gemini-1.5-flash", contents=prompt, config={"response_mime_type": "application/json"})
        return json.loads(r.text)
    except:
        return {"interest_delta": 5, "ai_followup": "Understood, thank you!"}

def interest_score(a):
    prompt = f"Rate candidate interest 0-100 for: '{a}'. Return JSON: {{'score': int}}"
    try:
        r = client.models.generate_content(model="gemini-1.5-flash", contents=prompt, config={"response_mime_type": "application/json"})
        return int(json.loads(r.text).get("score", 50))
    except: return 50
