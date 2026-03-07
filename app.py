import streamlit as st
import paho.mqtt.client as mqtt

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC_STATUS = "ravi2025/home/status"

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"]
TOPICS = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in PINS}

# ─────────────────────────────────────────────
# Session state initialization
# ─────────────────────────────────────────────
if "client" not in st.session_state:
    st.session_state.client = None

if "status" not in st.session_state:
    st.session_state.status = "Starting MQTT..."

for pin in PINS:
    if pin not in st.session_state:
        st.session_state[pin] = False   # default OFF

# ─────────────────────────────────────────────
# MQTT callbacks
# ─────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    st.session_state.status = "Connected to MQTT broker"
    st.rerun()

def on_message(client, userdata, msg):
    # You can enhance this part later to parse real pin states if ESP publishes them
    st.session_state.status = msg.payload.decode()
    st.rerun()

# ─────────────────────────────────────────────
# MQTT connection (once)
# ─────────────────────────────────────────────
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
    except Exception as e:
        st.session_state.status = f"MQTT connection failed: {e}"

# ─────────────────────────────────────────────
# Streamlit UI
# ─────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Remote Control", layout="wide")

st.title("ESP8266 8-Pin Remote Control")
st.caption("Status: " + st.session_state.status)
st.markdown("---")

# 4-column layout
cols = st.columns(4)

for i, pin in enumerate(PINS):
    with cols[i % 4]:
        is_on = st.session_state[pin]
        
        # Visual toggle button
        if st.button(
            label = f"{pin}  {'🟢 ON' if is_on else '⚪ OFF'}",
            key   = f"toggle_{pin}",
            type  = "primary" if is_on else "secondary",
            use_container_width = True,
            help  = f"Click to turn {pin} {'OFF' if is_on else 'ON'}"
        ):
            # Toggle logic
            new_state = not is_on
            st.session_state[pin] = new_state
            
            command = "ON" if new_state else "OFF"
            
            if st.session_state.client:
                st.session_state.client.publish(TOPICS[pin], command)
            
            st.session_state.status = f"Sent: {pin} → {command}"
            st.rerun()

st.markdown("---")

st.subheader("Last ESP8266 message")
st.code(st.session_state.status, language=None)
