import streamlit as st
import pandas as pd
import altair as alt


def _create_chart():
    """
    Same chart code for both page and dialog
    """
    df = pd.DataFrame(
        {
            "x": [1, 2, 3],
            "y": [4, 5, 6],
            "y2": [1, 2, 3],
            # in this case, having a facet encoding doesn't make sense, but usually we'd have multiple kpis here
            "kpi": ["kpi1", "kpi1", "kpi1"],
        }
    )
    chart1 = (
        alt.Chart(df)
        .mark_line(point=alt.OverlayMarkDef(size=80))
        .encode(x="x", y="y", color="kpi", tooltip=["x", "y"])
        .interactive()
    )
    chart2 = (
        alt.Chart(df)
        .mark_area()
        .encode(x="x", y="y2", color="kpi", tooltip=["x", "y2"])
    )
    chart = alt.layer(chart1, chart2)
    return chart


@st.dialog("Dialog with Chart", width="large")
def show_dialog():
    # show the chart in the dialog
    chart = _create_chart()
    st.altair_chart(chart)


# show the chart in the page
chart = _create_chart()
st.altair_chart(chart)

show_dialog_btn = st.button("Show Dialog")


if show_dialog_btn:
    show_dialog()
