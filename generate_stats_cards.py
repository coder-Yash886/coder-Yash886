#!/usr/bin/env python3
"""Generate local GitHub stats SVG cards using GITHUB_TOKEN (includes private)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from github_stats import USERNAME, fetch_top_languages, fetch_user_stats, get_token

ASSETS = Path(__file__).parent / "assets"
STATS_SVG = ASSETS / "github-stats.svg"
LANGS_SVG = ASSETS / "top-langs.svg"


def build_stats_svg(stats: dict[str, int]) -> str:
    items = [
        ("⭐ Stars", stats.get("stars", 0)),
        ("📦 Repos", stats["repos"]),
        ("🔥 Contributions", stats["contributions"]),
        ("👥 Followers", stats["followers"]),
    ]
    rows = []
    y = 70
    for label, value in items:
        rows.append(f'<text x="30" y="{y}" class="label">{label}</text>')
        rows.append(f'<text x="300" y="{y}" class="value">{value:,}</text>')
        y += 42

    token_note = "with private data" if get_token() else "public data only"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="420" height="230">
<style>
  .title {{ font: bold 18px sans-serif; fill: #58a6ff; }}
  .label {{ font: 14px sans-serif; fill: #c9d1d9; }}
  .value {{ font: bold 20px sans-serif; fill: #f78166; text-anchor: end; }}
  .sub {{ font: 11px sans-serif; fill: #8b949e; }}
</style>
<rect width="420" height="230" rx="10" fill="#0d1117" stroke="#30363d"/>
<text x="20" y="32" class="title">GitHub Stats</text>
<text x="20" y="50" class="sub">@{USERNAME} · {token_note}</text>
{chr(10).join(rows)}
</svg>
"""


def build_langs_svg(languages: list[tuple[str, int, str]]) -> str:
    if not languages:
        languages = [("No data", 1, "#8b949e")]

    total = sum(size for _, size, _ in languages)
    rows = []
    y = 58
    for name, size, color in languages:
        pct = (size / total) * 100 if total else 0
        bar_w = max(4, int(300 * size / total))
        rows.append(f'<text x="20" y="{y}" class="label">{name}</text>')
        rows.append(f'<text x="390" y="{y}" class="pct">{pct:.1f}%</text>')
        rows.append(
            f'<rect x="20" y="{y + 6}" width="{bar_w}" height="10" rx="3" fill="{color}"/>'
        )
        y += 34

    height = max(120, y + 10)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{height}">
<style>
  .title {{ font: bold 18px sans-serif; fill: #58a6ff; }}
  .label {{ font: 13px sans-serif; fill: #c9d1d9; }}
  .pct {{ font: 12px sans-serif; fill: #8b949e; text-anchor: end; }}
</style>
<rect width="420" height="{height}" rx="10" fill="#0d1117" stroke="#30363d"/>
<text x="20" y="32" class="title">Top Languages</text>
{chr(10).join(rows)}
</svg>
"""


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    stats = fetch_user_stats()
    languages = fetch_top_languages()

    STATS_SVG.write_text(build_stats_svg(stats), encoding="utf-8")
    LANGS_SVG.write_text(build_langs_svg(languages), encoding="utf-8")

    print(f"Token used: {'yes' if get_token() else 'no (public only)'}")
    print(f"Generated {STATS_SVG} and {LANGS_SVG}")
    print(f"Stats: {stats} | updated: {date.today().isoformat()}")


if __name__ == "__main__":
    main()
