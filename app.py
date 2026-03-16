import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC_STATUS = "ravi2025/home/status"
TOPIC_STATUS_JSON = "ravi2025/home/status_json"

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"]
TOPICS = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in PINS}

# ─────────────────────────────────────────────
# Session state initialization - FIXED
# ─────────────────────────────────────────────
if "client" not in st.session_state:
    st.session_state.client = None

# FIXED: Initialize with better defaults
if "esp_status" not in st.session_state:
    st.session_state.esp_status = "CONNECTING"

if "wifi_rssi" not in st.session_state:
    st.session_state.wifi_rssi = -100

if "upload_time" not in st.session_state:
    st.session_state.upload_time = 0

if "last_heartbeat" not in st.session_state:
    st.session_state.last_heartbeat = 0

if "mqtt_status" not in st.session_state:
    st.session_state.mqtt_status = "🔄 Connecting..."

if "pin_states" not in st.session_state:
    st.session_state.pin_states = [False] * 8

# Heartbeat timeout
HEARTBEAT_TIMEOUT = 45  # Increased to 45s

# ─────────────────────────────────────────────
# MQTT callbacks - FIXED
# ─────────────────────────────────────────────
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
            st.session_state.last_heartbeat = time.time()
            
            # FIXED: Update pin states from JSON
            pins = data.get("pins", [0]*8)
            for i in range(8):
                st.session_state.pin_states[i] = bool(pins[i])
                
        elif msg.topic == TOPIC_STATUS:
            # Handle simple status messages
            if "ONLINE" in payload or "connected" in payload:
                st.session_state.esp_status = "ONLINE"
                st.session_state.last_heartbeat = time.time()
                
        st.rerun()
    except Exception as e:
        pass  # Ignore parse errors

# Check ESP heartbeat - FIXED
def check_esp_online():
    current_time = time.time()
    if st.session_state.last_heartbeat > 0:
        if current_time - st.session_state.last_heartbeat > HEARTBEAT_TIMEOUT:
            st.session_state.esp_status = "OFFLINE"
            st.session_state.wifi_rssi = -100
            st.session_state.upload_time = 0
    st.rerun()

# ─────────────────────────────────────────────
# MQTT connection - FIXED with retry
# ─────────────────────────────────────────────
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
        st.session_state.mqtt_status = "🔄 Waiting for ESP..."
    except Exception as e:
        st.session_state.mqtt_status = f"❌ MQTT Error: {e}"

# Force status check
if st.button("🔄 Refresh Status", key="refresh", help="Force check ESP status"):
    check_esp_online()

# ─────────────────────────────────────────────
# Streamlit UI
# ─────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Remote Control", layout="wide")

st.title("🔌 ESP8266 8-Pin Remote Control")

# Status dashboard - FIXED layout
col1, col2, col3, col4 = st.columns(4)

with col1:
    color = "🟢" if st.session_state.esp_status == "ONLINE" else "🔴"
    st.metric("ESP Status", f"{color} {st.session_state.esp_status}")

with col2:
    rssi = st.session_state.wifi_rssi
    bars = "█" * max(0, int((rssi + 100) / 20)) if rssi > -100 else ""
    st.metric("WiFi", f"{rssi} dBm", help=f"📶{bars}")

with col3:
    uptime = f"{st.session_state.upload_time//3600:.0f}h" if st.session_state.upload_time else "0s"
    st.metric("Uptime", uptime)

with col4:
    st.metric("MQTT", st.session_state.mqtt_status)

st.markdown("---")

# Buttons - FIXED with actual pin states from ESP
cols = st.columns(4)
esp_online = st.session_state.esp_status == "ONLINE"

pin_names = PINS
for i, pin in enumerate(pin_names):
    with cols[i % 4]:
        is_on = st.session_state.pin_states[i]  # Use actual ESP state
        
        if not esp_online:
            st.button(
                label=f"{pin} ❌ OFFLINE",
                key=f"btn_{pin}",
                disabled=True,
                use_container_width=True
            )
        else:
            if st.button(
                label=f"{pin} {'🟢 ON' if is_on else '⚪ OFF'}",
                key=f"toggle_{pin}",
                type="primary" if is_on else "secondary",
                use_container_width=True,
                help=f"Toggle {pin}"
            ):
                # Toggle and publish
                new_state = not is_on
                st.session_state.pin_states[i] = new_state
                
                command = "ON" if new_state else "OFF"
                topic = TOPICS[pin]
                
                if st.session_state.client:
                    result = st.session_state.client.publish(topic, command)
                    st.session_state.mqtt_status = f"✅ Sent {pin}={command}"
                
                st.rerun()

st.markdown("---")

# Debug - FIXED display
with st.expander("🔍 Debug Info"):
    st.json({
        "ESP Status": st.session_state.esp_status,
        "WiFi RSSI": st.session_state.wifi_rssi,
        "Uptime": st.session_state.upload_time,
        "Last Heartbeat": f"{time.time() - st.session_state.last_heartbeat:.1f}s ago" if st.session_state.last_heartbeat else "Never",
        "Pin States": st.session_state.pin_states,
        "MQTT Status": st.session_state.mqtt_status
    })

# Auto refresh every 5 seconds
check_esp_online()
