import streamlit as st
import requests
import json
import io
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av # Python library for audio/video processing, used by streamlit-webrtc

# --- Configuration (for local execution) ---
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" # Replace with your actual Gemini API Key
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- Streamlit App Layout ---
st.set_page_config(
    page_title="Interview Body Language Coach",
    page_icon="🎥",
    layout="centered"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main .block-container {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-width: 700px;
        margin: auto;
    }
    h1 {
        text-align: center;
        font-size: 2.5em;
        color: #1a202c;
        margin-bottom: 0.5em;
        background: linear-gradient(to right, #2563eb, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    p {
        text-align: center;
        color: #4a5568;
        margin-bottom: 1.5em;
    }
    .stFileUploader label, .stTextInput label {
        font-weight: 500;
        color: #2d3748;
        margin-bottom: 0.5em;
        display: block;
    }
    .stVideo {
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        width: 100%;
        max-height: 400px;
        margin-bottom: 1.5em;
    }
    .stButton>button {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0.75em 1.5em;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        color: white;
        background-image: linear-gradient(to right, #3b82f6, #8b5cf6);
        transition: all 0.3s ease-in-out;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        cursor: pointer;
    }
    .stButton>button:hover {
        background-image: linear-gradient(to right, #2563eb, #7c3aed);
    }
    .stButton>button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        background-image: linear-gradient(to right, #9ca3af, #6b7280);
    }
    .stAlert {
        margin-top: 1.5em;
        border-radius: 8px;
    }
    .feedback-box {
        margin-top: 1.5em;
        padding: 2em;
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .feedback-box h2 {
        color: #1e40af;
        font-size: 1.5em;
        font-weight: 700;
        margin-bottom: 1em;
    }
    .feedback-box p {
        text-align: left;
        color: #374151;
        line-height: 1.6;
        margin-bottom: 0.5em;
    }
    .footer-text {
        text-align: center;
        color: #6b7280;
        font-size: 0.875em;
        margin-top: 2em;
    }
    .webrtc-container {
        margin-top: 1.5em;
        margin-bottom: 1.5em;
        padding: 1em;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background-color: #f7fafc;
        text-align: center;
    }
    .webrtc-container h3 {
        color: #1a202c;
        margin-bottom: 1em;
    }
</style>
""", unsafe_allow_html=True)


st.title("Interview Body Language Coach")
st.markdown("""
    Access your camera to record a short video, then get AI-powered feedback on your body language for interview skills.
    <br/>
    <span style="font-size: 0.875em; color: red; font-weight: bold;">
        Note: Actual video analysis is simulated in this demo.
    </span>
    """, unsafe_allow_html=True)

# Gemini API Key input
api_key_input = st.text_input(
    "Enter your Gemini API Key:",
    type="password",
    value=st.session_state.get('gemini_api_key', GEMINI_API_KEY if "YOUR_GEMINI_API_KEY_HERE" not in GEMINI_API_KEY else ""),
    help="You can get your API key from Google AI Studio (https://aistudio.google.com/app/apikey)."
)
if api_key_input and "YOUR_GEMINI_API_KEY_HERE" not in api_key_input:
    st.session_state.gemini_api_key = api_key_input
else:
    st.session_state.gemini_api_key = ""
    if st.button("Get API Key"):
        st.link_button("Go to Google AI Studio", "https://aistudio.google.com/app/apikey")

# --- Webcam Integration with streamlit-webrtc ---
st.markdown('<div class="webrtc-container">', unsafe_allow_html=True)
st.markdown('<h3>Live Camera Feed</h3>', unsafe_allow_html=True)
st.write("Grant camera access to start recording.")

# Session state to store recorded video bytes
if 'recorded_video_bytes' not in st.session_state:
    st.session_state.recorded_video_bytes = None

webrtc_ctx = webrtc_streamer(
    key="body-language-webrtc-stream",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTCConfiguration(
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    ),
    media_stream_constraints={"video": True, "audio": True},
    async_processing=True,
    video_html_attrs={"controls": True, "autoplay": True, "playsinline": True},
)

# After recording, the recorded_video_bytes will be available
if webrtc_ctx.video_receiver:
    try:
        video_frame_buffer = []
        # This loop captures frames if `webrtc_streamer` is in record mode and
        # a recording is being made.
        # However, `streamlit-webrtc` does not expose the recorded bytes directly
        # for post-processing in a simple way for the record button.
        # The typical use case is for real-time frame processing via a VideoProcessor.
        # For saving a file, `streamlit-webrtc` usually handles the download.
        # We'll adapt the logic: if a file was downloaded, we'll imagine it was "recorded".
        st.info("Start the camera and use the 'Record' button in the video player to save a clip.")
        st.warning("Note: `streamlit-webrtc`'s 'Record' button directly downloads the video. For this demo, imagine that downloaded video is what we're 'analyzing'.")

        # To make "Get Body Language Feedback" button work immediately after recording,
        # the user would typically re-upload the downloaded file, or we'd need a more
        # complex backend to intercept the stream.
        # For simplicity, we'll keep the file uploader for demonstration after recording,
        # or rely on the user to use the previous file upload logic.
        # A more advanced real-time system would capture frames and analyze them live.

    except Exception as e:
        st.error(f"Error handling video stream: {e}")

st.markdown('</div>', unsafe_allow_html=True) # End of webrtc-container


# --- File Uploader (kept for compatibility with previous logic, and if user wants to upload recorded file) ---
st.markdown('<h3 style="text-align: center; color: #1a202c; margin-top: 1.5em; margin-bottom: 1em;">Or Upload a Video File</h3>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Upload a pre-recorded video (e.g., one saved from the live camera above)",
    type=["mp4", "mov", "avi", "webm"],
    help="Supported formats: MP4, MOV, AVI, WebM."
)

video_bytes = None
file_name = None

if uploaded_file is not None:
    video_bytes = uploaded_file.read()
    file_name = uploaded_file.name
    st.markdown('<h3 style="text-align: center; color: #1a202c; margin-top: 1.5em; margin-bottom: 1em;">Uploaded Video Preview</h3>', unsafe_allow_html=True)
    st.video(video_bytes)
    st.info(f"File: {file_name} ({len(video_bytes) / (1024 * 1024):.2f} MB)")
    st.warning("Note: Streamlit's `st.video` does not provide direct duration metadata in the frontend. For a real system, video duration would be checked on the backend.")


# --- Review Button and Logic ---
# The button is disabled if no file is uploaded or API key is missing.
# For 'live' scenario, the user would need to record and then upload the downloaded file.
if st.button("Get Body Language Feedback", disabled=uploaded_file is None or not st.session_state.gemini_api_key):
    if not st.session_state.gemini_api_key:
        st.error("Please enter your Gemini API Key to get feedback.")
    elif uploaded_file is None:
        st.error("Please upload a video file (or record and re-upload) to get feedback.")
    else:
        with st.spinner("Reviewing Video... This may take a moment."):
            try:
                # --- SIMULATION OF VIDEO ANALYSIS ---
                # This part remains a simulation. In a true real-time system,
                # you would continuously analyze frames from the `webrtc_streamer`
                # (e.g., using `VideoProcessorBase` class with OpenCV/MediaPipe)
                # and then summarize the observations for the LLM.

                # For this demo, we use hardcoded, plausible observations as a placeholder.
                # These observations can be adjusted to seem like they came from a live analysis.
                simulated_observations = f"""
                Observations from a short recorded video (approx. 30-60 seconds):
                The individual appeared to maintain consistent eye contact for approximately 70% of the recording duration, showing good engagement.
                Hand gestures were natural and used appropriately to emphasize points, without being distracting.
                Posture remained generally open and confident.
                There was minimal fidgeting observed, suggesting a calm demeanor.
                Facial expressions were generally positive and responsive, including smiles at appropriate moments.
                Vocal clarity was good, though slight variations in speaking pace were noted, which could be consciously managed for optimal impact.
                """

                # Construct the prompt for the LLM, adjusted for a "live" feedback feel
                prompt = f"""
                You are an experienced interview coach providing immediate feedback on body language from a recent, short video recording.
                Analyze the following simulated observations from the recording and provide concise, actionable feedback on their body language, focusing on interview performance.
                Highlight strengths and suggest specific areas for improvement, such as eye contact, posture, gestures, confidence, and nervous habits.

                Simulated Body Language Observations from Live Recording:
                {simulated_observations}

                Please structure your feedback with clear points and actionable advice, suitable for immediate review.
                """

                headers = {
                    'Content-Type': 'application/json',
                }
                params = {'key': st.session_state.gemini_api_key}
                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": prompt}]
                        }
                    ]
                }

                response = requests.post(
                    url=GEMINI_API_URL,
                    headers=headers,
                    params=params,
                    data=json.dumps(payload)
                )
                response.raise_for_status()

                result = response.json()

                if result.get('candidates') and len(result['candidates']) > 0 and \
                   result['candidates'][0].get('content') and \
                   result['candidates'][0]['content'].get('parts') and \
                   len(result['candidates'][0]['content']['parts']) > 0:
                    feedback_text = result['candidates'][0]['content'].parts[0]['text']
                    st.session_state.feedback = feedback_text
                else:
                    st.error("Could not get feedback from the AI. The response structure was unexpected.")
                    print("Unexpected API response structure:", result)
                    st.session_state.feedback = None

            except requests.exceptions.RequestException as e:
                st.error(f"Failed to get feedback from AI: Network or API error. Details: {e}")
                st.session_state.feedback = None
            except json.JSONDecodeError:
                st.error("Failed to decode JSON response from AI. Please check API key and network.")
                st.session_state.feedback = None
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.session_state.feedback = None

# --- Display Feedback ---
if st.session_state.get('feedback'):
    st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
    st.markdown('<h2 style="margin-bottom: 0.5em;">AI Feedback:</h2>', unsafe_allow_html=True)
    for paragraph in st.session_state.feedback.split('\n'):
        st.write(paragraph)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Footer ---
st.markdown(
    """
    <div class="footer-text">
        <p>This is a simulated demo. Actual live video analysis requires a complex backend system.</p>
        <p>App ID: default-app-id (mock for local environment)</p>
    </div>
    """, unsafe_allow_html=True
)
