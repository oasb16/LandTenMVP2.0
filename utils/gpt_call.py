import openai
import os
from PIL import Image
import io
import base64
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]

def call_gpt_agent(chat_log):
    messages = [{"role": "system","content": (
            "You are a helpful assistant for property issues. Respond in 30 words max. "
            "Do not offer random solutions. Only help the user troubleshoot within their control. "
            "If more info is needed, ask clearly. "
            "If media is useful, ask for upload. "
            "Check for 5 key issue signals. "
            "Once enough info is gathered, confirm if user wants to file an incident. "
            "You are responsible for preparing a clean report that the landlord can act on easily, including job creation if needed. ")}]

    for msg in chat_log:
        if msg["role"] in ["tenant", "landlord", "contractor"]:
            messages.append({"role": "user", "content": msg["message"]})
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.4
    )
    return response.choices[0].message.content

def call_whisper(audio_bytes):
    response = openai.audio.transcriptions.create(
        model="whisper-1",
        file=io.BytesIO(audio_bytes),
        response_format="text"
    )
    return response

def call_gpt_vision(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    vision_prompt = [{
        "role": "user",
        "content": [
            {"type": "text", "text": "What do you see? Summarize any visible property issue."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    }]
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=vision_prompt,
        max_tokens=300
    )
    return response.choices[0].message.content
