#!/usr/bin/env python3
"""Fetch live GitHub contribution stats and write SVG cards."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

USERNAME = os.environ.get("STATS_USERNAME", "coder-Yash886")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
EMAIL = "yashkumar.967565@gmail.com"

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    createdAt
    repositories(ownerAffiliations: OWNER, isFork: false) {
      totalCount
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def graphql(query: str, variables: dict) -> dict:
    if not TOKEN:
        raise SystemExit("GH_TOKEN / GITHUB_TOKEN is required")
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "coder-Yash886-stats",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        payload = json.loads(resp.read().decode())
    if payload.get("errors"):
        raise SystemExit(payload["errors"])
    return payload["data"]


def streak_stats(days: list[tuple[date, int]]) -> tuple[int, str, str, int, str, str]:
    """Return current_len, current_from, current_to, longest_len, longest_from, longest_to."""
    if not days:
        return 0, "", "", 0, "", ""

    def fmt(d: date) -> str:
        return d.strftime("%b %d").replace(" 0", " ")

    longest = longest_start = longest_end = 0
    run = run_start = 0
    for i, (_, count) in enumerate(days):
        if count > 0:
            if run == 0:
                run_start = i
            run += 1
            if run > longest:
                longest = run
                longest_start = run_start
                longest_end = i
        else:
            run = 0

    today = date.today()
    idx = len(days) - 1
    # If today has 0, GitHub still counts a streak ending yesterday.
    if days[idx][1] == 0 and idx > 0:
        idx -= 1
    current = 0
    current_end = idx
    while idx >= 0 and days[idx][1] > 0:
        current += 1
        idx -= 1
    current_start = idx + 1 if current else current_end

    c_from = fmt(days[current_start][0]) if current else fmt(today)
    c_to = fmt(days[current_end][0]) if current else fmt(today)
    l_from = fmt(days[longest_start][0]) if longest else ""
    l_to = fmt(days[longest_end][0]) if longest else ""
    return current, c_from, c_to, longest, l_from, l_to


def range_label(days: list[tuple[date, int]]) -> str:
    if not days:
        return ""
    a, b = days[0][0], days[-1][0]
    return f"{a.strftime('%b %d, %Y').replace(' 0', ' ')} - Present"


def sparkline(values: list[int], x: float, y: float, w: float, h: float) -> str:
    if not values:
        return ""
    mx = max(values) or 1
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        px = x + (w * i / max(n - 1, 1))
        py = y + h - (h * v / mx)
        pts.append(f"{px:.1f},{py:.1f}")
    line = " ".join(pts)
    area = f"{x:.1f},{y + h:.1f} " + line + f" {x + w:.1f},{y + h:.1f}"
    return (
        f'<polygon fill="#a371f733" points="{area}"/>'
        f'<polyline fill="none" stroke="#a371f7" stroke-width="2.2" points="{line}"/>'
    )


def streak_svg(
    total: int,
    range_text: str,
    current: int,
    c_from: str,
    c_to: str,
    longest: int,
    l_from: str,
    l_to: str,
) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="540" height="200" viewBox="0 0 540 200">
  <rect width="540" height="200" rx="12" fill="#0d1117"/>
  <rect x="8" y="8" width="524" height="184" rx="10" fill="#161b22"/>
  <line x1="186" y1="36" x2="186" y2="164" stroke="#30363d" stroke-width="1"/>
  <line x1="354" y1="36" x2="354" y2="164" stroke="#30363d" stroke-width="1"/>
  <text x="97" y="88" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="36" font-weight="700" fill="#79b8ff">{total:,}</text>
  <text x="97" y="116" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#8b949e">Total Contributions</text>
  <text x="97" y="136" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" fill="#3fb950">{range_text}</text>
  <circle cx="270" cy="78" r="32" fill="none" stroke="#a371f7" stroke-width="6" stroke-linecap="round" stroke-dasharray="160 201"/>
  <text x="270" y="74" text-anchor="middle" font-size="16">🔥</text>
  <text x="270" y="96" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="22" font-weight="700" fill="#d2a8ff">{current}</text>
  <text x="270" y="128" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#d2a8ff">Current Streak</text>
  <text x="270" y="146" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" fill="#3fb950">{c_from} - {c_to}</text>
  <text x="447" y="88" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="36" font-weight="700" fill="#79b8ff">{longest}</text>
  <text x="447" y="116" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#8b949e">Longest Streak</text>
  <text x="447" y="136" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" fill="#3fb950">{l_from} - {l_to}</text>
</svg>
"""


def profile_svg(
    login: str,
    name: str,
    total: int,
    repos: int,
    joined: str,
    week_totals: list[int],
    commits: int,
) -> str:
    display = f"{login} ({name})" if name and name != login else login
    spark = sparkline(week_totals, 268, 52, 230, 88)
    first = datetime.now(timezone.utc).year
    try:
        first = datetime.fromisoformat(joined.replace("Z", "+00:00")).year
    except ValueError:
        pass
    years = max(datetime.now(timezone.utc).year - first, 1)
    joined_label = f"Joined GitHub {years} year{'s' if years != 1 else ''} ago"
    ticks = ""
    if week_totals:
        # 5 date labels across the sparkline
        pass
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="540" height="200" viewBox="0 0 540 200">
  <rect width="540" height="200" rx="12" fill="#0d1117"/>
  <rect x="8" y="8" width="524" height="184" rx="10" fill="#161b22"/>
  <text x="28" y="44" font-family="Segoe UI, Ubuntu, sans-serif" font-size="20" font-weight="700" fill="#79b8ff">{display}</text>
  <text x="28" y="78" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#d2a8ff">● {total:,} Contributions on GitHub</text>
  <text x="28" y="102" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#79b8ff">■ {repos} Public Repos</text>
  <text x="28" y="126" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#8b949e">◷ {joined_label}</text>
  <text x="28" y="150" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" fill="#3fb950">✉ {EMAIL}</text>
  <text x="488" y="40" text-anchor="end" font-family="Segoe UI, Ubuntu, sans-serif" font-size="10" fill="#3fb950">contributions in the last year</text>
  {spark}
  <text x="28" y="176" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" fill="#8b949e">Commits (last year): {commits:,}</text>
</svg>
"""


def main() -> None:
    data = graphql(QUERY, {"login": USERNAME})["user"]
    cal = data["contributionsCollection"]["contributionCalendar"]
    restricted = data["contributionsCollection"].get("restrictedContributionsCount", 0)
    total = cal["totalContributions"] + int(restricted)
    days: list[tuple[date, int]] = []
    week_totals: list[int] = []
    for week in cal["weeks"]:
        wsum = 0
        for d in week["contributionDays"]:
            dt = date.fromisoformat(d["date"])
            c = int(d["contributionCount"])
            days.append((dt, c))
            wsum += c
        week_totals.append(wsum)

    current, c_from, c_to, longest, l_from, l_to = streak_stats(days)
    commits = data["contributionsCollection"]["totalCommitContributions"]
    repos = data["repositories"]["totalCount"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "github-streak.svg").write_text(
        streak_svg(total, range_label(days), current, c_from, c_to, longest, l_from, l_to),
        encoding="utf-8",
    )
    name_display = data.get("name") or data["login"]
    (OUT / "github-profile.svg").write_text(
        profile_svg(
            data["login"],
            name_display,
            total,
            repos,
            data["createdAt"],
            week_totals,
            commits,
        ),
        encoding="utf-8",
    )
    print(f"Wrote stats: contributions={total} (restricted={restricted}) commits={commits} streak={current} longest={longest}")


if __name__ == "__main__":
    main()
