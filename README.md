# 🤖 TalentAI Scout
### AI-Powered Talent Scouting & Engagement Agent
> Built for **Catalyst Hackathon** | Solo submission by **Mukthanjali Bonala**

TalentAI Scout is an end-to-end recruitment agent that uses **Google Gemini 1.5 Flash** to find, rank, and engage candidates. It transforms a static candidate database into a dynamic, interactive shortlist.

## 🚀 How to Run
1. **Clone & Install:**
   ```bash
   pip install -r requirements.txt
   Setup API Key: Add GOOGLE_API_KEY to your .env file.

Launch: streamlit run app.py

✨ Tech Stack
LLM: Gemini 1.5 Flash (for JD Parsing, Insights, and Sentiment Analysis)

Frontend: Streamlit (Custom Dark Theme)

Data: JSON-based candidate store

🧠 Scoring System
Match Score (65%): Skills match (70pts), Experience match (20pts), Seniority bonus (10pts).

Interest Score (35%): Starts at 50%, delta updated (+/-) via AI analysis of candidate chat responses.
