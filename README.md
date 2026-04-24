# 🤖 AI Talent Scouting & Engagement Agent

## 🚀 Overview
This project is an AI-powered recruitment assistant that helps recruiters automatically find, evaluate, and rank candidates based on job requirements and engagement likelihood.

---

## 🔧 Features

- 📄 Job Description parsing (skills & experience extraction)
- 🧠 Candidate matching with explainable scoring
- 💬 Simulated candidate interest scoring
- 🏆 Final ranking based on Match Score + Interest Score
- 🌐 Interactive web app using Streamlit

---

## 🧠 How It Works

1. User inputs a Job Description
2. System extracts required skills and experience
3. Matches candidates from dataset
4. Calculates:
   - ✅ Match Score (skills + experience)
   - 💬 Interest Score (simulated engagement)
   - 🏆 Final Score (70% match + 30% interest)
5. Outputs ranked candidates with explanations

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

## 📊 Sample Output

- Ranked candidates
- Match Score
- Interest Score
- Final Score
- Explanation for each candidate

## 📌 Notes

Interest score is simulated to represent candidate engagement behavior in absence of real conversational APIs.

## 👩‍💻 Author

Mukthanjali Bonala
