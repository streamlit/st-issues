import altair as alt
import pandas as pd
import streamlit as st
import numpy as np

st.set_page_config(page_title="Test vconcat with repeat", layout="wide")
st.title("Testing vconcat with repeated charts")

# Generate sample data similar to your use case
np.random.seed(42)

# Create a dataframe with similar structure to your data
data = []
categories = ["config_A", "config_B", "config_C"]
bins = [30, 50, 70]

for category in categories:
    for bin_val in bins:
        for i in range(10):
            bw = 50 + i * 10 + np.random.uniform(-5, 5)
            data.append({
                "category": category,
                "bins": bin_val,
                "abw": bw,
                "arl": 100 + (bw - 50) * 0.5 + np.random.uniform(-10, 10),
                "aob": 20 + (bw - 50) * 0.3 + np.random.uniform(-5, 5),
                "tmp": 10 + (bw - 50) * 0.1 + np.random.uniform(-2, 2),
                "selected": i == 5  # Mark one point as selected
            })

df = pd.DataFrame(data)

st.write("### Sample Data")
st.dataframe(df)

# Define common elements
tooltip_list = [
    "category",
    "bins",
    "abw",
    "arl",
    "aob",
    "tmp",
]
custom_tooltip = alt.Tooltip(tooltip_list)

chart_legend = alt.Legend(
    orient="right",
    title="Category",
    titleColor="black",
    labelColor="black",
)

st.write("## Approach 1: Using vconcat with separate faceted charts")

# Create individual charts with faceting
chart_arl = (
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "abw",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(title="ABW"),
        ),
        y=alt.Y(
            "arl",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(title="ARL"),
        ),
        color=alt.Color("category:N", legend=chart_legend),
        tooltip=custom_tooltip,
    )
)

chart_arl_sel = (
    alt.Chart(df)
    .mark_point(shape="diamond", color="purple", filled=True, size=100)
    .encode(
        x=alt.X("abw", type="quantitative"),
        y=alt.Y("arl", type="quantitative"),
        tooltip=custom_tooltip,
    )
    .transform_filter(alt.datum.selected == True)
)

chart_arl_combined = alt.layer(chart_arl, chart_arl_sel).facet(
    column=alt.Column(
        "bins:N",
        title="Bins",
    )
)

chart_ob = (
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "abw",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(title="ABW"),
        ),
        y=alt.Y(
            "aob",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(title="AOB"),
        ),
        color=alt.Color("category:N", legend=chart_legend),
        tooltip=custom_tooltip,
    )
)

chart_ob_sel = (
    alt.Chart(df)
    .mark_point(shape="diamond", color="purple", filled=True, size=100)
    .encode(
        x=alt.X("abw", type="quantitative"),
        y=alt.Y("aob", type="quantitative"),
        tooltip=custom_tooltip,
    )
    .transform_filter(alt.datum.selected == True)
)

chart_ob_combined = alt.layer(chart_ob, chart_ob_sel).facet(
    column=alt.Column(
        "bins:N",
        title="Bins",
    )
)

chart_tmp = (
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "abw",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(title="ABW"),
        ),
        y=alt.Y(
            "tmp",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(title="TMP"),
        ),
        color=alt.Color("category:N", legend=chart_legend),
        tooltip=custom_tooltip,
    )
)

chart_tmp_sel = (
    alt.Chart(df)
    .mark_point(shape="diamond", color="purple", filled=True, size=100)
    .encode(
        x=alt.X("abw", type="quantitative"),
        y=alt.Y("tmp", type="quantitative"),
        tooltip=custom_tooltip,
    )
    .transform_filter(alt.datum.selected == True)
)

chart_tmp_combined = alt.layer(chart_tmp, chart_tmp_sel).facet(
    column=alt.Column(
        "bins:N",
        title="Bins",
    )
)

# Combine with vconcat
vconcat_chart = (
    alt.vconcat(
        chart_arl_combined,
        chart_ob_combined,
        chart_tmp_combined,
    )
    .resolve_scale(x="independent", y="independent")
    .properties(
        title=alt.TitleParams(
            text="Metrics vs ABW (vconcat approach)",
            anchor="middle",
            fontSize=16,
        )
    )
)

st.altair_chart(vconcat_chart, width='stretch')

st.write("## Approach 2: Using repeat with facet")

# Create base chart with repeat
base_chart = (
    alt.Chart()
    .mark_line(point=True, clip=True)
    .encode(
        x=alt.X(
            alt.repeat("column"),
            type="quantitative",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                title="ABW",
                titleFontSize=14,
            ),
        ),
        y=alt.Y(
            alt.repeat("row"),
            type="quantitative",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                titleFontSize=14,
            ),
        ),
        color=alt.Color("category:N", legend=chart_legend),
        tooltip=custom_tooltip,
    )
)

selected_chart = (
    alt.Chart()
    .mark_point(shape="diamond", color="purple", filled=True, size=100, clip=True)
    .encode(
        x=alt.X(alt.repeat("column"), type="quantitative"),
        y=alt.Y(alt.repeat("row"), type="quantitative"),
        tooltip=custom_tooltip,
    )
    .transform_filter(alt.datum.selected == True)
)

repeat_chart = (
    alt.layer(base_chart, selected_chart, data=df)
    .facet(
        column=alt.Column(
            "bins:N",
            title="Bins",
        )
    )
    .repeat(
        row=[
            "arl",
            "aob",
            "tmp",
        ],
        column=["abw"],
    )
    .resolve_scale(x="independent", y="independent")
    .properties(
        title=alt.TitleParams(
            text="Metrics vs ABW (repeat approach)",
            anchor="middle",
            fontSize=16,
        )
    )
)

st.altair_chart(repeat_chart, width='stretch')

st.write("## Comparison")
st.write("""
**Approach 1 (vconcat):**
- Creates separate charts for each metric
- Each chart is faceted by bins
- Charts are stacked vertically
- More control over individual chart properties
- But **Does not** render any charts

**Approach 2 (repeat with facet):**
- Uses repeat to create multiple rows
- Facets by bins for each repeated row
- More compact specification
- May have issues with facet + repeat interaction
- This **does** render charts but unable to label the y-axis
""")
