import datetime
import json
from typing import Iterable

import pandas as pd
import streamlit as st
from ghapi.all import GhApi, paged
from htbuilder import a, span
from stqdm import stqdm


def inline_space(num: int) -> str:
    return "&nbsp;" * num


def indent(html: str, num_indents: int) -> str:
    return "&nbsp;" * num_indents + html


def reactions_formatter(reactions: Iterable[str], counts: Iterable[int]) -> None:
    html = "&nbsp;&nbsp;  ·  &nbsp;&nbsp;".join(
        [f"{reaction} {count}" for (reaction, count) in zip(reactions, counts)]
    )
    st.caption(
        indent(html, 8),
        unsafe_allow_html=True,
    )


st.title("Github Issues Leaderboard")

api = GhApi(token=st.secrets.github.token)

GITHUB_REACTIONS = [
    "🫶",
    "👍",
    "👎",
    "😂",
    "🥳",
    "😕",
    "❤️",
    "🚀",
    "👁️",
]
COLUMNS = (
    "created_at",
    "updated_at",
    "comments",
    "body",
    "html_url",
    "title",
    "reactions.total_count",
    "reactions.+1",
    "reactions.-1",
    "reactions.laugh",
    "reactions.hooray",
    "reactions.confused",
    "reactions.heart",
    "reactions.rocket",
    "reactions.eyes",
)


LABEL_TO_COLUMN = dict(
    zip(
        GITHUB_REACTIONS,
        (
            "reactions_total_count",
            "reactions_plus1",
            "reactions_minus1",
            "reactions_laugh",
            "reactions_hooray",
            "reactions_confused",
            "reactions_heart",
            "reactions_rocket",
            "reactions_eyes",
        ),
    )
)


TODAY = datetime.date.today()
A_WEEK_AGO = TODAY - datetime.timedelta(days=7)
A_MONTH_AGO = TODAY - datetime.timedelta(days=30)
REPO_CREATION = datetime.date(2019, 1, 1)
CACHE_TIME = 60 * 60 * 72 # 3 days


@st.cache_data(ttl=CACHE_TIME, show_spinner=False)
def get_overall_issues() -> pd.DataFrame:

    with st.spinner("🙋 Crawling issues..."):
        # Get raw data
        raw_issues = list()

        pages = paged(
            api.issues.list_for_repo,
            owner="streamlit",
            repo="streamlit",
            per_page=100,
            sort="created",
            direction="desc",
        )

        for page in pages:
            df = pd.json_normalize(page)
            df = df[[
                "number",
                "created_at",
                "updated_at",
                "reactions_total_count",
                "reactions_total_count",
                "reactions_plus1",
                "reactions_minus1",
                "reactions_laugh",
                "reactions_hooray",
                "reactions_confused",
                "reactions_heart",
                "reactions_rocket",
                "reactions_eyes",
                "comments",
                "html_url",
                "title"]
                ]
            raw_issues += df
            break

        # Parse into a dataframe
        full_df = pd.concat(raw_issues)

        # Make sure types are properly understood
        full_df.created_at = pd.to_datetime(full_df.created_at)
        full_df.updated_at = pd.to_datetime(full_df.updated_at)

        # Replace special chars in columns to facilitate access in namedtuples
        full_df.columns = [
            col.replace(".", "_").replace("+1", "plus1").replace("-1", "minus1")
            for col in full_df.columns
        ]

    return full_df


def _reactions_formatter(
    reactions: Iterable[str],
    counts: Iterable[int],
    grayscale_mask: Iterable[bool],
) -> str:

    reactions = "&nbsp;&nbsp;  ·  &nbsp;&nbsp;".join(
        [
            f"{reaction} {count}"
            if not grayscale
            else f'<span style="-webkit-filter: grayscale(100%); filter: grayscale(100%);">{reaction}</span> {count}'
            for (reaction, count, grayscale) in zip(reactions, counts, grayscale_mask)
        ]
    )

    return reactions


def _get_issue_html(issue, rank: int, sort_by: str) -> str:

    separator = f"{inline_space(2)}·{inline_space(2)}"
    import html

    title = html.escape(issue.title)
    title = title[:50] + "..." if len(title) > 50 else title
    url = issue.html_url
    issue_html = str(
        a(
            contenteditable=False,
            href=url,
            rel="noopener noreferrer",
            style="color:inherit;text-decoration:inherit; height:auto!important",
            target="_blank",
        )(
            span(
                style=(
                    "border-bottom:0.05em solid"
                    " rgba(55,53,47,0.25);font-weight:500;flex-shrink:0"
                )
            )(title),
            span(),
        )
    )
    reactions = GITHUB_REACTIONS
    reaction_counts = (
        issue.reactions_total_count,
        issue.reactions_plus1,
        issue.reactions_minus1,
        issue.reactions_laugh,
        issue.reactions_hooray,
        issue.reactions_confused,
        issue.reactions_heart,
        issue.reactions_rocket,
        issue.reactions_eyes,
        issue.comments,
    )
    creation_date = str(issue.created_at)[:10]
    grayscale_mask = [reaction != sort_by for reaction in GITHUB_REACTIONS]
    formatted_reactions = _reactions_formatter(
        reactions, reaction_counts, grayscale_mask
    )
    return f"""**{rank}**{inline_space(4)}{issue_html}{separator}{creation_date}{separator} :green[**+ {issue.num_reactions}** {issue.reaction} {reactions_date_range_label.lower()}]<br>
{inline_space(7)}<small data-testid="stCaptionContainer">{formatted_reactions}</small>
"""


@st.cache_data(ttl=CACHE_TIME, show_spinner=False)
def _get_overall_reactions(issue_number: int):
    # Get raw data
    raw_reactions = list()

    pages = paged(
        api.reactions.list_for_issue,
        owner="streamlit",
        repo="streamlit",
        issue_number=issue_number,
        per_page=100,
    )

    for page in pages:
        raw_reactions += page

    # Parse into a dataframe
    reactions_df = pd.json_normalize(raw_reactions)
    if not reactions_df.empty:
        reactions_df = reactions_df[
                    ["created_at", "content", "user.login", "user.id", "user.avatar_url"]
                ]
        reactions_df["issue_number"] = issue_number
    return reactions_df


def get_overall_reactions(issue_numbers: list):
    reactions_dfs = list()
    for issue_number in stqdm(issue_numbers, desc="🤯 Crawling reactions..."):
        reactions_df = _get_overall_reactions(issue_number)
        if not reactions_df.empty:
            reactions_dfs.append(reactions_df)

    return pd.concat(reactions_dfs)


def display_issue(issue, rank: int, sort_by: str) -> None:
    st.write(
        _get_issue_html(
            issue,
            rank=rank,
            sort_by=sort_by,
        ),
        unsafe_allow_html=True,
    )


def display_issues(df: pd.DataFrame, sort_by: str) -> None:
    for rank, row in enumerate((df.itertuples())):
        display_issue(row, rank=rank + 1, sort_by=sort_by)


SORT_BY_HELP = """
- 🫶 = all reactions summed
- 👄 = comments
- Remaining emojis are just available reactions on GitHub
"""


def format_reaction_in_widget(reaction: str) -> str:
    if reaction == "🫶":
        return "🫶  (reactions overall)"
    elif reaction == "👄":
        return "👄  (comments)"
    else:
        return reaction


# Get all issues
all_issues = get_overall_issues()
st.dataframe(all_issues)

# Only query issues which had at least 1 reaction
issue_numbers = all_issues.query("reactions_total_count > 0").number.unique().tolist()
reactions_df = get_overall_reactions(issue_numbers)
st.dataframe(reactions_df)

one, two, three, four = st.columns((2, 2, 3, 2))

num_issues = one.selectbox(
    label="Show me at most...",
    options=(5, 10, 15),
    format_func=lambda x: f"{x} issues",
)

DATETIME_PERIODS = {
    "Last week": (A_WEEK_AGO, TODAY),
    "Last month": (A_MONTH_AGO, TODAY),
    "All time": (REPO_CREATION, TODAY),
}

issues_date_range_label = two.selectbox(
    label="Created...",
    options=DATETIME_PERIODS.keys(),
    index=2,
)

issues_date_range_label = str(issues_date_range_label)

sort_by_label = three.selectbox(
    label="Who received most...",
    options=LABEL_TO_COLUMN.keys(),
    format_func=format_reaction_in_widget,
)

sort_by_label = str(sort_by_label)

reactions_date_range_label = four.selectbox(
    label="During...",
    options=DATETIME_PERIODS.keys(),
)

reactions_date_range_label = str(reactions_date_range_label)

issues_date_range = DATETIME_PERIODS[issues_date_range_label]
reactions_date_range = DATETIME_PERIODS[reactions_date_range_label]
reactions_df.created_at = pd.to_datetime(reactions_df.created_at)


# Reaction date filter
numbers_from_reaction_date_filter = reactions_df[
    reactions_df.created_at.dt.date.between(*reactions_date_range)
].issue_number.unique()

emoji_to_label_mapper = {
    "🫶": "heart",
    "❤️": "heart",
    "👍": "+1",
    "👎": "-1",
    "🚀": "rocket",
    "😕": "confused",
    "👁️": "eyes",
    "😂": "laugh",
    "🥳": "hooray",
}


result = (
    reactions_df[
        (
            reactions_df.content.eq(emoji_to_label_mapper[sort_by_label])
            if sort_by_label != "🫶"
            else True
        )
        & reactions_df.created_at.dt.date.between(*reactions_date_range)
        & reactions_df.issue_number.isin(
            all_issues[
                all_issues.created_at.dt.date.between(*issues_date_range)
            ].number.unique()
        )
    ]
    .groupby("issue_number")
    .size()
    .sort_values(ascending=False)
    .to_frame("num_reactions")
    .assign(reaction=sort_by_label)
    .reset_index()
    .merge(all_issues, left_on="issue_number", right_on="number")
    .head(num_issues)
)

st.write("### Results")
if result.empty:
    st.caption(
        f"Empty results. No issue created {issues_date_range_label.lower()} was found with {sort_by_label} reactions happening {reactions_date_range_label.lower()}."
    )
display_issues(result, sort_by=sort_by_label)
