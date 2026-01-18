from __future__ import annotations

from typing import Any

import pandas as pd
import requests
import streamlit as st

from app.utils.github_utils import get_headers, get_issue_comments, get_issue_data

st.set_page_config(
    page_title="Company Requests",
    page_icon="🏢",
)

st.title("🏢 Company Requests")
st.caption("Analyze which companies engaged with a GitHub issue through reactions and comments.")

# Input field
issue_input = st.text_input(
    "Issue Number or URL",
    placeholder="Enter issue number (e.g., 1234) or GitHub URL",
)

# Extract issue number from input
issue_number = None
if issue_input:
    issue_input = issue_input.strip()

    # Check if it's a GitHub URL
    if "github.com/streamlit/streamlit/issues/" in issue_input:
        try:
            # Extract issue number from URL
            issue_number = issue_input.split("/issues/")[-1].split("/")[0].split("?")[0].split("#")[0]
        except (IndexError, ValueError):
            st.error("Invalid GitHub URL format")
            st.stop()
    else:
        # Assume it's just an issue number
        issue_number = issue_input

if issue_number:
    # Validate issue number
    if not issue_number.isdigit():
        st.error("Please enter a valid issue number")
        st.stop()

    issue_num = int(issue_number)

    # Fetch issue data first to validate it exists
    with st.spinner(f"Fetching issue #{issue_num}..."):
        issue_data = get_issue_data("streamlit/streamlit", issue_number)

        if not issue_data:
            st.error(f"Issue #{issue_num} not found")
            st.stop()

    # Display issue info
    st.subheader(f"{issue_data.get('title', 'Untitled')}")

    if issue_data.get("state") == "closed":
        st.badge("Closed", icon=":material/check_circle:", color="violet")
    else:
        st.badge("Open", icon=":material/circle:", color="green")

    # Fetch reactions
    @st.cache_data(ttl=60 * 60, show_spinner=False)
    def fetch_issue_reactions(issue_number: int) -> list[dict[str, Any]]:
        """Fetch all reactions for an issue."""
        reactions = []
        page = 1

        while True:
            try:
                response = requests.get(
                    f"https://api.github.com/repos/streamlit/streamlit/issues/{issue_number}/reactions?per_page=100&page={page}",
                    headers=get_headers(),
                    timeout=30,
                )

                if response.status_code == 200:
                    data = response.json()
                    if not data:
                        break
                    reactions.extend(data)
                    page += 1
                else:
                    if response.status_code != 404:
                        st.error(f"Failed to fetch reactions: {response.status_code}")
                    break
            except Exception as e:
                st.error(f"Error fetching reactions: {e}")
                break

        return reactions

    @st.cache_data(ttl=60 * 60, show_spinner=False)
    def fetch_user_info(username: str) -> dict[str, Any] | None:
        """Fetch detailed user information including company."""
        try:
            response = requests.get(
                f"https://api.github.com/users/{username}",
                headers=get_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    # Collect all engagement data
    engagement_data = []

    # Fetch reactions
    with st.spinner("Fetching reactions..."):
        reactions = fetch_issue_reactions(issue_num)

        # Process reactions
        for reaction in reactions:
            user = reaction.get("user", {})
            username = user.get("login", "Unknown")

            # Get user details for company info
            user_info = fetch_user_info(username)
            company = None
            if user_info:
                company = user_info.get("company", None)
                # Remove leading @ from company name
                if company and company.startswith("@"):
                    company = company[1:]

            # Map reaction content to emoji
            reaction_emoji_map = {
                "+1": "👍",
                "-1": "👎",
                "laugh": "😄",
                "confused": "😕",
                "heart": "❤️",
                "hooray": "🎉",
                "rocket": "🚀",
                "eyes": "👀",
            }
            reaction_content = reaction.get("content", "")
            emoji = reaction_emoji_map.get(reaction_content, reaction_content)

            engagement_data.append(
                {
                    "Username": username,
                    "Company": company or "—",
                    "Engagement": emoji,
                    "Avatar": user.get("avatar_url", ""),
                    "Profile": f"https://github.com/{username}",
                }
            )

    # Fetch comments
    with st.spinner("Fetching comments..."):
        comments = get_issue_comments("streamlit/streamlit", issue_number)

        if comments:
            # Process comments
            for comment in comments:
                user = comment.get("user", {})
                username = user.get("login", "Unknown")

                # Get user details for company info
                user_info = fetch_user_info(username)
                company = None
                if user_info:
                    company = user_info.get("company", None)
                    # Remove leading @ from company name
                    if company and company.startswith("@"):
                        company = company[1:]

                engagement_data.append(
                    {
                        "Username": username,
                        "Company": company or "—",
                        "Engagement": "Comment",
                        "Avatar": user.get("avatar_url", ""),
                        "Profile": f"https://github.com/{username}",
                    }
                )

    # Create DataFrame
    if engagement_data:
        df = pd.DataFrame(engagement_data)

        # Normalize data before grouping (trim whitespace)
        df["Company"] = df["Company"].str.strip()
        df["Username"] = df["Username"].str.strip()

        # Group by username and merge engagements
        # Use first avatar and profile in case they differ
        df_grouped = df.groupby(["Username", "Company"], as_index=False).agg(
            {
                "Engagement": ", ".join,
                "Avatar": "first",
                "Profile": "first",
            }
        )

        # Filter to only show users with companies and sort by company
        df_grouped = df_grouped[df_grouped["Company"] != "—"].sort_values("Company")

        # Display metrics (using original df for accurate counts)
        col1, col2, col3, col4 = st.columns(4)

        # Update metrics to reflect filtered data
        unique_users = df_grouped["Username"].nunique()
        total_reactions = len(df[(df["Engagement"] != "Comment") & (df["Company"] != "—")])
        total_comments = len(df[(df["Engagement"] == "Comment") & (df["Company"] != "—")])
        companies = df_grouped["Company"].nunique()

        with col1:
            st.metric("Unique Users", unique_users)
        with col2:
            st.metric("Reactions", total_reactions)
        with col3:
            st.metric("Comments", total_comments)
        with col4:
            st.metric("Companies", companies)

        # Check if we have any data after filtering
        if df_grouped.empty:
            st.info("No users with company information found for this issue")
            st.stop()

        # Display the dataframe
        st.subheader("Engagement Details")

        # Configure column display
        column_config = {
            "Username": st.column_config.TextColumn("Username", width="medium"),
            "Company": st.column_config.TextColumn("Company", width="medium"),
            "Engagement": st.column_config.TextColumn("Engagement", width="small"),
            "Avatar": st.column_config.ImageColumn("Avatar", width="small"),
            "Profile": st.column_config.LinkColumn(
                "Profile",
                display_text="View profile",
                width="small",
            ),
        }

        # Show dataframe (using grouped data)
        st.dataframe(
            df_grouped[["Avatar", "Username", "Company", "Engagement", "Profile"]],
            column_config=column_config,
            width="stretch",
            hide_index=True,
            height=600,
        )

        # Reaction breakdown
        if total_reactions > 0:
            st.subheader("Reaction Breakdown")
            reaction_counts = df[df["Engagement"] != "Comment"]["Engagement"].value_counts()

            # Create columns for reaction display
            cols = st.columns(len(reaction_counts))
            for i, (reaction_name, count) in enumerate(reaction_counts.items()):
                with cols[i]:
                    st.metric(str(reaction_name), count)

        # Company breakdown
        if companies > 0:
            st.subheader("Top Companies")
            company_counts = df_grouped["Company"].value_counts().head(10)

            # Create a bar chart
            st.bar_chart(company_counts)

    else:
        st.info("No engagement found for this issue")
