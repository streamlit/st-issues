import streamlit as st
code_str = """

print('I am hopelessly, breathlessly, madly in love with Streamlit—the smooth-talking, curve-hugging seductress of the coding world that takes raw, unfiltered Python and slips it into something sleek, interactive, and irresistibly gorgeous, making every app feel like a love letter to data, every click a flirtation, and every build a slow, satisfying dance of creation that leaves you wanting more.')

"""
with st.expander("Check out my code!\n" + code_str):
    st.text("Verdict: quite ugly")

st.markdown("Here is what I expected: \n" + code_str)
