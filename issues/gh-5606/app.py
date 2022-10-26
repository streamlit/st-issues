import streamlit as st

import pyarrow as pa
a = pa.array([1, 2, 3, 4])
b = pa.array([3, 10, 20, 50])

pydict = {'id': a, 'age': b}
df = pa.Table.from_pydict(pydict)

# >>> df.schema
# id: int64
# age: int64

st.dataframe(df)
