# import streamlit as st
# import tempfile
# import cv2
# import numpy as np
# import requests
# import json
# import os
# import atexit

# # Use a valid and recent model name.
# # The API URL will be constructed dynamically in the function.
# MODEL_NAME = "gemini-1.5-flash-latest"
# GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# st.set_page_config(page_title="Interview Body Language Coach", page_icon="�", layout="centered")
# st.title("Interview Body Language Coach")
# st.info("This app uses OpenCV for local video analysis and the Gemini API for generating feedback.")

# # Initialize session state for the video path
# if 'video_path' not in st.session_state:
#     st.session_state.video_path = None

# api_key = st.text_input("Enter your Gemini API Key:", type="password")
# if not api_key:
#     st.warning("Please enter your Gemini API Key from https://aistudio.google.com/app/apikey to get AI feedback.")

# uploaded_file = st.file_uploader(
#     "Upload a short video of yourself (up to 60 seconds)",
#     type=["mp4", "mov", "avi", "webm"],
# )

# # --- File Cleanup ---
# # Function to clean up the temporary file
# def cleanup_tempfile():
#     try:
#         if st.session_state.video_path and os.path.exists(st.session_state.video_path):
#             os.unlink(st.session_state.video_path)
#             st.session_state.video_path = None
#     except Exception as e:
#         # Silently pass on cleanup errors
#         pass

# # Register the cleanup function to be called on exit
# atexit.register(cleanup_tempfile)


# if uploaded_file is not None:
#     # Clean up any previous file before creating a new one
#     cleanup_tempfile()

#     with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
#         tfile.write(uploaded_file.read())
#         st.session_state.video_path = tfile.name
    
#     st.video(st.session_state.video_path)

# # Use OpenCV's built-in haarcascade paths
# CASCADE_PATH = cv2.data.haarcascades

# def analyze_video_opencv(path: str) -> dict:
#     """Analyzes the video to detect face, head movement, hands, and fidgeting."""
#     face_cascade = cv2.CascadeClassifier(os.path.join(CASCADE_PATH, 'haarcascade_frontalface_default.xml'))
    
#     # Note: haarcascade_hand.xml is not always included with OpenCV.
#     # This code checks for its existence. Hand detection will be skipped if not found.
#     hand_cascade_path = os.path.join(CASCADE_PATH, 'haarcascade_hand.xml')
#     hand_cascade = cv2.CascadeClassifier(hand_cascade_path) if os.path.exists(hand_cascade_path) else None

#     if not path or not os.path.exists(path):
#         st.error("Video file not found.")
#         return {}

#     cap = cv2.VideoCapture(path)
#     frame_count = 0
#     face_present_frames = 0
#     head_moving_frames = 0
#     last_face_pos = None
#     hand_present_frames = 0
#     fidgeting_frames = 0
#     prev_gray = None

#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             break
        
#         frame_count += 1
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         gray = cv2.equalizeHist(gray) # Improve contrast

#         # --- Face Detection and Head Movement ---
#         faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
#         if len(faces) > 0:
#             face_present_frames += 1
#             (x, y, w, h) = faces[0] # Assume one primary face
#             center = (x + w // 2, y + h // 2)
            
#             if last_face_pos is not None:
#                 # Calculate movement relative to face size to avoid detecting minor jitters
#                 movement_threshold = max(10, w * 0.08) 
#                 movement = np.linalg.norm(np.array(center) - np.array(last_face_pos))
#                 if movement > movement_threshold:
#                     head_moving_frames += 1
#             last_face_pos = center
#         else:
#             last_face_pos = None

#         # --- Hand Detection (if cascade file is available) ---
#         if hand_cascade is not None:
#             hands = hand_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
#             if len(hands) > 0:
#                 hand_present_frames += 1

#         # --- Fidgeting Detection (Frame-to-frame difference) ---
#         if prev_gray is not None:
#             diff = cv2.absdiff(prev_gray, gray)
#             # A mean difference > 15 suggests significant motion (potential fidgeting)
#             if np.mean(diff) > 15:
#                 fidgeting_frames += 1
#         prev_gray = gray

#     cap.release()
#     return {
#         "frame_count": frame_count,
#         "face_present_frames": face_present_frames,
#         "head_moving_frames": head_moving_frames,
#         "hand_present_frames": hand_present_frames,
#         "fidgeting_frames": fidgeting_frames,
#         "hand_detection_available": hand_cascade is not None
#     }

# def build_body_language_summary(stats: dict) -> str:
#     """Creates a human-readable summary from the analysis statistics."""
#     if not stats or stats.get('frame_count', 0) == 0:
#         return "Could not analyze the video. No frames were detected."

#     frame_count = stats['frame_count']
#     face_pct = 100 * stats['face_present_frames'] / frame_count
#     head_move_pct = 100 * stats['head_moving_frames'] / max(stats['face_present_frames'], 1)
#     hand_pct = 100 * stats['hand_present_frames'] / frame_count
#     fidget_pct = 100 * stats['fidgeting_frames'] / frame_count

#     summary = (
#         f"- Face was detected in {face_pct:.1f}% of the video.\n"
#         f"- Significant head movement (nodding/shaking) was detected in {head_move_pct:.1f}% of the frames where a face was visible.\n"
#         f"- Possible fidgeting or large body movements were detected in {fidget_pct:.1f}% of the video.\n"
#     )
#     if stats["hand_detection_available"]:
#          summary += f"- Hands were detected in {hand_pct:.1f}% of the video.\n"
#     else:
#         summary += "- Hand detection was skipped because the required 'haarcascade_hand.xml' was not found.\n"

#     # Add some basic interpretations
#     if face_pct < 80:
#         summary += "\n**Suggestion:** Try to keep your face centered and in view of the camera more consistently.\n"
#     if head_move_pct < 10:
#         summary += "**Suggestion:** Consider using occasional nods to show you are actively listening and engaged.\n"
#     if fidget_pct > 25:
#         summary += "**Suggestion:** The analysis detected a high degree of movement. Try to reduce fidgeting to project more confidence and calm.\n"

#     return summary

# def get_gemini_feedback(summary: str, api_key: str) -> str:
#     """Sends the summary to the Gemini API for professional feedback."""
#     # Construct the correct API URL with the specified model
#     url = f"{GEMINI_API_BASE_URL}/{MODEL_NAME}:generateContent?key={api_key}"
    
#     headers = {"Content-Type": "application/json"}

#     prompt = (
#         "You are an expert interview and communication coach. Your tone is encouraging, professional, and constructive. "
#         "Based on the following quantitative analysis of a person's body language from a video, provide actionable "
#         "and insightful feedback to help them improve their non-verbal communication in a job interview. "
#         "Focus on what the data implies (e.g., low head movement might mean lack of engagement, high fidgeting might mean nervousness). "
#         "Organize your feedback into clear, bulleted points.\n\n"
#         "**Body Language Analysis Summary:**\n"
#         f"{summary}\n\n"
#         "**Your Expert Feedback:**"
#     )
    
#     data = {"contents": [{"parts": [{"text": prompt}]}]}
    
#     try:
#         # Use json parameter to automatically handle serialization and headers
#         response = requests.post(url, headers=headers, json=data, timeout=60)
#         response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

#         completion = response.json()
#         return completion['candidates'][0]['content']['parts'][0]['text']

#     except requests.exceptions.HTTPError as http_err:
#         return f"Error from Gemini API: {http_err}\nResponse: {response.text}"
#     except requests.exceptions.RequestException as e:
#         return f"Failed to call Gemini API: {e}"
#     except (KeyError, IndexError) as e:
#         return f"Received an unexpected or malformed response from Gemini API: {e}"
#     except Exception as e:
#         return f"An unexpected error occurred: {e}"


# if st.session_state.video_path and api_key:
#     if st.button("Analyze My Body Language", type="primary"):
#         with st.spinner("Analyzing video with OpenCV... This may take a moment."):
#             stats = analyze_video_opencv(st.session_state.video_path)
        
#         if stats:
#             summary = build_body_language_summary(stats)
#             st.subheader("📊 Body Language Analysis")
#             st.markdown(summary)

#             with st.spinner("🤖 Getting feedback from Gemini AI..."):
#                 feedback = get_gemini_feedback(summary, api_key)
#                 st.subheader("🧠 Gemini AI Coach Feedback")
#                 st.markdown(feedback)
#         else:
#             st.error("Failed to process the video.")

# elif st.session_state.video_path and not api_key:
#     st.info("Please enter your API key above to enable the analysis button.")



import streamlit as st
import tempfile
import cv2
import numpy as np
import requests
import json
import os
import atexit
import pandas as pd
import altair as alt

# Use a valid and recent model name.
# The API URL will be constructed dynamically in the function.
MODEL_NAME = "gemini-1.5-flash-latest"
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

st.set_page_config(page_title="Interview Body Language Coach", page_icon="🎥", layout="wide")
st.title("Interview Body Language Coach")
st.info("This app uses OpenCV for local video analysis and the Gemini API for generating feedback. Upload a video, enter your API key, and click 'Analyze' to see your results.")

# Initialize session state for the video path
if 'video_path' not in st.session_state:
    st.session_state.video_path = None

# --- UI Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    api_key = st.text_input("Enter your Gemini API Key:", type="password")
    if not api_key:
        st.warning("Please enter your Gemini API Key from https://aistudio.google.com/app/apikey to get AI feedback.")

    uploaded_file = st.file_uploader(
        "Upload a short video of yourself (up to 60 seconds)",
        type=["mp4", "mov", "avi", "webm"],
    )

# --- File Cleanup ---
# Function to clean up the temporary file
def cleanup_tempfile():
    try:
        if st.session_state.video_path and os.path.exists(st.session_state.video_path):
            os.unlink(st.session_state.video_path)
            st.session_state.video_path = None
    except Exception as e:
        # Silently pass on cleanup errors
        pass

# Register the cleanup function to be called on exit
atexit.register(cleanup_tempfile)


if uploaded_file is not None:
    # Clean up any previous file before creating a new one
    cleanup_tempfile()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
        tfile.write(uploaded_file.read())
        st.session_state.video_path = tfile.name
    
    with col1:
        st.video(st.session_state.video_path)

# Use OpenCV's built-in haarcascade paths
CASCADE_PATH = cv2.data.haarcascades

def analyze_video_opencv(path: str, progress_bar) -> dict:
    """Analyzes the video to detect face, head movement, hands, and fidgeting."""
    face_cascade = cv2.CascadeClassifier(os.path.join(CASCADE_PATH, 'haarcascade_frontalface_default.xml'))
    hand_cascade_path = os.path.join(CASCADE_PATH, 'haarcascade_hand.xml')
    hand_cascade = cv2.CascadeClassifier(hand_cascade_path) if os.path.exists(hand_cascade_path) else None

    if not path or not os.path.exists(path):
        st.error("Video file not found.")
        return {}

    cap = cv2.VideoCapture(path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_count = 0
    face_present_frames = 0
    head_moving_frames = 0
    last_face_pos = None
    hand_present_frames = 0
    fidgeting_frames = 0
    prev_gray = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        progress_bar.progress(frame_count / total_frames)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
        if len(faces) > 0:
            face_present_frames += 1
            (x, y, w, h) = faces[0]
            center = (x + w // 2, y + h // 2)
            
            if last_face_pos is not None:
                movement_threshold = max(10, w * 0.08) 
                movement = np.linalg.norm(np.array(center) - np.array(last_face_pos))
                if movement > movement_threshold:
                    head_moving_frames += 1
            last_face_pos = center
        else:
            last_face_pos = None

        if hand_cascade is not None:
            hands = hand_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            if len(hands) > 0:
                hand_present_frames += 1

        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            if np.mean(diff) > 15:
                fidgeting_frames += 1
        prev_gray = gray

    cap.release()
    return {
        "frame_count": frame_count,
        "face_present_frames": face_present_frames,
        "head_moving_frames": head_moving_frames,
        "hand_present_frames": hand_present_frames,
        "fidgeting_frames": fidgeting_frames,
        "hand_detection_available": hand_cascade is not None
    }

def create_charts(stats: dict):
    """Creates Altair charts from the analysis statistics."""
    if not stats or stats.get('frame_count', 0) == 0:
        return None, None

    frame_count = stats['frame_count']
    face_pct = 100 * stats['face_present_frames'] / frame_count
    head_move_pct = 100 * stats['head_moving_frames'] / max(stats['face_present_frames'], 1)
    fidget_pct = 100 * stats['fidgeting_frames'] / frame_count
    
    data = [
        {"Metric": "Face Presence", "Percentage": face_pct, "Goal": 80},
        {"Metric": "Head Movement", "Percentage": head_move_pct, "Goal": 10},
        {"Metric": "Low Fidgeting", "Percentage": 100 - fidget_pct, "Goal": 75}
    ]
    if stats["hand_detection_available"]:
        hand_pct = 100 * stats['hand_present_frames'] / frame_count
        data.append({"Metric": "Hand Presence", "Percentage": hand_pct, "Goal": 20})

    df = pd.DataFrame(data)

    # --- Bar Chart ---
    bar_chart = alt.Chart(df).mark_bar(size=40).encode(
        x=alt.X('Percentage:Q', title='Percentage of Time (%)', scale=alt.Scale(domain=[0, 100])),
        y=alt.Y('Metric:N', title='Body Language Metric', sort='-x'),
        color=alt.condition(
            alt.datum.Percentage >= alt.datum.Goal,
            alt.value('green'),
            alt.value('salmon')
        ),
        tooltip=['Metric', 'Percentage']
    ).properties(
        title='Body Language Metrics Overview'
    )

    # --- Composure Gauge Chart ---
    # A simple score: high face presence and low fidgeting are good.
    composure_score = (face_pct + (100 - fidget_pct)) / 2
    
    gauge_data = pd.DataFrame([{"title": "Overall Composure", "value": composure_score}])
    
    base = alt.Chart(gauge_data).encode(
        theta=alt.Theta("value:Q", scale=alt.Scale(domain=[0, 100], range=[180, 0])),
        color=alt.Color("value:Q", scale=alt.Scale(domain=[0, 50, 75, 100], range=['red', 'orange', 'yellow', 'green']), legend=None)
    )
    
    arc = base.mark_arc(outerRadius=100)
    text = base.mark_text(radius=80, fontSize=20).encode(text=alt.Text("value:Q", format=".1f"))
    
    gauge_chart = (arc + text).properties(title="Overall Composure Score")

    return bar_chart, gauge_chart


def build_body_language_summary(stats: dict) -> str:
    """Creates a human-readable summary from the analysis statistics."""
    if not stats or stats.get('frame_count', 0) == 0:
        return "Could not analyze the video. No frames were detected."

    frame_count = stats['frame_count']
    face_pct = 100 * stats['face_present_frames'] / frame_count
    head_move_pct = 100 * stats['head_moving_frames'] / max(stats['face_present_frames'], 1)
    fidget_pct = 100 * stats['fidgeting_frames'] / frame_count

    summary = (
        f"- **Face Presence**: Detected in **{face_pct:.1f}%** of the video.\n"
        f"- **Head Movement**: Detected in **{head_move_pct:.1f}%** of frames with a visible face.\n"
        f"- **Fidgeting/Motion**: Detected in **{fidget_pct:.1f}%** of the video.\n"
    )
    if stats["hand_detection_available"]:
        hand_pct = 100 * stats['hand_present_frames'] / frame_count
        summary += f"- **Hand Presence**: Detected in **{hand_pct:.1f}%** of the video.\n"
    else:
        summary += "- **Hand Detection**: Skipped as 'haarcascade_hand.xml' was not found.\n"
    return summary

def get_gemini_feedback(summary: str, api_key: str) -> str:
    """Sends the summary to the Gemini API for professional feedback."""
    url = f"{GEMINI_API_BASE_URL}/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    prompt = (
        "You are an expert interview and communication coach. Your tone is encouraging, professional, and constructive. "
        "Based on the following quantitative analysis of a person's body language from a video, provide actionable "
        "and insightful feedback to help them improve their non-verbal communication in a job interview. "
        "Focus on what the data implies (e.g., low head movement might mean lack of engagement, high fidgeting might mean nervousness). "
        "Organize your feedback into clear, bulleted points.\n\n"
        "**Body Language Analysis Summary:**\n"
        f"{summary}\n\n"
        "**Your Expert Feedback:**"
    )
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        completion = response.json()
        return completion['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.HTTPError as http_err:
        return f"Error from Gemini API: {http_err}\nResponse: {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Failed to call Gemini API: {e}"
    except (KeyError, IndexError) as e:
        return f"Received an unexpected or malformed response from Gemini API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

with col1:
    if st.session_state.video_path and api_key:
        if st.button("Analyze My Body Language", type="primary", use_container_width=True):
            progress_bar = st.progress(0, text="Analyzing video...")
            stats = analyze_video_opencv(st.session_state.video_path, progress_bar)
            progress_bar.empty()
            
            with col2:
                if stats:
                    st.subheader("📊 Body Language Dashboard")
                    
                    summary = build_body_language_summary(stats)
                    bar_chart, gauge_chart = create_charts(stats)

                    chart_col, summary_col = st.columns(2)
                    with chart_col:
                        if gauge_chart:
                            st.altair_chart(gauge_chart, use_container_width=True)
                    with summary_col:
                        st.markdown("### Key Metrics")
                        st.markdown(summary)

                    if bar_chart:
                        st.altair_chart(bar_chart, use_container_width=True)

                    with st.spinner("🤖 Getting feedback from Gemini AI..."):
                        feedback = get_gemini_feedback(summary, api_key)
                    
                    st.markdown("---")
                    st.subheader("🧠 Gemini AI Coach Feedback")
                    st.markdown(feedback)
                else:
                    st.error("Failed to process the video.")

    elif st.session_state.video_path and not api_key:
        st.info("Please enter your API key to enable the analysis button.")