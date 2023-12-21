import datetime as dt
import streamlit as st


def updated():
    if st.session_state.get("thingy"):
        st.write(st.session_state.thingy)
    st.write(dt.datetime.now())


def update_value():
    # Uncomment/comment the below lines to go from correct to incorrect behavior
    # st.session_state.thingy = st.session_state.thingy + dt.timedelta(days=1)
    st.session_state.thingy = dt.datetime.now()


def main():
    st.title("reproducible")
    st.date_input("thingy", key="thingy", on_change=updated)
    st.button("update thingy", on_click=update_value)


if __name__ == "__main__":
    main()
