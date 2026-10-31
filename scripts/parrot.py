"""Render the Pirrot macaw (github.com/masluny/Pirrot) as an animated SVG.

Same sprite, branch and walk cycle as extensions/parrot-pet.ts, mirrored the
way pi draws it in the bottom-right corner. Output: assets/parrot.svg
"""

from pathlib import Path

PALETTE = {
    "R": (220, 54, 60), "r": (156, 30, 42), "W": (248, 246, 240), "w": (206, 198, 188),
    "K": (24, 20, 28), "y": (246, 202, 54), "B": (64, 120, 214), "b": (40, 82, 158),
    "f": (235, 180, 58),
    "N": (158, 114, 70), "m": (124, 86, 52), "n": (80, 54, 32),
    "G": (96, 168, 78), "g": (52, 112, 54), "L": (150, 205, 110),
    "O": (234, 226, 202), "o": (52, 48, 52),
}

BIRD = [
    "....RR......",
    "..RRRR......",
    ".RRWWROOO...",
    ".RRWKROOOO..",
    ".RRRRoOOO...",
    ".RRRRooO....",
    "..RyyRR.....",
    ".RyyyRR.....",
    ".RBBRR......",
    ".RBRR.......",
    "..RRR.......",
    "..f.f.......",
]
TAIL = ["RRr", "Rrr", "rrr", "rr.", "r.."]

W, H = 27, 16
LIMB_ROW, BIRD_X, BASE_X, ELBOW_X = 12, 8, 1, 5
LIMB_X1 = W - 2
BIRD_W, TAIL_W, TAIL_DX = 12, 3, 2

WALK = [(0, "R"), (1, "R"), (2, "R"), (3, "R"), (3, "L"), (2, "L"), (1, "L"),
        (0, "L"), (-1, "L"), (-2, "L"), (-2, "R"), (-1, "R")]
FRAME_S = 0.32
PX = 10


def blank():
    return [["."] * W for _ in range(H)]


def put(c, x, y, ch):
    if 0 <= y < H and 0 <= x < W:
        c[y][x] = ch


def stamp(c, grid, x0, y0):
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch != ".":
                put(c, x0 + x, y0 + y, ch)


def mirror(grid):
    return [row[::-1] for row in grid]


def draw_branch(c):
    base_y = H - 1
    steps = ELBOW_X - BASE_X
    for i in range(steps + 1):
        x = BASE_X + i
        y = round(base_y - ((base_y - LIMB_ROW) * i) / steps)
        put(c, x, y, "N")
        put(c, x, y + 1, "n")
        if i < steps:
            put(c, x + 1, y, "N")
            put(c, x + 1, y + 1, "n")
    for x in range(ELBOW_X, LIMB_X1 + 1):
        put(c, x, LIMB_ROW, "N")
        put(c, x, LIMB_ROW + 1, "n")
        if x <= ELBOW_X + 3:
            put(c, x, LIMB_ROW - 1, "m")
    put(c, 16, LIMB_ROW, "m")
    put(c, 16, LIMB_ROW - 1, "N")
    put(c, 17, LIMB_ROW, "n")
    for x in (10, 13, 20):
        put(c, x, LIMB_ROW, "m")
    put(c, LIMB_X1, LIMB_ROW + 1, ".")
    put(c, LIMB_X1 - 1, LIMB_ROW + 1, ".")
    put(c, LIMB_X1, LIMB_ROW, "m")
    stamp(c, [".L", "Gg"], 3, LIMB_ROW - 2)
    stamp(c, ["gG", "GG", ".g"], 21, LIMB_ROW - 3)
    stamp(c, ["Gg"], 24, LIMB_ROW - 1)


def bird_layer(dx, face):
    c = blank()
    bx = BIRD_X + dx
    if face == "L":
        stamp(c, mirror(TAIL), bx + (BIRD_W - TAIL_DX - TAIL_W), LIMB_ROW - 1)
        stamp(c, mirror(BIRD), bx, LIMB_ROW - 1 - (len(BIRD) - 1))
    else:
        stamp(c, TAIL, bx + TAIL_DX, LIMB_ROW - 1)
        stamp(c, BIRD, bx, LIMB_ROW - 1 - (len(BIRD) - 1))
    return c


def rects(grid, skip=None):
    """Horizontal runs of one color -> <rect>s. `skip` masks cells drawn elsewhere."""
    out = []
    for y, row in enumerate(grid):
        x = 0
        while x < W:
            ch = row[x]
            if ch == "." or (skip and skip[y][x] != "."):
                x += 1
                continue
            x1 = x
            while x1 + 1 < W and row[x1 + 1] == ch and not (skip and skip[y][x1 + 1] != "."):
                x1 += 1
            r, g, b = PALETTE[ch]
            out.append(f'<rect x="{x * PX}" y="{y * PX}" width="{(x1 - x + 1) * PX}" '
                       f'height="{PX}" fill="#{r:02x}{g:02x}{b:02x}"/>')
            x = x1 + 1
    return "".join(out)


def main():
    branch = blank()
    draw_branch(branch)
    branch = mirror(branch)
    n = len(WALK)
    dur = n * FRAME_S
    frames = []
    for i, (dx, face) in enumerate(WALK):
        layer = mirror(bird_layer(dx, face))
        frames.append(f'<g class="f" style="animation-delay:{i * FRAME_S:.2f}s">'
                      f'{rects(layer, skip=branch)}</g>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W * PX} {H * PX}" '
        f'width="{W * PX}" height="{H * PX}" shape-rendering="crispEdges" '
        f'role="img" aria-label="A pixel scarlet macaw walking along a branch">'
        f'<style>.f{{opacity:0;animation:walk {dur:.2f}s step-end infinite}}'
        f'@keyframes walk{{0%{{opacity:1}}{100 / n:.4f}%{{opacity:0}}100%{{opacity:0}}}}</style>'
        f'{"".join(frames)}<g>{rects(branch)}</g></svg>\n'
    )
    out = Path(__file__).resolve().parent.parent / "assets" / "parrot.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text(svg)
    print(f"wrote {out} ({len(svg) // 1024} KB, {n} frames)")


if __name__ == "__main__":
    main()
