"""
Reproduction for GitHub Issue #16148
Title: Screen reader is not announcing the visual label on the 'Fullscreen' button in windows
URL: https://github.com/streamlit/streamlit/issues/16148

Expected: The Fullscreen button's accessible name references the element it
          belongs to (e.g. "Federal Command Center Fullscreen").
Actual:   Every element's Fullscreen button has aria-label "Fullscreen", so a
          screen reader announces identical, indistinguishable buttons.
Reported version: 1.57.0
"""

import base64

import streamlit as st

st.title("Issue #16148: Fullscreen button has no accessible label")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/16148)")

# --- Issue Overview ---
st.header("Issue Overview")
st.write(
    "**Expected:** Each element's **Fullscreen** button has an accessible name "
    "that references the element, e.g. screen reader announces "
    '"Federal Command Center Fullscreen button".'
)
st.error(
    "**Actual (Bug):** Every Fullscreen button has the generic accessible name "
    '`aria-label="Fullscreen"`. On a page with several images/charts, a screen '
    'reader announces a list of identical "Fullscreen" buttons with no way to '
    "tell which element each one expands."
)

st.divider()

# --- Bug Demonstration ---
st.header("Bug Demonstration")
st.write(
    """
**Steps:**
1. Hover over an image to reveal its **Fullscreen** button (top-right).
2. Inspect the button, or tab to it with a screen reader.
3. Observe that its accessible name is just `Fullscreen`, independent of the
   image caption below it.
"""
)


def _svg(label: str, bg: str) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200">'
        f'<rect width="600" height="200" fill="{bg}"/>'
        f'<text x="300" y="110" fill="#E8EEF8" font-family="Arial" '
        f'font-size="26" text-anchor="middle">{label}</text></svg>'
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


st.image(_svg("Federal Command Center", "#0B1F3A"), caption="Federal Command Center")
st.image(
    _svg("DoD Network Architecture", "#102744"), caption="DoD Network Architecture"
)

st.caption(
    "Both Fullscreen buttons above expose the identical accessible name "
    '`aria-label="Fullscreen"`.'
)

st.divider()

# --- Workaround ---
st.header("Workaround")
st.write(
    "A client-side script can patch each Fullscreen button's `aria-label` to "
    "include the associated caption. This is a stopgap for app authors, not a "
    "fix in Streamlit itself."
)
st.code(
    """
import streamlit.components.v1 as components

components.html('''
<script>
(function () {
  const doc = window.parent.document;
  function fix() {
    doc.querySelectorAll('[data-testid="stFullScreenFrame"]').forEach(function (frame) {
      const caption = frame.querySelector('[data-testid="stImageCaption"] p');
      const btn = frame.querySelector('button[aria-label="Fullscreen"]');
      if (caption && btn) {
        btn.setAttribute('aria-label', caption.textContent.trim() + ' Fullscreen');
      }
    });
  }
  fix();
  new MutationObserver(fix).observe(doc.body, { childList: true, subtree: true });
})();
</script>
''', height=0)
""",
    language="python",
)

st.divider()

# --- Environment ---
st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
st.code(
    "Reported on: Streamlit 1.57.0, Python 3.11, Windows 11, Edge 151\n"
    "Confirmed on: 1.57.0 (aria-label is a frontend constant; also present on develop)"
)
