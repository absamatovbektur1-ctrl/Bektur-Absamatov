#!/usr/bin/env python3
"""
iMessage-style story renderer (1080x1920). Each frame shows the chat up to that
point; when it no longer fits, the oldest messages scroll off the top.

    python3 carousels/chat_render.py carousels/workspace/<slug>

config.json:
{
  "handle": "@kisowss",
  "contact": "Я год назад",
  "messages": [
    {"from": "them", "text": "..."},
    {"from": "me", "text": "...", "frame": true}   # frame=true ends a story frame here
  ],
  "typing_last": true                              # show "..." bubble on the last frame
}
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
TOP, BOT = 200, 230
ROOT = Path(__file__).resolve().parent
FONT = ROOT / "assets" / "fonts" / "Inter.ttf"

BG = (255, 255, 255)
INK = (0, 0, 0)
GRAY = (142, 142, 147)
THEM = (233, 233, 235)
ME = (10, 132, 255)
HAIR = (229, 229, 234)
PAD = 40
MAX_BUBBLE = 800


def font(size, weight="Regular"):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_name(weight)
    return f


F_MSG = font(56)
F_NAME = font(34, "Medium")
F_SMALL = font(28, "Medium")
F_AVATAR = font(54, "SemiBold")
LH = 72


def wrap(d, text, max_w):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=F_MSG) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur] if cur else lines


def bubble_size(d, msg):
    lines = wrap(d, msg["text"], MAX_BUBBLE - 64)
    w = max(d.textlength(l, font=F_MSG) for l in lines) + 64
    return lines, int(w), len(lines) * LH + 34


def header(d, contact):
    y = TOP + 40
    d.line([(PAD + 22, y - 22), (PAD, y), (PAD + 22, y + 22)], fill=ME, width=6, joint="curve")
    cx = W // 2
    d.ellipse([cx - 56, y - 50, cx + 56, y + 62], fill=(160, 166, 178))
    initials = "".join(p[0] for p in contact.split()[:2]).upper()
    d.text((cx, y + 6), initials, font=F_AVATAR, fill=BG, anchor="mm")
    d.text((cx, y + 100), contact + "  ›", font=F_NAME, fill=INK, anchor="mm")
    d.line([(0, y + 150), (W, y + 150)], fill=HAIR, width=2)
    return y + 190


def draw_bubble(d, msg, lines, w, h, y):
    me = msg["from"] == "me"
    x0 = W - PAD - w if me else PAD
    d.rounded_rectangle([x0, y, x0 + w, y + h], radius=42, fill=ME if me else THEM)
    ty = y + 14
    for line in lines:
        d.text((x0 + 32, ty), line, font=F_MSG, fill=BG if me else INK)
        ty += LH


def typing(d, y):
    d.rounded_rectangle([PAD, y, PAD + 170, y + 92], radius=46, fill=THEM)
    for i in range(3):
        cx = PAD + 50 + i * 35
        d.ellipse([cx - 11, y + 35, cx + 11, y + 57], fill=GRAY)


def render_frame(cfg, msgs, show_typing, idx, total):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    top = header(d, cfg["contact"])
    bottom = H - BOT - 130
    sized = [(m, *bubble_size(d, m)) for m in msgs]
    gaps = []
    for i, (m, *_rest) in enumerate(sized):
        gaps.append(0 if i == 0 else (12 if sized[i - 1][0]["from"] == m["from"] else 34))
    need = sum(h for *_x, h in sized) + sum(gaps) + (130 if show_typing else 0)
    start = 0
    while need > bottom - top and start < len(sized) - 1:  # scroll oldest off
        need -= sized[start][3] + gaps[start + 1]
        start += 1
    y = bottom - need
    if start == 0:
        y = top
    for i in range(start, len(sized)):
        if i > start:
            y += gaps[i]
        m, lines, w, h = sized[i]
        draw_bubble(d, m, lines, w, h, y)
        y += h
    if show_typing:
        typing(d, y + 34)
    # input bar
    iy = H - BOT - 80
    d.line([(0, iy - 40), (W, iy - 40)], fill=HAIR, width=2)
    d.rounded_rectangle([PAD + 70, iy - 22, W - PAD, iy + 52], radius=37, outline=HAIR, width=3)
    d.text((PAD + 105, iy + 15), "iMessage", font=F_SMALL, fill=GRAY, anchor="lm")
    d.text((PAD + 20, iy + 15), "+", font=font(56, "Light"), fill=GRAY, anchor="mm")
    d.text((W // 2, H - BOT + 40), f"{cfg['handle']}  ·  {idx}/{total}", font=F_SMALL, fill=GRAY, anchor="mm")
    return img


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    cfg = json.loads((src / "config.json").read_text(encoding="utf-8"))
    msgs = cfg["messages"]
    cuts = [i + 1 for i, m in enumerate(msgs) if m.get("frame")]
    if not cuts or cuts[-1] != len(msgs):
        cuts.append(len(msgs))
    for n, cut in enumerate(cuts, 1):
        last = n == len(cuts)
        render_frame(cfg, msgs[:cut], last and cfg.get("typing_last"), n, len(cuts)).save(src / f"slide_{n}.png")
        print(f"  slide_{n}.png")


if __name__ == "__main__":
    main()
