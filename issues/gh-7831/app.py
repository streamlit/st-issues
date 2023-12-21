import streamlit as st
import pandas as pd
import time

def main():
    text_container = st.empty()
    with text_container:
        st.write("Hello")

    st.data_editor(pd.DataFrame({"Key": ["My Property"], "Value": ["42.0"]}, dtype="string"),
                                column_config={"Key": st.column_config.TextColumn(), 
                                                "Value": st.column_config.TextColumn()},
                                num_rows="dynamic", hide_index=True, use_container_width=True)

    index = 1
    while(True):
        text_container.empty()
        with text_container:
            st.write(f"Hello {index}")
        index += 1
        time.sleep(1)

if __name__ == '__main__':
    main()
