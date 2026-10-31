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

CW, CH = 64, 96                                  # every card is the same size
PAIR_GAP, GROUP_GAP, PAD, CY = 8, 44, 28, 32
W = 2 * PAD + 4 * (2 * CW + PAIR_GAP) + 3 * GROUP_GAP
H = CY + CH + 26
FLIP_S = 0.32
CYAN, PINK, VIOLET = "#22e6ff", "#ff2bd6", "#b18cff"
CORE = {CYAN: "#dcfcff", PINK: "#ffe0f7"}       # near-white tube core, the glow carries the color
FACE_TOP, FACE_BOTTOM = "#11131d", "#0b0c14"

# per group: neon color, then (cycle length L, step seconds S, digit-of-step fn) for its two cards
GROUPS = [
    (CYAN, [(10, 864000, lambda k: k), (10, 86400, lambda k: k)]),
    (PINK, [(24, 3600, lambda k: k // 10), (24, 3600, lambda k: k % 10)]),
    (PINK, [(6, 600, lambda k: k), (10, 60, lambda k: k)]),
    (CYAN, [(6, 10, lambda k: k), (10, 1, lambda k: k)]),
]


def glow(fid, color, blur):
    return (f'<filter id="{fid}" x="-60%" y="-60%" width="220%" height="220%">'
            f'<feGaussianBlur in="SourceAlpha" stdDeviation="{blur}" result="b"/>'
            f'<feFlood flood-color="{color}"/><feComposite in2="b" operator="in" result="g"/>'
            f'<feGaussianBlur in="SourceAlpha" stdDeviation="{blur * 3}" result="b2"/>'
            f'<feFlood flood-color="{color}" flood-opacity=".55"/><feComposite in2="b2" operator="in" result="g2"/>'
            f'<feMerge><feMergeNode in="g2"/><feMergeNode in="g"/><feMergeNode in="g"/>'
            f'<feMergeNode in="SourceGraphic"/></feMerge></filter>')


def render(elapsed):
    elapsed = max(0.0, elapsed)
    css, body = [], []
    defs = [glow("gc", CYAN, 1.6), glow("gp", PINK, 1.6), glow("gv", VIOLET, 1.8),
            f'<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/>'
            f'<stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>',
            f'<linearGradient id="face" x1="0" y1="0" x2="0" y2="1"><stop offset=".5" stop-color="{FACE_TOP}"/>'
            f'<stop offset=".5" stop-color="{FACE_BOTTOM}"/></linearGradient>']

    body.append(f'<rect width="{W}" height="{H}" rx="16" fill="#05060b"/>')
    body.append(f'<rect class="tube" x="5" y="5" width="{W - 10}" height="{H - 10}" rx="12" fill="none" '
                f'stroke="url(#edge)" stroke-width="1.6" filter="url(#gv)"/>')

    n = 0
    hinge = CY + CH / 2
    size = round(CH * 0.62)
    base = CY + CH / 2 + size * 0.36
    for g, (color, specs) in enumerate(GROUPS):
        gx = PAD + g * (2 * CW + PAIR_GAP + GROUP_GAP)
        fid = "gc" if color == CYAN else "gp"
        if g:
            colon_x = gx - GROUP_GAP / 2
            body.append(f'<g class="colon" fill="{VIOLET}" filter="url(#gv)">'
                        f'<circle cx="{colon_x}" cy="{hinge - 15}" r="3.6"/>'
                        f'<circle cx="{colon_x}" cy="{hinge + 15}" r="3.6"/></g>')
        for i, (L, S, digit) in enumerate(specs):
            n += 1
            cx = gx + i * (CW + PAIR_GAP)
            d = elapsed % (L * S)
            d_prev = (d - S) % (L * S)
            strip = "".join(
                f'<text x="{cx + CW / 2}" y="{base + k * CH:.1f}">{digit(k)}</text>' for k in range(L)
            )
            defs.append(f'<clipPath id="c{n}"><rect x="{cx}" y="{CY}" width="{CW}" height="{CH}" rx="8"/></clipPath>')
            defs.append(f'<clipPath id="t{n}"><rect x="{cx}" y="{CY}" width="{CW}" height="{CH / 2}"/></clipPath>')
            css.append(
                f"#s{n},#p{n}{{animation:k{n} {L * S}s steps({L}) infinite}}"
                f"#s{n}{{animation-delay:-{d:.3f}s}}#p{n}{{animation-delay:-{d_prev:.3f}s}}"
                f"@keyframes k{n}{{to{{transform:translateY(-{L * CH}px)}}}}"
                f"#f{n}{{transform-origin:{cx + CW / 2}px {hinge}px;"
                f"animation:flip {S}s linear infinite;animation-delay:-{elapsed % S:.3f}s}}"
            )
            if S > FLIP_S:
                css.append(f"#f{n}{{animation-name:flip{n}}}"
                           f"@keyframes flip{n}{{0%{{transform:scaleY(1)}}"
                           f"{100 * FLIP_S / S:.4f}%,100%{{transform:scaleY(0)}}}}")

            rings = [cx + CW * 0.28, cx + CW * 0.72]
            for hx in rings:
                body.append(f'<circle cx="{hx:.1f}" cy="{CY - 3}" r="8" fill="none" stroke="{color}" '
                            f'stroke-width="1.6" opacity=".55"/>')
            body.append(f'<rect x="{cx}" y="{CY}" width="{CW}" height="{CH}" rx="8" fill="url(#face)" '
                        f'stroke="{color}" stroke-opacity=".7" stroke-width="1.2" filter="url(#{fid})"/>')
            body.append(f'<g fill="{CORE[color]}" font-size="{size}" filter="url(#{fid})">'
                        f'<g clip-path="url(#c{n})"><g id="s{n}">{strip}</g></g></g>')
            body.append(f'<g id="f{n}"><g clip-path="url(#t{n})">'
                        f'<rect x="{cx}" y="{CY}" width="{CW}" height="{CH}" rx="8" fill="{FACE_TOP}"/>'
                        f'<g fill="{CORE[color]}" font-size="{size}" filter="url(#{fid})"><g id="p{n}">{strip}</g></g>'
                        f'</g></g>')
            body.append(f'<line x1="{cx}" y1="{hinge}" x2="{cx + CW}" y2="{hinge}" stroke="#05060b" stroke-width="2"/>')
            for hx in rings:
                body.append(f'<circle cx="{hx:.1f}" cy="{CY + 6}" r="2.4" fill="#05060b"/>')
                body.append(f'<path d="M{hx - 8:.1f} {CY - 3} A8 8 0 0 1 {hx + 8:.1f} {CY - 3}" fill="none" '
                            f'stroke="{color}" stroke-width="1.8" filter="url(#{fid})"/>')

    css.append(
        "@keyframes flip{0%{transform:scaleY(1)}32%,100%{transform:scaleY(0)}}"
        f".colon{{animation:blink 1s steps(1) infinite;animation-delay:-{elapsed % 1:.3f}s}}"
        "@keyframes blink{0%{opacity:1}50%{opacity:.25}}"
        ".tube{animation:flicker 9s infinite}"
        "@keyframes flicker{0%,91%,93.5%,96%,100%{opacity:1}92%,95%{opacity:.35}}"
        "text{text-anchor:middle;font-family:'Arial Rounded MT Bold','Helvetica Neue',Arial,sans-serif;font-weight:700}"
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
