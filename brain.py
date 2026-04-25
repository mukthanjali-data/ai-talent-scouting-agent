from google import genai
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# ---------------------------
# 🔹 Fallback (Non-AI)
# ---------------------------
def extract_skills(jd_text):
    skills_list = ["Python", "SQL", "Excel", "Power BI", "Tableau", "Machine Learning"]
    found = [s for s in skills_list if s.lower() in jd_text.lower()]

    # Smart fallback
    if not found:
        if "data analyst" in jd_text.lower():
            return ["Python", "SQL", "Excel"]
        return ["Python"]

    return found


def extract_experience(jd_text):
    match = re.search(r'(\d+)\s*year', jd_text.lower())
    return int(match.group(1)) if match else 0


# ---------------------------
# 🤖 AI: Extract JD Requirements
# ---------------------------
def ai_extract_requirements(jd_text):
    prompt = f"""
    Extract required skills and years of experience from this job description.

    Return ONLY JSON:
    {{
        "skills": [],
        "experience": int
    }}

    Job Description:
    {jd_text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        data = json.loads(response.text)

        skills = data.get("skills", [])
        exp = data.get("experience", 0)

        # fallback safety
        if not skills:
            skills = extract_skills(jd_text)

        return skills, exp

    except Exception:
        return extract_skills(jd_text), extract_experience(jd_text)


# ---------------------------
# 🤖 AI: Generate Recruiter Insight
# ---------------------------
def ai_generate_reason(jd_text, candidate, match_score):
    prompt = f"""
    You are an expert recruiter.

    Job Description:
    {jd_text}

    Candidate Profile:
    {candidate}

    Match Score: {match_score}

    Explain in 1-2 short lines why this candidate is a good or bad fit.
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text.strip()

    except Exception:
        return f"{candidate['name']} shows moderate alignment with the job."


# ---------------------------
# 🎯 MAIN FUNCTION
# ---------------------------
def analyze_job_and_match(jd_text, candidate):
    try:
        # 🔥 AI-powered JD understanding
        required_skills, required_exp = ai_extract_requirements(jd_text)

        candidate_skills = candidate["skills"]
        candidate_exp = candidate["experience"]

        matched = list(set(candidate_skills) & set(required_skills))
        missing = list(set(required_skills) - set(candidate_skills))

        # 🎯 Skill score
        if required_skills:
            skill_score = len(matched) / len(required_skills)
        else:
            skill_score = 1

        # 🎯 Experience score
        if required_exp > 0:
            exp_score = min(candidate_exp / required_exp, 1)
        else:
            exp_score = 1

        # 🎯 Final match score
        match_score = round((0.7 * skill_score + 0.3 * exp_score) * 100, 2)

        # 🤖 AI reasoning
        note = ai_generate_reason(jd_text, candidate, match_score)

        return {
            "match_score": match_score,
            "matched_skills": matched if matched else ["None"],
            "missing_skills": missing,
            "recruiter_note": note
        }

    except Exception as e:
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "recruiter_note": f"Error: {str(e)}"
        }