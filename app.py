import streamlit as st
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT   = 1883

TOPIC_STATUS = "ravi2025/home/status"

pins = ["D0","D1","D2","D3","D4","D5","D6","D7"]

# create topic dictionary
topics = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in pins}

if "client" not in st.session_state:
    st.session_state.client = None
if "status" not in st.session_state:
    st.session_state.status = "Initializing MQTT connection..."

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    st.session_state.status = "Connected to broker"

def on_message(client, userdata, msg):
    st.session_state.status = msg.payload.decode()
    st.rerun()

# connect once
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    st.session_state.client = client

st.set_page_config(page_title="ESP8266 8 Relay Control", layout="wide")

st.title("ESP8266 Remote Control (8 Pins)")

st.write("Status:", st.session_state.status)

st.markdown("---")

cols = st.columns(4)

for i, pin in enumerate(pins):

    with cols[i % 4]:

        if st.button(f"{pin} ON", key=f"{pin}_on", use_container_width=True):
            st.session_state.client.publish(topics[pin], "ON")
            st.session_state.status=f"{pin} ON command sent"

        if st.button(f"{pin} OFF", key=f"{pin}_off", use_container_width=True):
            st.session_state.client.publish(topics[pin], "OFF")
            st.session_state.status=f"{pin} OFF command sent"

st.markdown("---")

st.subheader("ESP8266 Status")
st.code(st.session_state.status)
