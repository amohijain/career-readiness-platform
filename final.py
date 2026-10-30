import streamlit as st
import io
from docx import Document
from PyPDF2 import PdfReader
import os
import json
import google.generativeai as genai
import re

# --- Streamlit UI Configuration (MUST BE FIRST) ---
st.set_page_config(page_title="AI Resume Analyzer", layout="centered", page_icon="📄")

# --- Configuration and Initialization ---
# Load Google Gemini API key
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("Google Gemini API key not found. Please set the GOOGLE_API_KEY environment variable or add it to Streamlit secrets.")
    st.stop()

genai.configure(api_key=api_key)

# Initialize the Gemini model once to reuse it across calls
@st.cache_resource
def get_gemini_model():
    return genai.GenerativeModel("gemini-1.5-flash")

model = get_gemini_model()

# --- Text Extraction Functions ---
# Use st.cache_data for functions that process file uploads,
# so they don't re-run unnecessarily if the file content hasn't changed.
@st.cache_data
def extract_text_from_pdf(file):
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

@st.cache_data
def extract_text_from_docx(file):
    """Extracts text from a DOCX file."""
    try:
        doc = Document(file)
        return "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return None

@st.cache_data
def extract_text_from_txt(file):
    """Extracts text from a TXT file."""
    try:
        # Use file.getvalue() for BytesIO objects common with st.file_uploader
        return file.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Error reading TXT: {e}")
        return None

# --- Gemini AI Analysis Function ---
def analyze_resume_with_gemini(text):
    """Analyzes resume text using the Gemini AI model."""
    prompt = f"""
    You are an expert resume reviewer. Provide constructive feedback on the following resume text.
    Return the response strictly in JSON format with three keys: "strengths", "weaknesses", and "improvements".
    Each key should map to a list of strings, where each string is a concise point of feedback.
    Ensure the JSON is perfectly valid and contains no extra text outside the JSON object.

    Resume Text:
    {text}
    """

    try:
        response = model.generate_content(prompt)
        feedback_raw_text = response.text.strip()

        # Regex to robustly find the JSON part, accounting for potential markdown code blocks
        json_match = re.search(r"```json\n(.*)\n```", feedback_raw_text, re.DOTALL)
        if json_match:
            feedback_json_str = json_match.group(1).strip()
        else:
            # Fallback if no markdown code block is found
            feedback_json_str = feedback_raw_text

        # Parse the JSON string
        return json.loads(feedback_json_str)

    except json.JSONDecodeError as e:
        st.error(f"AI response error: Could not parse feedback as valid JSON. Details: {e}")
        st.code(feedback_raw_text, language="json") # Show raw response for debugging
        return {
            "strengths": [],
            "weaknesses": ["AI response was not valid JSON."],
            "improvements": ["Please try re-uploading, or simplify your resume for AI processing."]
        }
    except Exception as e:
        st.error(f"An error occurred during AI analysis: {e}")
        return {
            "strengths": [],
            "weaknesses": ["Failed to get AI feedback."],
            "improvements": ["Please check your API key and internet connection, then try again."]
        }

# --- Streamlit UI Components ---
st.title("📄 Resume Analyzer")
st.write("Upload your resume (PDF, DOCX, or TXT) to receive instant feedback on its strengths, weaknesses, and areas for improvement.")

uploaded_file = st.file_uploader("Upload Your Resume", type=["pdf", "docx", "txt"], help="Supported formats: PDF, DOCX, TXT")

if uploaded_file:
    resume_text = None
    file_type = uploaded_file.type

    # Determine file type and extract text
    if file_type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        resume_text = extract_text_from_docx(uploaded_file)
    elif file_type == "text/plain":
        resume_text = extract_text_from_txt(uploaded_file)

    if resume_text:
        st.subheader("Extracted Resume Content")
        # Display a truncated version for long resumes
        display_text = resume_text[:1500] + "..." if len(resume_text) > 1500 else resume_text
        st.code(display_text, language="text")

        st.info("Analyzing your resume... This might take a moment.")
        with st.spinner("Reviewing your resume. Please wait..."):
            feedback = analyze_resume_with_gemini(resume_text)

        st.subheader("Feedback on Your Resume")

        # --- Display Feedback in HTML style ---
        def render_feedback_section(title, items, emoji):
            """Renders a feedback section with a title, emoji, and list of items."""
            if items:
                list_items_html = "".join(f"<li>{item}</li>" for item in items)
                return f"""
                <div class='feedback-section'>
                    <h3>{emoji} {title}</h3>
                    <ul>{list_items_html}</ul>
                </div>
                """
            else:
                return f"<div class='feedback-section'><h3>{emoji} {title}</h3><p>No specific points identified.</p></div>"

        # Apply custom CSS for styling feedback sections
        st.markdown("""
            <style>
            .feedback-section {
                background-color: #e8f0fe; /* Lighter blue background */
                border-left: 6px solid #1A73E8; /* Google Blue border */
                padding: 1rem 1.2rem;
                margin-top: 1.5rem;
                border-radius: 0.6rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); /* Subtle shadow */
                color: #333333; /* Darker text for readability */
            }
            .feedback-section h3 {
                color: #1A73E8; /* Consistent Google Blue for headings */
                margin-bottom: 0.7rem;
                font-size: 1.3rem;
            }
            .feedback-section ul {
                padding-left: 1.5rem;
                margin-bottom: 0; /* Remove default bottom margin */
            }
            .feedback-section li {
                margin-bottom: 0.6rem;
                line-height: 1.5;
                color: #333333; /* Ensure list item text is dark */
                font-size: 0.95rem;
            }
            .feedback-section p {
                color: #333333; /* Ensure paragraph text is dark */
                font-size: 0.95rem;
            }
            </style>
        """, unsafe_allow_html=True)

        # Render each feedback section
        st.markdown(render_feedback_section("Strengths", feedback.get("strengths", []), "💪"), unsafe_allow_html=True)
        st.markdown(render_feedback_section("Weaknesses", feedback.get("weaknesses", []), "🚧"), unsafe_allow_html=True)
        st.markdown(render_feedback_section("Suggestions for Improvement", feedback.get("improvements", []), "💡"), unsafe_allow_html=True)

    else:
        st.warning("Could not extract readable text from the uploaded file. Please ensure it's not scanned or corrupted.")

st.markdown("---")
st.markdown("<center><i>Powered by Google Gemini AI</i></center>", unsafe_allow_html=True)