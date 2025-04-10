import streamlit as st
from streamlit_elements import mui, html

def create_canvas_card(title, content, actions):
    with mui.Card():
        mui.CardHeader(title=title)
        mui.CardContent(content)
        mui.CardActions(
            *[mui.Button(action['label'], onClick=action['callback']) for action in actions]
        )
