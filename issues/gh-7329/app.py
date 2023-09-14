import pandas as pd
import streamlit as st

# Create a test dataframe
df = pd.DataFrame(
    {
        "Name": ["Alice", "Bob", "Charlie"],
        "Age": [25.5, 30.3, 35.6],
        "Gender": ["Female", "Male", "Male"],
    }
)


# Define the Streamlit app
def app():
    st.header("Test Dataframe wo styling")
    st.dataframe(
        df,
        column_config={
            "Age": st.column_config.NumberColumn(
                "Age", help="age in years", min_value=0, format="%.0f"
            )
        },
    )
    st.header("Test Dataframe with styling")
    st.dataframe(
        df.style.highlight_max(subset=["Age"], axis=0),
        column_config={
            "Age": st.column_config.NumberColumn(
                "Age", help="age in years", min_value=0, format="%.0f"
            )
        },
    )


# Run the app
if __name__ == "__main__":
    app()
