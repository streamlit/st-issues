import numpy as np
import pandas as pd
import streamlit as st


def main():
    arrays = [
        ["bar", "bar", "baz", "baz", "foo", "foo", "qux"],
        ["one", "two", "one", "two", "one", "two", ""],
    ]
    tuples = list(zip(*arrays))
    index = pd.MultiIndex.from_tuples(tuples, names=["first", "second"])

    df = pd.DataFrame(np.random.randn(3, 7), index=["A", "B", "C"], columns=index)

    st.dataframe(df)


if __name__ == '__main__':
    import streamlit.web.bootstrap

    if '__streamlitmagic__' not in locals():
        st.web.bootstrap.run(__file__, False, [], {})

    main()
