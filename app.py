import streamlit as st
import paho.mqtt.client as mqtt
import time

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT = 1883

TOPIC_D1 = "ravi2025/home/d1/set"
TOPIC_D2 = "ravi2025/home/d2/set"
TOPIC_STATUS = "ravi2025/home/status"

# Session state
if "client" not in st.session_state:
    st.session_state.client = None
if "status" not in st.session_state:
    st.session_state.status = "Waiting for connection..."

def on_connect(client, userdata, flags, rc):
    st.session_state.status = "Connected to MQTT broker"
    client.subscribe(TOPIC_STATUS)

def on_message(client, userdata, msg):
    st.session_state.status = msg.payload.decode()
    st.rerun()

# Connect once
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    st.session_state.client = client

# UI
st.title("ESP8266 Remote Control – MQTT")
st.caption(f"Broker: {BROKER} | Status: {st.session_state.status}")

col1, col2 = st.columns(2)
with col1:
    if st.button("D1 ON"):
        st.session_state.client.publish(TOPIC_D1, "ON")
with col2:
    if st.button("D1 OFF"):
        st.session_state.client.publish(TOPIC_D1, "OFF")

col3, col4 = st.columns(2)
with col3:
    if st.button("D2 ON"):
        st.session_state.client.publish(TOPIC_D2, "ON")
with col4:
    if st.button("D2 OFF"):
        st.session_state.client.publish(TOPIC_D2, "OFF")

st.markdown("---")
st.subheader("Latest status")
st.code(st.session_state.status)