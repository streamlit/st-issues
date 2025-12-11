import streamlit as st

TITLE = "Streamlit Performance - Interpreting Pytest Benchmark Results"

st.set_page_config(page_title=TITLE)

st.header(TITLE)

DOCS = """
### How `pytest-benchmark` Works

`pytest-benchmark` captures statistics such as min, max, mean, median, standard
deviation, and interquartile range (IQR) by running the function multiple times
and collecting states on the results. Detailed documentation can be found
[here](https://pytest-benchmark.readthedocs.io/en/stable/calibration.html).

### Reading the Boxplots

Boxplots visualize the distribution of benchmark results, showing the minimum,
first quartile (Q1), median, third quartile (Q3), and maximum values. The
interquartile range (IQR) represents the middle 50% of the data. These plots
help identify outliers and understand test performance.

In the [Pytest Benchmark Runs](pytest_benchmark_runs), boxplots for each test
show the distribution of results, allowing performance comparison across
different runs over time.

There are some other FAQs answered in the [pytest-benchmark
docs](https://pytest-benchmark.readthedocs.io/en/stable/faq.html) that may be
helpful to cross-reference.
"""

st.markdown(DOCS)
