import pandas as pd
import streamlit as st


def main():
    input_form = st.sidebar.form("input_form")
    input_form.write("Query inputs:")
    submit_button = input_form.form_submit_button("Submit")

    if submit_button is True:

        df = pd.DataFrame(data={"col1": [1, 2], "col2": [3, 4]})

        st.dataframe(df)

        st.download_button(
            label="Download df",
            data=df.to_csv().encode("utf-8"),
            file_name="filename.csv",
            mime="text/csv",
            persist=True,  # <----------- here
        )


if __name__ == "__main__":
    main()
