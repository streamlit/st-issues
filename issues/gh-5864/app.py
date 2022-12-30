from decimal import Decimal
import pandas as pd
import streamlit as st

dec1 = Decimal('-0.03864734299516908213')
dec2 = Decimal('1111111111111111111111')

df = pd.DataFrame({'A': [dec1, dec2]})
st.dataframe(df)

l = [dec1, dec2]
st.table(l)
