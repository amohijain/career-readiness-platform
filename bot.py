import streamlit as st
import requests
import json
import os

# Set your Gemini API key from environment variables or Streamlit secrets
# It's highly recommended to use Streamlit secrets for production
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable or use Streamlit secrets.")
    st.stop()

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
    """
    Calls the Gemini API to get feedback and a numerical rating for an answer.
    """
    if not API_KEY:
        st.error("API key is not set. Cannot get feedback.")
        return {"feedback": "API key not configured.", "rating": "N/A"}

    prompt = f"Given the interview question: \"{question}\" and the candidate's answer: \"{answer}\", please provide constructive feedback on the answer and a numerical rating from 1 to 10 (1 being very poor, 10 being excellent). Focus on clarity, relevance, completeness, and confidence. The response should be in JSON format with 'feedback' (string) and 'rating' (number) keys."

    chat_history = [{"role": "user", "parts": [{"text": prompt}]}]

    payload = {
        "contents": chat_history,
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
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        result = response.json()

        if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
            json_string = result['candidates'][0]['content']['parts'][0]['text']
            parsed_json = json.loads(json_string)
            return parsed_json
        else:
            st.error("Unexpected API response structure or no content.")
            return {"feedback": "Could not generate feedback due to unexpected API response.", "rating": "N/A"}

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to Gemini API: {e}")
        return {"feedback": "Failed to connect to API.", "rating": "N/A"}
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse API response: {e}")
        return {"feedback": "Invalid API response format.", "rating": "N/A"}
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return {"feedback": "An unknown error occurred.", "rating": "N/A"}

# --- Streamlit UI Components ---
st.set_page_config(page_title="Interview Chatbot", layout="centered")

st.markdown(
    """
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
    .stTextArea label {
        font-size: 1.125rem;
        font-weight: 500;
        color: #374151;
        margin-bottom: 0.5rem;
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
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="main-header">Interview Chatbot</h1>', unsafe_allow_html=True)

# --- State Management (using st.session_state) ---
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'answer_results' not in st.session_state:
    st.session_state.answer_results = []
if 'interview_ended' not in st.session_state:
    st.session_state.interview_ended = False
if 'candidate_answer' not in st.session_state:
    st.session_state.candidate_answer = ""

# --- Interview Logic ---
if not st.session_state.interview_ended:
    current_question = interview_questions[st.session_state.current_question_index]

    st.markdown(f'<p class="text-xl font-semibold text-gray-700 mb-4">Question {st.session_state.current_question_index + 1} of {len(interview_questions)}:</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="question-box">{current_question}</div>', unsafe_allow_html=True)

    st.session_state.candidate_answer = st.text_area(
        "Your Answer:",
        value=st.session_state.candidate_answer,
        height=200,
        key=f"answer_input_{st.session_state.current_question_index}"
    )

    col1, col2 = st.columns([1, 4]) # Create columns for alignment

    with col1:
        if st.button("Submit Answer", key="submit_button"):
            if st.session_state.candidate_answer.strip() == "":
                st.warning("Please provide an answer before submitting.")
            else:
                with st.spinner("Getting feedback from AI..."):
                    feedback_data = get_feedback_and_rating(current_question, st.session_state.candidate_answer)

                st.session_state.answer_results.append({
                    "question": current_question,
                    "answer": st.session_state.candidate_answer,
                    "feedback": feedback_data["feedback"],
                    "rating": feedback_data["rating"]
                })
                st.session_state.candidate_answer = "" # Clear input after submission

                if st.session_state.current_question_index < len(interview_questions) - 1:
                    st.session_state.current_question_index += 1
                    st.rerun() # Rerun to display the next question
                else:
                    st.session_state.interview_ended = True
                    st.rerun() # Rerun to display the interview summary

else:
    st.markdown('<h2 class="text-3xl font-bold text-green-700 text-center mb-6">Interview Complete!</h2>', unsafe_allow_html=True)
    st.markdown('<p class="text-lg text-gray-700 text-center mb-8">Here\'s a summary of your performance:</p>', unsafe_allow_html=True)

    for i, result in enumerate(st.session_state.answer_results):
        st.markdown(f'<div class="feedback-box mb-8">', unsafe_allow_html=True)
        st.markdown(f'<h3 class="feedback-title">Question {i + 1}: <span class="font-normal italic">"{result["question"]}"</span></h3>', unsafe_allow_html=True)
        st.markdown(f'<p class="text-gray-600 mb-2"><span class="font-medium">Your Answer:</span> {result["answer"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="text-gray-700 mb-2"><span class="font-medium">Feedback:</span> {result["feedback"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="rating-text">Rating: <span class="text-blue-600">{result["rating"]}/10</span></p>', unsafe_allow_html=True)
        st.markdown(f'</div>', unsafe_allow_html=True)

    if st.button("Restart Interview", key="restart_button"):
        st.session_state.current_question_index = 0
        st.session_state.answer_results = []
        st.session_state.interview_ended = False
        st.session_state.candidate_answer = ""
        st.rerun()