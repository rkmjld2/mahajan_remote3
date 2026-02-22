# Add to session state init
if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = None

# After buttons, before metrics
col5, _ = st.columns([1,3])
with col5:
    if st.button("🔄 Poll Status", use_container_width=True):
        if st.session_state.client and st.session_state.client.is_connected():
            st.session_state.client.publish(TOPIC_STATUS, "REQUEST_STATUS")
            st.session_state.status = "Status requested"
        st.rerun()

# Fix metrics section
st.subheader("Current Pin Status from ESP")
if st.session_state.last_update_time:
    st.caption(f"Last update: {st.session_state.last_update_time}")
st.metric("D1", st.session_state.pin_d1)
st.metric("D2", st.session_state.pin_d2)
