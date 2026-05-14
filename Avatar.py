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


# ── Estado de sesión ──────────────────────────────────────────────────────────
for key in ["session_token", "session_id", "livekit_url",
            "livekit_client_token", "has_avatar_preview", "error_msg", "success_msg"]:
    if key not in st.session_state:
        st.session_state[key] = None

is_running = bool(
    st.session_state.session_id
    and st.session_state.session_token
    and st.session_state.livekit_url
    and st.session_state.livekit_client_token
)

# ── Acción del botón: viene del componente HTML vía query param ───────────────
# El componente HTML hace window.parent.postMessage o usa st.query_params
# para comunicarse. Usamos query_params para pasar la acción deseada.
action = st.query_params.get("action", None)

if action == "start" and not is_running:
    try:
        token_data = create_session_token()
        session_token = token_data["session_token"]
        session_data = start_session(session_token)

        st.session_state.session_token = session_token
        st.session_state.session_id = session_data["session_id"]
        st.session_state.livekit_url = session_data["livekit_url"]
        st.session_state.livekit_client_token = session_data["livekit_client_token"]
        st.session_state.has_avatar_preview = True
        st.session_state.success_msg = "Sesión iniciada correctamente."
        st.session_state.error_msg = None
    except requests.HTTPError as e:
        st.session_state.error_msg = f"Error HTTP: {e}"
    except Exception as e:
        st.session_state.error_msg = f"Error: {e}"
    finally:
        st.query_params.clear()
        st.rerun()

elif action == "stop" and is_running:
    try:
        stop_session(st.session_state.session_id, st.session_state.session_token)
        st.session_state.session_token = None
        st.session_state.session_id = None
        st.session_state.has_avatar_preview = True
        st.session_state.success_msg = "Sesión detenida correctamente."
        st.session_state.error_msg = None
    except requests.HTTPError as e:
        st.session_state.error_msg = f"Error HTTP: {e}"
    except Exception as e:
        st.session_state.error_msg = f"Error: {e}"
    finally:
        st.query_params.clear()
        st.rerun()

# Recalcular is_running tras posibles cambios
is_running = bool(
    st.session_state.session_id
    and st.session_state.session_token
    and st.session_state.livekit_url
    and st.session_state.livekit_client_token
)

# ── CSS global de Streamlit (solo oculta el menú hamburguesa y footer) ────────
st.markdown("""
<style>
    #MainMenu, footer, header { visibility: hidden; }
    .stApp { background: #0a0a0f; }
    .block-container {
        max-width: 600px;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    /* Eliminar cualquier margen extra de streamlit */
    .stAppViewBlockContainer { padding-top: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Notificaciones (si las hay) ───────────────────────────────────────────────
if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = None
if st.session_state.error_msg:
    st.error(st.session_state.error_msg)
    st.session_state.error_msg = None

# ── Variables para el componente HTML ────────────────────────────────────────
livekit_url     = json.dumps(st.session_state.livekit_url)
livekit_token   = json.dumps(st.session_state.livekit_client_token)
session_id      = json.dumps(st.session_state.session_id)
session_token   = json.dumps(st.session_state.session_token)
stop_url        = json.dumps(f"{BASE_URL}/sessions/stop")
session_dur_ms  = json.dumps(SESSION_DURATION_MS)
is_running_js   = json.dumps(is_running)
btn_label       = "Detener sesión" if is_running else "Iniciar sesión"
btn_label_js    = json.dumps(btn_label)
action_next     = "stop" if is_running else "start"
action_next_js  = json.dumps(action_next)

html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg:        #0a0a0f;
    --card-bg:   #0f0f1a;
    --border:    rgba(255,255,255,0.08);
    --accent1:   #3b6bff;
    --accent2:   #8b3dff;
    --text:      #e8e8f0;
    --muted:     #6b7280;
    --radius:    24px;
    --max-w:     480px;
    /* 720p nativo → mostramos a máx 480px de ancho para calidad perfecta */
    --avatar-w:  480px;
    --avatar-h:  640px; /* 3:4 portrait, típico de 720p avatar */
  }}

  html, body {{
    margin: 0; padding: 0;
    background: transparent;
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }}

  .page {{
    width: 100%;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2.5rem 1rem 2rem;
    gap: 1.5rem;
    background:
      radial-gradient(ellipse 70% 40% at 50% 0%, rgba(59,107,255,0.12) 0%, transparent 60%),
      radial-gradient(ellipse 50% 30% at 80% 100%, rgba(139,61,255,0.10) 0%, transparent 55%),
      var(--bg);
  }}

  /* ── Header ── */
  .header {{
    text-align: center;
    max-width: var(--max-w);
    width: 100%;
  }}

  .header h1 {{
    font-family: 'Syne', sans-serif;
    font-size: clamp(1.6rem, 5vw, 2.2rem);
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.15;
    background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.55rem;
  }}

  .header p {{
    font-size: 0.95rem;
    color: var(--muted);
    line-height: 1.5;
  }}

  /* ── Card del avatar ── */
  .avatar-card {{
    width: 100%;
    max-width: var(--max-w);
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow:
      0 0 0 1px rgba(59,107,255,0.08),
      0 32px 64px rgba(0,0,0,0.5),
      0 2px 8px rgba(0,0,0,0.3);
    display: flex;
    flex-direction: column;
  }}

  /* ── Área del video ── */
  .avatar-viewport {{
    position: relative;
    width: 100%;
    /* Aspect ratio 3:4 (portrait 720p) */
    aspect-ratio: 3 / 4;
    background: #06060e;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  #avatar-container {{
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }}

  /* Video e imagen: NO escalar más allá del tamaño original 720p.
     Si el contenedor es más pequeño, achicamos. Nunca pixelamos. */
  #avatar-container video,
  #avatar-container img {{
    display: block;
    /* Máximo = tamaño real 720p (480px ancho en este layout) */
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
    backface-visibility: hidden;
    transform: translateZ(0);
  }}

  /* Placeholder cuando no hay sesión */
  .avatar-placeholder {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    color: var(--muted);
    text-align: center;
    padding: 2rem;
    height: 100%;
    width: 100%;
  }}

  .avatar-placeholder svg {{
    width: 52px;
    height: 52px;
    opacity: 0.4;
  }}

  .avatar-placeholder span {{
    font-size: 0.88rem;
    font-family: 'DM Sans', sans-serif;
    opacity: 0.6;
    letter-spacing: 0.02em;
  }}

  /* Pulso cuando está activo */
  .live-badge {{
    position: absolute;
    top: 14px;
    right: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(0,0,0,0.65);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 999px;
    padding: 4px 10px 4px 8px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #fff;
    opacity: 0;
    transition: opacity 0.4s;
    pointer-events: none;
  }}

  .live-badge.visible {{ opacity: 1; }}

  .live-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
    animation: pulse-dot 1.5s infinite;
  }}

  @keyframes pulse-dot {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(34,197,94,0.6); }}
    50%        {{ box-shadow: 0 0 0 5px rgba(34,197,94,0); }}
  }}

  /* ── Footer de la card (botón) ── */
  .avatar-footer {{
    padding: 1rem 1.25rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
    background: rgba(255,255,255,0.015);
    border-top: 1px solid var(--border);
  }}

  #avatar-action-btn {{
    width: 100%;
    height: 52px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--accent1), var(--accent2));
    color: #fff;
    font-family: 'Syne', sans-serif;
    font-size: 0.97rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
    box-shadow: 0 6px 24px rgba(59,107,255,0.35);
    position: relative;
    overflow: hidden;
  }}

  #avatar-action-btn::after {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.12), transparent);
    pointer-events: none;
  }}

  #avatar-action-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 10px 32px rgba(59,107,255,0.5);
  }}

  #avatar-action-btn:active {{
    transform: translateY(0);
    opacity: 0.85;
  }}

  #avatar-action-btn:disabled {{
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }}

  .status-text {{
    text-align: center;
    font-size: 0.78rem;
    color: var(--muted);
    min-height: 1em;
    transition: color 0.3s;
  }}

  .status-text.ok  {{ color: #4ade80; }}
  .status-text.err {{ color: #f87171; }}

  /* ── Responsivo ── */
  @media (max-width: 520px) {{
    .page {{ padding: 1.5rem 0.75rem 1.5rem; gap: 1.2rem; }}
    .avatar-card {{ border-radius: 20px; }}
    .avatar-footer {{ padding: 0.9rem 1rem 1rem; }}
    #avatar-action-btn {{ height: 48px; font-size: 0.92rem; }}
  }}
</style>
</head>
<body>

<div class="page">

  <!-- Header -->
  <div class="header">
    <h1>Habla con nuestro agente</h1>
    <p>Activa el avatar y conversa directamente desde tu pantalla.</p>
  </div>

  <!-- Card del avatar -->
  <div class="avatar-card">

    <div class="avatar-viewport">
      <div id="avatar-container">
        <div class="avatar-placeholder" id="avatar-placeholder">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
            <circle cx="12" cy="8" r="4"/>
            <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
          </svg>
          <span>El avatar aparecerá aquí</span>
        </div>
      </div>
      <div class="live-badge" id="live-badge">
        <div class="live-dot"></div>
        EN VIVO
      </div>
    </div>

    <div class="avatar-footer">
      <button id="avatar-action-btn" type="button">{btn_label}</button>
      <div class="status-text" id="status-text"></div>
    </div>

  </div>

</div>

<script type="module">
  import {{
    Room,
    RoomEvent,
    Track
  }} from "https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.esm.mjs";

  // ── Datos de sesión inyectados desde Python ──────────────────────────────
  const livekitUrl      = {livekit_url};
  const livekitToken    = {livekit_token};
  const sessionId       = {session_id};
  const sessionToken    = {session_token};
  const stopUrl         = {stop_url};
  const sessionDuration = {session_dur_ms};
  const isRunning       = {is_running_js};
  const actionNext      = {action_next_js};

  // ── Referencias DOM ──────────────────────────────────────────────────────
  const actionBtn       = document.getElementById("avatar-action-btn");
  const container       = document.getElementById("avatar-container");
  const placeholder     = document.getElementById("avatar-placeholder");
  const statusText      = document.getElementById("status-text");
  const liveBadge       = document.getElementById("live-badge");
  const previewKey      = "liveavatar_last_preview";

  // ── Utilidades de almacenamiento ─────────────────────────────────────────
  function storageSet(k, v) {{
    try {{ sessionStorage.setItem(k, v); }} catch {{}}
    try {{ localStorage.setItem(k, v);   }} catch {{}}
  }}
  function storageGet(k) {{
    try {{ const v = sessionStorage.getItem(k); if (v) return v; }} catch {{}}
    try {{ const v = localStorage.getItem(k);   if (v) return v; }} catch {{}}
    return null;
  }}

  function setStatus(msg, type = "") {{
    statusText.textContent = msg;
    statusText.className = "status-text" + (type ? " " + type : "");
  }}

  // ── Navegación para disparar acción en Streamlit ─────────────────────────
  // Usamos query_params de Streamlit: añadimos ?action=start|stop a la URL
  // del padre, lo que provoca un rerun de Streamlit con el parámetro.
  actionBtn.addEventListener("click", () => {{
    actionBtn.disabled = true;
    setStatus("Procesando...");
    const parentUrl = new URL(window.parent.location.href);
    parentUrl.searchParams.set("action", actionNext);
    window.parent.location.href = parentUrl.toString();
  }});

  // ── Previsualización de frame ────────────────────────────────────────────
  let currentVideo   = null;
  let previewTimer   = null;
  let sessionStopped = false;
  const room         = new Room();

  function drawPreview(dataUrl) {{
    if (!dataUrl) return false;
    const img = new Image();
    img.src = dataUrl;
    img.alt = "Vista previa del avatar";
    // Sin forzar tamaño: el CSS se encarga de no pixelar
    container.innerHTML = "";
    container.appendChild(img);
    return true;
  }}

  function captureFrame(saveOnly = false) {{
    const vid = currentVideo || container.querySelector("video");
    if (!vid || vid.videoWidth === 0) return false;

    const canvas = document.createElement("canvas");
    canvas.width  = vid.videoWidth;
    canvas.height = vid.videoHeight;
    canvas.getContext("2d", {{ alpha: false }}).drawImage(vid, 0, 0);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
    storageSet(previewKey, dataUrl);

    if (!saveOnly) drawPreview(dataUrl);
    return true;
  }}

  function startPreviewCapture() {{
    if (previewTimer) return;
    previewTimer = setInterval(() => captureFrame(true), 900);
  }}

  // ── LiveKit ──────────────────────────────────────────────────────────────
  room.on(RoomEvent.TrackSubscribed, (track) => {{
    if (track.kind === Track.Kind.Video) {{
      const vid = track.attach();
      currentVideo = vid;
      // Dejar que el CSS controle las dimensiones; no forzar width/height en JS
      vid.autoplay   = true;
      vid.playsInline = true;
      vid.muted      = false;

      container.innerHTML = "";
      container.appendChild(vid);
      liveBadge.classList.add("visible");
      setStatus("Avatar conectado — micrófono activo", "ok");
      startPreviewCapture();
    }}
    if (track.kind === Track.Kind.Audio) {{
      const audio = track.attach();
      audio.autoplay = true;
      document.body.appendChild(audio);
    }}
  }});

  async function stopAvatarFromJS() {{
    if (sessionStopped || !sessionId || !sessionToken) return;
    sessionStopped = true;
    captureFrame(false);
    liveBadge.classList.remove("visible");
    try {{
      await fetch(stopUrl, {{
        method: "POST",
        headers: {{
          "Authorization": `Bearer ${{sessionToken}}`,
          "Content-Type": "application/json",
          "Accept": "application/json"
        }},
        body: JSON.stringify({{ session_id: sessionId, reason: "USER_DISCONNECTED" }})
      }});
      room.disconnect();
      setStatus("Sesión detenida automáticamente.", "ok");
    }} catch (e) {{
      setStatus("Error al detener: " + e.message, "err");
    }}
  }}

  async function connectAvatar() {{
    if (!isRunning) {{
      // Mostrar previsualización guardada si existe
      const saved = storageGet(previewKey);
      if (!drawPreview(saved)) {{
        setStatus("Inicia sesión para hablar con el agente.");
      }} else {{
        setStatus("Vista previa de la última sesión.");
      }}
      return;
    }}

    setStatus("Conectando...");
    try {{
      await room.connect(livekitUrl, livekitToken);
      await room.localParticipant.setMicrophoneEnabled(true);
      setStatus("Sesión activa", "ok");

      setTimeout(() => stopAvatarFromJS(), sessionDuration);
    }} catch (e) {{
      const saved = storageGet(previewKey);
      if (!drawPreview(saved)) setStatus("Error: " + e.message, "err");
      else setStatus("Error de conexión. Mostrando vista previa.", "err");
    }}
  }}

  connectAvatar();
</script>
</body>
</html>
"""

# ── Renderizar componente HTML (único punto de verdad para la UI del avatar) ─
# Altura calculada para que quepa header + card sin scroll en desktop.
# En móvil, el componente se adapta con CSS (min-height: auto).
components.html(html, height=780, scrolling=False)
