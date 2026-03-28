from pathlib import Path

import streamlit as st

# We cannot change the script name since its not possible to change the main script on community cloud.
ASSETS_FOLDER = Path(__file__).parent / "app" / "assets"

st.logo(ASSETS_FOLDER / "streamlit-logo.svg", size="small")
page = st.navigation(
    {
        "Issue management": [
            st.Page("./app/issue_explorer.py", title="Issue explorer", icon="🚧", default=True),
            st.Page(
                "./app/open_issues.py",
                title="Open issues",
                icon="🗃",
                url_path="Open_Issues",
            ),
            st.Page("./app/bug_explorer.py", title="Bug prioritization", icon="🐛"),
            st.Page("./app/issue_reactions.py", title="Issue reactions", icon="🫶"),
            st.Page("./app/company_requests.py", title="Company requests", icon="🏢"),
        ],
        "Operations dashboard": [
            st.Page("./app/interrupt_rotation.py", title="Interrupt rotation", icon="🩺"),
        ],
        "Test health": [
            st.Page("./app/flaky_tests.py", title="Flaky tests", icon="🧫"),
            st.Page(
                "./app/test_coverage_python.py",
                title="Python test coverage",
                icon="☂️",
                url_path="Test_Coverage_(Python)",
            ),
            st.Page(
                "./app/test_coverage_frontend.py",
                title="Frontend test coverage",
                icon="☂️",
                url_path="Test_Coverage_(Frontend)",
            ),
            st.Page(
                "./app/playwright_test_stats.py",
                title="Playwright test stats",
                icon="🎭",
                url_path="playwright_stats",
            ),
        ],
        "Performance and size": [
            st.Page(
                "./app/perf/playwright_performance_runs.py",
                title="Playwright performance",
                icon="🎭",
                url_path="playwright",
            ),
            st.Page(
                "./app/perf/pytest_benchmark_runs.py",
                title="Pytest performance",
                icon="🧪",
                url_path="pytest",
            ),
            st.Page(
                "./app/perf/lighthouse_runs.py",
                title="Lighthouse performance",
                icon="💡",
                url_path="lighthouse",
            ),
            st.Page(
                "./app/frontend_bundle_analysis.py",
                title="Frontend bundle analysis",
                icon="📦",
            ),
            st.Page("./app/wheel_size.py", title="Wheel size", icon="🛞"),
            st.Page("./app/load_testing.py", title="Load testing", icon="⚡"),
        ],
        "Collaboration insights": [
            st.Page("./app/community_prs.py", title="Community PRs", icon="👥"),
            st.Page("./app/github_stats.py", title="GitHub stats", icon="📊"),
        ],
        "Tools": [
            st.Page("./app/spec_renderer.py", title="Spec renderer", icon="🔧"),
            st.Page("./app/agent_wiki_explorer.py", title="Agent wiki explorer", icon="📚"),
        ],
    }
)
page.run()
