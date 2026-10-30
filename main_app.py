import streamlit as st
import subprocess  # For running submodules
import sys         # For detecting OS

# ------------------ Page Config ------------------
st.set_page_config(
    page_title="Smart Resume & Interview Suite",
    layout="wide",
)

# ------------------ Custom CSS ------------------
st.markdown("""
    <style>
    .title {
        font-size: 50px;
        font-weight: 700;
        color: #1f7a8c;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        font-size: 20px;
        text-align: center;
        color: #555;
        margin-bottom: 40px;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        padding: 20px;
        font-size: 20px;
        border: none;
        border-radius: 12px;
        width: 100%;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #388e3c;
    }
    .footer {
        text-align: center;
        color: gray;
        padding: 20px;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------ Header ------------------
st.markdown("<div class='title'>Smart Resume & Interview Platform</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Empowering your job journey with AI-driven insights</div>", unsafe_allow_html=True)

# ------------------ Function to Launch Modules ------------------
def run_streamlit_module(module_name):
    if sys.platform == "win32":
        # Hide console window on Windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen(["streamlit", "run", module_name], startupinfo=startupinfo)
    else:
        # Run silently on Linux/macOS
        subprocess.Popen(
            ["streamlit", "run", module_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

# ------------------ Buttons ------------------
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    if st.button("📝 Resume Analyzer"):
        run_streamlit_module("module1.py")

with col2:
    if st.button("🤖 Mock Interview Chatbot"):
        run_streamlit_module("module2.py")

with col3:
    if st.button("📈 Resume Evolution Tracker"):
        run_streamlit_module("module3.py")

with col4:
    if st.button("🎙 Video Pitch Review"):
        run_streamlit_module("module4.py")

# ------------------ Footer ------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2025 Smart Resume Platform | Made with ❤ using Streamlit</div>", unsafe_allow_html=True)