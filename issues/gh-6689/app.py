import pandas as pd
import streamlit as st

data1 = {
  "VALUE": [420, 380, 390],
  "DATE": [50, 60, 70]
}
data = pd.DataFrame(data1)

data2 = {
  "VALUE": [420, 200, 390, 600],
  "DATE": [50, 60, 70, 80]
}


if st.button(label="change"):
    data = pd.DataFrame(data2)
st.vega_lite_chart(
    data=pd.DataFrame(data),
    spec={
        "autosize": {
            "type": "fit",
            "contains": "padding",
            "resize": True,
        },
        "title": "test",
        "layer": [
            {
                "layer": [
                    {
                        "mark": "line",
                    },
                ],
                "encoding": {
                    "x": {
                        "field": "DATE",
                        "title": "",
                        "type": "quantitative",
                    },
                    "y": {
                        "field": "VALUE",
                        "title": "",
                        "type": "quantitative",
                    },
                },
            },
        ],
    },
    use_container_width=True,
    theme="streamlit",
)


st.vega_lite_chart(
    data=pd.DataFrame(data2),
    spec={
        "autosize": {
            "type": "fit",
            "contains": "padding",
            "resize": True,
        },
        "title": "test",
        "layer": [
            {
                "layer": [
                    {
                        "mark": "line",
                    },
                ],
                "encoding": {
                    "x": {
                        "field": "DATE",
                        "title": "",
                        "type": "quantitative",
                    },
                    "y": {
                        "field": "VALUE",
                        "title": "",
                        "type": "quantitative",
                    },
                },
            },
        ],
    },
    use_container_width=True,
    theme="streamlit",
)
