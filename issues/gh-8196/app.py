import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def create_trajectory_chart(actual_df, forecast_df):

    combined_df = pd.concat([actual_df, forecast_df], ignore_index=True)

    # Create an empty figure
    fig = go.Figure()
    # Add traces for each status
    for status in ['Actual', 'Forecast']:
        df_subset = combined_df[combined_df['status'] == status]
        if not df_subset.empty:
            fig.add_trace(go.Scatter(
                x=df_subset['year'],
                y=df_subset['percentage'],
                name=status
            ))

    # Update layout
    fig.update_layout(
        showlegend=False,
        hovermode="x unified"
    )

    return fig

# Actual data range
actual_data = {
    'year': [2018, 2019, 2020, 2021, 2022],
    'percentage': [10, 11, 12, 13, 14]
}

# This range does not produce error
forecast_data1 = {
    'year': [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042],
    'percentage': [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34]
}

# This range does not produce error when legend is hidden, however error occurs when legend is shown
forecast_data2 = {
    'year': [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046],
    'percentage': [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38]
}

# This range produces an error even when the legend is hidden
forecast_data3 = {
    'year': [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046, 2047],
    'percentage': [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]
}

# This range shows the error on the last two actual data points and first two forecast data points, even when the legend is hidden
forecast_data4 = {
    'year': [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046, 2047, 2048, 2049, 2050, 2051, 2052, 2053, 2054, 2055, 2056, 2057, 2058, 2059, 2060, 2061, 2062, 2063, 2064, 2065, 2066, 2067, 2068, 2069, 2070, 2071, 2072, 2073, 2074, 2075, 2076, 2077],
    'percentage': [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69]
}

# Create the dataframes
actual_df = pd.DataFrame(actual_data)
forecast_df = pd.DataFrame(forecast_data3) # Use this to switch between forecast data options
actual_df['status'] = 'Actual'
forecast_df['status'] = 'Forecast'

# Create the chart
fig_trajectory_chart = create_trajectory_chart(actual_df, forecast_df)
st.plotly_chart(fig_trajectory_chart)
