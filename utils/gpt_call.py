import openai
import os

def call_gpt(messages, temperature=0.5):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message["content"]