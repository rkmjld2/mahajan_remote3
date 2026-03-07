import streamlit as st
import paho.mqtt.client as mqtt
import time

BROKER = "broker.hivemq.com"
PORT = 1883

TOPIC_STATUS = "ravi2025/home/status"

PINS = ["D0","D1","D2","D3","D4","D5","D6","D7"]

TOPICS = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in PINS}

# ─────────────────────────────
# Session state initialization
# ─────────────────────────────
if "client" not in st.session_state:
    st.session_state.client = None

if "status" not in st.session_state:
    st.session_state.status = "Connecting to MQTT..."

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

for pin in PINS:
    if pin not in st.session_state:
        st.session_state[pin] = False


# ─────────────────────────────
# Parse ESP status message
# ─────────────────────────────
def update_pin_states(msg):

    parts = msg.split()

    for part in parts:
        if "=" in part:

            p, v = part.split("=")

            if p in PINS:
                st.session_state[p] = (v == "ON")


# ─────────────────────────────
# MQTT callbacks
# ─────────────────────────────
def on_connect(client, userdata, flags, rc):

    if rc == 0:
        st.session_state.status = "Connected to MQTT broker"
        client.subscribe(TOPIC_STATUS)
    else:
        st.session_state.status = "MQTT connection failed"


def on_message(client, userdata, msg):

    message = msg.payload.decode()

    st.session_state.status = message

    update_pin_states(message)

    st.rerun()


# ─────────────────────────────
# Connect MQTT once
# ─────────────────────────────
if st.session_state.client is None:

    try:

        client = mqtt.Client()

        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(BROKER, PORT, 60)

        client.loop_start()

        st.session_state.client = client

    except Exception as e:

        st.session_state.status = f"MQTT Error: {e}"


# ─────────────────────────────
# Streamlit UI
# ─────────────────────────────
st.set_page_config(page_title="ESP8266 Remote Control", layout="wide")

st.title("ESP8266 8-Pin Remote Control")

st.write("Status:", st.session_state.status)

st.markdown("---")

cols = st.columns(4)

for i, pin in enumerate(PINS):

    with cols[i % 4]:

        state = st.session_state[pin]

        label = f"{pin} : {'ON' if state else 'OFF'}"

        if st.button(label, key=f"btn_{pin}", use_container_width=True):

            new_state = not state
            st.session_state[pin] = new_state

            cmd = "ON" if new_state else "OFF"

            if st.session_state.client:
                st.session_state.client.publish(TOPICS[pin], cmd)

            st.session_state.status = f"{pin} turned {cmd}"

            st.rerun()

st.markdown("---")

st.subheader("ESP8266 Status Message")

st.code(st.session_state.status)


# ─────────────────────────────
# Auto refresh every 2 seconds
# ─────────────────────────────
if time.time() - st.session_state.last_refresh > 2:
    st.session_state.last_refresh = time.time()
    st.rerun()
