
import openai

def call_gpt(messages):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message["content"]
