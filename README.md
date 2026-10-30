# Smart Resume & Interview Platform

An AI-powered Streamlit suite that helps students and job seekers get job-ready.

## Modules (in `main/`)
1. **Resume Analyzer** (`module1.py`): Gemini-based score, ATS check, keywords, PDF report
2. **Mock Interview Chatbot** (`module2.py`): practice questions with AI feedback and rating
3. **Resume Evolution Tracker** (`module3.py`): compare two resume versions (TF-IDF + diff)
4. **Video Pitch Review** (`module4.py`): body-language analysis (OpenCV) + Gemini coaching

## Run
```bash
pip install -r requirements.txt
cd main
# copy .streamlit/secrets.toml.example to .streamlit/secrets.toml and add your Gemini API key
streamlit run main_app.py
```

Built for the Seva Innovation Challenge 2026.
