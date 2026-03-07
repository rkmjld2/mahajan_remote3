import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883

BASE_TOPIC = "ravi2025/home/"
TOPIC_STATUS = "ravi2025/home/status"

PINS = ["D0","D1","D2","D3","D4","D5","D6","D7","D8"]

# Session state
if "client" not in st.session_state:
    st.session_state.client = None
if "status" not in st.session_state:
    st.session_state.status = "Starting..."
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = ""

# ────────────────────────────────────────────────
# MQTT callbacks
# ────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    msg = "MQTT connected → waiting for ESP"
    st.session_state.status = msg
    speak(msg)

def on_message(client, userdata, msg):
    if msg.topic == TOPIC_STATUS:
        st.session_state.status = msg.payload.decode().strip()
        speak(st.session_state.status)
        st.rerun()

def speak(text: str):
    if not text or text == st.session_state.last_spoken:
        return
    st.session_state.last_spoken = text
    safe = text.replace('"', '\\"').replace("'", "\\'")
    js = f"""
    <script>
    if ('speechSynthesis' in window) {{
        let u = new SpeechSynthesisUtterance("{safe}");
        u.lang = 'en-US'; u.volume=0.95; u.rate=0.92; u.pitch=1.0;
        window.speechSynthesis.speak(u);
    }}
    </script>
    """
    st.components.v1.html(js, height=0)

# Connect
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
    except Exception as e:
        st.session_state.status = f"Connect failed: {e}"

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 All Pins Remote", layout="wide")
st.title("ESP8266 – Control All Pins (D0–D8)")
st.caption(f"Broker: {BROKER}  •  Status: {st.session_state.status}")
st.markdown("---")

# Create 3 columns with 3 buttons each (D0–D8)
cols = st.columns(3)
for i, pin in enumerate(PINS):
    col = cols[i % 3]
    with col:
        st.subheader(pin)
        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("ON", key=f"{pin}_on", use_container_width=True, type="primary"):
                if st.session_state.client:
                    st.session_state.client.publish(f"{BASE_TOPIC}{pin}/set", "ON")
                    speak(f"Sent {pin} ON")
                else:
                    st.error("No MQTT connection")
        with btn2:
            if st.button("OFF", key=f"{pin}_off", use_container_width=True):
                if st.session_state.client:
                    st.session_state.client.publish(f"{BASE_TOPIC}{pin}/set", "OFF")
                    speak(f"Sent {pin} OFF")
                else:
                    st.error("No MQTT connection")

st.markdown("---")
st.subheader("Latest ESP Status (spoken when changed)")
st.code(st.session_state.status, language="text")

if st.button("Test Voice"):
    speak("Hello Ravi! All pins control test – D5 on, D8 off.")

st.info("""
Active-low relays assumed (ON = LOW).  
Change digitalWrite in firmware to HIGH if your relays are active-high.  
D3,D4,D8,D0 have boot restrictions – test carefully.
""")
