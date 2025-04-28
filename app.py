import streamlit as st
import time
import re
import imagehash
import base64
from io import BytesIO
from PIL import Image

# --- Page Config ---
st.set_page_config(page_title="ACP/Lifeline Assistant", layout="wide")

# --- Styling ---
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
        'confirmed': False,
        'duplicate': False,
        'chat_history': [],
        'progress': 0,
        'awaiting_reset_confirm': False
    })

# --- Reset Function ---
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
        'confirmed': False,
        'duplicate': False,
        'chat_history': [],
        'progress': 0,
        'awaiting_reset_confirm': False
    })
    st.rerun()

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
                reset_session()
        with col2:
            if st.button("❌ No, Cancel"):
                st.session_state.awaiting_reset_confirm = False

    st.header("FAQ")
    faq = {
        "How do I apply for ACP or Lifeline?": "You can apply by providing your ID, uploading a photo, and confirming your details.",
        "What documents are needed for verification?": "We need either your SSN or Tribal ID, along with a recent photo.",
        "What happens after I submit my application?": "Your details are sent to NLAD for verification. Most applications are processed in 1–2 business days."
    }
    for question, answer in faq.items():
        if st.button(question):
            st.info(answer)

# --- Chat Bubble Function ---
def chat_bubble(message, sender='bot', save_to_history=True):
    avatar = "🤖" if sender == 'bot' else "🧑"
    bubble_class = 'bot-bubble' if sender == 'bot' else 'user-bubble'
    if sender == 'bot':
        time.sleep(0.5)
    st.markdown(
        f"""
        <div class="chat-bubble {bubble_class} clearfix">
            <strong>{avatar} {sender.capitalize()}:</strong><br>{message}
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

def check_duplicate(user_id, photo_hashes):
    existing_records = [
        {"id": "123-45-6789", "photo_hash": "abcd1234"},
        {"id": "555-66-7777", "photo_hash": "efgh5678"},
    ]
    for record in existing_records:
        if record['id'] == user_id or record['photo_hash'] in photo_hashes:
            return True
    return False

def save_user_data():
    # stub for saving into your DB
    pass

def update_progress_bar():
    target = {
        'start': 0,
        'awaiting_id': 20,
        'awaiting_photo': 50,
        'awaiting_confirmation': 80,
        'awaiting_provider_switch': 80,
        'done': 100
    }.get(st.session_state.step, st.session_state.progress)
    current = st.session_state.progress
    st.session_state.progress = target
    bar = st.empty()
    while current < target:
        current += 2
        if current > target: current = target
        bar.progress(current)
        time.sleep(0.02)

# --- Bot Logic ---
def bot_reply(user_input):
    step = st.session_state.step

    if step == 'awaiting_id':
        if validate_id(user_input):
            st.session_state.user_id = user_input
            st.session_state.step = 'awaiting_photo'
            chat_bubble("✅ ID confirmed. Now upload your photo(s).", sender='bot')
            update_progress_bar()
            st.rerun()
        else:
            chat_bubble("⚠️ Invalid ID format.", sender='bot')

    elif step == 'awaiting_confirmation':
        if user_input.lower() == 'yes':
            save_user_data()
            st.session_state.confirmed = True
            st.session_state.step = 'done'
            chat_bubble("✅ Details submitted to NLAD.", sender='bot')
            update_progress_bar()
        else:
            chat_bubble("👍 Okay, let me know when you’re ready.", sender='bot')

    elif step == 'awaiting_provider_switch':
        if user_input.lower() == 'yes':
            st.session_state.step = 'done'
            chat_bubble("✅ We'll assist with provider switch.", sender='bot')
        else:
            st.session_state.step = 'done'
            chat_bubble("👍 Keeping your current provider active.", sender='bot')

    elif step == 'done':
        # final message only once
        chat_bubble("🙏 Thank you for using the assistant. Have a great day!", sender='bot')

# --- Main Chat Area ---
st.title("ACP/Lifeline Assistant")

# Step: start → ask new/existing
if st.session_state.step == 'start':
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = True
        chat_bubble("👋 Hi there! I’m here to help you apply for ACP or Lifeline.", sender='bot')
        chat_bubble("Are you a new user or an existing user?", sender='bot')

    c1, c2 = st.columns(2)
    if c1.button("🆕 New"):
        st.session_state.user_type = 'new'
        st.session_state.step = 'ask_id_type'
        chat_bubble("New user selected.", sender='user')
        chat_bubble("What type of ID will you use?", sender='bot')
    if c2.button("👤 Existing"):
        st.session_state.user_type = 'existing'
        st.session_state.step = 'ask_id_type'
        chat_bubble("Existing user selected.", sender='user')
        chat_bubble("What type of ID will you use?", sender='bot')

# Step: ask ID type
if st.session_state.step == 'ask_id_type':
    c1, c2 = st.columns(2)
    if c1.button("SSN"):
        st.session_state.id_type = 'ssn'
        st.session_state.step = 'awaiting_id'
        chat_bubble("SSN selected.", sender='user')
        chat_bubble("Please enter your SSN (123-45-6789).", sender='bot')
    if c2.button("Tribal ID"):
        st.session_state.id_type = 'tribal'
        st.session_state.step = 'awaiting_id'
        chat_bubble("Tribal ID selected.", sender='user')
        chat_bubble("Please enter your Tribal ID (at least 5 digits).", sender='bot')

# Step: enter ID
if st.session_state.step == 'awaiting_id':
    with st.form("id_form", clear_on_submit=True):
        uid = st.text_input("Enter your ID:")
        if st.form_submit_button("➤") and uid:
            chat_bubble(uid, sender='user')
            bot_reply(uid)

# Step: photo upload & preview
if st.session_state.step == 'awaiting_photo':
    files = st.file_uploader(
        "Upload your photo(s) (jpg/png, max 5MB each)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    if files:
        valid = []
        for f in files:
            if f.size > 5 * 1024 * 1024:
                chat_bubble(f"⚠️ {f.name} is too large (>5MB).", sender='bot')
            else:
                valid.append(f)

        if valid:
            for f in valid:
                # store
                h = get_image_hash(f)
                st.session_state.photos.append({"file": f, "hash": h})
                # preview via base64
                b = f.getvalue()
                b64 = base64.b64encode(b).decode()
                html = (
                    f"📸 {f.name}<br>"
                    f"<img src='data:image/png;base64,{b64}' "
                    f"style='max-width:200px;border-radius:8px;'/>"
                )
                chat_bubble(html, sender='bot')

            # then duplicate check
            hashes = [p['hash'] for p in st.session_state.photos]
            if check_duplicate(st.session_state.user_id, hashes):
                st.session_state.duplicate = True
                st.session_state.step = 'awaiting_provider_switch'
                chat_bubble("⚠️ Duplicate detected. Switch provider?", sender='bot')
            else:
                st.session_state.step = 'awaiting_confirmation'
                chat_bubble("✅ No duplicate found. Submit to NLAD?", sender='bot')

            update_progress_bar()
            st.rerun()

# Step: confirmation / provider‐switch via buttons
if st.session_state.step in ['awaiting_confirmation', 'awaiting_provider_switch']:
    col1, col2 = st.columns(2)
    if col1.button("✅ Yes"):
        chat_bubble("Yes", sender='user')
        bot_reply("yes")
        update_progress_bar()
        st.rerun()
    if col2.button("❌ No"):
        chat_bubble("No", sender='user')
        bot_reply("no")
        update_progress_bar()
        st.rerun()
