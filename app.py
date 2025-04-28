import streamlit as st
import time
import re
import imagehash
import base64
from io import BytesIO
from PIL import Image

# --- Page Config ---
st.set_page_config(page_title="ACP/Lifeline Assistant", layout="wide")

# --- Fixed Header CSS ---
st.markdown(
    """
    <style>
      /* Pin the main title at top */
      h1 {
        position: fixed;
        top: 0;
        width: 100%;
        background-color: white;
        z-index: 1000;
        margin: 0;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #ddd;
      }
      /* Push content below the fixed header */
      .block-container {
        padding-top: 3.5rem;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Main Title (fixed) ---
st.title("ACP/Lifeline Assistant")

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
    st.title("Need help? Chat below!")
    if st.button("🔄 Reset Chat"):
        st.session_state.awaiting_reset_confirm = True
    if st.session_state.awaiting_reset_confirm:
        st.warning("⚠️ Are you sure you want to reset and lose your progress?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes, Reset"):
                reset_session()
        with c2:
            if st.button("❌ No, Cancel"):
                st.session_state.awaiting_reset_confirm = False

    st.header("FAQ")
    faq = {
        "How do I apply for ACP or Lifeline?":
            "You can apply by providing your ID, uploading a photo, and confirming your details.",
        "What documents are needed for verification?":
            "We need either your SSN or Tribal ID, along with a recent photo.",
        "What happens after I submit my application?":
            "Your details are sent to NLAD for verification. Most applications are processed in 1–2 business days."
    }
    for q, a in faq.items():
        if st.button(q):
            st.info(a)

# --- Chat Bubble ---
def chat_bubble(message, sender='bot', save_to_history=True):
    avatar = "🤖" if sender == 'bot' else "🧑"
    cls = 'bot-bubble' if sender == 'bot' else 'user-bubble'
    if sender == 'bot':
        time.sleep(0.5)
    st.markdown(
        f"""
        <div class="chat-bubble {cls} clearfix">
            <strong>{avatar} {sender.capitalize()}:</strong><br>{message}
        </div>
        """,
        unsafe_allow_html=True
    )
    if save_to_history:
        st.session_state.chat_history.append({'text': message, 'sender': sender})

# --- Replay History ---
for msg in st.session_state.chat_history:
    chat_bubble(msg['text'], sender=msg['sender'], save_to_history=False)

# --- Helpers ---
def validate_id(val):
    if st.session_state.id_type == 'ssn':
        return bool(re.match(r"^\d{3}-\d{2}-\d{4}$", val))
    else:
        return val.isdigit() and len(val) >= 5

def get_image_hash(f):
    img = Image.open(BytesIO(f.getvalue()))
    return str(imagehash.average_hash(img))

def check_duplicate(uid, hashes):
    existing = [
        {"id": "123-45-6789", "photo_hash": "abcd1234"},
        {"id": "555-66-7777", "photo_hash": "efgh5678"}
    ]
    return any(r['id']==uid or r['photo_hash'] in hashes for r in existing)

def save_user_data():
    pass  # implement as needed

def update_progress_bar():
    mapping = {
        'start': 0, 'awaiting_id': 20, 'awaiting_photo': 50,
        'awaiting_confirmation': 80, 'awaiting_provider_switch': 80,
        'done': 100
    }
    target = mapping.get(st.session_state.step, st.session_state.progress)
    current = st.session_state.progress
    st.session_state.progress = target
    bar = st.empty()
    while current < target:
        current += 2
        if current>target: current=target
        bar.progress(current)
        time.sleep(0.02)

# --- Bot Logic ---
def bot_reply(inp):
    step = st.session_state.step

    if step == 'awaiting_id':
        if validate_id(inp):
            st.session_state.user_id = inp
            st.session_state.step = 'awaiting_photo'
            chat_bubble("✅ ID confirmed. Now upload your photo(s).", 'bot')
            update_progress_bar()
            st.rerun()
        else:
            chat_bubble("⚠️ Invalid ID format.", 'bot')

    elif step == 'awaiting_confirmation':
        if inp.lower()=='yes':
            save_user_data()
            st.session_state.confirmed = True
            st.session_state.step = 'done'
            chat_bubble("✅ Details submitted to NLAD.", 'bot')
            update_progress_bar()
            chat_bubble("🎉 Thank you for using our service!", 'bot')
        else:
            chat_bubble("👍 Okay, let me know when you’re ready.", 'bot')

    elif step == 'awaiting_provider_switch':
        if inp.lower()=='yes':
            st.session_state.step = 'done'
            chat_bubble("✅ We'll assist with provider switch.", 'bot')
        else:
            st.session_state.step = 'done'
            chat_bubble("👍 Keeping your current provider active.", 'bot')
        chat_bubble("🎉 Thank you for using our service!", 'bot')

    elif step == 'done':
        # final message only once
        chat_bubble("🙏 Thank you for using the assistant. Have a great day!", 'bot')

# --- Main Chat Flow ---
if st.session_state.step == 'start':
    if 'welcome' not in st.session_state:
        st.session_state.welcome = True
        chat_bubble("👋 Hi there! I’m here to help you apply for ACP or Lifeline.", 'bot')
        chat_bubble("Are you a new user or an existing user?", 'bot')
    c1, c2 = st.columns(2)
    if c1.button("🆕 New"):
        st.session_state.step = 'ask_id_type'
        chat_bubble("New user selected.", 'user')
        chat_bubble("What type of ID will you use?", 'bot')
    if c2.button("👤 Existing"):
        st.session_state.step = 'ask_id_type'
        chat_bubble("Existing user selected.", 'user')
        chat_bubble("What type of ID will you use?", 'bot')

if st.session_state.step == 'ask_id_type':
    c1, c2 = st.columns(2)
    if c1.button("SSN"):
        st.session_state.id_type='ssn'; st.session_state.step='awaiting_id'
        chat_bubble("SSN selected.", 'user')
        chat_bubble("Please enter your SSN (123-45-6789).", 'bot')
    if c2.button("Tribal ID"):
        st.session_state.id_type='tribal'; st.session_state.step='awaiting_id'
        chat_bubble("Tribal ID selected.", 'user')
        chat_bubble("Please enter your Tribal ID (at least 5 digits).", 'bot')

if st.session_state.step == 'awaiting_id':
    with st.form("id_form", clear_on_submit=True):
        val = st.text_input("Enter your ID:")
        if st.form_submit_button("➤") and val:
            chat_bubble(val, 'user')
            bot_reply(val)

if st.session_state.step == 'awaiting_photo':
    files = st.file_uploader(
        "Upload your photo(s) (jpg/png, max 5MB each)",
        type=["jpg","jpeg","png"], accept_multiple_files=True
    )
    if files:
        valid=[]
        for f in files:
            if f.size>5*1024*1024:
                chat_bubble(f"⚠️ {f.name} is too large (>5MB).", 'bot')
            else:
                valid.append(f)
        if valid:
            for f in valid:
                h = get_image_hash(f)
                st.session_state.photos.append({"file":f,"hash":h})
                b = base64.b64encode(f.getvalue()).decode()
                html = (
                    f"📸 {f.name}<br>"
                    f"<img src='data:image/png;base64,{b}' "
                    "style='max-width:200px;border-radius:8px;'/>"
                )
                chat_bubble(html, 'bot')
            hashes=[p['hash'] for p in st.session_state.photos]
            if check_duplicate(st.session_state.user_id, hashes):
                st.session_state.step='awaiting_provider_switch'
                chat_bubble("⚠️ Duplicate detected. Switch provider?", 'bot')
            else:
                st.session_state.step='awaiting_confirmation'
                chat_bubble("✅ No duplicate found. Submit to NLAD?", 'bot')
            update_progress_bar()
            st.rerun()

if st.session_state.step in ['awaiting_confirmation','awaiting_provider_switch']:
    c1, c2 = st.columns(2)
    if c1.button("✅ Yes"):
        chat_bubble("Yes", 'user'); bot_reply("yes"); update_progress_bar(); st.rerun()
    if c2.button("❌ No"):
        chat_bubble("No", 'user'); bot_reply("no"); update_progress_bar(); st.rerun()
