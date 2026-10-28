#!/usr/bin/env python3
"""
Tweet-style carousel renderer (1080x1350): one post card per slide.

    python3 carousels/tweet_render.py carousels/workspace/<slug>

config.json:
{
  "name": "Бектур", "handle": "@kisowss", "time": "21:40 · 29 окт. 2026",
  "slides": [ {"paras": ["Абзац с ==выделением==.", "Ещё абзац."], "big": false} ]
}
Avatar: carousels/assets/headshot.jpg.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from notes_render import draw_words, font

W, H = 1080, 1350
ROOT = Path(__file__).resolve().parent
AVATAR = ROOT / "assets" / "headshot.jpg"

BG = (255, 255, 255)
INK = (15, 20, 25)
GRAY = (83, 100, 113)
HAIR = (239, 243, 244)
PAD = 90
TEXT_W = W - PAD * 2

F_NAME = font(42, "Bold")
F_HANDLE = font(38, "Regular")
F_TEXT = font(60, "Regular")
F_BIG = font(74, "SemiBold")
F_META = font(32, "Regular")
LH = 84
LH_BIG = 98


def avatar(size):
    im = ImageOps.fit(Image.open(AVATAR).convert("RGB"), (size * 2, size * 2))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, *im.size], fill=255)
    out = Image.new("RGBA", im.size)
    out.paste(im, (0, 0), mask)
    return out.resize((size, size), Image.LANCZOS)


def text_style(slide):
    return (F_BIG, LH_BIG) if slide.get("big") else (F_TEXT, LH)


def measure(cfg, slide, d):
    """Height of the text block, by drawing it on a throwaway canvas."""
    tmp = Image.new("RGBA", (W, 4000))
    td = ImageDraw.Draw(tmp)
    y = 0
    f, lh = text_style(slide)
    for p in slide["paras"]:
        td, y = draw_words(tmp, td, p, 0, y, f, INK, TEXT_W, lh)
        y += 34
    return y - 34


def render(cfg, slide, idx, total):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    body_h = measure(cfg, slide, d)
    card_h = 120 + 50 + body_h + 60 + 50
    y = max(110, (H - card_h) // 2 - 30)
    av = avatar(120)
    img.alpha_composite(av, (PAD, y))
    d.text((PAD + 150, y + 22), cfg["name"], font=F_NAME, fill=INK)
    d.text((PAD + 150, y + 74), cfg["handle"], font=F_HANDLE, fill=GRAY)
    y += 170
    f, lh = text_style(slide)
    for p in slide["paras"]:
        d, y = draw_words(img, d, p, PAD, y, f, INK, TEXT_W, lh)
        y += 34
    y += 26
    d.text((PAD, y), cfg["time"], font=F_META, fill=GRAY)
    y += 70
    d.line([(PAD, y), (W - PAD, y)], fill=HAIR, width=3)
    # page dots
    dots_w = total * 26
    x0 = (W - dots_w) // 2
    for i in range(total):
        c = INK if i == idx else (207, 217, 222)
        d.ellipse([x0 + i * 26, H - 90, x0 + i * 26 + 12, H - 78], fill=c)
    return img.convert("RGB")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    cfg = json.loads((src / "config.json").read_text(encoding="utf-8"))
    for i, s in enumerate(cfg["slides"]):
        render(cfg, s, i, len(cfg["slides"])).save(src / f"slide_{i + 1}.png")
        print(f"  slide_{i + 1}.png")


if __name__ == "__main__":
    main()
