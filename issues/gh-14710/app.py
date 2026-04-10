"""Reproduction for GitHub Issue #14710
Title: CCv2 setTriggerValue dropped on mount with multiple instances
Issue URL: https://github.com/streamlit/streamlit/issues/14710

Description:
Custom Components v2 (CCv2) components that call setTriggerValue synchronously
during mount have their trigger values intermittently dropped by the Python backend.
The JS side executes and sends the value (visible in browser console), but Python
receives None. With multiple component instances, the race compounds — typically
only the last instance's trigger survives.

Expected Behavior:
All component instances calling setTriggerValue on mount should have their trigger
values delivered to the Python backend after a rerun.

Actual Behavior:
Only the last component instance's trigger value arrives; earlier instances show None.
The bug is caused by _coalesce_widget_states dropping json_trigger_value when merging
queued rerun requests.

Reported Version: Streamlit 1.55
"""

from __future__ import annotations

import streamlit as st

# === HEADER ===
st.title("Issue #14710: CCv2 setTriggerValue Dropped on Mount")

st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/14710)")

# === ISSUE OVERVIEW ===
st.header("Issue Overview")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Expected Behavior")
    st.write(
        "All CCv2 component instances that call `setTriggerValue` on mount "
        "should have their values delivered to Python after the triggered rerun."
    )

with col2:
    st.subheader("Actual Behavior (Bug)")
    st.error(
        "Only the **last** component instance's trigger value arrives. "
        "Earlier instances show `None`. With 2 components, typically only 1 works. "
        "With 4+ components, only the very last one succeeds."
    )

st.divider()

# === BUG DEMONSTRATION ===
st.header("Bug Demonstration")

st.write("""
**How to test:**
1. **Hard-refresh** the page (Ctrl+Shift+R / Cmd+Shift+R)
2. Watch the results below — the app will settle after a few reruns
3. Check which instances received their trigger values vs showing `None`
4. Repeat the hard-refresh several times — the bug reproduces consistently
""")


# -- Component definition --

# Staggered delays force each instance's setTriggerValue into a separate
# macrotask, which causes separate rerunScript BackMsgs. The backend's
# _coalesce_widget_states merges them but only preserves the last one's
# json_trigger_value, dropping the rest.
trigger_on_mount = st.components.v2.component(
    "trigger_on_mount",
    js="""
    export default function(component) {
        const { data, setTriggerValue } = component;
        const delay = (data.index || 0) * 50;
        setTimeout(() => {
            console.log(`[CCv2] Instance ${data.index} firing trigger after ${delay}ms`);
            setTriggerValue("result", `value from instance ${data.index}`);
        }, delay);
    }
    """,
)

run_count = st.session_state.get("run_count", 0) + 1
st.session_state["run_count"] = run_count

st.caption(f"Script run #{run_count}")


def _on_result_change() -> None:
    pass


# -- 4 instances with staggered delays --
NUM_INSTANCES = 4
results: list[dict[str, str] | None] = []
for i in range(NUM_INSTANCES):
    r = trigger_on_mount(data={"index": i}, on_result_change=_on_result_change, key=f"comp_{i}")
    results.append(r)

# -- Display results --
successes = 0
for i, r in enumerate(results):
    val = r.get("result") if r else None
    if val:
        successes += 1
        st.write(f"Instance {i}: `{val}`")
    else:
        st.write(f"Instance {i}: **NONE / MISSING** — `{r}`")

st.write(f"**{successes}/{NUM_INSTANCES} instances returned trigger values**")

if successes < NUM_INSTANCES:
    st.error(
        f"BUG REPRODUCED: Only {successes}/{NUM_INSTANCES} triggers arrived. "
        f"The missing triggers were dropped during rerun request coalescing."
    )
else:
    st.success(
        "All triggers arrived on this load. Try hard-refreshing — the bug is intermittent without staggered delays."
    )

st.divider()

# === ROOT CAUSE ===
st.header("Root Cause")

st.write("""
The bug is a **backend rerun coalescing issue**, not a frontend timing race:

1. **Multiple `setTriggerValue` calls land in separate macrotasks** — each
   instance's JS runs in its own `setTimeout`, so the `WidgetStateManager`
   flushes them as separate `rerunScript` BackMsgs.

2. **After flushing, the frontend deletes trigger state** — the first flush
   sends instance 0's trigger and immediately removes it from the client-side
   `WidgetStateDict`. The second flush only contains instance 1's trigger.

3. **Backend coalescing drops JSON triggers** — when multiple `rerunScript`
   requests queue while a script run is active, `_coalesce_widget_states`
   merges them. It preserves boolean `trigger_value` (buttons) and
   `chat_input_value`, but **does not preserve `json_trigger_value`**
   (used by CCv2). Earlier triggers are silently dropped.
""")

st.code(
    """
# lib/streamlit/runtime/scriptrunner_utils/script_requests.py
# _coalesce_widget_states only preserves these trigger types:
trigger_value_types = [
    ("trigger_value", False),         # buttons — preserved ✓
    ("chat_input_value", ...),        # chat input — preserved ✓
    # json_trigger_value — NOT preserved ✗  ← THE BUG
    # string_trigger_value — NOT preserved ✗
]
""",
    language="python",
)

st.divider()

# === WORKAROUND ===
st.header("Workaround")

st.write("""
**Use `setStateValue` instead of `setTriggerValue` for mount-time data.**

State values persist across reruns and aren't affected by coalescing,
making them reliable for "send data on mount" patterns. Trigger values
are designed for one-shot events (like button clicks) and are intentionally
ephemeral.
""")

state_on_mount = st.components.v2.component(
    "state_on_mount",
    js="""
    export default function(component) {
        const { data, setStateValue } = component;
        const delay = (data.index || 0) * 50;
        setTimeout(() => {
            console.log(`[CCv2 workaround] Instance ${data.index} setting state`);
            setStateValue("result", `value from instance ${data.index}`);
        }, delay);
    }
    """,
)

st.write("**Using `setStateValue` (workaround):**")

state_results: list[dict[str, str] | None] = []
for i in range(NUM_INSTANCES):
    r = state_on_mount(data={"index": i}, key=f"state_comp_{i}")
    state_results.append(r)

state_successes = 0
for i, r in enumerate(state_results):
    val = r.get("result") if r else None
    if val:
        state_successes += 1
        st.write(f"Instance {i}: `{val}`")
    else:
        st.write(f"Instance {i}: waiting for state... `{r}`")

if state_successes == NUM_INSTANCES:
    st.success(f"All {NUM_INSTANCES} instances received values via setStateValue.")
else:
    st.warning(
        f"{state_successes}/{NUM_INSTANCES} received so far — "
        f"state values arrive on subsequent reruns but are not lost."
    )

st.divider()

# === ENVIRONMENT INFO ===
st.header("Environment Info")

st.code(f"""
Streamlit version: {st.__version__}
Reporter's version: 1.55
Reporter's OS: Ubuntu
Reporter's browser: Chromium / Opera
""")

st.divider()

# === TECHNICAL DETAILS ===
st.header("Technical Details")

st.write("""
**Affected Component:** `st.components.v2` — `setTriggerValue` on mount

**Regression:** No — this is a gap in the coalescing logic that has existed since
`json_trigger_value` was added for CCv2.

**Proposed Fix:** Extend `_coalesce_widget_states` in `script_requests.py` to
preserve `json_trigger_value` and `string_trigger_value` from older pending
`WidgetStates` when the newer message omits that widget ID — mirroring the
existing boolean trigger preservation logic.

**Key Files:**
- `lib/streamlit/runtime/scriptrunner_utils/script_requests.py`
- `frontend/lib/src/WidgetStateManager.ts`
""")

with st.expander("Console Evidence"):
    st.write(
        "Open browser DevTools (F12) and check the Console tab after a hard refresh. "
        "You should see all instances logging their trigger calls:"
    )
    st.code(
        """
[CCv2] Instance 0 firing trigger after 0ms
[CCv2] Instance 1 firing trigger after 50ms
[CCv2] Instance 2 firing trigger after 100ms
[CCv2] Instance 3 firing trigger after 150ms

All 4 fire successfully on the JS side, but only the last one's
value reaches Python.
""",
        language="text",
    )
