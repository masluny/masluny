#!/usr/bin/env python3
"""Flip-card counter: time since masluny's last public commit, as an SVG.

GET /last-commit.svg renders the elapsed time at request time; CSS animations
keep the cards flipping afterwards, so the image stays correct while it is open.
GitHub's image proxy (camo) refetches it on every view because of no-cache.

Stdlib only. Env: HOST (default 127.0.0.1), PORT (default 8787), GITHUB_USER, GITHUB_TOKEN (optional,
raises the API rate limit), CACHE_SECONDS (default 300; 4 API calls per refresh,
which keeps an unauthenticated server under GitHub's 60 requests/hour).
"""

import json
import os
import threading
import time
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

USER = os.environ.get("GITHUB_USER", "masluny")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8787"))
CACHE_SECONDS = int(os.environ.get("CACHE_SECONDS", "300"))

_lock = threading.Lock()
_cache = {"checked": 0.0, "commit_ts": None, "repo": "?"}


def gh(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "pirrot-flip-counter"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(f"https://api.github.com/{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=4) as resp:
        return json.load(resp)


def last_commit():
    """(unix time of USER's newest commit in their public repos, repo name).

    The public events feed skips pushes made while a repo was still private and
    can lag by hours, so this asks the recently pushed repos directly. The
    profile repo is skipped so the nightly bot commits don't reset the counter.
    Cached; never raises.
    """
    with _lock:
        if time.time() - _cache["checked"] < CACHE_SECONDS and _cache["commit_ts"]:
            return _cache["commit_ts"], _cache["repo"]
        try:
            repos = [r for r in gh(f"users/{USER}/repos?sort=pushed&per_page=4&type=owner")
                     if r["name"] != USER][:3]
            best = None
            for r in repos:
                commits = gh(f"repos/{USER}/{r['name']}/commits?author={USER}&per_page=1")
                if not commits:
                    continue
                stamp = commits[0]["commit"]["committer"]["date"]
                ts = datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
                if best is None or ts > best[0]:
                    best = (ts, r["name"])
            if best:
                _cache["commit_ts"], _cache["repo"] = best
            _cache["checked"] = time.time()
        except Exception:
            _cache["checked"] = time.time() - CACHE_SECONDS + 15
        return _cache["commit_ts"] or time.time(), _cache["repo"]


# ---------------------------------------------------------------- drawing --
# Palette borrowed from scripts/island.py so the counter matches the archipelago.

CW, CH = 64, 96                                  # every card is the same size
PAIR_GAP, GROUP_GAP, PAD, CY = 8, 40, 28, 40
W = 2 * PAD + 4 * (2 * CW + PAIR_GAP) + 3 * GROUP_GAP
H = CY + CH + 44
RISE_S, OVER_S, FLIP_S = 0.1, 0.2, 0.5          # back rises above the rings, tips over, front lands
RISE = 0.3                                       # how far the back pokes up, as a fraction of CH
SNOW, SAND, FOREST, ROCK = "#f4f4f2", "#e9d8a6", "#3f7a3b", "#8d8478"
BACK = {SNOW: "#d2d3cf", SAND: "#cbb985"}

# per group: card face, then (cycle length L, step seconds S, digit-of-step fn) for its two cards
GROUPS = [
    (SNOW, [(10, 864000, lambda k: k), (10, 86400, lambda k: k)]),
    (SAND, [(24, 3600, lambda k: k // 10), (24, 3600, lambda k: k % 10)]),
    (SAND, [(6, 600, lambda k: k), (10, 60, lambda k: k)]),
    (SNOW, [(6, 10, lambda k: k), (10, 1, lambda k: k)]),
]


def render(elapsed):
    elapsed = max(0.0, elapsed)
    css, defs, body = [], [], []

    body.append(f'<rect class="sea" width="{W}" height="{H}" rx="12"/>')

    n = 0
    size = round(CH * 0.62)
    base = CY + CH / 2 + size * 0.36
    for g, (face, specs) in enumerate(GROUPS):
        gx = PAD + g * (2 * CW + PAIR_GAP + GROUP_GAP)
        if g:
            colon_x = gx - GROUP_GAP / 2
            for dy in (-14, 14):
                body.append(f'<circle class="dot" cx="{colon_x}" cy="{CY + CH / 2 + dy}" r="3.5"/>')
        for i, (L, S, digit) in enumerate(specs):
            n += 1
            cx = gx + i * (CW + PAIR_GAP)
            d = elapsed % (L * S)
            d_prev = (d - S) % (L * S)
            strip = "".join(
                f'<text x="{cx + CW / 2}" y="{base + k * CH:.1f}">{digit(k)}</text>' for k in range(L)
            )
            card = f'<rect x="{cx}" y="{CY}" width="{CW}" height="{CH}" rx="7" fill="{face}"/>'
            defs.append(f'<clipPath id="c{n}"><rect x="{cx}" y="{CY}" width="{CW}" height="{CH}" rx="7"/></clipPath>')
            rise, over, land = (100 * t / S for t in (RISE_S, OVER_S, FLIP_S))
            css.append(
                f"#s{n},#p{n}{{animation:k{n} {L * S}s steps({L}) infinite}}"
                f"#s{n}{{animation-delay:-{d:.3f}s}}#p{n}{{animation-delay:-{d_prev:.3f}s}}"
                f"@keyframes k{n}{{to{{transform:translateY(-{L * CH}px)}}}}"
                f"#f{n},#b{n}{{transform-origin:{cx + CW / 2}px {CY}px}}"
                f"#f{n}{{animation:fall{n} {S}s linear infinite}}"
                f"#b{n}{{animation:back{n} {S}s linear infinite}}"
                f"#h{n}{{animation:shade{n} {S}s linear infinite}}"
                f"#f{n},#b{n},#h{n}{{animation-delay:-{elapsed % S:.3f}s}}"
                f"@keyframes back{n}{{0%{{transform:scaleY(0);animation-timing-function:ease-out}}"
                f"{rise:.4f}%{{transform:scaleY(-{RISE});animation-timing-function:ease-in}}"
                f"{over:.4f}%,100%{{transform:scaleY(0)}}}}"
                f"@keyframes fall{n}{{0%,{over:.4f}%{{transform:scaleY(0);animation-timing-function:ease-in}}"
                f"{land:.4f}%,100%{{transform:scaleY(1)}}}}"
                f"@keyframes shade{n}{{0%,{over:.4f}%{{opacity:.55}}{land:.4f}%,100%{{opacity:0}}}}"
            )

            rings = [cx + CW * 0.28, cx + CW * 0.72]
            for hx in rings:
                body.append(f'<circle cx="{hx:.1f}" cy="{CY - 3}" r="8" fill="none" stroke="{ROCK}" stroke-width="3"/>')
            body.append(f'<rect id="b{n}" x="{cx}" y="{CY}" width="{CW}" height="{CH}" rx="7" fill="{BACK[face]}" '
                        f'transform="scale(1 0)"/>')
            body.append(f'<rect class="shadow" x="{cx}" y="{CY + 3}" width="{CW}" height="{CH}" rx="7"/>')
            body.append(f'<g fill="{FOREST}" font-size="{size}">{card}'
                        f'<g clip-path="url(#c{n})"><g id="p{n}">{strip}</g></g>'
                        f'<g id="f{n}">{card}<g clip-path="url(#c{n})"><g id="s{n}">{strip}</g></g>'
                        f'<rect id="h{n}" x="{cx}" y="{CY}" width="{CW}" height="{CH}" rx="7" fill="#000" opacity="0"/></g></g>')
            for hx in rings:
                body.append(f'<circle class="hole" cx="{hx:.1f}" cy="{CY + 6}" r="2.6"/>')
                body.append(f'<path d="M{hx - 8:.1f} {CY - 3} A8 8 0 0 1 {hx + 8:.1f} {CY - 3}" fill="none" '
                            f'stroke="{ROCK}" stroke-width="3"/>')

    body.append(f'<text class="lbl" x="{W / 2}" y="{CY + CH + 30}">since last commit</text>')

    css.append(
        ".sea{fill:#b6dcf2}.dot,.hole{fill:#1d4f73}.shadow{fill:#1d4f73;opacity:.18}.lbl{fill:#1d4f73}"
        "@media (prefers-color-scheme:dark){.sea{fill:#1d4f73}.dot,.lbl{fill:#b6dcf2}.hole{fill:#1a4767}"
        ".shadow{fill:#000;opacity:.3}}"
        "text{text-anchor:middle;font-family:'Arial Rounded MT Bold','Helvetica Neue',Arial,sans-serif;font-weight:700}"
        ".lbl{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:15px;font-weight:600;letter-spacing:2px}"
        "@media (prefers-reduced-motion:reduce){*{animation-play-state:paused!important}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Time since last commit">'
        f'<style>{"".join(css)}</style><defs>{"".join(defs)}</defs>{"".join(body)}</svg>'
    )


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/health":
            body, ctype = b"ok", "text/plain"
        elif path in ("/", "/last-commit.svg"):
            ts, _ = last_commit()
            body, ctype = render(time.time() - ts).encode(), "image/svg+xml; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"flip counter for {USER} on {HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
