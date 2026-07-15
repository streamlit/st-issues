"""Issue #16005 — Widgets in an st.popover opened inside an st.dialog are occluded and unusable.

Metadata:
  - Reporter: sfc-gh-lwilby-1
  - Introduced: 1.59.0 (React Aria dialog migration, PR #15327)
  - Last working: 1.58.0
  - Status: Regression confirmed (1.58.0 works, 1.59.0+ broken)
  - Versions confirmed: 1.59.0 (broken), 1.58.0 (working); develop broken per issue bisect
"""

import streamlit as st

st.title("Issue #16005: popover inside a dialog is occluded")
st.markdown(
    "**[GitHub #16005](https://github.com/streamlit/streamlit/issues/16005)** — "
    "Since 1.59.0 (React Aria `st.dialog` migration, PR #15327), a `st.popover` "
    "opened **inside** a `st.dialog` has its body occluded by the dialog's overlay. "
    "Widgets in the popover (e.g. a `selectbox`) are not interactive, and clicking "
    "them lands on the dialog's dismiss overlay — which can close the dialog."
)

st.subheader("Reproduce")
st.markdown(
    "1. Click **Open dialog**.\n"
    "2. Inside the dialog, click **Open popover**.\n"
    "3. Try to open the popover's `Fruit` selectbox and pick an option.\n"
    "4. The dropdown does not open; clicking in the popover body hits the dialog "
    "overlay (and can dismiss the dialog)."
)


@st.dialog("My dialog")
def show_dialog():
    st.write("dialog content")

    st.markdown(
        "**Control:** this multiselect is placed *directly* in the dialog and works correctly (opens above the dialog)."
    )
    st.multiselect("Direct-in-dialog multiselect (works)", ["A", "B", "C"])

    st.markdown("**Bug:** the popover below opens, but its `selectbox` is occluded by the dialog and cannot be used.")
    with st.popover("Open popover"):
        fruit = st.selectbox("Fruit", ["Apple", "Banana", "Cherry"])
        st.write(f"picked: {fruit}")


if st.button("Open dialog"):
    show_dialog()

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.success(
        "**Expected (1.58.0)**\n\n"
        "The popover renders above the dialog. Opening the in-popover selectbox, "
        "picking an option, and committing the value works — dismissing neither the "
        "popover nor the dialog."
    )
with col2:
    st.error(
        "**Actual (1.59.0+)**\n\n"
        "The popover body is occluded by the dialog overlay. The in-popover "
        "selectbox is not interactive, and clicking it hits the dialog's dismiss "
        "overlay — which can close the dialog."
    )

st.divider()

st.subheader("Control: standalone popover (works)")
st.markdown("A popover that is **not** inside a dialog behaves correctly.")
with st.popover("Standalone popover"):
    fruit2 = st.selectbox("Fruit (standalone)", ["Apple", "Banana", "Cherry"])
    st.write(f"picked standalone: {fruit2}")

st.divider()

st.subheader("Root cause")
st.markdown(
    "Both the React Aria dialog overlay (`stDialog`, a full-viewport "
    "`position: fixed; inset: 0` element) and the floating-ui popover body "
    "(`stPopoverBody`, portalled to `document.body`) render at the same `popup` "
    "z-index tier. Objective hit-testing at the in-popover selectbox center returns "
    "the dialog, not the widget, and the popover body is absent from "
    "`document.elementsFromPoint` there:\n\n"
    "```\n"
    "selectbox_hit = { topTestId: 'stDialog', inBody: false, inDialog: true }\n"
    "dropdown_opened = false\n"
    "```\n\n"
    "Widgets placed *directly* in the dialog work because BaseWeb overlays render in "
    "the higher `basewebOverlay` tier (`popup + 1`); the popover body stays at "
    "`popup` and loses to the dialog overlay."
)
st.markdown(
    "**Code pointers:** `frontend/lib/src/components/shared/Modal/Modal.tsx` and "
    "`.../Modal/styled-components.ts` (React Aria `ModalOverlay`); "
    "`frontend/lib/src/components/elements/Popover/Popover.tsx` "
    "(`FloatingPortal` → `document.body`, `popup` tier); "
    "`frontend/lib/src/theme/primitives/zIndices.ts` (tier definitions)."
)

st.subheader("Workaround")
st.info(
    "No clean workaround for the popover-in-dialog pattern. Place interactive "
    "widgets directly in the dialog (not inside a popover), or move the popover "
    "outside the dialog."
)

st.subheader("Environment")
st.markdown(
    "- **Streamlit version**: 1.59.0+ (regression); 1.58.0 (last working)\n"
    "- **Browsers**: Chromium, WebKit (both affected)\n"
    "- **OS**: Linux, macOS\n"
    "- **Introduced by**: PR #15327 (React Aria `st.dialog` migration)\n"
    f"- **Running on**: Streamlit {st.__version__}"
)
