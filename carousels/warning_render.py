#!/usr/bin/env python3
"""
"Sensitive content" warning-screen carousel (trend parody), 1080x1350.

    python3 carousels/warning_render.py carousels/workspace/<slug>

config.json:
{
  "handle": "@kisowss",
  "bg_photo": "walk-road-back.jpg",
  "slides": [
    {"type": "warning", "title": "...", "text": "...", "button": "..."},
    {"type": "confirm", "title": "...", "text": "...", "yes": "...", "no": "..."},
    {"type": "note", "meta": "...", "title": "...", "items": ["..."], "caption": "...", "sub": "..."},
    {"type": "final", "lines": ["...", "==accent=="], "small": "..."}
  ]
}
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from notes_render import draw_words, font

W, H = 1080, 1350
ROOT = Path(__file__).resolve().parent
PHOTOS = ROOT.parent / "assets" / "photos"
WHITE = (255, 255, 255)
SOFT = (210, 210, 215)
DIM = (150, 150, 158)
ORANGE = (255, 122, 26)
PAD = 110
TEXT_W = W - PAD * 2


def blurred_bg(name):
    im = ImageOps.fit(ImageOps.exif_transpose(Image.open(PHOTOS / name)).convert("RGB"), (W, H))
    im = im.filter(ImageFilter.GaussianBlur(60))
    return ImageEnhance.Brightness(im).enhance(0.45).convert("RGBA")


def eye_slash(d, cx, cy):
    d.ellipse([cx - 70, cy - 40, cx + 70, cy + 40], outline=WHITE, width=7)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=WHITE)
    d.line([(cx - 80, cy - 70), (cx + 80, cy + 70)], fill=WHITE, width=8)


def centered(img, d, text, y, f, color, lh):
    """Centered multi-line text; ==...== drawn in orange (may span lines)."""
    acc_start = False
    for line in text.split("\n"):
        plain = line.replace("==", "")
        x = (W - d.textlength(plain, font=f)) // 2
        acc = acc_start
        for part in line.split("=="):
            if part:
                d.text((x, y), part, font=f, fill=ORANGE if acc else color)
                x += d.textlength(part, font=f)
            acc = not acc
        acc_start = not acc  # the loop flips once past the last part
        y += lh
    return y


def wrap_center(img, d, text, y, f, color, lh, width=TEXT_W):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t.replace("==", ""), font=f) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return centered(img, d, "\n".join(lines), y, f, color, lh)


def warning(cfg, s, bg):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    eye_slash(d, W // 2, 430)
    y = wrap_center(img, d, s["title"], 560, font(58, "Bold"), WHITE, 76)
    wrap_center(img, d, s["text"], y + 24, font(40), SOFT, 58)
    d.line([(0, H - 230), (W, H - 230)], fill=(255, 255, 255, 90), width=2)
    d.text((W // 2, H - 160), s["button"], font=font(42, "SemiBold"), fill=WHITE, anchor="mm")
    return img


def confirm(cfg, s, bg):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    y = wrap_center(img, d, s["title"], 400, font(64, "Bold"), WHITE, 84)
    y = wrap_center(img, d, s["text"], y + 30, font(40), SOFT, 58)
    by = y + 90
    for i, label in enumerate((s["yes"], s["no"])):
        x0, x1 = PAD, W - PAD
        if i == 0:
            d.rounded_rectangle([x0, by, x1, by + 110], radius=55, fill=WHITE)
            d.text((W // 2, by + 55), label, font=font(42, "SemiBold"), fill=(20, 20, 24), anchor="mm")
        else:
            d.rounded_rectangle([x0, by, x1, by + 110], radius=55, outline=WHITE, width=4)
            d.text((W // 2, by + 55), label, font=font(42, "SemiBold"), fill=WHITE, anchor="mm")
        by += 140
    return img


def note(cfg, s, bg):
    img = Image.new("RGBA", (W, H), (12, 12, 14, 255))
    d = ImageDraw.Draw(img)
    d.text((W // 2, 120), s["meta"], font=font(32, "Medium"), fill=DIM, anchor="mm")
    x0, y0, x1 = 90, 180, W - 90
    card = Image.new("RGBA", (W, H))
    cd = ImageDraw.Draw(card)
    f_item = font(44)
    item_y = y0 + 170
    item_y_end = item_y + len(s["items"]) * 84
    cd.rounded_rectangle([x0, y0, x1, item_y_end + 40], radius=36, fill=WHITE)
    img.alpha_composite(card)
    d = ImageDraw.Draw(img)
    d.text((x0 + 60, y0 + 60), s["title"], font=font(56, "Bold"), fill=(28, 28, 30))
    for it in s["items"]:
        cx, cy = x0 + 80, item_y + 30
        d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], outline=(199, 199, 204), width=4)
        d.text((cx + 46, item_y + 4), it, font=f_item, fill=(28, 28, 30))
        item_y += 84
    y = centered(img, d, s["caption"], item_y_end + 130, font(110, "Black"), WHITE, 120)
    wrap_center(img, d, s["sub"], y + 10, font(46, "Medium"), SOFT, 62)
    return img


def final(cfg, s, bg):
    img = Image.new("RGBA", (W, H), (12, 12, 14, 255))
    d = ImageDraw.Draw(img)
    f = font(80, "Bold")
    total = len(s["lines"]) * 100
    y = (H - total) // 2 - 120
    for line in s["lines"]:
        y = wrap_center(img, d, line, y, f, WHITE, 100) + 20
    wrap_center(img, d, s["small"], y + 60, font(40, "Medium"), DIM, 56)
    return img


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    cfg = json.loads((src / "config.json").read_text(encoding="utf-8"))
    bg = blurred_bg(cfg["bg_photo"])
    kinds = {"warning": warning, "confirm": confirm, "note": note, "final": final}
    for i, s in enumerate(cfg["slides"], 1):
        img = kinds[s["type"]](cfg, s, bg)
        ImageDraw.Draw(img).text((W // 2, H - 60), cfg["handle"], font=font(30, "Medium"), fill=DIM, anchor="mm")
        img.convert("RGB").save(src / f"slide_{i}.png")
        print(f"  slide_{i}.png")


if __name__ == "__main__":
    main()
