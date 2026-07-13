#!/usr/bin/env python3
"""Refresh README contribution graph URL only (stats use separate workflows)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from github_stats import USERNAME, fetch_user_stats

README = Path(__file__).parent / "README.md"


def update_readme() -> bool:
    today = date.today().isoformat()
    contributions = fetch_user_stats()["contributions"]
    content = README.read_text(encoding="utf-8")

    graph_block = f"""# 📈 Contribution Graph

<!-- graph-updated: {today} | contributions: {contributions} -->

<div align="center">

<img src="https://github-readme-activity-graph.vercel.app/graph?username={USERNAME}&theme=tokyo-night&hide_border=true&area=true&custom_title=Contributions%20in%20the%20last%20year&v={today}" alt="Contribution Graph" width="100%" />

</div>"""

    updated, count = re.subn(
        r"# 📈 Contribution Graph\n\n.*?\n\n# 🏆 Achievements",
        graph_block + "\n\n# 🏆 Achievements",
        content,
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
