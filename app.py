import streamlit as st
import paho.mqtt.client as mqtt
import re

# CONFIG - EXACT MATCH YOUR ESP
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_D1 = "ravi2025/home/d1/set"      # ESP SUBSCRIBES to this
TOPIC_D2 = "ravi2025/home/d2/set"      # ESP SUBSCRIBES to this  
TOPIC_STATUS = "ravi2025/home/status"  # ESP PUBLISHES to this

# Session state
for key in ["client", "status", "last_spoken", "esp_connected", "d1_state", "d2_state"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "client" else ""

st.session_state.status = "🔄 Connecting..."

def on_connect(client, userdata, flags, rc):
    st.info(f"✅ MQTT Connected (rc={rc}). Subscribed to {TOPIC_STATUS}")
    client.subscribe(TOPIC_STATUS)

def on_message(client, userdata, msg):
    msg_text = msg.payload.decode()
    st.session_state.status = f"📨 RECEIVED: {msg_text}"
    st.session_state.esp_connected = True
    
    # Parse any D1/D2 in message
    if "ON" in msg_text or "OFF" in msg_text:
        if "D1" in msg_text: st.session_state.d1_state = "ON" if "D1.*ON" in msg_text else "OFF"
        if "D2" in msg_text: st.session_state.d2_state = "ON" if "D2.*ON" in msg_text else "OFF"
    
    st.rerun()

def on_publish(client, userdata, mid):
    st.success("✅ Command SENT")

# CONNECT MQTT
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
    except:
        st.session_state.status = "❌ MQTT Connection FAILED"

def send_cmd(topic, cmd):
    if st.session_state.client:
        st.session_state.client.publish(topic, cmd)
        st.rerun()

# ─── UI ───
st.set_page_config(layout="wide")
st.title("🔌 ESP8266 Debug Control")

st.caption(f"**Status**: {st.session_state.status}")

# BIG STATUS DISPLAY
col1, col2 = st.columns(2)
with col1:
    st.metric("D1", st.session_state.d1_state or "WAIT")
with col2:
    st.metric("D2", st.session_state.d2_state or "WAIT")

esp_icon = "✅" if st.session_state.esp_connected else "❌"
st.metric("ESP", esp_icon, label_visibility="collapsed")

st.markdown("---")

# DEBUG BUTTONS
st.subheader("🔍 DEBUG - Send Test Commands")
c1, c2, c3 = st.columns(3)
if c1.button("📤 TEST STATUS", use_container_width=True):
    send_cmd(TOPIC_STATUS, "TEST from Streamlit")
if c2.button("📤 D1 ON", use_container_width=True):
    send_cmd(TOPIC_D1, "ON")
if c3.button("📤 D2 ON", use_container_width=True):
    send_cmd(TOPIC_D2, "ON")

# CONTROL BUTTONS
st.subheader("🎮 Main Controls")
cols = st.columns(4)
if cols[0].button("D1 ON"): send_cmd(TOPIC_D1, "ON")
if cols[1].button("D1 OFF"): send_cmd(TOPIC_D1, "OFF") 
if cols[2].button("D2 ON"): send_cmd(TOPIC_D2, "ON")
if cols[3].button("D2 OFF"): send_cmd(TOPIC_D2, "OFF")

st.markdown("---")
st.code(st.session_state.status)
