import streamlit as st
import pandas as pd 
import numpy as np 

st.title("Streamlit has a bug") 

data = [[[1, 2, 3], np.array(5)]] # With numpy object in dataframe, bug is reproduced 
#data = [[[1, 2, 3], [5]]] # Without numpy object in dataframe, bug is *not* reproduced 
df = pd.DataFrame(data, columns=[f"my_column_{i}" for i in range(2)])

st.write("Before calling st.write on the dataframe...") 
for col in df.columns:
    st.write(f"The type of column {col} is {type(df.my_column_0[0])}")
st.dataframe(df)
st.write("After calling st.write on the dataframe...")
for col in df.columns:
    st.write(f"The type of column {col} is {type(df.my_column_0[0])}")
