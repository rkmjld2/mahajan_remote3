import streamlit as st
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT   = 1883

TOPIC_D1     = "ravi2025/home/d1/set"
TOPIC_D2     = "ravi2025/home/d2/set"
TOPIC_STATUS = "ravi2025/home/status"

if "client" not in st.session_state:
    st.session_state.client = None
if "status" not in st.session_state:
    st.session_state.status = "Initializing MQTT connection..."
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""
if "pins" not in st.session_state:
    st.session_state.pins = {"D1": "UNKNOWN", "D2": "UNKNOWN"}

def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    st.session_state.status = "Connected to broker – waiting for ESP"

def on_message(client, userdata, msg):
    new_status = msg.payload.decode().strip()
    st.session_state.status = new_status

    # Parse "D1:OFF,D2:ON"
    try:
        parts = new_status.split(",")
        for p in parts:
            if ":" in p:
                k, v = p.split(":")
                st.session_state.pins[k.strip()] = v.strip()
    except Exception as e:
        print("Parse error:", e)

    # Speak only when ESP sends status
    speak_browser(new_status)
    st.rerun()

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

st.set_page_config(page_title="ESP8266 Remote + Voice", layout="wide")
st.title("ESP8266 D1 / D2 Remote Control")
st.caption(f"Broker: {BROKER}  |  Status: {st.session_state.status}")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

def send_command(topic, cmd, label):
    if st.session_state.client:
        st.session_state.client.publish(topic, cmd)
        st.session_state.status = f"Command sent: {label}"
        # Do NOT speak here — wait for ESP confirmation
    else:
        st.error("MQTT not connected yet")

with col1:
    if st.button("D1 ON", use_container_width=True, type="primary"):
        send_command(TOPIC_D1, "ON", "D1 ON")

with col2:
    if st.button("D1 OFF", use_container_width=True):
        send_command(TOPIC_D1, "OFF", "D1 OFF")

with col3:
    if st.button("D2 ON", use_container_width=True, type="primary"):
        send_command(TOPIC_D2, "ON", "D2 ON")

with col4:
    if st.button("D2 OFF", use_container_width=True):
        send_command(TOPIC_D2, "OFF", "D2 OFF")

st.markdown("---")
st.subheader("Current Pin Status (from ESP)")
st.json(st.session_state.pins)

st.subheader("Latest status message")
st.code(st.session_state.status)

if st.button("Test Voice Output"):
    speak_browser("Hello Ravi! This is a test of voice output. D1 on, D2 off.")


