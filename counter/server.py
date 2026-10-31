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

W, H = 820, 322
TOP = 78
BOARD = (30, 92, 790, 268)                      # x0, y0, x1, y1
CARD_GRAY = "#4a4d55"
WHITE, SALMON = "#e9edf2", "#f2826f"
FLIP_S = 0.32

# (group label, cards[(x, y, w, h)], digit color, cycle length L, step seconds S, digit-of-step fns)
GROUPS = [
    ("DAYS", [(52, 112, 82, 128), (140, 112, 82, 128)], WHITE,
     [(10, 864000, lambda k: k), (10, 86400, lambda k: k)]),
    ("HOURS", [(254, 112, 62, 96), (322, 112, 62, 96)], SALMON,
     [(24, 3600, lambda k: k // 10), (24, 3600, lambda k: k % 10)]),
    ("MIN", [(436, 112, 62, 96), (504, 112, 62, 96)], SALMON,
     [(6, 600, lambda k: k), (10, 60, lambda k: k)]),
    ("SEC", [(598, 112, 82, 128), (686, 112, 82, 128)], WHITE,
     [(6, 10, lambda k: k), (10, 1, lambda k: k)]),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(elapsed, repo):
    elapsed = max(0.0, elapsed)
    css, defs, body = [], [], []
    x0, y0, x1, y1 = BOARD

    body.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="6" fill="#1b1c1f"/>')
    body.append(f'<rect x="{x0}" y="{y1 - 6}" width="{x1 - x0}" height="6" rx="3" fill="#121214"/>')
    for cx in (x0 + 12, x1 - 12):
        body.append(f'<circle cx="{cx}" cy="{y1 - 16}" r="3.2" fill="#e5484d"/>')

    n = 0
    for label, cards, color, specs in GROUPS:
        for (cx, cy, cw, ch), (L, S, digit) in zip(cards, specs):
            n += 1
            d = elapsed % (L * S)
            d_prev = (d - S) % (L * S)
            size = round(ch * 0.62)
            base = cy + ch / 2 + size * 0.36
            strip = "".join(
                f'<text x="{cx + cw / 2}" y="{base + k * ch:.1f}">{digit(k)}</text>' for k in range(L)
            )
            hinge = cy + ch / 2
            defs.append(f'<clipPath id="c{n}"><rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="7"/></clipPath>')
            defs.append(f'<clipPath id="t{n}"><rect x="{cx}" y="{cy}" width="{cw}" height="{ch / 2}"/></clipPath>')
            css.append(
                f"#s{n},#p{n}{{animation:k{n} {L * S}s steps({L}) infinite}}"
                f"#s{n}{{animation-delay:-{d:.3f}s}}#p{n}{{animation-delay:-{d_prev:.3f}s}}"
                f"@keyframes k{n}{{to{{transform:translateY(-{L * ch}px)}}}}"
                f"#f{n}{{transform-origin:{cx + cw / 2}px {hinge}px;"
                f"animation:flip {S}s linear infinite;animation-delay:-{elapsed % S:.3f}s}}"
            )
            if S > FLIP_S:
                css.append(f"#f{n}{{animation-name:flip{n}}}"
                           f"@keyframes flip{n}{{0%{{transform:scaleY(1)}}"
                           f"{100 * FLIP_S / S:.4f}%,100%{{transform:scaleY(0)}}}}")

            for hx in (cx + cw * 0.28, cx + cw * 0.72):
                body.append(f'<circle cx="{hx:.1f}" cy="{cy - 4}" r="10" fill="none" stroke="#c9ccd1" stroke-width="3.2"/>')
            body.append(f'<g fill="{color}" font-size="{size}">'
                        f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="7" fill="{CARD_GRAY}"/>'
                        f'<g clip-path="url(#c{n})"><g id="s{n}">{strip}</g></g>'
                        f'<g id="f{n}"><g clip-path="url(#t{n})">'
                        f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="7" fill="{CARD_GRAY}"/>'
                        f'<g id="p{n}">{strip}</g>'
                        f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch / 2}" fill="#000" opacity=".12"/>'
                        f'</g></g>'
                        f'<line x1="{cx}" y1="{hinge}" x2="{cx + cw}" y2="{hinge}" stroke="#2a2c31" stroke-width="1.5"/>')
            for hx in (cx + cw * 0.28, cx + cw * 0.72):
                body.append(f'<circle cx="{hx:.1f}" cy="{cy + 7}" r="3" fill="#1b1c1f"/>')
                body.append(f'<path d="M{hx - 10:.1f} {cy - 4} A10 10 0 0 1 {hx + 10:.1f} {cy - 4}" fill="none" '
                            f'stroke="#c9ccd1" stroke-width="3.2"/>')
            body.append("</g>")
        lx = (cards[0][0] + cards[-1][0] + cards[-1][2]) / 2
        ly = max(c[1] + c[3] for c in cards) + 16
        body.append(f'<text class="lbl" x="{lx}" y="{ly}">{label}</text>')

    body.append(f'<text class="brand" x="410" y="246">SINCE LAST COMMIT</text>')
    body.append(f'<g transform="rotate(-4 90 286)"><rect x="6" y="262" width="168" height="48" rx="5" fill="#2b2d33"/>'
                f'<text class="tab" x="90" y="294">{esc(repo[:14])}</text></g>')

    css.append(
        "@keyframes flip{0%{transform:scaleY(1)}32%,100%{transform:scaleY(0)}}"
        "text{text-anchor:middle;font-family:'Arial Rounded MT Bold','Helvetica Neue',Arial,sans-serif;font-weight:700}"
        ".lbl{fill:#8f939b;font-size:12px;letter-spacing:3px;font-weight:600}"
        ".brand{fill:#d9d5d2;font-size:22px;letter-spacing:4px}"
        f".tab{{fill:{SALMON};font-size:22px}}"
        "@media (prefers-reduced-motion:reduce){*{animation-play-state:paused!important}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {TOP} {W} {H - TOP}" width="{W}" height="{H - TOP}" '
        f'role="img" aria-label="Time since last commit">'
        f'<style>{"".join(css)}</style><defs>{"".join(defs)}</defs>{"".join(body)}</svg>'
    )


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/health":
            body, ctype = b"ok", "text/plain"
        elif path in ("/", "/last-commit.svg"):
            ts, repo = last_commit()
            body, ctype = render(time.time() - ts, repo).encode(), "image/svg+xml; charset=utf-8"
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
