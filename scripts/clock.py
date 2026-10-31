"""Redraw assets/commit-clock.svg.

Counts every commit authored by USER in their public, non-fork repos and bins
it by local hour. Needs GITHUB_TOKEN (the Actions token is enough).
"""

import json
import os
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

USER = "masluny"
TZ = ZoneInfo("Europe/Madrid")
ROOT = Path(__file__).resolve().parent.parent


def api(path):
    items, url = [], f"https://api.github.com/{path}"
    while url:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        })
        try:
            with urllib.request.urlopen(req) as resp:
                items += json.load(resp)
                m = re.search(r'<([^>]+)>; rel="next"', resp.headers.get("Link", ""))
                url = m.group(1) if m else None
        except urllib.error.HTTPError as e:
            if e.code == 409:  # empty repository
                return items
            raise
    return items


def collect():
    repos = [r for r in api(f"users/{USER}/repos?per_page=100&type=owner")
             if not r["fork"] and r["name"] != USER]
    hours, total = Counter(), 0
    for r in repos:
        for c in api(f"repos/{USER}/{r['name']}/commits?author={USER}&per_page=100"):
            t = datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
            hours[t.astimezone(TZ).hour] += 1
            total += 1
    return [hours[h] for h in range(24)], total


def dead_zone(counts):
    """Longest run of zero-commit hours, wrapping past midnight. (start, length)."""
    best = (0, 0)
    for start in range(24):
        n = 0
        while n < 24 and counts[(start + n) % 24] == 0:
            n += 1
        if n > best[1]:
            best = (start, n)
    return best


def bar_color(h):
    if h < 6:
        return "#8b5cf6"   # the good hours
    if h >= 21:
        return "#6366f1"
    return "#f59e0b"


def svg(counts, total):
    bw, gap, left, top, plot_h = 22, 6, 34, 46, 120
    width = left + 24 * (bw + gap) + 10
    height = top + plot_h + 34
    peak = max(counts) or 1
    peak_h = counts.index(peak)
    dz_start, dz_len = dead_zone(counts)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
         f'width="{width}" height="{height}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" '
         f'role="img" aria-label="Commits by hour of day">',
         '<style>text{fill:#8b949e;font-size:11px}.t{font-size:13px;font-weight:600}'
         '.pk{fill:#a78bfa;font-weight:600}.dz{fill:#8b949e;font-style:italic}</style>',
         f'<text class="t" x="{left}" y="18">commits by hour · Europe/Madrid · {total} commits</text>']
    if dz_len >= 2:
        x0 = left + dz_start * (bw + gap) - gap / 2
        w = min(dz_len, 24 - dz_start) * (bw + gap)
        p.append(f'<rect x="{x0}" y="{top}" width="{w}" height="{plot_h}" rx="6" '
                 f'fill="#8b949e" fill-opacity="0.08" stroke="#8b949e" stroke-opacity="0.35" '
                 f'stroke-dasharray="4 4"/>')
        p.append(f'<text x="{x0 + w / 2}" y="{top + plot_h / 2 - 6}" text-anchor="middle" '
                 f'style="font-size:20px">☕</text>')
        p.append(f'<text class="dz" x="{x0 + w / 2}" y="{top + plot_h / 2 + 14}" '
                 f'text-anchor="middle">mornings: 404</text>')
    for h, n in enumerate(counts):
        x = left + h * (bw + gap)
        bh = max(2, round(plot_h * n / peak)) if n else 0
        if bh:
            p.append(f'<rect x="{x}" y="{top + plot_h - bh}" width="{bw}" height="{bh}" '
                     f'rx="3" fill="{bar_color(h)}"><title>{h:02d}:00 · {n} commits</title></rect>')
        if h % 3 == 0:
            p.append(f'<text x="{x + bw / 2}" y="{top + plot_h + 18}" text-anchor="middle">{h:02d}</text>')
    px = left + peak_h * (bw + gap) + bw / 2
    p.append(f'<text class="pk" x="{px}" y="{top - 6}" text-anchor="middle">peak {peak_h:02d}:00</text>')
    p.append("</svg>\n")
    return "".join(p)


def main():
    counts, total = collect()
    (ROOT / "assets" / "commit-clock.svg").write_text(svg(counts, total))
    print(f"{total} commits, peak {counts.index(max(counts)):02d}:00, "
          f"updated {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z")


if __name__ == "__main__":
    main()
