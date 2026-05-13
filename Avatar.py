import json
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="LiveAvatar en Streamlit", layout="wide")

API_KEY = st.secrets["LIVEAVATAR_API_KEY"]
AVATAR_ID = st.secrets["LIVEAVATAR_AVATAR_ID"]

BASE_URL = "https://api.liveavatar.com/v1"


def create_session_token():
    url = f"{BASE_URL}/sessions/token"

    payload = {
        "mode": "FULL",
        "avatar_id": AVATAR_ID,
        "is_sandbox": False,
        "video_settings": {
            "encoding": "VP8",
            "quality": "medium"
        }
    }

    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["data"]


def start_session(session_token):
    url = f"{BASE_URL}/sessions/start"

    headers = {
        "Authorization": f"Bearer {session_token}",
        "Accept": "application/json"
    }

    response = requests.post(url, headers=headers)
    response.raise_for_status()

    return response.json()["data"]


def stop_session(session_id, session_token):
    url = f"{BASE_URL}/sessions/stop"

    payload = {
        "session_id": session_id
    }

    headers = {
        "Authorization": f"Bearer {session_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


st.title("LiveAvatar en Streamlit")

if "session_token" not in st.session_state:
    st.session_state.session_token = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "livekit_url" not in st.session_state:
    st.session_state.livekit_url = None
if "livekit_client_token" not in st.session_state:
    st.session_state.livekit_client_token = None


col1, col2 = st.columns(2)

with col1:
    start_clicked = st.button("Iniciar avatar")

with col2:
    stop_clicked = st.button("Detener avatar")


if start_clicked:
    try:
        token_data = create_session_token()
        session_token = token_data["session_token"]

        session_data = start_session(session_token)

        st.session_state.session_token = session_token
        st.session_state.session_id = session_data["session_id"]
        st.session_state.livekit_url = session_data["livekit_url"]
        st.session_state.livekit_client_token = session_data["livekit_client_token"]

        st.success("Sesión iniciada correctamente.")

    except requests.HTTPError as e:
        st.error(f"Error HTTP: {e}")
        st.code(e.response.text if e.response is not None else "")
    except Exception as e:
        st.error(f"Error: {e}")


if stop_clicked:
    try:
        if st.session_state.session_id and st.session_state.session_token:
            stop_session(
                st.session_state.session_id,
                st.session_state.session_token
            )
            st.success("Sesión detenida.")
            st.session_state.session_id = None
            st.session_state.session_token = None
        else:
            st.warning("No hay una sesión activa.")
    except requests.HTTPError as e:
        st.error(f"Error HTTP: {e}")
        st.code(e.response.text if e.response is not None else "")
    except Exception as e:
        st.error(f"Error: {e}")


if st.session_state.livekit_url and st.session_state.livekit_client_token:
    livekit_url = json.dumps(st.session_state.livekit_url)
    livekit_token = json.dumps(st.session_state.livekit_client_token)
    session_id = json.dumps(st.session_state.session_id)

    html = f"""
    <div style="width:100%;height:620px;background:#111;border-radius:16px;overflow:hidden;">
      <div id="status" style="color:white;font-family:sans-serif;padding:12px;">
        Conectando avatar...
      </div>

      <div id="avatar-container" style="width:100%;height:560px;"></div>
    </div>

    <script type="module">
      import {{
        Room,
        RoomEvent,
        Track
      }} from "https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.esm.mjs";

      const livekitUrl = {livekit_url};
      const livekitToken = {livekit_token};
      const sessionId = {session_id};

      const statusEl = document.getElementById("status");
      const container = document.getElementById("avatar-container");

      const room = new Room();

      room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {{
        if (track.kind === Track.Kind.Video) {{
          const videoElement = track.attach();
          videoElement.style.width = "100%";
          videoElement.style.height = "100%";
          videoElement.style.objectFit = "contain";
          videoElement.autoplay = true;
          videoElement.playsInline = true;
          container.appendChild(videoElement);
          statusEl.innerText = "Avatar conectado";
        }}

        if (track.kind === Track.Kind.Audio) {{
          const audioElement = track.attach();
          audioElement.autoplay = true;
          document.body.appendChild(audioElement);
        }}
      }});

      async function connectAvatar() {{
        try {{
          await room.connect(livekitUrl, livekitToken);
          statusEl.innerText = "Sesión activa";

          // Corta visualmente la sesión después de 30 segundos.
          // El stop real del lado API lo maneja el botón de Streamlit.
          setTimeout(() => {{
            room.disconnect();
            statusEl.innerText = "Sesión finalizada después de 30 segundos";
            container.innerHTML = "";
          }}, 30000);

        }} catch (error) {{
          console.error(error);
          statusEl.innerText = "Error conectando LiveAvatar: " + error.message;
        }}
      }}

      connectAvatar();
    </script>
    """

    components.html(html, height=650)
