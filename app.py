import streamlit as st
import paho.mqtt.client as mqtt
import time

# CONFIG - EXACT MATCH YOUR ESP SERIAL OUTPUT
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_D1 = "ravi2025/home/d1/set"
TOPIC_D2 = "ravi2025/home/d2/set"
TOPIC_STATUS = "ravi2025/home/status"

# Initialize session state
for key in ["client", "status", "connected", "d1_state", "d2_state", "messages"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "client" else ""

st.session_state.status = "🚀 Starting MQTT..."

# MQTT Client Setup
client = mqtt.Client()
client.on_connect = lambda c,u,f,rc: (
    st.session_state.status := f"✅ MQTT CONNECTED (rc={rc})",
    c.subscribe(TOPIC_STATUS),
    st.rerun()
)
client.on_message = lambda c,u,msg: (
    st.session_state.messages.append(msg.payload.decode()),
    st.session_state.status := f"📨 GOT: {msg.payload.decode()}",
    st.rerun()
)

# FORCE CONNECT WITH TIMEOUT
if st.session_state.client is None:
    try:
        st.session_state.status = "🔄 Connecting MQTT... (5 sec)"
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        time.sleep(2)  # Give connection time
        st.session_state.client = client
        st.session_state.status = "✅ MQTT Ready - Waiting ESP status"
        st.session_state.messages = []
    except Exception as e:
        st.session_state.status = f"❌ MQTT FAILED: {e}"

def send_command(topic, cmd):
    if st.session_state.client:
        st.session_state.client.publish(topic, cmd)
        st.success(f"✅ SENT {cmd} to {topic}")

# ─── UI ───
st.set_page_config(layout="wide", page_title="ESP8266 Control")
st.title("🔌 ESP8266 D1/D2 Remote")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("D1", st.session_state.d1_state or "WAIT")
with col2:  
    st.metric("D2", st.session_state.d2_state or "WAIT")
with col3:
    st.metric("ESP", "✅" if "ESP online" in st.session_state.status else "❌")

st.caption(f"**Status**: {st.session_state.status}")

st.markdown("---")

# DEBUG SECTION
st.subheader("🔍 MQTT Test Commands")
col1, col2, col3 = st.columns(3)
if col1.button("📤 Test to STATUS topic", use_container_width=True):
    send_command(TOPIC_STATUS, "TEST from Web")
if col2.button("📤 D1 ON", use_container_width=True):
    send_command(TOPIC_D1, "ON")
if col3.button("📤 D2 ON", use_container_width=True): 
    send_command(TOPIC_D2, "ON")

st.markdown("---")

# MAIN CONTROLS
st.subheader("🎮 Pin Controls") 
cols = st.columns(4)
if cols[0].button("D1 ON", use_container_width=True): send_command(TOPIC_D1, "ON")
if cols[1].button("D1 OFF", use_container_width=True): send_command(TOPIC_D1, "OFF")
if cols[2].button("D2 ON", use_container_width=True): send_command(TOPIC_D2, "ON")
if cols[3].button("D2 OFF", use_container_width=True): send_command(TOPIC_D2, "OFF")

# RAW MESSAGES
st.subheader("📋 All MQTT Messages Received")
if st.session_state.messages:
    for msg in st.session_state.messages[-5:]:
        st.code(msg)
else:
    st.info("No messages from ESP yet...")

st.markdown("---")
st.caption("👉 ESP must publish 'ESP online - ready' to ravi2025/home/status")
