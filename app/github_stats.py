import re
import subprocess
import tempfile
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils.github_graphql_utils import fetch_merged_pr_metrics
from app.utils.github_utils import (
    ACTIVTE_STREAMLIT_TEAM_MEMBERS,
    STREAMLIT_TEAM_MEMBERS,
    get_all_github_issues,
    get_count_issues_commented_by_user,
)

# Define the repo URL
GITHUB_REPO = "streamlit/streamlit"

REACTION_EMOJI = {
    "+1": "👍",
    "-1": "👎",
    "confused": "😕",
    "eyes": "👀",
    "heart": "❤️",
    "hooray": "🎉",
    "laugh": "😄",
    "rocket": "🚀",
}


def reactions_to_str(reactions):
    return " ".join(
        [
            f"{reactions[name]} {emoji}"
            for name, emoji in REACTION_EMOJI.items()
            if reactions[name] > 0
        ]
    )


def get_issue_type(labels):
    is_bug = any(label["name"] == "type:bug" for label in labels)
    is_enhancement = any(label["name"] == "type:enhancement" for label in labels)

    if is_bug and is_enhancement:
        return ["Bug", "Enhancement"]
    elif is_bug:
        return "Bug"
    elif is_enhancement:
        return "Enhancement"
    else:
        return []


def get_issue_emoji(labels):
    label_names = [label["name"] for label in labels]
    if "type:enhancement" in label_names:
        return "✨"
    elif "type:bug" in label_names:
        return "🚨"
    elif "type:docs" in label_names:
        return "📚"
    elif "type:kudos" in label_names:
        return "🙏"
    else:
        return "❓"


title_row = st.container(
    horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
)
with title_row:
    st.title("📊 GitHub Stats")
    if st.button(":material/refresh: Refresh Data", type="tertiary"):
        fetch_merged_pr_metrics.clear()
        get_all_github_issues.clear()

st.caption("GitHub-based metrics aggregated from issue and pull request data.")

contribution_metrics = st.query_params.get("contribution", None)
selected_metrics = st.segmented_control(
    "Metric Collection",
    options=["Team Productivity Metrics", "Contribution Metrics"],
    label_visibility="collapsed",
    width="stretch",
    default="Team Productivity Metrics"
    if not contribution_metrics
    else "Contribution Metrics",
)

with st.sidebar:
    today = date.today()

    since_input = st.date_input(
        "Since",
        value=date.fromisoformat("2022-04-01"),
        max_value=today,
        help="Include PRs and issues closed on or after this date.",
    )
    exclude_bot_prs = st.toggle("Exclude Bot PRs")


@st.cache_data(show_spinner="Cloning and analyzing repository...")
def get_git_fame_stats():
    # Use a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Clone the repository
        subprocess.run(
            ["git", "clone", "https://github.com/" + GITHUB_REPO, temp_dir],
            check=True,
            capture_output=True,
        )

        import gitfame._gitfame

        # Run git-fame
        # churn=gitfame._gitfame.CHURN_SLOC is needed to calculate surviving LOC
        stats = gitfame._gitfame._get_auth_stats(
            temp_dir,
            include_files=re.compile(r".*"),
            exclude_files=re.compile(r".*yarn\.lock|NOTICES"),
            churn=gitfame._gitfame.CHURN_SLOC,
            show={"name", "email"},
        )

    return stats


@st.cache_data(ttl=60 * 60 * 72, show_spinner="Fetching PR metrics...")
def fetch_pr_metrics(merged_since: date):
    return fetch_merged_pr_metrics(merged_since=merged_since)


merged_prs_df = fetch_pr_metrics(merged_since=since_input)
if exclude_bot_prs:
    merged_prs_df = merged_prs_df[~merged_prs_df["from_bot"]]

if selected_metrics == "Contribution Metrics":
    st.markdown("#### :material/merge: Merged PRs by Authors")

    st.caption(
        f"GitHub users who have authored the most merged pull requests on `streamlit/streamlit` merged into `develop` since {since_input.strftime('%Y/%m/%d')}. "
        f"Total merged PRs: **{len(merged_prs_df)}.**"
    )

    if not merged_prs_df.empty:
        # Calculate feature and bugfix flags
        merged_prs_df["is_feature"] = merged_prs_df["labels"].apply(
            lambda labels: 1
            if "change:feature" in labels and "impact:users" in labels
            else 0
        )
        merged_prs_df["is_bugfix"] = merged_prs_df["labels"].apply(
            lambda labels: 1
            if "change:bugfix" in labels and "impact:users" in labels
            else 0
        )

        # Group by author and calculate stats
        author_stats = (
            merged_prs_df.groupby("author")
            .agg(
                prs_merged=("pr_number", "count"),
                total_loc_changes=("loc_changes", "sum"),
                total_additions=("additions", "sum"),
                total_deletions=("deletions", "sum"),
                merged_features=("is_feature", "sum"),
                merged_bugfixes=("is_bugfix", "sum"),
            )
            .reset_index()
            .sort_values("prs_merged", ascending=False)
            .reset_index(drop=True)
        )

        # Add links
        author_stats["Show PRs"] = author_stats["author"].apply(
            lambda x: f"https://github.com/streamlit/streamlit/pulls?q=is%3Apr+is%3Amerged+author%3A{x}+merged%3A>={since_input.strftime('%Y-%m-%d')}"
        )
        author_stats["author"] = author_stats["author"].apply(
            lambda x: f"https://github.com/{x}"
        )

        st.dataframe(
            author_stats.head(20),
            column_config={
                "author": st.column_config.LinkColumn(
                    "Author", display_text="github.com/([^/]+)"
                ),
                "prs_merged": st.column_config.NumberColumn("Merged PRs"),
                "merged_features": st.column_config.NumberColumn("Feature PRs"),
                "merged_bugfixes": st.column_config.NumberColumn("Bugfix PRs"),
                "total_loc_changes": st.column_config.NumberColumn("LOC Changed"),
                "total_additions": st.column_config.NumberColumn("LOC Additions"),
                "total_deletions": st.column_config.NumberColumn("LOC Deletions"),
                "Show PRs": st.column_config.LinkColumn(
                    display_text=":material/open_in_new:"
                ),
            },
            hide_index=True,
        )
    else:
        st.info("No merged PRs found for the selected period.")

    st.markdown("#### :material/rate_review: Merged PRs by Reviewers")

    st.caption(
        f"GitHub users who have reviewed the most pull requests on `streamlit/streamlit` merged into `develop` since {since_input.strftime('%Y/%m/%d')}. "
        f"Total merged PRs: **{len(merged_prs_df)} {'(including bot PRs)' if not exclude_bot_prs else ''}.**"
    )

    if not merged_prs_df.empty:
        # Explode reviewers to count each reviewer separately
        reviewers_exploded = merged_prs_df.copy().explode("reviewers")

        # Filter out None values if any
        reviewers_exploded = reviewers_exploded.dropna(subset=["reviewers"])

        # Count reviews by reviewer
        reviewer_counts = (
            reviewers_exploded.groupby("reviewers")
            .size()
            .reset_index(name="PRs Reviewed")
            .sort_values("PRs Reviewed", ascending=False)
            .reset_index(drop=True)
        )

        # Calculate % of others' PRs reviewed
        total_prs = len(merged_prs_df)
        author_counts_map = merged_prs_df["author"].value_counts().to_dict()

        def calculate_percentage(row):
            reviewer = row["reviewers"]
            prs_reviewed = row["PRs Reviewed"]
            prs_authored = author_counts_map.get(reviewer, 0)
            eligible_prs = total_prs - prs_authored
            if eligible_prs > 0:
                return prs_reviewed / eligible_prs
            return 0

        reviewer_counts["% of Others' PRs"] = reviewer_counts.apply(
            calculate_percentage, axis=1
        )

        # Add links
        reviewer_counts["Show PRs"] = reviewer_counts["reviewers"].apply(
            lambda x: f"https://github.com/streamlit/streamlit/pulls?q=is%3Apr+is%3Amerged+reviewed-by%3A{x}+merged%3A>={since_input.strftime('%Y-%m-%d')}"
        )
        reviewer_counts["reviewers"] = reviewer_counts["reviewers"].apply(
            lambda x: f"https://github.com/{x}"
        )

        selection = st.dataframe(
            reviewer_counts,
            column_config={
                "reviewers": st.column_config.LinkColumn(
                    display_text="github.com/([^/]+)"
                ),
                "% of Others' PRs": st.column_config.NumberColumn(
                    format="percent",
                    help="Percentage of PRs reviewed by the user that were not authored by the user",
                ),
                "Show PRs": st.column_config.LinkColumn(
                    display_text=":material/open_in_new:"
                ),
            },
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        if selection.selection.rows:
            selected_index = selection.selection.rows[0]
            selected_reviewer_url = reviewer_counts.iloc[selected_index]["reviewers"]
            selected_reviewer = selected_reviewer_url.split("/")[-1]

            # Filter PRs reviewed by the selected user
            # We check if the selected reviewer is in the list of reviewers for each PR
            reviewer_prs = merged_prs_df[
                merged_prs_df["reviewers"].apply(lambda x: selected_reviewer in x)
            ].copy()

            if not reviewer_prs.empty:
                st.markdown(f"##### PRs reviewed by {selected_reviewer}")

                detailed_pr_df = pd.DataFrame(
                    {
                        "Title": reviewer_prs["title"],
                        "Link": reviewer_prs["url"],
                        "Merged on": reviewer_prs["merge_date"].dt.date,
                        "Author": reviewer_prs["author"].apply(
                            lambda x: f"https://github.com/{x}"
                        ),
                    }
                )

                detailed_pr_df = detailed_pr_df.sort_values(
                    "Merged on", ascending=False
                )

                st.dataframe(
                    detailed_pr_df,
                    column_config={
                        "Title": st.column_config.TextColumn(width="large"),
                        "Link": st.column_config.LinkColumn(display_text="Open PR"),
                        "Merged on": st.column_config.DateColumn(format="MMM DD, YYYY"),
                        "Author": st.column_config.LinkColumn(
                            display_text="github.com/([^/]+)"
                        ),
                    },
                    hide_index=True,
                )

    else:
        st.info("No merged PRs found for the selected period.")

    st.markdown("#### :material/crowdsource: Merged Community PRs by Reviewers")

    if not merged_prs_df.empty:
        # Filter for community PRs
        community_prs_df = merged_prs_df[
            ~merged_prs_df["author"].isin(STREAMLIT_TEAM_MEMBERS)
        ].copy()
        # Always exclude bot PRs
        community_prs_df = community_prs_df[~community_prs_df["from_bot"]]

        st.caption(
            f"GitHub users who have reviewed the most pull requests on `streamlit/streamlit` merged into `develop` since {since_input.strftime('%Y/%m/%d')} that were authored by community members. "
            f"Total merged community PRs: **{len(community_prs_df)}.**"
        )

        if not community_prs_df.empty:
            # Explode reviewers to count each reviewer separately
            community_reviewers_exploded = community_prs_df.explode("reviewers")

            # Filter out None values if any
            community_reviewers_exploded = community_reviewers_exploded.dropna(
                subset=["reviewers"]
            )

            # Count reviews by reviewer
            community_reviewer_counts = (
                community_reviewers_exploded.groupby("reviewers")
                .size()
                .reset_index(name="PRs Reviewed")
                .sort_values("PRs Reviewed", ascending=False)
                .reset_index(drop=True)
            )

            # Add links
            community_reviewer_counts["Show PRs"] = community_reviewer_counts[
                "reviewers"
            ].apply(
                lambda x: f"https://github.com/streamlit/streamlit/pulls?q=is%3Apr+is%3Amerged+reviewed-by%3A{x}+merged%3A>={since_input.strftime('%Y-%m-%d')}"
            )
            community_reviewer_counts["reviewers"] = community_reviewer_counts[
                "reviewers"
            ].apply(lambda x: f"https://github.com/{x}")

            community_selection = st.dataframe(
                community_reviewer_counts.head(20),
                column_config={
                    "reviewers": st.column_config.LinkColumn(
                        "GitHub User", display_text="github.com/([^/]+)"
                    ),
                    "Show PRs": st.column_config.LinkColumn(
                        display_text=":material/open_in_new:"
                    ),
                },
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="community_reviewers_selection",
            )

            if community_selection.selection.rows:
                selected_community_index = community_selection.selection.rows[0]
                selected_community_reviewer_url = community_reviewer_counts.iloc[
                    selected_community_index
                ]["reviewers"]
                selected_community_reviewer = selected_community_reviewer_url.split(
                    "/"
                )[-1]

                # Filter PRs reviewed by the selected user
                community_reviewer_prs = community_prs_df[
                    community_prs_df["reviewers"].apply(
                        lambda x: selected_community_reviewer in x
                    )
                ].copy()

                if not community_reviewer_prs.empty:
                    st.markdown(
                        f"##### Community PRs reviewed by {selected_community_reviewer}"
                    )

                    detailed_community_pr_df = pd.DataFrame(
                        {
                            "Title": community_reviewer_prs["title"],
                            "Link": community_reviewer_prs["url"],
                            "Merged on": community_reviewer_prs["merge_date"].dt.date,
                            "Author": community_reviewer_prs["author"].apply(
                                lambda x: f"https://github.com/{x}"
                            ),
                        }
                    )

                    detailed_community_pr_df = detailed_community_pr_df.sort_values(
                        "Merged on", ascending=False
                    )

                    st.dataframe(
                        detailed_community_pr_df,
                        column_config={
                            "Title": st.column_config.TextColumn(width="large"),
                            "Link": st.column_config.LinkColumn(display_text="Open PR"),
                            "Merged on": st.column_config.DateColumn(
                                format="MMM DD, YYYY"
                            ),
                            "Author": st.column_config.LinkColumn(
                                display_text="github.com/([^/]+)"
                            ),
                        },
                        hide_index=True,
                    )
        else:
            st.info("No merged community PRs found for the selected period.")
    else:
        st.info("No merged PRs found for the selected period.")

    st.markdown("#### :material/thumbs_up_double: Issue Closers by Reactions")

    # Process the data
    all_issues_df = pd.DataFrame(
        [issue for issue in get_all_github_issues() if "pull_request" not in issue]
    )

    all_issues_df["closed_at"] = pd.to_datetime(all_issues_df["closed_at"])
    all_issues_df["created_at"] = pd.to_datetime(all_issues_df["created_at"])

    all_issues_df["total_reactions"] = all_issues_df["reactions"].apply(
        lambda x: x["total_count"]
    )

    # Closers who closed issues with the most reactions
    closers_df = all_issues_df.copy()
    if since_input:
        closers_df = closers_df[closers_df["closed_at"].dt.date >= since_input]

    closers_df["closed_by_login"] = closers_df["closed_by"].apply(
        lambda x: x.get("login", "") if isinstance(x, dict) else ""
    )
    # Remove entries without a valid closer
    closers_df = closers_df[closers_df["closed_by_login"] != ""]

    # Calculate issue types
    closers_df["is_bug"] = closers_df["labels"].apply(
        lambda x: 1 if any(l["name"] == "type:bug" for l in x) else 0
    )
    closers_df["is_enhancement"] = closers_df["labels"].apply(
        lambda x: 1 if any(l["name"] == "type:enhancement" for l in x) else 0
    )
    closers_df["is_other"] = closers_df["labels"].apply(
        lambda x: 1
        if not any(l["name"] in ["type:bug", "type:enhancement"] for l in x)
        else 0
    )

    closers_container = st.container(gap=None)
    row = closers_container.container(horizontal=True)
    title_container = row.container()

    filtered_closers_df = closers_df

    if filtered_closers_df.empty:
        with title_container:
            st.caption(
                ":material/person: No issues found for the current filters and closer selection."
            )
    else:
        closers_stats = (
            filtered_closers_df.groupby("closed_by_login")
            .agg(
                total_reactions=("total_reactions", "sum"),
                issues_closed=("total_reactions", "count"),
                bugs_closed=("is_bug", "sum"),
                enhancements_closed=("is_enhancement", "sum"),
                others_closed=("is_other", "sum"),
            )
            .reset_index()
            .rename(
                columns={
                    "closed_by_login": "Closer",
                    "total_reactions": "Total reactions",
                    "issues_closed": "Issues closed",
                    "bugs_closed": "Bugs closed",
                    "enhancements_closed": "Enhancements closed",
                    "others_closed": "Others closed",
                }
            )
        )
        closers_stats["Average reactions per issue"] = (
            closers_stats["Total reactions"] / closers_stats["Issues closed"]
        )
        closers_stats = closers_stats.sort_values(
            "Total reactions", ascending=False
        ).reset_index(drop=True)

        # Transform Closer to URL
        closers_stats["Closer"] = closers_stats["Closer"].apply(
            lambda x: f"https://github.com/{x}"
        )

        unique_closers = len(closers_stats)

        with title_container:
            st.caption(
                f"GitHub users sorted by total reactions on issues they closed - via pull request or manual closing - since {since_input.strftime('%Y/%m/%d')}. "
                f"Total closed reactions: **{closers_stats['Total reactions'].sum()}**. Total closed issues: **{closers_stats['Issues closed'].sum()}**. "
                f"Total closed bugs: **{closers_stats['Bugs closed'].sum()}**. Total closed enhancements: **{closers_stats['Enhancements closed'].sum()}**. "
            )

        selection = st.dataframe(
            closers_stats,
            column_config={
                "Closer": st.column_config.LinkColumn(
                    display_text="github.com/([^/]+)"
                ),
                "Total reactions": st.column_config.NumberColumn(),
                "Issues closed": st.column_config.NumberColumn(),
                "Bugs": st.column_config.NumberColumn(),
                "Enhancements": st.column_config.NumberColumn(),
                "Others": st.column_config.NumberColumn(),
                "Average reactions per issue": st.column_config.NumberColumn(
                    format="%.2f"
                ),
            },
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        if selection.selection.rows:
            selected_index = selection.selection.rows[0]
            selected_closer_url = closers_stats.iloc[selected_index]["Closer"]
            selected_closer = selected_closer_url.split("/")[-1]

            # Filter issues closed by the selected user
            # We need to go back to the filtered_closers_df which has the raw data
            closer_issues = filtered_closers_df[
                filtered_closers_df["closed_by_login"] == selected_closer
            ].copy()

            if not closer_issues.empty:
                issues_container = st.container(gap=None)
                issues_row = issues_container.container(horizontal=True)
                issues_title_container = issues_row.container()

                with issues_row.popover("Modify", width="content"):
                    min_reactions = st.number_input(
                        "Minimum reactions", min_value=0, value=0, step=1
                    )

                if min_reactions > 0:
                    closer_issues = closer_issues[
                        closer_issues["total_reactions"] >= min_reactions
                    ]

                with issues_title_container:
                    st.markdown(f"##### Issues closed by {selected_closer}")

                # Prepare the detailed dataframe
                detailed_df = pd.DataFrame(
                    {
                        "Title": closer_issues.apply(
                            lambda x: f"{get_issue_emoji(x['labels'])} {x['title']}",
                            axis=1,
                        ),
                        "Reactions": closer_issues["total_reactions"],
                        "Closed on": closer_issues["closed_at"].dt.date,
                        "Link": closer_issues["html_url"],
                        "Comments": closer_issues["comments"],
                        "Reaction Types": closer_issues["reactions"].apply(
                            reactions_to_str
                        ),
                        "Type": closer_issues["labels"].apply(get_issue_type),
                    }
                )

                # Sort by date
                detailed_df = detailed_df.sort_values("Closed on", ascending=False)

                st.dataframe(
                    detailed_df,
                    column_config={
                        "Title": st.column_config.TextColumn(width="large"),
                        "Link": st.column_config.LinkColumn(display_text="Open Issue"),
                        "Type": st.column_config.ListColumn(),
                        "Closed on": st.column_config.DateColumn(format="MMM DD, YYYY"),
                        "Reactions": st.column_config.NumberColumn(
                            format="%d 🫶", help="Total number of reactions"
                        ),
                        "Comments": st.column_config.NumberColumn(format="%d 💬"),
                    },
                    hide_index=True,
                )

    st.markdown("#### :material/contract_edit: Issue Authors")

    st.caption(
        f"GitHub users who created the most issues on `streamlit/streamlit` since {since_input.strftime('%Y/%m/%d')}."
    )

    # Calculate top issue authors
    authors_df = all_issues_df.copy()
    authors_df["author"] = authors_df["user"].apply(
        lambda x: x.get("login", "") if isinstance(x, dict) else ""
    )
    authors_df = authors_df[authors_df["author"] != ""]

    if since_input:
        authors_df = authors_df[authors_df["created_at"].dt.date >= since_input]

    if not authors_df.empty:
        author_counts = (
            authors_df.groupby("author")
            .size()
            .reset_index(name="Issue Count")
            .sort_values("Issue Count", ascending=False)
            .reset_index(drop=True)
        )

        # Add links
        author_counts["Show Issues"] = author_counts["author"].apply(
            lambda x: f"https://github.com/streamlit/streamlit/issues?q=is%3Aissue+author%3A{x}"
        )
        author_counts["author"] = author_counts["author"].apply(
            lambda x: f"https://github.com/{x}"
        )

        st.dataframe(
            author_counts.head(15),
            column_config={
                "author": st.column_config.LinkColumn(
                    display_text="github.com/([^/]+)"
                ),
                "Issue Count": st.column_config.NumberColumn(format="%d 📝"),
                "Show Issues": st.column_config.LinkColumn(
                    display_text=":material/open_in_new:"
                ),
            },
            hide_index=True,
        )
    else:
        st.info("No issue authors found.")

    st.markdown("#### :material/comment: Issue Commenters")
    st.caption(
        "The number of unique [GitHub issues](https://github.com/streamlit/streamlit/issues) commented on by Streamlit team members."
    )
    # Fetch data for all team members
    comment_counts = []
    for member in ACTIVTE_STREAMLIT_TEAM_MEMBERS:
        count = get_count_issues_commented_by_user(member)
        if count > 0:
            comment_counts.append({"User": member, "Issues Commented On": count})

    # Create DataFrame
    commenters_df = pd.DataFrame(comment_counts)
    commenters_df["Show Issues"] = commenters_df["User"].apply(
        lambda x: f"https://github.com/streamlit/streamlit/issues?q=is%3Aissue%20commenter%3A{x}"
    )
    commenters_df["User"] = commenters_df["User"].apply(
        lambda x: f"https://github.com/{x}"
    )

    if not commenters_df.empty:
        commenters_df = commenters_df.sort_values(
            "Issues Commented On", ascending=False
        ).reset_index(drop=True)
        st.dataframe(
            commenters_df,
            column_config={
                "User": st.column_config.LinkColumn(display_text="github.com/([^/]+)"),
                "Issues Commented On": st.column_config.NumberColumn(format="%d 💬"),
                "Show Issues": st.column_config.LinkColumn(
                    display_text=":material/open_in_new:"
                ),
            },
            hide_index=True,
        )
    else:
        st.info("No data found for team members.")

    st.markdown("#### :material/donut_small: Surviving Lines of Code")

    stats = get_git_fame_stats()

    # Process stats into a DataFrame
    # stats is a dict where keys are authors and values are dicts with 'loc', 'commits', 'files'
    data = []
    total_loc = 0
    total_commits = 0
    total_files = 0

    # First pass to calculate totals
    for metrics in stats.values():
        total_loc += metrics.get("loc", 0)
        total_commits += metrics.get("commits", 0)
        total_files += len(metrics.get("files", []))

    for author_key, metrics in stats.items():
        # author_key is "Name <Email>"
        match = re.match(r"(.*) <(.*)>", author_key)
        if match:
            name = match.group(1)
            email = match.group(2)
        else:
            name = author_key
            email = ""

        loc = metrics.get("loc", 0)
        commits = metrics.get("commits", 0)
        files = len(metrics.get("files", []))

        loc_pct = (loc / total_loc * 100) if total_loc > 0 else 0
        commits_pct = (commits / total_commits * 100) if total_commits > 0 else 0
        files_pct = (files / total_files * 100) if total_files > 0 else 0

        data.append(
            {
                "User": name,
                "Surviving LOC": loc,
                "Surviving LOC %": round(loc_pct, 1),
                "Commits to Main": commits,
                "Commits to Main %": round(commits_pct, 1),
                "Touched Files": files,
                "Touched Files %": round(files_pct, 1),
            }
        )

    df = pd.DataFrame(data)
    if not df.empty:
        st.caption(
            "Surviving lines of code (LOC) measures the number of lines of code currently present "
            "in the [codebase](https://github.com/streamlit/streamlit) that were authored by each user. "
            "This is calculated by [git-fame](https://github.com/casperdcl/git-fame). "
            f"Total LOC: **{total_loc}**; Total Commits: **{total_commits}**."
        )
        df = df.sort_values(by="Surviving LOC", ascending=False).reset_index(drop=True)
        st.dataframe(
            df,
            width="stretch",
            column_config={
                "Surviving LOC %": st.column_config.NumberColumn(format="%.1f%%"),
                "Commits to Main %": st.column_config.NumberColumn(format="%.1f%%"),
                "Touched Files %": st.column_config.NumberColumn(format="%.1f%%"),
            },
            hide_index=True,
        )
    else:
        st.warning("No data found.")
elif selected_metrics == "Team Productivity Metrics":
    # --- PR Metrics ---
    st.markdown("##### :material/merge: Pull Request Metrics")
    st.caption(
        f"Metrics based on merged pull requests on `streamlit/streamlit` merged into `develop` since {since_input.strftime('%Y/%m/%d')}."
    )

    if not merged_prs_df.empty:
        # Calculate PR metrics
        total_merged_prs = len(merged_prs_df)

        # Calculate medians
        median_open_to_merge = (
            merged_prs_df["time_open_to_merge"].dt.total_seconds() / 3600
        ).median()

        median_open_to_first_review = (
            merged_prs_df["time_open_to_first_review"].dt.total_seconds() / 3600
        ).median()

        total_loc_changed = merged_prs_df["loc_changes"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Merged PRs", total_merged_prs, border=True)
        col2.metric(
            "Median Time to Merge", f"{median_open_to_merge:.1f} h", border=True
        )
        col3.metric(
            "Median Time to First Review",
            f"{median_open_to_first_review:.1f} h",
            border=True,
        )
        col4.metric("Total LOC Changed", f"{total_loc_changed:,}", border=True)

        # Monthly PR Trends
        # Prepare data for monthly trends
        merged_prs_df["merge_month"] = (
            merged_prs_df["merge_date"].dt.to_period("M").dt.to_timestamp()
        )

        # Calculate feature and bugfix flags
        merged_prs_df["is_feature"] = merged_prs_df["labels"].apply(
            lambda labels: 1
            if "change:feature" in labels and "impact:users" in labels
            else 0
        )
        merged_prs_df["is_bugfix"] = merged_prs_df["labels"].apply(
            lambda labels: 1
            if "change:bugfix" in labels and "impact:users" in labels
            else 0
        )

        # Monthly PR Stats (Counts & LOC) - Full Data
        monthly_pr_stats = (
            merged_prs_df.groupby("merge_month")
            .agg(
                merged_prs=("pr_number", "count"),
                total_additions=("additions", "sum"),
                total_deletions=("deletions", "sum"),
                merged_features=("is_feature", "sum"),
                merged_bugfixes=("is_bugfix", "sum"),
                total_review_comments=("num_review_comments", "sum"),
                total_issue_comments=("num_issue_comments", "sum"),
                median_review_comments=("num_review_comments", "median"),
                median_issue_comments=("num_issue_comments", "median"),
            )
            .reset_index()
            .rename(
                columns={
                    "merge_month": "Date",
                    "merged_prs": "Merged PRs",
                    "total_additions": "Additions",
                    "total_deletions": "Deletions",
                    "merged_features": "Features",
                    "merged_bugfixes": "Bugfixes",
                    "total_review_comments": "Total Review Comments",
                    "total_issue_comments": "Total Issue Comments",
                    "median_review_comments": "Median Review Comments",
                    "median_issue_comments": "Median Issue Comments",
                }
            )
        )

        monthly_time_stats = (
            merged_prs_df.groupby("merge_month")
            .agg(
                median_time_to_merge=(
                    "time_open_to_merge",
                    lambda x: x.dt.total_seconds().median() / 3600,
                ),
                median_time_to_first_review=(
                    "time_open_to_first_review",
                    lambda x: x.dt.total_seconds().median() / 3600,
                ),
                median_time_first_review_to_merge=(
                    "time_first_review_to_merge_or_approval",
                    lambda x: x.dt.total_seconds().median() / 3600,
                ),
            )
            .reset_index()
            .rename(
                columns={
                    "merge_month": "Date",
                    "median_time_to_merge": "Median Time to Merge (h)",
                    "median_time_to_first_review": "Median Time to First Review (h)",
                    "median_time_first_review_to_merge": "Median Time First Review to Merge (h)",
                }
            )
        )

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "Merged PRs over Time",
                "Time Trends",
                "LOC Changes",
                "PR Types",
                "Active Contributors",
                "Comments",
            ]
        )

        with tab1:
            fig_prs = px.bar(
                monthly_pr_stats, x="Date", y="Merged PRs", title="Monthly Merged PRs"
            )
            st.plotly_chart(fig_prs, width="stretch")

        with tab2:
            st.caption("Excluding PRs open for more than 60 days.")
            fig_time = px.line(
                monthly_time_stats,
                x="Date",
                y=[
                    "Median Time to Merge (h)",
                    "Median Time to First Review (h)",
                    "Median Time First Review to Merge (h)",
                ],
                title="Median Time Trends (Hours)",
                markers=True,
            )
            st.plotly_chart(fig_time, width="stretch")

        with tab3:
            # Melt for LOC chart
            loc_melted = monthly_pr_stats.melt(
                id_vars="Date",
                value_vars=["Additions", "Deletions"],
                var_name="Type",
                value_name="Lines",
            )

            fig_loc = px.bar(
                loc_melted,
                x="Date",
                y="Lines",
                color="Type",
                title="Monthly LOC Changes",
                color_discrete_map={"Additions": "#28a745", "Deletions": "#dc3545"},
            )
            st.plotly_chart(fig_loc, width="stretch")

        with tab4:
            # Melt for Types chart
            types_melted = monthly_pr_stats.melt(
                id_vars="Date",
                value_vars=["Features", "Bugfixes"],
                var_name="Type",
                value_name="Count",
            )

            fig_types = px.bar(
                types_melted,
                x="Date",
                y="Count",
                color="Type",
                title="Monthly Merged Features vs Bugfixes",
                barmode="group",
            )
            st.plotly_chart(fig_types, width="stretch")

        with tab5:
            row = st.container()
            col1, col2 = row.columns([1, 0.2])
            with col2.popover("Modify", width="content"):
                min_prs = st.number_input(
                    "Minimum merged PRs", min_value=1, value=3, step=1
                )

            with col1:
                st.markdown(
                    f"##### Monthly Active Contributors (>= {min_prs} Merged PRs)"
                )

            # Calculate Active Contributors
            # Group by month and author to count PRs
            author_monthly_prs = (
                merged_prs_df.groupby(["merge_month", "author"])
                .size()
                .reset_index(name="pr_count")
            )

            # Filter for authors with >= min_prs in a month
            active_authors_monthly = author_monthly_prs[
                author_monthly_prs["pr_count"] >= min_prs
            ]

            # Count unique active authors per month
            active_contributors_stats = (
                active_authors_monthly.groupby("merge_month")["author"]
                .nunique()
                .reset_index(name="Active Contributors")
                .rename(columns={"merge_month": "Date"})
            )

            st.caption(
                f"Active contributors are users who have merged at least {min_prs} PRs in a given month."
            )
            if not active_contributors_stats.empty:
                fig_active = px.bar(
                    active_contributors_stats,
                    x="Date",
                    y="Active Contributors",
                )
                st.plotly_chart(fig_active, width="stretch")
            else:
                st.info("No active contributors found for the selected period.")

        with tab6:
            show_median = st.checkbox("Show Median per PR", value=False)

            if show_median:
                value_vars = ["Median Review Comments", "Median Issue Comments"]
                title = "Monthly Median PR Comments per PR (Review vs Issue)"
            else:
                value_vars = ["Total Review Comments", "Total Issue Comments"]
                title = "Monthly Total PR Comments (Review vs Issue)"

            # Melt for Comments chart
            comments_melted = monthly_pr_stats.melt(
                id_vars="Date",
                value_vars=value_vars,
                var_name="Type",
                value_name="Count",
            )

            fig_comments = px.bar(
                comments_melted,
                x="Date",
                y="Count",
                color="Type",
                title=title,
                barmode="stack" if not show_median else "group",
            )
            st.plotly_chart(fig_comments, width="stretch")
            st.caption(
                "Note: These metrics include comments from bots and automated systems."
            )

    else:
        st.info("No merged PRs found for the selected period.")

    # --- Issue Metrics ---
    st.markdown("##### :material/problem: Issue Metrics")
    st.caption(
        f"Metrics based on issues from `streamlit/streamlit` since {since_input.strftime('%Y/%m/%d')}."
    )

    # Prepare Issue Data
    # Reuse all_issues_df calculated previously if possible, but it's inside the other block.
    # So we recalculate it here or move it up.
    # To be safe and clean, I'll fetch it again or check if I can reuse the function call.
    # The previous block does:
    # all_issues_df = pd.DataFrame([issue for issue in get_all_github_issues() if "pull_request" not in issue])
    # Let's do that here too.

    all_issues_raw = [
        issue for issue in get_all_github_issues() if "pull_request" not in issue
    ]
    all_issues_df = pd.DataFrame(all_issues_raw)

    if not all_issues_df.empty:
        all_issues_df["created_at"] = pd.to_datetime(all_issues_df["created_at"])
        all_issues_df["closed_at"] = pd.to_datetime(all_issues_df["closed_at"])

        # Filter by date for "Created" metrics
        created_in_period = all_issues_df[
            all_issues_df["created_at"].dt.date >= since_input
        ]

        # Filter by date for "Closed" metrics
        closed_in_period = all_issues_df[
            (all_issues_df["closed_at"].notna())
            & (all_issues_df["closed_at"].dt.date >= since_input)
        ]

        total_created = len(created_in_period)
        total_closed = len(closed_in_period)

        # Calculate Time to Close for issues closed in the period
        closed_in_period = closed_in_period.copy()  # Avoid SettingWithCopyWarning
        closed_in_period["time_to_close"] = (
            closed_in_period["closed_at"] - closed_in_period["created_at"]
        )
        median_time_to_close = (
            closed_in_period["time_to_close"].dt.total_seconds() / 3600 / 24
        ).median()  # In days

        col1, col2, col3 = st.columns(3)
        col1.metric("Issues Created", total_created, border=True)
        col2.metric("Issues Closed", total_closed, border=True)
        col3.metric(
            "Median Time to Close",
            f"{median_time_to_close:.1f} days"
            if not pd.isna(median_time_to_close)
            else "—",
            border=True,
        )

        # Monthly Issue Trends
        # We want to show Created vs Closed over time
        # We need to aggregate by month for both created and closed dates

        # Created counts
        created_counts = (
            created_in_period.groupby(created_in_period["created_at"].dt.to_period("M"))
            .size()
            .reset_index(name="Created")
            .rename(columns={"created_at": "Month"})
        )

        # Closed counts
        closed_counts = (
            closed_in_period.groupby(closed_in_period["closed_at"].dt.to_period("M"))
            .size()
            .reset_index(name="Closed")
            .rename(columns={"closed_at": "Month"})
        )

        # Merge them
        issue_trends = pd.merge(
            created_counts, closed_counts, on="Month", how="outer"
        ).fillna(0)
        issue_trends["Month"] = issue_trends["Month"].dt.to_timestamp()
        issue_trends = issue_trends.sort_values("Month")

        # Melt for plotting
        issue_trends_melted = issue_trends.melt(
            id_vars="Month",
            value_vars=["Created", "Closed"],
            var_name="Status",
            value_name="Count",
        )

        fig_issues = px.bar(
            issue_trends_melted,
            x="Month",
            y="Count",
            color="Status",
            barmode="group",
            title="Monthly Issues: Created vs Closed",
        )
        st.plotly_chart(fig_issues, width="stretch")

        # --- New Visualization: Created Issues by Type ---
        created_by_type = created_in_period.copy()
        created_by_type["Type"] = created_by_type["labels"].apply(
            lambda labels: "Bug"
            if any(label["name"] == "type:bug" for label in labels)
            else (
                "Feature"
                if any(label["name"] == "type:enhancement" for label in labels)
                else None
            )
        )
        created_by_type = created_by_type.dropna(subset=["Type"])

        if not created_by_type.empty:
            created_by_type_monthly = (
                created_by_type.groupby(
                    [created_by_type["created_at"].dt.to_period("M"), "Type"]
                )
                .size()
                .reset_index(name="Count")
                .rename(columns={"created_at": "Month"})
            )
            created_by_type_monthly["Month"] = created_by_type_monthly[
                "Month"
            ].dt.to_timestamp()

            fig_created_by_type = px.bar(
                created_by_type_monthly,
                x="Month",
                y="Count",
                color="Type",
                title="Monthly Created Issues: Bugs vs Features",
                barmode="group",
            )
            st.plotly_chart(fig_created_by_type, width="stretch")

        # Priority Bug Resolution Time
        st.markdown("##### :material/timer: Bug Resolution Time by Priority")

        # Filter for bugs with priority labels
        priority_bugs = closed_in_period.copy()

        # Extract priority
        def extract_priority(labels):
            for label in labels:
                if label["name"].startswith("priority:"):
                    return label["name"].split("priority:")[-1]
            return None

        priority_bugs["priority"] = priority_bugs["labels"].apply(extract_priority)

        # Filter for only rows with priority and is a bug
        priority_bugs["is_bug"] = priority_bugs["labels"].apply(
            lambda x: any(l["name"] == "type:bug" for l in x)
        )
        priority_bugs = priority_bugs[
            (priority_bugs["priority"].notna()) & (priority_bugs["is_bug"])
        ]

        if not priority_bugs.empty:
            # Calculate time to close in days
            priority_bugs["time_to_close_days"] = (
                priority_bugs["time_to_close"].dt.total_seconds() / 3600 / 24
            )

            # Sort order for priorities
            priority_order = ["P0", "P1", "P2", "P3", "P4"]

            fig_priority = px.box(
                priority_bugs,
                x="priority",
                y="time_to_close_days",
                title="Time to Close by Bug Priority (Days)",
                labels={"priority": "Priority", "time_to_close_days": "Days to Close"},
                category_orders={"priority": priority_order},
                points="all",  # Show all points
                hover_data=["title", "html_url"],
            )
            st.plotly_chart(fig_priority, width="stretch")

            # Median Time to Close over Time
            priority_bugs["close_month"] = (
                priority_bugs["closed_at"].dt.to_period("M").dt.to_timestamp()
            )

            monthly_priority_stats = (
                priority_bugs.groupby(["close_month", "priority"])
                .agg(median_time_to_close=("time_to_close_days", "median"))
                .reset_index()
                .sort_values("close_month")
            )

            # Calculate rolling average
            monthly_priority_stats["rolling_median"] = monthly_priority_stats.groupby(
                "priority"
            )["median_time_to_close"].transform(
                lambda x: x.rolling(window=3, min_periods=1).mean()
            )

            fig_priority_over_time = px.line(
                monthly_priority_stats,
                x="close_month",
                y="rolling_median",
                color="priority",
                title="Median Time to Close over Time (3-month rolling avg)",
                labels={
                    "close_month": "Date",
                    "rolling_median": "Median Days to Close",
                    "priority": "Priority",
                },
                category_orders={"priority": priority_order},
                markers=True,
            )
            st.plotly_chart(fig_priority_over_time, width="stretch")
        else:
            st.info("No priority bugs found in the selected period.")

    else:
        st.info("No issues found.")
