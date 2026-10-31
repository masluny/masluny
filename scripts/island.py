"""Draw the last year of contributions as an archipelago -> assets/archipelago.svg

Days without contributions are ocean, busier days are taller land, and the
highest peak gets a pirate flag. Needs GITHUB_TOKEN (the Actions token is enough).
"""

import json
import math
import os
import urllib.request
from datetime import date, timedelta
from pathlib import Path

USER = "masluny"
OUT = Path(__file__).resolve().parent.parent / "assets" / "archipelago.svg"

CELL, OX, OY, LEFT = 12, 5, 5, 8
WATER = ("#b6dcf2", "#a7d3ee", "#c3e3f5")
WATER_DARK = ("#1d4f73", "#1a4767", "#22597f")


def fetch():
    query = """{user(login:"%s"){contributionsCollection{contributionCalendar{
      weeks{contributionDays{date contributionCount}}}}}}""" % USER
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
    )
    with urllib.request.urlopen(req) as resp:
        weeks = json.load(resp)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    return date.fromisoformat(days[0]["date"]), [d["contributionCount"] for d in days]


def terrain(n):
    if n <= 2:
        return "#e9d8a6"
    if n <= 5:
        return "#8cc06b"
    if n <= 10:
        return "#4f8f4a"
    if n <= 20:
        return "#8d8478"
    return "#f4f4f2"


def shade(hex_color, k):
    n = int(hex_color[1:], 16)
    return "#%02x%02x%02x" % tuple(round(((n >> s) & 255) * k) for s in (16, 8, 0))


def height(n):
    return 4 + 6 * math.log2(n + 1) if n else 0


def pts(*xy):
    return " ".join(f"{v:g}" for v in xy)


def svg(start, counts):
    weeks = math.ceil(len(counts) / 7)
    peak = max(counts)
    ground = math.ceil(height(peak) + 6 * OY + 34)
    width = LEFT + weeks * CELL + 6 * OX + CELL
    total_h = ground + 22
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total_h}" width="{width}" '
        f'height="{total_h}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" role="img" '
        f'aria-label="A year of contributions drawn as an archipelago">',
        "<style>"
        + "".join(f".w{i}{{fill:{c}}}" for i, c in enumerate(WATER))
        + "text{fill:#8b949e;font-size:10px}"
        + "@media (prefers-color-scheme:dark){"
        + "".join(f".w{i}{{fill:{c}}}" for i, c in enumerate(WATER_DARK))
        + "}"
        + ".wave{animation:wave 4s ease-in-out infinite}"
        + "@keyframes wave{0%,100%{opacity:1}50%{opacity:.72}}"
        + "</style>",
    ]
    peak_xy = None
    for r in range(6, -1, -1):
        for w in range(weeks):
            i = w * 7 + (6 - r)
            if i >= len(counts):
                continue
            n, h = counts[i], height(counts[i])
            x, y = LEFT + w * CELL + r * OX, ground - r * OY
            if not n:
                out.append(f'<polygon class="w{(w + r) % 3} wave" style="animation-delay:{w * 0.08:.2f}s" '
                           f'points="{pts(x, y, x + CELL, y, x + CELL + OX, y - OY, x + OX, y - OY)}"/>')
                continue
            c = terrain(n)
            day = start + timedelta(days=i)
            out.append(f'<g><title>{day:%b %-d}: {n} contribution{"s" if n != 1 else ""}</title>')
            out.append(f'<polygon fill="{shade(c, .62)}" points="{pts(x + CELL, y - h, x + CELL + OX, y - h - OY, x + CELL + OX, y - OY, x + CELL, y)}"/>')
            out.append(f'<rect x="{x}" y="{y - h:.1f}" width="{CELL}" height="{h:.1f}" fill="{shade(c, .8)}"/>')
            out.append(f'<polygon fill="{c}" points="{pts(x, y - h, x + CELL, y - h, x + CELL + OX, y - h - OY, x + OX, y - h - OY)}"/></g>')
            if n == peak and peak_xy is None:
                peak_xy = (x + CELL / 2 + OX / 2, y - h - OY / 2, day)
    if peak_xy:
        px, py, day = peak_xy
        top = py - 22
        out.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{top:.1f}" stroke="#6e5a44" stroke-width="1.5"/>')
        out.append(f'<rect x="{px + .75:.1f}" y="{top:.1f}" width="12" height="8" fill="#16161a" stroke="#c9ccd1" stroke-width=".8"/>')
        out.append(f'<rect x="{px + 5.5:.1f}" y="{top + 2.5:.1f}" width="2.5" height="2.5" fill="#f4f4f2"/>')
        out.append(f'<text x="{px + 16:.1f}" y="{top + 7:.1f}">{peak} · {day:%b %-d}</text>')
    last_month = None
    for w in range(weeks):
        d = start + timedelta(days=w * 7)
        if d.month != last_month:
            last_month = d.month
            if 0 < w < weeks - 2:
                out.append(f'<text x="{LEFT + w * CELL}" y="{total_h - 4}">{d:%b}</text>')
    out.append("</svg>\n")
    return "".join(out)


def main():
    start, counts = fetch()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(svg(start, counts))
    print(f"{sum(counts)} contributions, peak {max(counts)}")


if __name__ == "__main__":
    main()
