import streamlit as st

EXAMPLE_CHAT = [
    {"role": "Tenant", "message": "Cat on wall singing"},
    {"role": "GPT", "message": "Perhaps it's signaling distress or claiming territory."},
    {"role": "Tenant", "message": "Should I be worried?"},
    {"role": "GPT", "message": "Only if it’s frequent or aggressive."},
]

def chat_box(title, style_func):
    st.subheader(title)
    with st.container():
        chat_area = st.container()
        with chat_area:
            for msg in EXAMPLE_CHAT:
                style_func(msg["role"], msg["message"])

def style_plain(role, msg):
    st.markdown(f"**{role}:** {msg}")

def style_bubble(role, msg):
    bg = "#222" if role == "Tenant" else "#444"
    color = "#fff"
    st.markdown(
        f"""
        <div style='background-color:{bg}; color:{color}; padding:10px; border-radius:10px; margin-bottom:5px'>
        <b>{role}:</b> {msg}
        </div>
        """, unsafe_allow_html=True
    )

def style_emojis(role, msg):
    icon = "🧑‍💼" if role == "Tenant" else "🤖"
    st.markdown(f"{icon} **{role}:** {msg}")

def style_card(role, msg):
    st.markdown(
        f"""
        <div style='border:1px solid #555; padding:10px; border-radius:6px; margin-bottom:6px'>
        <b>{role}</b><br>{msg}
        </div>
        """, unsafe_allow_html=True
    )

# Layout: 4 chat design boxes
st.set_page_config(layout="wide")
st.title("🎛️ Chat UI Style Showcase")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    chat_box("🔹 Plain Text", style_plain)

with col2:
    chat_box("🔸 Bubble Style", style_bubble)

with col3:
    chat_box("🤖 Emojis + Role", style_emojis)

with col4:
    chat_box("📦 Card Design", style_card)
