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

# FIXED: Proper session state initialization
if "client" not in st.session_state:
    st.session_state.client = None
if "esp_status" not in st.session_state:
    st.session_state.esp_status = "CONNECTING"
if "wifi_rssi" not in st.session_state:
    st.session_state.wifi_rssi = -100
if "upload_time" not in st.session_state:
    st.session_state.upload_time = 0
if "last_heartbeat" not in st.session_state:
    st.session_state.last_heartbeat = 0.0  # FIXED: float!
if "mqtt_status" not in st.session_state:
    st.session_state.mqtt_status = "🔄 Connecting..."
if "pin_states" not in st.session_state:
    st.session_state.pin_states = [False] * 8

HEARTBEAT_TIMEOUT = 45

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    st.session_state.mqtt_status = "✅ MQTT Connected"
    client.subscribe(TOPIC_STATUS)
    client.subscribe(TOPIC_STATUS_JSON)
    st.rerun()

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        if msg.topic == TOPIC_STATUS_JSON:
            data = json.loads(payload)
            st.session_state.esp_status = data.get("status", "OFFLINE")
            st.session_state.wifi_rssi = data.get("rssi", -100)
            st.session_state.upload_time = data.get("uptime", 0)
            st.session_state.last_heartbeat = time.time()  # FIXED: Always float
            st.session_state.pin_states = [bool(p) for p in data.get("pins", [0]*8)]
        elif "ONLINE" in payload:
            st.session_state.esp_status = "ONLINE"
            st.session_state.last_heartbeat = time.time()
        st.rerun()
    except:
        pass

# Connect MQTT
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

# FIXED: Safe heartbeat check
current_time = time.time()
if (st.session_state.last_heartbeat is not None and 
    isinstance(st.session_state.last_heartbeat, (int, float)) and
    current_time - float(st.session_state.last_heartbeat) > HEARTBEAT_TIMEOUT):
    st.session_state.esp_status = "OFFLINE"
    st.session_state.wifi_rssi = -100
    st.session_state.upload_time = 0

# UI
st.set_page_config(page_title="ESP8266 Control", layout="wide")
st.title("🔌 ESP8266 8-Pin Control")

# Status dashboard
col1, col2, heartbeat_col, col4 = st.columns(4)
with col1:
    color = "🟢" if st.session_state.esp_status == "ONLINE" else "🔴"
    st.metric("ESP", f"{color} {st.session_state.esp_status}")
with col2:
    rssi = st.session_state.wifi_rssi
    bars = "█" * max(0, int((rssi + 100) / 20)) if rssi > -100 else ""
    st.metric("WiFi", f"{rssi} dBm", help=f"📶{bars}")
with heartbeat_col:
    if st.session_state.last_heartbeat:
        elapsed = current_time - float(st.session_state.last_heartbeat)
        st.metric("Heartbeat", f"{elapsed:.0f}s ago")
    else:
        st.metric("Heartbeat", "Never")
with col4:
    st.metric("MQTT", st.session_state.mqtt_status)

st.markdown("---")

esp_online = st.session_state.esp_status == "ONLINE"

# Buttons
cols = st.columns(4)
for i, pin in enumerate(PINS):
    with cols[i % 4]:
        is_on = st.session_state.pin_states[i]
        if not esp_online:
            st.button(f"{pin} ❌ OFFLINE", key=f"off_{pin}", 
                     disabled=True, use_container_width=True)
        else:
            if st.button(f"{pin} {'🟢 ON' if is_on else '⚪ OFF'}", 
                        key=f"btn_{pin}", 
                        type="primary" if is_on else "secondary",
                        use_container_width=True):
                new_state = not is_on
                st.session_state.pin_states[i] = new_state
                cmd = "ON" if new_state else "OFF"
                if st.session_state.client:
                    st.session_state.client.publish(TOPICS[pin], cmd)
                    st.session_state.mqtt_status = f"✅ Sent {pin}={cmd}"
                st.rerun()

st.markdown("---")

# Debug
with st.expander("🔍 Debug"):
    st.json({
        "ESP Status": st.session_state.esp_status,
        "WiFi RSSI": st.session_state.wifi_rssi,
        "Uptime": st.session_state.upload_time,
        "Last Heartbeat": st.session_state.last_heartbeat,
        "Heartbeat Age": f"{current_time - float(st.session_state.last_heartbeat):.1f}s" if st.session_state.last_heartbeat else "Never",
        "Pin States": st.session_state.pin_states,
        "MQTT": st.session_state.mqtt_status
    })

# Keep MQTT alive
if st.session_state.client:
    st.session_state.client.loop(timeout=0.1)
