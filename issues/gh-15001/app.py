import pandas as pd
import streamlit as st

st.set_page_config(page_title="gh-15001", layout="centered")

NESTED_DASHBOARD_SPEC = {
    "vconcat": [
        {
            "title": "Revenue by year",
            "data": {
                "values": [
                    {"year": "2024", "amount": 2200},
                    {"year": "2025", "amount": 2100},
                    {"year": "2026", "amount": 1600},
                ]
            },
            "mark": {"type": "line", "point": True},
            "encoding": {
                "x": {"field": "year", "type": "ordinal"},
                "y": {"field": "amount", "type": "quantitative"},
            },
            "width": 400,
        },
        {
            "title": "Budget and net",
            "hconcat": [
                {
                    "data": {
                        "values": [
                            {"metric": "Revenue", "value": 1600},
                            {"metric": "Net", "value": 420},
                        ]
                    },
                    "mark": "bar",
                    "encoding": {
                        "x": {"field": "value", "type": "quantitative"},
                        "y": {"field": "metric", "type": "nominal"},
                    },
                    "width": 400,
                },
                {
                    "data": {
                        "values": [
                            {"metric": "Revenue", "target": 2450},
                            {"metric": "Net", "target": 370},
                        ]
                    },
                    "mark": {"type": "rule", "strokeWidth": 3},
                    "encoding": {
                        "x": {"field": "target", "type": "quantitative"},
                        "y": {"field": "metric", "type": "nominal"},
                    },
                    "width": 400,
                },
            ],
        },
    ]
}

TABLE_DATA = pd.DataFrame(
    {
        "metric": ["Revenue", "Net"],
        "value": [1600, 420],
    }
)


@st.dialog("Dialog with tabs and nested Vega chart", width="medium")
def show_dialog() -> None:
    table_tab, dashboard_tab, analysis_tab = st.tabs(["Table", "Dashboard", "Analysis"])

    with table_tab:
        st.dataframe(TABLE_DATA, hide_index=True)

    with dashboard_tab:
        st.vega_lite_chart(NESTED_DASHBOARD_SPEC, width="stretch")

    with analysis_tab:
        st.write("Analysis tab placeholder")


st.title("Issue #15001")
st.write(
    "Minimal repro for a nested Vega-Lite composition rendered with "
    '`width="stretch"` inside `st.tabs` within an `st.dialog`.'
)

if st.button("Open repro dialog"):
    show_dialog()
