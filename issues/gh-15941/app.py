"""Reproduction for GitHub Issue #15941
Title: st.pydeck_chart selection events (on_select="rerun") are never delivered
       when the chart is inside @st.fragment
URL: https://github.com/streamlit/streamlit/issues/15941

Expected: Clicking a pickable object in the in-fragment chart triggers a
          (fragment) rerun and populates event.selection.objects, exactly like
          the identical chart outside a fragment.
Actual (reported): The selection event is silently dropped for the in-fragment
          chart — no rerun, no selection state, no console error. Hover
          highlight/tooltips keep working.
Reported versions: 1.56.0 and 1.59.1 (Windows 11 / Docker Debian, Python 3.14/3.11)

Note: This behavior did NOT reproduce in a clean environment on macOS with the
released Streamlit 1.59.1 (headless Chromium) — the in-fragment selection was
delivered in every tested sequence. It is published here so it can be tried on
the live build across different machines/browsers/GPUs, since it appears to be
environment- or hardware-specific. See NOTES.md for details.
"""

import pydeck as pdk
import streamlit as st

st.title("Issue #15941: pydeck selection inside st.fragment")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/15941)")

st.header("Issue Overview")
st.write(
    "**Expected:** clicking a pickable hexagon in the in-fragment chart triggers "
    "a rerun and populates `event.selection.objects`, just like the identical "
    "chart outside a fragment."
)
st.error(
    "**Reported (Bug):** the in-fragment chart silently drops the click — no "
    "rerun, no selection. Hover highlight/tooltips still work."
)
st.warning(
    "This did **not** reproduce in a clean macOS + Chromium test on Streamlit "
    "1.59.1 (both charts selected correctly). Try it on the machine/browser "
    "where you saw the problem and compare the two results below."
)

st.divider()

st.header("Live Reproduction")
st.markdown(
    """
**Steps**
1. Click a blue hexagon in the **first** (outside-fragment) chart → its status
   should switch to `SELECTED_OK`.
2. Click a blue hexagon in the **second** (inside-fragment) chart → its status
   should switch to `SELECTED_OK`.

If step 2 stays on `NO_SELECTION` while step 1 works, you've reproduced the bug.
"""
)

# neighbors, São Paulo (from the original report)
HEXES = ["87a8100d9ffffff", "87a8100dbffffff", "87a8100c1ffffff"]


def _chart(key: str) -> None:
    layer = pdk.Layer(
        "H3HexagonLayer",
        data=[{"hex_id": h} for h in HEXES],
        id="hexes",
        get_hexagon="hex_id",
        get_fill_color=[0, 150, 255, 160],
        pickable=True,
        auto_highlight=True,
    )
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=-23.55, longitude=-46.64, zoom=9),
        map_style=None,
    )
    event = st.pydeck_chart(deck, on_select="rerun", key=key, height=400)
    objects = getattr(getattr(event, "selection", None), "objects", {}) or {}
    if objects:
        st.success(f"`{key}` → SELECTED_OK")
    else:
        st.warning(f"`{key}` → NO_SELECTION (click a blue hexagon)")
    st.json(objects, expanded=False)


st.subheader("1. Outside fragment")
_chart("outside_fragment")


@st.fragment
def _in_fragment() -> None:
    st.subheader("2. Inside @st.fragment")
    _chart("inside_fragment")


_in_fragment()

st.divider()

st.header("Workaround (per reporter)")
st.markdown(
    "Move the chart out of the `@st.fragment` (render it inline in the page) — "
    "that restores click delivery. Downside: you lose the fragment-scoped rerun "
    "cost savings."
)

st.divider()

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}\npydeck version: {pdk.__version__}")
