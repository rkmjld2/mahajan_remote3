import streamlit as st
import paho.mqtt.client as mqtt
import time

BROKER = "broker.hivemq.com"
PORT = 1883

TOPIC_STATUS = "ravi2025/home/status"
TOPIC_HEARTBEAT = "ravi2025/home/heartbeat"

PINS = ["D0","D1","D2","D3","D4","D5","D6","D7"]

TOPICS = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in PINS}

if "client" not in st.session_state:
    st.session_state.client = None

if "status" not in st.session_state:
    st.session_state.status = "Connecting MQTT..."

if "esp_status" not in st.session_state:
    st.session_state.esp_status = "OFFLINE"

if "last_heartbeat" not in st.session_state:
    st.session_state.last_heartbeat = 0

for pin in PINS:
    if pin not in st.session_state:
        st.session_state[pin] = False


def update_pin_states(msg):

    parts = msg.split()

    for part in parts:

        if "=" in part:

            p,v = part.split("=")

            if p in PINS:
                st.session_state[p] = (v=="ON")


def on_message(client, userdata, msg):

    topic = msg.topic
    message = msg.payload.decode()

    if topic == TOPIC_STATUS:
        update_pin_states(message)
        st.session_state.status = message

    if topic == TOPIC_HEARTBEAT:
        st.session_state.last_heartbeat = time.time()
        st.session_state.esp_status = "ONLINE"

    st.rerun()


if st.session_state.client is None:

    client = mqtt.Client()

    client.on_message = on_message

    client.connect(BROKER,PORT,60)

    client.subscribe(TOPIC_STATUS)
    client.subscribe(TOPIC_HEARTBEAT)

    client.loop_start()

    st.session_state.client = client


if time.time() - st.session_state.last_heartbeat > 10:
    st.session_state.esp_status = "OFFLINE"


st.set_page_config(page_title="ESP8266 Remote Control",layout="wide")

st.title("ESP8266 8-Pin Remote Control")

st.write("ESP8266 Status:",st.session_state.esp_status)

st.markdown("---")

cols = st.columns(4)

for i,pin in enumerate(PINS):

    with cols[i%4]:

        state = st.session_state[pin]

        label = f"{pin} : {'ON' if state else 'OFF'}"

        if st.button(label,key=f"btn_{pin}",use_container_width=True):

            new_state = not state

            st.session_state[pin] = new_state

            cmd = "ON" if new_state else "OFF"

            if st.session_state.client:
                st.session_state.client.publish(TOPICS[pin],cmd)

            st.rerun()

st.markdown("---")

st.code(st.session_state.status)
