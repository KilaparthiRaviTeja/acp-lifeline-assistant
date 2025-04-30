import streamlit as st
from io import BytesIO
import re
import time
import imagehash
import base64
from PIL import Image
import hashlib
import numpy as np
import cv2

# --- Page Config ---
st.set_page_config(page_title="ACP/Lifeline Assistant", layout="wide")

# --- Style ---
st.markdown("""
    <style>
    body { background-color: white !important; color: black; }
    .chat-bubble {
        padding: 12px 16px; border-radius: 16px; margin: 8px 0;
        max-width: 75%; word-wrap: break-word; display: inline-block;
        font-size: 16px;
    }
    .bot-bubble { background-color: #f1f1f1; color: black; float: left; clear: both; }
    .user-bubble { background-color: #d1e7dd; color: black; float: right; clear: both; }
    .clearfix::after { content: ""; display: table; clear: both; }
    @media only screen and (max-width: 600px) {
        .chat-bubble {
            font-size: 14px;
            max-width: 90%;
        }
        .bot-bubble, .user-bubble {
            font-size: 14px;
            padding: 10px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if 'step' not in st.session_state:
    st.session_state.update({
        'step': 'start',
        'user_type': None,
        'id_type': None,
        'user_id': None,
        'photos': [],
        'application_type': None,
        'confirmed': False,
        'duplicate': False,
        'chat_history': [],
        'progress': 0,
        'awaiting_reset_confirm': False,
        'reminder_sent': False,
        'uploaded_hashes': [],
        'user_provider': None,
        'photo_uploaded': False
    })

# --- Sidebar ---
with st.sidebar:
    st.title("Welcome to our ACP/Lifeline Assistant.\nNeed help? Chat below!")

    if st.button("🔄 Reset Chat"):
        st.session_state.awaiting_reset_confirm = True

    if st.session_state.awaiting_reset_confirm:
        st.warning("⚠️ Are you sure you want to reset and lose your progress?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Reset"):
                def reset_session():
                    with st.spinner('Resetting chat...'):
                        time.sleep(1)
                    st.session_state.clear()
                    st.session_state.update({
                        'step': 'start',
                        'user_type': None,
                        'id_type': None,
                        'user_id': None,
                        'photos': [],
                        'application_type': None,
                        'confirmed': False,
                        'duplicate': False,
                        'chat_history': [],
                        'progress': 0,
                        'awaiting_reset_confirm': False,
                        'reminder_sent': False,
                        'uploaded_hashes': [],
                        'user_provider': None,
                        'photo_uploaded': False
                    })
                    st.rerun()
                reset_session()
        with col2:
            if st.button("❌ No, Cancel"):
                st.session_state.awaiting_reset_confirm = False

    # FAQ
    st.header("FAQ")
    faq = {
        "How do I apply for ACP or Lifeline?": "You can apply by providing your ID, uploading a photo, and confirming your details.",
        "What documents are needed for verification?": "We need either your SSN or Tribal ID, along with a recent photo.",
        "What happens after I submit my application?": "Your details are sent to NLAD for verification. Most applications are processed in 1–2 business days."
    }
    for question, answer in faq.items():
        if st.button(question):
            st.info(answer)

# --- Chat Bubble ---
def chat_bubble(message, sender='bot', save_to_history=True):
    avatar = "🤖" if sender == 'bot' else "🧑"
    bubble_class = 'bot-bubble' if sender == 'bot' else 'user-bubble'
    if sender == 'bot':
        time.sleep(0.5)
    st.markdown(
        f"""
        <div class="chat-bubble {bubble_class} clearfix">
            <strong>{avatar} {sender.capitalize()}:</strong> {message}
        </div>
        """,
        unsafe_allow_html=True
    )
    if save_to_history:
        st.session_state.chat_history.append({'text': message, 'sender': sender})

# --- Replay Chat History ---
for msg in st.session_state.chat_history:
    chat_bubble(msg['text'], sender=msg['sender'], save_to_history=False)

# --- Helpers ---
def validate_id(user_input):
    if st.session_state.id_type == 'ssn':
        return bool(re.match(r"^\d{3}-\d{2}-\d{4}$", user_input))
    elif st.session_state.id_type == 'tribal':
        return user_input.isdigit() and len(user_input) >= 5
    return False

def get_image_hash(uploaded_file):
    image = Image.open(BytesIO(uploaded_file.getvalue()))
    return str(imagehash.average_hash(image))

def generate_image_hash(image: Image) -> str:
    image = image.convert('L')
    image = image.resize((8, 8))
    image_data = np.array(image).flatten()
    
    avg = np.mean(image_data)
    diff = image_data > avg
    hash_string = ''.join(['1' if b else '0' for b in diff])
    hash_hex = hex(int(hash_string, 2))[2:]
    
    return hash_hex

def check_duplicate(user_id, photo_hashes):
    existing_records = [
        {"id": "123-45-6789", "photo_hash": "abcd1234"},
        {"id": "555-66-6777", "photo_hash": "efgh5678"},
    ]
    for record in existing_records:
        if record['id'] == user_id or record['photo_hash'] in photo_hashes:
            return True
    return False

def save_user_data():
    pass

def update_progress_bar():
    target_progress = {
        'start': 0,
        'awaiting_id': 20,
        'awaiting_photo': 50,
        'awaiting_confirmation': 80,
        'done': 100
    }.get(st.session_state.step, st.session_state.progress)

    current_progress = st.session_state.progress
    st.session_state.progress = target_progress

    progress_bar = st.empty()
    while current_progress < target_progress:
        current_progress += 2
        if current_progress > target_progress:
            current_progress = target_progress
        progress_bar.progress(current_progress)
        time.sleep(0.02)

def send_reminder():
    if st.session_state.step in ['awaiting_id', 'awaiting_photo'] and not st.session_state.reminder_sent:
        st.session_state.reminder_sent = True

def bot_reply(user_input):
    step = st.session_state.step

    if step == 'awaiting_id':
        if validate_id(user_input):
            st.session_state.user_id = user_input
            st.session_state.step = 'awaiting_photo'
            chat_bubble("✅ ID confirmed. Now please upload your photo(s) for verification.", sender='bot')
            update_progress_bar()
            st.rerun()  
        else:
            chat_bubble("⚠️ Invalid ID format.", sender='bot')

    elif step == 'awaiting_confirmation':
        if user_input.strip().lower() == 'yes':
            save_user_data()
            st.session_state.confirmed = True
            st.session_state.step = 'done'
            chat_bubble("✅ Details submitted to NLAD.", sender='bot')
        elif user_input.strip().lower() == 'no':
            chat_bubble("Okay, let us know when you're ready!", sender='bot')
        else:
            chat_bubble("⚠️ Please select 'yes' or 'no'.", sender='bot')

    elif step == 'awaiting_provider_switch':
        if user_input.strip().lower() == 'yes':
            st.session_state.step = 'done'
            chat_bubble("✅ We'll assist with switching providers.", sender='bot')
        elif user_input.strip().lower() == 'no':
            st.session_state.step = 'done'
            chat_bubble("Okay, your current provider remains active.", sender='bot')
        else:
            chat_bubble("⚠️ Please select 'yes' or 'no'.", sender='bot')


# --- Main Chat Area ---
send_reminder()

if st.session_state.step == 'start':
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = True
        chat_bubble("👋 Hi! Are you a new or existing user?", sender='bot')

    col1, col2 = st.columns(2)
    if col1.button("🆕 New"):
        st.session_state.user_type = 'new'
        st.session_state.step = 'ask_id_type'
        chat_bubble("New user selected.", sender='user')
        chat_bubble("What type of ID will you use?", sender='bot')

    if col2.button("👤 Existing"):
        st.session_state.user_type = 'existing'
        st.session_state.step = 'ask_id_type'
        chat_bubble("Existing user selected.", sender='user')
        chat_bubble("What type of ID will you use?", sender='bot')

if st.session_state.step == 'ask_id_type':
    col1, col2 = st.columns(2)
    if col1.button("SSN"):
        st.session_state.id_type = 'ssn'
        st.session_state.step = 'awaiting_id'
        chat_bubble("SSN selected.", sender='user')
        chat_bubble("Please enter your SSN (format: 123-45-6789).", sender='bot')

    if col2.button("Tribal ID"):
        st.session_state.id_type = 'tribal'
        st.session_state.step = 'awaiting_id'
        chat_bubble("Tribal ID selected.", sender='user')
        chat_bubble("Please enter your Tribal ID (at least 5 digits).", sender='bot')

if st.session_state.step == 'awaiting_id':
    with st.form("id_form", clear_on_submit=True):
        user_input = st.text_input("Enter your ID:")
        submitted = st.form_submit_button("Submit")
        if submitted:
            bot_reply(user_input)

if st.session_state.step == 'awaiting_photo':
    uploaded_files = st.file_uploader("Upload your photo(s) (jpg/png/jfif, max 5MB each)", type=["jpg", "jpeg", "png", "jfif"], accept_multiple_files=True)
    
    if uploaded_files:
        valid_files = []
        for uploaded_file in uploaded_files:
            if uploaded_file.size > 5 * 1024 * 1024:
                chat_bubble(f"⚠️ {uploaded_file.name} is too large (>5MB).", sender='bot')
            else:
                valid_files.append(uploaded_file)

        if valid_files:
            for file in valid_files:
                image = Image.open(file).convert("RGB")
                image_hash = generate_image_hash(image)

                # Check for duplicate hash
                if image_hash in st.session_state.uploaded_hashes:
                    st.warning("⚠️ This photo appears to be a duplicate.")
                    change_provider = st.radio("It seems that you already exist in the system. Do you want to change your provider?", 
                                               ["No, keep the existing provider", "Yes, change the provider"])

                    if change_provider == "Yes, change the provider":
                        st.session_state.user_provider = st.text_input("Enter your new provider name:")
                        st.success("✅ Provider changed successfully!")
                    else:
                        st.session_state.user_provider = "Existing Provider"
                        st.success("✅ Proceeding with the existing provider.")
                    st.session_state.photo_uploaded = False
                else:
                    st.session_state.uploaded_hashes.append(image_hash)
                    st.session_state.photo_uploaded = True
                    st.success("✅ Photo uploaded successfully!")

                col1, col2 = st.columns([2, 1])
                with col1:
                    st.image(image, caption="Uploaded Photo", use_column_width=True)
                with col2:
                    st.success("✅ Your photo looks clear!")

            photo_hashes = [p['hash'] for p in st.session_state.photos]
            if check_duplicate(st.session_state.user_id, photo_hashes):
                st.session_state.duplicate = True
                st.session_state.step = 'awaiting_provider_switch'
                chat_bubble("⚠️ Duplicate detected. Switch provider?", sender='bot')
            else:
                st.session_state.step = 'awaiting_confirmation'
                chat_bubble("✅ No duplicate found. Submit to NLAD?", sender='bot')

            update_progress_bar()
            st.rerun()

