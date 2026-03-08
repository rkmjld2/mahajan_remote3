# ─────────────────────────────────────────────
# Use this improved MQTT handling pattern
# ─────────────────────────────────────────────

import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# ─── Config ────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883

TOPIC_STATUS     = "ravi2025/home/status"
TOPIC_STATUS_JSON = "ravi2025/home/status_json"

PINS = ["D0","D1","D2","D3","D4","D5","D6","D7"]
TOPICS = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in PINS}

HEARTBEAT_TIMEOUT = 35

# ─── Session state ─────────────────────────────────
if "mqtt_client" not in st.session_state:
    st.session_state.mqtt_client = None
    st.session_state.mqtt_connected = False
    st.session_state.last_heartbeat = None

for pin in PINS:
    if pin not in st.session_state:
        st.session_state[pin] = False

for key in ["esp_status", "wifi_rssi", "uptime_sec", "mqtt_msg"]:
    if key not in st.session_state:
        st.session_state[key] = "—"

# ─── MQTT callbacks ────────────────────────────────
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        st.session_state.mqtt_connected = True
        client.subscribe(TOPIC_STATUS)
        client.subscribe(TOPIC_STATUS_JSON)
    else:
        st.session_state.mqtt_connected = False

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        if msg.topic == TOPIC_STATUS_JSON:
            data = json.loads(payload)
            st.session_state.esp_status  = data.get("status",   "OFFLINE")
            st.session_state.wifi_rssi   = data.get("rssi",     -100)
            st.session_state.uptime_sec  = data.get("uptime",   0)
            st.session_state.last_heartbeat = time.time()
        elif msg.topic == TOPIC_STATUS:
            st.session_state.esp_status = payload
            st.session_state.last_heartbeat = time.time()
    except:
        pass  # silent fail on bad messages

# ─── Create / connect client once ──────────────────
def get_mqtt_client():
    if st.session_state.mqtt_client is None:
        client = mqtt.Client(protocol=mqtt.MQTTv5)   # ← important: v5 helps with modern brokers
        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect(BROKER, PORT, keepalive=60)
            st.session_state.mqtt_client = client
        except Exception as e:
            st.error(f"Connect failed: {e}")
            return None

    return st.session_state.mqtt_client

# ─── Main logic ─────────────────────────────────────
client = get_mqtt_client()

if client:
    client.loop()          # ← Very important: call loop() manually every rerun
    # You can call it more often → client.loop(timeout=0.05)

# Check timeout
if st.session_state.last_heartbeat is not None:
    if time.time() - st.session_state.last_heartbeat > HEARTBEAT_TIMEOUT:
        st.session_state.esp_status = "OFFLINE"
        st.session_state.wifi_rssi  = -100
        st.session_state.uptime_sec = 0

# ─── UI ─────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Control", layout="wide")
st.title("ESP8266 8-Pin Remote Control")

# Status line
cols = st.columns([2,1,1,2])
with cols[0]:
    status = st.session_state.esp_status
    color = "🟢" if status == "ONLINE" else "🔴"
    st.markdown(f"**ESP Status:** {color} {status}")

with cols[1]:
    rssi = st.session_state.wifi_rssi
    bars = "█" * max(0, min(5, int((rssi + 100)/20)))
    st.markdown(f"**WiFi:** {rssi} dBm {bars}")

with cols[2]:
    up = st.session_state.uptime_sec
    up_str = f"{up//3600}h {up%3600//60:02d}m" if up else "—"
    st.markdown(f"**Uptime:** {up_str}")

with cols[3]:
    conn = "✅ Connected" if st.session_state.mqtt_connected else "❌ Disconnected"
    st.markdown(f"**MQTT:** {conn}")

st.divider()

# Buttons
btn_cols = st.columns(4)
esp_online = st.session_state.esp_status == "ONLINE"

for i, pin in enumerate(PINS):
    with btn_cols[i % 4]:
        is_on = st.session_state[pin]
        
        if not esp_online:
            st.button(
                f"{pin}  (offline)",
                disabled=True,
                key=f"btn_{pin}",
                use_container_width=True
            )
        else:
            label = f"{pin}  {'ON' if is_on else 'OFF'}"
            if st.button(
                label,
                type="primary" if is_on else "secondary",
                key=f"btn_{pin}",
                use_container_width=True
            ):
                new_state = not is_on
                st.session_state[pin] = new_state
                
                cmd = "ON" if new_state else "OFF"
                if client:
                    client.publish(TOPICS[pin], cmd)
                    st.toast(f"Sent: {pin} → {cmd}")
                st.rerun()

# ─── Auto refresh ───────────────────────────────────
time.sleep(0.15)           # small delay
st.rerun()                 # or use st.button + manual refresh
