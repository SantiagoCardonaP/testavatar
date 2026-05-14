import json
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Habla con nuestro agente",
    layout="centered",
    initial_sidebar_state="collapsed"
)

API_KEY = st.secrets["LIVEAVATAR_API_KEY"]
AVATAR_ID = st.secrets["LIVEAVATAR_AVATAR_ID"]
CONTEXT_ID = st.secrets["LIVEAVATAR_CONTEXT_ID"]
VOICE_ID = st.secrets["LIVEAVATAR_VOICE_ID"]

BASE_URL = "https://api.liveavatar.com/v1"
SESSION_DURATION_MS = 30000


def create_session_token():
    url = f"{BASE_URL}/sessions/token"

    payload = {
        "mode": "FULL",
        "avatar_id": AVATAR_ID,
        "avatar_persona": {
            "context_id": CONTEXT_ID,
            "voice_id": VOICE_ID,
            "language": "es"
        },
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
        "session_id": session_id,
        "reason": "USER_DISCONNECTED"
    }

    headers = {
        "Authorization": f"Bearer {session_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


for key in [
    "session_token",
    "session_id",
    "livekit_url",
    "livekit_client_token"
]:
    if key not in st.session_state:
        st.session_state[key] = None


is_running = bool(
    st.session_state.session_id
    and st.session_state.session_token
    and st.session_state.livekit_url
    and st.session_state.livekit_client_token
)


st.markdown("""
<style>
    .block-container {
        max-width: 520px;
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }

    h1 {
        text-align: center;
        font-size: 2rem !important;
        font-weight: 800 !important;
        margin-bottom: 0.4rem !important;
    }

    .subtitle {
        text-align: center;
        color: #6b7280;
        margin-bottom: 1.5rem;
        font-size: 1rem;
    }

    div.stButton > button {
        width: 100%;
        height: 58px;
        border-radius: 999px;
        font-size: 1.1rem;
        font-weight: 800;
        border: none;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: white;
        box-shadow: 0 12px 28px rgba(37, 99, 235, 0.35);
    }

    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 34px rgba(37, 99, 235, 0.45);
    }

    .status-card {
        text-align: center;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 0.9rem;
        margin-bottom: 1rem;
        color: #374151;
        font-weight: 600;
    }

    @media (max-width: 600px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        h1 {
            font-size: 1.7rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)


st.title("Habla con nuestro agente")
st.markdown(
    "<div class='subtitle'>Activa el avatar y conversa directamente desde tu pantalla.</div>",
    unsafe_allow_html=True
)


button_label = "Detener sesión" if is_running else "Iniciar sesión"

if st.button(button_label):
    if is_running:
        try:
            stop_session(
                st.session_state.session_id,
                st.session_state.session_token
            )

            st.session_state.session_token = None
            st.session_state.session_id = None
            st.session_state.livekit_url = None
            st.session_state.livekit_client_token = None

            st.success("Sesión detenida correctamente.")
            st.rerun()

        except requests.HTTPError as e:
            st.error(f"Error HTTP: {e}")
            if e.response is not None:
                st.code(e.response.text)
        except Exception as e:
            st.error(f"Error: {e}")

    else:
        try:
            token_data = create_session_token()
            session_token = token_data["session_token"]

            session_data = start_session(session_token)

            st.session_state.session_token = session_token
            st.session_state.session_id = session_data["session_id"]
            st.session_state.livekit_url = session_data["livekit_url"]
            st.session_state.livekit_client_token = session_data["livekit_client_token"]

            st.success("Sesión iniciada correctamente.")
            st.rerun()

        except requests.HTTPError as e:
            st.error(f"Error HTTP: {e}")
            if e.response is not None:
                st.code(e.response.text)
        except Exception as e:
            st.error(f"Error: {e}")


if st.session_state.livekit_url and st.session_state.livekit_client_token:
    st.markdown(
        "<div class='status-card'>Avatar activo. Puedes hablar con el agente.</div>",
        unsafe_allow_html=True
    )

    livekit_url = json.dumps(st.session_state.livekit_url)
    livekit_token = json.dumps(st.session_state.livekit_client_token)
    session_id = json.dumps(st.session_state.session_id)
    session_token = json.dumps(st.session_state.session_token)
    stop_url = json.dumps(f"{BASE_URL}/sessions/stop")
    session_duration_ms = json.dumps(SESSION_DURATION_MS)

    html = f"""
    <div class="avatar-shell">
      <div id="status">Conectando avatar...</div>
      <div id="avatar-container"></div>
    </div>

    <style>
      .avatar-shell {{
        width: 100%;
        max-width: 430px;
        height: min(72vh, 760px);
        min-height: 560px;
        margin: 0 auto;
        background: radial-gradient(circle at top, #1f2937, #020617);
        border-radius: 28px;
        overflow: hidden;
        font-family: Arial, sans-serif;
        box-shadow: 0 22px 55px rgba(15, 23, 42, 0.35);
        border: 1px solid rgba(255,255,255,0.12);
      }}

      #status {{
        color: white;
        text-align: center;
        padding: 14px 12px;
        font-size: 15px;
        font-weight: 700;
        background: rgba(15, 23, 42, 0.72);
        backdrop-filter: blur(10px);
      }}

      #avatar-container {{
        width: 100%;
        height: calc(100% - 48px);
        display: flex;
        align-items: center;
        justify-content: center;
        background: #050816;
      }}

      #avatar-container video,
      #avatar-container img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center top;
      }}

      @media (max-width: 600px) {{
        .avatar-shell {{
          max-width: 100%;
          height: 72vh;
          min-height: 520px;
          border-radius: 24px;
        }}
      }}
    </style>

    <script type="module">
      import {{
        Room,
        RoomEvent,
        Track
      }} from "https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.esm.mjs";

      const livekitUrl = {livekit_url};
      const livekitToken = {livekit_token};
      const sessionId = {session_id};
      const sessionToken = {session_token};
      const stopUrl = {stop_url};
      const sessionDurationMs = {session_duration_ms};

      const statusEl = document.getElementById("status");
      const container = document.getElementById("avatar-container");

      let currentVideoElement = null;
      let sessionStopped = false;

      const room = new Room();

      function freezeLastFrame() {{
        const video = currentVideoElement || container.querySelector("video");

        if (!video || video.videoWidth === 0 || video.videoHeight === 0) {{
          return false;
        }}

        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const frozenImage = document.createElement("img");
        frozenImage.src = canvas.toDataURL("image/png");
        frozenImage.style.width = "100%";
        frozenImage.style.height = "100%";
        frozenImage.style.objectFit = "cover";
        frozenImage.style.objectPosition = "center top";

        container.innerHTML = "";
        container.appendChild(frozenImage);

        return true;
      }}

      async function stopAvatarSession(reasonText) {{
        if (sessionStopped) return;

        sessionStopped = true;

        try {{
          statusEl.innerText = "Deteniendo sesión...";

          freezeLastFrame();

          const response = await fetch(stopUrl, {{
            method: "POST",
            headers: {{
              "Authorization": `Bearer ${{sessionToken}}`,
              "Content-Type": "application/json",
              "Accept": "application/json"
            }},
            body: JSON.stringify({{
              session_id: sessionId,
              reason: "USER_DISCONNECTED"
            }})
          }});

          if (!response.ok) {{
            const errorText = await response.text();
            throw new Error(errorText || `HTTP ${{response.status}}`);
          }}

          room.disconnect();
          statusEl.innerText = reasonText;

        }} catch (error) {{
          console.error(error);
          statusEl.innerText = "Error deteniendo sesión: " + error.message;
        }}
      }}

      room.on(RoomEvent.TrackSubscribed, (track) => {{
        if (track.kind === Track.Kind.Video) {{
          const videoElement = track.attach();
          currentVideoElement = videoElement;

          videoElement.style.width = "100%";
          videoElement.style.height = "100%";
          videoElement.style.objectFit = "cover";
          videoElement.style.objectPosition = "center top";
          videoElement.autoplay = true;
          videoElement.playsInline = true;

          container.innerHTML = "";
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
          await room.localParticipant.setMicrophoneEnabled(true);

          statusEl.innerText = "Sesión activa con micrófono";

          setTimeout(async () => {{
            await stopAvatarSession(
              "Sesión detenida automáticamente."
            );
          }}, sessionDurationMs);

        }} catch (error) {{
          console.error(error);
          statusEl.innerText = "Error conectando avatar: " + error.message;
        }}
      }}

      connectAvatar();
    </script>
    """

    components.html(html, height=820)

else:
    st.info("Presiona el botón para iniciar una sesión con el avatar.")
