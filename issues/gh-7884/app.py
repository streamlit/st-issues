import streamlit as st

emoji_str = '✨:sparkles:❔:grey_question:🚑:ambulance:4️⃣:four:'

st.markdown(
    f'''
    normal {emoji_str}
    :rainbow[rainbow {emoji_str}]
    :blue[blue {emoji_str}]
    :green[green {emoji_str}]
    :orange[orange {emoji_str}]
    :red[red {emoji_str}]
    :violet[violet {emoji_str}]
    :grey[grey {emoji_str}]
    '''
    )

st.markdown("strikethrough green: :green[~strikethrough~]")
st.markdown("strikethrough rainbow: :rainbow[~strikethrough~]")
st.markdown("LaTeX green: :green[$\\vec{LaTeX}$]")
st.markdown("LaTeX rainbow: :rainbow[$\\vec{LaTeX}$]")
st.markdown("𒐥 (U+12425) green: :green[𒐥]")
st.markdown("𒐥 (U+12425) rainbow: :rainbow[𒐥]")
