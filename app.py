import streamlit as st
import paho.mqtt.client as mqtt
import time

# CONFIG
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_D1 = "ravi2025/home/d1/set"
TOPIC_D2 = "ravi2025/home/d2/set"
TOPIC_STATUS = "ravi2025/home/status"

# Initialize session state
if "client" not in st.session_state: st.session_state.client = None
if "status" not in st.session_state: st.session_state.status = "🚀 Starting..."
if "connected" not in st.session_state: st.session_state.connected = False
if "d1_state" not in st.session_state: st.session_state.d1_state = "WAIT"
if "d2_state" not in st.session_state: st.session_state.d2_state = "WAIT"
if "messages" not in st.session_state: st.session_state.messages = []

def on_connect(client, userdata, flags, rc):
    st.session_state.status = f"✅ MQTT CONNECTED (rc={rc})"
    client.subscribe(TOPIC_STATUS)
    st.rerun()

def on_message(client, userdata, msg):
    msg_text = msg.payload.decode()
    st.session_state.messages.append(msg_text)
    st.session_state.status = f"📨 ESP SAYS: {msg_text}"
    st.session_state.connected = True
    
    # Parse D1/D2 states
    if "D1=ON" in msg_text: st.session_state.d1_state = "ON"
    elif "D1=OFF" in msg_text: st.session_state.d1_state = "OFF"
    if "D2=ON" in msg_text: st.session_state.d2_state = "ON" 
    elif "D2=OFF" in msg_text: st.session_state.d2_state = "OFF"
    
    st.rerun()

def send_command(topic, cmd):
    if st.session_state.client:
        st.session_state.client.publish(topic, cmd)
        st.success(f"✅ SENT {cmd} → {topic}")
        st.rerun()

# MQTT Setup - FIXED
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        st.session_state.status = "🔄 Connecting MQTT... please wait"
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        time.sleep(3)  # Critical: Let connection complete
        st.session_state.client = client
        st.session_state.status = "✅ MQTT READY - waiting for ESP..."
    except Exception as e:
        st.session_state.status = f"❌ MQTT ERROR: {e}"

# ─── UI ───
st.set_page_config(layout="wide")
st.title("🔌 ESP8266 D1/D2 Control Panel")

# Status Metrics
col1, col2, col3 = st.columns(3)
with col1: st.metric("D1", st.session_state.d1_state)
with col2: st.metric("D2", st.session_state.d2_state) 
with col3: st.metric("ESP", "✅" if st.session_state.connected else "❌")

st.caption(f"**MQTT**: {st.session_state.status}")

st.markdown("---")

# TEST BUTTONS
st.subheader("🔍 Test MQTT Communication")
col1, col2, col3 = st.columns(3)
if col1.button("📤 Send TEST to ESP", use_container_width=True):
    send_command(TOPIC_STATUS, "TEST from Web")
if col2.button("📤 D1 ON", use_container_width=True):
    send_command(TOPIC_D1, "ON")
if col3.button("📤 D2 ON", use_container_width=True):
    send_command(TOPIC_D2, "ON")

st.markdown("---")

# MAIN CONTROLS  
st.subheader("🎮 Pin Controls")
cols = st.columns(4)
if cols[0].button("D1 ON"): send_command(TOPIC_D1, "ON")
if cols[1].button("D1 OFF"): send_command(TOPIC_D1, "OFF")
if cols[2].button("D2 ON"): send_command(TOPIC_D2, "ON")
if cols[3].button("D2 OFF"): send_command(TOPIC_D2, "OFF")

st.markdown("---")

# DEBUG - All messages
st.subheader("📋 MQTT Messages from ESP")
if st.session_state.messages:
    for msg in st.session_state.messages[-10:]:
        st.code(msg)
else:
    st.info("👈 No messages received from ESP yet...")

st.caption("**ESP must publish to:** `ravi2025/home/status`")
