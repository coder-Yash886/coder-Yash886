#!/usr/bin/env python3
"""Refresh README GitHub stats and contribution graph URLs with live data."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from github_stats import USERNAME, fetch_user_stats

README = Path(__file__).parent / "README.md"


def update_readme() -> bool:
    today = date.today().isoformat()
    stats = fetch_user_stats()
    contributions = stats["contributions"]
    content = README.read_text(encoding="utf-8")

    stats_block = f"""# 📊 GitHub Stats

<!-- stats-updated: {today} | contributions: {contributions} | stars: {stats.get("stars", 0)} -->

<div align="center">

![GitHub Stats](./assets/github-stats.svg)

![Top Languages](./assets/top-langs.svg)

<br>

![Profile views](https://komarev.com/ghpvc/?username={USERNAME}&label=Profile%20views&color=0e75b6&style=for-the-badge)

</div>"""

    graph_block = f"""# 📈 Contribution Graph

<!-- graph-updated: {today} | contributions: {contributions} -->

<div align="center">

<img src="https://github-readme-activity-graph.vercel.app/graph?username={USERNAME}&theme=tokyo-night&hide_border=true&area=true&custom_title=Contributions%20in%20the%20last%20year&v={today}" alt="Contribution Graph" width="100%" />

</div>"""

    updated, count = re.subn(
        r"# 📊 GitHub Stats\n\n.*?\n\n---",
        stats_block + "\n\n---",
        content,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        return False

    updated, count = re.subn(
        r"# 📈 Contribution Graph\n\n.*?\n\n# 🏆 Achievements",
        graph_block + "\n\n# 🏆 Achievements",
        updated,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        return False

    if updated != content:
        README.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = update_readme()
    print("README updated." if changed else "README already up to date.")


if __name__ == "__main__":
    main()
