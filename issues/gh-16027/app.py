"""
Reproduction for GitHub Issue #16027
Title: `st.expander` content permanently clipped — interrupted open/close
       animation leaves inline height/overflow lock on `<details>`
URL: https://github.com/streamlit/streamlit/issues/16027

Expected: A re-expanded st.expander shows all of its content.
Actual:   After rapid open/close sequences on a long, chart-heavy page, one
          expander stays at a stale fixed height with the tail of its content
          clipped and unreachable until a rerun/reload.
Reported version: 1.59.2 (regression; the animated-expander logic landed in
          1.55.0 via #13933 / #13934)
"""

import numpy as np

import streamlit as st
import streamlit.components.v1 as components

st.title("Issue #16027: expander content permanently clipped")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/16027)")

# --- Issue Overview ---
st.header("Issue Overview")
st.write(
    "**Expected:** After collapsing and re-expanding an `st.expander`, it shows "
    "all of its content."
)
st.error(
    "**Actual (Bug):** After certain *rapid* open/close sequences across several "
    "expanders on a long, chart-heavy page, one expander ends up **permanently "
    "clipped** — it renders at a stale fixed height with the tail of its content "
    "cut off and unreachable (the page cannot scroll to it). The state persists "
    "until a rerun/reload."
)
st.warning(
    "This is a **timing race** in the frontend open/close animation cleanup, so "
    "it is not deterministic — it may take several rapid attempts to trigger, and "
    "is likeliest on a heavy page where layout is slow. Automated Playwright "
    "runs (200+ rapid bursts, including 6× CPU throttling) did not catch it, so "
    "manual triggering by a human is expected."
)

st.divider()

# --- Bug Demonstration ---
st.header("Bug Demonstration")
st.write(
    """
**Steps (from the reporter):**
1. Expand the collapsed sections at the bottom of the page.
2. Collapse the expanded sections at the top.
3. Collapse the bottom sections again, then re-expand them — **without waiting
   for the open/close animations to settle** (click quickly, several times).
4. It may take a few attempts. When it triggers, a re-expanded section shows
   only part of its content with the rest clipped and unreachable.

**What to look for in DevTools:** the `<details>` element inside
`div[data-testid="stExpander"]` keeps a leftover inline
`overflow: hidden` (and usually an inline `height: <px>`), with no height
animation currently running to clear it.
"""
)

# The optional detector below watches the parent document for the stale-lock
# state and flashes a banner if it sees one. It only works when the component
# iframe can read the parent DOM (same-origin); otherwise it silently no-ops,
# so use DevTools as the ground truth.
components.html(
    """
<div id="gh16027-status" style="font-family: sans-serif; padding: 8px 12px;
     border-radius: 6px; background:#eef; color:#333;">
  Detector: watching for a stale height/overflow lock… (open DevTools if this
  says "unavailable")
</div>
<script>
  const box = document.getElementById("gh16027-status");
  function scan() {
    let doc;
    try { doc = window.parent.document; } catch (e) { doc = null; }
    if (!doc) {
      box.textContent = "Detector unavailable (cross-origin) — use DevTools.";
      box.style.background = "#eee";
      return;
    }
    const details = [...doc.querySelectorAll(
      'div[data-testid="stExpander"] > details')];
    const bad = details.filter(d => {
      const running = d.getAnimations().filter(a => a.playState === "running").length;
      const clipped = d.scrollHeight - d.clientHeight > 5;
      return d.open && d.style.overflow === "hidden" && d.style.height !== ""
        && running === 0 && clipped;
    });
    if (bad.length) {
      box.textContent = "STALE LOCK DETECTED on " + bad.length +
        " expander(s): open with inline overflow:hidden + height, no animation " +
        "running, content clipped. This is bug #16027.";
      box.style.background = "#fdd";
      box.style.color = "#900";
    } else {
      box.textContent = "Detector active: no stale lock right now. Rapidly " +
        "toggle the expanders above to try to trigger it.";
      box.style.background = "#efe";
      box.style.color = "#060";
    }
  }
  setInterval(scan, 500);
  scan();
</script>
""",
    height=90,
)

rng = np.random.default_rng(0)
for i in range(7):
    with st.expander(f"Section {i}", expanded=(i < 3)):
        for j in range(3):
            st.line_chart(rng.standard_normal((200, 3)))

st.divider()

# --- Workaround ---
st.header("Workaround")
st.write(
    "Reloading the page or triggering a rerun that replaces the expander (e.g. "
    "changing its label) clears the stale inline styles. The reporter also ships "
    "a small watchdog that clears leftover inline `height`/`overflow` from "
    "`stExpander` `<details>` when no height animation is running:"
)
st.code(
    """// Watchdog: clear a stale height/overflow lock when nothing is animating.
setInterval(() => {
  document.querySelectorAll('div[data-testid=\"stExpander\"] > details')
    .forEach(d => {
      const running = d.getAnimations().filter(a => a.playState === 'running');
      if (running.length === 0 && d.style.overflow === 'hidden') {
        d.style.height = '';
        d.style.overflow = '';
      }
    });
}, 1000);""",
    language="javascript",
)

st.divider()

# --- Environment ---
st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
