import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG – MQTT public broker (free, no login)
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883

# Change "ravi2025" to your own unique string for privacy
TOPIC_D1     = "ravi2025/home/d1/set"
TOPIC_D2     = "ravi2025/home/d2/set"
TOPIC_STATUS = "ravi2025/home/status"

# Session state
if "client" not in st.session_state:
    st.session_state.client = None
if "status" not in st.session_state:
    st.session_state.status = "Connecting to MQTT broker..."

# Previous status – used to detect changes and speak only when needed
if "prev_status" not in st.session_state:
    st.session_state.prev_status = ""

# ────────────────────────────────────────────────
# MQTT callbacks
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    st.session_state.status = "Connected – waiting for ESP"

def on_message(client, userdata, msg):
    new_status = msg.payload.decode().strip()
    st.session_state.status = new_status
    # Speak only if status actually changed
    if new_status != st.session_state.prev_status:
        speak_browser(new_status)
        st.session_state.prev_status = new_status
    st.rerun()

# Connect once
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    st.session_state.client = client

# ────────────────────────────────────────────────
# Browser TTS – speaks text aloud in the user's browser
# ────────────────────────────────────────────────
def speak_browser(text: str):
    if not text:
        return
    # Escape quotes and special characters
    safe_text = text.replace('"', '\\"').replace("'", "\\'")
    js = f"""
    <script>
    if ('speechSynthesis' in window) {{
        const utterance = new SpeechSynthesisUtterance("{safe_text}");
        utterance.lang = 'en-US';
        utterance.volume = 1.0;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }}
    </script>
    """
    st.components.v1.html(js, height=0)

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Remote + Voice", layout="wide")

st.title("ESP8266 D1 / D2 Remote Control")
st.caption(f"Broker: {BROKER}  |  Status: {st.session_state.status}")

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("D1 ON", use_container_width=True, type="primary"):
        st.session_state.client.publish(TOPIC_D1, "ON")
        st.session_state.status = "Sent: D1 ON"

with col2:
    if st.button("D1 OFF", use_container_width=True):
        st.session_state.client.publish(TOPIC_D1, "OFF")
        st.session_state.status = "Sent: D1 OFF"

with col3:
    if st.button("D2 ON", use_container_width=True, type="primary"):
        st.session_state.client.publish(TOPIC_D2, "ON")
        st.session_state.status = "Sent: D2 ON"

with col4:
    if st.button("D2 OFF", use_container_width=True):
        st.session_state.client.publish(TOPIC_D2, "OFF")
        st.session_state.status = "Sent: D2 OFF"

st.markdown("---")

st.subheader("Latest status from ESP (spoken aloud when changed)")
st.code(st.session_state.status)

# Optional manual refresh
if st.button("Refresh status"):
    st.rerun()

st.info("""
Voice output is automatic:
• When ESP sends "D1 ON", "D2 OFF", etc., the browser will speak it aloud.
• Works in most browsers (Chrome/Edge best, Safari sometimes needs user interaction first).
• No microphone needed — only output (speaking).
""")
