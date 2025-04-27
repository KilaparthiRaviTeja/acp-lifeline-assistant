import streamlit as st
from io import BytesIO
import re
import time
import imagehash
from PIL import Image

# --- Page Config ---
st.set_page_config(page_title="ACP/Lifeline Assistant", layout="wide")

# --- Title ---
st.title("ACP/Lifeline Assistant")

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

# --- Sidebar ---
st.sidebar.title("Welcome to our ACP/Lifeline assistant. Need help? Chat below!")

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
        'reminder_sent': False
    })

# --- Existing Records (simulate database) ---
existing_records = [
    {"id": "123-45-6789", "photo_hash": "abcd1234"},
    {"id": "555-66-7777", "photo_hash": "efgh5678"},
]

# --- FAQ System ---
faq = {
    "How do I apply for ACP or Lifeline?": "You can apply by providing your ID, uploading a photo, and confirming your details.",
    "What documents are needed for verification?": "We need either your SSN or Tribal ID, along with a recent photo.",
    "What happens after I submit my application?": "Your details are sent to NLAD for verification. Most applications are processed in 1–2 business days."
}

def show_faq():
    st.sidebar.title("FAQ")
    for question, answer in faq.items():
        if st.sidebar.button(question):
            st.sidebar.write(answer)

# --- Chat Bubble ---
def chat_bubble(message, sender='bot', save_to_history=True):
    avatar = "🤖" if sender == 'bot' else "🧑"
    bubble_class = 'bot-bubble' if sender == 'bot' else 'user-bubble'
    if sender == 'bot':
        time.sleep(0.5)  # Typing delay for bot
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

# --- Progress Bar ---
st.progress(st.session_state.progress)

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

def check_duplicate(user_id, photo_hashes):
    for record in existing_records:
        if record['id'] == user_id or record['photo_hash'] in photo_hashes:
            return True
    return False

def save_user_data():
    for photo in st.session_state.photos:
        existing_records.append({
            "id": st.session_state.user_id,
            "photo_hash": get_image_hash(photo)
        })

def reset_session():
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
        'reminder_sent': False
    })
    st.experimental_rerun()

# --- Bot Logic ---
def bot_reply(user_input):
    step = st.session_state.step

    if st.session_state.awaiting_reset_confirm:
        user_response = st.text_input("Type 'yes' to confirm reset or 'no' to cancel", key="reset_input")
        
        if user_response:
            if 'yes' in user_response.lower():
                reset_session()  # Reset session and progress
            elif 'no' in user_response.lower():
                st.session_state.awaiting_reset_confirm = False
                chat_bubble("Reset cancelled.", sender='bot')
            else:
                chat_bubble("Please type 'yes' to confirm or 'no' to cancel.", sender='bot')
        return

    if step == 'awaiting_id':
        if validate_id(user_input):
            st.session_state.user_id = user_input
            st.session_state.step = 'awaiting_photo'
            st.session_state.progress = 60
            chat_bubble("✅ ID confirmed. Now please upload your photo(s) for verification.", sender='bot')
            chat_bubble("📈 Progress: 60% complete!", sender='bot')
        else:
            chat_bubble("⚠️ Please enter a valid SSN (123-45-6789) or Tribal ID (at least 5 digits).", sender='bot')

    elif step == 'awaiting_confirmation':
        if 'yes' in user_input.lower():
            save_user_data()
            st.session_state.confirmed = True
            st.session_state.step = 'done'
            chat_bubble("✅ Details sent to NLAD.", sender='bot')
            chat_bubble("📅 Most applications are processed in 1–2 business days.", sender='bot')
        elif 'no' in user_input.lower():
            chat_bubble("Okay! Let me know when you're ready.", sender='bot')
        else:
            chat_bubble("Please respond with 'yes' or 'no'.", sender='bot')

    elif step == 'awaiting_provider_switch':
        st.session_state.step = 'done'
        chat_bubble("Thanks! We'll help you switch your provider soon.", sender='bot')

    elif step == 'done':
        chat_bubble("🙏 Thank you for using the assistant. Have a great day!", sender='bot')

# --- Progress Update Enhancements ---
def update_progress_bar():
    if st.session_state.step == 'start':
        st.session_state.progress = 0
    elif st.session_state.step == 'awaiting_id':
        st.session_state.progress = 20
    elif st.session_state.step == 'awaiting_photo':
        st.session_state.progress = 50
    elif st.session_state.step == 'awaiting_confirmation':
        st.session_state.progress = 80
    elif st.session_state.step == 'done':
        st.session_state.progress = 100
    st.progress(st.session_state.progress)

# --- Automatic Reminder System ---
def send_reminder():
    if st.session_state.step in ['awaiting_id', 'awaiting_photo'] and 'reminder_sent' not in st.session_state:
        st.session_state.reminder_sent = True
        chat_bubble("⚠️ You haven't completed the process. Would you like to continue? (yes/no)", sender='bot')

# --- Reset Chat Button ---
if st.button("🔄 Reset Chat"):
    chat_bubble("⚠️ Are you sure you want to reset and lose progress? Type 'yes' to confirm or 'no' to cancel.", sender='bot')
    st.session_state.awaiting_reset_confirm = True

# --- Display FAQ on Sidebar ---
show_faq()

# --- Call the Reminder System (if needed) ---
send_reminder()

# --- Forms and Uploads ---
if st.session_state.step == 'start':
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = True
        chat_bubble("Hi there! 👋 I’m here to help you apply for ACP or Lifeline.", sender='bot')
        chat_bubble("Are you a new user or an existing user?", sender='bot')
    
    col1, col2 = st.columns(2)
    if col1.button("🆕 New User"):
        st.session_state.step = 'awaiting_id'
        st.session_state.user_type = 'new'
    elif col2.button("🔄 Existing User"):
        st.session_state.step = 'awaiting_id'
        st.session_state.user_type = 'existing'

if st.session_state.step == 'awaiting_id':
    user_input = st.text_input("Please enter your SSN or Tribal ID:")
    if user_input:
        bot_reply(user_input)

if st.session_state.step == 'awaiting_photo':
    photo = st.file_uploader("Please upload a photo for verification:", type=['jpg', 'jpeg', 'png'])
    if photo:
        st.session_state.photos.append(photo)
        chat_bubble(f"✅ Photo uploaded successfully. {len(st.session_state.photos)} photo(s) added.", sender='bot')

if st.session_state.step == 'awaiting_confirmation':
    user_input = st.text_input("Do you confirm the details? (yes/no)")
    if user_input:
        bot_reply(user_input)
