from __future__ import annotations

import json
import re
import time
from datetime import UTC, date, datetime
from http.client import IncompleteRead
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pandas as pd
import requests
import streamlit as st
from requests.exceptions import (
    JSONDecodeError as RequestsJSONDecodeError,
)
from requests.exceptions import (
    RequestException,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

GITHUB_GRAPHQL_ENDPOINT: Final[str] = "https://api.github.com/graphql"
CACHE_BASE_DIR: Final[Path] = Path(".cache/github_prs")
_RETRYABLE_HTTP_STATUS: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})
_RETRYABLE_GRAPHQL_ERROR_TYPES: Final[frozenset[str]] = frozenset({"INTERNAL", "TIMEOUT", "RATE_LIMITED"})
_RETRYABLE_GRAPHQL_MESSAGE_FRAGMENTS: Final[tuple[str, ...]] = (
    "something went wrong while executing your query",
    "timed out",
    "timeout",
    "rate limit",
    "temporarily unavailable",
    "please try again",
    "server error",
)
_MAX_GRAPHQL_ATTEMPTS: Final[int] = 5
_GRAPHQL_TIMEOUT_SECONDS: Final[int] = 40


class GitHubGraphQLError(RuntimeError):
    """Raised when a GitHub GraphQL request fails after retries."""


def get_graphql_headers() -> dict[str, str]:
    """Get headers for GitHub GraphQL requests."""
    headers = {"Accept": "application/json"}
    try:
        token = st.secrets["github"]["token"]
    except Exception as exc:
        _log_graphql("GitHub token unavailable from secrets", error=str(exc))
        return headers
    if isinstance(token, str) and token:
        headers["Authorization"] = f"bearer {token}"
    return headers


def _log_graphql(message: str, **details: Any) -> None:
    """Log GraphQL diagnostics without Streamlit UI elements.

    Cached callers use ``refresh_mode="background"``, which cannot render
    ``st.error`` / ``st.warning`` / ``st.exception``. Server logs remain visible.
    """
    parts = [f"[GitHub GraphQL] {message}"]
    extras = [f"{key}={value!r}" for key, value in details.items() if value is not None]
    if extras:
        parts.append("(" + ", ".join(extras) + ")")
    print(" ".join(parts), flush=True)


def _graphql_operation_name(query: str) -> str:
    match = re.search(r"\b(?:query|mutation)\s+([A-Za-z_][\w]*)", query)
    if match:
        return match.group(1)
    first_line = query.strip().splitlines()[0][:80] if query.strip() else "<empty>"
    return first_line


def _response_log_details(response: requests.Response | None) -> dict[str, Any]:
    if response is None:
        return {}
    snippet = " ".join((response.text or "").split())[:200]
    return {
        "status": response.status_code,
        "request_id": response.headers.get("X-GitHub-Request-Id") or response.headers.get("x-github-request-id"),
        "content_type": response.headers.get("Content-Type"),
        "content_length": response.headers.get("Content-Length"),
        "retry_after": response.headers.get("Retry-After"),
        "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining"),
        "body_snippet": snippet or None,
    }


def _parse_retry_after(response: requests.Response | None) -> float | None:
    if response is None:
        return None
    raw = response.headers.get("Retry-After")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _retry_wait_seconds(attempt: int, retry_after: float | None = None) -> float:
    if retry_after is not None:
        return min(max(retry_after, 1.0), 60.0)
    return min(2**attempt, 16) + 0.1 * (attempt % 5)


def _wait_before_retry(
    attempt: int,
    last_error: str,
    *,
    response: requests.Response | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    wait_seconds = _retry_wait_seconds(attempt, _parse_retry_after(response))
    _log_graphql(
        last_error,
        attempt=f"{attempt + 1}/{_MAX_GRAPHQL_ATTEMPTS}",
        retry_in_s=round(wait_seconds, 2),
        **_response_log_details(response),
        **(extra or {}),
    )
    time.sleep(wait_seconds)


def _graphql_errors_are_retryable(errors: list[Any]) -> bool:
    if not errors:
        return False
    for err in errors:
        if not isinstance(err, dict):
            return False
        err_type = str(err.get("type") or "").upper()
        message = str(err.get("message") or "").lower()
        if err_type in _RETRYABLE_GRAPHQL_ERROR_TYPES:
            continue
        if any(fragment in message for fragment in _RETRYABLE_GRAPHQL_MESSAGE_FRAGMENTS):
            continue
        return False
    return True


def _summarize_graphql_errors(errors: list[Any]) -> str:
    summaries: list[str] = []
    for err in errors:
        if not isinstance(err, dict):
            summaries.append(repr(err))
            continue
        err_type = err.get("type") or "UNKNOWN"
        message = str(err.get("message") or "").replace("\n", " ")
        if len(message) > 180:
            message = f"{message[:180].rstrip()}..."
        summaries.append(f"{err_type}: {message}" if message else str(err_type))
    return "; ".join(summaries) if summaries else "unknown GraphQL error"


def _run_graphql_query(
    query: str,
    variables: dict[str, Any],
    allow_rate_limit_wait: bool = False,
) -> dict[str, Any]:
    """Execute a GraphQL query with retry and rate-limit handling.

    Transport failures (502/504, truncated responses, empty bodies) are retried.
    This function never renders Streamlit UI; callers must log or surface errors
    outside ``refresh_mode="background"`` cache functions.
    """
    headers = get_graphql_headers()
    last_error: str | None = None
    operation = _graphql_operation_name(query)
    request_extra = {"operation": operation, "variables": variables}

    for attempt in range(_MAX_GRAPHQL_ATTEMPTS):
        response: requests.Response | None = None
        try:
            response = requests.post(
                GITHUB_GRAPHQL_ENDPOINT,
                headers=headers,
                json={"query": query, "variables": variables},
                timeout=_GRAPHQL_TIMEOUT_SECONDS,
            )
        except (RequestException, OSError, IncompleteRead) as exc:
            last_error = f"request failed ({type(exc).__name__}): {exc}"
            if attempt + 1 >= _MAX_GRAPHQL_ATTEMPTS:
                break
            _wait_before_retry(attempt, last_error, extra=request_extra)
            continue

        if response.status_code == 200:
            try:
                payload = response.json()
            except (RequestsJSONDecodeError, ValueError, TypeError):
                # GitHub occasionally returns a 200 with an empty or non-JSON
                # body (transient gateway/CDN hiccups). Treat it as retryable
                # instead of letting the JSONDecodeError crash the app.
                snippet = (response.text or "").strip()[:200]
                last_error = f"received 200 with non-JSON body: {snippet!r}"
                if attempt + 1 >= _MAX_GRAPHQL_ATTEMPTS:
                    break
                _wait_before_retry(attempt, last_error, response=response, extra=request_extra)
                continue

            if not isinstance(payload, dict):
                last_error = f"received 200 with non-object JSON: {type(payload).__name__}"
                if attempt + 1 >= _MAX_GRAPHQL_ATTEMPTS:
                    break
                _wait_before_retry(attempt, last_error, response=response, extra=request_extra)
                continue

            cost_info = (payload.get("extensions") or {}).get("cost")
            if isinstance(cost_info, dict):
                throttle_status = cost_info.get("throttleStatus") or {}
                _log_graphql(
                    "cost",
                    actual_cost=cost_info.get("actualQueryCost"),
                    remaining=throttle_status.get("remaining"),
                    reset_at=throttle_status.get("resetAt"),
                    operation=operation,
                )

            errors = payload.get("errors") or []
            if not isinstance(errors, list):
                errors = [errors]
            data = payload.get("data")

            if errors:
                error_summary = _summarize_graphql_errors(errors)
                rate_limited = any(
                    isinstance(err, dict)
                    and (
                        str(err.get("type") or "").upper() == "RATE_LIMITED"
                        or "rate limit" in str(err.get("message") or "").lower()
                    )
                    for err in errors
                )
                if rate_limited:
                    reset_at = None
                    if isinstance(data, dict):
                        reset_at = (data.get("rateLimit") or {}).get("resetAt")
                    wait_seconds = 5.0
                    if reset_at:
                        try:
                            reset_dt = datetime.fromisoformat(reset_at)
                            wait_seconds = max(5.0, (reset_dt - datetime.now(UTC)).total_seconds())
                        except ValueError:
                            wait_seconds = 5.0
                    last_error = f"rate limited: {error_summary}"
                    _log_graphql(
                        last_error,
                        attempt=f"{attempt + 1}/{_MAX_GRAPHQL_ATTEMPTS}",
                        retry_in_s=round(wait_seconds, 2),
                        operation=operation,
                    )
                    time.sleep(wait_seconds)
                    continue

                if isinstance(data, dict):
                    _log_graphql(
                        "returning partial data despite GraphQL errors",
                        errors=error_summary,
                        operation=operation,
                        request_id=(
                            response.headers.get("X-GitHub-Request-Id") or response.headers.get("x-github-request-id")
                        ),
                    )
                    return data

                last_error = f"GraphQL errors: {error_summary}"
                if _graphql_errors_are_retryable(errors) and attempt + 1 < _MAX_GRAPHQL_ATTEMPTS:
                    _wait_before_retry(attempt, last_error, response=response, extra=request_extra)
                    continue
                message = f"{last_error} (operation={operation})"
                raise GitHubGraphQLError(message)

            if not isinstance(data, dict):
                last_error = "received 200 with missing or non-object data"
                if attempt + 1 >= _MAX_GRAPHQL_ATTEMPTS:
                    break
                _wait_before_retry(attempt, last_error, response=response, extra=request_extra)
                continue

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
                last_error = "HTTP 403 with exhausted rate limit"
                _log_graphql(
                    last_error,
                    attempt=f"{attempt + 1}/{_MAX_GRAPHQL_ATTEMPTS}",
                    retry_in_s=wait_seconds,
                    operation=operation,
                )
                time.sleep(wait_seconds)
                continue

        if response.status_code in _RETRYABLE_HTTP_STATUS:
            last_error = f"received retryable status {response.status_code}"
            if attempt + 1 >= _MAX_GRAPHQL_ATTEMPTS:
                break
            _wait_before_retry(attempt, last_error, response=response, extra=request_extra)
            continue

        try:
            response.raise_for_status()
        except RequestException as exc:
            last_error = f"non-retryable HTTP {response.status_code}: {exc}"
            message = f"{last_error} (operation={operation}, details={_response_log_details(response)})"
            raise GitHubGraphQLError(message) from exc

        last_error = f"unexpected HTTP {response.status_code} without a JSON data payload"
        if attempt + 1 >= _MAX_GRAPHQL_ATTEMPTS:
            break
        _wait_before_retry(attempt, last_error, response=response, extra=request_extra)

    msg = f"GitHub GraphQL request failed after {_MAX_GRAPHQL_ATTEMPTS} attempts (operation={operation})."
    if last_error:
        msg = f"{msg} Last error: {last_error}"
    raise GitHubGraphQLError(msg)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).astimezone(UTC)
    except ValueError:
        return None


def _build_search_query(
    repo: str,
    base_branch: str,
    merged_since: date | None,
    merged_until: date | None,
) -> str:
    parts = [f"repo:{repo}", "is:pr", "is:merged", f"base:{base_branch}"]
    if merged_since:
        parts.append(f"merged:>={merged_since.isoformat()}")
    if merged_until:
        parts.append(f"merged:<={merged_until.isoformat()}")
    return " ".join(parts)


def _is_human_reviewer(typename: str, login: str | None, ignore_bots: bool) -> bool:
    if typename != "User" or not login:
        return False
    return not (ignore_bots and login.endswith("[bot]"))


PULL_REQUESTS_QUERY: Final[str] = """
query MergedPullRequests($owner: String!, $name: String!, $baseRef: String!, $cursor: String, $states: [PullRequestReviewState!], $direction: OrderDirection!) {
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
    pr_node: dict[str, Any],
    _review_states: Iterable[str],
    ignore_bots: bool,
    seen_pr_numbers: set[int],
) -> dict[str, Any] | None:
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
        _parse_iso_datetime(review.get("submittedAt")) for review in all_reviews if review.get("submittedAt")
    ]

    first_review_event = min(
        [dt for dt in review_times if dt is not None],
        default=None,
    )

    approvals = [
        dt
        for review in all_reviews
        if review.get("state") == "APPROVED" and review.get("submittedAt")
        for dt in [_parse_iso_datetime(review.get("submittedAt"))]
        if dt is not None
    ]
    earliest_approval = min(approvals) if approvals else None

    time_open_to_first_review = first_review_event - created_at if created_at and first_review_event else None

    post_first_candidates: list[datetime] = []
    if earliest_approval and first_review_event and earliest_approval >= first_review_event:
        post_first_candidates.append(earliest_approval)
    if merged_at and first_review_event and merged_at >= first_review_event:
        post_first_candidates.append(merged_at)

    time_first_review_to_merge_or_approval = (
        min(post_first_candidates) - first_review_event if first_review_event and post_first_candidates else None
    )

    time_open_to_merge = merged_at - created_at if created_at and merged_at else None

    num_review_comments = sum((review.get("comments") or {}).get("totalCount", 0) for review in all_reviews)

    reviewer_logins: set[str] = set()
    for review in all_reviews:
        author_info = review.get("author") or {}
        login = author_info.get("login")
        if login and _is_human_reviewer(author_info.get("__typename", ""), login, ignore_bots):
            reviewer_logins.add(login)

    reviewers = sorted(reviewer_logins)

    author_info = pr_node.get("author") or {}
    author_typename = author_info.get("__typename")
    author_login = author_info.get("login") if author_typename == "User" else None

    return {
        "pr_number": pr_number,
        "url": pr_node.get("url"),
        "title": pr_node.get("title"),
        "author": author_login,
        "from_bot": author_typename == "Bot" or (author_login and author_login.endswith("[bot]")),
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
        "loc_changes": (pr_node.get("additions", 0) or 0) + (pr_node.get("deletions", 0) or 0),
        "changed_files": pr_node.get("changedFiles", 0),
        "closing_issues": [
            node["number"] for node in (pr_node.get("closingIssuesReferences") or {}).get("nodes", []) if node
        ],
        "labels": [node["name"] for node in (pr_node.get("labels") or {}).get("nodes", []) if node],
    }


def _split_owner_repo(repo: str) -> tuple[str, str]:
    owner, name = repo.split("/", 1)
    return owner, name


def _cache_dir_for_branch(base_branch: str) -> Path:
    cache_dir = CACHE_BASE_DIR / base_branch
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _incremental_cache_path(base_branch: str) -> Path:
    cache_dir = _cache_dir_for_branch(base_branch)
    return cache_dir / "merged_prs.parquet"


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Loading merged PR metrics via GraphQL...", refresh_mode="background")
def fetch_merged_pr_metrics(
    repo: str = "streamlit/streamlit",
    base_branch: str = "develop",
    merged_since: date | None = None,
    merged_until: date | None = None,
    include_commented: bool = True,
    ignore_bots: bool = False,
    max_results: int | None = None,
    use_disk_cache: bool = False,
    paginate_ascending: bool = True,
    starting_cursor: str | None = None,
    full_history_cache_path: Path | None = None,
    resume_on_rate_limit: bool = False,
) -> pd.DataFrame:
    """Fetch merged PR metrics using the GitHub GraphQL API."""
    review_states: list[str] = ["APPROVED", "CHANGES_REQUESTED"]
    if include_commented:
        review_states.append("COMMENTED")

    existing_df: pd.DataFrame | None = None
    seen_pr_numbers: set[int] = set()
    records: list[dict[str, Any]] = []
    rate_stats: dict[str, Any] = {}
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
            try:
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
            except GitHubGraphQLError as exc:
                _log_graphql(
                    "aborting merged PR pagination after request failure",
                    error=str(exc),
                    collected=collected,
                    cursor=cursor,
                    page_count=rate_stats.get("page_count", 0),
                )
                # Keep partial results from earlier pages so a later 502 does not
                # discard work. Re-raise only when this call produced nothing, so
                # a background cache refresh can retain the previous value.
                if records or existing_df is not None or rate_stats.get("page_count"):
                    break
                raise
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
            record = _extract_pr_metrics(node, review_states, ignore_bots, seen_pr_numbers)
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
                reset_dt = datetime.fromisoformat(reset_at)
                sleep_seconds = max(5, (reset_dt - datetime.now(UTC)).total_seconds())
                _log_graphql(
                    "rate limit reached, pausing pagination",
                    retry_in_s=round(sleep_seconds),
                    remaining=remaining,
                    reset_at=reset_at,
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
