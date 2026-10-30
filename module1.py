import streamlit as st
import io
from docx import Document
from PyPDF2 import PdfReader
import os
import json
import google.generativeai as genai
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.units import inch # For Spacers
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont # For TrueType Fonts
from wordcloud import WordCloud # For potential word cloud visualization (requires matplotlib)
import matplotlib.pyplot as plt

# --- Streamlit UI Configuration (MUST BE FIRST) ---
st.set_page_config(page_title="AI Resume Analyzer", layout="centered", page_icon="📄")

# --- Configuration and Initialization ---
# Load Google Gemini API key
API_KEY = st.secrets["gemini"]["api_key"]
if not API_KEY:
    st.error("Google Gemini API key not found. Please set the GOOGLE_API_KEY environment variable or add it to Streamlit secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

# Initialize the Gemini model once to reuse it across calls
@st.cache_resource
def get_gemini_model():
    return genai.GenerativeModel("gemini-3-flash-preview")

model = get_gemini_model()

# --- Text Extraction Functions ---
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
        return file.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Error reading TXT: {e}")
        return None

# --- Gemini AI Analysis Function ---
def analyze_resume_with_gemini(text):
    """Analyzes resume text using the Gemini AI model and provides a detailed JSON output."""
    prompt = f"""
    You are an expert resume reviewer and career coach. Analyze the following resume text comprehensively.
    Provide feedback and scores, strictly in JSON format.

    The JSON should have the following keys:
    - "overall_rating": An integer from 1 to 10 (10 being excellent).
    - "strengths": A list of concise strings detailing the resume's strong points.
    - "weaknesses": A list of concise strings detailing areas that need improvement.
    - "improvements": A list of concise strings providing actionable suggestions.
    - "keyword_suggestions": A list of important skills, industries, or role-specific keywords found or recommended.
    - "ats_compatibility_score": An integer from 0 to 100, estimating how well the resume might pass an ATS (Applicant Tracking System). Focus on clarity, standard sections, and keyword presence.
    - "conciseness_score": An integer from 0 to 100, assessing how brief and to-the-point the resume is.
    - "action_verb_suggestions": A list of stronger action verbs that could be used.
    - "grammar_spelling_issues": A list of concise strings flagging any noticeable grammar or spelling issues (e.g., "Typo on 'responsibilites'", "Inconsistent capitalization in headings"). If none, provide an empty list.
    - "formatting_layout_feedback": A list of concise strings with general feedback on the resume's visual presentation and layout (e.g., "Good use of white space", "Consider a more modern template", "Ensure consistent date formats"). If none, provide an empty list.

    Ensure the JSON is perfectly valid and contains no extra text outside the JSON object.

    Resume Text:
    {text}
    """

    try:
        response = model.generate_content(prompt)
        feedback_raw_text = response.text.strip()

        # Robustly extract JSON from potential markdown code blocks
        json_match = re.search(r"json\n(.*)\n", feedback_raw_text, re.DOTALL)
        if json_match:
            feedback_json_str = json_match.group(1).strip()
        else:
            feedback_json_str = feedback_raw_text

        parsed_feedback = json.loads(feedback_json_str)

        # Validate and default scores/ratings if missing or invalid
        parsed_feedback['overall_rating'] = max(1, min(10, int(parsed_feedback.get('overall_rating', 5))))
        parsed_feedback['ats_compatibility_score'] = max(0, min(100, int(parsed_feedback.get('ats_compatibility_score', 50))))
        parsed_feedback['conciseness_score'] = max(0, min(100, int(parsed_feedback.get('conciseness_score', 50))))
        
        # Ensure all list keys exist and are lists to prevent errors later
        for key in ["strengths", "weaknesses", "improvements", "keyword_suggestions", 
                     "action_verb_suggestions", "grammar_spelling_issues", "formatting_layout_feedback"]:
            if not isinstance(parsed_feedback.get(key), list):
                parsed_feedback[key] = []

        return parsed_feedback

    except json.JSONDecodeError as e:
        st.error(f"AI response error: Could not parse feedback as valid JSON. Details: {e}")
        st.code(feedback_raw_text, language="json") # Show raw response for debugging
        return {
            "overall_rating": 5, "strengths": [], "weaknesses": ["AI response was not valid JSON."],
            "improvements": ["Please try re-uploading, or simplify your resume for AI processing."],
            "keyword_suggestions": [], "ats_compatibility_score": 50, "conciseness_score": 50,
            "action_verb_suggestions": [], "grammar_spelling_issues": [], "formatting_layout_feedback": []
        }
    except Exception as e:
        st.error(f"An error occurred during AI analysis: {e}")
        return {
            "overall_rating": 5, "strengths": [], "weaknesses": ["Failed to get AI feedback."],
            "improvements": ["Please check your API key and internet connection, then try again."],
            "keyword_suggestions": [], "ats_compatibility_score": 50, "conciseness_score": 50,
            "action_verb_suggestions": [], "grammar_spelling_issues": [], "formatting_layout_feedback": []
        }

# --- PDF Report Generation Function ---
def generate_pdf_report(feedback_data, resume_text):
    """Generates a PDF report of the resume analysis."""
    buffer = io.BytesIO()
    
    # Global variable to store the font name, default to Helvetica
    global DEFAULT_PDF_FONT
    DEFAULT_PDF_FONT = 'Helvetica' # Fallback default

    # --- ReportLab Font Registration for Unicode/Emojis ---
    try:
        # Check if DejaVuSans.ttf exists in the current directory
        if os.path.exists('DejaVuSans.ttf'):
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            pdfmetrics.registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans', italic='DejaVuSans', boldItalic='DejaVuSans')
            DEFAULT_PDF_FONT = 'DejaVuSans'
        else:
            st.warning("DejaVuSans.ttf not found in the current directory. Emojis and some special characters might not render in PDF. Please download it from Google Fonts (or similar) and place it next to your script.")
            
    except Exception as e:
        st.warning(f"Error registering font: {e}. Emojis and some special characters might not render in PDF. Using Helvetica as fallback.")
        DEFAULT_PDF_FONT = 'Helvetica'
            
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    Story = []
    styles = getSampleStyleSheet()

    # --- ReportLab Style Configuration ---
    styles['h1'].fontName = DEFAULT_PDF_FONT
    styles['h1'].fontSize = 24
    styles['h1'].leading = 28
    styles['h1'].alignment = TA_CENTER
    styles['h1'].spaceAfter = 20

    styles['h2'].fontName = DEFAULT_PDF_FONT
    styles['h2'].fontSize = 18
    styles['h2'].leading = 22
    styles['h2'].spaceAfter = 10
    styles['h2'].textColor = '#1A73E8' # Google Blue

    styles['Normal'].fontName = DEFAULT_PDF_FONT
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    styles['Normal'].spaceAfter = 6
    styles['Normal'].alignment = TA_LEFT

    styles.add(ParagraphStyle(name='ListItem',
                              parent=styles['Normal'],
                              fontName=DEFAULT_PDF_FONT,
                              leftIndent=20, # Indent for bullet points
                              spaceAfter=4))

    styles.add(ParagraphStyle(name='SmallText',
                              parent=styles['Normal'],
                              fontName=DEFAULT_PDF_FONT,
                              fontSize=8,
                              leading=10,
                              alignment=TA_CENTER))

    # --- Header and Footer on each page ---
    def header_footer_handler(canvas, doc):
        canvas.saveState()
        canvas.setFont(DEFAULT_PDF_FONT, 10)
        canvas.drawString(inch, 0.75 * inch, f"Page {doc.page}")
        
        # Use Paragraph for header text to ensure font consistency and wrapping
        # Need to use a temporary Paragraph object to get its width/height before drawing
        header_text_main = "Resume Analysis Report"
        header_para_main = Paragraph(header_text_main, styles['SmallText']) 
        w_main, h_main = header_para_main.wrapOn(canvas, letter[0] - 100, 50) 
        header_para_main.drawOn(canvas, letter[0]/2 - w_main/2, letter[1] - 30 - h_main) # Adjusted for height
        
        header_text_sub = "Generated by AI Resume Analyzer (Powered by Google Gemini AI)"
        header_para_sub = Paragraph(header_text_sub, styles['SmallText'])
        w_sub, h_sub = header_para_sub.wrapOn(canvas, letter[0] - 100, 50)
        header_para_sub.drawOn(canvas, letter[0]/2 - w_sub/2, letter[1] - 45 - h_main - h_sub) # Adjusted for space
        
        canvas.restoreState()

    # Add main title (first page only for aesthetic)
    Story.append(Paragraph("Resume Analysis Report", styles['h1']))
    Story.append(Paragraph("Generated by AI Resume Analyzer (Powered by Google Gemini AI)", styles['SmallText']))
    Story.append(Spacer(1, 0.2 * inch)) 

    # Helper to add sections to the Story
    def add_section_to_story(title, items, emoji, default_message="No specific points identified.", item_style='ListItem'):
        Story.append(Spacer(1, 0.2 * inch)) # Space before each section
        # Use the default font for the emoji within the heading
        Story.append(Paragraph(f"{emoji} {title}", styles['h2'])) 
        if items:
            for item in items:
                # FIX: Correctly replace ** with <b> and ** with </b> for ReportLab's HTML parser
                # This regex ensures that only content between ** is bolded.
                # It handles cases where there might be multiple bolded phrases in one item.
                formatted_item = re.sub(r'\\(.?)\\*', r'<b>\1</b>', item)
                
                # Ensure a clean string for Paragraph
                Story.append(Paragraph(f"- {formatted_item}", styles[item_style]))
        else:
            Story.append(Paragraph(default_message, styles['Normal']))
        Story.append(Spacer(1, 0.1 * inch)) # Small space after section

    # --- Add Feedback Sections to Story ---
    add_section_to_story("Overall Rating", [f"Your resume received an overall rating of: {feedback_data.get('overall_rating', 5)}/10"], "⭐")
    add_section_to_story("ATS Compatibility Score", [f"Estimated ATS Compatibility Score: {feedback_data.get('ats_compatibility_score', 50)}/100"], "🤖")
    add_section_to_story("Conciseness Score", [f"Conciseness Score: {feedback_data.get('conciseness_score', 50)}/100"], "📏")

    add_section_to_story("Strengths", feedback_data.get("strengths", []), "💪")
    add_section_to_story("Weaknesses", feedback.get("weaknesses", []), "🚧")
    add_section_to_story("Suggestions for Improvement", feedback.get("improvements", []), "💡")
    add_section_to_story("Suggested Keywords/Skills", feedback.get("keyword_suggestions", []), "🔑")
    add_section_to_story("Action Verb Suggestions", feedback.get("action_verb_suggestions", []), "⚡")
    add_section_to_story("Grammar & Spelling Issues", feedback.get("grammar_spelling_issues", []), "✍", "No major grammar or spelling issues detected.")
    add_section_to_story("Formatting & Layout Feedback", feedback.get("formatting_layout_feedback", []), "📐", "Looks good, or no specific formatting issues flagged.")

    # Original Resume Text Section (optional, for reference)
    if resume_text:
        Story.append(PageBreak()) 
        Story.append(Paragraph("Original Resume Text (Truncated for Report)", styles['h2']))
        Story.append(Spacer(1, 0.1 * inch))
        
        display_text_pdf = resume_text[:4000] + "\n\n[...Truncated for brevity...]" if len(resume_text) > 4000 else resume_text
        
        Story.append(Paragraph(display_text_pdf, styles['Normal']))
        Story.append(Spacer(1, 0.2 * inch))

    # --- Add a clickable link section ---
    Story.append(Spacer(1, 0.3 * inch))
    Story.append(Paragraph("---", styles['SmallText'])) # Separator
    Story.append(Spacer(1, 0.1 * inch))
    
    link_text = "Learn more about this AI Resume Analyzer project"
    link_url = "https://github.com/yourusername/your-resume-analyzer-repo" # IMPORTANT: REPLACE WITH YOUR ACTUAL URL
    
    Story.append(Paragraph(f"For more details, visit our project page: <link href='{link_url}'>{link_text}</link>", styles['Normal']))
    Story.append(Spacer(1, 0.2 * inch))
    Story.append(Paragraph("<center><i>Report End</i></center>", styles['SmallText']))


    # Build the PDF document with onFirstPage and onLaterPages
    try:
        doc.build(Story, onFirstPage=header_footer_handler, onLaterPages=header_footer_handler)
    except Exception as e:
        st.error(f"Error building PDF document: {e}. This might be due to problematic characters or very complex text. Please review your resume content for unusual characters.")
    buffer.seek(0)
    return buffer

# --- Streamlit UI Components ---
st.title("📄 AI Resume Analyzer")
st.write("Upload your resume (PDF, DOCX, or TXT) to receive instant, in-depth feedback and an interactive analysis dashboard.")

uploaded_file = st.file_uploader("Upload Your Resume", type=["pdf", "docx", "txt"], help="Supported formats: PDF, DOCX, TXT")

if uploaded_file:
    resume_text = None
    file_type = uploaded_file.type

    if file_type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        resume_text = extract_text_from_docx(uploaded_file)
    elif file_type == "text/plain":
        resume_text = extract_text_from_txt(uploaded_file)

    if resume_text:
        st.subheader("Extracted Resume Content (Preview)")
        display_text = resume_text[:1500] + "...\n[Full content processed for analysis]" if len(resume_text) > 1500 else resume_text
        st.code(display_text, language="text")

        st.info("Analyzing your resume... This might take a moment as AI processes the content.")
        with st.spinner("Deep diving into your resume. Please wait..."):
            feedback = analyze_resume_with_gemini(resume_text)

        st.subheader("Your Resume Analysis Dashboard")

        # --- Dashboard Layout ---
        tab1, tab2, tab3 = st.tabs(["📊 Overview & Scores", "📝 Detailed Feedback", "🔑 Keywords & Verbs"])

        with tab1:
            st.markdown("### Overall Performance Snapshot")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(label="Overall Rating", value=f"{feedback.get('overall_rating', 'N/A')}/10", delta="Higher is better")
                if feedback.get('overall_rating') is not None:
                    st.progress(feedback['overall_rating'] / 10.0)
            with col2:
                st.metric(label="ATS Compatibility", value=f"{feedback.get('ats_compatibility_score', 'N/A')}%", delta="Aim for >80%")
                if feedback.get('ats_compatibility_score') is not None:
                    st.progress(feedback['ats_compatibility_score'] / 100.0)
            with col3:
                st.metric(label="Conciseness", value=f"{feedback.get('conciseness_score', 'N/A')}%", delta="Avoid fluff")
                if feedback.get('conciseness_score') is not None:
                    st.progress(feedback['conciseness_score'] / 100.0)

            st.markdown("---")
            st.markdown("#### Quick Summary")
            # Displaying strengths as a quick highlight
            if feedback.get("strengths"):
                st.success("💪 Top Strengths:")
                for s in feedback["strengths"][:3]: # Show top 3
                    st.write(f"- {s}")
            else:
                st.info("No specific strengths highlighted yet.")

            if feedback.get("weaknesses"):
                st.warning("🚧 Key Areas for Improvement:")
                for w in feedback["weaknesses"][:3]: # Show top 3
                    st.write(f"- {w}")
            else:
                st.info("No specific weaknesses highlighted yet.")

        with tab2:
            st.markdown("### Comprehensive Feedback")
            
            # --- Display Feedback in HTML style ---
            def render_feedback_section_ui(title, items, emoji, default_message="No specific points identified."):
                """Renders a feedback section for the Streamlit UI."""
                if items:
                    list_items_html = "".join(f"<li>{item}</li>" for item in items)
                    return f"""
                    <div class='feedback-section'>
                        <h3>{emoji} {title}</h3>
                        <ul>{list_items_html}</ul>
                    </div>
                    """
                else:
                    return f"<div class='feedback-section'><h3>{emoji} {title}</h3><p>{default_message}</p></div>"

            # Custom CSS for Streamlit UI feedback sections
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
                    margin-bottom: 0;
                }
                .feedback-section li {
                    margin-bottom: 0.6rem;
                    line-height: 1.5;
                    color: #333333;
                    font-size: 0.95rem;
                }
                .feedback-section p {
                    color: #333333;
                    font-size: 0.95rem;
                }
                </style>
            """, unsafe_allow_html=True)

            st.markdown(render_feedback_section_ui("Strengths", feedback.get("strengths", []), "💪"), unsafe_allow_html=True)
            st.markdown(render_feedback_section_ui("Weaknesses", feedback.get("weaknesses", []), "🚧"), unsafe_allow_html=True)
            st.markdown(render_feedback_section_ui("Suggestions for Improvement", feedback.get("improvements", []), "💡"), unsafe_allow_html=True)
            st.markdown(render_feedback_section_ui("Grammar & Spelling Issues", feedback.get("grammar_spelling_issues", []), "✍", "No major grammar or spelling issues detected."), unsafe_allow_html=True)
            st.markdown(render_feedback_section_ui("Formatting & Layout Feedback", feedback.get("formatting_layout_feedback", []), "📐", "Looks good, or no specific formatting issues flagged."), unsafe_allow_html=True)

        with tab3:
            st.markdown("### Keywords & Action Verbs")
            
            st.markdown("#### Suggested Keywords/Skills")
            if feedback.get("keyword_suggestions"):
                text_for_wordcloud = " ".join([str(item) for item in feedback["keyword_suggestions"]])
                
                if text_for_wordcloud.strip():
                    try:
                        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text_for_wordcloud)
                        fig, ax = plt.subplots(figsize=(8, 4))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig)
                    except Exception as e:
                        st.warning(f"Could not generate keyword cloud. Ensure 'matplotlib' and 'wordcloud' libraries are installed. Error: {e}")
                else:
                    st.info("No keywords found to generate a word cloud.")
            else:
                st.info("No specific keywords or skills suggested.")

            st.markdown("---")
            st.markdown("#### Action Verb Suggestions")
            if feedback.get("action_verb_suggestions"):
                st.success("⚡ Consider using these strong action verbs:")
                verbs_list_html = "".join(f"<span style='background-color:#e6ffe6; border-radius:5px; padding:3px 8px; margin:3px; display:inline-block; font-size:0.9em;'>{verb}</span>" for verb in feedback["action_verb_suggestions"])
                st.markdown(f"<div>{verbs_list_html}</div>", unsafe_allow_html=True)
            else:
                st.info("No specific action verb suggestions at this time.")

        # --- Download PDF Report Button (remains at the bottom) ---
        st.markdown("---")
        st.subheader("Generate & Download Full Report")
        if st.button("Download Detailed Resume Report (PDF)"):
            with st.spinner("Generating PDF report... This might take a moment."):
                pdf_buffer = generate_pdf_report(feedback, resume_text)
            st.download_button(
                label="Download Resume Analysis Report PDF",
                data=pdf_buffer,
                file_name="resume_analysis_report.pdf",
                mime="application/pdf"
            )
            st.success("PDF report generated successfully!")

    else:
        st.warning("Could not extract readable text from the uploaded file. Please ensure it's not scanned or corrupted.")

st.markdown("---")
st.markdown("<center><i>Powered by Google Gemini AI</i></center>", unsafe_allow_html=True)

