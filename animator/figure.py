
from PIL import ImageDraw

LIMBS = [
    ("neck", "r_shoulder"), ("neck", "l_shoulder"),
    ("r_shoulder", "r_elbow"), ("r_elbow", "r_wrist"),
    ("l_shoulder", "l_elbow"), ("l_elbow", "l_wrist"),
    ("r_shoulder", "r_hip"), ("l_shoulder", "l_hip"),
    ("r_hip", "l_hip"),
    ("r_hip", "r_knee"), ("r_knee", "r_ankle"),
    ("l_hip", "l_knee"), ("l_knee", "l_ankle"),
]

HEAD_RADIUS = 13


def draw_figure(draw, joints, cx, cy, scale=1.1, color=(20, 20, 20), flash=False):
    def s(jx, jy):
        return (int(cx + jx * scale), int(cy + jy * scale))

    if flash:
        wx, wy = s(*joints["r_wrist"])
        draw.ellipse([wx - 28, wy - 28, wx + 28, wy + 28], fill=(255, 220, 50, 120))

    lw = max(3, int(4 * scale))
    for a, b in LIMBS:
        pa = s(*joints[a])
        pb = s(*joints[b])
        draw.line([pa, pb], fill=color, width=lw)
        draw.ellipse([pb[0]-3, pb[1]-3, pb[0]+3, pb[1]+3], fill=color)

    hx, hy = s(*joints["head"])
    r = int(HEAD_RADIUS * scale)
    draw.ellipse([hx - r, hy - r, hx + r, hy + r], outline=color, width=lw)
