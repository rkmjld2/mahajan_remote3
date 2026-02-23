import streamlit as st
import paho.mqtt.client as mqtt
import time

BROKER = "broker.hivemq.com"
PORT = 1883

CLIENT_ID = f"streamlit_ravi_{int(time.time())}"

TOPIC_D1_SET   = "ravi2025/home/d1/set"
TOPIC_D2_SET   = "ravi2025/home/d2/set"
TOPIC_STATUS   = "ravi2025/home/status"
TOPIC_D1_STATE = "ravi2025/home/d1/state"
TOPIC_D2_STATE = "ravi2025/home/d2/state"

if "client" not in st.session_state: st.session_state.client = None
if "connected" not in st.session_state: st.session_state.connected = False
if "device_online" not in st.session_state: st.session_state.device_online = False
if "d1_state" not in st.session_state: st.session_state.d1_state = "UNKNOWN"
if "d2_state" not in st.session_state: st.session_state.d2_state = "UNKNOWN"
if "last_spoken" not in st.session_state: st.session_state.last_spoken = ""
if "debug_log" not in st.session_state: st.session_state.debug_log = []
if "last_message" not in st.session_state: st.session_state.last_message = "No recent messages"

def log_debug(msg):
    ts = time.strftime("%H:%M:%S")
    st.session_state.debug_log.append(f"[{ts}] {msg}")
    if len(st.session_state.debug_log) > 20: st.session_state.debug_log.pop(0)

def speak(text):
    if not text or text == st.session_state.last_spoken: return
    st.session_state.last_spoken = text
    safe = text.replace('"', '\\"').replace("'", "\\'")
    js = f"""
    <script>
    if ('speechSynthesis' in window) {{
        const u = new SpeechSynthesisUtterance("{safe}");
        u.lang = 'en-US'; u.volume = 1.0; u.rate = 0.95; u.pitch = 1.0;
        window.speechSynthesis.speak(u);
    }}
    </script>
    """
    st.components.v1.html(js, height=0)

def on_connect(c, u, f, rc):
    if rc == 0:
        st.session_state.connected = True
        c.subscribe(TOPIC_STATUS, qos=1)
        c.subscribe(TOPIC_D1_STATE, qos=1)
        c.subscribe(TOPIC_D2_STATE, qos=1)
        log_debug("Connected → Subscribed (QoS 1)")
        speak("MQTT connected")
        st.rerun()
    else:
        log_debug(f"Connect failed rc={rc}")
        speak(f"Connect failed {rc}")

def on_message(c, u, msg):
    t = msg.topic
    p = msg.payload.decode(errors='ignore').strip()
    log_debug(f"RX: {t} → '{p}' (retain={msg.retain})")
    if t == TOPIC_STATUS:
        online = p.upper() == "ONLINE"
        st.session_state.device_online = online
        speak(f"Device {'ONLINE' if online else 'OFFLINE'}")
    elif t == TOPIC_D1_STATE:
        st.session_state.d1_state = p.upper()
    elif t == TOPIC_D2_STATE:
        st.session_state.d2_state = p.upper()
    st.session_state.last_message = f"{t}: {p}"
    st.rerun()

def init_client():
    if st.session_state.client and st.session_state.client.is_connected():
        return st.session_state.client
    log_debug("Init new client")
    c = mqtt.Client(client_id=CLIENT_ID, clean_session=False)
    c.on_connect = on_connect
    c.on_message = on_message
    c.reconnect_delay_set(1, 120)
    try:
        c.connect(BROKER, PORT, 60)
        c.loop_start()
        st.session_state.client = c
        log_debug("Connect requested")
    except Exception as e:
        log_debug(f"Connect fail: {e}")
    return c

client = init_client()

# UI
st.title("ESP8266 D1 / D2 Remote Control")
mqtt_st = "Connected" if st.session_state.connected else "Connecting..."
dev_st = "ONLINE" if st.session_state.device_online else "OFFLINE"
st.caption(f"Broker: {BROKER} | MQTT: {mqtt_st} | Device: {dev_st}")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    color = "green" if st.session_state.d1_state == "ON" else "red" if st.session_state.d1_state == "OFF" else "gray"
    st.markdown(f"**D1 → <span style='color:{color}'>{st.session_state.d1_state}</span>**", unsafe_allow_html=True)
with col2:
    color = "green" if st.session_state.d2_state == "ON" else "red" if st.session_state.d2_state == "OFF" else "gray"
    st.markdown(f"**D2 → <span style='color:{color}'>{st.session_state.d2_state}</span>**", unsafe_allow_html=True)

st.markdown("---")

disabled = not (st.session_state.connected and st.session_state.device_online)

cols = st.columns(4)
with cols[0]:
    if st.button("D1 ON", type="primary", disabled=disabled):
        client.publish(TOPIC_D1_SET, "ON", qos=1)
        speak("D1 ON sent")
with cols[1]:
    if st.button("D1 OFF", disabled=disabled):
        client.publish(TOPIC_D1_SET, "OFF", qos=1)
        speak("D1 OFF sent")
with cols[2]:
    if st.button("D2 ON", type="primary", disabled=disabled):
        client.publish(TOPIC_D2_SET, "ON", qos=1)
        speak("D2 ON sent")
with cols[3]:
    if st.button("D2 OFF", disabled=disabled):
        client.publish(TOPIC_D2_SET, "OFF", qos=1)
        speak("D2 OFF sent")

if disabled:
    st.warning("Buttons disabled – device not ONLINE yet (update ESP to publish retained status/states)")

st.subheader("Latest message")
st.code(st.session_state.last_message)

with st.expander("Debug Log"):
    for l in st.session_state.debug_log:
        st.text(l)
    if st.button("Clear Log"): st.session_state.debug_log = []

if st.button("Test Voice"):
    speak("Test voice: D1 on, D2 off")

st.info("After updating ESP → refresh page. Check debug log for 'RX:' lines with retain=True.")
