import streamlit as st

# Display title
st.title("Streamlit Selectbox with Dict Example")

# Options dictionary
# Below causes the problem that menu items were "1-0","2-0","3-0". "100-Value 1",...expected.
options = {
    "100": "Value 1",
    "200": "Value 2",
    "300": "Value 3"
}

# Below causes "IndexError: string index out of range"
options = {
    "1": "Value 1",
    "2": "Value 2",
    "3": "Value 3"
}


# TypeError: 'int' object is not subscriptable
options = {
    1: "Value 1",
    2: "Value 2",
    3: "Value 3"
}

# TypeError: 'int' object is not subscriptable
options = {
    100: "Value 1",
    200: "Value 2",
    300: "Value 3"
}


# Create selectbox
selected_key = st.selectbox("Choose an option:", options=options.items(), format_func=lambda x: f"{x[0]} - {x[1]}", key="test") # Error occurred above.
