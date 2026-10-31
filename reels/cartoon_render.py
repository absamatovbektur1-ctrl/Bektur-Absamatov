#!/usr/bin/env python3
"""
Cartoon / comic Reel from photos. 1080x1920, 30 fps, H.264, no audio.

Each scene: photo -> cartoon look (flat colours, bold ink lines, halftone shadows),
slow Ken Burns zoom, a yellow narrator box, a speech bubble that pops in with a
spring, a white flash between scenes, and an optional "bam" (shake + starburst).

    python3 reels/cartoon_render.py reels/<slug>

config.json:
{
  "handle": "@kisowss",
  "scenes": [
    {"img": "ski-pose-lift.jpg", "x": 0.5, "y": 0.5, "dur": 1.8,
     "narrator": "И тогда я просто попробовал",
     "bubble": "Поехали!", "bubble_at": [0.62, 0.30], "tail_to": [0.45, 0.42],
     "bam": "БАМ!", "narrator_y": 1400}
  ]
}
bubble_at = bubble centre, tail_to = where the tail points (fractions of the frame).
narrator_y = top of the narrator box in px (default 250; use ~1400 to keep a face clear).
"""

import json
import math
import random
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
ZOOM = 1.10
ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "assets" / "photos"
FONTS = ROOT / "carousels" / "assets" / "fonts"
INK = (18, 18, 22)
YELLOW = (255, 216, 77)


def font(size, weight="ExtraBold"):
    f = ImageFont.truetype(str(FONTS / "Rubik.ttf"), size)
    f.set_variation_by_name(weight)
    return f


F_NARR = font(46, "Bold")
F_BUBBLE = font(54, "ExtraBold")
F_BAM = font(170, "Black")
F_HANDLE = font(34, "SemiBold")


# -- cartoon look --------------------------------------------------------------

def cover(path, w, h, fx, fy):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    left = int(min(max(fx * im.width - w / 2, 0), im.width - w))
    top = int(min(max(fy * im.height - h / 2, 0), im.height - h))
    return im.crop((left, top, left + w, top + h))


def cartoonize(pil):
    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    # lift dark photos so the cartoon stays bright
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    lab[..., 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[..., 0])
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    # painterly flat shading that keeps faces readable
    paint = cv2.stylization(img, sigma_s=50, sigma_r=0.35)
    # posterize to a few tones per channel for the "cel" look
    paint = (paint // 36) * 36 + 18
    paint = cv2.bilateralFilter(paint, 7, 40, 40)
    # thin ink lines from the original detail, isolated specks removed
    gray = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 5)
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 11)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
    out = cv2.bitwise_and(paint, paint, mask=edges)
    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.3, 0, 255)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    # light halftone dots only in mid shadows
    lum = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
    step = 16
    dots = np.full(lum.shape, 255, np.uint8)
    for y in range(0, lum.shape[0], step):
        for x in range((y // step % 2) * step // 2, lum.shape[1], step):
            if 30 < lum[y, x] < 80:
                cv2.circle(dots, (x, y), 3, 0, -1)
    out = np.where(dots[..., None] == 0, (out * 0.75).astype(np.uint8), out)
    return Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))


# -- overlays --------------------------------------------------------------------

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


def narrator_box(text):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = wrap(d, text, F_NARR, 820)
    w = int(max(d.textlength(l, font=F_NARR) for l in lines)) + 60
    h = len(lines) * 58 + 40
    im = Image.new("RGBA", (w + 14, h + 14))
    dd = ImageDraw.Draw(im)
    dd.rectangle([10, 10, w + 10, h + 10], fill=INK)  # hard comic shadow
    dd.rectangle([0, 0, w, h], fill=YELLOW, outline=INK, width=6)
    y = 20
    for line in lines:
        dd.text((30, y), line, font=F_NARR, fill=INK)
        y += 58
    return im


def bubble(text, centre, tail_to):
    """Full-frame RGBA layer with a speech bubble; returns (layer, bbox)."""
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    lines = wrap(d, text, F_BUBBLE, 640)
    tw = max(d.textlength(l, font=F_BUBBLE) for l in lines)
    bw, bh = int(tw) + 110, len(lines) * 66 + 80
    cx, cy = int(centre[0] * W), int(centre[1] * H)
    box = [cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2]
    tx, ty = int(tail_to[0] * W), int(tail_to[1] * H)
    base = [(cx - 40, cy + bh // 2 - 10), (cx + 40, cy + bh // 2 - 10)] if ty > cy else \
           [(cx - 40, cy - bh // 2 + 10), (cx + 40, cy - bh // 2 + 10)]
    d.polygon([base[0], (tx, ty), base[1]], fill=INK)
    d.ellipse([box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6], fill=INK)
    inner = [(base[0][0] + 9, base[0][1]), (tx + (cx - tx) // 12, ty + (cy - ty) // 12), (base[1][0] - 9, base[1][1])]
    d.polygon(inner, fill="white")
    d.ellipse(box, fill="white")
    y = cy - len(lines) * 66 // 2
    for line in lines:
        d.text((cx, y), line, font=F_BUBBLE, fill=INK, anchor="ma")
        y += 66
    pad = 20
    bbox = (min(box[0], tx) - pad, min(box[1], ty) - pad, max(box[2], tx) + pad, max(box[3], ty) + pad)
    return layer, bbox


def starburst(text):
    im = Image.new("RGBA", (760, 520))
    d = ImageDraw.Draw(im)
    cx, cy, pts = 380, 260, []
    for i in range(24):
        r = 250 if i % 2 == 0 else 150
        a = math.pi * 2 * i / 24
        pts.append((cx + r * 1.35 * math.cos(a), cy + r * math.sin(a)))
    d.polygon([(x + 10, y + 10) for x, y in pts], fill=INK)
    d.polygon(pts, fill=(235, 52, 52), outline=INK, width=8)
    d.text((cx, cy), text, font=F_BAM, fill=YELLOW, anchor="mm", stroke_width=8, stroke_fill=INK)
    return im


def pop_scale(t):
    """Seconds since the pop -> scale that grows fast, overshoots, then settles at 1."""
    if t <= 0:
        return 0.0
    return max(0.0, 1 + 0.3 * math.exp(-6 * t) * math.cos(14 * t) - 0.3 * math.exp(-40 * t) * 3.3)


# -- render ------------------------------------------------------------------------

def scene_frames(cfg, sc, first, rng):
    bw, bh = int(W * ZOOM), int(H * ZOOM)
    art = cartoonize(cover(PHOTOS / sc["img"], bw, bh, sc.get("x", 0.5), sc.get("y", 0.5))).convert("RGBA")
    narr = narrator_box(sc["narrator"]) if sc.get("narrator") else None
    bub = bubble(sc["bubble"], sc.get("bubble_at", [0.5, 0.3]), sc.get("tail_to", [0.5, 0.45])) if sc.get("bubble") else None
    bam = starburst(sc["bam"]) if sc.get("bam") else None
    n = int(sc["dur"] * FPS)
    for i in range(n):
        p = i / max(1, n - 1)
        z = 1 + (ZOOM - 1) * p
        cw, ch = int(bw / z), int(bh / z)
        x0, y0 = (bw - cw) // 2, (bh - ch) // 2
        frame = art.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)
        if bam and i < 10:  # camera shake
            s = int(22 * (1 - i / 10))
            frame = frame.transform(frame.size, Image.AFFINE, (1, 0, rng.randint(-s, s), 0, 1, rng.randint(-s, s)))
        t = i / FPS
        if narr is not None:
            slide = min(1.0, t / 0.18)
            nx = int(-narr.width + (60 + narr.width) * (1 - (1 - slide) ** 3))
            frame.alpha_composite(narr, (nx, sc.get("narrator_y", 250)))
        if bub is not None:
            layer, bbox = bub
            sc_ = pop_scale(t - 0.3)
            if sc_ > 0.05:
                crop = layer.crop(bbox)
                cw2, ch2 = max(1, int(crop.width * sc_)), max(1, int(crop.height * sc_))
                crop = crop.resize((cw2, ch2), Image.BILINEAR)
                cx, cy = (bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2
                frame.alpha_composite(crop, (max(0, cx - cw2 // 2), max(0, cy - ch2 // 2)))
        if bam is not None:
            sc_ = pop_scale(t - 0.05)
            if sc_ > 0.05:
                b = bam.resize((max(1, int(bam.width * sc_)), max(1, int(bam.height * sc_))), Image.BILINEAR)
                frame.alpha_composite(b, ((W - b.width) // 2, int(H * 0.62) - b.height // 2))
        if not first and i < 3:  # white flash cut
            frame = Image.blend(frame, Image.new("RGBA", frame.size, (255, 255, 255, 255)), 0.8 - i * 0.3)
        d = ImageDraw.Draw(frame)
        d.text((W // 2, H - 330), cfg["handle"], font=F_HANDLE, fill="white", anchor="mm",
               stroke_width=4, stroke_fill=INK)
        # comic page border
        d.rectangle([0, 0, W - 1, H - 1], outline=INK, width=14)
        yield frame.convert("RGB")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    cfg = json.loads((src / "config.json").read_text(encoding="utf-8"))
    tmp, out = src / "tmp.mp4", src / "reel.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                           "-preset", "fast", "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    rng = random.Random(7)
    poster = None
    for k, sc in enumerate(cfg["scenes"]):
        print(f"  scene {k + 1}/{len(cfg['scenes'])}: {sc['img']}")
        for j, fr in enumerate(scene_frames(cfg, sc, k == 0, rng)):
            ff.stdin.write(fr.tobytes())
            if k == 0 and j == int(sc["dur"] * FPS) - 1:
                poster = fr
    ff.stdin.close()
    ff.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-fflags", "+genpts+igndts", "-i", str(tmp),
                    "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    tmp.unlink()
    if poster:
        poster.save(src / "cover.png")
    print(f"  {out}")


if __name__ == "__main__":
    main()
