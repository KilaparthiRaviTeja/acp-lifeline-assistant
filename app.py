import streamlit as st
from PIL import Image
import imagehash
import time
import json
import requests
#from streamlit_lottie import st_lottie

# --- Setup ---
st.set_page_config(layout="centered")
st.markdown("""
    <style>
        .chat-container {
            max-width: 600px;
            margin: auto;
            padding: 1rem;
            font-family: 'Arial', sans-serif;
        }
        .chat-message {
            margin-bottom: 1rem;
        }
        .user-message {
            text-align: right;
            color: blue;
        }
        .assistant-message {
            text-align: left;
            color: green;
        }
        .step-tracker {
            display: flex;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        .step {
            flex: 1;
            text-align: center;
            padding: 0.5rem;
            border-bottom: 2px solid lightgray;
        }
        .step.active {
            border-bottom: 2px solid blue;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# --- Session state initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "step" not in st.session_state:
    st.session_state.step = "start"

if "id_type" not in st.session_state:
    st.session_state.id_type = None

if "id_value" not in st.session_state:
    st.session_state.id_value = None

if "photo" not in st.session_state:
    st.session_state.photo = None

if "photo_hashes" not in st.session_state:
    st.session_state.photo_hashes = set()

if "service" not in st.session_state:
    st.session_state.service = None

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = "👤"

# --- Helper functions ---
def chat_message(sender, message, avatar=None):
    with st.chat_message(sender, avatar=avatar):
        st.markdown(message)

def add_to_history(sender, message, avatar=None):
    st.session_state.chat_history.append((sender, message, avatar))
    chat_message(sender, message, avatar)

def reset_photo():
    st.session_state.photo = None

def check_duplicate(photo):
    hash_val = imagehash.average_hash(photo)
    if str(hash_val) in st.session_state.photo_hashes:
        return True
    else:
        st.session_state.photo_hashes.add(str(hash_val))
        return False

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# --- Visual Step Tracker ---
def display_step_tracker(current_step):
    steps = ["Start", "Select ID", "Enter ID", "Upload Photo", "Confirm Photo", "Check Duplicate", "Select Service", "Submit", "End"]
    step_index = steps.index(current_step) if current_step in steps else 0
    st.markdown('<div class="step-tracker">', unsafe_allow_html=True)
    for i, step in enumerate(steps):
        class_attr = "step active" if i == step_index else "step"
        st.markdown(f'<div class="{class_attr}">{step}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Replay chat history on rerun ---
for sender, message, avatar in st.session_state.chat_history:
    chat_message(sender, message, avatar)

# --- Chatbot Flow ---
display_step_tracker(st.session_state.step)

if st.session_state.step == "start":
    st_lottie(load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_mDnmhAgZkb.json"), height=100)
    st.session_state.user_name = st.text_input("Please enter your name:")
    if st.session_state.user_name:
        st.session_state.user_avatar = st.selectbox("Choose your avatar:", ["👩", "👨", "🧑", "👧", "👦", "🧔", "👵", "👴"])
        add_to_history("assistant", f"Welcome {st.session_state.user_name}! Are you a new or existing applicant? 😊", "🤖")
        col1, col2 = st.columns(2)
        if col1.button("🆕 New"):
            st.session_state.step = "select_id"
            st.rerun()
        if col2.button("🧑‍💼 Existing"):
            st.session_state.step = "select_id"
            st.rerun()

elif st.session_state.step == "select_id":
    add_to_history("assistant", "Please select your ID type:", "🤖")
    id_type = st.radio("ID Type", ["Tribal ID", "Social Security Number (SSN)"], key="id_type_radio")
    if id_type:
        st.session_state.id_type = id_type
        st.session_state.step = "enter_id"
        st.rerun()

elif st.session_state.step == "enter_id":
    add_to_history("assistant", f"Enter your {st.session_state.id_type}:", "🤖")
    id_input = st.text_input(f"{st.session_state.id_type}:", key="id_input")
    if id_input:
        st.session_state.id_value = id_input
        st.session_state.step = "upload_photo"
        st.rerun()

elif st.session_state.step == "upload_photo":
    add_to_history("assistant", "📷 Please upload a photo of your ID", "🤖")
    uploaded = st.file_uploader("Upload ID photo", type=["png", "jpg", "jpeg"])
    if uploaded:
        image = Image.open(uploaded)
        st.session_state.photo = image
        st.session_state.step = "preview_photo"
        st.rerun()

elif st.session_state.step == "preview_photo":
    if st.session_state.photo:
        st.image(st.session_state.photo, caption="Uploaded ID Photo", use_column_width=True)
        col1, col2 = st.columns(2)
        if col1.button("🔄 Re-upload"):
            reset_photo()
            st.session_state.step = "upload_photo"
            st.rerun()
        if col2.button("✅ Confirm"):
            st.session_state.step = "check_duplicate"
            st.rerun()

elif st.session_state.step == "check_duplicate":
    add_to_history("assistant", "🔍 Checking for duplicate records...", "🤖")
    time.sleep(2)
    if check_duplicate(st.session_state.photo):
        st.error("⚠️ Duplicate ID photo detected. Please upload a different one.")
        st.session_state.step = "upload_photo"
    else:
        st.success("✅ No duplicate found. Proceeding to service selection.")
        st.session_state.step = "select_service"
    st.rerun()

elif st.session_state.step == "select_service":
    add_to_history("assistant", "Which service would you like to apply for?", "🤖")
    service = st.radio("Select a service", ["Affordable Connectivity Program (ACP)", "Lifeline"], key="service_select")
    if service:
        st.session_state.service = service
        st.session_state.step = "submit_nlad"
        st.rerun()

elif st.session_state.step == "submit_nlad":
    add_to_history("assistant", f"📤 Submitting your application to NLAD for {st.session_state.service}...", "🤖")
    st.info("Submission in progress... Estimated time: 5 seconds.")
    time.sleep(5)
    st.success("✅ Submitted successfully to NLAD!")
    st.session_state.step = "end"
    st.rerun()

elif st.session_state.step == "end":
    add_to_history("assistant", f"🎉 You're all set, {st.session_state.user_name}! Thank you for using our chatbot.", "🤖")
    if st.button("🚪 Exit"):
        st.session_state.clear()
        st.rerun()

# --- Persistent Chat Input Box ---
user_input = st.chat_input("Type your message here...")
if user_input:
    add_to_history("user", user_input, st.session_state.user_avatar)
    # Here you can add logic to handle user input

# --- Chat Export ---
if st.button("Download Chat History"):
    chat_text = "\n".join([f"{sender}: {message}" for sender, message, _ in st.session_state.chat_history])
    st.download_button("Download Chat", chat_text, file_name="chat_history.txt")
