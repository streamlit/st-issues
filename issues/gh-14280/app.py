import streamlit as st
import time
import uuid

# --------------------------------------------
# Session state
# --------------------------------------------

if "items" not in st.session_state:
    st.session_state["items"] = [str(uuid.uuid4())[:5] for _ in range(5)]

# --------------------------------------------
# Stable row containers
# --------------------------------------------

row_containers = []
MAX_ROWS = 5
for i in range(MAX_ROWS):
    row_containers.append(
        st.container(key=f"row_container_{i}")
    )

# Additional nested containers (each with its own key) to demonstrate that
# having stable keyed containers does not prevent clearing
row_content_containers = []
for i in range(MAX_ROWS):
    row_content_containers.append(
        st.container(key=f"row_content_container_{i}")
    )


# --------------------------------------------
# Render rows in their stable containers
# --------------------------------------------

for idx, item in enumerate(st.session_state["items"]):

    # Get the stable container for this row index
    container = row_containers[idx]

    # A nested tree of elements to stress diffing
    container.markdown(f"### Row {idx} — {item}")
    container.code(item)

    if container.button("Remove", key=f"remove_{item}"):
        # Attempt to remove row
        st.session_state["items"] = [
            x for x in st.session_state["items"] if x != item
        ]

        # Explicitly clear the row container
        row_containers[idx].empty()
        st.rerun()


# --------------------------------------------
# Polling simulation, usually we'd grab new data here and update session state, but for this demo we just refresh
# --------------------------------------------
st.caption("Polling refresh…")
time.sleep(2)
st.rerun()
