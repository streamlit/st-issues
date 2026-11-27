"""Synthetic reproduction for GitHub issue #18181."""

import streamlit as st

st.set_page_config(
    page_title="Issue #18181 print-preview patches",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Issue #18181: Print-preview color patches")
st.info("🔗 [View original issue](https://github.com/streamlit/streamlit/issues/18181)")

st.header("Issue overview")
st.write(
    "**Expected:** Printing a fixed-height dashboard container preserves its "
    "screen dimensions without stretching custom backgrounds."
)
st.error(
    "**Actual:** In Streamlit 1.67.0, print layout expands the container and "
    "turns its blue and green background regions into long vertical patches."
)
st.caption(
    "The reporter did not provide their app or CSS. This app uses synthetic "
    "colors to reproduce the same class of print-layout regression."
)

st.header("Reproduction")
st.markdown(
    """
1. Leave **Apply print-safe workaround** unchecked.
2. Open the browser print dialog with **Ctrl+P** or **Cmd+P**.
3. Select landscape layout and compare the panel with its on-screen height.
"""
)

apply_workaround = st.checkbox(
    "Apply print-safe workaround",
    key="apply-print-workaround",
    help="Removes the custom panel background only while printing.",
)

workaround_css = (
    """
    @media print {
        .st-key-patch-panel {
            background: none !important;
        }
    }
    """
    if apply_workaround
    else ""
)
st.markdown(
    f"""
    <style>
    .st-key-patch-panel {{
        background: linear-gradient(
            to right,
            #1010f0 0 44px,
            transparent 44px 72px,
            #00b83f 72px 108px,
            transparent 108px
        ) !important;
    }}
    {workaround_css}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Print test")
st.sidebar.write(f"Streamlit {st.__version__}")
for index in range(10):
    st.sidebar.caption(f"Sidebar row {index + 1}")

controls = st.columns(3)
controls[0].number_input("Columns requested", 1, 8, 3)
controls[1].selectbox("Make dashboard", ["Yes", "No"])
controls[2].selectbox("Show legend", ["No", "Yes"])

with st.container(key="patch-panel", height=420, border=True):
    label_column, data_column = st.columns([1, 4])
    with label_column:
        st.markdown("**Method of repetition**")
        st.selectbox(
            "Method",
            ["Selected metrics"],
            label_visibility="collapsed",
        )
    with data_column:
        st.dataframe(
            {
                "Chart type": ["Bar chart"] * 5,
                "X-axis": ["Period_YYYY_MM"] * 5,
                "Y-axis": ["CIF, CC_PV, CC_Trnx"] * 5,
            },
            height=230,
            use_container_width=True,
        )
        st.bar_chart(
            {
                "CIF": [20, 32, 45, 54, 72, 81],
                "Transactions": [12, 18, 27, 35, 44, 56],
            },
            height=300,
        )

st.header("Content after the fixed-height panel")
for index in range(6):
    st.write(f"Follow-up row {index + 1}")

st.header("Workaround")
st.write(
    "Enable **Apply print-safe workaround** and reopen print preview. The app "
    "keeps its custom background on screen but removes it from printed output. "
    "Pinning Streamlit 1.66.0 also avoids the 1.67.0 height expansion."
)

st.header("Environment")
st.code(f"Streamlit version: {st.__version__}")
