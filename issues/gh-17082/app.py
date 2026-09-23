"""
Reproduction for GitHub Issue #17082
Title: GlobalHotkeys crashes on keydown/keyup events without a key
URL: https://github.com/streamlit/streamlit/issues/17082

Expected: Malformed keydown/keyup events without a string key are ignored.
Actual:   GlobalHotkeys throws TypeError: Cannot read properties of undefined
          (reading 'toLowerCase')
Reported version: 1.63.0
"""

import streamlit as st
import streamlit.components.v1 as components

st.title("Issue #17082: GlobalHotkeys missing key")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/17082)")

st.header("Issue Overview")
st.write(
    "**Expected:** keydown/keyup events without a string `key` are ignored. "
    "Normal keyboard shortcuts continue to work."
)
st.error(
    "**Actual (Bug):** `GlobalHotkeys.normalizeKey` calls `toLowerCase` on "
    "`undefined` and throws an uncaught TypeError."
)

st.divider()

st.header("Bug Demonstration")
st.write(
    """
**Steps:**
1. Wait for this app to finish loading.
2. Click **Dispatch keyless events** below, or run this in the browser console:

```js
document.dispatchEvent(new Event("keydown"))
document.dispatchEvent(new Event("keyup"))
```

3. The document-level `GlobalHotkeys` listeners throw
   `TypeError: Cannot read properties of undefined (reading 'toLowerCase')`.
"""
)

components.html(
    """
    <button id="repro" style="font: 14px sans-serif; padding: 6px 12px;">
      Dispatch keyless events
    </button>
    <pre id="out" style="margin-top: 8px; font: 12px/1.4 monospace; white-space: pre-wrap;"></pre>
    <script>
      const out = document.getElementById("out");
      const errors = [];
      function record(message) {
        errors.push(message);
        out.textContent = errors.join("\\n");
      }
      try {
        parent.addEventListener("error", (event) => {
          record(String(event.error || event.message));
        });
      } catch (error) {
        record("Could not attach parent error listener: " + error);
      }
      document.getElementById("repro").onclick = () => {
        errors.length = 0;
        out.textContent = "Dispatched. Check this box and the browser console.";
        parent.document.dispatchEvent(new Event("keydown"));
        parent.document.dispatchEvent(new Event("keyup"));
      };
    </script>
    """,
    height=110,
)

st.divider()

st.header("Workaround")
st.write(
    "No app-level workaround. Avoid dispatching plain `Event('keydown')` / "
    "`Event('keyup')` objects; use a `KeyboardEvent` with a string `key` instead. "
    "The library fix is to ignore non-string `event.key` values in both handlers."
)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
