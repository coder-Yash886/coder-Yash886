#!/usr/bin/env python3
"""Refresh README GitHub stats and contribution graph URLs with live data."""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import date
from pathlib import Path

USERNAME = "coder-Yash886"
README = Path(__file__).parent / "README.md"


def fetch_contributions() -> int:
    for url in (
        f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last",
        f"https://github-contributions-api.deno.dev/{USERNAME}.json",
    ):
        try:
            with urllib.request.urlopen(url) as resp:
                data = json.load(resp)
            return (
                data.get("total", {}).get("lastYear")
                or data.get("contributions")
                or 0
            )
        except Exception:
            continue
    return 0


def update_readme() -> bool:
    today = date.today().isoformat()
    contributions = fetch_contributions()
    content = README.read_text(encoding="utf-8")

    stats_block = f"""# 📊 GitHub Stats

<!-- stats-updated: {today} | contributions: {contributions} -->

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github-readme-stats.vercel.app/api?username={USERNAME}&show_icons=true&theme=radical&hide_border=false&include_all_commits=true&count_private=true&v={today}">
  <img src="https://github-readme-stats.vercel.app/api?username={USERNAME}&show_icons=true&theme=default&hide_border=false&include_all_commits=true&count_private=true&v={today}" alt="GitHub Stats" height="165"/>
</picture>

<img src="https://github-readme-stats.vercel.app/api/top-langs/?username={USERNAME}&layout=compact&theme=radical&hide_border=false&langs_count=8&v={today}" alt="Top Languages" height="165"/>

<br/><br/>

![Profile views](https://komarev.com/ghpvc/?username={USERNAME}&label=Profile%20views&color=0e75b6&style=for-the-badge)

</div>"""

    graph_block = f"""# 📈 Contribution Graph

<!-- graph-updated: {today} | contributions: {contributions} -->

<div align="center">

<img src="https://github-readme-activity-graph.vercel.app/graph?username={USERNAME}&theme=tokyo-night&hide_border=true&area=true&custom_title=Contributions%20in%20the%20last%20year&v={today}" alt="Contribution Graph" />

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
