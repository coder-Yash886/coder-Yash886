#!/usr/bin/env python3
"""GitHub API helpers with optional token for private contributions."""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

USERNAME = os.environ.get("GITHUB_USERNAME", "coder-Yash886")
GRAPHQL_URL = "https://api.github.com/graphql"


def get_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("PAT")


def graphql_request(query: str, variables: dict) -> dict:
    token = get_token()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "coder-Yash886-profile-stats",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as resp:
        payload = json.load(resp)

    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


def fetch_user_stats(username: str = USERNAME) -> dict[str, int]:
    """Fetch stats; uses token when available for private contributions."""
    token = get_token()

    if token:
        try:
            return _fetch_stats_graphql(username)
        except Exception:
            pass

    return _fetch_stats_public(username)


def _fetch_stats_public(username: str) -> dict[str, int]:
    with urllib.request.urlopen(f"https://api.github.com/users/{username}") as resp:
        user = json.load(resp)

    contributions = 0
    for url in (
        f"https://github-contributions-api.jogruber.de/v4/{username}?y=last",
        f"https://github-contributions-api.deno.dev/{username}.json",
    ):
        try:
            with urllib.request.urlopen(url) as resp:
                data = json.load(resp)
            contributions = (
                data.get("total", {}).get("lastYear")
                or data.get("contributions")
                or 0
            )
            if contributions:
                break
        except Exception:
            continue

    stars = 0
    page = 1
    while True:
        with urllib.request.urlopen(
            f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
        ) as resp:
            repos = json.load(resp)
        if not repos:
            break
        stars += sum(repo.get("stargazers_count", 0) for repo in repos)
        if len(repos) < 100:
            break
        page += 1

    return {
        "repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "contributions": contributions,
        "stars": stars,
    }


def _fetch_stats_graphql(username: str) -> dict[str, int]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365)

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        repositories { totalCount }
        followers { totalCount }
        following { totalCount }
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar { totalContributions }
        }
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
          nodes {
            stargazers { totalCount }
            languages(first: 10) {
              edges { size node { name color } }
            }
          }
        }
      }
    }
    """
    data = graphql_request(
        query,
        {
            "login": username,
            "from": start.isoformat(),
            "to": end.isoformat(),
        },
    )
    user = data["user"]
    repos_nodes = user["repositories"]["nodes"] or []

    return {
        "repos": user["repositories"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "following": user["following"]["totalCount"],
        "contributions": user["contributionsCollection"]["contributionCalendar"][
            "totalContributions"
        ],
        "stars": sum(repo["stargazers"]["totalCount"] for repo in repos_nodes),
    }


def fetch_top_languages(username: str = USERNAME, limit: int = 5) -> list[tuple[str, int, str]]:
    token = get_token()
    if not token:
        return []

    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
          nodes {
            languages(first: 10) {
              edges { size node { name color } }
            }
          }
        }
      }
    }
    """
    try:
        data = graphql_request(query, {"login": username})
    except Exception:
        return []

    totals: dict[str, list] = {}
    for repo in data["user"]["repositories"]["nodes"] or []:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            size = edge["size"]
            color = edge["node"]["color"] or "#8b949e"
            if name not in totals:
                totals[name] = [0, color]
            totals[name][0] += size

    ranked = sorted(totals.items(), key=lambda item: item[1][0], reverse=True)
    return [(name, size, color) for name, (size, color) in ranked[:limit]]
