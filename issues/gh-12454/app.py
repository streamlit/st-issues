import streamlit as st
import streamlit.components.v1 as components

wake_lock_js = """
<script>
  let wakeLock = null;
  async function requestWakeLock() {
    try {
      wakeLock = await navigator.wakeLock.request('screen');
      console.log('Wake Lock is active!');
    } catch (err) {
      console.error('Wake Lock request failed:', err);
    }
  }
  if ('wakeLock' in navigator) {
    requestWakeLock();
  } else {
    console.log('Wake Lock API not supported in this browser.');
  }
</script>
"""

st.write("Test")
st.divider()

st.write("Components height test. Height = 0")
components.html(wake_lock_js, height=0)
st.divider()

st.write("Components height test. Height = 1")
components.html(wake_lock_js, height=1)
st.divider()

st.write("No components")
st.divider()
st.write("Test end")
st.divider()
