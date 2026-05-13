import streamlit as st
import requests
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

API_KEY = st.secrets["LIVEAVATAR_API_KEY"]
AVATAR_ID = st.secrets["LIVEAVATAR_AVATAR_ID"]

def create_liveavatar_session():
    url = "https://api.liveavatar.com/v1/sessions"

    payload = {
        "avatar_id": AVATAR_ID,
        "is_sandbox": False
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    return r.json()["data"]

if st.button("Iniciar avatar"):
    session = create_liveavatar_session()

    session_token = session["session_token"]
    session_id = session["session_id"]

    html = f"""
    <div id="avatar-container" style="width:100%;height:600px;background:#000;"></div>

    <script type="module">
      import {{
        LiveAvatar
      }} from "https://cdn.jsdelivr.net/npm/@heygen/liveavatar-web-sdk/+esm";

      const avatar = new LiveAvatar({{
        sessionToken: "{session_token}",
        sessionId: "{session_id}"
      }});

      async function start() {{
        await avatar.start(document.getElementById("avatar-container"));

        setTimeout(async () => {{
          await avatar.stop();
          document.getElementById("avatar-container").innerHTML =
            "<p style='color:white;text-align:center;padding-top:250px;'>Sesión finalizada</p>";
        }}, 30000);
      }}

      start();
    </script>
    """

    components.html(html, height=620)
