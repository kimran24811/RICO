
import math
from PIL import Image, ImageChops


class SpriteEntry:
    def __init__(self, path, pil_image, animation_mode="bounce", base_scale=1.0,
                 x_offset=0, y_offset=0, remove_bg=False, bg_tolerance=30):
        self.path = path
        self.base_scale = base_scale
        self.animation_mode = animation_mode
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.pil_image = _prepare_image(pil_image, remove_bg, bg_tolerance)

    def to_dict(self):
        return {
            "path": self.path,
            "animation_mode": self.animation_mode,
            "base_scale": self.base_scale,
            "x_offset": self.x_offset,
            "y_offset": self.y_offset,
        }


def _prepare_image(img, remove_bg, tolerance):
    img = img.convert("RGBA")
    if remove_bg:
        img = _remove_white_bg(img, tolerance)
    return img


def _remove_white_bg(img, tolerance=30):
    img = img.convert("RGBA")
    data = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = data[x, y]
            if r > 255 - tolerance and g > 255 - tolerance and b > 255 - tolerance:
                data[x, y] = (r, g, b, 0)
    return img


def compute_sprite_transform(frame_index, total_frames, mode, joints,
                              canvas_w, canvas_h, base_scale=1.0,
                              x_offset=0, y_offset=0):
    t = frame_index / max(total_frames - 1, 1)
    pi = math.pi
    cx = canvas_w // 2 + x_offset
    cy = int(canvas_h * 0.55) + y_offset

    if mode == "bounce":
        bounce_h = 40
        y = cy - abs(math.sin(pi * t * 2)) * bounce_h
        x = cx + math.sin(2 * pi * t) * 20
        rot = math.sin(2 * pi * t) * 6
        scale = 1.0 + 0.05 * abs(math.sin(pi * t * 2))

    elif mode == "run_along":
        x = cx + math.sin(pi * t - pi/2) * (canvas_w * 0.4)
        y = cy + math.sin(2 * pi * t * 2) * 8
        rot = math.sin(2 * pi * t * 2) * 8
        scale = 1.0

    elif mode == "spin":
        rot = t * 360
        x = cx + math.sin(2 * pi * t) * 30
        y = cy + math.cos(2 * pi * t) * 10
        scale = 0.9 + 0.2 * abs(math.sin(pi * t))

    elif mode == "float":
        x = cx + math.sin(2 * pi * t * 0.7) * 30
        y = cy + math.sin(2 * pi * t * 1.1) * 20 - 40
        rot = math.sin(2 * pi * t * 0.5) * 5
        scale = 1.0 + 0.03 * math.sin(2 * pi * t)

    elif mode == "fight":
        # Follow the right wrist joint if available
        if joints and "r_wrist" in joints:
            jx, jy = joints["r_wrist"]
            scx = canvas_w // 2
            scy = int(canvas_h * 0.55)
            x = scx + jx * 1.25 + x_offset
            y = scy + jy * 1.25 + y_offset
            rot = math.sin(t * pi * 4) * 20
            scale = 1.0 + 0.1 * abs(math.sin(t * pi * 3))
        else:
            x, y, rot, scale = cx, cy, 0, 1.0

    elif mode == "slam":
        x = cx
        y = cy - (1 - t) * 100 if t < 0.5 else cy
        scale = 0.8 + t * 0.4
        rot = (1 - t) * -15

    else:
        x, y, rot, scale = cx, cy, 0, 1.0

    return (x, y, rot, scale * base_scale)


def composite_sprite(img, sprite_entry, frame_index, total_frames, joints, canvas_w, canvas_h):
    x, y, rot, scale = compute_sprite_transform(
        frame_index, total_frames, sprite_entry.animation_mode,
        joints, canvas_w, canvas_h, sprite_entry.base_scale,
        sprite_entry.x_offset, sprite_entry.y_offset
    )
    src = sprite_entry.pil_image.copy()
    new_w = max(1, int(src.width * scale))
    new_h = max(1, int(src.height * scale))
    src = src.resize((new_w, new_h), Image.LANCZOS)
    if rot != 0:
        src = src.rotate(-rot, expand=True, resample=Image.BICUBIC)
    px = int(x - src.width // 2)
    py = int(y - src.height // 2)
    # Ensure RGBA
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    if src.mode == "RGBA":
        mask = src.split()[3]
        overlay.paste(src, (px, py), mask)
    else:
        overlay.paste(src, (px, py))
    result = Image.alpha_composite(base, overlay)
    return result.convert("RGB")
