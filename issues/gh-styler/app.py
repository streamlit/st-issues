import itertools

import numpy as np
import pandas as pd

import streamlit as st

HEADER_COLOR_CYCLE = itertools.cycle(
    [
        "#00c0f2",  # light-blue-70",
        "#ffbd45",  # "orange-70",
        "#00d4b1",  # "blue-green-70",
        "#1c83e1",  # "blue-70",
        "#803df5",  # "violet-70",
        "#ff4b4b",  # "red-70",
        "#21c354",  # "green-70",
        "#faca2b",  # "yellow-80",
    ]
)


def icon(emoji: str):
    """Shows an emoji as a Notion-style page icon."""
    st.write(
        f'<span style="font-size: 78px; line-height: 1">{emoji}</span>',
        unsafe_allow_html=True,
    )


def space(num_lines=1):
    """Adds empty lines to the Streamlit app."""
    for _ in range(num_lines):
        st.write("")


def colored_header(label, description=None, color=None):
    """Shows a header with a colored underline and an optional description."""
    space(num_lines=2)
    if color is None:
        color = next(HEADER_COLOR_CYCLE)
    st.subheader(label)
    st.write(
        f'<hr style="background-color: {color}; margin-top: 0; margin-bottom: 0; height: 3px; border: none; border-radius: 3px;">',
        unsafe_allow_html=True,
    )
    if description:
        st.caption(description)


TABLE_COUNTER = 0


def show_styler(styled_df):
    global TABLE_COUNTER
    styled_df.set_uuid(f"table_{TABLE_COUNTER}")
    st.markdown("Via Styler HTML:")
    st.markdown(
        styled_df.to_html(),
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown("Via st.table:")
    st.table(styled_df)

    st.markdown("---")

    st.markdown("Via st.dataframe:")
    st.dataframe(styled_df)
    
    TABLE_COUNTER += 1


df = pd.DataFrame(
    [[38.0, 2.0, 18.0, 22.0, 21, np.nan], [19, 439, 6, 452, 226, 232]],
    index=pd.Index(
        ["Tumour (Positive)", "Non-Tumour (Negative)"], name="Actual Label:"
    ),
    columns=pd.MultiIndex.from_product(
        [["Decision Tree", "Regression", "Random"], ["Tumour", "Non-Tumour"]],
        names=["Model:", "Predicted:"],
    ),
)

colored_header("⚠️ Grouped Columns")

show_styler(df.style)

colored_header("✅ Formatting Values")

styled_df_1 = df.style.format(
    precision=0,
    na_rep="MISSING",
    thousands=" ",
    formatter={
        ("Decision Tree", "Tumour"): "{:.2f}",
        ("Regression", "Non-Tumour"): lambda x: f"$ {x * -1e6:,.1f}",
    },
)

show_styler(styled_df_1)

colored_header("✅ Style Values")

weather_df = pd.DataFrame(
    np.random.rand(10, 2) * 5,
    index=pd.date_range(start="2021-01-01", periods=10),
    columns=["Tokyo", "Beijing"],
)


def rain_condition(v):
    if v < 1.75:
        return "Dry"
    elif v < 2.75:
        return "Rain"
    return "Heavy Rain"


def make_pretty(styler):
    styler.set_caption("Weather Conditions")
    styler.format(rain_condition)
    # styler.format_index(lambda v: v.strftime("%A"))
    styler.background_gradient(axis=None, vmin=1, vmax=5, cmap="YlGnBu")
    return styler


styled_df_2 = weather_df.loc["2021-01-04":"2021-01-08"].style.pipe(make_pretty)

show_styler(styled_df_2)

colored_header("❌ Hiding Data")

styled_df_1 = df.style.format("{:.0f}").hide(
    [("Random", "Tumour"), ("Random", "Non-Tumour")], axis="columns"
)
show_styler(styled_df_1)

colored_header("❌ Table Styles")

cell_hover = {  # for row hover use <tr> instead of <td>
    "selector": "td:hover",
    "props": [("background-color", "#ffffb3")],
}
index_names = {
    "selector": ".index_name",
    "props": "font-style: italic; color: darkgrey; font-weight:normal;",
}
headers = {
    "selector": "th:not(.index_name)",
    "props": "background-color: #000066; color: white;",
}
styled_df_1.set_table_styles([cell_hover, index_names, headers])

styled_df_1.set_table_styles(
    [
        {"selector": "th.col_heading", "props": "text-align: center;"},
        {"selector": "th.col_heading.level0", "props": "font-size: 1.5em;"},
        {"selector": "td", "props": "text-align: center; font-weight: bold;"},
    ],
    overwrite=False,
)

styled_df_1.set_table_styles(
    {
        ("Regression", "Tumour"): [
            {"selector": "th", "props": "border-left: 1px solid white"},
            {"selector": "td", "props": "border-left: 1px solid #000066"},
        ]
    },
    overwrite=False,
    axis=0,
)

show_styler(styled_df_1)

colored_header("❌ Data Cell CSS Classes")

styled_df_1.set_table_styles(
    [  # create internal CSS classes
        {"selector": ".true", "props": "background-color: #e6ffe6;"},
        {"selector": ".false", "props": "background-color: #ffe6e6;"},
    ],
    overwrite=False,
)
cell_color = pd.DataFrame(
    [["true ", "false ", "true ", "false "], ["false ", "true ", "false ", "true "]],
    index=df.index,
    columns=df.columns[:4],
)
styled_df_1.set_td_classes(cell_color)

show_styler(styled_df_1)

colored_header("✅ Acting on Data")

np.random.seed(0)
df2 = pd.DataFrame(np.random.randn(10, 4), columns=["A", "B", "C", "D"])


def style_negative(v, props=""):
    return props if v < 0 else None


def highlight_max(s, props=""):
    return np.where(s == np.nanmax(s.values), props, "")


styled_df_3 = df2.style.applymap(style_negative, props="color:red;").applymap(
    lambda v: "opacity: 20%;" if (v < 0.3) and (v > -0.3) else None
)

styled_df_3.apply(highlight_max, props="color:white;background-color:darkblue", axis=0)

styled_df_3.apply(
    highlight_max, props="color:white;background-color:pink;", axis=1
).apply(highlight_max, props="color:white;background-color:purple", axis=None)

show_styler(styled_df_3)

colored_header("❌ Acting on the Index and Column Headers")

styled_df_3.applymap_index(
    lambda v: "color:pink;" if v > 4 else "color:darkblue;", axis=0
)
styled_df_3.apply_index(
    lambda s: np.where(s.isin(["A", "B"]), "color:pink;", "color:darkblue;"), axis=1
)

show_styler(styled_df_3)

colored_header("❌ Add Caption")

styled_df_3.set_caption(
    "Confusion matrix for multiple cancer prediction models."
).set_table_styles(
    [{"selector": "caption", "props": "caption-side: bottom; font-size:1.25em;"}],
    overwrite=False,
)

show_styler(styled_df_3)

colored_header("❌ Highlight Borders")

styled_df_1.set_table_styles(
    [  # create internal CSS classes
        {"selector": ".border-red", "props": "border: 2px dashed red;"},
        {"selector": ".border-green", "props": "border: 2px dashed green;"},
    ],
    overwrite=False,
)
cell_border = pd.DataFrame(
    [["border-green ", " ", " ", "border-red "], [" ", " ", " ", " "]],
    index=df.index,
    columns=df.columns[:4],
)
styled_df_1.set_td_classes(cell_color + cell_border)

show_styler(styled_df_1)

colored_header("❌ Add Tooltips")

tt = pd.DataFrame(
    [
        [
            "This model has a very strong true positive rate",
            "This model's total number of false negatives is too high",
        ]
    ],
    index=["Tumour (Positive)"],
    columns=df.columns[[0, 3]],
)


styled_df_1.set_tooltips(
    tt,
    props="visibility: hidden; position: absolute; z-index: 1; border: 1px solid #000066;"
    "background-color: white; color: #000066; font-size: 0.8em;"
    "transform: translate(0px, -24px); padding: 0.6em; border-radius: 0.5em;",
)

show_styler(styled_df_1)

colored_header("✅ Finer Control with Slicing")

df3 = pd.DataFrame(
    np.random.randn(4, 4),
    pd.MultiIndex.from_product([["A", "B"], ["r1", "r2"]]),
    columns=["c1", "c2", "c3", "c4"],
)

idx = pd.IndexSlice

slice_ = idx[idx[(df3["c1"] + df3["c3"]) < -2.0], ["c2", "c4"]]
styled_df_4 = df3.style.apply(
    highlight_max, props="color:red;", axis=1, subset=slice_
).set_properties(**{"background-color": "#ffffb3"}, subset=slice_)

show_styler(styled_df_4)

colored_header("❌ Change Font")

df4 = pd.DataFrame([[1, 2], [3, 4]])

props = 'font-family: "Times New Roman", Times, serif; color: #e83e8c; font-size:1.3em;'
styled_df_5 = df4.style.set_table_styles([{"selector": "td.col1", "props": props}])

show_styler(styled_df_5)

colored_header("❌ Use classes instead of Styler functions")

build = lambda x: pd.DataFrame(x, index=df2.index, columns=df2.columns)
cls1 = build(df2.apply(highlight_max, props="cls-1 ", axis=0))
cls2 = build(
    df2.apply(highlight_max, props="cls-2 ", axis=1, result_type="expand").values
)
cls3 = build(highlight_max(df2, props="cls-3 "))
styled_df_6 = df2.style.set_table_styles(
    [
        {"selector": ".cls-1", "props": "color:white;background-color:darkblue;"},
        {"selector": ".cls-2", "props": "color:white;background-color:pink;"},
        {"selector": ".cls-3", "props": "color:white;background-color:purple;"},
    ]
).set_td_classes(cls1 + cls2 + cls3)

show_styler(styled_df_6)

colored_header("✅ Builtin Styles: Highlight Null")

df2.iloc[0, 2] = np.nan
df2.iloc[4, 3] = np.nan
styled_df_7 = df2.loc[:4].style.highlight_null(color="yellow")

show_styler(styled_df_7)

colored_header("✅ Builtin Styles: Highlight Min or Max")

styled_df_7 = df2.loc[:4].style.highlight_max(
    axis=1, props="color:white; font-weight:bold; background-color:darkblue;"
)

show_styler(styled_df_7)

colored_header("✅ Builtin Styles: Highlight Between")

left = pd.Series([1.0, 0.0, 1.0], index=["A", "B", "D"])
styled_df_7 = df2.loc[:4].style.highlight_between(
    left=left, right=1.5, axis=1, props="color:white; background-color:purple;"
)

show_styler(styled_df_7)

colored_header("✅ Builtin Styles: Highlight Quantile")

styled_df_7 = df2.loc[:4].style.highlight_quantile(
    q_left=0.85, axis=None, color="yellow"
)

show_styler(styled_df_7)

colored_header("✅ Builtin Styles: Background Gradient")

import seaborn as sns

cm = sns.light_palette("green", as_cmap=True)

styled_df_7 = df2.style.background_gradient(cmap=cm)

show_styler(styled_df_7)

colored_header("✅ Builtin Styles: Text Gradient")

styled_df_7 = df2.style.text_gradient(cmap=cm)

show_styler(styled_df_7)

colored_header("✅ Builtin Styles: Set properties")

styled_df_7 = df2.loc[:4].style.set_properties(
    **{"background-color": "black", "color": "lawngreen", "border-color": "white"}
)

show_styler(styled_df_7)

colored_header("❌ Builtin Styles: Bar charts 1")

styled_df_7 = df2.style.bar(subset=["A", "B"], color="#d65f5f")

show_styler(styled_df_7)

colored_header("❌ Builtin Styles: Bar charts 2")

styled_df_7 = (
    df2.style.format("{:.3f}", na_rep="")
    .bar(
        align=0,
        vmin=-2.5,
        vmax=2.5,
        cmap="bwr",
        height=50,
        width=60,
        props="width: 120px; border-right: 1px solid black;",
    )
    .text_gradient(cmap="bwr", vmin=-2.5, vmax=2.5)
)

show_styler(styled_df_7)

colored_header("❌ Magnify")


def magnify():
    return [
        dict(selector="th", props=[("font-size", "4pt")]),
        dict(selector="td", props=[("padding", "0em 0em")]),
        dict(selector="th:hover", props=[("font-size", "12pt")]),
        dict(
            selector="tr:hover td:hover",
            props=[("max-width", "200px"), ("font-size", "12pt")],
        ),
    ]


np.random.seed(25)
cmap = cmap = sns.diverging_palette(5, 250, as_cmap=True)
bigdf = pd.DataFrame(np.random.randn(20, 25)).cumsum()

styled_df_8 = (
    bigdf.style.background_gradient(cmap, axis=1)
    .set_properties(**{"max-width": "80px", "font-size": "1pt"})
    .set_caption("Hover to magnify")
    .format(precision=2)
    .set_table_styles(magnify())
)

show_styler(styled_df_8)

colored_header("❌ Sticky Headers")

bigdf = pd.DataFrame(np.random.randn(16, 100))
styled_df_8 = bigdf.style.set_sticky(axis="index")

show_styler(styled_df_8)

colored_header("❌ Format Index")

df9 = pd.DataFrame([[1, 2, 3]], columns=[2.0, np.nan, 4.0])
styled_df_9 = df9.style.format_index("{:.2f}", axis=1, na_rep="MISS")

show_styler(styled_df_9)

colored_header("❌ Hide Rows")

df10 = pd.DataFrame([[1, 2], [3, 4], [5, 6]], index=["a", "b", "c"], columns=["A", "B"])
styled_df_9 = df10.style.hide(["a", "b"])

show_styler(styled_df_9)

colored_header("❌ Hide Index 1")

midx = pd.MultiIndex.from_product([["x", "y"], ["a", "b", "c"]])
df11 = pd.DataFrame(np.random.randn(6, 6), index=midx, columns=midx)
styled_df_9 = df11.style.format("{:.1f}").hide()

show_styler(styled_df_9)

colored_header("❌ Hide Index 2")

styled_df_9 = df10.style.hide()

show_styler(styled_df_9)

colored_header("❌ Hide Columns")

df13 = pd.DataFrame([[1, 2], [3, 4], [5, 6]], index=["a", "b", "c"], columns=["A", "B"])
styled_df_9 = df13.style.hide_columns(["A"])

show_styler(styled_df_9)

colored_header("✅ Set Precision")

np.random.seed(24)
df14 = pd.DataFrame({"A": np.linspace(1, 10, 10)})
df14 = pd.concat(
    [df14, pd.DataFrame(np.random.randn(10, 4), columns=list("BCDE"))], axis=1
)
df14.iloc[3, 3] = np.nan
df14.iloc[0, 2] = np.nan


def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = "red" if val < 0 else "black"
    return "color: %s" % color


styled_df_9 = (
    df14.style.applymap(color_negative_red).apply(highlight_max).set_precision(2)
)

show_styler(styled_df_9)


colored_header("❌ Set Column Width")

df17 = pd.DataFrame(
    {
        "test": ["foo foo foo foo foo foo foo foo", "bar bar bar bar bar"],
        "number": [1, 2],
    }
)
styled_df_9 = df17.style.set_properties(subset=["test"], **{"width": "500px"})

show_styler(styled_df_9)

colored_header(
    "Websocket Message Comparison",
    description="In this example, the websocket package of the styled dataframe is 5x larger and requires 10x the loading time compared to the unstyled dataframe. "
    "The reason for the overhead is that in addition to the actual values, a styled dataframe also includes a display value and CSS style for every cell within the proto message.",
)

number_of_rows = st.slider(
    "Number of rows", min_value=10, max_value=150000, value=60000
)

weather_df = pd.DataFrame(
    np.random.rand(number_of_rows, 4) * 5,
    columns=["Tokyo", "Beijing", "Berlin", "San Francisco"],
)

if st.button("Show styled dataframe"):
    styled_weather_df = weather_df.style.pipe(make_pretty)
    st.dataframe(styled_weather_df)

if st.button("Show unstyled dataframe"):
    st.dataframe(weather_df)

colored_header("❌ Format Values 2")

df15 = pd.DataFrame([[np.nan, 1.0, "A"], [2.0, np.nan, 3.0]])
func = lambda s: "STRING" if isinstance(s, str) else "FLOAT"
styled_df_9 = df15.style.format({0: "{:.1f}", 2: func}, precision=4, na_rep="MISS")

show_styler(styled_df_9)
