import streamlit as st
import paho.mqtt.client as mqtt

# MQTT Broker
BROKER = "broker.hivemq.com"
PORT = 1883

TOPIC_STATUS = "ravi2025/home/status"

# ESP8266 pins
PINS = ["D0","D1","D2","D3","D4","D5","D6","D7"]

# MQTT topics
TOPICS = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in PINS}

# ─────────────────────────────────────────────
# Session variables
# ─────────────────────────────────────────────
if "client" not in st.session_state:
    st.session_state.client = None

if "status" not in st.session_state:
    st.session_state.status = "Starting MQTT..."

# store pin states
for pin in PINS:
    if pin not in st.session_state:
        st.session_state[pin] = False


# ─────────────────────────────────────────────
# MQTT callbacks
# ─────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    st.session_state.status = "Connected to MQTT broker"


def on_message(client, userdata, msg):
    st.session_state.status = msg.payload.decode()
    st.rerun()


# ─────────────────────────────────────────────
# Connect MQTT once
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
        st.session_state.status = f"MQTT Error: {e}"


# ─────────────────────────────────────────────
# Streamlit UI
# ─────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Remote Control", layout="wide")

st.title("ESP8266 8-Pin Remote Control")

st.write("Status:", st.session_state.status)

st.markdown("---")

# Create 4 columns
cols = st.columns(4)

# Buttons
for i, pin in enumerate(PINS):

    with cols[i % 4]:

        state = st.session_state[pin]

        label = f"{pin} : {'ON' if state else 'OFF'}"

        if st.button(label, key=f"btn_{pin}", use_container_width=True):

            # toggle state
            new_state = not state
            st.session_state[pin] = new_state

            command = "ON" if new_state else "OFF"

            if st.session_state.client:
                st.session_state.client.publish(TOPICS[pin], command)

            st.session_state.status = f"{pin} turned {command}"

            st.rerun()

st.markdown("---")

st.subheader("ESP8266 Status")
st.code(st.session_state.status)
