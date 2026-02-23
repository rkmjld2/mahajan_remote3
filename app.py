import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT = 1883

CLIENT_ID = "streamlit_ui_ravi"  # unique for this app

TOPIC_D1_SET    = "ravi2025/home/d1/set"
TOPIC_D2_SET    = "ravi2025/home/d2/set"
TOPIC_STATUS    = "ravi2025/home/status"       # online / offline (LWT + retained)
TOPIC_D1_STATE  = "ravi2025/home/d1/state"     # ON / OFF (retained)
TOPIC_D2_STATE  = "ravi2025/home/d2/state"     # ON / OFF (retained)

# Session state
if "client" not in st.session_state:
    st.session_state.client = None
if "connected_to_broker" not in st.session_state:
    st.session_state.connected_to_broker = False
if "device_online" not in st.session_state:
    st.session_state.device_online = False
if "d1_state" not in st.session_state:
    st.session_state.d1_state = "UNKNOWN"
if "d2_state" not in st.session_state:
    st.session_state.d2_state = "UNKNOWN"
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""

# ────────────────────────────────────────────────
# MQTT callbacks
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.connected_to_broker = True
        client.subscribe(TOPIC_STATUS)
        client.subscribe(TOPIC_D1_STATE)
        client.subscribe(TOPIC_D2_STATE)
        speak("Connected to broker – waiting for ESP device")
    else:
        st.session_state.connected_to_broker = False
        speak(f"Connection failed – code {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode().strip()

    if topic == TOPIC_STATUS:
        st.session_state.device_online = (payload.lower() == "online")
        if st.session_state.device_online:
            speak("ESP device is now ONLINE")
        else:
            speak("ESP device is OFFLINE")
    elif topic == TOPIC_D1_STATE:
        st.session_state.d1_state = payload.upper()
    elif topic == TOPIC_D2_STATE:
        st.session_state.d2_state = payload.upper()

    st.rerun()  # refresh UI

# Connect / reconnect logic
def get_mqtt_client():
    if st.session_state.client is None or not st.session_state.client.is_connected():
        client = mqtt.Client(client_id=CLIENT_ID, clean_session=True)
        client.on_connect = on_connect
        client.on_message = on_message

        # Optional: keepalive + reconnect delay
        client.reconnect_delay_set(min_delay=1, max_delay=120)

        try:
            client.connect(BROKER, PORT, keepalive=60)
            client.loop_start()
            st.session_state.client = client
        except Exception as e:
            st.session_state.status_message = f"Connect failed: {e}"
            return None
    return st.session_state.client

# ────────────────────────────────────────────────
# Browser TTS
# ────────────────────────────────────────────────
def speak(text: str):
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
st.set_page_config(page_title="ESP8266 D1/D2 Remote", layout="wide")
st.title("ESP8266 D1 / D2 Remote Control")

client = get_mqtt_client()

status_text = "Connected" if st.session_state.connected_to_broker else "Connecting..."
device_text = "ONLINE" if st.session_state.device_online else "OFFLINE"
st.caption(f"Broker: {BROKER} | MQTT: {status_text} | Device: {device_text}")

st.markdown("---")

# Show current pin states (big & clear)
col_status1, col_status2 = st.columns(2)
with col_status1:
    color = "green" if st.session_state.d1_state == "ON" else "red" if st.session_state.d1_state == "OFF" else "gray"
    st.markdown(f"**D1: <span style='color:{color};font-size:1.4em;'>{st.session_state.d1_state}</span>**", unsafe_allow_html=True)
with col_status2:
    color = "green" if st.session_state.d2_state == "ON" else "red" if st.session_state.d2_state == "OFF" else "gray"
    st.markdown(f"**D2: <span style='color:{color};font-size:1.4em;'>{st.session_state.d2_state}</span>**", unsafe_allow_html=True)

st.markdown("---")

# Control buttons – disabled when device offline
disabled = not (st.session_state.connected_to_broker and st.session_state.device_online)

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("D1 ON", use_container_width=True, type="primary", disabled=disabled):
        if client:
            client.publish(TOPIC_D1_SET, "ON")
            speak("Sent command: D1 ON")
with col2:
    if st.button("D1 OFF", use_container_width=True, disabled=disabled):
        if client:
            client.publish(TOPIC_D1_SET, "OFF")
            speak("Sent command: D1 OFF")
with col3:
    if st.button("D2 ON", use_container_width=True, type="primary", disabled=disabled):
        if client:
            client.publish(TOPIC_D2_SET, "ON")
            speak("Sent command: D2 ON")
with col4:
    if st.button("D2 OFF", use_container_width=True, disabled=disabled):
        if client:
            client.publish(TOPIC_D2_SET, "OFF")
            speak("Sent command: D2 OFF")

if disabled and st.session_state.connected_to_broker:
    st.warning("Buttons disabled – waiting for ESP device to come ONLINE")

st.markdown("---")
st.subheader("Latest device message")
st.code(st.session_state.get("status_message", "No recent messages"))

if st.button("Test Voice Output"):
    speak("Hello Ravi! Voice test – D1 on, D2 off.")

st.info("""
Voice speaks automatically on real status changes or successful commands.
Works best in Chrome/Edge. No microphone needed.
You must update ESP code to support LWT + retained state topics.
""")
