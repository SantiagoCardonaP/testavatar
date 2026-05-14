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
            "encoding": "H264",
            "quality": "high"
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
    "livekit_client_token",
    "has_avatar_preview"
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
    .stApp {
        background: #111111;
    }

    .block-container {
        max-width: 560px;
        padding-top: 1.6rem;
        padding-bottom: 1.5rem;
    }

    h1 {
        text-align: center;
        font-size: 2rem !important;
        font-weight: 850 !important;
        margin-bottom: 0.4rem !important;
        color: #ffffff !important;
    }

    .subtitle {
        text-align: center;
        color: #94a3b8;
        margin-bottom: 1.5rem;
        font-size: 1rem;
    }

    .button-wrap {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0.5rem auto 1rem auto;
    }

    .button-wrap-hidden {
        width: 1px;
        height: 1px;
        overflow: hidden;
        opacity: 0;
        position: absolute;
        pointer-events: none;
    }

    .button-wrap div[data-testid="stButton"],
    .button-wrap-hidden div[data-testid="stButton"] {
        width: 100%;
        display: flex;
        justify-content: center;
    }

    .button-wrap div[data-testid="stButton"] > button {
        display: block;
        margin-left: auto !important;
        margin-right: auto !important;
        width: 78% !important;
        max-width: 360px !important;
        min-width: 230px !important;
        height: 60px;
        border-radius: 999px;
        font-size: 1.08rem;
        font-weight: 850;
        border: none;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: white;
        box-shadow: 0 12px 30px rgba(37, 99, 235, 0.45);
    }

    .button-wrap div[data-testid="stButton"] > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 36px rgba(37, 99, 235, 0.58);
    }

    .status-card {
        text-align: center;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 0.9rem;
        margin: 0.5rem auto 1rem auto;
        color: #1e293b;
        font-weight: 750;
        max-width: 490px;
    }

    div[data-testid="stAlert"] {
        max-width: 490px;
        margin-left: auto;
        margin-right: auto;
    }

    @media (max-width: 600px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        h1 {
            font-size: 1.7rem !important;
        }

        .button-wrap div[data-testid="stButton"] > button {
            width: 88% !important;
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

should_show_avatar = bool(
    st.session_state.livekit_url
    and st.session_state.livekit_client_token
    and (is_running or st.session_state.has_avatar_preview)
)

button_wrap_class = "button-wrap-hidden" if should_show_avatar else "button-wrap"

st.markdown(f"<div class='{button_wrap_class}'>", unsafe_allow_html=True)
button_clicked = st.button(button_label, use_container_width=False)
st.markdown("</div>", unsafe_allow_html=True)

if button_clicked:
    if is_running:
        try:
            stop_session(
                st.session_state.session_id,
                st.session_state.session_token
            )

            # Marcamos la sesion como detenida, pero NO borramos livekit_url ni
            # livekit_client_token. El componente usa la ultima imagen guardada
            # en sessionStorage/localStorage para conservar la vista previa.
            st.session_state.session_token = None
            st.session_state.session_id = None
            st.session_state.has_avatar_preview = True

            st.success("Sesión detenida correctamente. Vista previa conservada.")
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
            st.session_state.has_avatar_preview = True

            st.success("Sesión iniciada correctamente.")
            st.rerun()

        except requests.HTTPError as e:
            st.error(f"Error HTTP: {e}")
            if e.response is not None:
                st.code(e.response.text)
        except Exception as e:
            st.error(f"Error: {e}")


if should_show_avatar:
    livekit_url = json.dumps(st.session_state.livekit_url)
    livekit_token = json.dumps(st.session_state.livekit_client_token)
    session_id = json.dumps(st.session_state.session_id)
    session_token = json.dumps(st.session_state.session_token)
    stop_url = json.dumps(f"{BASE_URL}/sessions/stop")
    session_duration_ms = json.dumps(SESSION_DURATION_MS)
    is_running_js = json.dumps(is_running)

    html = f"""
    <div class="avatar-shell">
      <div id="status">
        <button id="avatar-action-btn" type="button">
          {button_label}
        </button>
      </div>
      <div id="avatar-container">
        <div class="avatar-placeholder">Vista previa del avatar</div>
      </div>
    </div>

    <style>
      html, body {{
        margin: 0;
        padding: 0;
        background: transparent;
      }}

      .avatar-shell {{
        width: 100%;
        max-width: 430px;
        height: min(72vh, 760px);
        min-height: 560px;
        margin: 0 auto;
        background: #000;
        border-radius: 28px;
        overflow: hidden;
        font-family: Arial, sans-serif;
        box-shadow: 0 22px 55px rgba(15, 23, 42, 0.38);
        border: 1px solid rgba(255,255,255,0.14);
      }}

      #status {{
        color: white;
        text-align: center;
        padding: 10px 12px;
        font-size: 15px;
        font-weight: 800;
        background: rgba(15, 23, 42, 0.88);
        backdrop-filter: blur(10px);
        display: flex;
        align-items: center;
        justify-content: center;
      }}

      #avatar-action-btn {{
        width: min(86%, 320px);
        min-height: 44px;
        border: none;
        border-radius: 999px;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: #ffffff;
        font-size: 16px;
        font-weight: 850;
        cursor: pointer;
        box-shadow: 0 10px 26px rgba(37, 99, 235, 0.45);
      }}

      #avatar-action-btn:hover {{
        transform: translateY(-1px);
        box-shadow: 0 14px 32px rgba(37, 99, 235, 0.58);
      }}

      #avatar-container {{
        width: 100%;
        height: calc(100% - 48px);
        display: flex;
        align-items: center;
        justify-content: center;
        background: #000;
      }}

      #avatar-container video,
      #avatar-container img {{
        width: 100%;
        height: 100%;
        max-width: none;
        object-fit: cover;
        object-position: center center;
        image-rendering: auto;
        backface-visibility: hidden;
        transform: translateZ(0);
      }}

      .avatar-placeholder {{
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: rgba(255,255,255,0.72);
        font-size: 16px;
        font-weight: 800;
        background:
          radial-gradient(circle at 50% 22%, rgba(124, 58, 237, 0.35), transparent 34%),
          linear-gradient(180deg, #111827 0%, #020617 100%);
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
      const isRunning = {is_running_js};

      const statusEl = document.getElementById("status");
      const actionBtn = document.getElementById("avatar-action-btn");
      const container = document.getElementById("avatar-container");
      const previewKey = "liveavatar_last_preview";

      actionBtn.addEventListener("click", () => {
        const buttons = window.parent.document.querySelectorAll("button");
        const target = Array.from(buttons).find((button) =>
          button.innerText.trim() === actionBtn.innerText.trim()
        );

        if (target) {
          target.click();
        }
      });

      let currentVideoElement = null;
      let sessionStopped = false;
      let previewInterval = null;
      const room = new Room();

      function storageSet(key, value) {{
        try {{ window.sessionStorage.setItem(key, value); }} catch (e) {{}}
        try {{ window.localStorage.setItem(key, value); }} catch (e) {{}}
      }}

      function storageGet(key) {{
        try {{
          const value = window.sessionStorage.getItem(key);
          if (value) return value;
        }} catch (e) {{}}

        try {{
          const value = window.localStorage.getItem(key);
          if (value) return value;
        }} catch (e) {{}}

        return null;
      }}

      function drawPreviewImage(dataUrl, statusText) {{
        if (!dataUrl) return false;

        const previewImage = document.createElement("img");
        previewImage.src = dataUrl;
        previewImage.alt = "Vista previa del avatar";
        previewImage.style.width = "100%";
        previewImage.style.height = "100%";
        previewImage.style.maxWidth = "none";
        previewImage.style.objectFit = "cover";
        previewImage.style.objectPosition = "center center";
        previewImage.style.imageRendering = "auto";
        previewImage.style.backfaceVisibility = "hidden";
        previewImage.style.transform = "translateZ(0)";

        container.innerHTML = "";
        container.appendChild(previewImage);
        statusEl.title = statusText;
        return true;
      }}

      function captureCurrentFrame(saveOnly = false) {{
        const video = currentVideoElement || container.querySelector("video");

        if (!video || video.videoWidth === 0 || video.videoHeight === 0) {{
          return false;
        }}

        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext("2d", {{ alpha: false }});
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
        storageSet(previewKey, dataUrl);

        if (!saveOnly) {{
          drawPreviewImage(dataUrl, "Sesión detenida. Vista previa conservada.");
        }}

        return true;
      }}

      function startPreviewCapture() {{
        if (previewInterval) return;
        previewInterval = setInterval(() => {{
          captureCurrentFrame(true);
        }}, 900);
      }}

      async function stopAvatarSession(reasonText) {{
        if (sessionStopped || !sessionId || !sessionToken) return;

        sessionStopped = true;

        try {{
          statusEl.title = "Deteniendo sesión...";
          captureCurrentFrame(false);

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
          statusEl.title = reasonText;

        }} catch (error) {{
          console.error(error);
          statusEl.title = "Error deteniendo sesión: " + error.message;
        }}
      }}

      room.on(RoomEvent.TrackSubscribed, (track) => {{
        if (track.kind === Track.Kind.Video) {{
          const videoElement = track.attach();
          currentVideoElement = videoElement;

          videoElement.style.width = "100%";
          videoElement.style.height = "100%";
          videoElement.style.maxWidth = "none";
          videoElement.style.objectFit = "cover";
          videoElement.style.objectPosition = "center center";
          videoElement.style.imageRendering = "auto";
          videoElement.style.backfaceVisibility = "hidden";
          videoElement.style.transform = "translateZ(0)";
          videoElement.autoplay = true;
          videoElement.playsInline = true;

          container.innerHTML = "";
          container.appendChild(videoElement);

          statusEl.title = "Avatar conectado";
          startPreviewCapture();
        }}

        if (track.kind === Track.Kind.Audio) {{
          const audioElement = track.attach();
          audioElement.autoplay = true;
          document.body.appendChild(audioElement);
        }}
      }});

      async function connectAvatar() {{
        if (!isRunning) {{
          const savedPreview = storageGet(previewKey);
          if (!drawPreviewImage(savedPreview, "Sesión detenida. Vista previa conservada.")) {{
            statusEl.title = "Vista previa del avatar";
          }}
          return;
        }}

        try {{
          await room.connect(livekitUrl, livekitToken);
          await room.localParticipant.setMicrophoneEnabled(true);

          statusEl.title = "Sesión activa con micrófono";

          setTimeout(async () => {{
            await stopAvatarSession("Sesión detenida automáticamente. Vista previa conservada.");
          }}, sessionDurationMs);

        }} catch (error) {{
          console.error(error);
          const savedPreview = storageGet(previewKey);
          if (!drawPreviewImage(savedPreview, "Vista previa del avatar")) {{
            statusEl.title = "Error conectando avatar: " + error.message;
          }}
        }}
      }}

      connectAvatar();
    </script>
    """

    components.html(html, height=820)

else:
    st.info("Presiona el botón para iniciar una sesión con el avatar.")
