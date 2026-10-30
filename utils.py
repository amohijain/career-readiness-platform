# import difflib
# import re
# import string
# import nltk
# from collections import Counter
# from nltk.corpus import stopwords
# from sklearn.feature_extraction.text import TfidfVectorizer
# from fpdf import FPDF

# nltk.download('punkt')
# nltk.download('stopwords')

# def extract_text_from_docx(path):
#     """Extract text from .docx file."""
#     from docx import Document
#     doc = Document(path)
#     return "\n".join([para.text for para in doc.paragraphs])

# def preprocess(text):
#     """Preprocess text by removing punctuation, digits, and stopwords."""
#     text = text.lower()
#     text = re.sub(r'\d+', '', text)
#     text = text.translate(str.maketrans('', '', string.punctuation))
#     words = nltk.word_tokenize(text)
#     return [word for word in words if word not in stopwords.words('english')]

# def get_text_diff(text1, text2):
#     """Generate textual differences between two texts."""
#     diff = difflib.ndiff(text1.splitlines(), text2.splitlines())
#     return '\n'.join(diff)

# def rate_resume(text):
#     """Rate the resume on a scale of 1 to 10 based on readability and keyword usage."""
#     words = preprocess(text)
#     word_count = len(words)
#     readability_score = min(10, word_count / 100)  # A simple readability metric

#     # Rate keyword optimization using TF-IDF (higher score for more relevant keywords)
#     vectorizer = TfidfVectorizer(stop_words='english')
#     tfidf_matrix = vectorizer.fit_transform([text])
#     keyword_score = len(vectorizer.get_feature_names_out())  # Number of unique keywords

#     # Combine scores (you can adjust these weights)
#     total_score = (readability_score + keyword_score / 10) / 2
#     return round(total_score, 1)

# def generate_pdf(diff_text):
#     """Generate PDF containing the resume differences."""
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)
#     pdf.multi_cell(0, 10, diff_text)
#     return pdf


# import difflib
# import re
# import string
# import nltk
# from collections import Counter
# from nltk.corpus import stopwords
# from sklearn.feature_extraction.text import TfidfVectorizer
# from fpdf import FPDF

# nltk.download('punkt')
# nltk.download('stopwords')

# def extract_text_from_docx(path):
#     """Extract text from .docx file."""
#     from docx import Document
#     doc = Document(path)
#     return "\n".join([para.text for para in doc.paragraphs])

# def preprocess(text):
#     """Preprocess text by removing punctuation, digits, and stopwords."""
#     text = text.lower()
#     text = re.sub(r'\d+', '', text)
#     text = text.translate(str.maketrans('', '', string.punctuation))
#     words = nltk.word_tokenize(text)
#     return [word for word in words if word not in stopwords.words('english')]

# def get_text_diff(text1, text2):
#     """Generate textual differences between two texts."""
#     diff = difflib.ndiff(text1.splitlines(), text2.splitlines())
#     return '\n'.join(diff)

# def rate_resume(text):
#     """Rate the resume on a scale of 1 to 10 based on readability and keyword usage."""
#     words = preprocess(text)
#     word_count = len(words)
#     readability_score = min(10, word_count / 100)  # Simple readability metric

#     # Rate keyword optimization using TF-IDF (higher score for more relevant keywords)
#     vectorizer = TfidfVectorizer(stop_words='english')
#     tfidf_matrix = vectorizer.fit_transform([text])
#     keyword_score = len(vectorizer.get_feature_names_out())  # Number of unique keywords

#     # Combine scores (you can adjust these weights)
#     total_score = (readability_score + keyword_score / 10) / 2
#     return round(total_score, 1)

# def sanitize_text(text):
#     """Sanitize text to ensure compatibility with Latin-1 encoding used by FPDF."""
#     replacements = {
#         '\u2013': '-',  # en-dash
#         '\u2014': '-',  # em-dash
#         '\u2018': "'",  # left single quote
#         '\u2019': "'",  # right single quote
#         '\u201c': '"',  # left double quote
#         '\u201d': '"',  # right double quote
#         '\u2026': '...',  # ellipsis
#         '\xa0': ' '      # non-breaking space
#     }
#     for key, val in replacements.items():
#         text = text.replace(key, val)
#     return text

# def generate_pdf(diff_text, output_path="resume_diff.pdf", return_bytes=False):
#     """Generate PDF containing the resume differences.
    
#     If return_bytes=True, return the PDF data as bytes instead of saving to file.
#     """
#     print("Generating PDF...")  # Debugging print statement

#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)

#     clean_text = sanitize_text(diff_text)
#     pdf.multi_cell(0, 10, clean_text)

#     if return_bytes:
#         print("Returning PDF as bytes...")  # Debugging print statement
#         return pdf.output(dest='S').encode('latin1')  # Return PDF as bytes
#     else:
#         print(f"Saving PDF to {output_path}")  # Debugging print statement
#         pdf.output(output_path)  # Save to file
#         print(f"PDF saved to {output_path}")

# # === Example Usage ===

# if __name__ == "__main__":
#     # Load and compare two resumes
#     text1 = extract_text_from_docx("resume_old.docx")
#     text2 = extract_text_from_docx("resume_new.docx")

#     # Show score (optional)
#     print("Old Resume Score:", rate_resume(text1))
#     print("New Resume Score:", rate_resume(text2))

#     # Generate diff and save PDF
#     diff_text = get_text_diff(text1, text2)
#     generate_pdf(diff_text)  # Saves PDF to resume_diff.pdf

#     # Optional: get PDF as bytes instead (e.g., for email or API)
#     # pdf_bytes = generate_pdf(diff_text, return_bytes=True)


import streamlit as st
import re
import string
import difflib
from docx import Document
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from tabulate import tabulate
import nltk

nltk.download('punkt')
nltk.download('stopwords')


# =================== Utility Functions ===================

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def preprocess(text):
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = word_tokenize(text)
    return [word for word in words if word not in stopwords.words('english')]

def rate_resume(text):
    words = preprocess(text)
    word_count = len(words)
    readability_score = min(10, word_count / 100)
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([text])
    keyword_score = len(vectorizer.get_feature_names_out())
    total_score = (readability_score + keyword_score / 10) / 2
    return round(total_score, 1)

def extract_sections(text):
    text = text.lower()
    sections = {
        'education': '',
        'experience': '',
        'skills': '',
        'certifications': ''
    }

    current_section = None
    for line in text.splitlines():
        line = line.strip()
        if re.match(r'^(education|academic background)', line):
            current_section = 'education'
        elif re.match(r'^(experience|work history|professional experience)', line):
            current_section = 'experience'
        elif re.match(r'^(skills|technical skills)', line):
            current_section = 'skills'
        elif re.match(r'^(certifications|licenses)', line):
            current_section = 'certifications'
        elif re.match(r'^[a-z ]+$', line) and len(line.split()) < 4:
            current_section = None

        if current_section and line:
            sections[current_section] += line + '\n'

    return sections

def compare_sections(sections1, sections2):
    table_data = []
    for section in sections1:
        text1 = sections1.get(section, '').strip()
        text2 = sections2.get(section, '').strip()
        if not text1 and not text2:
            diff_summary = "❌ Not found in both"
        elif not text1:
            diff_summary = "🆕 Added in New"
        elif not text2:
            diff_summary = "🗑️ Removed from Old"
        elif text1 == text2:
            diff_summary = "✅ No Change"
        else:
            sm = difflib.SequenceMatcher(None, text1, text2)
            diff_summary = f"🔁 Changed ({round(sm.ratio()*100, 1)}% similarity)"
        table_data.append([section.capitalize(), diff_summary])
    return table_data

# =================== Streamlit App ===================

st.set_page_config(page_title="Resume Comparator", layout="wide")
st.title("📄 Resume Evolution Tracker")

col1, col2 = st.columns(2)

with col1:
    resume_old = st.file_uploader("Upload Old Resume (.docx)", type=["docx"])
with col2:
    resume_new = st.file_uploader("Upload New Resume (.docx)", type=["docx"])

if resume_old and resume_new:
    text_old = extract_text_from_docx(resume_old)
    text_new = extract_text_from_docx(resume_new)

    # Ratings
    score_old = rate_resume(text_old)
    score_new = rate_resume(text_new)

    col1, col2 = st.columns(2)
    col1.metric("Old Resume Score", score_old)
    col2.metric("New Resume Score", score_new)

    # Section-wise comparison
    st.subheader("📊 Section-wise Comparison")
    sections_old = extract_sections(text_old)
    sections_new = extract_sections(text_new)
    comparison = compare_sections(sections_old, sections_new)

    # Format as markdown table
    st.markdown("### Summary Table")
    st.table(comparison)

    # Optional: Show full diffs per section
    with st.expander("🔍 Show Section Differences"):
        for section in sections_old:
            st.markdown(f"**{section.capitalize()}**")
            diff = difflib.unified_diff(
                sections_old[section].splitlines(),
                sections_new[section].splitlines(),
                lineterm=''
            )
            st.code('\n'.join(diff), language="diff")

else:
    st.info("Please upload both resumes to proceed.")

