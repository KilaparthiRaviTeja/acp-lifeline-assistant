import streamlit as st
from io import BytesIO
import re
import time
import imagehash
from PIL import Image

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
        'reset_confirm': False,
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

# --- Sidebar Content ---
with st.sidebar:
    st.title("Welcome to our ACP/Lifeline assistant.\nNeed help? Chat below!")
    if st.button("🔄 Reset Chat"):
        st.session_state.reset_confirm = True

    if st.session_state.reset_confirm:
        st.warning("⚠️ Are you sure you want to reset and lose progress?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Reset"):
                st.session_state.clear()
                st.rerun()
        with col2:
            if st.button("❌ No, Cancel"):
                st.session_state.reset_confirm = False

    st.header("FAQ")
    for question, answer in faq.items():
        if st.button(question):
            st.info(answer)

# --- Chat Bubble Function ---
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

# --- Helper Functions ---
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
            "photo_hash": photo['hash']
        })

def bot_reply(user_input):
    step = st.session_state.step

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
        if user_input.strip().lower() == 'yes':
            save_user_data()
            st.session_state.confirmed = True
            st.session_state.step = 'done'
            chat_bubble("✅ Details sent to NLAD.", sender='bot')
            chat_bubble("📅 Most applications are processed in 1–2 business days.", sender='bot')
        elif user_input.strip().lower() == 'no':
            chat_bubble("Okay! Let me know when you're ready.", sender='bot')
        else:
            chat_bubble("⚠️ Please respond with 'yes' or 'no'.", sender='bot')

    elif step == 'awaiting_provider_switch':
        if user_input.strip().lower() == 'yes':
            st.session_state.step = 'done'
            chat_bubble("Thanks! We'll help you switch your provider soon.", sender='bot')
        elif user_input.strip().lower() == 'no':
            st.session_state.step = 'done'
            chat_bubble("Okay, your current provider will remain active.", sender='bot')
        else:
            chat_bubble("⚠️ Please respond with 'yes' or 'no'.", sender='bot')

    elif step == 'done':
        chat_bubble("🙏 Thank you for using the assistant. Have a great day!", sender='bot')

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

# --- Main Chat Logic ---
st.title("ACP/Lifeline Assistant")

if st.session_state.step == 'start':
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = True
        chat_bubble("Hi there! 👋 I’m here to help you apply for ACP or Lifeline.", sender='bot')
        chat_bubble("Are you a new user or an existing user?", sender='bot')

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
        chat_bubble("Please enter your SSN (123-45-6789).", sender='bot')

    if col2.button("Tribal ID"):
        st.session_state.id_type = 'tribal'
        st.session_state.step = 'awaiting_id'
        chat_bubble("Tribal ID selected.", sender='user')
        chat_bubble("Please enter your Tribal ID (at least 5 digits).", sender='bot')

if st.session_state.step == 'awaiting_id':
    with st.form("id_form", clear_on_submit=True):
        user_input = st.text_input("Enter your ID:")
        submitted = st.form_submit_button("➤")
        if submitted and user_input:
            chat_bubble(user_input, sender='user')
            bot_reply(user_input)
            update_progress_bar()

if st.session_state.step == 'awaiting_photo':
    uploaded_files = st.file_uploader("Upload your photo(s) (jpg/png, max 5MB each)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files:
        valid_files = []
        for uploaded_file in uploaded_files:
            if uploaded_file.size > 5 * 1024 * 1024:
                chat_bubble(f"⚠️ {uploaded_file.name} is too large (>5MB). Please upload a smaller file.", sender='bot')
            else:
                valid_files.append(uploaded_file)

        if valid_files:
            for file in valid_files:
                file_hash = get_image_hash(file)
                st.session_state.photos.append({"file": file, "hash": file_hash})
                chat_bubble(f"📸 Uploaded: {file.name}", sender='bot')
                st.image(BytesIO(file.getvalue()), caption=file.name, use_column_width=True)

            photo_hashes = [get_image_hash(file) for file in valid_files]
            if check_duplicate(st.session_state.user_id, photo_hashes):
                st.session_state.duplicate = True
                st.session_state.step = 'awaiting_provider_switch'
                chat_bubble("⚠️ Duplicate detected! It looks like you're already registered.", sender='bot')
                chat_bubble("Would you like to switch providers instead? (yes/no)", sender='bot')
            else:
                st.session_state.step = 'awaiting_confirmation'
                chat_bubble("✅ No duplicate found. Do you want to submit your details to NLAD? (yes/no)", sender='bot')

if st.session_state.step in ['awaiting_confirmation', 'awaiting_provider_switch']:
    with st.form("confirm_form", clear_on_submit=True):
        user_input = st.text_input("Your response:")
        submitted = st.form_submit_button("➤")
        if submitted and user_input:
            chat_bubble(user_input, sender='user')
            bot_reply(user_input)
            update_progress_bar()
