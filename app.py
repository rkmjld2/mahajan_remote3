import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# Config
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_STATUS = "ravi2025/home/status"
TOPIC_STATUS_JSON = "ravi2025/home/status_json"
PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"]
TOPICS = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in PINS}

# Session state
for key in ["client", "esp_status", "wifi_rssi", "upload_time", "last_heartbeat", 
           "mqtt_status", "pin_states"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "client" else "CONNECTING" if key == "esp_status" else 0 if "time" in key else -100 if key == "wifi_rssi" else [False]*8 if key == "pin_states" else "🔄 Connecting..."

st.session_state.pin_states = [False]*8
HEARTBEAT_TIMEOUT = 45

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    st.session_state.mqtt_status = "✅ MQTT Connected"
    client.subscribe(TOPIC_STATUS)
    client.subscribe(TOPIC_STATUS_JSON)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        if msg.topic == TOPIC_STATUS_JSON:
            data = json.loads(payload)
            st.session_state.esp_status = data.get("status", "OFFLINE")
            st.session_state.wifi_rssi = data.get("rssi", -100)
            st.session_state.upload_time = data.get("uptime", 0)
            st.session_state.last_heartbeat = time.time()
            st.session_state.pin_states = [bool(p) for p in data.get("pins", [0]*8)]
        elif "ONLINE" in payload:
            st.session_state.esp_status = "ONLINE"
            st.session_state.last_heartbeat = time.time()
        st.rerun()
    except: pass

# Connect MQTT (SIMPLE - no threads)
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
        st.session_state.mqtt_status = "🔄 Waiting ESP..."
    except Exception as e:
        st.session_state.mqtt_status = f"❌ {e}"

# UI
st.set_page_config(page_title="ESP8266 Control", layout="wide")
st.title("🔌 ESP8266 8-Pin Control")

# Status Row
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("ESP", f"{'🟢' if st.session_state.esp_status=='ONLINE' else '🔴'} {st.session_state.esp_status}")
with col2: 
    rssi = st.session_state.wifi_rssi
    st.metric("WiFi", f"{rssi}dBm", help="📶" + "█"*max(0,int((rssi+100)/20)))
with col3: st.metric("Uptime", f"{st.session_state.upload_time//3600}h")
with col4: st.metric("MQTT", st.session_state.mqtt_status)

st.markdown("---")

# Check heartbeat
if st.session_state.last_heartbeat and time.time() - st.session_state.last_heartbeat > HEARTBEAT_TIMEOUT:
    st.session_state.esp_status = "OFFLINE"

esp_online = st.session_state.esp_status == "ONLINE"

# Buttons
cols = st.columns(4)
for i, pin in enumerate(PINS):
    with cols[i%4]:
        is_on = st.session_state.pin_states[i]
        if not esp_online:
            st.button(f"{pin} ❌", disabled=True, use_container_width=True)
        else:
            if st.button(f"{pin} {'🟢' if is_on else '⚪'}", 
                        key=f"btn_{pin}", 
                        type="primary" if is_on else "secondary",
                        use_container_width=True):
                new_state = not is_on
                st.session_state.pin_states[i] = new_state
                cmd = "ON" if new_state else "OFF"
                st.session_state.client.publish(TOPICS[pin], cmd)
                st.session_state.mqtt_status = f"✅ {pin}={cmd}"
                st.rerun()

# Debug
with st.expander("Debug"):
    st.json({
        "Status": st.session_state.esp_status,
        "RSSI": st.session_state.wifi_rssi,
        "Uptime": st.session_state.upload_time,
        "Pins": st.session_state.pin_states,
        "MQTT": st.session_state.mqtt_status
    })

# Keep MQTT alive
if st.session_state.client:
    st.session_state.client.loop(timeout=0.1)
