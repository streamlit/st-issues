import streamlit as st

option_map = {
    0: ":flag-gb:",
    1: ":flag-ie:",
    2: ":flag-de:",
    3: ":flag-at:",
    4: ":hash:",
}
selection = st.pills(
    "Tool",
    options=option_map.keys(),
    format_func=lambda option: option_map[option],
    selection_mode="single",
)
st.write(
    "Your selected option: "
    f"{None if selection is None else option_map[selection]}"
)

st.markdown(":flag-gb:	:hash:")
