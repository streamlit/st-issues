import altair as alt
import pandas as pd
import numpy as np
import streamlit as st


st.subheader('Altair Selection API Bug')

st.write(f"Streamlit version: {st.__version__}")
st.write(f"Altair version: {alt.__version__}")

st.write("In altair version 5 a new api for selection was introduced, this new api uses selection_interval and selection_point insteand of the older selection(type = ...). Below are two examples that should with current altair version return the same output. I can confirm the output is same if executed in a jupyter notebook notebooks. ")

import altair as alt
import pandas as pd
import numpy as np
import streamlit as st


def generate_selection(selection):
    np.random.seed(42)
    columns = ["A", "B", "C"]
    source = pd.DataFrame(
        np.cumsum(np.random.randn(100, 3), 0).round(2),
        columns=columns, index=pd.RangeIndex(100, name="x"),
    )
    source = source.reset_index().melt("x", var_name="category", value_name="y")
    
    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection_point(nearest=True, on="pointerover",
                                fields=["x"], empty=False)
    
    # The basic line
    line = alt.Chart(source).mark_line(interpolate="basis").encode(
        x="x:Q",
        y="y:Q",
        color="category:N"
    )
    
    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(selection, alt.value(1), alt.value(0))
    )
    
    # Draw a rule at the location of the selection
    rules = alt.Chart(source).transform_pivot(
        "category",
        value="y",
        groupby=["x"]
    ).mark_rule(color="gray").encode(
        x="x:Q",
        opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
        tooltip=[alt.Tooltip(c, type="quantitative") for c in columns],
    ).add_params(selection)
    
    
    # Put the five layers into a chart and bind the data
    return alt.layer(
        line, points, rules
    ).properties(
        width=600, height=300
    )

st.subheader('Old API for selection')

st.write("""The old apy uses the `on="mouseover"` event to trigger the selection and the `type = 'single'` to select only one point at a time. Using this yield in depreciation warning""")

# Old API Selection
old_selection = alt.selection(nearest=True, on="mouseover",  fields=["x"], empty=False, type = 'single')

# Create chart 
chart = generate_selection(old_selection)

st.altair_chart(chart, use_container_width=True)


st.subheader('New API for selection')

st.write("""The new API uses the `on="pointerover"` event to trigger the selection and the `nearest=True` to select the nearest point to the pointer.""")

new_selection = alt.selection_point(nearest=True, on="pointerover",  fields=["x"], empty=False)

# Create chart 
chart = generate_selection(new_selection)

st.altair_chart(chart, use_container_width=True)
