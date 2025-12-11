import streamlit as st

from app.perf.utils.docs import METRIC_DEFINITIONS

TITLE = "Streamlit Performance - Interpreting Playwright Performance Results"

st.set_page_config(page_title=TITLE)

st.header(TITLE)

DOCS = f"""
While the infrastructure for writing these tests aims to be as simple as
possible, interpreting the results and ensuring that the tests themselves are
meaningful can be a bit more complex.

In general, Playwright Performance tests should be aimed towards a specific set
of user interactions to understand their interactivity profile. The Metrics that
we get from these tests are geared towards user-perceived performance and are
augmented with React Profiler metrics as a way of helping you identify where
potential bottlenecks/optimizations might be.

The metric definitions are as follows:

{METRIC_DEFINITIONS}

## A Note on Variance

With any kind of performance testing, there will be variance between runs due to
several factors. For instance, the current load on the system running the tests
can affect performance metrics. Background processes and other applications
might introduce noise. The type of underlying hardware is a huge factor. The
results you'll see when running a performance test locally on a high powered
MacBook Pro is going to be very different from running the same test on a CI
machine with a different configuration.

We work with this constraint by leveraging a dedicated CI job for Performance
tests where we run each test multiple times. We expect some amount of test runs
to be clear statistical anomalies, which we can choose to filter out to reduce
noise. The output of these multiple runs is then aggregated and analyzed to give
you a more accurate picture of the performance of your test not just for a
single point in time, but to see this trend over time.
"""

st.markdown(DOCS)
