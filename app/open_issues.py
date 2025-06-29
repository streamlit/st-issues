import json
import pathlib
import urllib.request
from datetime import date, datetime
from typing import Dict, List
from urllib.parse import quote

import altair as alt
import pandas as pd
import requests
import streamlit as st

from app.utils.github_utils import GITHUB_API_HEADERS, get_all_github_issues

DEFAULT_ISSUES_FOLDER = "issues"
PATH_OF_SCRIPT = pathlib.Path(__file__).parent.resolve()
PATH_TO_ISSUES = (
    pathlib.Path(PATH_OF_SCRIPT).parent.joinpath(DEFAULT_ISSUES_FOLDER).resolve()
)

st.set_page_config(
    page_title="Open Issues",
    page_icon="🗃",
    initial_sidebar_state="collapsed",
)


GROWTH_PERIODS = {
    "Last week": date.today() - pd.Timedelta(days=7),
    "Last month": date.today() - pd.Timedelta(days=30),
    "Last 3 months": date.today() - pd.Timedelta(days=90),
}


@st.cache_data(ttl=60 * 60 * 72, show_spinner=False)  # 3 days
def get_issue_reactions(issue_number: int) -> pd.DataFrame:
    reactions = []
    page = 1

    while True:
        try:
            response = requests.get(
                f"https://api.github.com/repos/streamlit/streamlit/issues/{issue_number}/reactions?per_page=100&page={page}",
                headers=GITHUB_API_HEADERS,
                timeout=100,
            )

            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                reactions.extend(data)
                page += 1
            else:
                # Don't show error for 404, might just mean no reactions
                if response.status_code != 404:
                    print(
                        f"Failed to retrieve reactions for issue {issue_number}: {response.status_code}:",
                        response.text,
                    )
                break
        except Exception as ex:
            print(ex, flush=True)
            break

    if not reactions:
        return pd.DataFrame()

    reactions_df = pd.json_normalize(reactions)
    if not reactions_df.empty:
        reactions_df = reactions_df[
            ["created_at", "content", "user.login", "user.id", "user.avatar_url"]
        ]
        reactions_df["issue_number"] = issue_number
    return reactions_df


def get_all_reactions(issue_numbers: list):
    reactions_dfs = list()
    progress_bar = st.progress(0, text="🤯 Crawling reactions...")
    total_issues = len(issue_numbers)
    for i, issue_number in enumerate(issue_numbers):
        reactions_df = get_issue_reactions(issue_number)
        if not reactions_df.empty:
            reactions_dfs.append(reactions_df)
        progress_bar.progress(
            (i + 1) / total_issues,
            text=f"🤯 Crawling reactions... ({i + 1}/{total_issues})",
        )

    progress_bar.empty()
    if not reactions_dfs:
        return pd.DataFrame()
    return pd.concat(reactions_dfs)


# Add checkbox for showing statistics
show_statistics = st.sidebar.checkbox("Show issue statistics", value=False)
show_reactions_growth = st.sidebar.checkbox("Show reactions growth", value=False)

if show_reactions_growth:
    reaction_growth_period = st.sidebar.selectbox(
        "Reaction growth period", options=GROWTH_PERIODS.keys(), index=1
    )

# Ignore Pull Requests
all_issues = [
    issue
    for issue in get_all_github_issues(state="open")
    if "pull_request" not in issue
]
all_labels = set()

for issue in all_issues:
    for label in issue["labels"]:
        all_labels.add(label["name"])


def initial_query_params(key: str) -> List[str]:
    """
    When page is first loaded, or if current params are empty, sync url params to
    session state. Afterwards, just return local copy.
    """
    if (
        "initial_query_params_labels" not in st.session_state
        or not st.session_state["initial_query_params_labels"]
    ):
        st.session_state["initial_query_params_labels"] = st.query_params.get_all(key)
    return st.session_state["initial_query_params_labels"]


default_filters = initial_query_params("label")

for label in default_filters:
    if label not in all_labels:
        st.warning(f"Label `{label}` does not exist")
        print(default_filters, flush=True)
        default_filters.remove(label)

filter_labels = st.sidebar.multiselect(
    "Filter by label", list(all_labels), default=default_filters
)
filter_missing_labels = st.sidebar.checkbox(
    "Filter issues that require feature labels", value=False
)

print("Show issues with labels:", filter_labels, flush=True)

st.query_params["label"] = filter_labels

filtered_issues = []
for issue in all_issues:
    filtered_out = False
    issue_labels: List[str] = [label["name"] for label in issue["labels"]]
    if filter_missing_labels:
        filtered_out = False
        for label in issue_labels:
            if (
                label.startswith("feature:")
                or label.startswith("area:")
                or label == "type:kudos"
            ):
                filtered_out = True
                break

    for filter_label in filter_labels:
        if filter_label not in issue_labels:
            filtered_out = True

    if not filtered_out:
        filtered_issues.append(issue)


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


def labels_to_type(labels: List[str]):
    if "type:enhancement" in labels:
        return "✨"
    elif "type:bug" in labels:
        return "🚨"
    elif "type:docs" in labels:
        return "📚"
    elif "type:kudos" in labels:
        return "🙏"
    else:
        return "❓"


def get_reproducible_example(issue_number: int):
    issue_folder_name = f"gh-{issue_number}"
    if PATH_TO_ISSUES.joinpath(issue_folder_name).is_dir():
        return "/?issue=" + issue_folder_name
    return None


@st.cache_data(ttl=60 * 60 * 12)  # cache for 12 hours
def get_view_counts(issue_numbers_series: pd.Series) -> pd.Series:
    # Get unique issue numbers and create batch request
    unique_issues = issue_numbers_series.unique()
    if len(unique_issues) == 0:
        return pd.Series(index=issue_numbers_series.index, dtype=float)

    # Process in batches of 100
    batch_size = 100
    view_counts = {}

    for i in range(0, len(unique_issues), batch_size):
        batch = unique_issues[i : i + batch_size]
        # Create batch request URL with current batch of issue numbers
        keys = ",".join(f"st-issue-{num}" for num in batch)
        url = f"https://api.views-badge.org/stats-batch?keys={keys}"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request) as response:
                if not response or response.status != 200:
                    print("Failed to fetch issue view counts", flush=True)
                    continue

                data = json.loads(response.read().decode("utf-8"))

                # Add view counts from this batch to the mapping
                view_counts.update(
                    {
                        int(key.split("-")[-1]): data.get(key, {}).get("views", None)
                        or None
                        for key in data.keys()
                    }
                )
        except Exception:
            print("Failed to fetch issue view counts", flush=True)
            continue

    # Map the view counts back to the original series
    return issue_numbers_series.map(view_counts)


df = pd.DataFrame.from_dict(filtered_issues)
if df.empty:
    st.markdown("No issues found")
else:
    df["labels"] = df["labels"].map(
        lambda x: [label["name"] if label else "" for label in x]
    )
    df["type"] = df["labels"].map(labels_to_type)
    df["reproducible_example"] = df["number"].map(get_reproducible_example)
    df["title"] = df["type"] + df["title"]
    df["reaction_types"] = df["reactions"].map(reactions_to_str)
    df["total_reactions"] = (
        df["reactions"].map(lambda x: x["total_count"]) + df["comments"]
    )
    df["author_avatar"] = df["user"].map(lambda x: x["avatar_url"])
    df["assignee_avatar"] = df["assignee"].map(lambda x: x["avatar_url"] if x else None)
    df["views"] = get_view_counts(df["number"])

    if show_reactions_growth:
        # --- NEW LOGIC FOR REACTION GROWTH ---
        issue_numbers_for_growth = (
            df[df["total_reactions"] >= 15]["number"].unique().tolist()
        )
        all_reactions_df = get_all_reactions(issue_numbers_for_growth)

        if not all_reactions_df.empty:
            start_date = GROWTH_PERIODS[reaction_growth_period]
            all_reactions_df["created_at"] = pd.to_datetime(
                all_reactions_df["created_at"]
            )

            recent_reactions = all_reactions_df[
                all_reactions_df["created_at"].dt.date >= start_date
            ]

            reaction_growth = (
                recent_reactions.groupby("issue_number")
                .size()
                .to_frame("reaction_growth")
            )

            df = df.merge(
                reaction_growth, left_on="number", right_on="issue_number", how="left"
            )
            df["reaction_growth"] = df["reaction_growth"].fillna(None).astype(int)
        else:
            df["reaction_growth"] = None

    df = df.sort_values(by=["total_reactions", "updated_at"], ascending=[False, False])

    link_qs_labels = "+".join([quote("label:" + label) for label in filter_labels])
    link = f"https://github.com/streamlit/streamlit/issues?q={quote('is:open')}+{quote('is:issue')}+{link_qs_labels}"

    st.markdown("")  # Add some space to prevent issue in embedded mode
    st.caption(
        f"**{len(filtered_issues)} issues** with **{df['total_reactions'].sum()} reactions** "
        f"and **{int(df['views'].sum())} views** based on the selected filters. "
        f"[View on GitHub :material/open_in_new:]({link})"
    )

    columns_to_display = [
        "title",
        "total_reactions",
        "author_avatar",
        "updated_at",
        "created_at",
        "html_url",
        "reaction_types",
        "comments",
        "views",
        "assignee_avatar",
        "labels",
        "reproducible_example",
        "state",
    ]

    if show_reactions_growth:
        columns_to_display.insert(2, "reaction_growth")

    column_config = {
        "title": st.column_config.TextColumn("Title", width=300),
        "type": "Type",
        "updated_at": st.column_config.DatetimeColumn(
            "Last Updated", format="distance"
        ),
        "created_at": st.column_config.DatetimeColumn("Created at", format="distance"),
        "author_avatar": st.column_config.ImageColumn("Author"),
        "total_reactions": st.column_config.NumberColumn(
            "Reactions", format="%d 🫶", help="Total number of reactions"
        ),
        "assignee_avatar": st.column_config.ImageColumn("Assignee"),
        "reaction_types": "Reactions Types",
        "labels": "Labels",
        "state": "State",
        "comments": st.column_config.NumberColumn("Comments", format="%d 💬"),
        "html_url": st.column_config.LinkColumn("Url", display_text="Open Issue"),
        "reproducible_example": st.column_config.LinkColumn(
            "Reproducible Example", width="medium"
        ),
        "views": st.column_config.NumberColumn("Views", format="%d 👁️", width=100),
    }

    if show_reactions_growth:
        column_config["reaction_growth"] = st.column_config.NumberColumn(
            "Growth",
            help="Reaction growth in the selected period.",
            format="+%d",
        )

    st.dataframe(
        df[columns_to_display],
        column_config=column_config,
        hide_index=True,
    )

    # Display statistics if checkbox is checked
    if show_statistics:
        st.divider()
        st.subheader("📊 Issue Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Age statistics
            if not df.empty:
                # Fix: Convert created_at to datetime and handle timezone properly
                df["age_days"] = df["created_at"].apply(
                    lambda x: (
                        datetime.now(
                            datetime.fromisoformat(x.replace("Z", "+00:00")).tzinfo
                        )
                        - datetime.fromisoformat(x.replace("Z", "+00:00"))
                    ).days
                )

                st.metric("Average age (days)", round(df["age_days"].mean(), 1))
                st.metric("Oldest issue (days)", df["age_days"].max())

        with col2:
            # Reaction and comment statistics
            if not df.empty:
                st.metric(
                    "Average reactions per issue",
                    round(df["total_reactions"].mean(), 1),
                )
                st.metric(
                    "Most reactions on an issue", int(df["total_reactions"].max())
                )

        with col3:
            if "views" in df.columns and not df["views"].isna().all():
                st.metric("Average views per issue", round(df["views"].mean(), 1))
                st.metric("Most viewed issue", int(df["views"].max()))

        # Categorized statistics (similar to Streamlit Issues Summary)
        if not df.empty and "labels" in df.columns:
            # Create category dictionaries
            categories: Dict[str, Dict[str, int]] = {
                "priority": {},
                "status": {},
                "feature": {},
                "area": {},
                "type": {},
            }

            # Count issues by category
            for _, issue in df.iterrows():
                issue_counted = {cat: False for cat in categories.keys()}

                for label in issue["labels"]:
                    if ":" in label:
                        category, value = label.split(":", 1)
                        if category in categories:
                            categories[category][value] = (
                                categories[category].get(value, 0) + 1
                            )
                            issue_counted[category] = True
                    elif label.startswith("type:"):
                        # Handle type labels separately
                        value = label[5:]  # Remove 'type:' prefix
                        categories["type"][value] = categories["type"].get(value, 0) + 1
                        issue_counted["type"] = True

                # Count issues without specific category labels
                for cat in categories.keys():
                    if not issue_counted[cat]:
                        categories[cat]["(not specified)"] = (
                            categories[cat].get("(not specified)", 0) + 1
                        )

            # Display category charts
            st.subheader("Issues by Category")

            # Create tabs for different categories
            tabs = st.tabs(["Priority", "Status", "Feature", "Area", "Type"])

            # Helper function to create horizontal bar chart
            def create_horizontal_bar_chart(data_df, title, x_field, y_field):
                # Set minimum bar height and spacing
                bar_height = 15  # Minimum height for each bar in pixels
                bar_padding = 1  # Padding between bars (proportion of bar height)

                # Calculate chart height based on number of items
                chart_height = max(200, len(data_df) * (bar_height * (1 + bar_padding)))

                # Create the chart with improved styling
                chart = (
                    alt.Chart(data_df, title=title)
                    .mark_bar(
                        cornerRadiusTopRight=3,
                        cornerRadiusBottomRight=3,
                        height=bar_height,
                    )
                    .encode(
                        x=alt.X(f"{x_field}:Q", title="Count"),
                        y=alt.Y(
                            f"{y_field}:N",
                            title=title,
                            sort="-x",
                            axis=alt.Axis(labelLimit=200),  # Allow longer labels
                        ),
                        tooltip=[y_field, x_field],
                        color=alt.Color(
                            f"{x_field}:Q", legend=None, scale=alt.Scale(scheme="blues")
                        ),
                    )
                    .properties(height=chart_height)
                    .configure_axis(labelFontSize=12, titleFontSize=14)
                    .configure_title(fontSize=16, anchor="start")
                )

                return chart

            # Priority tab
            with tabs[0]:
                if categories["priority"]:
                    priority_df = pd.DataFrame(
                        list(categories["priority"].items()),
                        columns=["Priority", "Count"],
                    )
                    # Filter out "(not specified)" entries
                    priority_df = priority_df[
                        priority_df["Priority"] != "(not specified)"
                    ]
                    if not priority_df.empty:
                        priority_df = priority_df.sort_values("Count", ascending=False)
                        st.altair_chart(
                            create_horizontal_bar_chart(
                                priority_df, "Priority", "Count", "Priority"
                            ),
                            use_container_width=True,
                        )
                    else:
                        st.write("No priority data available")
                else:
                    st.write("No priority data available")

            # Status tab
            with tabs[1]:
                if categories["status"]:
                    status_df = pd.DataFrame(
                        list(categories["status"].items()), columns=["Status", "Count"]
                    )
                    # Filter out "(not specified)" entries
                    status_df = status_df[status_df["Status"] != "(not specified)"]
                    if not status_df.empty:
                        status_df = status_df.sort_values("Count", ascending=False)
                        st.altair_chart(
                            create_horizontal_bar_chart(
                                status_df, "Status", "Count", "Status"
                            ),
                            use_container_width=True,
                        )
                    else:
                        st.write("No status data available")
                else:
                    st.write("No status data available")

            # Feature tab
            with tabs[2]:
                if categories["feature"]:
                    feature_df = pd.DataFrame(
                        list(categories["feature"].items()),
                        columns=["Feature", "Count"],
                    )
                    # Filter out "(not specified)" entries
                    feature_df = feature_df[feature_df["Feature"] != "(not specified)"]
                    if not feature_df.empty:
                        feature_df = feature_df.sort_values("Count", ascending=False)
                        st.altair_chart(
                            create_horizontal_bar_chart(
                                feature_df, "Feature", "Count", "Feature"
                            ),
                            use_container_width=True,
                        )
                    else:
                        st.write("No feature data available")
                else:
                    st.write("No feature data available")

            # Area tab
            with tabs[3]:
                if categories["area"]:
                    area_df = pd.DataFrame(
                        list(categories["area"].items()), columns=["Area", "Count"]
                    )
                    # Filter out "(not specified)" entries
                    area_df = area_df[area_df["Area"] != "(not specified)"]
                    if not area_df.empty:
                        area_df = area_df.sort_values("Count", ascending=False)
                        st.altair_chart(
                            create_horizontal_bar_chart(
                                area_df, "Area", "Count", "Area"
                            ),
                            use_container_width=True,
                        )
                    else:
                        st.write("No area data available")
                else:
                    st.write("No area data available")

            # Type tab
            with tabs[4]:
                if categories["type"]:
                    type_df = pd.DataFrame(
                        list(categories["type"].items()), columns=["Type", "Count"]
                    )
                    # Filter out "(not specified)" entries
                    type_df = type_df[type_df["Type"] != "(not specified)"]
                    if not type_df.empty:
                        type_df = type_df.sort_values("Count", ascending=False)
                        st.altair_chart(
                            create_horizontal_bar_chart(
                                type_df, "Type", "Count", "Type"
                            ),
                            use_container_width=True,
                        )
                    else:
                        st.write("No type data available")
                else:
                    st.write("No type data available")
