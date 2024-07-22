import streamlit as st

np.random.seed(1)

weather = pd.DataFrame(
    np.c_[
        np.random.uniform(0, 35, 10),
        np.random.uniform(20, 100, 10),
        np.random.uniform(980, 1050, 10),
    ],
    index=pd.date_range(start="20240101", periods=10).date,
    columns=[*"ABC"],
)

colnames = {"A": "Temperature (°C)", "B": "Humidity (%)", "C": "Pressure (hPa)"}

st.dataframe(
    weather.style
    # do your stuff here
    .background_gradient(cmap="coolwarm")
    .set_properties(**{"text-align": "center", "width": "110px"})
    # then rename the header
    .format_index(colnames.get, axis=1)
)
