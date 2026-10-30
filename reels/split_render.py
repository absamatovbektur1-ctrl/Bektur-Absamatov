#!/usr/bin/env python3
"""
"Да… но" split-screen Reel (trend, Oct 2026). 1080x1920 H.264, no audio.
Top half: the "yes" (looks bad, muted colours). Bottom half: the "but" (bright).
Each pair shows the top first, then reveals the bottom.

    python3 reels/split_render.py reels/<slug>

config.json:
{
  "labels": ["Да", "Но"],
  "pairs": [ {"top": {"img": "...", "text": "...", "x": 0.5, "y": 0.5},
              "bottom": {"img": "...", "text": "..."}} ],
  "final": {"img": "...", "text": "...", "y": 0.5},
  "timing": {"top": 1.4, "both": 2.6, "final": 3.0}
}
"""

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1920
HALF = H // 2
ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "assets" / "photos"
FONT = ROOT / "carousels" / "assets" / "fonts" / "Inter.ttf"


def font(size, weight):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_name(weight)
    return f


F_TEXT = font(64, "Bold")
F_LABEL = font(40, "Bold")


def cover(name, w, h, fx=0.5, fy=0.5):
    im = ImageOps.exif_transpose(Image.open(PHOTOS / name)).convert("RGB")
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    left = int(min(max(fx * im.width - w / 2, 0), im.width - w))
    top = int(min(max(fy * im.height - h / 2, 0), im.height - h))
    return im.crop((left, top, left + w, top + h))


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


def text_block(img, text, cy, f=F_TEXT, lh=82):
    """White centred text with a soft shadow, vertically centred on cy."""
    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)
    lines = wrap(d, text, f, W - 160)
    y = cy - len(lines) * lh // 2
    for line in lines:
        d.text((W // 2, y), line, font=f, fill=(255, 255, 255, 255), anchor="ma")
        y += lh
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(layer.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda a: int(a * 0.7)))
    return Image.alpha_composite(Image.alpha_composite(img, shadow), layer)


def label(img, text, x, y, bg, fg):
    d = ImageDraw.Draw(img)
    w = d.textlength(text, font=F_LABEL) + 56
    d.rounded_rectangle([x, y, x + w, y + 70], radius=35, fill=bg)
    d.text((x + 28, y + 35), text, font=F_LABEL, fill=fg, anchor="lm")


def half(spec, muted):
    im = cover(spec["img"], W, HALF, spec.get("x", 0.5), spec.get("y", 0.5))
    if muted:
        im = ImageEnhance.Color(im).enhance(0.25)
        im = ImageEnhance.Brightness(im).enhance(0.6)
    else:
        im = ImageEnhance.Color(im).enhance(1.12)
        im = ImageEnhance.Contrast(im).enhance(1.05)
    return im.convert("RGBA")


def pair_frames(cfg, p):
    yes, no = cfg.get("labels", ["Да", "Но"])
    top = text_block(half(p["top"], True), p["top"]["text"], HALF - 150)
    label(top, yes, 60, 230, (255, 255, 255, 235), (20, 20, 24))
    bottom = text_block(half(p["bottom"], False), p["bottom"]["text"], HALF - 330)
    label(bottom, no, 60, 40, (255, 214, 10, 255), (20, 20, 24))

    a = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    a.paste(top, (0, 0))
    dim = bottom.filter(ImageFilter.GaussianBlur(40))
    dim = Image.alpha_composite(dim, Image.new("RGBA", dim.size, (0, 0, 0, 150)))
    a.paste(dim, (0, HALF))
    a = text_block(a, no + "…", HALF + HALF // 2 - 40)

    b = Image.new("RGBA", (W, H))
    b.paste(top, (0, 0))
    b.paste(bottom, (0, HALF))
    ImageDraw.Draw(b).line([(0, HALF), (W, HALF)], fill=(255, 255, 255), width=6)
    return a.convert("RGB"), b.convert("RGB")


def final_frame(cfg):
    f = cfg["final"]
    im = cover(f["img"], W, H, f.get("x", 0.5), f.get("y", 0.5)).convert("RGBA")
    im = Image.alpha_composite(im, Image.new("RGBA", im.size, (0, 0, 0, 70)))
    return text_block(im, f["text"], 560, font(76, "Bold"), 96).convert("RGB")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    cfg = json.loads((src / "config.json").read_text(encoding="utf-8"))
    t = {"top": 1.4, "both": 2.6, "final": 3.0, **cfg.get("timing", {})}
    fdir = src / "frames"
    fdir.mkdir(exist_ok=True)
    seq = []
    for p in cfg["pairs"]:
        a, b = pair_frames(cfg, p)
        seq += [(a, t["top"]), (b, t["both"])]
    seq.append((final_frame(cfg), t["final"]))
    lines = []
    for i, (im, dur) in enumerate(seq):
        path = (fdir / f"{i:02d}.png").resolve()
        im.save(path)
        lines += [f"file '{path}'", f"duration {dur}"]
    lines.append(lines[-2])  # concat demuxer needs the last file repeated
    (src / "list.txt").write_text("\n".join(lines) + "\n")
    tmp, out = src / "tmp.mp4", src / "reel.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(src / "list.txt"),
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "fast", str(tmp)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-fflags", "+genpts+igndts", "-i", str(tmp),
                    "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    tmp.unlink()
    print(f"  {out}")


if __name__ == "__main__":
    main()
