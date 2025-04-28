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
if 'reset_response' not in st.session_state:
    st.session_state.reset_response = None
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
    st.session_state.step = 'start'
    st.session_state.progress = 0
    st.session_state.user_id = None
    st.session_state.photos = []
    st.session_state.reminder_sent = False
    st.session_state.awaiting_reset_confirm = False
    st.session_state.reset_response = None
    st.session_state.chat_history = []

# Sidebar reset
with st.sidebar:
    st.header("FAQ")
    st.write("""
    **Q: How do I use this onboarding bot?**
    - Follow the steps provided by the bot to upload your ID and photo.
    
    **Q: Can I reset my progress?**
    - Yes, you can reset the process at any time by clicking on the "Reset Chat" button.

    **Q: What happens after I submit my ID and photo?**
    - After uploading your ID and photo, you'll be asked to confirm your submission.

    **Q: Is my data safe?**
    - Yes, your data is kept confidential and only used for the onboarding process.
    """)

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

# Handle reset confirmation
if st.session_state.awaiting_reset_confirm:
    user_input = st.text_input("You:", key='user_input')
    if user_input:
        chat_bubble(user_input, sender='user')

        if user_input.lower() == 'yes':
            reset_chat()
        elif user_input.lower() == 'no':
            chat_bubble("✅ Reset cancelled. Let's continue!", sender='bot')
            st.session_state.awaiting_reset_confirm = False
            st.session_state.reset_response = 'no'
        else:
            chat_bubble("❓ Please type 'yes' to confirm or 'no' to continue.", sender='bot')

else:
    # User text input
    user_input = st.text_input("Your response:", key="response")
    if user_input:
        chat_bubble(user_input, sender='user')
        # Handle bot response based on current step
        if st.session_state.step == 'start':
            chat_bubble("Hi there! 👋 I’m here to help you apply for ACP or Lifeline.", sender='bot')
            chat_bubble("Are you a new user or an existing user?", sender='bot')
            st.session_state.step = 'awaiting_id'

        elif st.session_state.step == 'awaiting_id':
            chat_bubble("Please enter your ID number", sender='bot')
            st.session_state.step = 'awaiting_photo'

        elif st.session_state.step == 'awaiting_photo':
            chat_bubble("Please upload your photo", sender='bot')
            st.session_state.step = 'awaiting_confirmation'

        elif st.session_state.step == 'awaiting_confirmation':
            chat_bubble("Please confirm your details for submission", sender='bot')
            st.session_state.step = 'done'

        elif st.session_state.step == 'done':
            chat_bubble("Application complete! Thank you for using the ACP/Lifeline Assistant!", sender='bot')
