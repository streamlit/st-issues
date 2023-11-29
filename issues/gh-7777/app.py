import pandas as pd
df = pd.DataFrame(data={'copy from here': [1, 2], 'paste to here': [3, 4]})
st.data_editor(df)
