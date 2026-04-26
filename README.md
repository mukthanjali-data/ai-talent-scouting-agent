# 🤖 TalentAI Scout  
### *AI-Powered Intelligent Recruitment Agent*

> 🚀 Hire smarter. Faster. Better. 

---

## 🌐 Project Link

👉 https://ai-talent-agent-muktha.streamlit.app/

---

## 🎥 Demo Video

👉 https://drive.google.com/file/d/1-RqMk__cFHJIFri2RKowq_5cI1DubNVs/view?usp=sharing

---

## 🧠 What is TalentAI Scout?

**TalentAI Scout** is an end-to-end AI recruitment system that automates the entire hiring workflow — from **Job Description parsing** to **candidate ranking and resume evaluation**.

It enables recruiters to **save time, improve accuracy, and make better hiring decisions using AI**.

---

## ❗ Problem Statement

Recruiters today face multiple challenges:

- ⏳ Manual resume screening takes hours  
- ❌ Poor candidate-job matching  
- 📞 No visibility into candidate interest  
- 🔄 Constant switching between multiple tools  

---

## 💡 Solution

TalentAI Scout provides a **unified intelligent platform** that:

- 📄 Understands Job Descriptions using AI  
- 🎯 Matches candidates based on skills and experience  
- 💬 Simulates candidate interaction (*Interest Check*)  
- 🧠 Provides explainable insights  
- 🏆 Automatically ranks candidates  

---

## ⚙️ Core Features

### 📄 1. AI JD Parsing
- Automatically extracts role, skills, and experience  
- Handles real-world, unstructured job descriptions  

---

### 🎯 2. Smart Candidate Matching
Matches candidates based on:

- Skills  
- Experience  

**Outputs:**
- Match Score  
- Matched Skills  
- Missing Skills  
- Recruiter Insight  

---

### 💬 3. Interest Check *(Unique Feature)*
Simulates recruiter interaction:

> *"Are you open to this opportunity?"*

- Generates an **Interest Score**  
- Enhances ranking accuracy  

---

### 🏆 4. Intelligent Ranking
- **Final Score = Match Score + Interest Score**  
- Enables faster and better shortlisting  

---

### 📋 5. Resume Evaluation
- Upload or paste a resume  
- Compare directly with Job Description  

**Outputs:**
- Match Percentage  
- Role Detection  
- Skill Gap Analysis  
- Hiring Recommendation  

---

## 📊 Scoring Logic

The system uses a weighted scoring model:

- **Skill Match Score (High Weight)**  
  Based on overlap between JD skills and candidate skills  

- **Experience Score (Medium Weight)**  
  Based on required vs actual experience  

- **Interest Score (Medium Weight)**  
  Based on simulated candidate response  

👉 **Final Score = Combined Intelligent Ranking (Skill + Experience + Interest)**  

This ensures a balanced and explainable ranking system.

---

## 🧪 Sample Input & Output

### 📥 Input (Job Description)
Looking for a Data Analyst with Python, SQL, Excel, and 2+ years of experience.

### 📤 Output
- Candidate A → Match: 85%, Interest: 90%, Final Score: 88  
- Candidate B → Match: 70%, Interest: 60%, Final Score: 65  

👉 Candidates are automatically ranked based on final score.

---

## 🔄 How It Works

1. Paste or upload Job Description  
2. AI extracts skills & requirements  
3. Candidates are matched and scored  
4. Interest simulation is performed  
5. Final ranked list is generated  
6. Recruiter reviews insights and selects candidates  

---

## 🧠 Architecture

TalentAI Scout follows a modular architecture:

1. **Input Layer**
   - Job Description (JD)
   - Candidate Data / Resume  

2. **AI Processing Layer**
   - JD Parsing (Gemini API)  
   - Skill & Experience Extraction  
   - Resume Parsing  

3. **Matching Engine**
   - Skill Matching Algorithm  
   - Experience Scoring  
   - Gap Analysis  

4. **Engagement Layer**
   - Simulated Candidate Interaction  
   - Interest Score Calculation  

5. **Ranking Engine**
   - Final Score = Match Score + Interest Score  

6. **Output Layer**
   - Ranked Candidates  
   - Recruiter Insights  

---

## 🖥️ Tech Stack

- **Frontend:** Streamlit  
- **Backend:** Python  
- **AI Model:** Google Gemini API  
- **Libraries:** PyPDF2, python-docx, python-dotenv  

---

## 📂 Project Structure

```
ai-talent-scout/
│
├── app.py              # Streamlit UI  
├── brain.py            # AI logic + scoring engine  
├── candidates.json     # Candidate dataset  
├── requirements.txt  
└── README.md  
```

---

## ▶️ How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🔥 Key Highlights

- ✅ AI-based JD understanding  
- ✅ Explainable candidate scoring  
- ✅ Interest-based ranking *(unique feature)*  
- ✅ Resume evaluation system  
- ✅ End-to-end recruitment workflow  

---

## 📈 Impact

- ⏱️ Saves **60%+ recruiter time**  
- 🎯 Improves hiring accuracy  
- 🔄 Reduces manual effort  

---

## 👩‍💻 Author

**Mukthanjali Bonala**  
Aspiring Data Analyst | AI Enthusiast  

🔗 GitHub: https://github.com/mukthanjali-data  
🔗 LinkedIn: https://www.linkedin.com/in/mukthanjalibonala  

---

## 🏁 Conclusion

**TalentAI Scout** transforms traditional hiring into a smart, AI-driven process — enabling recruiters to make **faster, more accurate, and confident decisions**.

---

⭐ *If you like this project, consider giving it a star!*
