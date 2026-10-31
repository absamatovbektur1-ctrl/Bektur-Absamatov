#!/usr/bin/env python3
"""
Motion Reel from real photos: fast trendy transitions + kinetic text. 1080x1920, 30 fps.

Transitions (field "in" of a shot = how it arrives):
  cut      hard cut with a zoom punch
  whip     whip pan with motion blur (dir: left/right/up/down)
  zoom     zoom-through: previous rushes into camera, next pulls back
  flip     3D page flip around the vertical axis
  page     page turn: previous peels away to the left like a book page, with shadow
  swipe    card swipe: previous flies off rotated, next is underneath (card stack)
  spin     spin + zoom blur
  drop     next drops in as a white-framed card onto the previous (stack builds up)

    python3 reels/motion_render.py reels/<slug>

config.json:
{
  "shots": [ {"img": "x.jpg", "x": 0.5, "y": 0.5, "dur": 0.9, "in": "whip", "dir": "left",
              "text": "слова появляются по одному"} ]
}
"""

import json
import math
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
TR = 8  # transition length in frames
ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "assets" / "photos"
FONT = ROOT / "carousels" / "assets" / "fonts" / "Inter.ttf"
F_TEXT = ImageFont.truetype(str(FONT), 76)
F_TEXT.set_variation_by_name("ExtraBold")


def ease(t):
    return t * t * (3 - 2 * t)


def ease_in(t):
    return t ** 3


def ease_out(t):
    return 1 - (1 - t) ** 3


def load(shot, scale=1.12):
    im = ImageOps.exif_transpose(Image.open(PHOTOS / shot["img"])).convert("RGB")
    w, h = int(W * scale), int(H * scale)
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    fx, fy = shot.get("x", 0.5), shot.get("y", 0.5)
    left = int(min(max(fx * im.width - w / 2, 0), im.width - w))
    top = int(min(max(fy * im.height - h / 2, 0), im.height - h))
    im = im.crop((left, top, left + w, top + h))
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(1.12)
    return np.array(im)


def view(big, z):
    """Crop a W x H window at zoom z (1 = widest) from the oversized photo."""
    bh, bw = big.shape[:2]
    cw, ch = int(bw / z), int(bh / z)
    cw, ch = max(W, min(bw, cw)), max(H, min(bh, ch))
    x0, y0 = (bw - cw) // 2, (bh - ch) // 2
    return cv2.resize(big[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)


def motion_blur(img, length, horizontal=True):
    if length < 2:
        return img
    k = np.zeros((length, length), np.float32)
    if horizontal:
        k[length // 2, :] = 1
    else:
        k[:, length // 2] = 1
    return cv2.filter2D(img, -1, k / length)


def zoom_blur(img, amount):
    acc = img.astype(np.float32)
    n = 6
    for i in range(1, n):
        s = 1 + amount * i / n
        m = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s)
        acc += cv2.warpAffine(img, m, (W, H), borderMode=cv2.BORDER_REFLECT)
    return (acc / n).astype(np.uint8)


def perspective_y(img, angle, bg):
    """Rotate img around the vertical centre axis by angle (deg), pasted on bg."""
    a = math.radians(angle)
    c, s = math.cos(a), math.sin(a)
    if c <= 0.02:
        return bg
    f = 1800.0
    pts = []
    for x, y in ((-W / 2, -H / 2), (W / 2, -H / 2), (W / 2, H / 2), (-W / 2, H / 2)):
        X, Z = x * c, x * s
        k = f / (f + Z)
        pts.append((W / 2 + X * k, H / 2 + y * k))
    src = np.float32([(0, 0), (W, 0), (W, H), (0, H)])
    m = cv2.getPerspectiveTransform(src, np.float32(pts))
    warped = cv2.warpPerspective(img, m, (W, H))
    mask = cv2.warpPerspective(np.full((H, W), 255, np.uint8), m, (W, H))
    shade = 1 - 0.45 * abs(s)
    warped = (warped * shade).astype(np.uint8)
    out = bg.copy()
    out[mask > 0] = warped[mask > 0]
    return out


def affine(img, angle, scale, dx, dy):
    m = cv2.getRotationMatrix2D((W / 2, H / 2), angle, scale)
    m[0, 2] += dx
    m[1, 2] += dy
    warped = cv2.warpAffine(img, m, (W, H))
    mask = cv2.warpAffine(np.full((H, W), 255, np.uint8), m, (W, H))
    return warped, mask


def shadowed(top, mask, under, strength=0.5, offset=(24, 30), blur=41):
    sh = cv2.GaussianBlur(np.roll(np.roll(mask, offset[1], 0), offset[0], 1), (blur, blur), 0)
    out = (under * (1 - strength * sh[..., None] / 255.0)).astype(np.uint8)
    out[mask > 0] = top[mask > 0]
    return out


def card(img, border=34):
    """White-framed card version of a photo (for drop stacks)."""
    small = cv2.resize(img, (W - 2 * border - 120, H - 2 * border - 260))
    c = np.full((small.shape[0] + 2 * border, small.shape[1] + 2 * border + 0, 3), 250, np.uint8)
    c[border:border + small.shape[0], border:border + small.shape[1]] = small
    canvas = np.zeros((H, W, 3), np.uint8)
    y0, x0 = (H - c.shape[0]) // 2, (W - c.shape[1]) // 2
    canvas[y0:y0 + c.shape[0], x0:x0 + c.shape[1]] = c
    m = np.zeros((H, W), np.uint8)
    m[y0:y0 + c.shape[0], x0:x0 + c.shape[1]] = 255
    return canvas, m


def transition(kind, a, b, t, shot):
    """a, b: full frames (numpy). t in [0,1]."""
    d = shot.get("dir", "left")
    if kind == "whip":
        horiz = d in ("left", "right")
        forward = d in ("left", "up")  # content moves left/up: b comes from right/bottom
        span = W if horiz else H
        axis = 1 if horiz else 0
        both = np.concatenate([a, b] if forward else [b, a], axis=axis)
        u = ease(t)
        pos = int(span * u) if forward else int(span * (1 - u))
        frame = both[:, pos:pos + W] if horiz else both[pos:pos + H, :]
        blur = int(180 * math.sin(math.pi * t)) | 1
        return motion_blur(np.ascontiguousarray(frame), blur, horiz)
    if kind == "zoom":
        if t < 0.5:
            u = ease_in(t * 2)
            m = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + 1.6 * u)
            return zoom_blur(cv2.warpAffine(a, m, (W, H)), 0.25 * u)
        u = ease_out((t - 0.5) * 2)
        m = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1.6 - 0.6 * u)
        return zoom_blur(cv2.warpAffine(b, m, (W, H)), 0.25 * (1 - u))
    if kind == "flip":
        black = np.zeros_like(a)
        if t < 0.5:
            return perspective_y(a, 90 * ease_in(t * 2), black)
        return perspective_y(b, -90 + 90 * ease_out((t - 0.5) * 2), black)
    if kind == "page":
        u = ease(t)
        # previous page hinges on the left edge and turns away
        a_ = math.radians(180 * u)
        if math.cos(a_) <= 0.02:
            return b
        f = 1900.0
        pts = []
        for x, y in ((0, -H / 2), (W, -H / 2), (W, H / 2), (0, H / 2)):
            X, Z = x * math.cos(a_), -x * math.sin(a_)
            k = f / (f + Z)
            pts.append((X * k, H / 2 + y * k))
        src = np.float32([(0, 0), (W, 0), (W, H), (0, H)])
        mtx = cv2.getPerspectiveTransform(src, np.float32(pts))
        warped = cv2.warpPerspective((a * (1 - 0.35 * u)).astype(np.uint8), mtx, (W, H))
        mask = cv2.warpPerspective(np.full((H, W), 255, np.uint8), mtx, (W, H))
        return shadowed(warped, mask, b, 0.55 * (1 - u), (30, 0), 61)
    if kind == "swipe":
        u = ease_in(t)
        sign = -1 if d == "left" else 1
        top, mask = affine(a, sign * -22 * u, 1 - 0.08 * u, sign * 1.25 * W * u, 120 * u)
        under = (b * (0.8 + 0.2 * t)).astype(np.uint8)
        return shadowed(top, mask, under, 0.6)
    if kind == "spin":
        if t < 0.5:
            u = ease_in(t * 2)
            m = cv2.getRotationMatrix2D((W / 2, H / 2), -90 * u, 1 + 0.8 * u)
            return zoom_blur(cv2.warpAffine(a, m, (W, H), borderMode=cv2.BORDER_REFLECT), 0.3 * u)
        u = ease_out((t - 0.5) * 2)
        m = cv2.getRotationMatrix2D((W / 2, H / 2), 90 - 90 * u, 1.8 - 0.8 * u)
        return zoom_blur(cv2.warpAffine(b, m, (W, H), borderMode=cv2.BORDER_REFLECT), 0.3 * (1 - u))
    if kind == "drop":
        c, cm = card(b)
        u = ease_out(t)
        rot = shot.get("tilt", 4) * (1 - 0.3 * u)
        top, mask = affine(c, rot, 1.5 - 0.5 * u, 0, -260 * (1 - u))
        top_m, _ = affine(cm, rot, 1.5 - 0.5 * u, 0, -260 * (1 - u))
        mask = top_m
        under = (a * 0.75).astype(np.uint8)
        return shadowed(top, mask, under, 0.5)
    return b


def kinetic_text(frame, text, t):
    """Words pop in one by one with a spring, centred in the upper third."""
    if not text:
        return frame
    img = Image.fromarray(frame).convert("RGBA")
    d = ImageDraw.Draw(img)
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if d.textlength(test, font=F_TEXT) <= W - 160 or not cur:
            cur.append(w)
        else:
            lines.append(cur)
            cur = [w]
    lines.append(cur)
    layer = Image.new("RGBA", img.size)
    ld = ImageDraw.Draw(layer)
    k, y = 0, 380
    space = d.textlength(" ", font=F_TEXT)
    for line in lines:
        lw = sum(d.textlength(w, font=F_TEXT) for w in line) + space * (len(line) - 1)
        x = (W - lw) / 2
        for w in line:
            tw = d.textlength(w, font=F_TEXT)
            p = t - 0.12 - k * 0.09
            if p > 0:
                s = 1 + 0.35 * math.exp(-9 * p) * math.cos(20 * p)
                tmp = Image.new("RGBA", (int(tw) + 40, 120))
                ImageDraw.Draw(tmp).text((20, 10), w, font=F_TEXT, fill="white")
                tmp = tmp.resize((max(1, int(tmp.width * s)), max(1, int(tmp.height * s))), Image.BILINEAR)
                layer.alpha_composite(tmp, (int(x + tw / 2 - tmp.width / 2), int(y + 50 - tmp.height / 2)))
            x += tw + space
            k += 1
        y += 96
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(layer.split()[3].filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.75)))
    img = Image.alpha_composite(Image.alpha_composite(img, shadow), layer)
    return np.array(img.convert("RGB"))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    cfg = json.loads((src / "config.json").read_text(encoding="utf-8"))
    shots = cfg["shots"]
    bigs = [load(s) for s in shots]
    tmp, out = src / "tmp.mp4", src / "reel.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                           "-preset", "fast", "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    prev_last = None
    for i, (s, big) in enumerate(zip(shots, bigs)):
        n = int(s["dur"] * FPS)
        kind = s.get("in", "cut") if i else "cut"
        for f in range(n):
            p = f / max(1, n - 1)
            z = 1.0 + 0.10 * p  # slow push-in
            if kind == "cut" and f < 5:  # zoom punch on the cut
                z += 0.10 * (1 - f / 5)
            frame = view(big, z)
            frame = kinetic_text(frame, s.get("text"), f / FPS)
            if prev_last is not None and kind != "cut" and f < TR:
                frame = transition(kind, prev_last, frame, (f + 1) / (TR + 1), s)
            ff.stdin.write(np.ascontiguousarray(frame).tobytes())
            last = frame
        prev_last = last
        print(f"  shot {i + 1}/{len(shots)} ({kind})")
    ff.stdin.close()
    ff.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-fflags", "+genpts+igndts", "-i", str(tmp),
                    "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    tmp.unlink()
    print(f"  {out}")


if __name__ == "__main__":
    main()
