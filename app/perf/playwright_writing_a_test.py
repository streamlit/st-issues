import streamlit as st

TITLE = "Streamlit Performance - Writing a Playwright Performance Test"

st.set_page_config(page_title=TITLE)

st.header(TITLE)

DOCS = """

## When to Use a Playwright Performance Test

✅ When you want to capture the browser experience of a user interacting with
  Streamlit.

✅ When you want fine-grained information about how the browser and the
  underlying React internals are performing.

❌ If you want to measure how performant some backend-specific code path is in
  isolation, utilize the [Pytest Benchmarking](pytest_writing_a_test) tooling instead.

## How to write a Playwright Performance Test

1. In any test in the
   [`e2e_playwright`](https://github.com/streamlit/streamlit/tree/develop/e2e_playwright)
   directory, add `import pytest` and decorate the test with
   `@pytest.mark.performance`.
2. That's it! Your tests will now be run in the Playwright Performance job in CI
   and output Metrics that can be ingested and analyzed with this app.

## Debugging and fixing performance issues

- This app includes a helpful `Playwright Metrics Explorer` that allows you to
  dig into the various metrics that are captured during a Playwright Performance
  test run.
    - This isn't the only way to analyze the data, but it's a good starting
      point if you aren't quite sure where the bottleneck might be coming from.
- Run the test locally via `pytest`
    - The outputted metric JSON file will be automatically outputted to
      `streamlit/e2e_playwright/performance-results`
- Emulate the same scenario as the test locally in your browser
    - As mentioned above, the performance profiles are going to be different
      from CI vs local, however, you can still get a sense of where the issue
      might be coming from via Chrome DevTools.
        - One of the most helpful things you can do is to purposefully [throttle
          your CPU in Chrome DevTools](https://stackoverflow.com/a/34943525)
          while capturing a performance trace. This will get you closer to
          understanding how your app performs under lower-powered hardware and
          can help you identify bottlenecks quickly.
"""

st.markdown(DOCS)
