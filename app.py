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
# Session State
# ─────────────────────────────────────────────
if "client" not in st.session_state: st.session_state.client = None
if "esp_status" not in st.session_state: st.session_state.esp_status = "OFFLINE"
if "wifi_rssi" not in st.session_state: st.session_state.wifi_rssi = -100
if "upload_time" not in st.session_state: st.session_state.upload_time = 0
if "last_heartbeat" not in st.session_state: st.session_state.last_heartbeat = 0
if "mqtt_status" not in st.session_state: st.session_state.mqtt_status = "🔄 Connecting"
if "pin_states" not in st.session_state: st.session_state.pin_states = [False] * 8
if "is_test_active" not in st.session_state: st.session_state.is_test_active = False  # ✅ FIXED KEY NAME

HEARTBEAT_TIMEOUT = 45

# ─────────────────────────────────────────────
# MQTT Functions
# ─────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC_STATUS)
        client.subscribe(TOPIC_STATUS_JSON)
        st.session_state.mqtt_status = "✅ MQTT Broker Connected"
    else:
        st.session_state.mqtt_status = f"❌ MQTT RC:{rc}"

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        if msg.topic == TOPIC_STATUS_JSON:
            data = json.loads(payload)
            st.session_state.esp_status = data.get("status", "OFFLINE")
            st.session_state.wifi_rssi = data.get("rssi", -100)
            st.session_state.upload_time = data.get("uptime", 0)
            st.session_state.last_heartbeat = time.time()
            st.session_state.pin_states = [bool(x) for x in data.get("pins", [0]*8)]
            st.session_state.is_test_active = False  # Real ESP clears test
        elif "ONLINE" in payload.upper():
            st.session_state.esp_status = "ONLINE"
            st.session_state.last_heartbeat = time.time()
            st.session_state.is_test_active = False
    except: pass

def check_heartbeat():
    if st.session_state.last_heartbeat > 0 and not st.session_state.is_test_active:
        if time.time() - st.session_state.last_heartbeat > HEARTBEAT_TIMEOUT:
            st.session_state.esp_status = "OFFLINE"
            st.session_state.wifi_rssi = -100

# ─────────────────────────────────────────────
# Page Setup
# ─────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Control", layout="wide")
st.title("🔌 ESP8266 Remote Control")

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
        st.session_state.mqtt_status = "✅ MQTT Ready"
    except Exception as e:
        st.session_state.mqtt_status = f"❌ {e}"
else:
    try:
        st.session_state.client.loop(timeout=0.1)
    except: pass

# Refresh button
if st.button("🔄 Refresh", key="refresh_btn"): st.rerun()

# ─────────────────────────────────────────────
# Status Row
# ─────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    color = "🟢" if st.session_state.esp_status == "ONLINE" else "🔴"
    status_text = "ONLINE (TEST)" if st.session_state.is_test_active else st.session_state.esp_status
    st.metric("ESP", f"{color} {status_text}")

with col2:
    rssi = st.session_state.wifi_rssi
    bars = "█" * max(0, int((rssi + 100) / 20))
    st.metric("WiFi", f"{rssi}dBm", help=bars)

with col3:
    uptime = f"{st.session_state.upload_time//3600}h"
    st.metric("Uptime", uptime)

with col4:
    mqtt_text = "✅ Connected" if st.session_state.client and st.session_state.client.is_connected() else "❌ Disconnected"
    st.metric("MQTT", st.session_state.mqtt_status)

st.markdown("---")

# ✅ FIXED Test Buttons - UNIQUE KEYS!
col_test1, col_test2 = st.columns(2)
with col_test1:
    if st.button("🧪 TEST MODE", key="test_activate_btn"):  # ✅ UNIQUE KEY
        st.session_state.is_test_active = True
        st.session_state.esp_status = "ONLINE"
        st.session_state.wifi_rssi = -60
        st.session_state.upload_time = 3600
        st.session_state.last_heartbeat = time.time()
        st.session_state.pin_states = [True, False, True, False, True, False, True, False]
        st.rerun()

with col_test2:
    if st.button("🔄 REAL MODE", key="test_deactivate_btn"):  # ✅ UNIQUE KEY
        st.session_state.is_test_active = False
        st.rerun()

# ─────────────────────────────────────────────
# Pin Buttons
# ─────────────────────────────────────────────
cols = st.columns(4)
esp_active = st.session_state.esp_status == "ONLINE" or st.session_state.is_test_active

for i, pin in enumerate(PINS):
    with cols[i % 4]:
        is_on = st.session_state.pin_states[i]
        
        if not esp_active:
            st.button(f"{pin}\n❌ OFFLINE", 
                     disabled=True, 
                     use_container_width=True,
                     key=f"offline_{i}")  # ✅ UNIQUE KEYS
        else:
            if st.button(
                f"{pin}\n{'🟢 ON' if is_on else '⚪ OFF'}",
                key=f"pin_btn_{i}",  # ✅ UNIQUE KEYS
                type="primary" if is_on else "secondary",
                use_container_width=True
            ):
                st.session_state.pin_states[i] = not is_on
                cmd = "ON" if st.session_state.pin_states[i] else "OFF"
                topic = TOPICS[pin]
                
                if st.session_state.client and st.session_state.client.is_connected():
                    result = st.session_state.client.publish(topic, cmd)
                    st.session_state.mqtt_status = f"✅ {pin}={cmd}"
                st.rerun()

st.markdown("---")

# Debug
with st.expander("🔍 Debug Info"):
    st.json({
        "ESP": st.session_state.esp_status + (" (TEST)" if st.session_state.is_test_active else ""),
        "RSSI": st.session_state.wifi_rssi,
        "Uptime": st.session_state.upload_time,
        "Heartbeat": f"{time.time()-st.session_state.last_heartbeat:.0f}s ago" if st.session_state.last_heartbeat else "Never",
        "Test Mode": st.session_state.is_test_active,
        "Pins": {PINS[i]: st.session_state.pin_states[i] for i in range(8)},
        "MQTT Broker": "✅ Connected" if st.session_state.client and st.session_state.client.is_connected() else "❌ Disconnected",
        "MQTT Status": st.session_state.mqtt_status
    })
