# 🤖 AI Talent Scouting & Engagement Agent

## 🚀 Overview
An AI-powered recruitment assistant that automates candidate discovery, matching, and engagement scoring.  
Given a Job Description (JD), the system extracts required skills and experience, evaluates candidates, and returns a ranked shortlist with clear, explainable scores.

---

## ✨ Key Features

- 📄 JD Parsing: Extracts required skills and experience from job descriptions  
- 🧠 Candidate Matching: Scores candidates based on skill and experience alignment  
- 💬 Interest Scoring (Simulated): Represents candidate engagement level  
- 🏆 Final Ranking: Combines Match Score (70%) + Interest Score (30%)  
- 🔍 Explainability: Shows matched skills and reasoning  
- 🌐 Interactive UI: Built using Streamlit  

---

## 🧠 How It Works

1. User inputs a Job Description  
2. System extracts required skills and experience  
3. Matches candidates from dataset  
4. Calculates:
   - Match Score (skills + experience)
   - Interest Score (simulated)
   - Final Score (70% match + 30% interest)
5. Outputs ranked candidates with explanation  

---

## 📊 Scoring Logic

| Metric           | Description                                      |
|------------------|--------------------------------------------------|
| Match Score      | Skills + experience alignment (0–100%)           |
| Interest Score   | Simulated engagement likelihood (50–100)         |
| Final Score      | 70% Match + 30% Interest                         |

---

## 🛠️ Tech Stack

- Python  
- Streamlit  
- JSON  

---

## ▶️ Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py

## Open in browser:
http://localhost:8501

## 🧪 Sample Input

Looking for Data Analyst with Python, SQL, Excel and 2 years experience

📈 Sample Output
- Ranked candidates
- Match Score
- Interest Score
- Final Score
- Matched Skills
- Explanation

## 📌 Design Choices & Assumptions

- Interest score is simulated to represent candidate engagement behavior
- Skill matching uses keyword-based approach
- Experience scoring is capped at 100%

## 🔮 Future Improvements

- Real candidate sourcing integration
- AI-based JD parsing using NLP/LLMs
- Chat-based candidate interaction
- Resume parsing (PDF support)
- Advanced ML-based ranking

## 👩‍💻 Author

Mukthanjali Bonala

## 📎 Notes

This project focuses on end-to-end functionality, explainability, and usability within hackathon constraints.
