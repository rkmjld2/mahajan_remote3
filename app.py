import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT = 1883

# Unique client ID for this Streamlit instance
CLIENT_ID = f"streamlit_ravi_{int(time.time())}"

TOPIC_D1_SET   = "ravi2025/home/d1/set"
TOPIC_D2_SET   = "ravi2025/home/d2/set"
TOPIC_STATUS   = "ravi2025/home/status"      # ONLINE / OFFLINE (retained + LWT)
TOPIC_D1_STATE = "ravi2025/home/d1/state"    # ON / OFF (retained)
TOPIC_D2_STATE = "ravi2025/home/d2/state"    # ON / OFF (retained)

# Session state variables
if "client" not in st.session_state:
    st.session_state.client = None
if "connected" not in st.session_state:
    st.session_state.connected = False
if "device_online" not in st.session_state:
    st.session_state.device_online = False
if "d1_state" not in st.session_state:
    st.session_state.d1_state = "UNKNOWN"
if "d2_state" not in st.session_state:
    st.session_state.d2_state = "UNKNOWN"
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""
if "debug_log" not in st.session_state:
    st.session_state.debug_log = []
if "last_message" not in st.session_state:
    st.session_state.last_message = "No recent messages"

# ────────────────────────────────────────────────
# Helper: Add to debug log
# ────────────────────────────────────────────────
def log_debug(msg):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.debug_log.append(f"[{timestamp}] {msg}")
    if len(st.session_state.debug_log) > 15:
        st.session_state.debug_log.pop(0)

# ────────────────────────────────────────────────
# Browser TTS (voice output)
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
# MQTT callbacks
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.connected = True
        client.subscribe(TOPIC_STATUS, qos=1)
        client.subscribe(TOPIC_D1_STATE, qos=1)
        client.subscribe(TOPIC_D2_STATE, qos=1)
        log_debug("Connected & subscribed (QoS 1)")
        speak("Connected to broker – waiting for ESP")
        st.rerun()
    else:
        st.session_state.connected = False
        log_debug(f"Connect failed - code {rc}")
        speak(f"Connection failed - code {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode(errors='ignore').strip()
    log_debug(f"Received: {topic} → '{payload}' (retain={msg.retain})")

    if topic == TOPIC_STATUS:
        online = payload.upper() == "ONLINE"
        st.session_state.device_online = online
        speak(f"ESP device is now {'ONLINE' if online else 'OFFLINE'}")
    elif topic == TOPIC_D1_STATE:
        st.session_state.d1_state = payload.upper()
    elif topic == TOPIC_D2_STATE:
        st.session_state.d2_state = payload.upper()

    st.session_state.last_message = f"{topic}: {payload}"
    st.rerun()

# ────────────────────────────────────────────────
# MQTT client init / reconnect
# ────────────────────────────────────────────────
def get_or_create_client():
    client = st.session_state.client
    if client is None or not client.is_connected():
        log_debug("Creating new MQTT client")
        client = mqtt.Client(client_id=CLIENT_ID, clean_session=False)  # persistent session
        client.on_connect = on_connect
        client.on_message = on_message
        client.reconnect_delay_set(min_delay=1, max_delay=120)

        try:
            client.connect(BROKER, PORT, keepalive=60)
            client.loop_start()
            st.session_state.client = client
            log_debug("Connect called – waiting for on_connect")
        except Exception as e:
            log_debug(f"Connect error: {str(e)}")
            return None
    return client

# Try to get/init client
client = get_or_create_client()

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 D1/D2 Remote", layout="wide")
st.title("ESP8266 D1 / D2 Remote Control")

# Status line
mqtt_status = "Connected" if st.session_state.connected else "Connecting..."
device_status = "ONLINE" if st.session_state.device_online else "OFFLINE"
st.caption(f"Broker: {BROKER} | MQTT: {mqtt_status} | Device: {device_status}")

st.markdown("---")

# Pin states display
col1, col2 = st.columns(2)
with col1:
    color = "green" if st.session_state.d1_state == "ON" else "red" if st.session_state.d1_state == "OFF" else "gray"
    st.markdown(f"**D1: <span style='color:{color}; font-size:1.6em;'>{st.session_state.d1_state}</span>**", unsafe_allow_html=True)
with col2:
    color = "green" if st.session_state.d2_state == "ON" else "red" if st.session_state.d2_state == "OFF" else "gray"
    st.markdown(f"**D2: <span style='color:{color}; font-size:1.6em;'>{st.session_state.d2_state}</span>**", unsafe_allow_html=True)

st.markdown("---")

# Buttons – disabled if not ready
disabled = not (st.session_state.connected and st.session_state.device_online and client is not None)

col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
with col_btn1:
    if st.button("D1 ON", use_container_width=True, type="primary", disabled=disabled):
        client.publish(TOPIC_D1_SET, "ON", qos=1)
        speak("Sent command: D1 ON")
with col_btn2:
    if st.button("D1 OFF", use_container_width=True, disabled=disabled):
        client.publish(TOPIC_D1_SET, "OFF", qos=1)
        speak("Sent command: D1 OFF")
with col_btn3:
    if st.button("D2 ON", use_container_width=True, type="primary", disabled=disabled):
        client.publish(TOPIC_D2_SET, "ON", qos=1)
        speak("Sent command: D2 ON")
with col_btn4:
    if st.button("D2 OFF", use_container_width=True, disabled=disabled):
        client.publish(TOPIC_D2_SET, "OFF", qos=1)
        speak("Sent command: D2 OFF")

if disabled:
    if not st.session_state.connected:
        st.warning("MQTT not connected yet...")
    elif not st.session_state.device_online:
        st.warning("Waiting for ESP device to come ONLINE (check your ESP code for retained publishes)")

st.markdown("---")
st.subheader("Latest device message")
st.code(st.session_state.last_message)

# Debug section – very useful!
with st.expander("Debug Log (last events + received messages)"):
    for line in st.session_state.debug_log:
        st.text(line)
    if st.button("Clear Debug Log"):
        st.session_state.debug_log = []

st.markdown("---")
if st.button("Test Voice Output"):
    speak("Hello Ravi! This is a voice test. D1 on, D2 off.")

st.info("""
Voice speaks on real status changes or button presses (only when device is ONLINE).
Best in Chrome/Edge.  
You **must** update ESP to publish retained ONLINE + pin states!
""")
