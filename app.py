import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq

# API Key load karein
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Groq Client setup
if api_key:
    client = Groq(api_key=api_key)
else:
    st.error("⚠️ Error: API Key nahi mili! Kripya .env file check karein.")
    st.stop()

# Page ka title aur UI setup
st.set_page_config(page_title="My AI Chatbot", page_icon="🤖")

st.title("🤖 Groq AI Chatbot")
st.markdown("Yeh chatbot Llama 3 model par chal raha hai. Aap isse kuch bhi pooch sakte hain!")

# Chat history ko session state mein save karein (taaki page refresh hone par chat delete na ho)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful, smart, and friendly AI assistant."}
    ]

# Purani chat history ko screen par dikhane ke liye loop
for msg in st.session_state.messages:
    if msg["role"] != "system": # System prompt ko UI par nahi dikhana hai
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# User input box (Niche chat box dikhane ke liye)
user_input = st.chat_input("Apna message yahan type karein...")

if user_input:
    # 1. User ke message ko screen par dikhayein
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 2. User ke message ko history mein save karein
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 3. Bot ka response laayein aur dikhayein
    with st.chat_message("assistant"):
        try:
            # API Call
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=st.session_state.messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            bot_reply = response.choices[0].message.content
            st.markdown(bot_reply)
            
            # Bot ke reply ko history mein save karein
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
        except Exception as e:
            st.error(f"⚠️ Error aayi hai: {e}")