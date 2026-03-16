import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_STATUS = "ravi2025/home/status"
TOPIC_STATUS_JSON = "ravi2025/home/status_json"

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"]
TOPICS = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in PINS}

# ─────────────────────────────────────────────
# Session state initialization
# ─────────────────────────────────────────────
if "client" not in st.session_state:
    st.session_state.client = None

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
HEARTBEAT_TIMEOUT = 45

# ─────────────────────────────────────────────
# MQTT callbacks - NO st.rerun() in callbacks!
# ─────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    """MQTT connection callback - NO Streamlit calls here"""
    if rc == 0:
        client.subscribe(TOPIC_STATUS)
        client.subscribe(TOPIC_STATUS_JSON)
        st.session_state.mqtt_status = "✅ MQTT Connected"
    else:
        st.session_state.mqtt_status = f"❌ MQTT Error: {rc}"

def on_message(client, userdata, msg):
    """MQTT message callback - ONLY update session state"""
    try:
        payload = msg.payload.decode()
        
        if msg.topic == TOPIC_STATUS_JSON:
            data = json.loads(payload)
            st.session_state.esp_status = data.get("status", "OFFLINE")
            st.session_state.wifi_rssi = data.get("rssi", -100)
            st.session_state.upload_time = data.get("uptime", 0)
            st.session_state.last_heartbeat = time.time()
            
            # Update pin states from JSON
            pins = data.get("pins", [0]*8)
            for i in range(8):
                st.session_state.pin_states[i] = bool(pins[i])
                
        elif msg.topic == TOPIC_STATUS:
            if "ONLINE" in payload or "connected" in payload:
                st.session_state.esp_status = "ONLINE"
                st.session_state.last_heartbeat = time.time()
                
    except Exception:
        pass  # Silently ignore parse errors

# Check ESP heartbeat
def check_esp_online():
    """Check if ESP is still online"""
    current_time = time.time()
    if st.session_state.last_heartbeat > 0:
        if current_time - st.session_state.last_heartbeat > HEARTBEAT_TIMEOUT:
            st.session_state.esp_status = "OFFLINE"
            st.session_state.wifi_rssi = -100
            st.session_state.upload_time = 0

# ─────────────────────────────────────────────
# Streamlit UI Setup
# ─────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Remote Control", layout="wide")
st.title("🔌 ESP8266 8-Pin Remote Control")

# ─────────────────────────────────────────────
# MQTT Connection & Polling (Main Thread Only!)
# ─────────────────────────────────────────────
# Initialize MQTT client if needed
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(BROKER, PORT, 60)
        st.session_state.client = client
        st.session_state.mqtt_status = "🔄 Waiting for ESP..."
    except Exception as e:
        st.session_state.mqtt_status = f"❌ MQTT Error: {str(e)}"

# CRITICAL: Non-blocking MQTT poll in MAIN THREAD only
if st.session_state.client:
    st.session_state.client.loop(timeout=0.01, max_packets=1)

# Always check ESP status
check_esp_online()

# Force refresh button
if st.button("🔄 Refresh Status", key="refresh", help="Force check ESP status"):
    st.rerun()

# ─────────────────────────────────────────────
# Status Dashboard
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# Pin Control Buttons
# ─────────────────────────────────────────────
cols = st.columns(4)
esp_online = st.session_state.esp_status == "ONLINE"

for i, pin in enumerate(PINS):
    with cols[i % 4]:
        is_on = st.session_state.pin_states[i]
        
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
                # Toggle locally first
                new_state = not is_on
                st.session_state.pin_states[i] = new_state
                
                # Publish to ESP
                command = "ON" if new_state else "OFF"
                topic = TOPICS[pin]
                
                if st.session_state.client:
                    result = st.session_state.client.publish(topic, command)
                    if result.rc == 0:
                        st.session_state.mqtt_status = f"✅ Sent {pin}={command}"
                    else:
                        st.session_state.mqtt_status = f"❌ Publish failed: {result.rc}"
                
                st.rerun()

st.markdown("---")

# ─────────────────────────────────────────────
# Debug Info
# ─────────────────────────────────────────────
with st.expander("🔍 Debug Info"):
    st.json({
        "ESP Status": st.session_state.esp_status,
        "WiFi RSSI": st.session_state.wifi_rssi,
        "Uptime": st.session_state.upload_time,
        "Last Heartbeat": f"{time.time() - st.session_state.last_heartbeat:.1f}s ago" if st.session_state.last_heartbeat else "Never",
        "Pin States": st.session_state.pin_states,
        "MQTT Status": st.session_state.mqtt_status,
        "Client Connected": st.session_state.client.is_connected() if st.session_state.client else False
    })
