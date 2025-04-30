import streamlit as st
import base64
import hashlib
from PIL import Image
from io import BytesIO

# ---- Page config ----
st.set_page_config(page_title="ACP/Lifeline Assistant", layout="centered")
st.markdown("<style>body { font-family: 'Arial', sans-serif; }</style>", unsafe_allow_html=True)

# ---- Utility functions ----
def get_image_hash(image_file):
    image = Image.open(image_file)
    image = image.convert('RGB')
    resized = image.resize((128, 128))
    buf = BytesIO()
    resized.save(buf, format="JPEG")
    img_bytes = buf.getvalue()
    return hashlib.md5(img_bytes).hexdigest()

def check_duplicate(user_id, photo_hashes):
    known_hashes = {"abc123", "def456"}  # Simulated existing hashes
    return any(h in known_hashes for h in photo_hashes)

def chat_bubble(message, sender='bot'):
    align = "flex-start" if sender == 'bot' else "flex-end"
    bg = "#e6f2ff" if sender == 'bot' else "#dcf8c6"
    avatar = "🤖" if sender == 'bot' else "🧑"
    st.markdown(f"""
    <div style="display: flex; justify-content: {align}; margin: 5px 0;">
        <div style="background-color: {bg}; padding: 10px 15px; border-radius: 15px; max-width: 80%;">
            <span style="font-size: 24px;">{avatar}</span> {message}
        </div>
    </div>
    """, unsafe_allow_html=True)

def update_progress_bar():
    steps = {
        "start": 0,
        "user_type": 10,
        "id_type": 20,
        "id_input": 30,
        "awaiting_photo": 50,
        "awaiting_confirmation": 60,
        "awaiting_provider_switch": 60,
        "enter_provider_name": 70,
        "ask_more_help": 80,
        "awaiting_query": 90,
        "done": 100
    }
    progress = steps.get(st.session_state.step, 0)
    st.progress(progress, text=f"Progress: {progress}%")

# ---- Session state initialization ----
if "step" not in st.session_state:
    st.session_state.step = "start"
    st.session_state.user_type = None
    st.session_state.id_type = None
    st.session_state.user_id = ""
    st.session_state.photos = []
    st.session_state.duplicate = False
    st.session_state.provider_name = ""

# ---- Main chatbot logic ----
st.title("📱 ACP/Lifeline Application Assistant")
update_progress_bar()

if st.session_state.step == "start":
    chat_bubble("Welcome! Are you a new or existing user?", sender='bot')
    col1, col2 = st.columns(2)
    if col1.button("🆕 New"):
        st.session_state.user_type = "new"
        chat_bubble("New", sender='user')
        st.session_state.step = "id_type"
        st.rerun()
    if col2.button("👤 Existing"):
        st.session_state.user_type = "existing"
        chat_bubble("Existing", sender='user')
        st.session_state.step = "id_type"
        st.rerun()

elif st.session_state.step == "id_type":
    chat_bubble("What ID will you use?", sender='bot')
    col1, col2 = st.columns(2)
    if col1.button("🪪 Tribal ID"):
        st.session_state.id_type = "tribal"
        chat_bubble("Tribal ID", sender='user')
        st.session_state.step = "id_input"
        st.rerun()
    if col2.button("🔢 SSN"):
        st.session_state.id_type = "ssn"
        chat_bubble("SSN", sender='user')
        st.session_state.step = "id_input"
        st.rerun()

elif st.session_state.step == "id_input":
    prompt = "Enter your Tribal ID:" if st.session_state.id_type == "tribal" else "Enter the last 4 digits of your SSN:"
    user_id = st.text_input(prompt)
    if user_id:
        st.session_state.user_id = user_id.strip()
        chat_bubble(user_id.strip(), sender='user')
        st.session_state.step = "awaiting_photo"
        chat_bubble("Please upload your photo(s) for verification.", sender='bot')
        st.rerun()

elif st.session_state.step == "awaiting_photo":
    uploaded_files = st.file_uploader(
        "Upload your photo(s) (jpg/png/jfif, max 5MB each)",
        type=["jpg", "jpeg", "png", "jfif"],
        accept_multiple_files=True
    )
    if uploaded_files:
        valid_files = []
        for uploaded_file in uploaded_files:
            if uploaded_file.size > 5 * 1024 * 1024:
                chat_bubble(f"⚠️ {uploaded_file.name} is too large (>5MB).", sender='bot')
            else:
                valid_files.append(uploaded_file)

        if valid_files:
            for file in valid_files:
                file_hash = get_image_hash(file)
                st.session_state.photos.append({"file": file, "hash": file_hash})
                file_bytes = file.getvalue()
                b64 = base64.b64encode(file_bytes).decode()
                img_html = f"📸 {file.name}<br><img src='data:image/png;base64,{b64}' style='max-width:200px;border-radius:8px;'/>"
                chat_bubble(img_html, sender='bot')

            photo_hashes = [p['hash'] for p in st.session_state.photos]
            if check_duplicate(st.session_state.user_id, photo_hashes):
                st.session_state.duplicate = True
                st.session_state.step = 'awaiting_provider_switch'
                chat_bubble("⚠️ Duplicate found. You are already in the program. Do you want to change your provider?", sender='bot')
            else:
                st.session_state.duplicate = False
                st.session_state.step = 'awaiting_confirmation'
                chat_bubble("✅ No duplicate found. Do you want to submit to NLAD?", sender='bot')

            update_progress_bar()
            st.rerun()

elif st.session_state.step == "awaiting_confirmation":
    col1, col2 = st.columns(2)
    if col1.button("✅ Yes"):
        chat_bubble("Yes", sender='user')
        chat_bubble("📤 Details submitted to NLAD.", sender='bot')
        st.session_state.step = 'ask_more_help'
        chat_bubble("Do you need any other help?", sender='bot')
    if col2.button("❌ No"):
        chat_bubble("No", sender='user')
        st.session_state.step = 'ask_more_help'
        chat_bubble("Okay. Do you need any other help?", sender='bot')

elif st.session_state.step == 'awaiting_provider_switch':
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, change provider"):
            chat_bubble("Yes, change provider.", sender='user')
            st.session_state.step = 'enter_provider_name'
            chat_bubble("Please enter your new provider's name.", sender='bot')
            st.rerun()
    with col2:
        if st.button("❌ No, continue with current provider"):
            chat_bubble("No, continue with current provider.", sender='user')
            st.session_state.step = 'ask_more_help'
            chat_bubble("Thank you. Do you need any other help?", sender='bot')
            st.rerun()

elif st.session_state.step == 'enter_provider_name':
    provider_name = st.text_input("Enter new provider's name:")
    if provider_name:
        chat_bubble(provider_name, sender='user')
        chat_bubble("Thank you. We will guide you through the process.", sender='bot')
        st.session_state.step = 'ask_more_help'
        chat_bubble("Do you need any other help?", sender='bot')

elif st.session_state.step == 'ask_more_help':
    col1, col2 = st.columns(2)
    if col1.button("📝 Yes"):
        st.session_state.step = 'awaiting_query'
        chat_bubble("What do you need help with?", sender='bot')
    if col2.button("🙅 No"):
        chat_bubble("Thank you for using the assistant. Have a great day!", sender='bot')
        st.session_state.step = 'done'

elif st.session_state.step == 'awaiting_query':
    query = st.text_input("Enter your question:")
    if query:
        chat_bubble(query, sender='user')
        chat_bubble("Thank you for your question. Our support team will follow up shortly.", sender='bot')
        st.session_state.step = 'done'

elif st.session_state.step == 'done':
    st.markdown("✅ Chat session complete.")
