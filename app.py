import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883

# Change this prefix to something unique
TOPIC_D1     = "ravi2025/home/d1/set"
TOPIC_D2     = "ravi2025/home/d2/set"
TOPIC_STATUS = "ravi2025/home/status"

# Session state
if "client" not in st.session_state:
    st.session_state.client = None
if "status" not in st.session_state:
    st.session_state.status = "Waiting for connection to broker..."
if "last_real_status" not in st.session_state:
    st.session_state.last_real_status = "No status received yet"

# ────────────────────────────────────────────────
# MQTT callbacks
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    st.session_state.status = "Connected to broker – waiting for ESP"

def on_message(client, userdata, msg):
    new_status = msg.payload.decode().strip()
    # Only update and speak real status from ESP
    st.session_state.last_real_status = new_status
    st.session_state.status = f"ESP reports: {new_status}"
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
# Browser TTS – speaks only real status changes
# ────────────────────────────────────────────────
def speak_browser(text: str):
    if not text:
        return
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
st.caption(f"Broker: {BROKER}  |  {st.session_state.status}")

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("D1 ON", use_container_width=True, type="primary"):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D1, "ON")
            st.session_state.status = "Command sent: D1 ON → waiting for ESP reply"
        else:
            st.error("MQTT client not connected")

with col2:
    if st.button("D1 OFF", use_container_width=True):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D1, "OFF")
            st.session_state.status = "Command sent: D1 OFF → waiting for ESP reply"
        else:
            st.error("MQTT client not connected")

with col3:
    if st.button("D2 ON", use_container_width=True, type="primary"):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D2, "ON")
            st.session_state.status = "Command sent: D2 ON → waiting for ESP reply"
        else:
            st.error("MQTT client not connected")

with col4:
    if st.button("D2 OFF", use_container_width=True):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D2, "OFF")
            st.session_state.status = "Command sent: D2 OFF → waiting for ESP reply"
        else:
            st.error("MQTT client not connected")

st.markdown("---")

st.subheader("Real status from ESP (updated & spoken only when received)")
st.code(st.session_state.last_real_status if st.session_state.last_real_status else "No status received yet")

st.info("""
• Voice speaks **only** when ESP actually replies
• If ESP is off → buttons send command but no voice/status update occurs
• Press buttons → wait 2–5 seconds → if ESP is on, you will hear the real status
""")

if st.button("Test Voice (browser check)"):
    speak_browser("Hello! This is a test of voice output.")
