import pandas as pd
import streamlit as st


labels = [
    ["Aiyana", "Aiyana", "Anisha", "Anisha"],
    ["Mathematics", "Science", "Mathematics", "Science"]
]
tuples = list(zip(*labels))
index = pd.MultiIndex.from_tuples(tuples, names=["Students", "Subjects"])
df = pd.DataFrame([
    [98, 95, 99],
    [95, 93, 96],
    [92, 99, 95],
    [99, 95, 97]
], index=index, columns=["1st term", "2nd term", "Final"])

# works as expected for a dataframe
st.dataframe(df)


# transposing..... shows weird results
st.dataframe(df.T)
