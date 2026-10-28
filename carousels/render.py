#!/usr/bin/env python3
"""Instagram Carousel Renderer. Usage: python3 render.py <carousel-dir>"""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SLIDE_WIDTH, SLIDE_HEIGHT = 1080, 1350
ASSETS_DIR = Path(__file__).parent / "assets"
FONT_DIR = ASSETS_DIR / "fonts"
HEADSHOT_PATH = ASSETS_DIR / "headshot.jpg"
DEJAVU = Path("/usr/share/fonts/truetype/dejavu")

COLORS = {
    "bg_dark": "#0D1B2A", "bg_card": "#152238", "accent": "#5DCCFF", "accent_dark": "#0871B8",
    "accent_secondary": "#E91E63", "white": "#FFFFFF", "off_white": "#F0F0F0", "cream": "#D4D4D4",
    "gray": "#94A3B8", "light_gray": "#CBD5E1", "blue": "#1976D2", "red": "#E91E63", "grid_line": "#1A2D42",
}
PADDING = 80
CONTENT_WIDTH = SLIDE_WIDTH - PADDING * 2
FOOTER_HEIGHT = 80

# -- Fonts --------------------------------------------------------------------

def _font(candidates, size, variation=None):
    for p in candidates:
        p = Path(p)
        if p.exists():
            f = ImageFont.truetype(str(p), size)
            if variation:
                try:
                    f.set_variation_by_name(variation)
                except Exception:
                    pass
            return f
    return ImageFont.load_default(size)

def load_fonts():
    head = [FONT_DIR / "Oswald.ttf", FONT_DIR / "BebasNeue-Regular.ttf", DEJAVU / "DejaVuSansCondensed-Bold.ttf", DEJAVU / "DejaVuSans-Bold.ttf"]
    body = [FONT_DIR / "Inter.ttf", DEJAVU / "DejaVuSans-Bold.ttf"]
    body_reg = [FONT_DIR / "Inter.ttf", DEJAVU / "DejaVuSans.ttf"]
    hand = [FONT_DIR / "Caveat.ttf", DEJAVU / "DejaVuSans-Oblique.ttf", DEJAVU / "DejaVuSerif-Bold.ttf"]
    H = lambda s: _font(head, s, "Bold")
    return {
        "headline_xl": H(132), "headline_lg": H(100), "headline_md": H(68), "headline_sm": H(54), "headline_italic": H(84),
        "body_lg": _font(body, 48, "Bold"), "body": _font(body, 44, "Bold"), "body_sm": _font(body, 34, "SemiBold"),
        "body_bold": _font(body, 44, "Bold"), "caption": _font(body, 30, "Bold"), "handle": _font(body_reg, 28, "Regular"),
        "display_name": _font(body, 36, "SemiBold"),
        "hand_lg": _font(hand, 58, "Bold"), "hand_md": _font(hand, 48, "Bold"), "hand_sm": _font(hand, 40, "Bold"),
    }

# -- Helpers ------------------------------------------------------------------

def hex_to_rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def create_circular_image(image, size):
    big = size * 2
    w, h = image.size; s = min(w, h)
    image = image.crop(((w - s)//2, (h - s)//2, (w + s)//2, (h + s)//2)).resize((big, big), Image.LANCZOS)
    mask = Image.new("L", (big, big), 0); ImageDraw.Draw(mask).ellipse((0, 0, big, big), fill=255)
    out = Image.new("RGBA", (big, big), (0, 0, 0, 0)); out.paste(image, (0, 0), mask)
    return out.resize((size, size), Image.LANCZOS)

def draw_grid_texture(img, color, spacing=40, alpha=18):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(overlay); r, g, b = hex_to_rgb(color)
    for x in range(0, SLIDE_WIDTH, spacing): d.line([(x, 0), (x, SLIDE_HEIGHT)], fill=(r, g, b, alpha))
    for y in range(0, SLIDE_HEIGHT, spacing): d.line([(0, y), (SLIDE_WIDTH, y)], fill=(r, g, b, alpha))
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"), (0, 0))

def draw_gradient_bar(img, y, height, cl, cr):
    l, r = hex_to_rgb(cl), hex_to_rgb(cr); px = img.load()
    for x in range(SLIDE_WIDTH):
        t = x / SLIDE_WIDTH; c = tuple(int(l[i] + (r[i] - l[i]) * t) for i in range(3))
        for dy in range(height): px[x, y + dy] = c

def draw_curved_arrow(draw, start, end, color, width=3):
    sx, sy = start; ex, ey = end
    cx = (sx + ex)//2 + (ey - sy)//3; cy = (sy + ey)//2 - (ex - sx)//3
    pts = [((1-t)**2*sx + 2*(1-t)*t*cx + t**2*ex, (1-t)**2*sy + 2*(1-t)*t*cy + t**2*ey) for t in [i/20 for i in range(21)]]
    for i in range(len(pts) - 1): draw.line([pts[i], pts[i+1]], fill=hex_to_rgb(color), width=width)
    ang = math.atan2(ey - pts[-2][1], ex - pts[-2][0])
    for off in (-0.5, 0.5):
        a = ang + math.pi + off
        draw.line([(ex, ey), (ex + 18*math.cos(a), ey + 18*math.sin(a))], fill=hex_to_rgb(color), width=width)

def wrap_text(text, font, max_width, draw):
    lines, cur = [], []
    for w in text.split():
        test = " ".join(cur + [w]); bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_width: cur.append(w)
        else:
            if cur: lines.append(" ".join(cur))
            cur = [w]
    if cur: lines.append(" ".join(cur))
    return lines

def get_line_height(font, draw, spacing=1.4):
    bb = draw.textbbox((0, 0), "ÁgЙ", font=font); return int((bb[3] - bb[1]) * spacing)

def get_text_height(text, font, max_width, draw, ls=1.4):
    lines = wrap_text(text, font, max_width, draw)
    return get_line_height(font, draw, ls) * len(lines) if lines else 0

def draw_rich_text(draw, text, xy, font, default_color, accent_color, max_width, line_spacing=1.25, align="left", accent_font=None):
    x, y = xy; accent_font = accent_font or font
    words = []
    for i, part in enumerate(text.split("*")):
        for w in part.split():
            acc = i % 2 == 1
            words.append((w, accent_color if acc else default_color, accent_font if acc else font))
    lines, cur = [], []
    for item in words:
        test = " ".join([w for w, _, _ in cur] + [item[0]]); bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_width: cur.append(item)
        else:
            if cur: lines.append(cur)
            cur = [item]
    if cur: lines.append(cur)
    lh = get_line_height(font, draw, line_spacing)
    for line in lines:
        full = " ".join(w for w, _, _ in line)
        dx = x + (max_width - (draw.textbbox((0, 0), full, font=font)[2]))//2 if align == "center" else x
        for w, c, f in line:
            draw.text((dx, y), w, font=f, fill=hex_to_rgb(c))
            dx += draw.textbbox((0, 0), w + " ", font=f)[2]
        y += lh
    return y

def draw_wrapped_text(draw, text, xy, font, fill, max_width, line_spacing=1.4, align="left"):
    x, y = xy; lh = get_line_height(font, draw, line_spacing)
    for line in wrap_text(text, font, max_width, draw):
        dx = x + (max_width - draw.textbbox((0, 0), line, font=font)[2])//2 if align == "center" else x
        draw.text((dx, y), line, font=font, fill=fill); y += lh
    return y

def load_and_fit_image(path, max_w, max_h, radius=16):
    img = Image.open(path).convert("RGBA"); r = min(max_w / img.width, max_h / img.height)
    img = img.resize((int(img.width*r), int(img.height*r)), Image.LANCZOS)
    mask = Image.new("L", img.size, 0); ImageDraw.Draw(mask).rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0)); out.paste(img, (0, 0), mask); return out

def resolve_image_path(name, carousel_dir):
    return ASSETS_DIR / name[6:] if name.startswith("asset:") else carousel_dir / "reference" / name

def draw_editorial_footer(img, draw, config, fonts):
    row_c = SLIDE_HEIGHT - 70 + 14; f = fonts["caption"]; col = hex_to_rgb(COLORS["off_white"])
    handle = config["profile"]["handle"]; bb = draw.textbbox((0, 0), handle, font=f)
    draw.text((PADDING, row_c - (bb[3]-bb[1])//2 - bb[1]), handle, font=f, fill=col)
    save = config.get("save_text", "сохрани себе"); sb = draw.textbbox((0, 0), save, font=f)
    sx = SLIDE_WIDTH - PADDING - (sb[2] - sb[0]); bw, bh = 16, 22; bx = sx - bw - 10; by = row_c - bh//2
    draw.polygon([(bx, by), (bx+bw, by), (bx+bw, by+bh), (bx+bw//2, by+bh-7), (bx, by+bh)], outline=col, width=2)
    draw.text((sx, row_c - (sb[3]-sb[1])//2 - sb[1]), save, font=f, fill=col)

def create_dark_slide():
    img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT), hex_to_rgb(COLORS["bg_dark"]))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([SLIDE_WIDTH//2-600, SLIDE_HEIGHT//2-700, SLIDE_WIDTH//2+600, SLIDE_HEIGHT//2+700], fill=(20, 55, 100, 30))
    img = Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(200))).convert("RGB")
    draw_grid_texture(img, COLORS["grid_line"]); return img

# -- Slides -------------------------------------------------------------------

def render_hook_slide(config, slide, fonts, carousel_dir):
    img = create_dark_slide(); draw = ImageDraw.Draw(img)
    draw_gradient_bar(img, 0, 6, COLORS["blue"], COLORS["red"])
    if slide.get("image"):
        p = resolve_image_path(slide["image"], carousel_dir)
        if p.exists():
            h = Image.open(str(p)).convert("RGBA"); r = SLIDE_WIDTH / h.width
            h = h.resize((SLIDE_WIDTH, int(h.height*r)), Image.LANCZOS)
            crop_h = min(h.height, int(SLIDE_HEIGHT*0.62)); h = h.crop((0, 0, SLIDE_WIDTH, crop_h))
            bg = img.getpixel((SLIDE_WIDTH//2, crop_h))[:3]
            col = Image.new("L", (1, crop_h))
            for yy in range(crop_h):
                prog = yy / crop_h
                col.putpixel((0, yy), 0 if prog < 0.65 else int(min(255, ((prog-0.65)/0.35)**3 * 800)))
            grad = Image.new("RGBA", h.size, bg + (0,)); grad.putalpha(col.resize(h.size))
            img.paste(Image.alpha_composite(h, grad).convert("RGB"), (0, 0)); draw = ImageDraw.Draw(img)
    text = slide["text"].upper(); f = fonts["headline_xl"]
    th = get_text_height(text.replace("*", ""), f, CONTENT_WIDTH, draw, 1.1)
    extra = 0
    if slide.get("subtitle"): extra += get_text_height(slide["subtitle"], fonts["body_lg"], CONTENT_WIDTH, draw, 1.3) + 20
    if slide.get("annotation"): extra += 80
    y = max(int(SLIDE_HEIGHT*0.45), SLIDE_HEIGHT - FOOTER_HEIGHT - th - extra - 60)
    y = draw_rich_text(draw, text, (PADDING, y), f, COLORS["white"], COLORS["accent"], CONTENT_WIDTH, line_spacing=1.1)
    if slide.get("subtitle"):
        y = draw_wrapped_text(draw, slide["subtitle"], (PADDING, y + 20), fonts["body_lg"], hex_to_rgb(COLORS["gray"]), CONTENT_WIDTH, 1.3)
    if slide.get("annotation"):
        af = fonts["hand_lg"]; ay = y + 16
        draw.text((PADDING, ay), slide["annotation"], font=af, fill=hex_to_rgb(COLORS["accent"]))
        aw = draw.textbbox((0, 0), slide["annotation"], font=af)[2]
        draw_curved_arrow(draw, (PADDING+aw+20, ay+25), (PADDING+aw+110, ay+20), COLORS["accent"])
    draw_editorial_footer(img, draw, config, fonts); return img

def render_body_slide(config, slide, fonts, carousel_dir):
    img = create_dark_slide(); draw = ImageDraw.Draw(img)
    draw_gradient_bar(img, 0, 6, COLORS["blue"], COLORS["red"])
    top, bottom = PADDING, SLIDE_HEIGHT - FOOTER_HEIGHT - 40; usable = bottom - top
    ipath = resolve_image_path(slide["image"], carousel_dir) if slide.get("image") else None
    has_image = bool(ipath and ipath.exists())
    sparse = sum([bool(slide.get("title")), bool(slide.get("text")), has_image, bool(slide.get("bullets"))]) <= 2 and not has_image
    tf = fonts["headline_xl"] if sparse else fonts["headline_lg"]
    xf = fonts["headline_sm"] if sparse else fonts["body"]
    bf = fonts["body_lg"] if sparse else fonts["body"]
    fixed = 0
    if slide.get("title"): fixed += get_text_height(slide["title"].upper().replace("*", "") + ".", tf, CONTENT_WIDTH, draw, 1.1) + 40
    if slide.get("text"): fixed += get_text_height(slide["text"].replace("*", ""), xf, CONTENT_WIDTH, draw, 1.5) + 28
    if slide.get("annotation"): fixed += 70
    if slide.get("bullets"):
        fixed += sum(get_text_height(b.replace("*", ""), bf, CONTENT_WIDTH-44, draw, 1.35) for b in slide["bullets"]) + 28*(len(slide["bullets"])-1) + 12
    body_img, is_logo = None, False
    if has_image:
        src = Image.open(str(ipath)); asp = src.width / max(1, src.height); src.close()
        is_logo = 0.5 < asp < 2.0 and bool(slide.get("bullets"))
        max_h = 150 if is_logo else max(300, min(900, usable - fixed - 60))
        body_img = load_and_fit_image(str(ipath), CONTENT_WIDTH, max_h, radius=12)
    total = fixed + (body_img.height if body_img else 0)
    y = top + max(0, (usable - total)//2)
    y = max(top, min(y, int(SLIDE_HEIGHT*(0.35 if sparse else 0.20))))
    gap = 20 + max(0, min(40, (usable - total)//3))
    if slide.get("title"):
        t = slide["title"].upper()
        if "*" not in t:
            if not t.endswith("."): t += "."
            parts = t.rsplit(" ", 1); t = parts[0] + " *" + parts[1] + "*" if len(parts) == 2 else t
        y = draw_rich_text(draw, t, (PADDING, y), tf, COLORS["white"], COLORS["accent"], CONTENT_WIDTH, 1.1)
        draw.rounded_rectangle([(PADDING, y+8), (PADDING+80, y+14)], radius=3, fill=hex_to_rgb(COLORS["accent"])); y += 32 + gap//2
    if slide.get("text"):
        y = draw_rich_text(draw, slide["text"], (PADDING, y), xf, COLORS["white"] if sparse else COLORS["off_white"], COLORS["accent"], CONTENT_WIDTH, 1.4 if sparse else 1.5) + gap
    if body_img:
        x = PADDING + (CONTENT_WIDTH - body_img.width)//2
        if not is_logo:
            sh = Image.new("RGBA", (body_img.width+20, body_img.height+20), (0, 0, 0, 0))
            sh.paste(Image.new("RGBA", body_img.size, (0, 0, 0, 60)), (10, 10)); sh = sh.filter(ImageFilter.GaussianBlur(8))
            base = img.convert("RGBA"); base.alpha_composite(sh, (x, y)); img = base.convert("RGB")
        img.paste(body_img, (x, y), body_img); draw = ImageDraw.Draw(img); y += body_img.height + gap
    if slide.get("annotation"):
        af = fonts["hand_md"]; draw.text((PADDING+20, y), slide["annotation"], font=af, fill=hex_to_rgb(COLORS["accent"]))
        aw = draw.textbbox((0, 0), slide["annotation"], font=af)[2]
        draw_curved_arrow(draw, (PADDING+20+aw+10, y+20), (PADDING+20+aw+60, y+55), COLORS["accent"]); y += 60
    if slide.get("bullets"):
        bl = slide["bullets"]
        hs = [get_text_height(b.replace("*", ""), bf, CONTENT_WIDTH-44, draw, 1.35) for b in bl]
        g = max(24, min((bottom - y - 20 - sum(hs))//max(1, len(bl)), 100)); by = y + 12
        for b in bl:
            draw.ellipse([(PADDING, by+14), (PADDING+14, by+28)], fill=hex_to_rgb(COLORS["accent"]))
            by = draw_rich_text(draw, b, (PADDING+44, by), bf, COLORS["off_white"], COLORS["accent"], CONTENT_WIDTH-44, 1.35) + g
    draw_editorial_footer(img, draw, config, fonts); return img

def render_cta_slide(config, slide, fonts, carousel_dir):
    img = create_dark_slide(); draw = ImageDraw.Draw(img)
    draw_gradient_bar(img, 0, 8, COLORS["blue"], COLORS["red"])
    cx = SLIDE_WIDTH//2; hs = 240; rs = hs + 20
    hs_y = PADDING + 8 + (SLIDE_HEIGHT - 70 - PADDING - 8 - 740)//2
    ring = Image.new("RGBA", (rs, rs), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
    rd.ellipse([(0, 0), (rs, rs)], fill=hex_to_rgb(COLORS["accent"]) + (40,)); rd.ellipse([(8, 8), (rs-8, rs-8)], fill=(0, 0, 0, 0))
    img.paste(ring, (cx - rs//2, hs_y - 8), ring)
    name = config["profile"]["display_name"]
    if HEADSHOT_PATH.exists():
        circ = create_circular_image(Image.open(HEADSHOT_PATH).convert("RGBA"), hs); img.paste(circ, (cx - hs//2, hs_y), circ)
    else:
        draw = ImageDraw.Draw(img); draw.ellipse([(cx-hs//2, hs_y), (cx+hs//2, hs_y+hs)], fill=hex_to_rgb(COLORS["accent_dark"]))
        initials = "".join(p[0] for p in name.split()[:2]).upper()
        draw.text((cx, hs_y + hs//2), initials, font=fonts["headline_lg"], fill=hex_to_rgb(COLORS["white"]), anchor="mm")
    draw = ImageDraw.Draw(img)
    ny = hs_y + hs + 40
    draw.text((cx, ny), name, font=fonts["headline_md"], fill=hex_to_rgb(COLORS["white"]), anchor="mt")
    hy = ny + 80; draw.text((cx, hy), config["profile"]["handle"], font=fonts["body_sm"], fill=hex_to_rgb(COLORS["gray"]), anchor="mt")
    dy = hy + 64; draw.rounded_rectangle([(cx-60, dy), (cx+60, dy+3)], radius=2, fill=hex_to_rgb(COLORS["accent"]))
    ct = slide.get("text", "Подписывайся, чтобы не пропустить"); cf = fonts["body_lg"]; cy = dy + 52
    draw_wrapped_text(draw, ct, (PADDING+20, cy), cf, hex_to_rgb(COLORS["off_white"]), CONTENT_WIDTH-40, 1.4, "center")
    if slide.get("button_text"):
        bt = slide["button_text"]; bfnt = fonts["body"]; bb = draw.textbbox((0, 0), bt, font=bfnt)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]; bw, bh = tw + 80, th + 48; bx = cx - bw//2
        by = cy + get_text_height(ct, cf, CONTENT_WIDTH-40, draw, 1.4) + 56
        draw.rounded_rectangle([(bx, by), (bx+bw, by+bh)], radius=bh//2, fill=hex_to_rgb(COLORS["accent_secondary"]))
        draw.text((bx + (bw-tw)//2, by + (bh-th)//2 - bb[1]), bt, font=bfnt, fill=hex_to_rgb(COLORS["white"]))
        draw_curved_arrow(draw, (cx, by+bh+20), (cx, by+bh+70), COLORS["accent_secondary"])
    draw_gradient_bar(img, SLIDE_HEIGHT-8, 8, COLORS["blue"], COLORS["red"])
    draw_editorial_footer(img, draw, config, fonts); return img

# -- Main ---------------------------------------------------------------------

def render_carousel(carousel_dir):
    carousel_dir = Path(carousel_dir); cfg = json.loads((carousel_dir / "config.json").read_text())
    COLORS.update(cfg.get("colors", {}))
    fonts = load_fonts(); (carousel_dir / "reference").mkdir(exist_ok=True)
    for i, s in enumerate(cfg["slides"]):
        t = s.get("type", "body")
        r = {"hook": render_hook_slide, "cta": render_cta_slide}.get(t, render_body_slide)(cfg, s, fonts, carousel_dir)
        out = carousel_dir / f"slide_{i+1}.png"; r.save(str(out), "PNG"); print(f"  {out.name} ({t})")
    print(f"Done: {len(cfg['slides'])} slides")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit("Usage: python3 render.py <carousel-dir>")
    render_carousel(sys.argv[1])
