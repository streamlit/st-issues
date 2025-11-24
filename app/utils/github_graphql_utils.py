from __future__ import annotations

import pandas as pd
import json

import json
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Final, Iterable, List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st
from requests.exceptions import (
    ChunkedEncodingError,
    ConnectionError as RequestsConnectionError,
)


GITHUB_GRAPHQL_ENDPOINT: Final[str] = "https://api.github.com/graphql"
CACHE_BASE_DIR: Final[Path] = Path(".cache/github_prs")


def get_graphql_headers() -> Dict[str, str]:
    """Get headers for GitHub GraphQL requests."""
    return {
        "Authorization": f"bearer {st.secrets['github']['token']}",
        "Accept": "application/json",
    }


def _run_graphql_query(
    query: str,
    variables: Dict[str, Any],
    allow_rate_limit_wait: bool = False,
) -> Dict[str, Any]:
    """Execute a GraphQL query with retry and rate-limit handling."""

    headers = get_graphql_headers()
    retryable_status = {502, 503, 504, 429}

    for attempt in range(5):
        try:
            response = requests.post(
                GITHUB_GRAPHQL_ENDPOINT,
                headers=headers,
                json={"query": query, "variables": variables},
                timeout=40,
            )
        except (ChunkedEncodingError, RequestsConnectionError) as exc:
            wait_seconds = 1.5 * (attempt + 1)
            time.sleep(wait_seconds)
            continue
        if response.status_code == 200:
            payload = response.json()
            cost_info = payload.get("extensions", {}).get("cost")
            if cost_info:
                actual_cost = cost_info.get("actualQueryCost")
                throttle_status = cost_info.get("throttleStatus", {})
                remaining = throttle_status.get("remaining")
                reset_at = throttle_status.get("resetAt")
                print(
                    "[GitHub GraphQL] cost=",
                    actual_cost,
                    "remaining=",
                    remaining,
                    "resetAt=",
                    reset_at,
                )

            if "errors" in payload and payload["errors"]:
                # Handle rate limit errors specifically if present
                error_messages = {
                    err.get("type", ""): err.get("message", "")
                    for err in payload["errors"]
                }
                if "RATE_LIMITED" in error_messages or any(
                    "rate limit" in msg.lower() for msg in error_messages.values()
                ):
                    reset_at = (
                        payload.get("data", {}).get("rateLimit", {}).get("resetAt")
                    )
                    wait_seconds = 5
                    if reset_at:
                        try:
                            reset_dt = datetime.fromisoformat(
                                reset_at.replace("Z", "+00:00")
                            )
                            wait_seconds = max(
                                5,
                                (reset_dt - datetime.now(timezone.utc)).total_seconds(),
                            )
                        except ValueError:
                            wait_seconds = 5

                    print(f"Waiting {wait_seconds} seconds before retrying...")
                    time.sleep(wait_seconds)
                    continue

                raise RuntimeError(f"GitHub GraphQL error: {payload['errors']}")

            data = payload.get("data")
            if data is None:
                raise RuntimeError("GitHub GraphQL response missing data")

            return data

        if response.status_code == 403 and allow_rate_limit_wait:
            remaining_header = response.headers.get("X-RateLimit-Remaining")
            if remaining_header == "0":
                reset_ts = response.headers.get("X-RateLimit-Reset")
                if reset_ts is not None:
                    try:
                        reset_epoch = int(reset_ts)
                        wait_seconds = max(0, reset_epoch - int(time.time())) + 1
                    except ValueError:
                        wait_seconds = 60
                else:
                    wait_seconds = 60
                time.sleep(wait_seconds)
                continue

        if response.status_code in retryable_status:
            wait_seconds = 1.5 * (attempt + 1)
            time.sleep(wait_seconds)
            continue

        response.raise_for_status()

    raise RuntimeError("GitHub GraphQL request failed after retries.")


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except ValueError:
        return None


def _build_search_query(
    repo: str,
    base_branch: str,
    merged_since: Optional[date],
    merged_until: Optional[date],
) -> str:
    parts = [f"repo:{repo}", "is:pr", "is:merged", f"base:{base_branch}"]
    if merged_since:
        parts.append(f"merged:>={merged_since.isoformat()}")
    if merged_until:
        parts.append(f"merged:<={merged_until.isoformat()}")
    return " ".join(parts)


def _is_human_reviewer(typename: str, login: Optional[str], ignore_bots: bool) -> bool:
    if typename != "User" or not login:
        return False
    if ignore_bots and login.endswith("[bot]"):
        return False
    return True


PULL_REQUESTS_QUERY: Final[str] = """
query($owner: String!, $name: String!, $baseRef: String!, $cursor: String, $states: [PullRequestReviewState!], $direction: OrderDirection!) {
  rateLimit { cost remaining resetAt }
  repository(owner: $owner, name: $name) {
    pullRequests(
      states: MERGED,
      baseRefName: $baseRef,
      first: 100,
      after: $cursor,
      orderBy: { field: UPDATED_AT, direction: $direction }
    ) {
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          id number url title isDraft
          createdAt mergedAt updatedAt
          mergedBy { login }
          additions deletions changedFiles
          author { __typename ... on User { login } ... on Bot { login } }
          comments { totalCount }
          reviews(states: $states, first: 100) {
            nodes {
              state
              submittedAt
              author { __typename ... on User { login } ... on Bot { login } }
              comments { totalCount }
            }
          }
          closingIssuesReferences(first: 100) {
            nodes { number }
          }
          labels(first: 100) {
            nodes { name }
          }
        }
      }
    }
  }
}
"""


def _extract_pr_metrics(
    pr_node: Dict[str, Any],
    review_states: Iterable[str],
    ignore_bots: bool,
    seen_pr_numbers: set[int],
) -> Optional[Dict[str, Any]]:
    pr_number = pr_node["number"]
    if pr_number in seen_pr_numbers:
        return None

    seen_pr_numbers.add(pr_number)

    created_at = _parse_iso_datetime(pr_node.get("createdAt"))
    merged_at = _parse_iso_datetime(pr_node.get("mergedAt"))
    updated_at = _parse_iso_datetime(pr_node.get("updatedAt"))

    reviews_conn = pr_node.get("reviews") or {}
    all_reviews = reviews_conn.get("nodes", [])

    review_times = [
        _parse_iso_datetime(review.get("submittedAt"))
        for review in all_reviews
        if review.get("submittedAt")
    ]

    first_review_event = min(
        [dt for dt in review_times if dt is not None],
        default=None,
    )

    approvals = [
        _parse_iso_datetime(review.get("submittedAt"))
        for review in all_reviews
        if review.get("state") == "APPROVED" and review.get("submittedAt")
    ]
    earliest_approval = min(approvals) if approvals else None

    time_open_to_first_review = (
        first_review_event - created_at if created_at and first_review_event else None
    )

    post_first_candidates: List[datetime] = []
    if (
        earliest_approval
        and first_review_event
        and earliest_approval >= first_review_event
    ):
        post_first_candidates.append(earliest_approval)
    if merged_at and first_review_event and merged_at >= first_review_event:
        post_first_candidates.append(merged_at)

    time_first_review_to_merge_or_approval = (
        min(post_first_candidates) - first_review_event
        if first_review_event and post_first_candidates
        else None
    )

    time_open_to_merge = merged_at - created_at if created_at and merged_at else None

    num_review_comments = sum(
        (review.get("comments") or {}).get("totalCount", 0) for review in all_reviews
    )

    reviewer_logins: set[str] = set()
    for review in all_reviews:
        author_info = review.get("author") or {}
        login = author_info.get("login")
        if _is_human_reviewer(author_info.get("__typename", ""), login, ignore_bots):
            reviewer_logins.add(login)  # type: ignore[arg-type]

    reviewers = sorted(reviewer_logins)

    author_info = pr_node.get("author") or {}
    author_typename = author_info.get("__typename")
    author_login = author_info.get("login") if author_typename == "User" else None

    return {
        "pr_number": pr_number,
        "url": pr_node.get("url"),
        "title": pr_node.get("title"),
        "author": author_login,
        "from_bot": author_typename == "Bot"
        or (author_login and author_login.endswith("[bot]")),
        "merged_by": (pr_node.get("mergedBy") or {}).get("login"),
        "is_draft": pr_node.get("isDraft", False),
        "open_date": created_at,
        "merge_date": merged_at,
        "updated_at": updated_at,
        "time_open_to_first_review": time_open_to_first_review,
        "time_first_review_to_merge_or_approval": time_first_review_to_merge_or_approval,
        "time_open_to_merge": time_open_to_merge,
        "num_review_comments": num_review_comments,
        "num_issue_comments": (pr_node.get("comments") or {}).get("totalCount", 0),
        "reviewers": reviewers,
        "distinct_reviewer_count": len(reviewers),
        "additions": pr_node.get("additions", 0),
        "deletions": pr_node.get("deletions", 0),
        "loc_changes": (pr_node.get("additions", 0) or 0)
        + (pr_node.get("deletions", 0) or 0),
        "changed_files": pr_node.get("changedFiles", 0),
        "closing_issues": [
            node["number"]
            for node in (pr_node.get("closingIssuesReferences") or {}).get("nodes", [])
            if node
        ],
        "labels": [
            node["name"]
            for node in (pr_node.get("labels") or {}).get("nodes", [])
            if node
        ],
    }


def _split_owner_repo(repo: str) -> Tuple[str, str]:
    owner, name = repo.split("/", 1)
    return owner, name


def _cache_dir_for_branch(base_branch: str) -> Path:
    cache_dir = CACHE_BASE_DIR / base_branch
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _incremental_cache_path(base_branch: str) -> Path:
    cache_dir = _cache_dir_for_branch(base_branch)
    return cache_dir / "merged_prs.parquet"


@st.cache_data(
    ttl=60 * 60 * 24, show_spinner="Loading merged PR metrics via GraphQL..."
)
def fetch_merged_pr_metrics(
    repo: str = "streamlit/streamlit",
    base_branch: str = "develop",
    merged_since: Optional[date] = None,
    merged_until: Optional[date] = None,
    include_commented: bool = True,
    ignore_bots: bool = False,
    max_results: Optional[int] = None,
    use_disk_cache: bool = False,
    paginate_ascending: bool = True,
    starting_cursor: Optional[str] = None,
    full_history_cache_path: Optional[Path] = None,
    resume_on_rate_limit: bool = False,
) -> pd.DataFrame:
    """Fetch merged PR metrics using the GitHub GraphQL API."""

    review_states: List[str] = ["APPROVED", "CHANGES_REQUESTED"]
    if include_commented:
        review_states.append("COMMENTED")

    existing_df: Optional[pd.DataFrame] = None
    seen_pr_numbers: set[int] = set()
    records: List[Dict[str, Any]] = []
    rate_stats: Dict[str, Any] = {}
    collected = 0
    owner, name = _split_owner_repo(repo)
    order_direction = "ASC" if paginate_ascending else "DESC"
    cache_dir = _cache_dir_for_branch(base_branch)
    cursor = starting_cursor

    if full_history_cache_path and full_history_cache_path.exists():
        existing_df = pd.read_parquet(full_history_cache_path)
        if not existing_df.empty:
            seen_pr_numbers.update(existing_df["pr_number"].astype(int).tolist())

    while True:
        cache_key = f"{order_direction}_{cursor or 'START'}"
        cache_path = cache_dir / f"{cache_key}.json"
        if use_disk_cache and cache_path.exists():
            with cache_path.open("r", encoding="utf-8") as f:
                response_data = json.load(f)
        else:
            response_data = _run_graphql_query(
                PULL_REQUESTS_QUERY,
                {
                    "owner": owner,
                    "name": name,
                    "baseRef": base_branch,
                    "cursor": cursor,
                    "states": list(review_states),
                    "direction": order_direction,
                },
                allow_rate_limit_wait=resume_on_rate_limit,
            )
            if use_disk_cache:
                with cache_path.open("w", encoding="utf-8") as f:
                    json.dump(response_data, f)

        rate_info = response_data.get("rateLimit") or {}
        cost = rate_info.get("cost", 0)
        rate_stats["total_cost"] = rate_stats.get("total_cost", 0) + cost
        remaining = rate_info.get("remaining")
        rate_stats["last_remaining"] = remaining
        rate_stats["reset_at"] = rate_info.get("resetAt")

        repo_block = response_data.get("repository")
        if not repo_block:
            break

        pr_connection = repo_block.get("pullRequests", {})
        page_info = pr_connection.get("pageInfo", {})
        for edge in pr_connection.get("edges", []):
            node = edge.get("node")
            if not node:
                continue
            record = _extract_pr_metrics(
                node, review_states, ignore_bots, seen_pr_numbers
            )
            if not record:
                continue
            merge_date = record.get("merge_date")
            if merge_date:
                merge_date_only = merge_date.date()
                if merged_until and merge_date_only > merged_until:
                    continue
                if merged_since and merge_date_only < merged_since:
                    continue
            records.append(record)
            collected += 1
            if max_results and collected >= max_results:
                break

        if max_results and collected >= max_results:
            break

        cursor = page_info.get("endCursor")
        rate_stats["last_cursor"] = cursor
        rate_stats["page_count"] = rate_stats.get("page_count", 0) + 1

        if resume_on_rate_limit and remaining is not None and remaining <= 0:
            reset_at = rate_stats.get("reset_at")
            if reset_at:
                reset_dt = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))
                sleep_seconds = max(
                    5, (reset_dt - datetime.now(timezone.utc)).total_seconds()
                )
                st.info(
                    f"Rate limit reached. Waiting {sleep_seconds:.0f} seconds to resume…"
                )
                time.sleep(sleep_seconds)
                continue

        if not page_info.get("hasNextPage"):
            break

        if cursor is None:
            break

    if not records and existing_df is None:
        return pd.DataFrame()

    new_df = pd.DataFrame.from_records(records)
    if existing_df is not None and not existing_df.empty:
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset="pr_number", keep="last")
    else:
        combined_df = new_df

    if full_history_cache_path:
        combined_df.to_parquet(full_history_cache_path, index=False)

    df = combined_df
    df.attrs["rate_limit_cost"] = rate_stats.get("total_cost", 0)
    df.attrs["rate_limit_remaining"] = rate_stats.get("last_remaining")
    df.attrs["rate_limit_reset_at"] = rate_stats.get("reset_at")
    df.attrs["last_cursor"] = rate_stats.get("last_cursor")
    df.attrs["page_count"] = rate_stats.get("page_count", 0)

    timedelta_cols = [
        "time_open_to_first_review",
        "time_first_review_to_merge_or_approval",
        "time_open_to_merge",
    ]
    for col in timedelta_cols:
        if col in df.columns:
            df[col] = pd.to_timedelta(df[col])

    if "open_date" in df.columns:
        df["open_date"] = pd.to_datetime(df["open_date"], utc=True)
    if "merge_date" in df.columns:
        df["merge_date"] = pd.to_datetime(df["merge_date"], utc=True)

    return df
