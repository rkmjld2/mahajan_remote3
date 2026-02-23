import streamlit as st
import paho.mqtt.client as mqtt
import time
import re

# CONFIG
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_D1 = "ravi2025/home/d1/set"
TOPIC_D2 = "ravi2025/home/d2/set" 
TOPIC_STATUS = "ravi2025/home/status"

# Session state
if "client" not in st.session_state: st.session_state.client = None
if "status" not in st.session_state: st.session_state.status = "Initializing..."
if "last_spoken" not in st.session_state: st.session_state.last_spoken = ""
if "d1_state" not in st.session_state: st.session_state.d1_state = "UNKNOWN"
if "d2_state" not in st.session_state: st.session_state.d2_state = "UNKNOWN"
if "esp_connected" not in st.session_state: st.session_state.esp_connected = False

def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    st.session_state.status = "✅ MQTT OK – waiting ESP..."
    speak_browser("Connected, waiting for ESP")

def on_message(client, userdata, msg):
    status = msg.payload.decode().strip()
    st.session_state.status = status
    
    # Detect ESP connection & parse pins
    if any(x in status.lower() for x in ["online", "ready", "connected"]):
        st.session_state.esp_connected = True
        speak_browser("ESP connected!")
    
    # Parse D1,D2 (flexible matching)
    d1_match = re.search(r'D1[=:]\s*([A-Z]+)', status, re.I)
    d2_match = re.search(r'D2[=:]\s*([A-Z]+)', status, re.I)
    if d1_match: st.session_state.d1_state = d1_match.group(1)
    if d2_match: st.session_state.d2_state = d2_match.group(1)
    
    st.rerun()

# MQTT Setup
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
        st.rerun()
    except Exception as e:
        st.session_state.status = f"❌ MQTT fail: {e}"

def send_command(topic, cmd):
    if st.session_state.client and st.session_state.esp_connected:
        st.session_state.client.publish(topic, cmd)
        speak_browser(f"Sent {cmd}")
        st.rerun()
    else:
        st.error("ESP not ready")

def speak_browser(text):
    if text == st.session_state.last_spoken: return
    st.session_state.last_spoken = text
    safe = text.replace('"', '\\"').replace("'", "\\'")
    st.components.v1.html(f"""
    <script>
    if (speechSynthesis) {{
        speechSynthesis.speak(new SpeechSynthesisUtterance("{safe}"));
    }}
    </script>
    """, height=0)

# ─── UI ───
st.set_page_config(layout="wide")
st.title("🔌 ESP8266 D1/D2 Control")

st.caption(f"MQTT: {BROKER}:{PORT} | Status: **{st.session_state.status}**")

# Pin Status Cards
st.subheader("📊 Pin Status")
col1, col2, col3 = st.columns([2,2,3])

with col1:
    color1 = "inverse" if st.session_state.d1_state == "ON" else "secondary"
    st.metric("D1", st.session_state.d1_state, label_visibility="collapsed")

with col2:
    color2 = "inverse" if st.session_state.d2_state == "ON" else "secondary"
    st.metric("D2", st.session_state.d2_state, label_visibility="collapsed")

with col3:
    conn_color = "inverse" if st.session_state.esp_connected else "warning"
    st.metric("ESP", "✅" if st.session_state.esp_connected else "❌", label_visibility="collapsed")

st.markdown("---")

# Buttons - FIXED SYNTAX (no lambda in on_click)
st.subheader("🎮 Controls")
col1, col2, col3, col4 = st.columns(4)

if col1.button("D1 ON", use_container_width=True, disabled=not st.session_state.esp_connected):
    send_command(TOPIC_D1, "ON")
if col2.button("D1 OFF", use_container_width=True, disabled=not st.session_state.esp_connected):
    send_command(TOPIC_D1, "OFF")
if col3.button("D2 ON", use_container_width=True, disabled=not st.session_state.esp_connected):
    send_command(TOPIC_D2, "ON")
if col4.button("D2 OFF", use_container_width=True, disabled=not st.session_state.esp_connected):
    send_command(TOPIC_D2, "OFF")

st.markdown("---")
st.subheader("📡 Raw ESP Status")
st.code(st.session_state.status)

st.info("🔧 **Debug**: Check browser console + ESP serial for MQTT topics match")
