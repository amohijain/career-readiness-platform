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
import pdfplumber # New import for PDF text extraction

# Ensure NLTK data is downloaded. These calls are idempotent.
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords')


# =================== Utility Functions ===================

def extract_text_from_docx(file):
    """
    Extracts plain text from a .docx file.
    """
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pdf(file):
    """
    Extracts plain text from a .pdf file using pdfplumber.
    """
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or "" # extract_text() can return None
    return text

def preprocess(text):
    """
    Cleans and tokenizes text:
    - Converts to lowercase.
    - Removes numbers.
    - Removes punctuation.
    - Tokenizes into words.
    - Removes English stopwords.
    """
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = word_tokenize(text)
    # Use a set for faster stopword lookup
    stop_words = set(stopwords.words('english'))
    return [word for word in words if word not in stop_words]

def rate_resume(text):
    """
    Rates a resume based on word count (readability) and keyword density (TF-IDF).
    Returns a score out of 10.
    """
    words = preprocess(text)
    word_count = len(words)
    # Readability score: max 10 based on 1000 words.
    readability_score = min(10, word_count / 100) 
    
    vectorizer = TfidfVectorizer(stop_words='english')
    keyword_score = 0
    # Fit TF-IDF only if the text is not empty to avoid ValueError
    if text and text.strip():
        tfidf_matrix = vectorizer.fit_transform([text])
        keyword_score = len(vectorizer.get_feature_names_out())
    
    # Normalize keyword score and combine with readability
    # Keyword score contributes based on the number of unique, important words.
    # Dividing by 10 to bring it into a comparable range with readability_score.
    total_score = (readability_score + keyword_score / 10) / 2
    return round(total_score, 1)

def extract_sections(text):
    """
    Attempts to extract common resume sections (education, experience, skills, certifications)
    from the raw text using predefined keywords.
    """
    text = text.lower()
    sections = {
        'education': '',
        'experience': '',
        'skills': '',
        'certifications': ''
    }

    # Define keywords for each section. Using regex for flexibility.
    section_keywords = {
        'education': [r'^(education|academic background|academics)'],
        'experience': [r'^(experience|work history|professional experience)'],
        'skills': [r'^(skills|technical skills|abilities)'],
        'certifications': [r'^(certifications|licenses|awards)']
    }

    current_section_key = None
    for line in text.splitlines():
        line = line.strip()
        is_header = False
        
        # Check if the current line is a recognized section header
        for key, patterns in section_keywords.items():
            for pattern in patterns:
                if re.match(pattern, line):
                    current_section_key = key
                    is_header = True
                    break # Found a header, move to next line
            if is_header:
                break # Found a header, stop checking other sections for this line
        
        # If it's not a new header and we are currently tracking a section, append the line
        if not is_header and current_section_key:
            if line: # Only add non-empty lines to the section content
                sections[current_section_key] += line + '\n'
    
    # Clean up trailing newlines from extracted sections
    for key in sections:
        sections[key] = sections[key].strip()

    return sections

def compare_sections(sections1, sections2):
    """
    Compares two sets of extracted resume sections and summarizes changes.
    Returns a list of lists suitable for a table.
    """
    table_data = []
    # Get all unique section keys from both resume dictionaries for comprehensive comparison
    all_sections_keys = sorted(list(set(sections1.keys()) | set(sections2.keys())))

    for section in all_sections_keys:
        text1 = sections1.get(section, '').strip() # Content from old resume
        text2 = sections2.get(section, '').strip() # Content from new resume
        
        diff_summary = ""
        if not text1 and not text2:
            diff_summary = "❌ Not found in both"
        elif not text1: 
            diff_summary = "🆕 Added in New" # Section present only in new resume
        elif not text2: 
            diff_summary = "🗑 Removed from Old" # Section present only in old resume
        elif text1 == text2:
            diff_summary = "✅ No Change" # Content is identical
        else:
            # Calculate similarity ratio for changed sections
            sm = difflib.SequenceMatcher(None, text1, text2)
            diff_summary = f"🔁 Changed ({round(sm.ratio()*100, 1)}% similarity)"
        table_data.append([section.capitalize(), diff_summary])
    return table_data

def generate_report_content(score_old, score_new, comparison_table, sections_old, sections_new):
    """
    Generates a comprehensive Markdown-formatted report string
    detailing the resume comparison.
    """
    report_md = "# Resume Comparison Report\n\n"
    report_md += f"## 📄 Resume Scores\n"
    report_md += f"- *Old Resume Score:* {score_old}\n"
    report_md += f"- *New Resume Score:* {score_new}\n\n"

    report_md += "## 📊 Section-wise Comparison Summary\n"
    
    # Format the comparison table as a Markdown table using tabulate library
    headers = ["Section", "Change Summary"]
    report_md += tabulate(comparison_table, headers=headers, tablefmt="pipe") + "\n\n"

    report_md += "## 🔍 Detailed Section Differences\n"
    # Iterate through all unique sections to ensure all differences are reported
    all_sections_for_diff_report = sorted(list(set(sections_old.keys()) | set(sections_new.keys())))

    for section_name in all_sections_for_diff_report:
        text_old = sections_old.get(section_name, '').strip()
        text_new = sections_new.get(section_name, '').strip()

        report_md += f"### {section_name.capitalize()}\n"
        if not text_old and not text_new:
            report_md += "This section was not found in either resume.\n\n"
        elif not text_old:
            report_md += "This section was *added* in the New Resume:\n"
            report_md += "\n" + text_new + "\n\n\n"
        elif not text_new:
            report_md += "This section was *removed* from the Old Resume:\n"
            report_md += "\n" + text_old + "\n\n\n"
        else:
            # Generate a unified diff for changes between versions
            diff_lines = list(difflib.unified_diff(
                text_old.splitlines(),
                text_new.splitlines(),
                lineterm='', # Prevents adding extra newlines if input already has them
                fromfile=f'a/{section_name}.txt', # Labels for the diff tool
                tofile=f'b/{section_name}.txt'   # Labels for the diff tool
            ))
            if not diff_lines:
                report_md += "No changes detected in this section.\n\n"
            else:
                report_md += "diff\n" + "\n".join(diff_lines) + "\n\n\n"
    
    return report_md

# =================== Streamlit App ===================

# Configure the Streamlit page
st.set_page_config(page_title="Resume Comparator", layout="wide")
st.title("📄 Resume Tracker Tool")

# File uploaders for the old and new resumes
col1, col2 = st.columns(2)

with col1:
    resume_old = st.file_uploader("Upload Old Resume (.docx or .pdf)", type=["docx", "pdf"])
with col2:
    resume_new = st.file_uploader("Upload New Resume (.docx or .pdf)", type=["docx", "pdf"])

# Proceed only if both resumes are uploaded
if resume_old and resume_new:
    # Determine file type and extract text for old resume
    if resume_old.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text_old = extract_text_from_docx(resume_old)
    elif resume_old.type == "application/pdf":
        text_old = extract_text_from_pdf(resume_old)
    else:
        st.error("Unsupported file type for Old Resume. Please upload a .docx or .pdf file.")
        st.stop()

    # Determine file type and extract text for new resume
    if resume_new.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text_new = extract_text_from_docx(resume_new)
    elif resume_new.type == "application/pdf":
        text_new = extract_text_from_pdf(resume_new)
    else:
        st.error("Unsupported file type for New Resume. Please upload a .docx or .pdf file.")
        st.stop()

    # Calculate and display overall resume scores
    score_old = rate_resume(text_old)
    score_new = rate_resume(text_new)

    st.markdown("## Overall Resume Scores")
    score_col1, score_col2 = st.columns(2)
    score_col1.metric("Old Resume Score", score_old)
    score_col2.metric("New Resume Score", score_new)

    # Perform and display section-wise comparison
    st.markdown("---") # Visual separator
    st.subheader("📊 Section-wise Comparison")
    sections_old = extract_sections(text_old)
    sections_new = extract_sections(text_new)
    comparison = compare_sections(sections_old, sections_new)

    st.markdown("### Summary Table")
    st.table(comparison) # Streamlit's built-in table display

    # Optional: Expandable section to show full differences per section
    with st.expander("🔍 Show Detailed Section Differences"):
        # Ensure consistent order for displaying sections in the diff
        all_sections_in_diff_display = sorted(list(set(sections_old.keys()) | set(sections_new.keys())))

        for section in all_sections_in_diff_display:
            st.markdown(f"{section.capitalize()}")
            text1 = sections_old.get(section, '').strip()
            text2 = sections_new.get(section, '').strip()

            if not text1 and not text2:
                st.info("Content not found in either resume for this section.")
            elif not text1:
                st.success(f"'{section.capitalize()}' section was ADDED in the New Resume:")
                st.code(text2, language="text")
            elif not text2:
                st.error(f"'{section.capitalize()}' section was REMOVED from the Old Resume:")
                st.code(text1, language="text")
            else:
                # Generate and display a unified diff for clarity
                diff = difflib.unified_diff(
                    text1.splitlines(),
                    text2.splitlines(),
                    lineterm='',
                    fromfile=f'a/{section}.txt',
                    tofile=f'b/{section}.txt'
                )
                diff_str = '\n'.join(diff)
                if diff_str:
                    st.code(diff_str, language="diff")
                else:
                    st.info("No substantial changes detected in this section.")
    
    st.markdown("---") # Visual separator
    st.subheader("⬇ Generate Report")

    # Generate the full report content in Markdown format
    full_report_content = generate_report_content(
        score_old, score_new, comparison, sections_old, sections_new
    )

    # Provide a download button for the generated report
    st.download_button(
        label="Download Full Report (Markdown/Text)",
        data=full_report_content,
        file_name="resume_comparison_report.md",
        mime="text/markdown", # Suggests it's a Markdown file
        help="Download the complete comparison report in Markdown format. You can then print this file to PDF."
    )
    
    # Also show the report content in an expander for quick preview/copying
    with st.expander("Preview Full Report"):
        st.code(full_report_content, language="markdown")
        st.info(
            "You can copy this text and paste it into a Markdown editor, "
            "or use your browser's print function (Ctrl+P / Cmd+P) and select 'Save as PDF' to generate a PDF."
        )

else:
    # Message displayed when files are not yet uploaded
    st.info("Please upload both resumes (.docx or .pdf files) to proceed with the comparison.")