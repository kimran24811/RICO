
import numpy as np
from PIL import Image, ImageDraw
import math


def make_gradient(w, h, top_color, bottom_color):
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for i in range(h):
        t = i / max(h - 1, 1)
        for c in range(3):
            arr[i, :, c] = int(top_color[c] * (1 - t) + bottom_color[c] * t)
    return Image.fromarray(arr, "RGB")


def draw_dojo(w, h):
    img = make_gradient(w, h, (40, 20, 10), (80, 45, 20))
    draw = ImageDraw.Draw(img)
    # Floor
    floor_y = int(h * 0.78)
    draw.rectangle([0, floor_y, w, h], fill=(55, 32, 12))
    draw.line([(0, floor_y), (w, floor_y)], fill=(90, 60, 25), width=3)
    # Wood planks
    for i in range(0, w, 60):
        draw.line([(i, floor_y), (i, h)], fill=(65, 38, 14), width=1)
    # Lanterns
    for lx in [80, w - 80]:
        draw.ellipse([lx-10, 30, lx+10, 60], fill=(255, 160, 40), outline=(180, 90, 10), width=2)
        draw.line([(lx, 0), (lx, 30)], fill=(120, 70, 20), width=2)
    # Banner
    draw.rectangle([w//2-30, 10, w//2+30, 80], fill=(140, 20, 20), outline=(200, 150, 50), width=2)
    return img


def draw_city_night(w, h):
    img = make_gradient(w, h, (5, 8, 30), (15, 20, 60))
    draw = ImageDraw.Draw(img)
    # Stars
    import random
    rng = random.Random(42)
    for _ in range(80):
        sx = rng.randint(0, w)
        sy = rng.randint(0, int(h * 0.6))
        r = rng.randint(1, 2)
        draw.ellipse([sx-r, sy-r, sx+r, sy+r], fill=(255, 255, 255, rng.randint(100, 220)))
    # Moon
    draw.ellipse([w-90, 20, w-40, 70], fill=(230, 230, 180), outline=(200, 200, 150), width=2)
    # Buildings silhouette
    floor_y = int(h * 0.78)
    buildings = [(0,180,100),(120,120,160),(240,160,140),(380,100,180),
                 (500,140,120),(600,80,160)]
    for bx, bh, bw in buildings:
        by = floor_y - bh
        draw.rectangle([bx, by, bx+bw, floor_y], fill=(12, 14, 35))
        # Windows
        for wy in range(by+10, floor_y-10, 20):
            for wx2 in range(bx+10, bx+bw-10, 18):
                if (wx2 + wy) % 3 != 0:
                    draw.rectangle([wx2, wy, wx2+8, wy+10], fill=(255, 230, 100, 180))
    # Floor
    draw.rectangle([0, floor_y, w, h], fill=(10, 12, 30))
    draw.line([(0, floor_y), (w, floor_y)], fill=(30, 40, 80), width=2)
    return img


def draw_arena(w, h):
    img = make_gradient(w, h, (80, 5, 5), (140, 20, 20))
    draw = ImageDraw.Draw(img)
    floor_y = int(h * 0.78)
    # Crowd dots
    import random
    rng = random.Random(7)
    for _ in range(120):
        cx2 = rng.randint(0, w)
        cy2 = rng.randint(0, floor_y - 60)
        r = rng.randint(3, 7)
        col = rng.choice([(200,200,200),(255,100,0),(100,200,255),(255,50,50)])
        draw.ellipse([cx2-r, cy2-r, cx2+r, cy2+r], fill=col)
    # Ring ropes
    for rope_y in [floor_y - 60, floor_y - 40, floor_y - 20]:
        draw.line([(0, rope_y), (w, rope_y)], fill=(220, 220, 220), width=3)
    # Floor
    draw.rectangle([0, floor_y, w, h], fill=(60, 20, 10))
    draw.line([(0, floor_y), (w, floor_y)], fill=(100, 60, 30), width=3)
    # Spotlight
    cx_s = w // 2
    for radius in [200, 160, 120]:
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay, "RGBA")
        od.ellipse([cx_s-radius, floor_y-radius, cx_s+radius, floor_y+20],
                   fill=(255, 240, 180, 15))
        img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))
    return img


def draw_forest(w, h):
    img = make_gradient(w, h, (10, 35, 15), (30, 70, 30))
    draw = ImageDraw.Draw(img)
    floor_y = int(h * 0.78)
    # Trees background
    import random
    rng = random.Random(99)
    for tx in range(0, w + 60, 60):
        th = rng.randint(80, 180)
        tw = rng.randint(28, 48)
        ty = floor_y - th
        draw.rectangle([tx - tw//2, ty, tx + tw//2, floor_y], fill=(20, 50, 15))
        draw.ellipse([tx - tw, ty - 30, tx + tw, ty + 40], fill=(15, 70, 20))
    # Ground
    draw.rectangle([0, floor_y, w, h], fill=(25, 55, 20))
    draw.line([(0, floor_y), (w, floor_y)], fill=(40, 80, 30), width=2)
    # Light rays
    for lx in [w//3, 2*w//3]:
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay, "RGBA")
        od.polygon([(lx-20, 0), (lx+20, 0), (lx+80, floor_y), (lx-80, floor_y)],
                   fill=(200, 255, 180, 18))
        img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))
    return img


SCENE_BUILDERS = {
    "White":      lambda w, h: Image.new("RGB", (w, h), (255, 255, 255)),
    "Black":      lambda w, h: Image.new("RGB", (w, h), (12, 12, 18)),
    "Dojo":       draw_dojo,
    "City Night": draw_city_night,
    "Arena":      draw_arena,
    "Forest":     draw_forest,
    "Gradient: Sunset": lambda w, h: make_gradient(w, h, (255, 100, 30), (40, 10, 80)),
    "Gradient: Ocean":  lambda w, h: make_gradient(w, h, (10, 80, 180), (180, 230, 255)),
    "Custom Image":     None,  # handled separately
}


def build_background(name, w, h, custom_img=None):
    if name == "Custom Image" and custom_img is not None:
        return custom_img.resize((w, h), Image.LANCZOS).convert("RGB")
    builder = SCENE_BUILDERS.get(name)
    if builder:
        return builder(w, h)
    return Image.new("RGB", (w, h), (255, 255, 255))
