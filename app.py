import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG – MUST MATCH ESP EXACTLY (copy-paste from Serial)
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883

TOPIC_D1     = "ravi2025/home/d1/set"
TOPIC_D2     = "ravi2025/home/d2/set"
TOPIC_STATUS = "ravi2025/home/status"   # Copy this from Serial exactly

# Session state
if "client" not in st.session_state:
    st.session_state.client = None
if "status" not in st.session_state:
    st.session_state.status = "Starting MQTT connection..."
if "pin_d1" not in st.session_state:
    st.session_state.pin_d1 = "UNKNOWN"
if "pin_d2" not in st.session_state:
    st.session_state.pin_d2 = "UNKNOWN"
if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = None

# ────────────────────────────────────────────────
# MQTT callbacks
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    st.session_state.status = f"Connected (rc={rc}) – subscribed to status"
    client.subscribe(TOPIC_STATUS)
    # Request current status immediately
    client.publish(TOPIC_STATUS, "App requesting status")

def on_message(client, userdata, msg):
    new_status = msg.payload.decode().strip()
    st.session_state.last_update_time = time.strftime("%H:%M:%S")
    st.session_state.status = f"Received from ESP: {new_status}"
    
    # Parse pin status
    if "D1 ON" in new_status or "D1:ON" in new_status:
        st.session_state.pin_d1 = "ON"
        speak_browser("D1 is on")
    elif "D1 OFF" in new_status or "D1:OFF" in new_status:
        st.session_state.pin_d1 = "OFF"
        speak_browser("D1 is off")
    
    if "D2 ON" in new_status or "D2:ON" in new_status:
        st.session_state.pin_d2 = "ON"
        speak_browser("D2 is on")
    elif "D2 OFF" in new_status or "D2:OFF" in new_status:
        st.session_state.pin_d2 = "OFF"
        speak_browser("D2 is off")
    
    st.rerun()

# Connect & maintain
if st.session_state.client is None:
    client = mqtt.Client(client_id="streamlit_app_ravi_" + str(int(time.time())))
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
    except Exception as e:
        st.session_state.status = f"Connect error: {str(e)}"
else:
    # Force resubscribe every 10 seconds if connected
    if time.time() % 10 < 1 and client.is_connected():
        client.subscribe(TOPIC_STATUS)

# ────────────────────────────────────────────────
# Browser TTS
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
            st.session_state.status = "Sent D1 ON – waiting for ESP reply"
        else:
            st.error("MQTT client not connected")

with col2:
    if st.button("D1 OFF", use_container_width=True):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D1, "OFF")
            st.session_state.status = "Sent D1 OFF – waiting for ESP reply"
        else:
            st.error("MQTT client not connected")

with col3:
    if st.button("D2 ON", use_container_width=True, type="primary"):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D2, "ON")
            st.session_state.status = "Sent D2 ON – waiting for ESP reply"
        else:
            st.error("MQTT client not connected")

with col4:
    if st.button("D2 OFF", use_container_width=True):
        if st.session_state.client:
            st.session_state.client.publish(TOPIC_D2, "OFF")
            st.session_state.status = "Sent D2 OFF – waiting for ESP reply"
        else:
            st.error("MQTT client not connected")

st.markdown("---")

st.subheader("Current Pin Status from ESP")
if st.session_state.last_update_time:
    st.caption(f"Last update: {st.session_state.last_update_time}")
st.metric("D1", st.session_state.pin_d1)
st.metric("D2", st.session_state.pin_d2)

st.subheader("Voice Test")
if st.button("Test Voice"):
    speak_browser("Test successful! Voice is working.")

st.info("""
Voice & pin status update only when ESP publishes to "{TOPIC_STATUS}"
Check Serial Monitor for "Published D1 ON → SUCCESS" after button press
If pins change but status stays UNKNOWN → topic mismatch or publish failed
""")
