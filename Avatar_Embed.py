import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="LiveAvatar Embed",
    layout="centered"
)

st.title("LiveAvatar")

iframe_html = """
<div style="width:100%; max-width:420px; margin:0 auto;">
  <iframe
    src="https://embed.liveavatar.com/v1/821a21ad-b848-470e-9749-0e8ff0c00c87?orientation=vertical"
    allow="microphone"
    title="LiveAvatar Embed"
    style="
      width:100%;
      aspect-ratio:9/16;
      border:0;
      border-radius:16px;
      overflow:hidden;
    ">
  </iframe>
</div>
"""

components.html(iframe_html, height=760)
