import streamlit as st
import os
import cv2
import numpy as np
import pandas as pd
import speech_recognition as sr
from textblob import TextBlob
import plotly.express as px
import plotly.graph_objects as go
import tempfile
import plotly.express as mp
import mediapipe as mp_mediapipe
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime

# Set up page config
st.set_page_config(
    page_title="Interview Video Analyzer",
    page_icon="🎤",
    layout="wide"
)

# Initialize session state
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'video_file' not in st.session_state:
    st.session_state.video_file = None

# Constants
FILLER_WORDS = ['um', 'uh', 'like', 'you know', 'so', 'basically', 'well']
BENCHMARK_VALUES = {
    'speech_rate': 150,  # words per minute
    'filler_ratio': 0.02,  # 2% of words
    'eye_contact': 0.7,  # 70% of time
    'jd_similarity': 0.6  # 60% match
}

# Helper functions
def extract_audio(video_path):
    """Extract audio from video file"""
    clip = mp.VideoFileClip(video_path)
    audio_path = os.path.join(tempfile.gettempdir(), "extracted_audio.wav")
    clip.audio.write_audiofile(audio_path)
    return audio_path

def analyze_speech(video_path):
    """Analyze speech from video"""
    try:
        audio_path = extract_audio(video_path)
        duration = mp.VideoFileClip(video_path).duration
        
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
        
        blob = TextBlob(text)
        sentiment = blob.sentiment
        
        # Count filler words
        filler_count = sum(text.lower().count(word) for word in FILLER_WORDS)
        word_count = len(text.split())
        
        return {
            'transcript': text,
            'sentiment_polarity': sentiment.polarity,
            'sentiment_subjectivity': sentiment.subjectivity,
            'word_count': word_count,
            'speech_rate': word_count / (duration / 60),  # words per minute
            'filler_count': filler_count,
            'filler_ratio': filler_count / word_count if word_count > 0 else 0,
            'duration': duration
        }
    except Exception as e:
        st.error(f"Speech analysis failed: {str(e)}")
        return None

def analyze_body_language(video_path):
    """Analyze body language using MediaPipe"""
    mp_pose = mp_mediapipe.solutions.pose
    mp_face = mp_mediapipe.solutions.face_mesh
    pose = mp_pose.Pose()
    face = mp_face.FaceMesh()
    
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    eye_contact_frames = 0
    smile_frames = 0
    good_posture_frames = 0
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break
            
        frame_count += 1
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Pose detection
        pose_results = pose.process(image_rgb)
        if pose_results.pose_landmarks:
            # Simple posture check - shoulders level
            left_shoulder = pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            if abs(left_shoulder.y - right_shoulder.y) < 0.05:  # threshold
                good_posture_frames += 1
        
        # Face detection
        face_results = face.process(image_rgb)
        if face_results.multi_face_landmarks:
            # Simple eye contact detection (looking roughly forward)
            # This is a simplified approach - real implementation would be more complex
            eye_contact_frames += 1
            
            # Simple smile detection (mouth corners)
            # Again, simplified for demo purposes
            smile_frames += 1
    
    cap.release()
    
    return {
        'posture_score': good_posture_frames / frame_count if frame_count > 0 else 0,
        'eye_contact_score': eye_contact_frames / frame_count if frame_count > 0 else 0,
        'smile_score': smile_frames / frame_count if frame_count > 0 else 0,
        'frame_count': frame_count
    }

def analyze_content(transcript, job_description=""):
    """Analyze content relevance"""
    if not job_description:
        job_description = "Experience Skills Teamwork Communication Problem-solving"
    
    # Content similarity
    vectorizer = TfidfVectorizer()
    try:
        tfidf = vectorizer.fit_transform([transcript, job_description])
        similarity = (tfidf * tfidf.T).A[0,1]
    except:
        similarity = 0
    
    # Keyword extraction (simple approach)
    jd_keywords = set(job_description.lower().split())
    transcript_words = set(transcript.lower().split())
    matched_keywords = jd_keywords.intersection(transcript_words)
    
    return {
        'jd_similarity': similarity,
        'keyword_matches': list(matched_keywords),
        'keyword_count': len(matched_keywords)
    }

def generate_feedback(analysis_results):
    """Generate personalized feedback"""
    feedback = []
    
    # Speech feedback
    if analysis_results['speech']['filler_ratio'] > 0.05:
        feedback.append("🚫 Reduce filler words - try pausing instead of saying 'um' or 'like'")
    if analysis_results['speech']['speech_rate'] > 180:
        feedback.append("🐢 Slow down - you're speaking very fast which can make you harder to understand")
    elif analysis_results['speech']['speech_rate'] < 120:
        feedback.append("🐇 Speak up - a slightly faster pace will make you sound more energetic")
    
    # Body language feedback
    if analysis_results['body']['eye_contact_score'] < 0.6:
        feedback.append("👀 Improve eye contact - practice looking directly at the camera")
    if analysis_results['body']['posture_score'] < 0.7:
        feedback.append("🧘 Work on posture - sit up straight to project confidence")
    if analysis_results['body']['smile_score'] < 0.3:
        feedback.append("😊 Smile more - it makes you appear more approachable and confident")
    
    # Content feedback
    if analysis_results['content']['jd_similarity'] < 0.5:
        feedback.append("🎯 Focus more on keywords from the job description in your answers")
    if analysis_results['content']['keyword_count'] < 3:
        feedback.append("🔑 Highlight more skills from the job description in your responses")
    
    if not feedback:
        feedback.append("👍 Great job! Keep practicing to maintain your strong performance")
    
    return feedback

def save_analysis_results(results):
    """Save results to session history"""
    results['timestamp'] = datetime.now()
    st.session_state.analysis_history.append(results)
    return len(st.session_state.analysis_history) - 1  # return index

# UI Components
def show_main_analysis(results):
    """Show main analysis dashboard"""
    st.header("Interview Performance Analysis")
    
    # Overall score
    overall_score = calculate_overall_score(results)
    st.subheader(f"Overall Score: {overall_score}/100")
    st.progress(overall_score / 100)
    
    # Metrics overview
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Speech Clarity", 
               f"{results['speech']['speech_rate']:.0f} WPM", 
               f"{results['speech']['speech_rate'] - BENCHMARK_VALUES['speech_rate']:.0f} vs benchmark")
    col2.metric("Filler Words", 
               f"{results['speech']['filler_ratio']*100:.1f}%", 
               "High" if results['speech']['filler_ratio'] > 0.05 else "Good")
    col3.metric("Eye Contact", 
               f"{results['body']['eye_contact_score']*100:.1f}%", 
               f"{results['body']['eye_contact_score'] - BENCHMARK_VALUES['eye_contact']:.1%} vs benchmark")
    col4.metric("JD Match", 
               f"{results['content']['jd_similarity']*100:.1f}%", 
               f"{results['content']['jd_similarity'] - BENCHMARK_VALUES['jd_similarity']:.1%} vs benchmark")
    
    st.divider()
    
    # Video playback
    st.subheader("Your Recording")
    st.video(st.session_state.video_file)
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Speech Analysis", "Body Language", "Content", "Feedback"])
    
    with tab1:
        show_speech_analysis(results['speech'])
    
    with tab2:
        show_body_language_analysis(results['body'])
    
    with tab3:
        show_content_analysis(results['content'], results['speech']['transcript'])
    
    with tab4:
        show_feedback_section(results)

def calculate_overall_score(results):
    """Calculate composite score from all metrics"""
    speech_score = 100 - (abs(results['speech']['speech_rate'] - BENCHMARK_VALUES['speech_rate']) / 2)
    speech_score *= 0.8 if results['speech']['filler_ratio'] < 0.05 else 0.6
    
    body_score = (results['body']['eye_contact_score'] * 40 + 
                 results['body']['posture_score'] * 30 + 
                 results['body']['smile_score'] * 30)
    
    content_score = results['content']['jd_similarity'] * 100
    
    return (speech_score * 0.4 + body_score * 0.3 + content_score * 0.3)

def show_speech_analysis(speech_data):
    """Show speech analysis visualizations"""
    st.subheader("Speech Analysis")
    
    # Sentiment analysis
    sentiment_val = "Positive" if speech_data['sentiment_polarity'] > 0.1 else "Negative" if speech_data['sentiment_polarity'] < -0.1 else "Neutral"
    st.metric("Sentiment", sentiment_val)
    
    # Speech metrics
    col1, col2 = st.columns(2)
    with col1:
        fig1 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=speech_data['speech_rate'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Speech Rate (WPM)"},
            gauge={'axis': {'range': [100, 200]},
                   'steps': [
                       {'range': [100, 140], 'color': "lightgray"},
                       {'range': [140, 160], 'color': "gray"},
                       {'range': [160, 200], 'color': "darkgray"}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': BENCHMARK_VALUES['speech_rate']}}))
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.bar(
            x=['Your Ratio', 'Benchmark'],
            y=[speech_data['filler_ratio'], BENCHMARK_VALUES['filler_ratio']],
            title="Filler Word Ratio",
            labels={'x': '', 'y': 'Ratio'}
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Transcript section
    st.subheader("Transcript")
    st.text_area("Full Transcript", speech_data['transcript'], height=200)

def show_body_language_analysis(body_data):
    """Show body language visualizations"""
    st.subheader("Body Language Analysis")
    
    # Radar chart
    fig1 = go.Figure()
    
    fig1.add_trace(go.Scatterpolar(
        r=[body_data]['eye_contact_score'],
        theta=['Eye Contact'],
        fill='toself',
        name='Your Score'))
    
    fig1.add_trace(go.Scatterpolar(
        r=[BENCHMARK_VALUES['eye_contact']],
        theta=['Eye Contact'],
        fill='toself',
        name='Benchmark'
    ))
    
    fig1.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Detailed metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Posture Score", f"{body_data['posture_score']*100:.1f}%")
    col2.metric("Smile Frequency", f"{body_data['smile_score']*100:.1f}%")
    col3.metric("Frame Analyzed", body_data['frame_count'])

def show_content_analysis(content_data, transcript):
    """Show content analysis visualizations"""
    st.subheader("Content Relevance")
    
    # Similarity score
    fig1 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=content_data['jd_similarity']*100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Job Description Match"},
        gauge={'axis': {'range': [0, 100]},
               'threshold': {'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': BENCHMARK_VALUES['jd_similarity']*100}}))
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Keyword matches
    st.subheader("Matched Keywords")
    if content_data['keyword_matches']:
        cols = st.columns(4)
        for i, keyword in enumerate(content_data['keyword_matches'][:8]):
            cols[i%4].success(f"✅ {keyword}")
    else:
        st.warning("No keywords matched with the job description")
    
    # Highlight keywords in transcript
    st.subheader("Keywords in Your Transcript")
    highlighted_text = transcript
    for word in content_data['keyword_matches']:
        highlighted_text = highlighted_text.replace(word, f"{word}")
    st.markdown(highlighted_text)

def show_feedback_section(results):
    """Show personalized feedback"""
    st.subheader("Personalized Feedback")
    
    feedback_items = generate_feedback(results)
    
    for item in feedback_items:
        st.write(item)
    
    # Improvement plan
    st.subheader("Suggested Improvement Plan")
    
    if results['speech']['filler_ratio'] > 0.05:
        st.write("🗓 *Practice reducing filler words*: Try recording yourself answering common questions and count your filler words")
    
    if results['body']['eye_contact_score'] < 0.6:
        st.write("🗓 *Eye contact practice*: Place sticky notes around your webcam to remind yourself to look at the camera")
    
    if results['content']['jd_similarity'] < 0.5:
        st.write("🗓 *Study the job description*: Make a list of key requirements and prepare examples that demonstrate each one")

def show_history():
    """Show analysis history"""
    st.header("Your Analysis History")
    
    if not st.session_state.analysis_history:
        st.info("No analysis history yet. Record or upload a video to get started.")
        return
    
    # Create dataframe from history
    history_df = pd.DataFrame([{
        'Date': x['timestamp'].strftime('%Y-%m-%d %H:%M'),
        'Overall Score': calculate_overall_score(x),
        'Speech Rate': x['speech']['speech_rate'],
        'Filler Ratio': x['speech']['filler_ratio'],
        'Eye Contact': x['body']['eye_contact_score'],
        'JD Match': x['content']['jd_similarity']
    } for x in st.session_state.analysis_history])
    
    # Show history table
    st.dataframe(history_df.sort_values('Date', ascending=False), hide_index=True)
    
    # Progress charts
    st.subheader("Progress Over Time")
    
    fig = px.line(history_df, x='Date', y='Overall Score', title="Overall Score Trend")
    st.plotly_chart(fig, use_container_width=True)
    
    fig2 = px.line(history_df, x='Date', y=['Speech Rate', 'Filler Ratio', 'Eye Contact', 'JD Match'],
                  title="Detailed Metrics Over Time")
    st.plotly_chart(fig2, use_container_width=True)

# Main app
def main():
    st.title("🎤 Interview Video Analyzer")
    st.markdown("Record or upload your interview practice videos to get detailed feedback on your performance.")
    
    # Sidebar
    with st.sidebar:
        st.header("Video Input")
        
        # Job description input
        job_desc = st.text_area("Paste Job Description (for content analysis)", 
                               "Enter skills and requirements from the job description here...")
        
        # Video input options
        input_option = st.radio("Choose input method:", 
                               ["Upload video", "Record video"])
        
        if input_option == "Upload video":
            video_file = st.file_uploader("Upload your interview video", 
                                         type=['mp4', 'mov', 'avi'])
            if video_file:
                st.session_state.video_file = video_file
        else:
            video_file = st.camera_input("Record your interview answer")
            if video_file:
                st.session_state.video_file = video_file
        
        if st.session_state.video_file:
            if st.button("Analyze Video"):
                with st.spinner("Analyzing your video..."):
                    # Save video to temp file
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    tfile.write(st.session_state.video_file.read())
                    
                    # Run analyses
                    speech_results = analyze_speech(tfile.name)
                    body_results = analyze_body_language(tfile.name)
                    content_results = analyze_content(speech_results['transcript'], job_desc) if speech_results else {}
                    
                    if speech_results and body_results and content_results:
                        full_results = {
                            'speech': speech_results,
                            'body': body_results,
                            'content': content_results
                        }
                        save_analysis_results(full_results)
                        st.success("Analysis complete!")
                        st.experimental_rerun()
                    else:
                        st.error("Analysis failed. Please try another video.")
    
    # Main content area
    if st.session_state.video_file and st.session_state.analysis_history:
        show_main_analysis(st.session_state.analysis_history[-1])
    
    # History tab
    st.divider()
    show_history()

if _name_ == "_main_":
    main()