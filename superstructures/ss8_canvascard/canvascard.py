import streamlit as st
from streamlit_elements import mui, html

def create_canvas_card(title, content, actions):
    with mui.Card(sx={"marginBottom": 2, "backgroundColor": "#1e1e1e", "color": "white", "maxWidth": 700}):
        mui.CardHeader(title=title)
        mui.CardContent(html.p(content))

        if actions:
            with mui.CardActions():
                for action in actions:
                    mui.Button(action["label"], onClick=action["callback"])
