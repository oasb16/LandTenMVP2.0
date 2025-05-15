import streamlit as st
from streamlit_javascript import st_javascript
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login
from superstructures.ss1_gate.persona_extractor import extract_persona
from superstructures.ss1_gate.shared.dynamodb import save_user_profile
from datetime import datetime
import requests, base64, json, jwt

st.set_page_config(page_title="LandTen 2.0 – TriChatLite", layout="wide")

# === Secrets
try:
    COGNITO_DOMAIN = st.secrets["COGNITO_DOMAIN"]
    REDIRECT_URI = st.secrets["REDIRECT_URI"]
    CLIENT_ID = st.secrets["COGNITO_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["COGNITO_CLIENT_SECRET"]
    TOKEN_ENDPOINT = f"{COGNITO_DOMAIN}/oauth2/token"
except KeyError as e:
    st.error(f"Missing required secret: {e.args[0]}")
    st.stop()

# === Utils: Store & Restore
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

def store_session(profile):
    st.session_state["user_profile"] = profile
    st.session_state["email"] = profile.get("email", "")
    st.session_state["expires_at"] = profile.get("exp")
    st.session_state["logged_in"] = True
    js = f"""
        localStorage.setItem("user_profile", JSON.stringify({json.dumps(profile)}));
        localStorage.setItem("expires_at", {profile.get("exp", 0)});
    """
    import streamlit.components.v1 as components
    components.html(f"<script>{js}</script>", height=0)

# === Restore session
if "logged_in" not in st.session_state:
    try_restore_session()

# === If query code exists AND session not restored, then try token exchange
if "code" in st.query_params and "user_profile" not in st.session_state:
    st.session_state["oauth_code"] = st.query_params["code"]
    # Do NOT run token exchange immediately — wait for store_session later

    st.session_state["persona"] = st.selectbox("Choose your role", ["tenant", "landlord", "contractor"])
    st.session_state["logged_in"] = True
    st.success("✅ Logged in successfully")

# === Token Exchange
if st.session_state.get("oauth_code") and "user_profile" not in st.session_state:
    code = st.session_state["oauth_code"]
    if st.session_state.get("last_code") == code:
        st.warning("⚠️ Duplicate login attempt.")
    else:
        st.session_state["last_code"] = code
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
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

                user_info["persona"] = st.session_state["persona"]
                store_session(user_info)


                try:
                    save_user_profile({
                        "user_id": user_info.get("userId", ""),
                        "name": user_info.get("cognito:username", ""),
                        "email": user_info.get("email", ""),
                        "persona": user_info.get("persona"),
                        "login_source": "GoogleSSO",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    st.success("✅ Profile saved to DB")
                except Exception as e:
                    st.error(f"❌ DB save error: {e}")
            else:
                st.error(f"OAuth failed: {res.status_code} {res.text}")
        except Exception as e:
            st.error(f"Token exchange error: {e}")

# === Routing Helper
def handle_persona_routing():
    route_map = {
        "tenant": "tenant_dashboard",
        "contractor": "contractor_dashboard",
        "landlord": "landlord_dashboard"
    }
    route = route_map.get(st.session_state.get("persona"))
    if route:
        st.session_state["page"] = route
    else:
        st.error("Unknown persona route.")

# === Logout Handler
def logout():
    keys = ["logged_in", "user_profile", "email", "persona", "page", "expires_at"]
    for k in keys:
        st.session_state.pop(k, None)
    import streamlit.components.v1 as components
    components.html("""
        <script>
        localStorage.removeItem("user_profile");
        localStorage.removeItem("expires_at");
        </script>
    """, height=0)
    st.rerun()

# === Routing
if "user_profile" in st.session_state:
    handle_persona_routing()

if st.session_state.get("logged_in") and "page" not in st.session_state:
    handle_persona_routing()

page = st.session_state.get("page")
if not page:
    st.error("No page specified. Please log in again.")
    st.stop()

# === Load Dashboard
if page == "tenant_dashboard":
    from superstructures.ss1_gate.streamlit_frontend.tenant_dashboard import run_tenant_dashboard
    run_tenant_dashboard()
elif page == "contractor_dashboard":
    from superstructures.ss1_gate.streamlit_frontend.contractor_dashboard import run_contractor_dashboard
    run_contractor_dashboard()
elif page == "landlord_dashboard":
    from superstructures.ss1_gate.streamlit_frontend.landlord_dashboard import run_landlord_dashboard
    run_landlord_dashboard()
else:
    st.error("Invalid route.")
