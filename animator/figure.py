
from PIL import ImageDraw
import math

LIMBS = [
    ("neck",       "r_shoulder", 5),
    ("neck",       "l_shoulder", 5),
    ("r_shoulder", "r_elbow",    5),
    ("r_elbow",    "r_wrist",    4),
    ("l_shoulder", "l_elbow",    5),
    ("l_elbow",    "l_wrist",    4),
    ("neck",       "torso_mid",  6),
    ("torso_mid",  "torso_low",  6),
    ("torso_low",  "r_hip",      5),
    ("torso_low",  "l_hip",      5),
    ("r_hip",      "r_knee",     5),
    ("r_knee",     "r_ankle",    5),
    ("r_ankle",    "r_toe",      4),
    ("l_hip",      "l_knee",     5),
    ("l_knee",     "l_ankle",    5),
    ("l_ankle",    "l_toe",      4),
]

HEAD_R = 16


def draw_figure(draw, joints, cx, cy, scale=1.0, color=(20, 20, 20),
                flash=False, shadow=True, glow=False):

    def s(jx, jy):
        return (int(cx + jx * scale), int(cy + jy * scale))

    # Shadow
    if shadow:
        for a, b, w in LIMBS:
            pa = s(joints[a][0] + 4, joints[a][1] + 4)
            pb = s(joints[b][0] + 4, joints[b][1] + 4)
            sw = max(2, int(w * scale))
            draw.line([pa, pb], fill=(0, 0, 0, 50), width=sw)
        hx, hy = s(joints["head"][0] + 4, joints["head"][1] + 4)
        r = max(10, int(HEAD_R * scale))
        draw.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(0, 0, 0, 50))

    # Impact flash
    if flash:
        wx, wy = s(*joints["r_wrist"])
        for radius, alpha in [(48, 40), (32, 80), (18, 140)]:
            draw.ellipse([wx - radius, wy - radius, wx + radius, wy + radius],
                         fill=(255, 230, 60, alpha))

    # Glow outline
    if glow:
        glow_col = (*color[:3], 60)
        for a, b, w in LIMBS:
            pa = s(*joints[a])
            pb = s(*joints[b])
            gw = max(4, int((w + 4) * scale))
            draw.line([pa, pb], fill=glow_col, width=gw)

    # Main limbs
    for a, b, w in LIMBS:
        pa = s(*joints[a])
        pb = s(*joints[b])
        lw = max(2, int(w * scale))
        draw.line([pa, pb], fill=color, width=lw)
        # Round joints
        jw = max(2, int((w // 2 + 1) * scale))
        draw.ellipse([pb[0]-jw, pb[1]-jw, pb[0]+jw, pb[1]+jw], fill=color)
        draw.ellipse([pa[0]-jw, pa[1]-jw, pa[0]+jw, pa[1]+jw], fill=color)

    # Head
    hx, hy = s(*joints["head"])
    r = max(10, int(HEAD_R * scale))
    # Head fill (lighter than outline for cartoon look)
    if color == (20, 20, 20):
        fill_col = (50, 50, 50)
    elif color == (240, 240, 240):
        fill_col = (210, 210, 210)
    else:
        r2, g2, b2 = color
        fill_col = (min(255, r2 + 40), min(255, g2 + 40), min(255, b2 + 40))
    draw.ellipse([hx - r, hy - r, hx + r, hy + r], fill=fill_col, outline=color,
                 width=max(2, int(3 * scale)))

    # Eyes
    ew = max(2, int(3 * scale))
    ex_off = max(3, int(5 * scale))
    ey_off = max(1, int(3 * scale))
    draw.ellipse([hx - ex_off - ew, hy - ey_off - ew,
                  hx - ex_off + ew, hy - ey_off + ew], fill=color)
    draw.ellipse([hx + ex_off - ew, hy - ey_off - ew,
                  hx + ex_off + ew, hy - ey_off + ew], fill=color)
