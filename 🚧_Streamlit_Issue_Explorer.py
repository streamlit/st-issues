from pathlib import Path

import streamlit as st

# We cannot change the script name since its not possible to change the main script on community cloud.
ASSETS_FOLDER = Path(__file__).parent / "app" / "assets"

st.logo(ASSETS_FOLDER / "streamlit-logo.svg", size="small")
page = st.navigation(
    {
        "Issue management": [
            st.Page("./app/issue_explorer.py", title="Issue explorer", icon=":material/construction:", default=True),
            st.Page(
                "./app/open_issues.py",
                title="Open issues",
                icon=":material/inbox:",
                url_path="Open_Issues",
            ),
            st.Page("./app/bug_explorer.py", title="Bug prioritization", icon=":material/bug_report:"),
            st.Page("./app/issue_reactions.py", title="Issue reactions", icon=":material/add_reaction:"),
            st.Page("./app/company_requests.py", title="Company requests", icon=":material/apartment:"),
        ],
        "Operations dashboard": [
            st.Page("./app/interrupt_rotation.py", title="Interrupt rotation", icon=":material/stethoscope:"),
            st.Page("./app/ai_workflow_usage.py", title="AI workflow usage", icon=":material/smart_toy:"),
        ],
        "Test health": [
            st.Page("./app/flaky_tests.py", title="Flaky tests", icon=":material/flaky:"),
            st.Page(
                "./app/test_coverage_python.py",
                title="Python test coverage",
                icon=":material/umbrella:",
                url_path="Test_Coverage_(Python)",
            ),
            st.Page(
                "./app/test_coverage_frontend.py",
                title="Frontend test coverage",
                icon=":material/umbrella:",
                url_path="Test_Coverage_(Frontend)",
            ),
            st.Page(
                "./app/playwright_test_stats.py",
                title="Playwright test stats",
                icon=":material/theater_comedy:",
                url_path="playwright_stats",
            ),
        ],
        "Performance and size": [
            st.Page(
                "./app/perf/playwright_performance_runs.py",
                title="Playwright performance",
                icon=":material/theater_comedy:",
                url_path="playwright",
            ),
            st.Page(
                "./app/perf/pytest_benchmark_runs.py",
                title="Pytest performance",
                icon=":material/science:",
                url_path="pytest",
            ),
            st.Page(
                "./app/perf/lighthouse_runs.py",
                title="Lighthouse performance",
                icon=":material/lightbulb:",
                url_path="lighthouse",
            ),
            st.Page(
                "./app/frontend_bundle_analysis.py",
                title="Frontend bundle analysis",
                icon=":material/inventory_2:",
            ),
            st.Page("./app/wheel_size.py", title="Wheel size", icon=":material/package_2:"),
            st.Page("./app/load_testing.py", title="Load testing", icon=":material/bolt:"),
        ],
        "Collaboration insights": [
            st.Page("./app/community_prs.py", title="Community PRs", icon=":material/groups:"),
            st.Page("./app/github_stats.py", title="GitHub stats", icon=":material/bar_chart:"),
        ],
        "Tools": [
            st.Page("./app/spec_renderer.py", title="Spec renderer", icon=":material/build:"),
            st.Page("./app/agent_wiki_explorer.py", title="Agent wiki explorer", icon=":material/menu_book:"),
        ],
    }
)
page.run()
