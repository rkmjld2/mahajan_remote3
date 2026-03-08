import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

st.set_page_config(layout="wide")
st.title("🔌 ESP8266 TEST")

# MQTT Setup
BROKER = "broker.hivemq.com"
TOPIC_STATUS_JSON = "ravi2025/home/status_json"

# Simple session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "esp_status" not in st.session_state:
    st.session_state.esp_status = "WAITING..."
if "last_msg" not in st.session_state:
    st.session_state.last_msg = None

# MQTT Client
client = mqtt.Client()
received_count = 0

def on_connect(client, userdata, flags, rc):
    st.session_state.esp_status = f"✅ MQTT Connected (Code: {rc})"
    client.subscribe(TOPIC_STATUS_JSON)
    st.rerun()

def on_message(client, userdata, msg):
    global received_count
    try:
        payload = msg.payload.decode()
        st.session_state.messages.append(payload)
        st.session_state.last_msg = payload
        st.session_state.esp_status = "🟢 ONLINE!"
        received_count += 1
        st.rerun()
    except Exception as e:
        st.session_state.messages.append(f"ERROR: {e}")

client.on_connect = on_connect
client.on_message = on_message

# Connect
if st.button("🔌 CONNECT MQTT"):
    client.connect(BROKER, 1883, 60)
    client.loop_start()
    st.write("Connecting... Wait 5 seconds")

# Show status
col1, col2, col3 = st.columns(3)
col1.metric("ESP Status", st.session_state.esp_status)
col2.metric("Messages Received", len(st.session_state.messages))
col3.metric("Last Message", st.session_state.last_msg[:50] + "..." if st.session_state.last_msg else "None")

st.markdown("---")

# Raw messages
st.subheader("📡 Raw MQTT Messages (from ESP8266)")
for i, msg in enumerate(st.session_state.messages[-10:]):  # Last 10
    st.code(msg, language="json")

# Manual publish test
if st.button("🧪 Test Publish TO ESP"):
    client.publish("ravi2025/home/d0/set", "ON")
    st.success("Sent ON to D0")

# MQTT Loop
client.loop(timeout=0.1)

st.caption("🔥 ESP8266 Serial shows 'Status: RSSI=-70' = MQTT WORKING. Wait 15-30 seconds for first message!")
