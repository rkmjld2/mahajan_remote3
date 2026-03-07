import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG – MQTT public broker
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883

# Make sure these match EXACTLY with your ESP code (case-sensitive!)
TOPIC_D1     = "ravi2025/home/d1/set"
TOPIC_D2     = "ravi2025/home/d2/set"
TOPIC_STATUS = "ravi2025/home/status"

# Session state
if "client" not in st.session_state:
    st.session_state.client = None
if "status" not in st.session_state:
    st.session_state.status = "Initializing MQTT connection..."
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""

# ────────────────────────────────────────────────
# MQTT callbacks
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    new_msg = "Connected to broker – waiting for ESP"
    st.session_state.status = new_msg
    speak_browser(new_msg)

def on_message(client, userdata, msg):
    new_status = msg.payload.decode().strip()
    st.session_state.status = new_status
    speak_browser(new_status)
    st.rerun()

# Connect once
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
    except Exception as e:
        st.session_state.status = f"Connection failed: {str(e)}"

# ────────────────────────────────────────────────
# Browser TTS – speaks text aloud
# ────────────────────────────────────────────────
def speak_browser(text: str):
    if not text or text == st.session_state.last_spoken:
        return
    st.session_state.last_spoken = text
    safe_text = text.replace('"', '\\"').replace("'", "\\'")
    js = f"""
    <script>
    if ('speechSynthesis' in window) {{
        const utterance = new SpeechSynthesisUtterance("{safe_text}");
        utterance.lang = 'en-US';
        utterance.volume = 1.0;
        utterance.rate = 0.95;
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
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D1, "ON")
            msg = "Sent command: D1 ON"
            st.session_state.status = msg
            speak_browser(msg)
        else:
            st.error("MQTT not connected yet")

with col2:
    if st.button("D1 OFF", use_container_width=True):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D1, "OFF")
            msg = "Sent command: D1 OFF"
            st.session_state.status = msg
            speak_browser(msg)
        else:
            st.error("MQTT not connected yet")

with col3:
    if st.button("D2 ON", use_container_width=True, type="primary"):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D2, "ON")
            msg = "Sent command: D2 ON"
            st.session_state.status = msg
            speak_browser(msg)
        else:
            st.error("MQTT not connected yet")

with col4:
    if st.button("D2 OFF", use_container_width=True):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D2, "OFF")
            msg = "Sent command: D2 OFF"
            st.session_state.status = msg
            speak_browser(msg)
        else:
            st.error("MQTT not connected yet")

st.markdown("---")

st.subheader("Latest status from ESP (spoken aloud when changed)")
st.code(st.session_state.status)

if st.button("Test Voice Output"):
    speak_browser("Hello Ravi! This is a test of voice output. D1 on, D2 off.")

st.info("""
Voice output is automatic when status changes or buttons are pressed.
Works best in Chrome/Edge. Safari may need page interaction first.
No microphone needed — only speaking.
""")
