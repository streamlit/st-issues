import streamlit as st
import pandas as pd

html = """<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Variable</th>
      <th>d = 0.1</th>
      <th>d = 0.2</th>
      <th>d = 0.5</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Adj Control Sample Size*</th>
      <td>nc (adj)</td>
      <td>1569.780</td>
      <td>392.440</td>
      <td>62.790</td>
    </tr>
    <tr>
      <th>Adj Test Sample Size*</th>
      <td>nt (adj)</td>
      <td>1569.780</td>
      <td>392.440</td>
      <td>62.790</td>
    </tr>
    <tr>
      <th>Control Sample Size</th>
      <td>nc</td>
      <td>1569.780</td>
      <td>392.440</td>
      <td>62.795</td>
    </tr>
    <tr>
      <th>Test Sample Size</th>
      <td>nt</td>
      <td>1569.780</td>
      <td>392.440</td>
      <td>62.790</td>
    </tr>
    <tr>
      <th>Confidence</th>
      <td>1-alpha</td>
      <td>0.975</td>
      <td>0.975</td>
      <td>0.970</td>
    </tr>
    <tr>
      <th>Power</th>
      <td>1-beta</td>
      <td>0.800</td>
      <td>0.800</td>
      <td>0.800</td>
    </tr>
  </tbody>
</table>
"""

df = pd.read_html(html)[0]
st.components.v1.html(html)
st.dataframe(df)
st.dataframe(df.style.format(precision=2))
