import streamlit as st
import pandas as pd

some_letters = "abc"
some_strings = set(some_letters)
for length in range(1, 3):
    some_strings.update(
        {letter + string for letter in some_letters for string in some_strings}
    )

# Create a dataframe
df = pd.DataFrame(
    {
        "a": list(some_strings),
        "b": range(len(some_strings)),
        "c": reversed(range(len(some_strings))),
    }
)

# works as expected
st.write(df)


# does not print data in a sorted manner
st.write(df.set_index("a"))
