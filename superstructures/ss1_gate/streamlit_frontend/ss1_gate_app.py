import streamlit as st
import requests
import base64
import json
from datetime import datetime
import jwt
from urllib.parse import quote, unquote

from superstructures.ss1_gate.persona_extractor import extract_persona
from superstructures.ss1_gate.shared.dynamodb import write_user_profile

# ------------------------------
# Configuration
# ------------------------------
# Verify secrets configuration
try:
    COGNITO_DOMAIN = st.secrets["COGNITO_DOMAIN"]
    REDIRECT_URI = st.secrets["REDIRECT_URI"]
    CLIENT_ID = st.secrets["COGNITO_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["COGNITO_CLIENT_SECRET"]
    TOKEN_ENDPOINT = f"{COGNITO_DOMAIN}/oauth2/token"
except KeyError as e:
    st.error(f"Missing required secret: {e.args[0]}")
    st.stop()

# ------------------------------
# Login Flow
# ------------------------------
def run_login():
    # Step 1: Persona Picker
    if "persona" not in st.session_state:
        st.session_state["persona"] = st.selectbox("Choose your role", ["tenant", "landlord", "contractor"])

    query_params = st.query_params
    code = query_params.get("code", None)
    state_raw = query_params.get("state", None)

    # Step 2: Decode state param (persona)
    try:
        decoded_state = json.loads(unquote(state_raw)) if state_raw else {}
        persona = decoded_state.get("persona", st.session_state.get("persona", "tenant"))
    except:
        persona = st.session_state.get("persona", "tenant")

    # Step 3: Handle OAuth2 code exchange
    if code:
        # Prevent reusing same code
        if st.session_state.get("last_code") == code:
            st.warning("⚠️ Duplicate login attempt — please refresh and retry.")
            return
        st.session_state["last_code"] = code

        # Prepare token request
        basic_auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}"
        }
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }

        try:
            res = requests.post(TOKEN_ENDPOINT, data=payload, headers=headers)
            if res.status_code == 200:
                tokens = res.json()
                id_token = tokens.get("id_token", "")
                user_info = jwt.decode(id_token, options={"verify_signature": False})

                st.session_state["logged_in"] = True
                st.session_state["email"] = user_info.get("email", "")
                st.session_state["persona"] = persona

                # DB Sync
                try:
                    write_user_profile({
                        "email": st.session_state["email"],
                        "persona": persona,
                        "login_source": "GoogleSSO",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    st.success(f"✅ Profile saved to DB: {st.session_state['email']} ({persona})")
                except Exception as db_error:
                    st.error(f"❌ DB error: {db_error}")

                # Final cleanup
                st.query_params.clear()
                st.rerun()

            else:
                st.error(f"Login failed: {res.text}")

        except requests.exceptions.RequestException as req_error:
            st.error(f"Network error during login: {req_error}")
        except jwt.DecodeError:
            st.error("Failed to decode ID token. Please try again.")
        except Exception as e:
            st.error(f"Unexpected error during login: {e}")

    # Step 4: Show login button if not authenticated
    else:
        from urllib.parse import quote
        import json
        import streamlit as st

        persona = st.session_state.get("persona", "tenant")
        state_json = json.dumps({"persona": persona})
        encoded_state = quote(state_json)

        login_url = (
            "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com/oauth2/authorize"
            f"?identity_provider=Google"
            f"&redirect_uri=https://landtenmvp20.streamlit.app/"
            f"&response_type=CODE"
            f"&client_id=2u127f11v2mjq1sq08j4i9pq4l"
            f"&state={encoded_state}"
            f"&scope=email+openid+phone"
        )

        # Use JS redirect to avoid iframe issues
        if st.button("🔐 Login with Google SSO"):
            st.markdown(
                f"<script>window.location.href = '{login_url}'</script>",
                unsafe_allow_html=True
            )