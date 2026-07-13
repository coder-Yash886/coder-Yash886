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

ASCII_WIDTH = 30
ASCII_HEIGHT = 22
ASCII_CHARS = " .:-=+*#%@"


def escape_svg(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_ascii_art(theme: str = "dark") -> list[str]:
    """Convert profile photo into portrait ASCII art (original style, wider)."""
    img = Image.open(PROFILE).convert("L")
    width, height = img.size

    # Original face-focused crop from first version
    left = int(width * 0.25)
    top = int(height * 0.05)
    right = int(width * 0.75)
    bottom = int(height * 0.55)
    portrait = img.crop((left, top, right, bottom))

    # Slight warmth for natural skin tones
    rgb = Image.open(PROFILE).convert("RGB").crop((left, top, right, bottom))
    pixels = rgb.load()
    warm = Image.new("L", portrait.size)
    warm_pixels = warm.load()
    for y in range(portrait.size[1]):
        for x in range(portrait.size[0]):
            red, green, blue = pixels[x, y]
            warm_pixels[x, y] = int(0.35 * red + 0.45 * green + 0.20 * blue)

    contrast = 1.55 if theme == "light" else 1.4
    portrait = ImageEnhance.Contrast(warm).enhance(contrast)
    portrait = ImageEnhance.Brightness(portrait).enhance(1.05 if theme == "dark" else 0.95)
    portrait = portrait.resize((ASCII_WIDTH, ASCII_HEIGHT), Image.Resampling.LANCZOS)

    lines: list[str] = []
    for y in range(ASCII_HEIGHT):
        row = ""
        for x in range(ASCII_WIDTH):
            pixel = portrait.getpixel((x, y))
            if theme == "light":
                index = int((255 - pixel) / 255 * (len(ASCII_CHARS) - 1))
            else:
                index = int(pixel / 255 * (len(ASCII_CHARS) - 1))
            row += ASCII_CHARS[index]
        lines.append(row)

    if theme == "dark":
        ASCII_FILE.write_text("\n".join(lines))
    return lines


def fetch_github_stats() -> dict[str, int]:
    with urllib.request.urlopen(f"https://api.github.com/users/{USERNAME}") as resp:
        user = json.load(resp)

    contributions = 0
    for url in (
        f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last",
        f"https://github-contributions-api.deno.dev/{USERNAME}.json",
    ):
        try:
            with urllib.request.urlopen(url) as resp:
                contrib = json.load(resp)
            contributions = (
                contrib.get("total", {}).get("lastYear")
                or contrib.get("contributions")
                or 0
            )
            if contributions:
                break
        except Exception:
            continue

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
        ascii_fill = "#c9d1d9"
        key = "#ffa657"
        value = "#a5d6ff"
        cc = "#616e7f"
        add = "#3fb950"
        del_ = "#f85149"
        stroke = "none"
    else:
        bg = "#f6f8fa"
        text = "#24292f"
        ascii_fill = "#3d444d"
        key = "#bc4c00"
        value = "#0969da"
        cc = "#656d76"
        add = "#1a7f37"
        del_ = "#cf222e"
        stroke = "#d0d7de"

    ascii_y_start = 30
    ascii_line_height = 20
    ascii_tspans = "\n".join(
        f'<tspan x="15" y="{ascii_y_start + i * ascii_line_height}">{escape_svg(line)}</tspan>'
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
    stroke_attr = (
        f'stroke="{stroke}" stroke-width="1"'
        if stroke != "none"
        else ""
    )

    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="Consolas,monospace" width="985px" height="{svg_height}px" font-size="16px">
<style>
.key {{fill: {key};}}
.value {{fill: {value};}}
.addColor {{fill: {add};}}
.delColor {{fill: {del_};}}
.cc {{fill: {cc};}}
.ascii {{fill: {ascii_fill};}}
text, tspan {{white-space: pre;}}
</style>
<rect width="985px" height="{svg_height}px" fill="{bg}" rx="15" {stroke_attr}/>
<text x="15" y="30" class="ascii">
{ascii_tspans}
</text>
<text x="{info_x}" y="30" fill="{text}">
{chr(10).join(info_tspans)}
</text>
</svg>
"""


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    stats = fetch_github_stats()
    dark_ascii = generate_ascii_art("dark")
    light_ascii = generate_ascii_art("light")

    (ROOT / "dark_mode.svg").write_text(build_svg(dark_ascii, stats, "dark"))
    (ROOT / "light_mode.svg").write_text(build_svg(light_ascii, stats, "light"))
    print("Generated dark_mode.svg and light_mode.svg")
    print(f"Stats: {stats}")


if __name__ == "__main__":
    main()
