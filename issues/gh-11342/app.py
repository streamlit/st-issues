import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def generate_data(num_rows: int, list_length: int, n: int = 5) -> pd.DataFrame:
    x_data = [list(np.linspace(0, 10, list_length)) for _ in range(num_rows)]
    data = {"x": x_data}
    for i in range(1, n + 1):
        data[f"y{i}"] = [list(np.random.rand(list_length)) for _ in range(num_rows)]
    return pd.DataFrame(data)


def main():
    st.dataframe(df, on_select="rerun", key="selections")
    tabs = st.tabs([f"y{i}" for i in range(1, 6)])
    for i, tab in enumerate(tabs, start=1):
        with tab:
            st.subheader(f"Plot y{i} over x")
            selected = st.session_state.selections.get("selection", {}).get("rows", [])
            if selected:
                x_vals, y_vals, labels = [], [], []
                for idx in selected:
                    x_list = df.at[idx, "x"]
                    y_list = df.at[idx, f"y{i}"]
                    x_vals.extend(x_list)
                    y_vals.extend(y_list)
                    labels.extend([str(idx)] * len(x_list))
                plot_df = pd.DataFrame({"x": x_vals, "y": y_vals, "row": labels})
                chart = (
                    alt.Chart(plot_df)
                    .mark_line()
                    .encode(x="x:Q", y="y:Q", color="row:N")
                    .properties(width=700, height=400)
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Please select at least one row to display the plot.")


df = generate_data(num_rows=5, list_length=5000, n=5)
main()
