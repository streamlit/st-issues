import pandas as pd
import streamlit as st

df = pd.DataFrame(data= {
    "State" : ["Taken", "Booked", "Free", "Free", "Free", "Reserved", "Reserved"],
    "Till"  : ["2023-01-25 03:00"] + ["2023-01-25 06:00"] + ["2023-01-25 07:00"] + ([""]*4),
    "By"    : ["one@some-domain.com", "(two@some-domain.com)", "", "", "", "(three@some-domain.com)", "(four@some-domain.com)"]
})

state_colors_translated = {
    "Free"     : "LightGreen",
    "Booked"   : "Wheat",
    "Taken"    : "LightCoral",
    "Reserved" : "LightGray",
}

   
st.subheader("App name")
st.write('**Alex**, welcome!')
st.write("")

state_by_place = {i:df["State"][i] for i in df.index}

df_styled = df.style \
                    .applymap(lambda c: f"background-color: {state_colors_translated[c]}", subset=["State"]) \
                    .applymap(lambda c: "color: lightgray" if isinstance(c, str) and c and c[0]=="(" else "")

st.write('State:')
st.dataframe(df_styled)
