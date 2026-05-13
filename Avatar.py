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
SESSION_DURATION_MS = 30_000


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


def reset_session_state():
    st.session_state.session_token = None
    st.session_state.session_id = None
    st.session_state.livekit_url = None
    st.session_state.livekit_client_token = None


if "session_token" not in st.session_state:
    st.session_state.session_token = None

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "livekit_url" not in st.session_state:
    st.session_state.livekit_url = None

if "livekit_client_token" not in st.session_state:
    st.session_state.livekit_client_token = None


st.title("LiveAvatar en Streamlit")
st.caption("La sesión se detiene automáticamente a nivel API después de 30 segundos. El último frame del avatar queda visible.")

col1, col2 = st.columns(2)

with col1:
    start_clicked = st.button("Iniciar nueva sesión")

with col2:
    stop_clicked = st.button("Detener sesión ahora")


if start_clicked:
    try:
        # Si ya había una sesión activa, se detiene antes de crear otra.
        if st.session_state.session_id and st.session_state.session_token:
            try:
                stop_session(st.session_state.session_id, st.session_state.session_token)
            except requests.HTTPError:
                pass

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
            stop_session(st.session_state.session_id, st.session_state.session_token)
            reset_session_state()
            st.success("Sesión detenida correctamente.")
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
    base_url = json.dumps(BASE_URL)
    session_duration_ms = SESSION_DURATION_MS

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
      const baseUrl = {base_url};
      const sessionDurationMs = {session_duration_ms};

      const statusEl = document.getElementById("status");
      const container = document.getElementById("avatar-container");

      const room = new Room();
      let stoppedByTimer = false;

      room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {{
        if (track.kind === Track.Kind.Video) {{
          const videoElement = track.attach();
          videoElement.id = "avatar-video";
          videoElement.style.width = "100%";
          videoElement.style.height = "100%";
          videoElement.style.objectFit = "contain";
          videoElement.autoplay = true;
          videoElement.playsInline = true;

          container.innerHTML = "";
          container.appendChild(videoElement);

          statusEl.innerText = "Avatar conectado. Micrófono activo.";
        }}

        if (track.kind === Track.Kind.Audio) {{
          const audioElement = track.attach();
          audioElement.autoplay = true;
          document.body.appendChild(audioElement);
        }}
      }});

      async function stopAvatarSessionAtApiLevel() {{
        const response = await fetch(`${{baseUrl}}/sessions/stop`, {{
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
          const text = await response.text();
          throw new Error(`No se pudo detener la sesión: ${{response.status}} ${{text}}`);
        }}
      }}

      async function connectAvatar() {{
        try {{
          await room.connect(livekitUrl, livekitToken);

          // Habilita la entrada de audio del navegador y publica el micrófono a la sala.
          await room.localParticipant.setMicrophoneEnabled(true);

          statusEl.innerText = "Sesión activa con micrófono";

          setTimeout(async () => {{
            try {{
              stoppedByTimer = true;

              // Detiene la sesión real del avatar a nivel API.
              await stopAvatarSessionAtApiLevel();

              // Desconecta LiveKit, pero NO limpia el contenedor ni reemplaza el video.
              // Así el último frame del avatar queda visible mientras se inicia otra sesión.
              room.disconnect();

              const videoElement = document.getElementById("avatar-video");
              if (videoElement) {{
                videoElement.pause();
                videoElement.style.opacity = "1";
              }}

              statusEl.innerText = "Sesión detenida automáticamente. El avatar queda visible para iniciar una nueva sesión.";
            }} catch (error) {{
              console.error(error);
              statusEl.innerText = "Error deteniendo la sesión: " + error.message;
            }}
          }}, sessionDurationMs);

        }} catch (error) {{
          console.error(error);
          statusEl.innerText = "Error conectando avatar o micrófono: " + error.message;
        }}
      }}

      window.addEventListener("beforeunload", async () => {{
        if (!stoppedByTimer) {{
          try {{
            await stopAvatarSessionAtApiLevel();
          }} catch (error) {{
            console.warn("No se pudo detener la sesión antes de cerrar la página", error);
          }}
        }}
      }});

      connectAvatar();
    </script>
    """

    components.html(html, height=650)
else:
    st.info("Inicia una sesión para mostrar el avatar.")
