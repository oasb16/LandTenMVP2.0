import openai, os
import streamlit as st

openai.key = st.secrets.get("OPENAI_API_KEY")

def get_gpt_reply(messages):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You're a landlord assistant summarizing tenant issues into short bullet points."}] + messages,
            max_tokens=40
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ GPT Error: {e}"