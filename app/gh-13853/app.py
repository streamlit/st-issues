import streamlit as st

num_elements = 10

st.set_page_config(page_title="Mock element Slider", layout="centered")

element_ids = [f"mock-element-{i:02d}" for i in range(num_elements)]
element_to_idx = {element_id: idx for idx, element_id in enumerate(element_ids)}

url_element_id = st.query_params.get("element_id")
if (
    "mock_element_id" not in st.session_state
    or st.session_state["mock_element_id"] not in element_to_idx
):
    st.session_state["mock_element_id"] = (
        url_element_id if url_element_id in element_to_idx else element_ids[0]
    )

with st.container(key="mock-element-slider"):
    st.select_slider(
        "element",
        options=element_ids,
        key="mock_element_id",
        label_visibility="collapsed",
    )

st.query_params["element_id"] = st.session_state["mock_element_id"]

current_element_id = st.session_state["mock_element_id"]
current_idx = element_to_idx[current_element_id]
with st.popover(f"element `{current_element_id}`"):
    st.markdown(f"({current_idx}/{num_elements})")
