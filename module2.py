import streamlit as st
import requests
import json
# import pandas as pd
from fpdf import FPDF # Import FPDF

# --- Securely load Gemini API Key from Streamlit secrets ---
API_KEY = st.secrets["gemini"]["api_key"]

# --- Interview Questions ---
interview_questions = [
    "Tell me about yourself.",
    "What are your strengths and weaknesses?",
    "Why do you want to work for our company?",
    "Where do you see yourself in five years?",
    "Describe a challenging situation you faced at work and how you overcame it."
]

# --- Gemini API Call Function ---
def get_feedback_and_rating(question, answer):
    prompt = f"""
    Given the interview question: "{question}" and the candidate's answer: "{answer}",
    provide constructive feedback and a rating (1-10). Justify the rating briefly.
    Return a JSON with two keys: 'feedback' and 'rating'.
    """

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "feedback": {"type": "STRING"},
                    "rating": {"type": "NUMBER"}
                },
                "propertyOrdering": ["feedback", "rating"]
            }
        }
    }

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        result = response.json()

        if result.get('candidates') and result['candidates'][0]['content'].get('parts'):
            json_string = result['candidates'][0]['content']['parts'][0]['text']
            try:
                return json.loads(json_string)
            except json.JSONDecodeError:
                return {"feedback": json_string, "rating": "N/A"}
        else:
            return {"feedback": "Could not understand the response.", "rating": "N/A"}

    except Exception as e:
        st.error(f"API error: {e}")
        return {"feedback": "Failed to get response from Gemini API.", "rating": "N/A"}

# --- PDF Generation Function ---
def create_pdf(data):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Mock Interview Feedback", 0, 1, "C")
    pdf.ln(10)

    for i, result in enumerate(data):
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 10, f"Q{i + 1}: {result['question']}")
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 10, f"Your Answer: {result['answer']}")
        pdf.multi_cell(0, 10, f"Feedback: {result['feedback']}")
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(0, 10, f"Rating: {result['rating']}/10")
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin1') # Return bytes

# --- UI Styling and Layout ---
st.set_page_config(page_title="Mock Interview Chatbot", layout="centered")

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(to right, #2563eb, #6d28d9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stButton > button {
        background: linear-gradient(to right, #3b82f6, #8b5cf6);
        color: white;
        font-weight: bold;
        padding: 0.75rem 2rem;
        border-radius: 9999px;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton > button:hover {
        transform: scale(1.05);
        background: linear-gradient(to right, #2563eb, #6d28d9);
    }
    .question-box {
        background-color: #eff6ff;
        border-left: 5px solid #60a5fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        font-size: 1.25rem;
        color: #1f2937;
    }
    .feedback-box {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .feedback-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
    }
    .rating-text {
        font-size: 1.125rem;
        font-weight: bold;
        color: #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">Mock Interview Chatbot</h1>', unsafe_allow_html=True)

# --- State Management ---
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'answer_results' not in st.session_state:
    st.session_state.answer_results = []
if 'interview_ended' not in st.session_state:
    st.session_state.interview_ended = False
if 'candidate_answer' not in st.session_state:
    st.session_state.candidate_answer = ""

# --- Interview Flow ---
if not st.session_state.interview_ended:
    question = interview_questions[st.session_state.current_question_index]

    st.markdown(f'<div class="question-box">Q{st.session_state.current_question_index + 1}: {question}</div>', unsafe_allow_html=True)

    # Progress bar
    progress = (st.session_state.current_question_index + 1) / len(interview_questions)
    st.progress(progress)

    st.session_state.candidate_answer = st.text_area(
        "Your Answer:",
        value=st.session_state.candidate_answer,
        height=180,
        key=f"answer_{st.session_state.current_question_index}"
    )

    if st.button("Submit Answer"):
        if st.session_state.candidate_answer.strip() == "":
            st.warning("Please write an answer before submitting.")
        else:
            with st.spinner("Analyzing your answer..."):
                feedback_data = get_feedback_and_rating(question, st.session_state.candidate_answer)

            st.session_state.answer_results.append({
                "question": question,
                "answer": st.session_state.candidate_answer,
                "feedback": feedback_data["feedback"],
                "rating": feedback_data["rating"]
            })

            st.session_state.candidate_answer = ""

            if st.session_state.current_question_index < len(interview_questions) - 1:
                st.session_state.current_question_index += 1
                st.rerun()
            else:
                st.session_state.interview_ended = True
                st.rerun()

# --- Results Summary ---
else:
    st.markdown('<h2 class="text-3xl font-bold text-green-700 text-center mb-6">Interview Complete!</h2>', unsafe_allow_html=True)

    for i, result in enumerate(st.session_state.answer_results):
        st.markdown(f'<div class="feedback-box mb-6">', unsafe_allow_html=True)
        st.markdown(f'<h3 class="feedback-title">Q{i + 1}: "{result["question"]}"</h3>', unsafe_allow_html=True)
        st.markdown(f'<p><strong>Your Answer:</strong> {result["answer"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p><strong>Feedback:</strong> {result["feedback"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="rating-text">Rating: {result["rating"]}/10</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Download as PDF
    if st.button("Download Feedback as PDF"):
        pdf_output = create_pdf(st.session_state.answer_results)
        st.download_button(
            label="Download PDF",
            data=pdf_output,
            file_name="interview_feedback.pdf",
            mime="application/pdf"
        )

    if st.button("Restart Interview"):
        st.session_state.current_question_index = 0
        st.session_state.answer_results = []
        st.session_state.interview_ended = False
        st.session_state.candidate_answer = ""
        st.rerun()