import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG – Copy EXACTLY from Serial Monitor "Subscribed to:"
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
    st.session_state.status = "Starting..."
if "pin_d1" not in st.session_state:
    st.session_state.pin_d1 = "UNKNOWN"
if "pin_d2" not in st.session_state:
    st.session_state.pin_d2 = "UNKNOWN"
if "debug_log" not in st.session_state:
    st.session_state.debug_log = "Debug log:\n"

# Add debug on every rerun
st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] App rerun started\n"

# ────────────────────────────────────────────────
# MQTT callbacks with heavy debug
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    msg = f"Connected (rc={rc})"
    st.session_state.status = msg
    st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] {msg}\n"
    client.subscribe(TOPIC_STATUS)
    st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Subscribed to {TOPIC_STATUS}\n"
    client.publish(TOPIC_STATUS, "App connected - request status")
    st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Requested current status from ESP\n"

def on_message(client, userdata, msg):
    received_time = time.strftime("%H:%M:%S")
    new_status = msg.payload.decode().strip()
    st.session_state.debug_log += f"[{received_time}] Received on {msg.topic}: '{new_status}'\n"
    st.session_state.status = f"Received from ESP: {new_status} ({received_time})"
    
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
    client = mqtt.Client(client_id=f"streamlit_ravi_{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
        st.session_state.status = "Connecting..."
        st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Connecting to broker...\n"
    except Exception as e:
        st.session_state.status = f"Connect failed: {str(e)}"
        st.session_state.debug_log += f"Connect error: {str(e)}\n"
else:
    # Force resubscribe on every rerun if connected
    if st.session_state.client.is_connected():
        st.session_state.client.subscribe(TOPIC_STATUS)
        st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Resubscribed to {TOPIC_STATUS}\n"

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
        if st.session_state.client and st.session_state.client.is_connected():
            st.session_state.client.publish(TOPIC_D1, "ON")
            st.session_state.status = "Sent D1 ON – waiting for ESP reply"
            speak_browser("D1 command sent")
        else:
            st.error("MQTT not connected")

with col2:
    if st.button("D1 OFF", use_container_width=True):
        if st.session_state.client and st.session_state.client.is_connected():
            st.session_state.client.publish(TOPIC_D1, "OFF")
            st.session_state.status = "Sent D1 OFF – waiting for ESP reply"
            speak_browser("D1 command sent")
        else:
            st.error("MQTT not connected")

with col3:
    if st.button("D2 ON", use_container_width=True, type="primary"):
        if st.session_state.client and st.session_state.client.is_connected():
            st.session_state.client.publish(TOPIC_D2, "ON")
            st.session_state.status = "Sent D2 ON – waiting for ESP reply"
            speak_browser("D2 command sent")
        else:
            st.error("MQTT not connected")

with col4:
    if st.button("D2 OFF", use_container_width=True):
        if st.session_state.client and st.session_state.client.is_connected():
            st.session_state.client.publish(TOPIC_D2, "OFF")
            st.session_state.status = "Sent D2 OFF – waiting for ESP reply"
            speak_browser("D2 command sent")
        else:
            st.error("MQTT not connected")

st.markdown("---")

st.subheader("Current Pin Status from ESP")
if st.session_state.last_update_time:
    st.caption(f"Last update: {st.session_state.last_update_time}")
st.metric("D1", st.session_state.pin_d1)
st.metric("D2", st.session_state.pin_d2)

st.subheader("Debug Log (last 500 characters)")
st.code(st.session_state.debug_log[-500:] if st.session_state.debug_log else "No debug info yet")

st.subheader("Voice Test")
if st.button("Test Voice"):
    speak_browser("Hello! Voice test successful. D1 on, D2 off.")

st.info("""
• Voice speaks on command sent + when ESP replies with status
• If status stays UNKNOWN → ESP publish not reaching app
• Check debug log for "Subscribed to..." and "Received on..."
""")
