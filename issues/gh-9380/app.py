import pandas as pd
import streamlit as st

NESTED_LAT_LON_COORDS = [
    [
        [8.7778551, 49.3375681],
        [8.7775115, 49.3371419],
        [8.7772715, 49.3369171],
    ],
    [
        [
            [8.7778551, 49.3375681],
            [8.7775115, 49.3371419],
        ]
    ],
]

df = pd.DataFrame(
    {
        "nested_lat_lon_coords": NESTED_LAT_LON_COORDS,
    }
)
st.write(df)
