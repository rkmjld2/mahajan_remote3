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
if "pin_d1" not in st.session_state:
    st.session_state.pin_d1 = "UNKNOWN"
if "pin_d2" not in st.session_state:
    st.session_state.pin_d2 = "UNKNOWN"

# ────────────────────────────────────────────────
# MQTT callbacks
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    st.session_state.status = "Connected to broker – waiting for ESP"

def on_message(client, userdata, msg):
    new_status = msg.payload.decode().strip()
    st.session_state.status = f"ESP reports: {new_status}"
    # Parse pin status and speak
    if "D1 ON" in new_status:
        st.session_state.pin_d1 = "ON"
        speak_browser("D1 is on")
    elif "D1 OFF" in new_status:
        st.session_state.pin_d1 = "OFF"
        speak_browser("D1 is off")
    if "D2 ON" in new_status:
        st.session_state.pin_d2 = "ON"
        speak_browser("D2 is on")
    elif "D2 OFF" in new_status:
        st.session_state.pin_d2 = "OFF"
        speak_browser("D2 is off")
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
# Browser TTS – speaks pin status
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

with col2:
    if st.button("D1 OFF", use_container_width=True):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D1, "OFF")
            st.session_state.status = "Command sent: D1 OFF → waiting for ESP reply"

with col3:
    if st.button("D2 ON", use_container_width=True, type="primary"):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D2, "ON")
            st.session_state.status = "Command sent: D2 ON → waiting for ESP reply"

with col4:
    if st.button("D2 OFF", use_container_width=True):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D2, "OFF")
            st.session_state.status = "Command sent: D2 OFF → waiting for ESP reply"

st.markdown("---")

st.subheader("Current Pin Status (from ESP)")
st.write(f"D1: {st.session_state.pin_d1}")
st.write(f"D2: {st.session_state.pin_d2}")

st.subheader("Voice Output Test")
if st.button("Test Voice"):
    speak_browser("Hello! This is a test of voice output. D1 on, D2 off.")

st.info("""
• Voice speaks only when ESP replies with pin status (e.g. "D1 is on", "D2 is off").
• If ESP is off → no voice and status remains "UNKNOWN" (command sent but no reply).
• Pin status shows current ON/OFF from ESP (updated only on reply).
""")
