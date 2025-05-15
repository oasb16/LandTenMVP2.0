from streamlit_javascript import st_javascript
import streamlit as st
import json

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
        st.session_state["user_profile"] = result["user_profile"]
        st.session_state["email"] = result["user_profile"].get("email")
        st.session_state["expires_at"] = result["expires_at"]
        st.session_state["logged_in"] = True
        st.session_state["persona"] = result["user_profile"].get("persona", "tenant")
        st.success("✅ Session restored from localStorage.")

def store_session(user_info):
    st.session_state["user_profile"] = user_info
    st.session_state["email"] = user_info.get("email", "")
    st.session_state["persona"] = user_info.get("persona", "tenant")
    st.session_state["expires_at"] = user_info["exp"]
    st.session_state["logged_in"] = True

    import streamlit.components.v1 as components
    components.html(f"""
        <script>
        localStorage.setItem("user_profile", JSON.stringify({json.dumps(user_info)}));
        localStorage.setItem("expires_at", {user_info["exp"]});
        </script>
    """, height=0)
