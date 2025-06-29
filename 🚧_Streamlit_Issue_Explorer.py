import streamlit as st

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
        st.Page("./app/issue_leaderboard.py", title="Issue Leaderboard", icon="🏆"),
        st.Page("./app/issue_reactions.py", title="Issue Reactions", icon="🫶"),
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
    ]
)
page.run()
