import streamlit as st
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT   = 1883

TOPIC_STATUS = "ravi2025/home/status"

pins = ["D0","D1","D2","D3","D4","D5","D6","D7"]

topics = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in pins}

# Session states
if "client" not in st.session_state:
    st.session_state.client = None

if "status" not in st.session_state:
    st.session_state.status = "Initializing MQTT connection..."

# store pin states
for pin in pins:
    if pin not in st.session_state:
        st.session_state[pin] = False

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    st.session_state.status = "Connected to broker"

def on_message(client, userdata, msg):
    st.session_state.status = msg.payload.decode()
    st.rerun()

# Connect MQTT
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    st.session_state.client = client

st.set_page_config(page_title="ESP8266 8 Pin Control", layout="wide")

st.title("ESP8266 Remote Control (Toggle Switches)")

st.write("Status:", st.session_state.status)

st.markdown("---")

cols = st.columns(4)

for i, pin in enumerate(pins):

    with cols[i % 4]:

        state = st.session_state[pin]

        label = f"{pin} : {'ON' if state else 'OFF'}"

        if st.button(label, key=pin, use_container_width=True):

            # Toggle state
            new_state = not st.session_state[pin]
            st.session_state[pin] = new_state

            cmd = "ON" if new_state else "OFF"

            st.session_state.client.publish(topics[pin], cmd)

            st.session_state.status = f"{pin} turned {cmd}"

            st.rerun()

st.markdown("---")

st.subheader("ESP8266 Status")
st.code(st.session_state.status)
