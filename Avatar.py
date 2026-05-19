import json
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Julius Fest — Asistente Virtual",
    layout="centered",
    initial_sidebar_state="collapsed"
)

API_KEY    = st.secrets["LIVEAVATAR_API_KEY"]
AVATAR_ID  = st.secrets["LIVEAVATAR_AVATAR_ID"]
CONTEXT_ID = st.secrets["LIVEAVATAR_CONTEXT_ID"]
VOICE_ID   = st.secrets["LIVEAVATAR_VOICE_ID"]

BASE_URL            = "https://api.liveavatar.com/v1"
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
        "video_settings": {"encoding": "H264", "quality": "high"}
    }
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["data"]


def start_session(token):
    url = f"{BASE_URL}/sessions/start"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]


def stop_session(sid, token):
    url = f"{BASE_URL}/sessions/stop"
    payload = {"session_id": sid, "reason": "USER_DISCONNECTED"}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


# ── Estado ────────────────────────────────────────────────────────────────────
for key in ["session_token", "session_id", "livekit_url", "livekit_client_token",
            "has_avatar_preview"]:
    if key not in st.session_state:
        st.session_state[key] = None

is_running = bool(
    st.session_state.session_id
    and st.session_state.session_token
    and st.session_state.livekit_url
    and st.session_state.livekit_client_token
)

# ── CSS global de Streamlit ───────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');

    #MainMenu, footer, header { visibility: hidden; }

    html, body, .stApp {
        font-family: 'Montserrat', sans-serif !important;
        background: #0a0a0f !important;
    }

    .stApp {
        padding-top: 0 !important;
    }

    .block-container {
        max-width: 480px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* Botón Streamlit: off-screen, invisible, sin espacio en el layout */
    div[data-testid="stButton"] {
        position: fixed !important;
        top: -9999px !important;
        left: -9999px !important;
        width: 1px !important;
        height: 1px !important;
        overflow: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        z-index: -1 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Botón Streamlit oculto (el iframe hace .click() sobre él) ─────────────────
btn_label   = "Detener conversación" if is_running else "Toca para conversar"
btn_clicked = st.button(btn_label, key="streamlit_action_btn")

if btn_clicked:
    if is_running:
        try:
            stop_session(st.session_state.session_id, st.session_state.session_token)
            st.session_state.session_token      = None
            st.session_state.session_id         = None
            st.session_state.has_avatar_preview = True
        except Exception as e:
            st.error(f"Error al detener: {e}")
    else:
        try:
            token_data   = create_session_token()
            session_tok  = token_data["session_token"]
            session_data = start_session(session_tok)

            st.session_state.session_token        = session_tok
            st.session_state.session_id           = session_data["session_id"]
            st.session_state.livekit_url          = session_data["livekit_url"]
            st.session_state.livekit_client_token = session_data["livekit_client_token"]
            st.session_state.has_avatar_preview   = True
        except Exception as e:
            st.error(f"Error al iniciar: {e}")
    st.rerun()

# Recalcular tras posibles cambios
is_running = bool(
    st.session_state.session_id
    and st.session_state.session_token
    and st.session_state.livekit_url
    and st.session_state.livekit_client_token
)

# ── Variables para el HTML ────────────────────────────────────────────────────
livekit_url    = json.dumps(st.session_state.livekit_url)
livekit_token  = json.dumps(st.session_state.livekit_client_token)
session_id     = json.dumps(st.session_state.session_id)
session_token  = json.dumps(st.session_state.session_token)
stop_url       = json.dumps(f"{BASE_URL}/sessions/stop")
session_dur_ms = json.dumps(SESSION_DURATION_MS)
is_running_js  = json.dumps(is_running)
btn_label_js   = json.dumps(btn_label)

# Altura del iframe calibrada para móvil (aprox. 680–780px de viewport visible).
IFRAME_HEIGHT = 720

html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg:    #0a0a0f;
    --card:  #0f0f1a;
    --bdr:   rgba(255,255,255,0.09);
    --a1:    #3b6bff;
    --a2:    #8b3dff;
    --text:  #e8e8f0;
    --muted: #7c849a;
    --r:     20px;
    --font:  'Montserrat', sans-serif;
  }}

  html, body {{
    margin: 0; padding: 0;
    background: transparent;
    font-family: var(--font);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
    height: {IFRAME_HEIGHT}px;
    overflow: hidden;
  }}

  /* Fondo con gradientes */
  .page {{
    width: 100%;
    height: {IFRAME_HEIGHT}px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 20px 14px 14px;
    gap: 14px;
    background:
      radial-gradient(ellipse 80% 35% at 50% 0%, rgba(59,107,255,0.18) 0%, transparent 55%),
      radial-gradient(ellipse 55% 25% at 85% 95%, rgba(139,61,255,0.14) 0%, transparent 50%),
      var(--bg);
    overflow: hidden;
  }}

  /* ── Header ── */
  .hdr {{
    text-align: center;
    width: 100%;
    max-width: 440px;
    flex-shrink: 0;
  }}

  .hdr h1 {{
    font-family: var(--font);
    font-size: clamp(1.4rem, 5.5vw, 1.75rem);
    font-weight: 900;
    letter-spacing: -0.02em;
    line-height: 1.15;
    background: linear-gradient(140deg, #ffffff 25%, #a5b4fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
  }}

  .hdr p {{
    font-family: var(--font);
    font-size: clamp(0.78rem, 3vw, 0.9rem);
    font-weight: 500;
    color: var(--muted);
    line-height: 1.5;
    max-width: 360px;
    margin: 0 auto;
  }}

  /* ── Card ── */
  .card {{
    width: 100%;
    max-width: 440px;
    flex: 1;
    min-height: 0;
    background: var(--card);
    border: 1px solid var(--bdr);
    border-radius: var(--r);
    overflow: hidden;
    box-shadow:
      0 0 0 1px rgba(59,107,255,0.08),
      0 20px 50px rgba(0,0,0,0.6),
      0 2px 6px rgba(0,0,0,0.4);
    display: flex;
    flex-direction: column;
  }}

  /* ── Viewport del avatar ── */
  .viewport {{
    position: relative;
    width: 100%;
    flex: 1;
    min-height: 0;
    background: #05050d;
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
  }}

  /* Nunca pixelar: no escalar más allá de la resolución nativa */
  #avatar-container video,
  #avatar-container img {{
    display: block;
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
    backface-visibility: hidden;
    transform: translateZ(0);
    image-rendering: -webkit-optimize-contrast;
  }}

  /* Placeholder */
  .placeholder {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: var(--muted);
    text-align: center;
    padding: 2rem;
    width: 100%;
    height: 100%;
  }}
  .placeholder svg {{
    width: 44px; height: 44px;
    opacity: 0.3;
  }}
  .placeholder span {{
    font-family: var(--font);
    font-size: 0.85rem;
    font-weight: 500;
    opacity: 0.5;
    letter-spacing: 0.01em;
  }}

  /* Badge EN VIVO */
  .live-badge {{
    position: absolute;
    top: 10px; right: 10px;
    display: flex; align-items: center; gap: 6px;
    background: rgba(0,0,0,0.65);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 999px;
    padding: 4px 10px 4px 8px;
    font-family: var(--font);
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #fff;
    opacity: 0;
    transition: opacity 0.4s;
    pointer-events: none;
  }}
  .live-badge.on {{ opacity: 1; }}
  .live-dot {{
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #22c55e;
    animation: pdot 1.5s infinite;
  }}
  @keyframes pdot {{
    0%,100% {{ box-shadow: 0 0 0 0 rgba(34,197,94,.65); }}
    50%      {{ box-shadow: 0 0 0 5px rgba(34,197,94,0); }}
  }}

  /* ── Footer con botón ── */
  .card-footer {{
    flex-shrink: 0;
    padding: 12px 14px 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    border-top: 1px solid var(--bdr);
    background: rgba(255,255,255,0.018);
  }}

  #action-btn {{
    width: 100%;
    height: 52px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--a1) 0%, var(--a2) 100%);
    color: #fff;
    font-family: var(--font);
    font-size: 0.97rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s, opacity 0.2s;
    box-shadow: 0 6px 22px rgba(59,107,255,0.42);
    position: relative;
    overflow: hidden;
  }}
  #action-btn::after {{
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.14), transparent 60%);
    pointer-events: none;
  }}
  #action-btn:hover:not(:disabled) {{
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(59,107,255,0.56);
  }}
  #action-btn:active:not(:disabled) {{
    transform: translateY(1px);
    opacity: 0.88;
  }}
  #action-btn:disabled {{
    opacity: 0.42;
    cursor: not-allowed;
    transform: none;
  }}

  .status {{
    text-align: center;
    font-family: var(--font);
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--muted);
    min-height: 1em;
    transition: color 0.3s;
    letter-spacing: 0.01em;
  }}
  .status.ok  {{ color: #4ade80; }}
  .status.err {{ color: #f87171; }}
</style>
</head>
<body>
<div class="page">

  <div class="hdr">
    <h1>Habla con nuestro agente</h1>
    <p>Conversa con nuestro asistente virtual y conoce todo acerca de Julius Fest</p>
  </div>

  <div class="card">
    <div class="viewport">
      <div id="avatar-container">
        <div class="placeholder" id="placeholder">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.1">
            <circle cx="12" cy="8" r="4"/>
            <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
          </svg>
          <span>El avatar aparecerá aquí</span>
        </div>
      </div>
      <div class="live-badge" id="live-badge">
        <div class="live-dot"></div>EN VIVO
      </div>
    </div>

    <div class="card-footer">
      <button id="action-btn" type="button">{btn_label}</button>
      <div class="status" id="status"></div>
    </div>
  </div>

</div>

<script type="module">
  import {{ Room, RoomEvent, Track }}
    from "https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.esm.mjs";

  const livekitUrl   = {livekit_url};
  const livekitToken = {livekit_token};
  const sessionId    = {session_id};
  const sessionToken = {session_token};
  const stopUrl      = {stop_url};
  const sessionDurMs = {session_dur_ms};
  const isRunning    = {is_running_js};
  const btnLabel     = {btn_label_js};

  const actionBtn  = document.getElementById("action-btn");
  const container  = document.getElementById("avatar-container");
  const liveBadge  = document.getElementById("live-badge");
  const statusEl   = document.getElementById("status");
  const previewKey = "liveavatar_last_preview";

  function setStatus(msg, cls = "") {{
    statusEl.textContent = msg;
    statusEl.className   = "status" + (cls ? " " + cls : "");
  }}

  // ── Clic en el botón del iframe → activa el botón oculto de Streamlit ────
  actionBtn.addEventListener("click", () => {{
    actionBtn.disabled = true;
    setStatus("Procesando...");
    try {{
      const parentDoc = window.parent.document;
      const allBtns   = Array.from(parentDoc.querySelectorAll("button"));

      // Buscar por texto exacto
      let target = allBtns.find(b => b.innerText.trim() === btnLabel);

      // Fallback: primer botón en un contenedor stButton
      if (!target) {{
        target = allBtns.find(b => b.closest('[data-testid="stButton"]'));
      }}

      if (target) {{
        target.click();
      }} else {{
        setStatus("No se encontró el botón de Streamlit.", "err");
        actionBtn.disabled = false;
      }}
    }} catch (e) {{
      setStatus("Error: " + e.message, "err");
      actionBtn.disabled = false;
    }}
  }});

  // ── Preview storage ───────────────────────────────────────────────────────
  function storageSet(k, v) {{
    try {{ sessionStorage.setItem(k, v); }} catch {{}}
    try {{ localStorage.setItem(k, v);   }} catch {{}}
  }}
  function storageGet(k) {{
    try {{ const v = sessionStorage.getItem(k); if (v) return v; }} catch {{}}
    try {{ const v = localStorage.getItem(k);   if (v) return v; }} catch {{}}
    return null;
  }}
  function drawPreview(dataUrl) {{
    if (!dataUrl) return false;
    const img = new Image();
    img.src   = dataUrl;
    img.alt   = "Vista previa";
    container.innerHTML = "";
    container.appendChild(img);
    return true;
  }}

  let currentVideo   = null;
  let previewTimer   = null;
  let sessionStopped = false;
  const room         = new Room();

  function captureFrame(saveOnly = false) {{
    const vid = currentVideo || container.querySelector("video");
    if (!vid || vid.videoWidth === 0) return false;
    const c   = document.createElement("canvas");
    c.width   = vid.videoWidth;
    c.height  = vid.videoHeight;
    c.getContext("2d", {{ alpha: false }}).drawImage(vid, 0, 0);
    const url = c.toDataURL("image/jpeg", 0.92);
    storageSet(previewKey, url);
    if (!saveOnly) drawPreview(url);
    return true;
  }}

  function startCapture() {{
    if (previewTimer) return;
    previewTimer = setInterval(() => captureFrame(true), 900);
  }}

  // ── LiveKit ───────────────────────────────────────────────────────────────
  room.on(RoomEvent.TrackSubscribed, (track) => {{
    if (track.kind === Track.Kind.Video) {{
      const vid       = track.attach();
      currentVideo    = vid;
      vid.autoplay    = true;
      vid.playsInline = true;
      container.innerHTML = "";
      container.appendChild(vid);
      liveBadge.classList.add("on");
      setStatus("Avatar conectado — micrófono activo", "ok");
      startCapture();
    }}
    if (track.kind === Track.Kind.Audio) {{
      const a    = track.attach();
      a.autoplay = true;
      document.body.appendChild(a);
    }}
  }});

  async function stopFromJS() {{
    if (sessionStopped || !sessionId || !sessionToken) return;
    sessionStopped = true;
    captureFrame(false);
    liveBadge.classList.remove("on");
    try {{
      await fetch(stopUrl, {{
        method: "POST",
        headers: {{
          Authorization: `Bearer ${{sessionToken}}`,
          "Content-Type": "application/json",
          Accept: "application/json"
        }},
        body: JSON.stringify({{ session_id: sessionId, reason: "USER_DISCONNECTED" }})
      }});
      room.disconnect();
      setStatus("Conversación detenida automáticamente.", "ok");
    }} catch (e) {{
      setStatus("Error al detener: " + e.message, "err");
    }}
  }}

  async function connectAvatar() {{
    if (!isRunning) {{
      const saved = storageGet(previewKey);
      if (!drawPreview(saved)) setStatus("Toca el botón para iniciar la conversación.");
      else setStatus("Vista previa de la última sesión.");
      return;
    }}
    setStatus("Conectando...");
    try {{
      await room.connect(livekitUrl, livekitToken);
      await room.localParticipant.setMicrophoneEnabled(true);
      setStatus("Conversación activa", "ok");
      setTimeout(stopFromJS, sessionDurMs);
    }} catch (e) {{
      const saved = storageGet(previewKey);
      if (!drawPreview(saved)) setStatus("Error: " + e.message, "err");
      else setStatus("Error de conexión. Vista previa conservada.", "err");
    }}
  }}

  connectAvatar();
</script>
</body>
</html>
"""

components.html(html, height=IFRAME_HEIGHT, scrolling=False)
