import streamlit as st
import google.generativeai as genai
import os
import io
from pypdf import PdfReader
from docx import Document

# --- Streamlit Page Config ---
st.set_page_config(page_title="Resume Analyzer", layout="centered")

# --- Load Google API Key Safely ---
try:
    api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Google API Key not found. Set it in secrets or environment variable.")
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ API Key Setup Failed: {e}")
    st.stop()

# --- Load Gemini Model ---
try:
    model = genai.GenerativeModel("gemini-pro")
except Exception as e:
    st.error(f"❌ Failed to initialize Gemini model: {e}")
    st.stop()

# --- File Text Extraction ---
def extract_text_from_pdf(file):
    try:
        reader = PdfReader(file)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except Exception as e:
        st.error(f"❌ PDF extraction error: {e}")
        return None

def extract_text_from_docx(file):
    try:
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"❌ DOCX extraction error: {e}")
        return None

def extract_text(uploaded_file, file_bytes):
    file_type = uploaded_file.type
    if file_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_bytes)
    elif file_type == "text/plain":
        return file_bytes.getvalue().decode("utf-8")
    else:
        st.warning("⚠️ Unsupported file type.")
        return None

# --- Prompt Template ---
PROMPT_TEMPLATE = """
You are an expert career counselor and resume analyst. Analyze the following resume and provide:
A. **Strengths:** (3–5 clear bullet points)
B. **Areas for Improvement:** (3–5 with actionable suggestions)

Resume:
{resume_text}
"""

# --- UI ---
st.title("📄 AI-Powered Resume Analyzer")
st.markdown("Upload your resume (PDF, DOCX, or TXT) and receive instant professional feedback from **Google Gemini**.")

uploaded_file = st.file_uploader("📤 Upload Resume", type=["pdf", "docx", "txt"])

if uploaded_file:
    file_bytes = io.BytesIO(uploaded_file.read())

    with st.spinner("🔍 Extracting text from your resume..."):
        resume_text = extract_text(uploaded_file, file_bytes)

    if resume_text and resume_text.strip():
        st.success("✅ Text extracted successfully!")

        with st.expander("📄 View Extracted Text"):
            st.text_area("Resume Content", resume_text, height=300, disabled=True)

        if st.button("✨ Analyze Resume"):
            try:
                with st.spinner("🤖 Analyzing your resume with Gemini..."):
                    prompt = PROMPT_TEMPLATE.format(resume_text=resume_text)
                    response = model.generate_content(prompt)
                st.subheader("📊 Resume Feedback")
                st.markdown(response.text)
                st.info("💡 This feedback is AI-generated. Consider combining it with human review for best results.")
            except Exception as e:
                st.error(f"❌ AI analysis error: {e}")
    else:
        st.error("❗ Could not extract text. Please upload a readable file (not scanned image).")

st.markdown("---")
st.caption("🚀 Built with ❤️ using Streamlit and Google Gemini")
