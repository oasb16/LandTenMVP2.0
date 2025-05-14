# utils/session_persistence.py
import json
import streamlit as st
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript

def try_restore_session():
    result = st_javascript("""
        async () => {
            const profile = localStorage.getItem("user_profile");
            const expires = localStorage.getItem("expires_at");
            if (!profile || !expires) return null;

            const now = Math.floor(Date.now() / 1000);
            if (parseInt(expires) < now) {
                localStorage.removeItem("user_profile");
                localStorage.removeItem("expires_at");
                return null;
            }

            return {
                user_profile: JSON.parse(profile),
                expires_at: parseInt(expires)
            };
        }
    """)

    if result:
        st.success("Session restored from local storage.")
        st.session_state["user_profile"] = result["user_profile"]
        st.session_state["email"] = result["user_profile"].get("email")
        st.session_state["expires_at"] = result["expires_at"]
        st.session_state["logged_in"] = True
        st.session_state["persona"] = result["user_profile"].get("persona", "tenant")
    
    return result


def store_session(user_profile: dict):
    exp = user_profile.get("exp")
    if not exp:
        st.error("⚠️ Cannot persist session without 'exp' in user_profile.")
        return

    profile_json = json.dumps(user_profile)
    components.html(f"""
        <script>
            localStorage.setItem("user_profile", JSON.stringify({profile_json}));
            localStorage.setItem("expires_at", {exp});
        </script>
    """, height=0)
