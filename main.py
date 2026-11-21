#!/usr/bin/env python3
"""BRUMALIA — travel poster for a place that isn't there.

Draws a 1024x1024 vintage 1930s railway poster: a glowing ice palace
under an aurora, a red steam train crossing the snow, and the place name
BRUMALIA set large at the top. The only text in the image is the name.
Writes /output/entry.png (PNG, <= 1 MiB).
"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_font(name, size):
    """Load a font bundled inside this repo first, then system fallbacks.

    The grader sandbox has no network and no home-directory paths, so the
    repo must carry its own fonts under fonts/ next to this file.
    """
    candidates = [
        os.path.join(BASE_DIR, "fonts", name),
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default(size)


NAME_FONT = "PlayfairDisplay-900.ttf"

# Palette: red-white-blue night
NAVY_TOP = (7, 16, 38)
NAVY_MID = (13, 32, 66)
NAVY_LOW = (24, 52, 96)
HORIZON = (58, 92, 140)
CREAM = (240, 230, 205)
SNOW = (238, 244, 250)
ICE = (178, 216, 240)
ICE_DEEP = (110, 168, 208)
AURORA1 = (110, 235, 165)
AURORA2 = (70, 200, 190)
AURORA3 = (150, 240, 200)
RED = (176, 32, 46)
RED_DARK = (122, 18, 30)
AMBER = (255, 196, 107)
GOLD = (212, 175, 105)

random.seed(1930)


def vgrad(size, stops):
    """Vertical gradient image from [(pos0-1, rgb), ...]."""
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                px[0, y] = tuple(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
                break
        else:
            px[0, y] = stops[-1][1]
    return img.resize((w, h))


def stars(draw, n=220, y_max=560):
    for _ in range(n):
        x = random.uniform(0, W)
        y = random.uniform(0, y_max)
        r = random.choice([1, 1, 1, 2, 2, 3])
        a = random.randint(120, 235)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))


def aurora(base):
    """Translucent green aurora ribbons across the upper sky."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for band, (col, amp, y0, alpha) in enumerate([
        (AURORA1, 70, 150, 110),
        (AURORA2, 95, 230, 90),
        (AURORA3, 55, 95, 70),
    ]):
        pts_top, pts_bot = [], []
        for x in range(-20, W + 21, 20):
            wave = (math.sin(x / 260.0 + band * 1.7) * amp
                    + math.sin(x / 110.0 + band) * amp * 0.35)
            pts_top.append((x, y0 + wave - 26))
            pts_bot.append((x, y0 + wave + 34))
        d.polygon(pts_top + pts_bot[::-1], fill=col + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(14))
    # soft glow under the ribbons
    glow = layer.filter(ImageFilter.GaussianBlur(40))
    base.alpha_composite(glow)
    base.alpha_composite(layer)


def mountains(draw):
    """Distant snow-capped ridge, higher contrast, behind the palace.

    Smooth ridge curve (long wavelengths only) and snow caps drawn as one
    continuous smooth band, so no zigzag sawtooth appears.
    """
    ridge = []
    for x in range(0, W + 21, 10):
        y = 560 + math.sin(x / 190.0) * 42 + math.sin(x / 140.0) * 10
        ridge.append((x, y))
    draw.polygon([(0, H)] + ridge + [(W, H)], fill=(26, 46, 86, 255))
    # snow caps: one smooth band hugging the ridge, deeper over the peaks
    cap_top = ridge
    cap_bot = []
    for x, y in ridge:
        depth = 26 + 14 * math.sin(x / 160.0 + 1.3)
        cap_bot.append((x, y + max(depth, 10)))
    draw.polygon(cap_top + cap_bot[::-1], fill=(214, 230, 244, 255))


def ice_palace(draw, glow_layer):
    """The landmark: a glowing ice palace of spires and domes, centre."""
    cx = W // 2
    base_y = 700
    # halo behind the palace
    gd = ImageDraw.Draw(glow_layer)
    gd.ellipse([cx - 260, base_y - 420, cx + 260, base_y + 60],
               fill=(140, 200, 240, 90))
    # main keep: tall central spire
    towers = [
        # (centre x, width, height, dome?)
        (cx - 190, 70, 200, False),
        (cx - 120, 90, 290, True),
        (cx - 40, 80, 240, False),
        (cx, 110, 380, True),      # great spire
        (cx + 45, 80, 250, False),
        (cx + 125, 90, 300, True),
        (cx + 195, 70, 195, False),
    ]
    # connecting base wall
    draw.polygon([(cx - 250, base_y), (cx - 250, base_y - 120),
                  (cx + 250, base_y - 120), (cx + 250, base_y)],
                 fill=ICE_DEEP)
    for tx, tw, th, dome in towers:
        top = base_y - th
        # body
        draw.polygon([(tx - tw // 2, base_y), (tx - tw // 2, top + 60),
                      (tx, top), (tx + tw // 2, top + 60),
                      (tx + tw // 2, base_y)], fill=ICE)
        # shaded right face
        draw.polygon([(tx, top), (tx + tw // 2, top + 60),
                      (tx + tw // 2, base_y), (tx, base_y)], fill=ICE_DEEP)
        # lit left edge
        draw.line([(tx - tw // 2, base_y), (tx - tw // 2, top + 60),
                   (tx, top)], fill=(235, 248, 255), width=3)
        if dome:
            # true half-dome: upper half of an ellipse rising from the spire
            # top, tall enough to read as a curved dome, not a flat plate
            dome_h = int(tw * 0.55)
            draw.pieslice([tx - tw // 2 - 6, top - dome_h,
                           tx + tw // 2 + 6, top + dome_h],
                          180, 360, fill=(226, 242, 252))
            draw.arc([tx - tw // 2 - 6, top - dome_h,
                      tx + tw // 2 + 6, top + dome_h],
                     180, 360, fill=(150, 200, 232), width=2)
            draw.line([(tx - tw // 2 - 6, top), (tx + tw // 2 + 6, top)],
                      fill=(150, 200, 232), width=2)
            # finial rising from the dome crown
            draw.line([(tx, top - dome_h), (tx, top - dome_h - 26)],
                      fill=GOLD, width=4)
            draw.ellipse([tx - 5, top - dome_h - 32, tx + 5, top - dome_h - 22],
                         fill=AMBER)
        else:
            # finial on the bare spire tip
            draw.line([(tx, top), (tx, top - 26)], fill=GOLD, width=4)
            draw.ellipse([tx - 5, top - 32, tx + 5, top - 22], fill=AMBER)
    # glowing windows: warm amber slits in the ice
    for wx in range(cx - 220, cx + 221, 34):
        for wy in (base_y - 88, base_y - 52):
            if random.random() < 0.75:
                draw.rectangle([wx, wy, wx + 12, wy + 22], fill=AMBER)
    # great arched gate, warm light spilling out
    draw.polygon([(cx - 34, base_y), (cx - 34, base_y - 78),
                  (cx, base_y - 102), (cx + 34, base_y - 78),
                  (cx + 34, base_y)], fill=(255, 214, 130))
    draw.polygon([(cx - 34, base_y), (cx - 34, base_y - 78),
                  (cx, base_y - 102), (cx + 34, base_y - 78),
                  (cx + 34, base_y)], outline=(160, 110, 40), width=3)


def pines(draw, y_base, color, scale=1.0, count=14):
    for _ in range(count):
        x = random.uniform(0, W)
        hgt = random.uniform(55, 110) * scale
        wdt = hgt * 0.42
        y = y_base + random.uniform(-6, 10)
        draw.polygon([(x, y - hgt), (x - wdt, y), (x + wdt, y)], fill=color)
        draw.polygon([(x, y - hgt * 0.72), (x - wdt * 0.75, y - hgt * 0.28),
                      (x + wdt * 0.75, y - hgt * 0.28)], fill=color)
        draw.rectangle([x - 3, y, x + 3, y + 12], fill=color)


def train(draw):
    """1930s red steam locomotive crossing the lower third, left to right."""
    y_track = 872
    # track bed + rails
    draw.rectangle([0, y_track, W, y_track + 10], fill=(30, 34, 44))
    draw.rectangle([0, y_track + 2, W, y_track + 5], fill=(200, 205, 215))
    draw.rectangle([0, y_track + 12, W, y_track + 15], fill=(200, 205, 215))
    for x in range(0, W, 46):
        draw.rectangle([x, y_track - 2, x + 14, y_track + 18], fill=(52, 44, 38))
    # tender + locomotive (side profile, facing right)
    x0, y0 = 150, y_track - 8          # tender left edge, wheel line
    # tender
    draw.rectangle([x0, y0 - 92, x0 + 150, y0], fill=RED_DARK)
    draw.rectangle([x0, y0 - 92, x0 + 150, y0 - 78], fill=CREAM)
    draw.rectangle([x0 + 12, y0 - 70, x0 + 138, y0 - 14], fill=(60, 20, 26))
    # cab
    draw.rectangle([x0 + 150, y0 - 148, x0 + 250, y0], fill=RED)
    draw.rectangle([x0 + 150, y0 - 148, x0 + 250, y0 - 132], fill=CREAM)
    draw.rectangle([x0 + 168, y0 - 122, x0 + 202, y0 - 84], fill=AMBER)  # cab window
    draw.rectangle([x0 + 168, y0 - 122, x0 + 202, y0 - 84], outline=(90, 40, 20), width=3)
    # boiler
    draw.rectangle([x0 + 250, y0 - 118, x0 + 470, y0 - 6], fill=RED)
    draw.ellipse([x0 + 448, y0 - 118, x0 + 500, y0 - 6], fill=RED)
    draw.rectangle([x0 + 250, y0 - 118, x0 + 470, y0 - 104], fill=CREAM)
    # chimney
    draw.rectangle([x0 + 440, y0 - 168, x0 + 462, y0 - 112], fill=(28, 28, 34))
    draw.rectangle([x0 + 432, y0 - 176, x0 + 470, y0 - 164], fill=(28, 28, 34))
    # dome + headlamp — dome seated ON the boiler, not floating above it
    draw.ellipse([x0 + 330, y0 - 134, x0 + 368, y0 - 100], fill=GOLD)
    draw.ellipse([x0 + 486, y0 - 96, x0 + 508, y0 - 74], fill=AMBER)
    draw.ellipse([x0 + 486, y0 - 96, x0 + 508, y0 - 74], outline=(90, 40, 20), width=3)
    # headlamp beam — narrow, dim cone (was a wide yellow fog)
    beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(x0 + 500, y0 - 86), (W, y0 - 102), (W, y0 - 70)],
               fill=(255, 220, 140, 28))
    beam = beam.filter(ImageFilter.GaussianBlur(4))
    # wheels
    for wx, wr in [(x0 + 40, 26), (x0 + 110, 26), (x0 + 200, 30),
                   (x0 + 300, 34), (x0 + 380, 34), (x0 + 450, 30)]:
        draw.ellipse([wx - wr, y0 - wr, wx + wr, y0 + wr], fill=(24, 24, 30))
        draw.ellipse([wx - wr + 8, y0 - wr + 8, wx + wr - 8, y0 + wr - 8],
                     outline=(150, 150, 160), width=3)
        draw.ellipse([wx - 6, y0 - 6, wx + 6, y0 + 6], fill=(150, 150, 160))
    # connecting rod
    draw.line([(x0 + 200, y0), (x0 + 450, y0)], fill=(180, 180, 190), width=6)
    return beam


def smoke(base):
    """Small, layered, translucent steam wisps from the chimney.

    Puffs are ~40% smaller and far more transparent than before, so the
    palace and mountains stay visible behind them.
    """
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = 598, 690
    for i, (dx, dy, r, a) in enumerate([
        (0, 0, 16, 150), (16, -26, 20, 125), (36, -50, 24, 100),
        (62, -70, 28, 78), (92, -86, 30, 58), (126, -96, 32, 40),
    ]):
        d.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r],
                  fill=(245, 248, 252, a))
    layer = layer.filter(ImageFilter.GaussianBlur(8))
    base.alpha_composite(layer)


def snowfall(draw, n=260):
    for _ in range(n):
        x = random.uniform(0, W)
        y = random.uniform(430, H)
        r = random.choice([1, 1, 2, 2, 3])
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, random.randint(150, 235)))


def grain(base):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = layer.load()
    for _ in range(26000):
        x = random.randint(0, W - 1)
        y = random.randint(0, H - 1)
        v = random.randint(0, 255)
        px[x, y] = (v, v, v, 14)
    base.alpha_composite(layer)


def name_block(draw):
    """BRUMALIA — the only text. Large Playfair 900, cream on navy."""
    font = load_font(NAME_FONT, 148)
    name = "BRUMALIA"
    bbox = draw.textbbox((0, 0), name, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2 - bbox[0]
    y = 78
    # soft shadow for legibility
    draw.text((x + 5, y + 6), name, font=font, fill=(4, 10, 26, 255))
    draw.text((x, y), name, font=font, fill=CREAM + (255,))
    # deco rule + diamond under the name
    cy = y + 178
    draw.line([(W // 2 - 210, cy), (W // 2 - 26, cy)], fill=GOLD, width=3)
    draw.line([(W // 2 + 26, cy), (W // 2 + 210, cy)], fill=GOLD, width=3)
    draw.polygon([(W // 2, cy - 11), (W // 2 + 11, cy),
                  (W // 2, cy + 11), (W // 2 - 11, cy)], fill=GOLD)


def frame(draw):
    draw.rectangle([26, 26, W - 27, H - 27], outline=CREAM, width=4)
    draw.rectangle([40, 40, W - 41, H - 41], outline=GOLD, width=2)


def main():
    img = vgrad((W, H), [
        (0.0, NAVY_TOP), (0.45, NAVY_MID), (0.62, NAVY_LOW), (0.72, HORIZON),
        (1.0, (30, 44, 78)),
    ]).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    stars(d)
    aurora(img)
    d = ImageDraw.Draw(img, "RGBA")
    mountains(d)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ice_palace(d, glow)
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img, "RGBA")
    # snowfield from the palace base down
    d.polygon([(0, 700), (W, 700), (W, H), (0, H)], fill=SNOW + (255,))
    # soft shadow under palace + track line
    d.polygon([(W // 2 - 280, 700), (W // 2 + 280, 700),
               (W // 2 + 340, 760), (W // 2 - 340, 760)], fill=(200, 216, 232, 255))
    pines(d, 742, (16, 40, 66), scale=0.9, count=9)
    pines(d, 1010, (12, 30, 54), scale=1.15, count=12)
    beam = train(d)
    img.alpha_composite(beam)
    smoke(img)
    d = ImageDraw.Draw(img, "RGBA")
    snowfall(d)
    name_block(d)
    frame(d)
    grain(img)

    os.makedirs("/output", exist_ok=True)
    out = img.convert("RGB")
    out.save("/output/entry.png", optimize=True)
    size = os.path.getsize("/output/entry.png")
    print(f"entry.png: {out.size} {size} bytes")
    if size > 1048576:
        out.save("/output/entry.png", "JPEG", quality=92, optimize=True)
        print(f"re-saved as JPEG: {os.path.getsize('/output/entry.png')} bytes")


if __name__ == "__main__":
    main()
