import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def call_gpt_agent(chat_log):
    messages = [{"role": "system", "content": "You are a helpful assistant helping tenants report house issues."}]
    
    for msg in chat_log:
        if msg["role"] in ["tenant", "user"]:
            messages.append({"role": "user", "content": msg["message"]})
        elif msg["role"] in ["agent", "assistant"]:
            messages.append({"role": "assistant", "content": msg["message"]})
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[GPT error: {e}]"
