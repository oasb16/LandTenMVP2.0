import json
from utils.gpt_call import call_gpt_model

def analyze_feedback(path="logs/feedback.json") -> str:
    try:
        with open(path, "r") as f:
            entries = json.load(f)

        system_prompt = """
You are a property maintenance system assistant.

Given a list of job feedback entries (with rating, comment), generate:

1. Key complaints
2. Common praise
3. Any recommendations for improving job flow

Return a markdown-formatted summary only.
        """

        context = json.dumps(entries)
        return call_gpt_model(system_prompt + "\n\n" + context)

    except Exception as e:
        return f"⚠️ Feedback analysis failed: {e}"