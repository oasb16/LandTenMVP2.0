import openai
import os

def call_gpt_agent(chat_log):

    openai.api_key = os.getenv("OPENAI_API_KEY")

    messages = [
        {"role": "system", "content": "You are a helpful property assistant for tenant issues."}
    ] + [{"role": "user", "content": msg["message"]} for msg in chat_log if msg["role"] == "tenant"]

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.5
    )

    return response.choices[0].message.content
