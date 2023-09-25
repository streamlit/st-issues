import streamlit as st

dot_code = """
    digraph Diagram {
        // rankdir=LR; // Set the layout direction to Left-to-Right
        node [shape=record, style=filled, fillcolor=gray95, margin=0.1, height=0.1, width=0.1]
        Node0 [label = <<b>node0</b>|it's 5pm on friday and I have no idea why this box is so long at the end of this sentence>]
        Node1 [label = <<b>node1</b>|I need to improve product>]
        Node2 [label = <<b>node2</b>|The extra space at the end of the line appears to be proportional to the length of the sentence so I expect the extra space here is going to be very much longer.>]

        Node0 -> Node1 -> Node2;
        }
    """
st.graphviz_chart(dot_code, use_container_width=False)
