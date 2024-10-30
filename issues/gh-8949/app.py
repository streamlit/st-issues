import streamlit as st
import pandas as pd

df = pd.DataFrame(dict(timedelta=[pd.Timedelta(hours=2),
                                  pd.Timedelta(days=1),
                                  pd.Timedelta(days=3),
                                  pd.Timedelta(days=14)]))

st.dataframe(df)
