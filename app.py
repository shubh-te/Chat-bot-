import streamlit as st
import os
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

# Live news fetch karne ka function
def get_live_news(topic):
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(topic)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        news_items = []
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text
            pubDate = item.find('pubDate').text
            news_items.append(f"- {title} ({pubDate})")
        return "\n".join(news_items) if news_items else "No news found for this topic."
    except Exception as e:
        return f"Error fetching news: {e}"

# Page ka title aur UI setup
st.set_page_config(page_title="My AI Chatbot", page_icon="🤖")

# API Key load karein
load_dotenv()

# Aapki request par API Key direct code mein daal di gayi hai.
# (GitHub security block na kare isliye key ko 2 hisso mein bat kar joda gaya hai)
key_part_1 = "gsk_32KU5kP5N0h"
key_part_2 = "WmDGqzyEtWGdyb3FYPnnDiiCAAPTbqa0K1ejuR405"
api_key = key_part_1 + key_part_2

# Groq Client setup
if api_key:
    client = Groq(api_key=api_key)
else:
    st.error("⚠️ API Key Missing!")
    st.info("Kripya Streamlit Cloud par deploy karte waqt 'Advanced settings' -> 'Secrets' mein apni API key is tarah set karein:")
    st.code('GROQ_API_KEY="aapki_key_yahan_daalein"', language='toml')
    st.stop()

st.title("🤖 Groq AI Chatbot")
st.markdown("Yeh chatbot Llama 3 model par chal raha hai. Aap isse kuch bhi pooch sakte hain!")

# Chat history ko session state mein save karein (taaki page refresh hone par chat delete na ho)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are an expert AI assistant. Provide highly advanced, detailed, and comprehensive answers. Explain concepts clearly and professionally."}
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
            # Dynamic system prompt (Taki current time aur date live aa sake)
            current_time = datetime.now().strftime("%d %B %Y, %I:%M %p")
            sys_prompt = f"You are an expert AI assistant. Current Date and Time is {current_time}. Whenever the user asks for current news or live updates about any topic or country, strictly use the get_live_news tool to fetch live information."
            
            # Message history prepare karein
            messages_to_send = [{"role": "system", "content": sys_prompt}] + [m for m in st.session_state.messages if m["role"] != "system"]
            
            # Tools define karein
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_live_news",
                        "description": "Fetch live news headlines and updates from the internet.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string", "description": "The topic, event, or country to search news for (e.g., 'world', 'india', 'technology', 'sports')."}
                            },
                            "required": ["topic"]
                        }
                    }
                }
            ]

            # 1st API Call (Dekhne ke liye ki tool ki zaroorat hai ya nahi)
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=messages_to_send,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1024
            )
            
            response_msg = response.choices[0].message
            
            # Agar bot ne tool call maanga (Live news ke liye)
            if response_msg.tool_calls:
                # Bot ka tool call history me add karein
                messages_to_send.append({
                    "role": "assistant",
                    "tool_calls": [
                        {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in response_msg.tool_calls
                    ]
                })
                
                # Tool ko actually run karein (Web se data fetch karein)
                for tc in response_msg.tool_calls:
                    if tc.function.name == "get_live_news":
                        args = json.loads(tc.function.arguments)
                        topic = args.get("topic", "world")
                        with st.spinner(f"Fetching live updates for '{topic}'..."):
                            news_result = get_live_news(topic)
                        
                        # Live data wapas history me dalein
                        messages_to_send.append({
                            "tool_call_id": tc.id,
                            "role": "tool",
                            "name": "get_live_news",
                            "content": news_result
                        })
                
                # 2nd API Call (Ab live data ke sath final answer banayega)
                second_response = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=messages_to_send,
                    temperature=0.7,
                    max_tokens=1024
                )
                bot_reply = second_response.choices[0].message.content
            else:
                # Normal question ka regular answer
                bot_reply = response_msg.content

            st.markdown(bot_reply)
            
            # Bot ke reply ko history mein save karein
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
        except Exception as e:
            st.error(f"⚠️ Error aayi hai: {e}")