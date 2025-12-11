import streamlit as st

TITLE = "Streamlit Performance - Writing a Pytest Benchmark Test"

st.set_page_config(page_title=TITLE)

st.header(TITLE)

DOCS = """
## When to Use a Pytest Benchmark Test

✅ When you want to test the performance of a specific piece of Python code.

✅ When you need to compare the performance of different implementations of a
function.

✅ When you want to ensure that performance regressions are caught during
development.

❌ If you want to test a function that is I/O bound, a benchmark test may not be
best suited due to the variability in I/O performance.

❌ If you want to measure the user experience performance of a Streamlit app in
the browser, utilize [Playwright Performance Testing](playwright_writing_a_test)
instead.

## How to write a Pytest Benchmark test in the Streamlit codebase

1. Add the `@pytest.mark.usefixtures("benchmark")` decorator to the test
   function.
2. Utilize the `benchmark` callable object to benchmark the code you want to
   test.

    - If the test is unittest-style, then utilize `self.benchmark`
    - If the test is pytest-style, then utilize the `benchmark` argument given to the test function
    - For example, to benchmark a function `my_function`, you can write:

     ```python
     # unittest-style test
     @pytest.mark.usefixtures("benchmark")
     def test_my_function():
         self.benchmark(my_function, "some_string_arg")

     ```

     ```python
     # pytest-style test
     @pytest.mark.usefixtures("benchmark")
     def test_my_function(benchmark):
         benchmark(my_function, "some_string_arg")

     ```

See the [pytest-benchmark usage
docs](https://pytest-benchmark.readthedocs.io/en/stable/usage.html) for in-depth
examples.

"""

st.markdown(DOCS)
