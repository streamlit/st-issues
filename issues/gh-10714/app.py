import streamlit as st

st.markdown(
    """<style>
@font-face {font-family: 'My Custom Font';
    src: url("https://raw.githubusercontent.com/githubnext/monaspace/refs/heads/main/fonts/webfonts/MonaspaceArgon-Regular.woff2") format('woff2');
}
h1 {font-family: 'My Custom Font', sans-serif !important;
}
h3 {font-family: 'My Custom Font', sans-serif !important;
}
</style>""",
    unsafe_allow_html=True,
)

st.title("Hello world")
st.header("This is a header")
