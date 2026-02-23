import streamlit as st
import paho.mqtt.client as mqtt
import time

# ===============================================
# CONFIGURATION
# ===============================================
BROKER = "broker.hivemq.com"
PORT = 1883

# Unique client ID (changes on each run to avoid conflicts)
CLIENT_ID = f"streamlit_ravi_{int(time.time())}"

TOPIC_D1_SET   = "ravi2025/home/d1/set"
TOPIC_D2_SET   = "ravi2025/home/d2/set"
TOPIC_STATUS   = "ravi2025/home/status"       # expects "ONLINE" or "OFFLINE" (retained)
TOPIC_D1_STATE = "ravi2025/home/d1/state"     # expects "ON" or "OFF" (retained)
TOPIC_D2_STATE = "ravi2025/home/d2/state"     # expects "ON" or "OFF" (retained)

# Session state initialization
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
    st.session_state.last_message = "No messages received yet"

def log_debug(msg):
    ts = time.strftime("%H:%M:%S")
    st.session_state.debug_log.append(f"[{ts}] {msg}")
    if len(st.session_state.debug_log) > 20:
        st.session_state.debug_log.pop(0)

def speak(text):
    if not text or text == st.session_state.last_spoken:
        return
    st.session_state.last_spoken = text
    safe_text = text.replace('"', '\\"').replace("'", "\\'")
    js_code = f"""
    <script>
    if (window.speechSynthesis) {{
        let utterance = new SpeechSynthesisUtterance("{safe_text}");
        utterance.lang = 'en-US';
        utterance.volume = 1.0;
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }}
    </script>
    """
    st.components.v1.html(js_code, height=0)

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.connected = True
        client.subscribe(TOPIC_STATUS, qos=1)
        client.subscribe(TOPIC_D1_STATE, qos=1)
        client.subscribe(TOPIC_D2_STATE, qos=1)
        log_debug("MQTT connected → subscribed to topics")
        speak("Connected to broker")
        st.rerun()
    else:
        log_debug(f"Connection failed - return code {rc}")
        speak(f"Connection failed code {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode(errors='ignore').strip()
    log_debug(f"Received → {topic}: '{payload}' (retained={msg.retain})")

    changed = False
    if topic == TOPIC_STATUS:
        was_online = st.session_state.device_online
        st.session_state.device_online = (payload.upper() == "ONLINE")
        if st.session_state.device_online != was_online:
            speak(f"Device is now {'ONLINE' if st.session_state.device_online else 'OFFLINE'}")
        changed = True
    elif topic == TOPIC_D1_STATE:
        st.session_state.d1_state = payload.upper()
        changed = True
    elif topic == TOPIC_D2_STATE:
        st.session_state.d2_state = payload.upper()
        changed = True

    st.session_state.last_message = f"{topic}: {payload}"
    if changed:
        st.rerun()

# MQTT client management
def get_client():
    if st.session_state.client and st.session_state.client.is_connected():
        return st.session_state.client

    log_debug("Creating / reconnecting MQTT client")
    client = mqtt.Client(client_id=CLIENT_ID, clean_session=False)
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=120)

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()
        st.session_state.client = client
        log_debug("Connect command sent")
    except Exception as e:
        log_debug(f"Connect error: {str(e)}")
        return None

    return client

client = get_client()

# ===============================================
# USER INTERFACE
# ===============================================
st.set_page_config(page_title="ESP8266 Remote Control", layout="wide")
st.title("ESP8266 D1 / D2 Remote Control")

mqtt_text = "Connected" if st.session_state.connected else "Connecting..."
device_text = "ONLINE" if st.session_state.device_online else "OFFLINE"
st.caption(f"Broker: {BROKER} | MQTT: {mqtt_text} | Device: {device_text}")

st.markdown("---")

# Show pin states
col_left, col_right = st.columns(2)
with col_left:
    color = "green" if st.session_state.d1_state == "ON" else "red" if st.session_state.d1_state == "OFF" else "gray"
    st.markdown(f"**D1: <span style='color:{color}; font-size: 1.8em;'>{st.session_state.d1_state}</span>**", unsafe_allow_html=True)

with col_right:
    color = "green" if st.session_state.d2_state == "ON" else "red" if st.session_state.d2_state == "OFF" else "gray"
    st.markdown(f"**D2: <span style='color:{color}; font-size: 1.8em;'>{st.session_state.d2_state}</span>**", unsafe_allow_html=True)

st.markdown("---")

# Buttons - disabled until device is online
disabled = not (st.session_state.connected and st.session_state.device_online and client is not None)

cols = st.columns(4)
with cols[0]:
    if st.button("D1 ON", type="primary", use_container_width=True, disabled=disabled):
        client.publish(TOPIC_D1_SET, "ON", qos=1)
        speak("Command sent: D1 ON")
with cols[1]:
    if st.button("D1 OFF", use_container_width=True, disabled=disabled):
        client.publish(TOPIC_D1_SET, "OFF", qos=1)
        speak("Command sent: D1 OFF")
with cols[2]:
    if st.button("D2 ON", type="primary", use_container_width=True, disabled=disabled):
        client.publish(TOPIC_D2_SET, "ON", qos=1)
        speak("Command sent: D2 ON")
with cols[3]:
    if st.button("D2 OFF", use_container_width=True, disabled=disabled):
        client.publish(TOPIC_D2_SET, "OFF", qos=1)
        speak("Command sent: D2 OFF")

if disabled:
    if not st.session_state.connected:
        st.warning("MQTT connection is still establishing...")
    else:
        st.warning("Waiting for ESP to send ONLINE status and pin states (check ESP code)")

st.markdown("---")
st.subheader("Latest received message")
st.code(st.session_state.last_message)

with st.expander("Debug Log – very important for troubleshooting"):
    for entry in st.session_state.debug_log:
        st.text(entry)
    if st.button("Clear debug log"):
        st.session_state.debug_log = []

st.markdown("---")
if st.button("Test Voice Output"):
    speak("Hello Ravi. This is a test. D1 on, D2 off.")

st.info("""
Important:
• The ESP **must** publish retained messages to:
  - ravi2025/home/status → "ONLINE"
  - ravi2025/home/d1/state → "ON" or "OFF"
  - ravi2025/home/d2/state → "ON" or "OFF"
• After updating ESP code → refresh this page
• Look at Debug Log – you should see "Received" lines with retain=True
""")
