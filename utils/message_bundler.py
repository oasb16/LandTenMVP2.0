def bundle_agent_and_action(agent_msg: dict, user_action: str, result_summary: str) -> dict:
    """
    Combines GPT's message, user's chosen action, and system result.
    Returns a dict suitable to append to chat log.
    """
    return {
        "sender": "system",
        "message": (
            f"🤖 Agent proposed: {agent_msg.get('message', '').strip()}\n"
            f"✅ User action: {user_action}\n"
            f"📦 System response: {result_summary}"
        ),
        "actions": []
    }