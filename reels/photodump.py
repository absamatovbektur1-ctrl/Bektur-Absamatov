#!/usr/bin/env python3
"""
Photo-dump Reel: photos cut fast to the beat, one line of text on top. 1080x1920 H.264.

    python3 reels/photodump.py reels/<slug>

config.json:
{
  "frames": [ {"img": "walk-road-back.jpg", "x": 0.5, "y": 0.5, "dur": 1.2, "text": "a"} ],
  "texts": { "a": "line one||line two" }
}
Photos come from assets/photos/. x/y = crop focus (0..1). No audio: add a trending
sound in the Instagram app when posting.
"""

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1920
ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "assets" / "photos"
FONT = ROOT / "carousels" / "assets" / "fonts" / "Inter.ttf"
TEXT_TOP = 440  # where IG-native reel text usually sits


def cover(path, fx, fy):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    left = int(min(max(fx * im.width - W / 2, 0), im.width - W))
    top = int(min(max(fy * im.height - H / 2, 0), im.height - H))
    im = im.crop((left, top, left + W, top + H))
    im = ImageEnhance.Contrast(im).enhance(1.06)
    return ImageEnhance.Color(im).enhance(1.08)


def overlay_text(im, text):
    f = ImageFont.truetype(str(FONT), 58)
    f.set_variation_by_name("Bold")
    layer = Image.new("RGBA", im.size)
    d = ImageDraw.Draw(layer)
    y = TEXT_TOP
    for line in text.split("||"):
        d.text((W // 2, y), line, font=f, fill=(255, 255, 255, 255), anchor="ma",
               stroke_width=0)
        y += 74
    shadow = layer.split()[3].filter(ImageFilter.GaussianBlur(10))
    dark = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dark.putalpha(shadow.point(lambda a: int(a * 0.55)))
    out = Image.alpha_composite(im.convert("RGBA"), dark)
    return Image.alpha_composite(out, layer).convert("RGB")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    cfg = json.loads((src / "config.json").read_text(encoding="utf-8"))
    fdir = src / "frames"
    fdir.mkdir(exist_ok=True)
    lines = []
    for i, fr in enumerate(cfg["frames"]):
        im = cover(PHOTOS / fr["img"], fr.get("x", 0.5), fr.get("y", 0.5))
        if fr.get("text"):
            im = overlay_text(im, cfg["texts"][fr["text"]])
        p = fdir / f"{i:02d}.png"
        im.save(p)
        lines += [f"file '{p.resolve()}'", f"duration {fr['dur']}"]
    lines.append(f"file '{(fdir / f'{len(cfg['frames']) - 1:02d}.png').resolve()}'")  # concat quirk
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
