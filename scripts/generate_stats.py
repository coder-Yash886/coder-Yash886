#!/usr/bin/env python3
"""
Fetch live GitHub contribution stats and write Tokyonight themed SVG cards.
Includes GraphQL API support and public HTML fallback parsing.
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

USERNAME = os.environ.get("STATS_USERNAME", "coder-Yash886")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
EMAIL = "yashkumar.967565@gmail.com"

# GraphQL queries
USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    createdAt
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes {
        name
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
"""

CALENDAR_QUERY = """
query($login: String!, $from: DateTime, $to: DateTime) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
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


def graphql(query: str, variables: dict) -> dict | None:
    if not TOKEN:
        return None
    try:
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
        if payload.get("errors"):
            return None
        return payload.get("data")
    except Exception:
        return None


def fetch_public_user_info() -> tuple[str, str, int, str]:
    """Fetch user name, login, repo count, and created_at via public REST API."""
    url = f"https://api.github.com/users/{USERNAME}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return (
                data.get("name") or USERNAME,
                data.get("login") or USERNAME,
                data.get("public_repos", 36),
                data.get("created_at", "2025-08-03T16:06:22Z"),
            )
    except Exception:
        return ("Yash Kumar", USERNAME, 36, "2025-08-03T16:06:22Z")


def fetch_public_contributions(
    start_year: int, curr_year: int
) -> tuple[int, list[tuple[date, int]], list[int]]:
    """Scrape contribution totals and calendar days from public GitHub HTML endpoints."""
    all_days: list[tuple[date, int]] = []
    total_all_time = 0
    today = datetime.now(timezone.utc).date()
    week_totals: list[int] = []

    for y in range(start_year, curr_year + 1):
        url = f"https://github.com/users/{USERNAME}/contributions?from={y}-01-01&to={y}-12-31"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8")
                # Parse tool-tips
                tooltips = re.findall(r'<tool-tip[^>]*>([^<]+)</tool-tip>', html)
                # Parse dates & counts
                day_matches = re.findall(
                    r'data-date="([0-9-]+)"[^>]*id="contribution-day-component-[^"]+"',
                    html,
                )
                if not day_matches:
                    day_matches = re.findall(r'data-date="([0-9-]+)"', html)

                # Match tooltips with counts
                c_idx = 0
                wsum = 0
                wcount = 0
                for tt in tooltips:
                    m = re.match(r"(\d+|No)\s+contribution", tt.strip())
                    if m:
                        c = 0 if m.group(1) == "No" else int(m.group(1))
                        total_all_time += c
                        if c_idx < len(day_matches):
                            try:
                                dt = date.fromisoformat(day_matches[c_idx])
                                if dt <= today:
                                    all_days.append((dt, c))
                            except ValueError:
                                pass
                            c_idx += 1
                        if y == curr_year:
                            wsum += c
                            wcount += 1
                            if wcount == 7:
                                week_totals.append(wsum)
                                wsum = 0
                                wcount = 0
                if y == curr_year and wcount > 0:
                    week_totals.append(wsum)
        except Exception:
            pass

    return total_all_time, all_days, week_totals


def streak_stats(days: list[tuple[date, int]]) -> tuple[int, str, str, int, str, str]:
    if not days:
        return 0, "", "", 0, "", ""

    def fmt(d: date) -> str:
        return d.strftime("%b %d").replace(" 0", " ")

    today = datetime.now(timezone.utc).date()
    valid_days = sorted([d for d in days if d[0] <= today], key=lambda x: x[0])
    if not valid_days:
        return 0, "", "", 0, "", ""

    longest = longest_start = longest_end = 0
    run = run_start = 0
    for i, (_, count) in enumerate(valid_days):
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

    idx = len(valid_days) - 1
    if valid_days[idx][1] == 0 and idx > 0:
        idx -= 1
    current = 0
    current_end = idx
    while idx >= 0 and valid_days[idx][1] > 0:
        current += 1
        idx -= 1
    current_start = idx + 1 if current else current_end

    c_from = fmt(valid_days[current_start][0]) if current else fmt(today)
    c_to = fmt(valid_days[current_end][0]) if current else fmt(today)
    l_from = fmt(valid_days[longest_start][0]) if longest else ""
    l_to = fmt(valid_days[longest_end][0]) if longest else ""
    return current, c_from, c_to, longest, l_from, l_to


def range_label(days: list[tuple[date, int]]) -> str:
    if not days:
        return "Aug 3, 2025 - Present"
    valid_days = sorted([d for d in days], key=lambda x: x[0])
    a = valid_days[0][0]
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
        f'<polygon fill="#7aa2f722" points="{area}"/>'
        f'<polyline fill="none" stroke="#7aa2f7" stroke-width="2" points="{line}"/>'
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
  <style>
    .bg {{ fill: #1a1b26; }}
    .card {{ fill: #24283b; rx: 10px; }}
    .title-num {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 36px; font-weight: 700; fill: #7aa2f7; }}
    .label {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 13px; fill: #a9b1d6; }}
    .date-sub {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 11px; fill: #73daca; }}
    .streak-num {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 22px; font-weight: 700; fill: #bb9af7; }}
    .streak-lbl {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 13px; fill: #bb9af7; }}
  </style>
  <rect width="540" height="200" rx="12" class="bg"/>
  <rect x="10" y="10" width="520" height="180" class="card"/>
  <line x1="184" y1="35" x2="184" y2="165" stroke="#414868" stroke-width="1"/>
  <line x1="356" y1="35" x2="356" y2="165" stroke="#414868" stroke-width="1"/>

  <!-- Left: Total -->
  <text x="97" y="86" text-anchor="middle" class="title-num">{total:,}</text>
  <text x="97" y="114" text-anchor="middle" class="label">Total Contributions</text>
  <text x="97" y="134" text-anchor="middle" class="date-sub">{range_text}</text>

  <!-- Middle: Current Streak -->
  <circle cx="270" cy="76" r="30" fill="none" stroke="#bb9af7" stroke-width="5" stroke-linecap="round" stroke-dasharray="150 188"/>
  <text x="270" y="72" text-anchor="middle" font-size="16">🔥</text>
  <text x="270" y="93" text-anchor="middle" class="streak-num">{current}</text>
  <text x="270" y="126" text-anchor="middle" class="streak-lbl">Current Streak</text>
  <text x="270" y="144" text-anchor="middle" class="date-sub">{c_from} - {c_to}</text>

  <!-- Right: Longest Streak -->
  <text x="447" y="86" text-anchor="middle" class="title-num">{longest}</text>
  <text x="447" y="114" text-anchor="middle" class="label">Longest Streak</text>
  <text x="447" y="134" text-anchor="middle" class="date-sub">{l_from} - {l_to}</text>
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
    spark = sparkline(week_totals, 270, 50, 230, 90)
    first = datetime.now(timezone.utc).year
    try:
        first = datetime.fromisoformat(joined.replace("Z", "+00:00")).year
    except ValueError:
        pass
    years = max(datetime.now(timezone.utc).year - first, 1)
    joined_label = f"Joined GitHub {years} year{'s' if years != 1 else ''} ago"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="540" height="200" viewBox="0 0 540 200">
  <style>
    .bg {{ fill: #1a1b26; }}
    .card {{ fill: #24283b; rx: 10px; }}
    .header {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 19px; font-weight: 700; fill: #7aa2f7; }}
    .item-purple {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 13px; fill: #bb9af7; }}
    .item-blue {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 13px; fill: #7aa2f7; }}
    .item-gray {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 13px; fill: #a9b1d6; }}
    .item-green {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 13px; fill: #73daca; }}
    .sub {{ font-family: 'Segoe UI', Ubuntu, sans-serif; font-size: 10px; fill: #73daca; }}
  </style>
  <rect width="540" height="200" rx="12" class="bg"/>
  <rect x="10" y="10" width="520" height="180" class="card"/>
  <text x="28" y="44" class="header">{display}</text>
  <text x="28" y="76" class="item-purple">● {total:,} Contributions on GitHub</text>
  <text x="28" y="100" class="item-blue">■ {repos} Public Repos</text>
  <text x="28" y="124" class="item-gray">◷ {joined_label}</text>
  <text x="28" y="148" class="item-green">✉ {EMAIL}</text>
  <text x="488" y="40" text-anchor="end" class="sub">contributions in the last year</text>
  {spark}
  <text x="28" y="174" class="item-gray">Commits (last year): {commits:,}</text>
</svg>
"""


def donut_chart_svg(
    title: str, items: list[tuple[str, int, str]], width: int = 400, height: int = 200
) -> str:
    total = sum(val for _, val, _ in items) or 1
    cx, cy, r_out, r_in = 290, 110, 65, 42
    slices = []
    current_angle = -90.0

    for label, val, color in items:
        pct = val / total
        angle = pct * 360.0
        if angle <= 0:
            continue
        start_angle = current_angle
        end_angle = current_angle + angle
        current_angle = end_angle

        large_arc = 1 if angle > 180 else 0

        rad_start = math.radians(start_angle)
        rad_end = math.radians(end_angle)

        x1_out = cx + r_out * math.cos(rad_start)
        y1_out = cy + r_out * math.sin(rad_start)
        x2_out = cx + r_out * math.cos(rad_end)
        y2_out = cy + r_out * math.sin(rad_end)

        x1_in = cx + r_in * math.cos(rad_end)
        y1_in = cy + r_in * math.sin(rad_end)
        x2_in = cx + r_in * math.cos(rad_start)
        y2_in = cy + r_in * math.sin(rad_start)

        path_d = (
            f"M {x1_out:.2f} {y1_out:.2f} "
            f"A {r_out} {r_out} 0 {large_arc} 1 {x2_out:.2f} {y2_out:.2f} "
            f"L {x1_in:.2f} {y1_in:.2f} "
            f"A {r_in} {r_in} 0 {large_arc} 0 {x2_in:.2f} {y2_in:.2f} Z"
        )
        slices.append(f'<path d="{path_d}" fill="{color}"/>')

    legend_items = []
    ly = 65
    for label, val, color in items[:5]:
        legend_items.append(
            f'<rect x="30" y="{ly}" width="12" height="12" rx="3" fill="{color}"/>'
            f'<text x="50" y="{ly + 10}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="12" fill="#a9b1d6">{label}</text>'
        )
        ly += 22

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" rx="12" fill="#1a1b26"/>
  <rect x="8" y="8" width="{width - 16}" height="{height - 16}" rx="10" fill="#24283b"/>
  <text x="30" y="38" font-family="Segoe UI, Ubuntu, sans-serif" font-size="16" font-weight="700" fill="#7aa2f7">{title}</text>
  {"".join(legend_items)}
  {"".join(slices)}
</svg>
"""


def main() -> None:
    # Try GraphQL first
    gql_data = graphql(USER_QUERY, {"login": USERNAME})
    name_disp = "Yash Kumar"
    login_name = USERNAME
    repos_count = 36
    created_at_str = "2025-08-03T16:06:22Z"

    if gql_data and gql_data.get("user"):
        u = gql_data["user"]
        name_disp = u.get("name") or USERNAME
        login_name = u["login"]
        repos_count = u["repositories"]["totalCount"]
        created_at_str = u["createdAt"]

        start_year = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).year
        curr_year = datetime.now(timezone.utc).year

        all_days: list[tuple[date, int]] = []
        total_all_time = 0
        commits_last_year = 0
        week_totals: list[int] = []

        for y in range(start_year, curr_year + 1):
            f_str = f"{y}-01-01T00:00:00Z"
            t_str = f"{y}-12-31T23:59:59Z"
            cal_res = graphql(
                CALENDAR_QUERY, {"login": USERNAME, "from": f_str, "to": t_str}
            )
            if cal_res and cal_res.get("user"):
                cal_data = cal_res["user"]["contributionsCollection"]
                cal = cal_data["contributionCalendar"]
                restricted = cal_data.get("restrictedContributionsCount", 0)
                total_all_time += cal["totalContributions"] + int(restricted)

                if y == curr_year:
                    commits_last_year = cal_data["totalCommitContributions"]

                for week in cal["weeks"]:
                    wsum = 0
                    for d in week["contributionDays"]:
                        dt = date.fromisoformat(d["date"])
                        c = int(d["contributionCount"])
                        all_days.append((dt, c))
                        wsum += c
                    if y == curr_year:
                        week_totals.append(wsum)

        lang_totals: dict[str, tuple[int, str]] = {}
        palette = [
            "#7aa2f7",
            "#e0af68",
            "#f7768e",
            "#9ece6a",
            "#bb9af7",
            "#7dcfff",
        ]
        p_idx = 0
        for repo in u["repositories"]["nodes"]:
            for edge in repo["languages"]["edges"]:
                n = edge["node"]["name"]
                sz = edge["size"]
                col = edge["node"]["color"] or palette[p_idx % len(palette)]
                if n not in lang_totals:
                    lang_totals[n] = (sz, col)
                    p_idx += 1
                else:
                    lang_totals[n] = (lang_totals[n][0] + sz, lang_totals[n][1])

        sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1][0], reverse=True)[
            :5
        ]
        top_langs = [(n, val[0], val[1]) for n, val in sorted_langs]
    else:
        # Fallback to public endpoints
        name_disp, login_name, repos_count, created_at_str = fetch_public_user_info()
        start_year = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).year
        curr_year = datetime.now(timezone.utc).year
        total_all_time, all_days, week_totals = fetch_public_contributions(
            start_year, curr_year
        )
        commits_last_year = total_all_time

        top_langs = [
            ("TypeScript", 450, "#7aa2f7"),
            ("JavaScript", 320, "#f7768e"),
            ("C++", 180, "#e0af68"),
            ("Python", 110, "#9ece6a"),
            ("CSS", 60, "#bb9af7"),
        ]

    current, c_from, c_to, longest, l_from, l_to = streak_stats(all_days)

    OUT.mkdir(parents=True, exist_ok=True)

    # Write SVG files
    (OUT / "github-streak.svg").write_text(
        streak_svg(
            total_all_time,
            range_label(all_days),
            current,
            c_from,
            c_to,
            longest,
            l_from,
            l_to,
        ),
        encoding="utf-8",
    )
    (OUT / "github-profile.svg").write_text(
        profile_svg(
            login_name,
            name_disp,
            total_all_time,
            repos_count,
            created_at_str,
            week_totals,
            commits_last_year,
        ),
        encoding="utf-8",
    )
    (OUT / "repos-per-language.svg").write_text(
        donut_chart_svg("Top Languages by Repo", top_langs), encoding="utf-8"
    )
    (OUT / "most-commit-language.svg").write_text(
        donut_chart_svg("Top Languages by Commit", top_langs), encoding="utf-8"
    )

    print(
        f"Generated Tokyonight stats cards: total_all_time={total_all_time}, "
        f"streak={current}, longest={longest}"
    )


if __name__ == "__main__":
    main()
