import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG – MUST MATCH ESP EXACTLY (copy from Serial Monitor)
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883

TOPIC_D1     = "ravi2025/home/d1/set"
TOPIC_D2     = "ravi2025/home/d2/set"
TOPIC_STATUS = "ravi2025/home/status"   # Copy this line from ESP Serial if different

# Session state
if "client" not in st.session_state:
    st.session_state.client = None
if "status" not in st.session_state:
    st.session_state.status = "Starting..."
if "pin_d1" not in st.session_state:
    st.session_state.pin_d1 = "UNKNOWN"
if "pin_d2" not in st.session_state:
    st.session_state.pin_d2 = "UNKNOWN"
if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = None
if "debug_log" not in st.session_state:
    st.session_state.debug_log = ""

# ────────────────────────────────────────────────
# MQTT callbacks with debug
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    st.session_state.status = f"Connected (rc={rc})"
    st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Connected (rc={rc})\n"
    client.subscribe(TOPIC_STATUS)
    st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Subscribed to {TOPIC_STATUS}\n"
    # Request status immediately
    client.publish(TOPIC_STATUS, "App requesting status")
    st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Requested status from ESP\n"

def on_message(client, userdata, msg):
    new_status = msg.payload.decode().strip()
    st.session_state.last_update_time = time.strftime("%H:%M:%S")
    st.session_state.status = f"Received from ESP: {new_status}"
    st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Received on {msg.topic}: {new_status}\n"
    
    # Parse pins and speak
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
        st.session_state.status = "Connecting to broker..."
    except Exception as e:
        st.session_state.status = f"Connect failed: {str(e)}"
        st.session_state.debug_log += f"Connect error: {str(e)}\n"

# Periodic resubscribe (every rerun if needed)
if st.session_state.client is not None and st.session_state.client.is_connected():
    st.session_state.client.subscribe(TOPIC_STATUS)

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
        else:
            st.error("MQTT not connected yet")

with col2:
    if st.button("D1 OFF", use_container_width=True):
        if st.session_state.client and st.session_state.client.is_connected():
            st.session_state.client.publish(TOPIC_D1, "OFF")
            st.session_state.status = "Sent D1 OFF – waiting for ESP reply"
        else:
            st.error("MQTT not connected yet")

with col3:
    if st.button("D2 ON", use_container_width=True, type="primary"):
        if st.session_state.client and st.session_state.client.is_connected():
            st.session_state.client.publish(TOPIC_D2, "ON")
            st.session_state.status = "Sent D2 ON – waiting for ESP reply"
        else:
            st.error("MQTT not connected yet")

with col4:
    if st.button("D2 OFF", use_container_width=True):
        if st.session_state.client and st.session_state.client.is_connected():
            st.session_state.client.publish(TOPIC_D2, "OFF")
            st.session_state.status = "Sent D2 OFF – waiting for ESP reply"
        else:
            st.error("MQTT not connected yet")

st.markdown("---")

st.subheader("Current Pin Status from ESP")
if st.session_state.last_update_time:
    st.caption(f"Last update: {st.session_state.last_update_time}")
st.metric("D1", st.session_state.pin_d1)
st.metric("D2", st.session_state.pin_d2)

st.subheader("Debug Log (last 10 lines)")
st.code(st.session_state.debug_log[-500:] if st.session_state.debug_log else "No debug info yet")

st.subheader("Voice Test")
if st.button("Test Voice"):
    speak_browser("Hello! This is a voice test. D1 on, D2 off.")

st.info("""
• Voice speaks only when ESP replies with status
• If status stays UNKNOWN → ESP publish not reaching app
• Check debug log for connection/subscribe info
""")
