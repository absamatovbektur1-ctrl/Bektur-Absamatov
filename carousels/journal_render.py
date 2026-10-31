#!/usr/bin/env python3
"""
Photo-journal carousel (photo dump + one lesson per photo), 1080x1350.
Full-bleed photo with a soft film grade, a small counter, and a serif caption.

    python3 carousels/journal_render.py carousels/workspace/<slug>

config.json:
{
  "handle": "@kisowss",
  "kicker": "уроки 2026",
  "slides": [
    {"img": "yurt-portrait-fur.jpg", "title": "Большой заголовок", "text": "подзаголовок", "x": 0.5, "y": 0.4},
    {"img": "batu-caves.jpg", "text": "Один урок под фото.", "x": 0.6, "y": 0.5}
  ]
}
A slide with "title" is a cover: big serif title, no counter.
"""

import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

W, H = 1080, 1350
ROOT = Path(__file__).resolve().parent
PHOTOS = ROOT.parent / "assets" / "photos"
FONTS = ROOT / "assets" / "fonts"
PAD = 80


def font(name, size, weight="Regular"):
    f = ImageFont.truetype(str(FONTS / name), size)
    f.set_variation_by_name(weight)
    return f


F_COVER = font("Lora.ttf", 104, "SemiBold")
F_CAPTION = font("Lora-Italic.ttf", 56, "Medium Italic")
F_SMALL = font("Inter.ttf", 30, "Medium")


def cover_crop(name, fx, fy):
    im = ImageOps.exif_transpose(Image.open(PHOTOS / name)).convert("RGB")
    r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    left = int(min(max(fx * im.width - W / 2, 0), im.width - W))
    top = int(min(max(fy * im.height - H / 2, 0), im.height - H))
    return im.crop((left, top, left + W, top + H))


def film(im, seed):
    """Warm, slightly faded grade with fine grain."""
    im = ImageEnhance.Color(im).enhance(0.9)
    im = ImageEnhance.Contrast(im).enhance(0.95)
    warm = Image.new("RGB", im.size, (255, 226, 190))
    im = Image.blend(im, warm, 0.06)
    rnd = random.Random(seed)
    noise = Image.effect_noise((W // 2, H // 2), 22).resize((W, H)).convert("RGB")
    im = Image.blend(im, noise, 0.05 + rnd.random() * 0.01)
    return im.convert("RGBA")


def bottom_gradient(height, strength):
    g = Image.new("L", (1, height))
    for y in range(height):
        g.putpixel((0, y), int(strength * (y / height) ** 1.6))
    alpha = g.resize((W, height))
    layer = Image.new("RGBA", (W, height), (0, 0, 0, 255))
    layer.putalpha(alpha)
    return layer


def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def render(cfg, s, idx, total):
    im = film(cover_crop(s["img"], s.get("x", 0.5), s.get("y", 0.5)), idx)
    im.alpha_composite(bottom_gradient(720, 210), (0, H - 720))
    im.alpha_composite(bottom_gradient(220, 120).transpose(Image.FLIP_TOP_BOTTOM), (0, 0))
    d = ImageDraw.Draw(im)
    white = (255, 255, 255)
    if s.get("title"):
        lines = wrap(d, s["title"], F_COVER, W - PAD * 2)
        y = H - 170 - len(lines) * 116 - (70 if s.get("text") else 0)
        for line in lines:
            d.text((PAD, y), line, font=F_COVER, fill=white)
            y += 116
        if s.get("text"):
            d.text((PAD, y + 20), s["text"], font=F_SMALL, fill=(235, 235, 235))
    else:
        d.text((PAD, 70), f"{idx:02d} / {total - 1:02d}", font=F_SMALL, fill=white)
        lines = wrap(d, s["text"], F_CAPTION, W - PAD * 2)
        y = H - 150 - len(lines) * 72
        for line in lines:
            d.text((PAD, y), line, font=F_CAPTION, fill=white)
            y += 72
    d.text((W - PAD, H - 70), cfg["handle"], font=F_SMALL, fill=(230, 230, 230), anchor="rm")
    if cfg.get("kicker"):
        d.text((W - PAD, 70), cfg["kicker"], font=F_SMALL, fill=white, anchor="ra")
    return im.convert("RGB")


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
