"""Reproduction for GitHub Issue #15905
Title: `st.camera_input` disabled on mobile + docs.streamlit.io is DOWN
URL: https://github.com/streamlit/streamlit/issues/15905

Expected: On a secure context (HTTPS or localhost) with camera permission
          granted, st.camera_input opens the camera and shows a live preview.
Actual:   The widget stays on the "This app would like to use your camera.
          Learn how to allow access." message and never opens the camera on the
          reporter's mobile device.
Reported version: 1.58

Analysis: This message is shown by the frontend WebcamComponent whenever the
browser's `navigator.mediaDevices.getUserMedia()` does not resolve successfully.
That happens when camera permission is denied/blocked, when there is no camera,
when the page is not a secure context, or when the app is embedded in an iframe
without an `allow="camera"` permissions policy. It is the expected fallback UI,
not a code regression — so this reproduction is educational: it shows the state
and lets you confirm behavior on a real device.

Note on "docs are DOWN": the widget's "Learn how to allow access" link points to
https://docs.streamlit.io/knowledge-base/using-streamlit/enable-camera which
resolves normally (HTTP 200). The reporter referenced `docs.streamlit.app`,
which is a different host.
"""

import streamlit as st

st.title("Issue #15905: st.camera_input on mobile")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/15905)")

st.header("Issue Overview")
st.write(
    "**Expected:** On a secure context with camera permission granted, "
    "`st.camera_input` opens the camera and shows a live preview with an enabled "
    "**Take Photo** button."
)
st.error(
    "**Reported (Bug):** On mobile the widget stays on *'This app would like to "
    "use your camera. Learn how to allow access.'* and never opens the camera."
)

st.divider()

st.header("Live Widget")
st.write("Open this app on the device where you see the problem and interact with the widget below:")

photo = st.camera_input("Take a picture")

if photo is not None:
    st.success("Camera access granted — a photo was captured. Works as expected here.")
    st.image(photo)
else:
    st.warning(
        "No photo yet. If you see the *'This app would like to use your camera'* "
        "message and it never opens the camera, camera access is being blocked "
        "(see 'Why this happens' below)."
    )

st.divider()

st.header("Why this happens")
st.markdown(
    """
`st.camera_input` relies on the browser's `getUserMedia()` API. The
*"This app would like to use your camera"* message is shown whenever that API
does **not** succeed. The most common causes on mobile are:

- **Permission was denied or dismissed** — most mobile browsers only prompt
  once. If you dismissed or blocked it, you must re-enable camera access for the
  site in the browser's site settings.
- **In-app / embedded browsers** — camera access is frequently blocked in the
  in-app browsers used by Instagram, Facebook, LinkedIn, etc. Open the app in a
  full browser (Safari / Chrome) instead.
- **Insecure context** — `getUserMedia()` only works over HTTPS (or
  `localhost`). A plain-HTTP deployment will never get camera access.
- **Iframe embed without a camera policy** — if the app is embedded via
  `<iframe>` (including some custom deployments), the iframe must include
  `allow="camera"` or the browser blocks the camera.
"""
)

st.divider()

st.header("Workaround")
st.markdown(
    """
1. Open the app directly in Safari or Chrome (not inside another app's in-app
   browser).
2. Ensure the app is served over **HTTPS**.
3. Re-enable camera permission for the site in the browser's site settings, then
   reload.
4. If the app is embedded in an `<iframe>`, add `allow="camera; microphone"` to
   the iframe tag.
"""
)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
