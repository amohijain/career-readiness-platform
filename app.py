import streamlit as st
from utils import extract_text_from_docx, get_text_diff, rate_resume, generate_pdf

# Load resume texts
text_v1 = extract_text_from_docx('resumes/resume_v1.docx')
text_v2 = extract_text_from_docx('resumes/resume_v2.docx')

# Show textual differences
st.subheader("Textual Differences (Line-by-Line Comparison)")
diff_text = get_text_diff(text_v1, text_v2)
st.text(diff_text)

# Show Resume Ratings
rating_v1 = rate_resume(text_v1)
rating_v2 = rate_resume(text_v2)

st.subheader("Resume Ratings")
st.write(f"**Version 1 Rating**: {rating_v1}/10")
st.write(f"**Version 2 Rating**: {rating_v2}/10")

# Generate and download PDF report
pdf = generate_pdf(diff_text)
st.download_button(
    label="Download PDF Report",
    data=pdf.output(dest='S').encode('latin1'),
    file_name="resume_comparison_report.pdf",
    mime="application/pdf"
)
