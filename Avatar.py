import json
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="LiveAvatar Streamlit", layout="wide")

API_KEY = st.secrets["LIVEAVATAR_API_KEY"]
AVATAR_ID = st.secrets["LIVEAVATAR_AVATAR_ID"]
CONTEXT_ID = st.secrets["LIVEAVATAR_CONTEXT_ID"]
VOICE_ID = st.secrets["LIVEAVATAR_VOICE_ID"]

BASE_URL = "https://api.liveavatar.com/v1"
SESSION_DURATION_MS = 10000


def create_session_token():
    url = f"{BASE_URL}/sessions/token"

    payload = {
        "mode": "LITE",
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


st.title("LiveAvatar en Streamlit")

col1, col2 = st.columns(2)

with col1:
    start_clicked = st.button("Iniciar nueva sesión")

with col2:
    stop_clicked = st.button("Detener sesión ahora")


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
        if e.response is not None:
            st.code(e.response.text)
    except Exception as e:
        st.error(f"Error: {e}")


if stop_clicked:
    try:
        if st.session_state.session_id and st.session_state.session_token:
            stop_session(
                st.session_state.session_id,
                st.session_state.session_token
            )

            # No limpiamos el contenedor visual desde Python.
            # El frontend mantiene congelado el último frame hasta nueva sesión.
            st.session_state.session_token = None
            st.session_state.session_id = None
            st.session_state.livekit_url = None
            st.session_state.livekit_client_token = None

            st.success("Sesión detenida a nivel del avatar.")
        else:
            st.warning("No hay una sesión activa.")

    except requests.HTTPError as e:
        st.error(f"Error HTTP: {e}")
        if e.response is not None:
            st.code(e.response.text)
    except Exception as e:
        st.error(f"Error: {e}")


if st.session_state.livekit_url and st.session_state.livekit_client_token:
    livekit_url = json.dumps(st.session_state.livekit_url)
    livekit_token = json.dumps(st.session_state.livekit_client_token)
    session_id = json.dumps(st.session_state.session_id)
    session_token = json.dumps(st.session_state.session_token)
    stop_url = json.dumps(f"{BASE_URL}/sessions/stop")
    session_duration_ms = json.dumps(SESSION_DURATION_MS)

    html = f"""
    <div style="
        width:100%;
        height:620px;
        background:#111;
        border-radius:16px;
        overflow:hidden;
        font-family:Arial, sans-serif;
    ">
      <div id="status" style="
          color:white;
          padding:12px;
          font-size:16px;
      ">
        Conectando avatar...
      </div>

      <div id="avatar-container" style="
          width:100%;
          height:560px;
          display:flex;
          align-items:center;
          justify-content:center;
      "></div>
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
        frozenImage.style.objectFit = "contain";

        container.innerHTML = "";
        container.appendChild(frozenImage);

        return true;
      }}

      async function stopAvatarSession(reasonText) {{
        if (sessionStopped) {{
          return;
        }}

        sessionStopped = true;

        try {{
          statusEl.innerText = "Deteniendo sesión del avatar...";

          // 1. Congela el último frame antes de cortar la sesión real.
          freezeLastFrame();

          // 2. Detiene la sesión real del avatar/API.
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

          // 3. Desconecta LiveKit solo después de congelar la imagen.
          room.disconnect();

          statusEl.innerText = reasonText;

        }} catch (error) {{
          console.error(error);
          statusEl.innerText = "Error deteniendo sesión del avatar: " + error.message;
        }}
      }}

      room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {{
        if (track.kind === Track.Kind.Video) {{
          const videoElement = track.attach();
          currentVideoElement = videoElement;

          videoElement.style.width = "100%";
          videoElement.style.height = "100%";
          videoElement.style.objectFit = "contain";
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

          // Habilita entrada de audio del micrófono.
          // El navegador pedirá permiso la primera vez.
          await room.localParticipant.setMicrophoneEnabled(true);

          statusEl.innerText = "Sesión activa con micrófono";

          // Detiene la sesión real del avatar a los 30 segundos.
          // La app de Streamlit queda abierta y el último frame queda visible.
          setTimeout(async () => {{
            await stopAvatarSession(
              "Sesión detenida automáticamente. El avatar queda visible para iniciar una nueva sesión."
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

    components.html(html, height=650)
else:
    st.info("Presiona 'Iniciar nueva sesión' para activar el avatar.")
