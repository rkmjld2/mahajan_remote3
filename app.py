import streamlit as st
import paho.mqtt.client as mqtt
import time
import re

# ────────────────────────────────────────────────
# CONFIG – MQTT public broker
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883

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

def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    new_msg = "Connected to broker – waiting for ESP"
    st.session_state.status = new_msg
    speak_browser(new_msg)

def on_message(client, userdata, msg):
    new_status = msg.payload.decode().strip()
    st.session_state.status = new_status
    
    # ✅ FIXED: Detect your ESP's actual message + pin format
    if "ESP online" in new_status or "ready" in new_status:
        st.session_state.esp_connected = True
        speak_browser("ESP connected and ready!")
    elif re.match(r"D1=([A-Z]+),D2=([A-Z]+)", new_status):
        match = re.match(r"D1=([A-Z]+),D2=([A-Z]+)", new_status)
        st.session_state.d1_state = match.group(1)
        st.session_state.d2_state = match.group(2)
        st.session_state.esp_connected = True
    else:
        # Fallback if only pins change without full status
        match = re.search(r"D1=([A-Z]+)", new_status)
        if match:
            st.session_state.d1_state = match.group(1)
        match = re.search(r"D2=([A-Z]+)", new_status)
        if match:
            st.session_state.d2_state = match.group(1)
        if st.session_state.d1_state != "UNKNOWN" or st.session_state.d2_state != "UNKNOWN":
            st.session_state.esp_connected = True
    
    speak_browser(new_status)
    st.rerun()

# Connect MQTT
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(Broker, PORT, 60)
        client.loop_start()
        st.session_state.client = client
    except Exception as e:
        st.session_state.status = f"Connection failed: {str(e)}"

def send_command(topic, cmd):
    if st.session_state.client and st.session_state.esp_connected:
        st.session_state.client.publish(topic, cmd)
        msg = f"✅ Sent: {cmd}"
        st.session_state.status = msg
        speak_browser(msg)
    else:
        st.warning("⚠️ ESP not detected yet – check status above")

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

# ──────────────────────────────────────────────── UI ────────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Remote + Voice", layout="wide")

st.title("🔌 ESP8266 D1/D2 Remote Control")
st.caption(f"**Broker**: {BROKER}  |  **Status**: {st.session_state.status}")

st.markdown("---")

# Pin Status
st.subheader("📊 Current Pin Status")
col1, col2 = st.columns(2)

with col1:
    color = "green" if st.session_state.d1_state == "ON" else "red" if st.session_state.d1_state == "OFF" else "orange"
    st.metric("D1", st.session_state.d1_state, delta=None)

with col2:
    color = "green" if st.session_state.d2_state == "ON" else "red" if st.session_state.d2_state == "OFF" else "orange"
    st.metric("D2", st.session_state.d2_state, delta=None)

# ESP Connection Indicator
status_emoji = "✅ CONNECTED" if st.session_state.esp_connected else "❌ WAITING..."
st.success(f"**ESP Status**: {status_emoji}") if st.session_state.esp_connected else st.warning(f"**ESP Status**: {status_emoji}")

st.markdown("---")

# Buttons
st.subheader("🎮 Controls (Active when ESP ✅)")
cols = st.columns(4)
with cols[0]:
    st.button("D1 ON", use_container_width=True, type="primary", disabled=not st.session_state.esp_connected, on_click=lambda: send_command(TOPIC_D1, "ON"))
with cols[1]:
    st.button("D1 OFF", use_container_width=True, disabled=not st.session_state.esp_connected, on_click=lambda: send_command(TOPIC_D1, "OFF"))
with cols[2]:
    st.button("D2 ON", use_container_width=True, type="primary", disabled=not st.session_state.esp_connected, on_click=lambda: send_command(TOPIC_D2, "ON"))
with cols[3]:
    st.button("D2 OFF", use_container_width=True, disabled=not st.session_state.esp_connected, on_click=lambda: send_command(TOPIC_D2, "OFF"))

st.markdown("---")

st.subheader("📝 Raw ESP Status")
st.code(st.session_state.status)

if st.button("🔊 Test Voice"):
    speak_browser("ESP control ready! D1 and D2 working.")

st.info("🎯 Now detects your ESP's 'ESP online - ready' message perfectly!")
