import streamlit as st

same_response ="""Thought: 我需要调用数据库表名清单API来获取数据库中的表名列表。\nAction: list_sql_database_tool\nAction Input: {}\nObservation: dataDict\nThought: 我现在知道了数据库中的表名。\nFinal Answer: 数据库中有以下表：{table1}。请提供具体的表名以获取更详细的信息。"""

if "messages" not in st.session_state or st.button("Clear message history"):  # st.sidebar.button
    st.session_state["messages"] = [{"role": "assistant", "content": "您需要我做什么？"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input(placeholder="请输入您的问题…")
history = []
if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        response, history = same_response,[]
        st.session_state.messages.append({"role": "assistant", "content": response})
        N = response.count("Thought:")
        if N > 0:
            for _ in range(N):
                try:
                    current_sector = response[response.index("Thought:") + 9:response.index("\nThought:")]
                    response = response[response.index("\nThought:") + 1:]

                except:
                    current_sector = response[response.index("Thought:") + 9:response.index("\nFinal Answer:") + 1]
                    final_answer = response[response.index("\nFinal Answer:") + 15:]

                if "Action:" in current_sector:
                    with st.expander(label=current_sector[:current_sector.index("\n")]):
                        st.write("**test**")
                else:
                    container = st.container()
                    container.write(current_sector[:current_sector.index("\n")])
            st.write(final_answer)
        else:
            st.write(response)
