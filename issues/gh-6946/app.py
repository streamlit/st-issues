import streamlit as st

sb_target_variable = st.selectbox("Seleccione Variable target: ", ["2112:CV201-Split.F80.mm:A ➡ CONC Split Faja CV-201 Tamaño de tamiz que deja pasar 80% de las particulas"])

st.subheader("Use st.write")
st.write(sb_target_variable)

st.subheader("Use st.text")
st.text(sb_target_variable)
