# 🤖 TalentAI Scout
### AI-Powered Talent Scouting & Engagement Agent
> Built for **Catalyst Hackathon** by Deccan AI | Solo submission by **Mukthanjali Bonala**

---

## 🚀 Overview

TalentAI Scout is an end-to-end AI recruitment agent that eliminates manual hiring grunt work. Give it a Job Description — it parses requirements, discovers matching candidates, engages them conversationally to assess genuine interest, and outputs a ranked shortlist scored on two dimensions: **Match Score** and **Interest Score**.

No decks. No mockups. Real, running code.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📄 **JD Parsing** | Upload PDF/DOCX/TXT or paste — AI extracts skills, experience range, and role |
| 🧠 **AI Matching** | Gemini AI scores every candidate against JD requirements |
| 💬 **Conversational Outreach** | Multi-turn AI chat simulates recruiter-candidate engagement |
| 📊 **Dual Scoring** | Separate Match Score + Interest Score → combined Final Score |
| 🔍 **Explainability** | Every result shows matched skills, missing skills, and AI recruiter insight |
| 🎯 **Resume Evaluator** | Upload any resume to instantly evaluate against a JD |
| 🌐 **Dark UI** | Professional recruiter-grade Streamlit interface |

---

## 🧠 How It Works

```
Job Description (text / PDF / DOCX)
         ↓
   AI JD Parser (Gemini)
   → Extracts: skills, experience range, role title
         ↓
   Candidate Matching Engine
   → Scores each candidate: skill overlap + experience fit + bonuses
         ↓
   AI Recruiter Insight
   → Gemini generates 2-sentence fit analysis per candidate
         ↓
   Conversational Outreach Agent
   → Multi-turn chat, Gemini assesses interest delta per response
         ↓
   Ranked Shortlist
   → Final Score = 65% Match + 35% Interest
```

---

## 📊 Scoring Logic

### Match Score (0–100%)

| Component | Weight | Description |
|---|---|---|
| Skill Match Ratio | 70 pts | Matched skills ÷ Required skills |
| Experience Score | 20 pts | Candidate exp vs required range (graduated) |
| Experience Bonus | 0–10 pts | Extra years above minimum requirement |
| **Total** | **100 pts** | Unique score per candidate |

**Graduated Experience Scoring:**
- Meets or exceeds requirement → 100%
- 75–99% of requirement → 80%
- 50–74% of requirement → 60%
- Below 50% → proportional (min 30%)

### Interest Score (0–100%)

- Starts at **50%** (neutral baseline)
- Updated after each chat response by Gemini AI
- Gemini analyzes sentiment and assigns delta (−20 to +20) per answer
- 5 questions covering: openness, relocation, salary, notice period, motivation

| Sentiment | Delta |
|---|---|
| Very enthusiastic | +15 to +20 |
| Open / willing | +5 to +10 |
| Vague / unclear | 0 to +5 |
| Hesitant | −10 to −5 |
| Negative | −20 to −10 |

### Final Score

```
Final Score = (0.65 × Match Score) + (0.35 × Interest Score)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| AI Engine | Google Gemini 1.5 Flash |
| File Parsing | PyPDF2, python-docx |
| Language | Python 3.10+ |
| Config | python-dotenv |

---

## 📁 Project Structure

```
talentai-scout/
├── app.py              # Streamlit UI — tabs, chat, results
├── brain.py            # AI engine — parsing, scoring, insights
├── candidates.json     # 20 candidate profiles across domains
├── requirements.txt    # Dependencies
├── .env                # API key (not committed)
└── README.md
```

---

## ▶️ Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/mukthanjali-data/ai-talent-scouting-agent
cd ai-talent-scouting-agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up API key
Create a `.env` file:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```
Get a free key at: https://aistudio.google.com/app/apikey

### 4. Run
```bash
streamlit run app.py
```
Open: http://localhost:8501

---

## 🧪 Sample Input

```
We are looking for a Senior Data Analyst with 3+ years of experience.
Required skills: Python, SQL, Power BI, Tableau, Excel.
Knowledge of Machine Learning is a plus.
Location: Hyderabad. CTC: Up to 12 LPA.
```

## 📈 Sample Output

```
🥇 Arun Tiwari    — Final: 89.3% | Match: 96.0% | Interest: 75%
🥈 Suresh Babu    — Final: 79.1% | Match: 87.2% | Interest: 62%
🥉 Deepa Iyer     — Final: 74.5% | Match: 83.5% | Interest: 55%
#4 Akash Patel    — Final: 68.2% | Match: 76.0% | Interest: 50%
...
```

Each result includes:
- Match Score with skill breakdown
- Missing skills highlighted
- AI recruiter insight (2 sentences)
- Conversational interest assessment
- Final ranked score

---

## 🗂️ Candidate Database

20 diverse candidates across domains:

| Domain | Candidates |
|---|---|
| Data & Analytics | Arun Tiwari, Deepa Iyer, Akash Patel, Suresh Babu, Arjun Mehta, Sneha Verma, Divya Krishnan, Kavitha Menon |
| Sales | Rohit Sharma, Vikram Singh, Priya Nair |
| Marketing | Rakesh Singh, Anjali Verma |
| HR & Talent | Manish Yadav, Pooja Sharma |
| Business Analysis | Karthik Reddy, Neha Joshi |
| ML / AI | Rahul Gupta |
| Operations | Suresh Kumar, Meena Kumari |

---

## 🔌 API & Tools Used

| Tool | Purpose | Tier |
|---|---|---|
| Google Gemini 1.5 Flash | JD parsing, matching insight, interest assessment | Free |
| Streamlit | Web UI | Free |
| PyPDF2 | PDF resume/JD parsing | Free |
| python-docx | DOCX resume/JD parsing | Free |

> All tools used are within free/trial tiers. No paid API credits required.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│                  app.py (UI)                  │
│  Tab 1: Find & Rank    Tab 2: Evaluate Resume │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│                 brain.py (Engine)             │
│                                              │
│  extract_requirements()  ←→  Gemini AI       │
│  analyze_candidate()     ←→  Score Engine    │
│  analyze()               ←→  Free-text mode  │
│  ai_assess_interest()    ←→  Gemini AI       │
│  interest_score()        ←→  Gemini AI       │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│           candidates.json                    │
│   20 profiles: skills, exp, location, CTC   │
└──────────────────────────────────────────────┘
```

---

## 📐 Design Decisions & Trade-offs

| Decision | Reason |
|---|---|
| Gemini 1.5 Flash | Fast, free tier, reliable JSON output |
| JD parsed once, reused | Prevents inconsistent scoring across candidates |
| Graduated exp scoring | More realistic than binary pass/fail |
| Interest starts at 50% | Neutral baseline — neither penalizes nor rewards by default |
| Skills capped at 8 from JD | Prevents soft skills from diluting technical match |
| Fallback scoring | App works even if Gemini API fails |

---

## 🔮 Future Improvements

- LinkedIn / Naukri live candidate sourcing
- Resume PDF bulk upload and parsing
- Email outreach automation
- Advanced NLP-based semantic skill matching
- ML model trained on historical hiring data
- Dashboard analytics for recruiters

---

## 👩‍💻 Author

**Mukthanjali Bonala**
Built solo for Catalyst Hackathon — Deccan AI, April 2026

---
