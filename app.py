import streamlit as st
import paho.mqtt.client as mqtt
import time
import re

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
if "d1_state" not in st.session_state:
    st.session_state.d1_state = "UNKNOWN"
if "d2_state" not in st.session_state:
    st.session_state.d2_state = "UNKNOWN"
if "esp_connected" not in st.session_state:
    st.session_state.esp_connected = False

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
    
    # Parse ESP pin status (e.g., "D1=ON,D2=OFF")
    match = re.match(r"D1=([A-Z]+),D2=([A-Z]+)", new_status)
    if match:
        st.session_state.d1_state = match.group(1)
        st.session_state.d2_state = match.group(2)
        st.session_state.esp_connected = True
    else:
        st.session_state.esp_connected = False
        st.session_state.d1_state = "UNKNOWN"
        st.session_state.d2_state = "UNKNOWN"
    
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

# Function to send command only if ESP connected
def send_command(topic, cmd):
    if st.session_state.client and st.session_state.esp_connected:
        st.session_state.client.publish(topic, cmd)
        msg = f"Sent: {cmd}"
        st.session_state.status = msg
        speak_browser(msg)
    else:
        st.error("ESP not connected yet – wait for status like 'D1=ON,D2=OFF'")

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

st.title("🔌 ESP8266 D1 / D2 Remote Control")
st.caption(f"**Broker**: {BROKER}  |  **MQTT Status**: {st.session_state.status}")

st.markdown("---")

# Current Pin Status Display (Always visible)
st.subheader("📊 Current Pin Status")
col_status1, col_status2 = st.columns(2)

with col_status1:
    d1_color = "green" if st.session_state.d1_state == "ON" else "red" if st.session_state.d1_state == "OFF" else "orange"
    st.metric("D1", st.session_state.d1_state, delta=None, label_visibility="collapsed")

with col_status2:
    d2_color = "green" if st.session_state.d2_state == "ON" else "red" if st.session_state.d2_state == "OFF" else "orange"
    st.metric("D2", st.session_state.d2_state, delta=None, label_visibility="collapsed")

esp_status = "✅ CONNECTED" if st.session_state.esp_connected else "❌ NOT CONNECTED"
st.info(f"**ESP Status**: {esp_status}")

st.markdown("---")

# Control Buttons (Disabled visually if not connected)
st.subheader("Controls (Voice commands only when ESP connected)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    btn_disabled = not st.session_state.esp_connected
    if st.button("D1 ON", use_container_width=True, type="primary", disabled=btn_disabled):
        send_command(TOPIC_D1, "ON")

with col2:
    btn_disabled = not st.session_state.esp_connected
    if st.button("D1 OFF", use_container_width=True, disabled=btn_disabled):
        send_command(TOPIC_D1, "OFF")

with col3:
    btn_disabled = not st.session_state.esp_connected
    if st.button("D2 ON", use_container_width=True, type="primary", disabled=btn_disabled):
        send_command(TOPIC_D2, "ON")

with col4:
    btn_disabled = not st.session_state.esp_connected
    if st.button("D2 OFF", use_container_width=True, disabled=btn_disabled):
        send_command(TOPIC_D2, "OFF")

st.markdown("---")

st.subheader("📝 Latest Raw Status from ESP")
st.code(st.session_state.status)

if st.button("🔊 Test Voice Output"):
    speak_browser("Hello Ravi! Voice test. ESP status is ready.")

st.info("""
✅ **Voice**: Auto-speaks on status changes/button presses **only if ESP connected**.
✅ **Best in Chrome/Edge**. No mic needed.
✅ **ESP Detection**: Waits for 'D1=ON,D2=OFF' format from your ESP code.
""")
