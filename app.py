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

HEARTBEAT_TIMEOUT = 45

# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────
if "client" not in st.session_state: st.session_state.client = None
if "esp_status" not in st.session_state: st.session_state.esp_status = "🔌 OFFLINE"
if "wifi_rssi" not in st.session_state: st.session_state.wifi_rssi = -100
if "upload_time" not in st.session_state: st.session_state.upload_time = 0
if "last_heartbeat" not in st.session_state: st.session_state.last_heartbeat = 0
if "mqtt_status" not in st.session_state: st.session_state.mqtt_status = "🔄 Connecting"
if "pin_states" not in st.session_state: st.session_state.pin_states = [False] * 8
if "test_active" not in st.session_state: st.session_state.test_active = False

# ─────────────────────────────────────────────
# MQTT Functions
# ─────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC_STATUS)
        client.subscribe(TOPIC_STATUS_JSON)
        st.session_state.mqtt_status = "🌐 MQTT OK"
    else:
        st.session_state.mqtt_status = f"❌ MQTT RC:{rc}"

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        if msg.topic == TOPIC_STATUS_JSON:
            data = json.loads(payload)
            st.session_state.esp_status = "🟢 ONLINE"
            st.session_state.wifi_rssi = data.get("rssi", -100)
            st.session_state.upload_time = data.get("uptime", 0)
            st.session_state.last_heartbeat = time.time()
            st.session_state.pin_states = [bool(x) for x in data.get("pins", [0]*8)]
            st.session_state.test_active = False
    except:
        pass

def check_heartbeat():
    if st.session_state.last_heartbeat > 0 and not st.session_state.test_active:
        elapsed = time.time() - st.session_state.last_heartbeat
        if elapsed > HEARTBEAT_TIMEOUT:
            st.session_state.esp_status = "🔌 OFFLINE"
    else:
        if not st.session_state.test_active:
            st.session_state.esp_status = "🔌 OFFLINE"

# ─────────────────────────────────────────────
# Page Setup
# ─────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Control", layout="wide")
st.title("🔌 ESP8266 Remote Control")

# Heartbeat check
check_heartbeat()

# MQTT Setup
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.loop(timeout=1.0)
        st.session_state.client = client
        st.session_state.mqtt_status = "🌐 MQTT Ready"
    except Exception as e:
        st.session_state.mqtt_status = f"❌ {e}"
else:
    try:
        st.session_state.client.loop(timeout=0.1)
    except:
        pass

# ─────────────────────────────────────────────
# Status Row
# ─────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.session_state.test_active:
        st.metric("ESP", "🧪 TEST", "-60")
        st.caption("SIMULATED")
    else:
        color = "🟢" if "ONLINE" in st.session_state.esp_status else "🔴"
        st.metric("ESP", st.session_state.esp_status, f"{st.session_state.wifi_rssi}")

with col2:
    rssi = st.session_state.wifi_rssi
    bars = "█" * max(0, int((rssi + 100) / 20))
    st.metric("WiFi", f"{rssi}dBm", help=bars)

with col3:
    uptime = f"{st.session_state.upload_time//3600}h"
    st.metric("Uptime", uptime)

with col4:
    broker_status = "✅ Connected" if st.session_state.client and st.session_state.client.is_connected() else "❌ Down"
    st.metric("MQTT", st.session_state.mqtt_status, help=broker_status)

st.markdown("---")

# Test Control Buttons
col_test1, col_test2 = st.columns(2)
with col_test1:
    if st.button("🧪 START TEST", key="start_test"):
        st.session_state.test_active = True
        st.session_state.esp_status = "🧪 TEST"
        st.session_state.wifi_rssi = -60
        st.session_state.upload_time = 3600
        st.session_state.last_heartbeat = time.time()
        st.session_state.pin_states = [True, False, True, False, True, False, True, False]
        st.rerun()

with col_test2:
    if st.button("🔌 REAL ESP", key="stop_test"):
        st.session_state.test_active = False
        st.session_state.esp_status = "🔌 OFFLINE"
        st.rerun()

# Status Indicator
status_col1, status_col2 = st.columns(2)
with status_col1:
    if st.session_state.test_active:
        st.success("🧪 TEST MODE ACTIVE")
    elif "ONLINE" in st.session_state.esp_status:
        st.success("🟢 REAL ESP8266 CONNECTED")
    else:
        st.error("🔌 ESP8266 OFFLINE")
        
with status_col2:
    if st.session_state.client and st.session_state.client.is_connected():
        st.success("🌐 MQTT CONNECTED")
    else:
        st.error("🌐 MQTT DISCONNECTED")

st.markdown("---")

# Pin Buttons
cols = st.columns(4)
pins_active = st.session_state.test_active or "ONLINE" in st.session_state.esp_status

for i, pin in enumerate(PINS):
    with cols[i % 4]:
        is_on = st.session_state.pin_states[i]
        
        if not pins_active:
            st.button(f"{pin}\n❌ OFFLINE", 
                     disabled=True, 
                     use_container_width=True,
                     key=f"off_{i}")
        else:
            if st.button(
                f"{pin}\n{'🟢 ON' if is_on else '⚪ OFF'}",
                key=f"pin_{i}",
                type="primary" if is_on else "secondary",
                use_container_width=True
            ):
                st.session_state.pin_states[i] = not is_on
                cmd = "ON" if st.session_state.pin_states[i] else "OFF"
                if st.session_state.client and st.session_state.client.is_connected():
                    st.session_state.client.publish(TOPICS[pin], cmd)
                    st.session_state.mqtt_status = f"✅ {pin}={cmd}"
                st.rerun()

st.markdown("---")

# Debug
with st.expander("🔍 Debug"):
    st.json({
        "ESP Status": st.session_state.esp_status,
        "Test Active": st.session_state.test_active,
        "WiFi RSSI": st.session_state.wifi_rssi,
        "Uptime": st.session_state.upload_time,
        "Last Heartbeat": f"{time.time()-st.session_state.last_heartbeat:.0f}s ago" if st.session_state.last_heartbeat else "Never",
        "Pin States": {PINS[i]: st.session_state.pin_states[i] for i in range(8)},
        "MQTT Broker": "✅ Connected" if st.session_state.client and st.session_state.client.is_connected() else "❌ Disconnected"
    })
