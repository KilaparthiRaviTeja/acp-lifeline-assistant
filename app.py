import streamlit as st
import hashlib
import time

# Hash uploaded photo
def get_image_hash(image):
    return hashlib.sha256(image.getvalue()).hexdigest()

# Bot typing with blinking dots
def bot_typing_animation():
    typing_message = st.empty()
    for _ in range(3):  # Repeat blinking dots a few times
        for dots in ["", ".", "..", "..."]:
            typing_message.markdown(
                f"<div class='chat-bubble bot-bubble clearfix'><strong>🤖 Bot:</strong> Typing{dots}</div>",
                unsafe_allow_html=True
            )
            time.sleep(0.3)
    typing_message.empty()

# Chat bubble display
def chat_bubble(message, sender='bot', save_to_history=True):
    avatar = "🤖" if sender == 'bot' else "🧑"
    bubble_class = 'bot-bubble' if sender == 'bot' else 'user-bubble'

    if sender == 'bot':
        bot_typing_animation()

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

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 'start'
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'photos' not in st.session_state:
    st.session_state.photos = []
if 'reminder_sent' not in st.session_state:
    st.session_state.reminder_sent = False
if 'awaiting_reset_confirm' not in st.session_state:
    st.session_state.awaiting_reset_confirm = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Simulated existing records
existing_records = []

# Smooth progress bar animation
def update_progress_bar():
    step_target = {
        'start': 0,
        'awaiting_id': 20,
        'awaiting_photo': 50,
        'awaiting_confirmation': 80,
        'done': 100
    }
    target_progress = step_target.get(st.session_state.step, st.session_state.progress)

    progress_bar = st.empty()
    current_progress = st.session_state.progress

    while current_progress < target_progress:
        current_progress += 2
        if current_progress > target_progress:
            current_progress = target_progress
        progress_bar.progress(current_progress)
        time.sleep(0.02)

    st.session_state.progress = current_progress

# Reminder system
def send_reminder():
    if st.session_state.step in ['awaiting_id', 'awaiting_photo'] and not st.session_state.reminder_sent:
        st.session_state.reminder_sent = True
        chat_bubble("⚠️ You haven't completed the process. Would you like to continue? (yes/no)", sender='bot')

# Save user data
def save_user_data():
    for photo in st.session_state.photos:
        existing_records.append({
            "id": st.session_state.user_id,
            "photo_hash": get_image_hash(photo)
        })

# Reset everything
def reset_chat():
    for key in ['step', 'progress', 'user_id', 'photos', 'reminder_sent', 'awaiting_reset_confirm', 'chat_history']:
        if key in st.session_state:
            del st.session_state[key]
    st.experimental_rerun()

# Sidebar reset
with st.sidebar:
    if st.button("🔄 Reset Chat"):
        chat_bubble("⚠️ Are you sure you want to reset and lose progress? (yes/no)", sender='bot')
        st.session_state.awaiting_reset_confirm = True

# App title
st.title("🧩 Smart ACP/Lifeline Onboarding Bot")

# Progress bar
update_progress_bar()

# Replay chat history
for chat in st.session_state.chat_history:
    chat_bubble(chat['text'], chat['sender'], save_to_history=False)

# User text input
user_input = st.text_input("You:", key='user_input')

if user_input:
    chat_bubble(user_input, sender='user')

    if st.session_state.awaiting_reset_confirm:
        if user_input.lower() == 'yes':
            reset_chat()
        elif user_input.lower() == 'no':
            chat_bubble("✅ Reset cancelled. Let's continue!", sender='bot')
            st.session_state.awaiting_reset_confirm = False

    elif st.session_state.step == 'start':
        chat_bubble("👋 Welcome! Please enter your ID number.", sender='bot')
        st.session_state.step = 'awaiting_id'
        update_progress_bar()

    elif st.session_state.step == 'awaiting_id':
        st.session_state.user_id = user_input.strip()
        chat_bubble(f"📸 Great! Now upload a photo for ID verification.", sender='bot')
        st.session_state.step = 'awaiting_photo'
        update_progress_bar()

    elif st.session_state.step == 'awaiting_photo':
        chat_bubble("📸 Please upload your photo using the uploader below.", sender='bot')

    elif st.session_state.step == 'awaiting_confirmation':
        if user_input.lower() == 'yes':
            save_user_data()
            chat_bubble("🎉 Your application has been submitted!", sender='bot')
            st.session_state.step = 'done'
            update_progress_bar()
        elif user_input.lower() == 'no':
            chat_bubble("🔄 Let's start over. Please enter your ID number.", sender='bot')
            st.session_state.step = 'awaiting_id'
            update_progress_bar()
        else:
            chat_bubble("❓ Please type 'yes' to confirm or 'no' to restart.", sender='bot')

# Upload section (photo uploader)
if st.session_state.step == 'awaiting_photo':
    uploaded_file = st.file_uploader("Upload your photo here", type=['jpg', 'jpeg', 'png'])

    if uploaded_file:
        uploaded_hash = get_image_hash(uploaded_file)

        duplicate = False
        for record in existing_records:
            if record['id'] == st.session_state.user_id or record['photo_hash'] == uploaded_hash:
                duplicate = True
                break

        if duplicate:
            chat_bubble("🚫 Duplicate detected! You've already submitted before.", sender='bot')
        else:
            st.session_state.photos.append(uploaded_file)

            # Display mini thumbnail preview
            st.image(uploaded_file, width=150, caption="Uploaded Photo Preview")

            chat_bubble("✅ Photo uploaded successfully! Confirm submission? (yes/no)", sender='bot')
            st.session_state.step = 'awaiting_confirmation'
            update_progress_bar()

# Reminder if user stuck
send_reminder()

# CSS for chat bubbles & animations
st.markdown("""
    <style>
    .chat-bubble {
        max-width: 70%;
        padding: 10px 15px;
        margin: 8px;
        border-radius: 20px;
        font-size: 16px;
        line-height: 1.5;
        animation: fadeIn 0.5s ease;
    }
    .user-bubble {
        background-color: #DCF8C6;
        margin-left: auto;
        text-align: right;
    }
    .bot-bubble {
        background-color: #F1F0F0;
        margin-right: auto;
        text-align: left;
    }
    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    </style>
""", unsafe_allow_html=True)
