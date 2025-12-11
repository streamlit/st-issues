import streamlit as st

pages = {
    "Playwright": [
        st.Page(
            "playwright_performance_runs.py",
            title="Playwright Performance Runs",
            icon="🚀",
        ),
        st.Page(
            "playwright_metrics_explorer.py",
            title="Playwright Metrics Explorer",
            icon="🔍",
        ),
        st.Page(
            "playwright_interpreting_results.py",
            title="Interpreting Playwright Performance Results",
            icon="📊",
        ),
        st.Page(
            "playwright_writing_a_test.py",
            title="Writing a Playwright Performance Test",
            icon="📝",
        ),
    ],
    "Pytest": [
        st.Page(
            "pytest_benchmark_runs.py",
            title="Pytest Benchmark Runs",
            icon="🚀",
        ),
        st.Page(
            "pytest_interpreting_results.py",
            title="Interpreting Pytest Benchmark Results",
            icon="📊",
        ),
        st.Page(
            "pytest_writing_a_test.py",
            title="Writing a Pytest Benchmark Test",
            icon="📝",
        ),
    ],
    "Lighthouse": [
        st.Page(
            "lighthouse_runs.py",
            title="Lighthouse Runs",
            icon="🚀",
        ),
        st.Page(
            "lighthouse_interpreting_results.py",
            title="Interpreting Lighthouse Results",
            icon="📊",
        ),
        st.Page(
            "lighthouse_writing_a_test.py",
            title="Writing a Lighthouse Test",
            icon="📝",
        ),
        # st.Page("lighthouse_prs.py", title="Open PRs", icon="💻"),
    ],
}

pg = st.navigation(pages)
pg.run()
