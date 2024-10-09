import time
import traceback

import streamlit as st
from streamlit.runtime.scriptrunner import StopException


def _clean_input() -> None:
    """Cleans the input field off its contents."""
    st.session_state["chat_bot_input"] = st.session_state.text_input_input_str


def main():
    try:
        chat_placeholder = st.empty()

        button_generate = st.chat_input(
            key="text_input_input_str",
            on_submit=_clean_input,
            placeholder="Deine Nachricht ...")

        st.session_state["stopped"] = False
        def handle_stop():
            print("click!")
            st.session_state["stopped"] = True
        button_stop = st.button("Halt. Stop.", use_container_width=True, on_click=handle_stop)

        result = ["Das", "Alphabet", "besteht", "aus", "24", "Buchstaben", ":", "a,", "b, ", "c, ", "d, ", "e, ", "f, ", "g, ", "h, ", "i, ", "j, ", "k, ", "l, ", "m, ", "n, "]
        complete_result = ""

        if button_generate:
            print("generate.")
            for chunk in result:
                # try:
                do_stop = st.session_state["stopped"]
                if do_stop:
                    print(f"Break! {do_stop}")
                    # StopException thrown <=> st.stop() ??
                    break
                print("loopy")
                complete_result += chunk
                chat_placeholder.empty()
                with chat_placeholder.container():
                    time.sleep(.005)
                    with st.chat_message(name="assistant"):
                        st.markdown(complete_result + " ")
                # except StopException:
                #     print("Exception: Stop Exception.")
                #     break
                # except Exception as ex:
                #     print(f"Uh oh! Exception: {ex}. Traceback: {traceback.print_exc()}")

                print("out of loop")
                chat_placeholder.empty()
                result = {"role": "assistant", "content": complete_result}

                st.write(result["content"])
                st.rerun()

    except StopException as ex:
        print(f"Halt. Exception: Stop Exception.")
        traceback.print_exc()
        st.exception(ex)

    except Exception as ex:
        print(
            f"Exception raised: {ex}. Traceback: {traceback.print_exc()}"
        )
        st.caption(":red[_Bei der Textgenerierung kam es zu einem unerwartetem Fehler._]")
        st.exception(ex)




if __name__ == "__main__":
    main()
