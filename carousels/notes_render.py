#!/usr/bin/env python3
"""
iPhone Notes-style carousel renderer (1080x1350, light mode).

    python3 carousels/notes_render.py carousels/workspace/<slug>

config.json:
{
  "handle": "@kisowss",
  "date": "28 октября 2026 г. в 21:40",
  "slides": [
    {"title": "Заголовок заметки",
     "blocks": [
       {"p": "Абзац. ==Выделение маркером== поддерживается."},
       {"check": ["пункт", "пункт"], "done": [0]},
       {"img": "photo.jpg"},
       {"space": 30}
     ]}
  ]
}
Images resolve from <slug>/reference/ first, then assets/photos/.
"""

import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1350
ROOT = Path(__file__).resolve().parent
FONT = ROOT / "assets" / "fonts" / "Inter.ttf"
PHOTOS = ROOT.parent / "assets" / "photos"

BG = (255, 255, 255)
INK = (28, 28, 30)
GRAY = (142, 142, 147)
HAIR = (229, 229, 234)
YELLOW = (227, 160, 8)          # iOS Notes accent
MARK = (255, 214, 10, 110)      # highlighter
PAD = 72
TEXT_W = W - PAD * 2


def font(size, weight="Regular"):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_name(weight)
    return f


F_NAV = font(40, "Regular")
F_DATE = font(28, "Medium")
F_TITLE = font(62, "Bold")
F_BODY = font(44, "Regular")
F_FOOT = font(28, "Medium")


def nav_bar(d):
    y = 64
    # back chevron + label
    d.line([(PAD + 18, y - 18), (PAD, y), (PAD + 18, y + 18)], fill=YELLOW, width=6, joint="curve")
    d.text((PAD + 34, y), "Заметки", font=F_NAV, fill=YELLOW, anchor="lm")
    # share icon
    sx = W - PAD - 150
    d.rounded_rectangle([sx - 18, y - 6, sx + 18, y + 26], radius=5, outline=YELLOW, width=4)
    d.rectangle([sx - 8, y - 8, sx + 8, y - 2], fill=BG)
    d.line([(sx, y + 8), (sx, y - 28)], fill=YELLOW, width=4)
    d.line([(sx - 12, y - 16), (sx, y - 28), (sx + 12, y - 16)], fill=YELLOW, width=4)
    # "more" icon
    mx = W - PAD - 30
    d.ellipse([mx - 26, y - 26, mx + 26, y + 26], outline=YELLOW, width=4)
    for dx in (-12, 0, 12):
        d.ellipse([mx + dx - 3, y - 3, mx + dx + 3, y + 3], fill=YELLOW)


def toolbar(d, footer):
    y = H - 70
    d.line([(0, y - 46), (W, y - 46)], fill=HAIR, width=2)
    # checklist icon
    x = PAD + 10
    d.ellipse([x - 14, y - 14, x + 14, y + 14], outline=YELLOW, width=4)
    d.line([(x - 6, y), (x - 1, y + 6), (x + 7, y - 6)], fill=YELLOW, width=4)
    # compose icon
    cx = W - PAD - 20
    d.rounded_rectangle([cx - 22, y - 18, cx + 14, y + 20], radius=6, outline=YELLOW, width=4)
    d.line([(cx - 4, y + 2), (cx + 24, y - 26)], fill=YELLOW, width=5)
    d.text((W // 2, y), footer, font=F_FOOT, fill=GRAY, anchor="mm")


def tokens(text):
    """Split text into (word, highlighted) pairs; ==...== marks a highlight."""
    out = []
    for i, part in enumerate(re.split(r"==", text)):
        for j, w in enumerate(part.split()):
            # punctuation right after a highlight sticks to the previous word
            glue = j == 0 and bool(out) and not part[:1].isspace() and re.fullmatch(r"[.,!?:;»)]+", w) is not None
            out.append((w, i % 2 == 1, glue))
    return out


def layout(words, f, max_w, d):
    lines, cur = [], []
    for w in words:
        test = " ".join(t[0] for t in cur + [w])
        if d.textlength(test, font=f) <= max_w or not cur:
            cur.append(w)
        else:
            lines.append(cur)
            cur = [w]
    if cur:
        lines.append(cur)
    return lines


def draw_words(img, d, text, x, y, f, color, max_w, lh):
    space = d.textlength(" ", font=f)
    for line in layout(tokens(text), f, max_w, d):
        cx = x
        for i, (w, hl, glue) in enumerate(line):
            if glue and i:
                cx -= space
            wl = d.textlength(w, font=f)
            if hl:
                nxt = i + 1 < len(line) and line[i + 1][1]
                ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
                ImageDraw.Draw(ov).rounded_rectangle(
                    [cx - 6, y + lh * 0.12, cx + wl + (space if nxt else 6), y + lh * 0.86], radius=6, fill=MARK)
                img.alpha_composite(ov)
                d = ImageDraw.Draw(img)
            d.text((cx, y), w, font=f, fill=color)
            cx += wl + space
        y += lh
    return d, y


def paste_photo(img, path, y, max_h, focus=0.5):
    """Full text width; crop vertically around `focus` (0 top .. 1 bottom) to fit."""
    ph = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    ph = ph.resize((TEXT_W, int(ph.height * TEXT_W / ph.width)), Image.LANCZOS)
    h = min(ph.height, int(max_h))
    top = int(min(max(focus * ph.height - h / 2, 0), ph.height - h))
    ph = ph.crop((0, top, TEXT_W, top + h))
    mask = Image.new("L", ph.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, ph.width, ph.height], radius=22, fill=255)
    img.paste(ph, (PAD, y), mask)
    return y + ph.height


def render_slide(cfg, slide, idx, total, src_dir):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    nav_bar(d)
    y = 140
    if idx == 0 and cfg.get("date"):
        d.text((W // 2, y), cfg["date"], font=F_DATE, fill=GRAY, anchor="mt")
        y += 70
    else:
        y += 20
    if slide.get("title"):
        d, y = draw_words(img, d, slide["title"], PAD, y, F_TITLE, INK, TEXT_W, 78)
        y += 26
    bottom = H - 140
    lh = 62
    for b in slide.get("blocks", []):
        if "p" in b:
            d, y = draw_words(img, d, b["p"], PAD, y, F_BODY, INK, TEXT_W, lh)
            y += 30
        elif "check" in b:
            done = set(b.get("done", []))
            for i, item in enumerate(b["check"]):
                cx, cy = PAD + 22, y + 30
                if i in done:
                    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=YELLOW)
                    d.line([(cx - 10, cy + 1), (cx - 3, cy + 9), (cx + 11, cy - 8)], fill=BG, width=5)
                    color = GRAY
                else:
                    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], outline=(199, 199, 204), width=4)
                    color = INK
                d, y = draw_words(img, d, item, PAD + 70, y, F_BODY, color, TEXT_W - 70, lh)
                y += 18
            y += 14
        elif "img" in b:
            p = src_dir / "reference" / b["img"]
            if not p.exists():
                p = PHOTOS / b["img"]
            if p.exists():
                y = paste_photo(img, p, y + 6, max(240, bottom - y - 40), b.get("focus", 0.5)) + 30
                d = ImageDraw.Draw(img)
            else:
                print(f"  warning: image not found: {b['img']}")
        elif "space" in b:
            y += b["space"]
    if y > bottom:
        print(f"  warning: slide {idx + 1} overflows by {y - bottom}px, shorten the text")
    toolbar(d, f"{cfg['handle']}  ·  {idx + 1}/{total}")
    return img.convert("RGB")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    cfg = json.loads((src / "config.json").read_text(encoding="utf-8"))
    slides = cfg["slides"]
    for i, s in enumerate(slides):
        out = src / f"slide_{i + 1}.png"
        render_slide(cfg, s, i, len(slides), src).save(out)
        print(f"  {out.name}")


if __name__ == "__main__":
    main()
