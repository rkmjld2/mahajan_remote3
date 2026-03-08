import streamlit as st
import paho.mqtt.client as mqtt
import time, json

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC_STATUS = "ravi2025/home/status"
TOPIC_STATUS_JSON = "ravi2025/home/status_json"

PINS = ["D0","D1","D2","D3","D4","D5","D6","D7"]
TOPICS = {pin: f"ravi2025/home/{pin.lower()}/set" for pin in PINS}

# ─────────────────────────────────────────────
# Session state initialization
# ─────────────────────────────────────────────
if "client" not in st.session_state:
    st.session_state.client = None
if "esp_status" not in st.session_state:
    st.session_state.esp_status = "OFFLINE"
if "wifi_rssi" not in st.session_state:
    st.session_state.wifi_rssi = -100
if "upload_time" not in st.session_state:
    st.session_state.upload_time = None
if "last_heartbeat" not in st.session_state:
    st.session_state.last_heartbeat = None
if "mqtt_status" not in st.session_state:
    st.session_state.mqtt_status = "Starting MQTT..."
for pin in PINS:
    if pin not in st.session_state:
        st.session_state[pin] = False

HEARTBEAT_TIMEOUT = 30

# ─────────────────────────────────────────────
# MQTT callbacks
# ─────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_STATUS)
    client.subscribe(TOPIC_STATUS_JSON)
    st.session_state.mqtt_status = "✅ Connected to MQTT broker"

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if msg.topic == TOPIC_STATUS_JSON:
        try:
            data = json.loads(payload)
            st.session_state.esp_status = data.get("status","OFFLINE")
            st.session_state.wifi_rssi = data.get("rssi",-100)
            st.session_state.upload_time = data.get("uptime",0)
            st.session_state.last_heartbeat = time.time()
        except:
            pass
    elif msg.topic == TOPIC_STATUS:
        st.session_state.esp_status = payload
        st.session_state.last_heartbeat = time.time()

def check_esp_online():
    if st.session_state.last_heartbeat:
        if time.time() - st.session_state.last_heartbeat > HEARTBEAT_TIMEOUT:
            st.session_state.esp_status = "OFFLINE"
            st.session_state.wifi_rssi = -100
            st.session_state.upload_time = 0

# ─────────────────────────────────────────────
# MQTT connection (once)
# ─────────────────────────────────────────────
if st.session_state.client is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        st.session_state.client = client
    except Exception as e:
        st.session_state.mqtt_status = f"❌ MQTT connection failed: {e}"

# ─────────────────────────────────────────────
# Streamlit UI
# ─────────────────────────────────────────────
st.set_page_config(page_title="ESP8266 Remote Control", layout="wide")
st.title("🔌 ESP8266 8-Pin Remote Control")

# Auto-refresh every 5 seconds (new API)
st_autorefresh = st.autorefresh(interval=5000, limit=None, key="refresh")

check_esp_online()

# Status dashboard
col1, col2, col3, col4 = st.columns(4)
with col1:
    status_color = "🟢 ONLINE" if st.session_state.esp_status=="ONLINE" else "🔴 OFFLINE"
    st.metric("ESP8266 Status", status_color)
with col2:
    rssi_bars = "📶" + "█"*max(0,int((st.session_state.wifi_rssi+100)/20)) if st.session_state.wifi_rssi>-100 else "📴"
    st.metric("WiFi Signal", f"{st.session_state.wifi_rssi} dBm", help=rssi_bars)
with col3:
    uptime_str = f"{st.session_state.upload_time//3600}h" if st.session_state.upload_time else "N/A"
    st.metric("Uptime", uptime_str)
with col4:
    st.metric("MQTT", st.session_state.mqtt_status)

st.markdown("---")

# Pin controls
cols = st.columns(4)
esp_online = st.session_state.esp_status=="ONLINE"
for i,pin in enumerate(PINS):
    with cols[i%4]:
        is_on = st.session_state[pin]
        if not esp_online:
            st.button(f"{pin} ❌ OFFLINE", key=f"toggle_{pin}", disabled=True, use_container_width=True)
        else:
            if st.button(f"{pin} {'🟢 ON' if is_on else '⚪ OFF'}", key=f"toggle_{pin}", type="primary" if is_on else "secondary", use_container_width=True):
                new_state = not is_on
                st.session_state[pin] = new_state
                command = "ON" if new_state else "OFF"
                if st.session_state.client:
                    st.session_state.client.publish(TOPICS[pin], command)
                st.session_state.mqtt_status = f"✅ Sent: {pin} → {command}"

st.markdown("---")
with st.expander("📊 Debug Info"):
    st.json({
        "ESP Status": st.session_state.esp_status,
        "WiFi RSSI": st.session_state.wifi_rssi,
        "Uptime (sec)": st.session_state.upload_time,
        "Last Heartbeat": st.session_state.last_heartbeat,
        "MQTT Status": st.session_state.mqtt_status
    })
