import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883

TOPIC_D1     = "ravi2025/home/d1/set"
TOPIC_D2     = "ravi2025/home/d2/set"
TOPIC_STATUS = "ravi2025/home/status"

# Session state with button debounce
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
    st.session_state.debug_log = "Debug log:\n"
if "last_button_click" not in st.session_state:
    st.session_state.last_button_click = 0

# Add debug on every rerun
st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] App rerun started\n"

# ────────────────────────────────────────────────
# MQTT callbacks
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    msg = f"Connected (rc={rc})"
    st.session_state.status = msg
    st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] {msg}\n"
    client.subscribe(TOPIC_STATUS)
    st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Subscribed to {TOPIC_STATUS}\n"
    time.sleep(0.5)
    client.publish(TOPIC_STATUS, "REQUEST_STATUS")
    st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Requested ESP status\n"

def on_message(client, userdata, msg):
    received_time = time.strftime("%H:%M:%S")
    new_status = msg.payload.decode().strip()
    st.session_state.debug_log += f"[{received_time}] 📨 {msg.topic}: '{new_status}'\n"
    
    st.session_state.status = f"ESP: {new_status}"
    st.session_state.last_update_time = received_time
    
    # Parse ESP status formats
    status_lower = new_status.lower()
    if any(x in status_lower for x in ["d1:on", "d1 on", "d1=1"]):
        st.session_state.pin_d1 = "🟢 ON"
        speak_browser("D1 turned ON")
    elif any(x in status_lower for x in ["d1:off", "d1 off", "d1=0"]):
        st.session_state.pin_d1 = "🔴 OFF"
        speak_browser("D1 turned OFF")
    
    if any(x in status_lower for x in ["d2:on", "d2 on", "d2=1"]):
        st.session_state.pin_d2 = "🟢 ON"
        speak_browser("D2 turned ON")
    elif any(x in status_lower for x in ["d2:off", "d2 off", "d2=0"]):
        st.session_state.pin_d2 = "🔴 OFF"
        speak_browser("D2 turned OFF")

# Connect MQTT
if st.session_state.client is None:
    client = mqtt.Client(client_id=f"streamlit_ravi_{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
        st.session_state.status = "Connecting..."
        st.session_state.debug_log += f"[{time.strftime('%H:%M:%S')}] Connecting...\n"
    except Exception as e:
        st.session_state.status = f"❌ Connect failed: {str(e)}"
else:
    if st.session_state.client and st.session_state.client.is_connected():
        st.session_state.status = "✅ MQTT Connected"

# ────────────────────────────────────────────────
# Button handler with debounce - FIXED SYNTAX
# ────────────────────────────────────────────────
def send_mqtt_command(topic, payload, voice_msg, button_label, button_type=None):
    now = time.time()
    if now - st.session_state.last_button_click < 2.0:
        st.warning("⏳ Please wait 2 seconds before next command")
        return
    
    if st.button(button_label, use_container_width=True, type=button_type or "secondary"):
        st.session_state.last_button_click = now
        if st.session_state.client and st.session_state.client.is_connected():
            st.session_state.client.publish(topic, payload)
            st.session_state.status = f"Sent {payload} → waiting ESP reply"
            speak_browser(voice_msg)
            st.rerun()
        else:
            st.error("❌ MQTT not connected")

# ────────────────────────────────────────────────
# Browser TTS
# ────────────────────────────────────────────────
def speak_browser(text: str):
    if not text: return
    safe_text = text.replace('"', '\\"').replace("'", "\\'")
    js = f"""
    <script>
    setTimeout(() => {{
        if ('speechSynthesis' in window) {{
            speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance("{safe_text}");
            utterance.lang = 'en-US';
            utterance.rate = 0.9;
            speechSynthesis.speak(utterance);
        }}
    }}, 50);
    </script>
    """
    st.components.v1.html(js, height=0)

# ────────────────────────────────────────────────
# UI LAYOUT
# ────────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Remote + Voice", layout="wide")

st.title("🔌 ESP8266 D1/D2 Remote Control")
st.caption(f"Broker: {BROKER}  |  {st.session_state.status}")

st.markdown("---")

# Control buttons - FIXED: Proper function calls
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    send_mqtt_command(TOPIC_D1, "ON", "D1 ON command sent", "D1 🟢 ON", "primary")

with col2:
    send_mqtt_command(TOPIC_D1, "OFF", "D1 OFF command sent", "D1 🔴 OFF")

with col3:
    send_mqtt_command(TOPIC_D2, "ON", "D2 ON command sent", "D2 🟢 ON", "primary")

with col4:
    send_mqtt_command(TOPIC_D2, "OFF", "D2 OFF command sent", "D2 🔴 OFF")

with col5:
    if st.button("🔄 Poll ESP Status", use_container_width=True):
        if st.session_state.client and st.session_state.client.is_connected():
            st.session_state.client.publish(TOPIC_STATUS, "REQUEST_STATUS")
            st.session_state.status = "📡 Status requested from ESP..."
            speak_browser("Status requested")
        else:
            st.error("❌ MQTT not connected")
        st.rerun()

st.markdown("---")

# Pin Status - Always visible
st.subheader("📊 Current Pin Status from ESP")
if st.session_state.last_update_time:
    st.caption(f"✅ Last update: {st.session_state.last_update_time}")
else:
    st.caption("⏳ Press 🔄 Poll ESP Status for first reading")

col_status1, col_status2 = st.columns(2)
with col_status1:
    st.metric("GPIO D1", st.session_state.pin_d1)
with col_status2:
    st.metric("GPIO D2", st.session_state.pin_d2)

st.markdown("---")

st.subheader("🐛 Debug Log (last 1000 chars)")
st.code(st.session_state.debug_log[-1000:], language="log")

st.subheader("🔊 Voice Test")
if st.button("🎤 Test Voice"):
    speak_browser("ESP8266 control system working perfectly.")

st.info("""
🔧 **Expected ESP Response Format:**
• `ravi2025/home/status` → "D1:ON D2:OFF" or "D1 ON, D2 OFF"
• Check ESP Serial Monitor for publish confirmation
• Press 🔄 Poll ESP Status to test connection
""")
