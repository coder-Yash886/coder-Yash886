#!/usr/bin/env python3
"""Generate neofetch-style SVG cards for GitHub profile README."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"
PROFILE = ASSETS / "profile.png"
ASCII_FILE = ASSETS / "ascii-art.txt"
USERNAME = "coder-Yash886"


def generate_ascii_art() -> list[str]:
    img = Image.open(PROFILE).convert("L")
    w, h = img.size
    left, top, right, bottom = int(w * 0.25), int(h * 0.05), int(w * 0.75), int(h * 0.55)
    img = img.crop((left, top, right, bottom))
    img = ImageEnhance.Contrast(img).enhance(1.5)

    ascii_w, ascii_h = 22, 22
    img = img.resize((ascii_w, ascii_h))

    chars = " .:-=+*#%@"
    lines: list[str] = []
    for y in range(ascii_h):
        row = ""
        for x in range(ascii_w):
            pixel = img.getpixel((x, y))
            idx = int(pixel / 255 * (len(chars) - 1))
            row += chars[idx]
        lines.append(row)

    ASCII_FILE.write_text("\n".join(lines))
    return lines


def fetch_github_stats() -> dict[str, int]:
    with urllib.request.urlopen(f"https://api.github.com/users/{USERNAME}") as resp:
        user = json.load(resp)

    try:
        with urllib.request.urlopen(
            f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
        ) as resp:
            contrib = json.load(resp)
        contributions = contrib.get("total", {}).get("lastYear", 0)
    except Exception:
        contributions = 0

    return {
        "repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "contributions": contributions,
    }


def pad_dots(label: str, value: str, total_width: int = 28) -> str:
    dots = max(1, total_width - len(label) - len(value))
    return "." * dots


def build_svg(ascii_lines: list[str], stats: dict[str, int], theme: str) -> str:
    if theme == "dark":
        bg = "#161b22"
        text = "#c9d1d9"
        key = "#ffa657"
        value = "#a5d6ff"
        cc = "#616e7f"
        add = "#3fb950"
        del_ = "#f85149"
    else:
        bg = "#ffffff"
        text = "#24292f"
        key = "#953800"
        value = "#0550ae"
        cc = "#8b949e"
        add = "#1a7f37"
        del_ = "#cf222e"

    ascii_y_start = 30
    ascii_line_height = 20
    ascii_tspans = "\n".join(
        f'<tspan x="15" y="{ascii_y_start + i * ascii_line_height}">{line:<22}</tspan>'
        for i, line in enumerate(ascii_lines)
    )

    info_x = 390
    lines = [
        ("OS", "Linux, Windows, Android"),
        ("Host", "AKGEC, Ghaziabad, India"),
        ("Kernel", "Backend Developer @ OSS RNDC"),
        ("IDE", "VS Code, Cursor"),
        ("", ""),
        ("Languages.Programming", "JavaScript, TypeScript, C++, Python"),
        ("Languages.Computer", "HTML, CSS, JSON, YAML, Markdown"),
        ("Languages.Real", "English, Hindi"),
        ("", ""),
        ("Hobbies.Software", "Open Source, DSA, Hackathons"),
        ("Hobbies.Hardware", "Cloud, DevOps, System Design"),
    ]

    info_tspans: list[str] = []
    y = 30
    info_tspans.append(
        f'<tspan x="{info_x}" y="{y}">yash@{USERNAME}</tspan> '
        f"-{'—' * 42}-"
    )
    y += 20

    for label, val in lines:
        if not label:
            info_tspans.append(f'<tspan x="{info_x}" y="{y}" class="cc">. </tspan>')
        else:
            dots = pad_dots(label, val)
            info_tspans.append(
                f'<tspan x="{info_x}" y="{y}" class="cc">. </tspan>'
                f'<tspan class="key">{label}</tspan>:'
                f'<tspan class="cc">{dots} </tspan>'
                f'<tspan class="value">{val}</tspan>'
            )
        y += 20

    y += 10
    info_tspans.append(f'<tspan x="{info_x}" y="{y}">- Contact -{"—" * 38}-</tspan>')
    y += 20

    contacts = [
        ("Email", "yashkumar.967565@gmail.com"),
        ("LinkedIn", "yash-kumar-2a7076325"),
        ("GitHub", USERNAME),
        ("LeetCode", "Yk_coder886"),
        ("CodeChef", "yash886 (2★)"),
    ]
    for label, val in contacts:
        dots = pad_dots(label, val)
        info_tspans.append(
            f'<tspan x="{info_x}" y="{y}" class="cc">. </tspan>'
            f'<tspan class="key">{label}</tspan>:'
            f'<tspan class="cc">{dots} </tspan>'
            f'<tspan class="value">{val}</tspan>'
        )
        y += 20

    y += 10
    info_tspans.append(f'<tspan x="{info_x}" y="{y}">- GitHub Stats -{"—" * 33}-</tspan>')
    y += 20

    repo_dots = pad_dots("Repos", str(stats["repos"]), 8)
    star_line = (
        f'<tspan x="{info_x}" y="{y}" class="cc">. </tspan>'
        f'<tspan class="key">Repos</tspan>:'
        f'<tspan class="cc">{repo_dots} </tspan>'
        f'<tspan class="value">{stats["repos"]}</tspan> '
        f'{{<tspan class="key">Contributions</tspan>: '
        f'<tspan class="value">{stats["contributions"]}</tspan>}} | '
        f'<tspan class="key">Followers</tspan>:'
        f'<tspan class="cc">{pad_dots("Followers", str(stats["followers"]), 8)} </tspan>'
        f'<tspan class="value">{stats["followers"]}</tspan>'
    )
    info_tspans.append(star_line)
    y += 20

    following_dots = pad_dots("Following", str(stats["following"]))
    info_tspans.append(
        f'<tspan x="{info_x}" y="{y}" class="cc">. </tspan>'
        f'<tspan class="key">Following</tspan>:'
        f'<tspan class="cc">{following_dots} </tspan>'
        f'<tspan class="value">{stats["following"]}</tspan> | '
        f'<tspan class="key">OWASP PRs</tspan>:'
        f'<tspan class="cc"> .... </tspan>'
        f'<tspan class="value">12+ merged</tspan>'
    )
    y += 20

    info_tspans.append(
        f'<tspan x="{info_x}" y="{y}" class="cc">. </tspan>'
        f'<tspan class="key">Open Source</tspan>:'
        f'<tspan class="cc"> .... </tspan>'
        f'<tspan class="value">OWASP cve-lite-cli</tspan> '
        f'(<tspan class="addColor">OSS RNDC</tspan>)'
    )

    svg_height = max(ascii_y_start + len(ascii_lines) * ascii_line_height + 20, y + 30)

    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="Consolas,monospace" width="985px" height="{svg_height}px" font-size="16px">
<style>
.key {{fill: {key};}}
.value {{fill: {value};}}
.addColor {{fill: {add};}}
.delColor {{fill: {del_};}}
.cc {{fill: {cc};}}
text, tspan {{white-space: pre;}}
</style>
<rect width="985px" height="{svg_height}px" fill="{bg}" rx="15"/>
<text x="15" y="30" fill="{text}" class="ascii">
{ascii_tspans}
</text>
<text x="{info_x}" y="30" fill="{text}">
{chr(10).join(info_tspans)}
</text>
</svg>
"""


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    ascii_lines = generate_ascii_art()
    stats = fetch_github_stats()

    (ROOT / "dark_mode.svg").write_text(build_svg(ascii_lines, stats, "dark"))
    (ROOT / "light_mode.svg").write_text(build_svg(ascii_lines, stats, "light"))
    print("Generated dark_mode.svg and light_mode.svg")
    print(f"Stats: {stats}")


if __name__ == "__main__":
    main()
