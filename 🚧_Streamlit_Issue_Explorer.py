from pathlib import Path

import streamlit as st

# We cannot change the script name since its not possible to change the main script on community cloud.
ASSETS_FOLDER = Path(__file__).parent / "app" / "assets"

st.logo(ASSETS_FOLDER / "streamlit-logo.svg", size="small")
page = st.navigation(
    [
        st.Page(
            "./app/issue_explorer.py", title="Issue Explorer", icon="🚧", default=True
        ),
        st.Page(
            "./app/open_issues.py",
            title="Open Issues",
            icon="🗃",
            url_path="Open_Issues",
        ),
        st.Page("./app/interrupt_rotation.py", title="Interrupt Rotation", icon="🩺"),
        st.Page("./app/issue_reactions.py", title="Issue Reactions", icon="🫶"),
        st.Page("./app/company_requests.py", title="Company Requests", icon="🏢"),
        st.Page("./app/flaky_tests.py", title="Flaky Tests", icon="🧫"),
        st.Page("./app/wheel_size.py", title="Wheel Size", icon="🛞"),
        st.Page(
            "./app/test_coverage_python.py",
            title="Test Coverage (Python)",
            icon="☂️",
            url_path="Test_Coverage_(Python)",
        ),
        st.Page(
            "./app/test_coverage_frontend.py",
            title="Test Coverage (Frontend)",
            icon="☂️",
            url_path="Test_Coverage_(Frontend)",
        ),
        st.Page("./app/community_prs.py", title="Community PRs", icon="👥"),
        st.Page("./app/spec_renderer.py", title="Spec Renderer", icon="🔧"),
        st.Page(
            "./app/frontend_bundle_analysis.py",
            title="Frontend Bundle Analysis",
            icon="📦",
        ),
        st.Page("./app/github_stats.py", title="GitHub Stats", icon="📊"),
        st.Page("./app/bug_explorer.py", title="Bug Prioritization", icon="🐛"),
        st.Page(
            "./app/perf/playwright_performance_runs.py",
            title="Performance - Playwright",
            icon="🎭",
            url_path="playwright",
        ),
        st.Page(
            "./app/perf/pytest_benchmark_runs.py",
            title="Performance - Pytest",
            icon="🧪",
            url_path="pytest",
        ),
        st.Page(
            "./app/perf/lighthouse_runs.py",
            title="Performance - Lighthouse",
            icon="💡",
            url_path="lighthouse",
        ),
    ]
)
page.run()
