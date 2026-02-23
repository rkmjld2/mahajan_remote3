import streamlit as st
import paho.mqtt.client as mqtt
import time

BROKER = "broker.hivemq.com"
PORT = 1883

# Listen to ALL ravi2025 topics to catch ESP messages
TOPIC_WILDCARD = "ravi2025/#"

if "client" not in st.session_state: 
    st.session_state.client = None
    st.session_state.all_messages = []
    st.session_state.status = "🚀 Starting MQTT listener..."

def on_connect(client, userdata, flags, rc):
    st.session_state.status = f"✅ MQTT Connected! Listening to ALL ravi2025 topics"
    client.subscribe(TOPIC_WILDCARD)  # Catch EVERYTHING from your ESP
    st.rerun()

def on_message(client, userdata, msg):
    msg_data = f"📨 TOPIC: {msg.topic} | PAYLOAD: {msg.payload.decode()}"
    st.session_state.all_messages.append(msg_data)
    st.session_state.status = msg_data
    st.rerun()

# Setup MQTT
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    st.session_state.client = client
    time.sleep(2)

st.title("🔍 MQTT ESP DEBUGGER")
st.info(f"**Status**: {st.session_state.status}")

st.subheader("📡 ALL MQTT Messages (ravi2025/#)")
if st.session_state.all_messages:
    for msg in st.session_state.all_messages[-10:]:
        st.code(msg)
else:
    st.warning("⏳ NO MESSAGES YET - ESP must publish something...")

st.subheader("🧪 Send Test Commands")
col1, col2, col3 = st.columns(3)
if col1.button("📤 ravi2025/home/status", use_container_width=True):
    st.session_state.client.publish("ravi2025/home/status", "TEST-WEB")
if col2.button("📤 ravi2025/home/d1/set", use_container_width=True):
    st.session_state.client.publish("ravi2025/home/d1/set", "ON")
if col3.button("📤 ravi2025/home/d2/set", use_container_width=True):
    st.session_state.client.publish("ravi2025/home/d2/set", "ON")

st.markdown("---")
st.info("""
🔑 **WHAT TO EXPECT:**
1. Status: ✅ MQTT Connected! 
2. ESP sends ANY message → Shows here IMMEDIATELY
3. If NO messages after 1 minute → ESP MQTT publish BROKEN

👉 **YOUR ESP serial shows 'Published: ESP online - ready'** 
   but Streamlit sees NOTHING = WRONG TOPIC!
""")
