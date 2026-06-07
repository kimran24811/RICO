"""
Generate Rico-style SVG character parts for Wick Editor import.
Run this once: python generate_assets.py
It creates a folder called 'wick_assets' with all SVG files.
"""

import os
import math

OUT = "wick_assets"
os.makedirs(OUT, exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def svg(w, h, content, viewbox=None):
    vb = viewbox or f"0 0 {w} {h}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{w}" height="{h}" viewBox="{vb}">'
            f'{content}</svg>')

def circle(cx, cy, r, fill="#1a1a1a", stroke="none", sw=0):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')

def line(x1, y1, x2, y2, stroke="#1a1a1a", sw=8, cap="round"):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}"/>')

def rounded_rect(x, y, w, h, rx, fill="#1a1a1a"):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>'

def save(name, content):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        f.write(content)
    print(f"  Saved: {name}")

# ── Character Parts ───────────────────────────────────────────────────────────

# HEAD — big round head with eyes, eyebrows, slight smirk (Rico style)
def make_head():
    c = ""
    # Head circle
    c += circle(50, 50, 44, fill="#2a2a2a", stroke="#111", sw=3)
    # White of eyes
    c += circle(34, 44, 12, fill="white")
    c += circle(66, 44, 12, fill="white")
    # Pupils
    c += circle(36, 46, 6, fill="#111")
    c += circle(68, 46, 6, fill="#111")
    # Eye shine
    c += circle(39, 43, 2, fill="white")
    c += circle(71, 43, 2, fill="white")
    # Eyebrows (thick, angled — action style)
    c += f'<line x1="24" y1="30" x2="44" y2="34" stroke="#111" stroke-width="4" stroke-linecap="round"/>'
    c += f'<line x1="56" y1="34" x2="76" y2="30" stroke="#111" stroke-width="4" stroke-linecap="round"/>'
    # Smirk
    c += f'<path d="M 38 62 Q 50 70 62 62" stroke="#111" stroke-width="3" fill="none" stroke-linecap="round"/>'
    # Spiky hair (Rico signature look)
    spikes = [(30,-8,20,-20),(45,-8,42,-24),(55,-8,58,-22),(68,-6,72,-16)]
    for x1,y1,x2,y2 in spikes:
        c += f'<line x1="{x1}" y1="{50+y1}" x2="{x2}" y2="{50+y2}" stroke="#111" stroke-width="5" stroke-linecap="round"/>'
    return svg(100, 100, c)

# TORSO — thick rounded body
def make_torso():
    c = ""
    c += rounded_rect(10, 0, 60, 80, 12, fill="#1a1a1a")
    # Collar line
    c += f'<line x1="20" y1="8" x2="60" y2="8" stroke="#333" stroke-width="2"/>'
    return svg(80, 80, c)

# UPPER ARM
def make_upper_arm():
    c = line(10, 10, 10, 55, stroke="#1a1a1a", sw=16, cap="round")
    c += circle(10, 10, 8, fill="#1a1a1a")
    c += circle(10, 55, 8, fill="#1a1a1a")
    return svg(20, 65, c)

# LOWER ARM + FIST
def make_lower_arm():
    c = line(10, 5, 10, 50, stroke="#1a1a1a", sw=14, cap="round")
    # Fist
    c += rounded_rect(2, 50, 18, 16, 5, fill="#1a1a1a")
    c += circle(10, 5, 7, fill="#1a1a1a")
    return svg(20, 68, c)

# UPPER LEG
def make_upper_leg():
    c = line(10, 8, 10, 60, stroke="#1a1a1a", sw=18, cap="round")
    c += circle(10, 8, 9, fill="#1a1a1a")
    c += circle(10, 60, 9, fill="#1a1a1a")
    return svg(20, 70, c)

# LOWER LEG + FOOT
def make_lower_leg():
    c = line(10, 5, 10, 55, stroke="#1a1a1a", sw=16, cap="round")
    # Foot
    c += rounded_rect(2, 55, 28, 12, 6, fill="#1a1a1a")
    c += circle(10, 5, 8, fill="#1a1a1a")
    return svg(32, 69, c)

# NECK
def make_neck():
    c = rounded_rect(6, 0, 18, 26, 5, fill="#2a2a2a")
    return svg(30, 26, c)

# ── Pose Reference Sheets ─────────────────────────────────────────────────────

def make_pose_sheet():
    """SVG showing idle, run, punch, kick poses side by side for reference"""
    W, H = 800, 300
    c = f'<rect width="{W}" height="{H}" fill="#f5f5f5"/>'
    c += f'<text x="10" y="20" font-family="Arial" font-size="14" font-weight="bold" fill="#333">RICO — Pose Reference Sheet</text>'

    poses = [
        ("IDLE",  160, [
            (100,60,100,60), # head at 100,60
        ]),
    ]

    labels = ["IDLE", "RUN", "JUMP", "PUNCH", "KICK", "DEATH"]
    for i, label in enumerate(labels):
        lx = 70 + i * 120
        c += f'<text x="{lx}" y="{H-10}" font-family="Arial" font-size="11" text-anchor="middle" fill="#666">{label}</text>'

    return svg(W, H, c)


# ── Full Character (single SVG, easy to import) ───────────────────────────────

def make_full_character_idle():
    """Complete Rico-style character in idle pose as single SVG"""
    W, H = 160, 320
    c = f'<rect width="{W}" height="{H}" fill="none"/>'

    cx = W // 2  # 80

    # Shadow
    c += f'<ellipse cx="{cx}" cy="300" rx="40" ry="8" fill="#00000022"/>'

    # LEGS
    # Left leg (back)
    c += line(cx-8, 180, cx-12, 240, sw=18, stroke="#1a1a1a")  # upper
    c += line(cx-12, 240, cx-16, 285, sw=15, stroke="#1a1a1a")  # lower
    c += rounded_rect(cx-30, 281, 36, 14, 7, fill="#1a1a1a")  # foot

    # Right leg
    c += line(cx+8, 180, cx+12, 240, sw=18, stroke="#1a1a1a")
    c += line(cx+12, 240, cx+16, 285, sw=15, stroke="#1a1a1a")
    c += rounded_rect(cx+4, 281, 36, 14, 7, fill="#1a1a1a")

    # TORSO
    c += rounded_rect(cx-32, 100, 64, 90, 14, fill="#1a1a1a")

    # ARMS
    # Left arm (back)
    c += line(cx-30, 110, cx-48, 170, sw=15, stroke="#1a1a1a")  # upper
    c += line(cx-48, 170, cx-44, 220, sw=13, stroke="#1a1a1a")  # lower
    c += rounded_rect(cx-54, 218, 20, 14, 5, fill="#1a1a1a")  # fist

    # Right arm
    c += line(cx+30, 110, cx+48, 170, sw=15, stroke="#1a1a1a")
    c += line(cx+48, 170, cx+44, 220, sw=13, stroke="#1a1a1a")
    c += rounded_rect(cx+34, 218, 20, 14, 5, fill="#1a1a1a")

    # NECK
    c += rounded_rect(cx-10, 88, 20, 18, 5, fill="#1a1a1a")

    # HEAD
    c += circle(cx, 62, 42, fill="#2a2a2a")

    # Eyes
    c += circle(cx-16, 56, 11, fill="white")
    c += circle(cx+16, 56, 11, fill="white")
    c += circle(cx-14, 58, 6, fill="#111")
    c += circle(cx+18, 58, 6, fill="#111")
    c += circle(cx-12, 55, 2, fill="white")
    c += circle(cx+20, 55, 2, fill="white")

    # Eyebrows
    c += f'<line x1="{cx-26}" y1="43" x2="{cx-6}" y2="46" stroke="#111" stroke-width="4" stroke-linecap="round"/>'
    c += f'<line x1="{cx+6}" y1="46" x2="{cx+26}" y2="43" stroke="#111" stroke-width="4" stroke-linecap="round"/>'

    # Mouth
    c += f'<path d="M {cx-12} 74 Q {cx} 82 {cx+12} 74" stroke="#111" stroke-width="3" fill="none" stroke-linecap="round"/>'

    # Hair spikes
    hair = [(cx-22,20),(cx-8,14),(cx+8,14),(cx+22,20),(cx+30,30)]
    roots = [(cx-26,30),(cx-10,24),(cx+8,22),(cx+22,28),(cx+32,38)]
    for (hx,hy),(rx,ry) in zip(hair,roots):
        c += f'<line x1="{rx}" y1="{ry}" x2="{hx}" y2="{hy}" stroke="#111" stroke-width="6" stroke-linecap="round"/>'

    return svg(W, H, c)


def make_full_character_punch():
    W, H = 200, 320
    c = f'<rect width="{W}" height="{H}" fill="none"/>'
    cx = 70

    c += f'<ellipse cx="{cx}" cy="300" rx="40" ry="8" fill="#00000022"/>'

    # Legs (stable stance)
    c += line(cx-8, 180, cx-14, 242, sw=18, stroke="#1a1a1a")
    c += line(cx-14, 242, cx-18, 287, sw=15, stroke="#1a1a1a")
    c += rounded_rect(cx-32, 283, 36, 14, 7, fill="#1a1a1a")
    c += line(cx+8, 180, cx+14, 242, sw=18, stroke="#1a1a1a")
    c += line(cx+14, 242, cx+18, 287, sw=15, stroke="#1a1a1a")
    c += rounded_rect(cx+8, 283, 36, 14, 7, fill="#1a1a1a")

    # Torso (slight lean forward)
    c += rounded_rect(cx-28, 102, 60, 88, 14, fill="#1a1a1a")

    # Left arm (guard position)
    c += line(cx-26, 112, cx-40, 168, sw=15, stroke="#1a1a1a")
    c += line(cx-40, 168, cx-34, 210, sw=13, stroke="#1a1a1a")
    c += rounded_rect(cx-44, 208, 20, 14, 5, fill="#1a1a1a")

    # Right arm — EXTENDED PUNCH
    c += line(cx+26, 110, cx+68, 120, sw=15, stroke="#1a1a1a")
    c += line(cx+68, 120, cx+118, 116, sw=13, stroke="#1a1a1a")
    # Big fist
    c += rounded_rect(cx+116, 110, 24, 18, 6, fill="#1a1a1a")
    # Impact lines
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        x1 = cx + 140 + math.cos(rad) * 8
        y1 = 119 + math.sin(rad) * 8
        x2 = cx + 140 + math.cos(rad) * 20
        y2 = 119 + math.sin(rad) * 20
        c += f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#FFD700" stroke-width="3" stroke-linecap="round"/>'

    # Neck + head
    c += rounded_rect(cx-8, 90, 20, 18, 5, fill="#1a1a1a")
    c += circle(cx+4, 64, 42, fill="#2a2a2a")
    c += circle(cx-12, 58, 11, fill="white")
    c += circle(cx+20, 58, 11, fill="white")
    c += circle(cx-10, 60, 6, fill="#111")
    c += circle(cx+22, 60, 6, fill="#111")
    c += circle(cx-8, 57, 2, fill="white")
    c += circle(cx+24, 57, 2, fill="white")
    c += f'<line x1="{cx-22}" y1="45" x2="{cx-2}" y2="48" stroke="#111" stroke-width="4" stroke-linecap="round"/>'
    c += f'<line x1="{cx+10}" y1="46" x2="{cx+30}" y2="42" stroke="#111" stroke-width="5" stroke-linecap="round"/>'
    c += f'<path d="M {cx-8} 76 Q {cx+4} 82 {cx+16} 76" stroke="#111" stroke-width="3" fill="none" stroke-linecap="round"/>'
    hair = [(cx-18,22),(cx-4,16),(cx+10,16),(cx+24,22)]
    roots = [(cx-22,32),(cx-6,26),(cx+10,24),(cx+24,30)]
    for (hx,hy),(rx,ry) in zip(hair,roots):
        c += f'<line x1="{rx}" y1="{ry}" x2="{hx}" y2="{hy}" stroke="#111" stroke-width="6" stroke-linecap="round"/>'

    return svg(W, H, c)


def make_full_character_kick():
    W, H = 220, 320
    c = f'<rect width="{W}" height="{H}" fill="none"/>'
    cx = 70

    c += f'<ellipse cx="{cx}" cy="300" rx="35" ry="8" fill="#00000022"/>'

    # Standing leg
    c += line(cx+6, 178, cx+10, 240, sw=18, stroke="#1a1a1a")
    c += line(cx+10, 240, cx+12, 287, sw=15, stroke="#1a1a1a")
    c += rounded_rect(cx+0, 283, 36, 14, 7, fill="#1a1a1a")

    # Kicking leg — EXTENDED HIGH
    c += line(cx-6, 178, cx-30, 150, sw=18, stroke="#1a1a1a")  # upper thigh
    c += line(cx-30, 150, cx+40, 130, sw=15, stroke="#1a1a1a")  # lower leg extended
    # Foot at end
    c += rounded_rect(cx+32, 122, 38, 14, 7, fill="#1a1a1a")

    # Torso
    c += rounded_rect(cx-28, 100, 62, 88, 14, fill="#1a1a1a")

    # Arms — balance pose
    c += line(cx-28, 110, cx-56, 158, sw=15, stroke="#1a1a1a")
    c += line(cx-56, 158, cx-58, 202, sw=13, stroke="#1a1a1a")
    c += rounded_rect(cx-68, 200, 20, 14, 5, fill="#1a1a1a")
    c += line(cx+28, 110, cx+52, 148, sw=15, stroke="#1a1a1a")
    c += line(cx+52, 148, cx+50, 192, sw=13, stroke="#1a1a1a")
    c += rounded_rect(cx+40, 190, 20, 14, 5, fill="#1a1a1a")

    # Impact lines at foot
    for ang in range(0, 360, 40):
        rad = math.radians(ang)
        x1 = cx + 70 + math.cos(rad) * 8
        y1 = 129 + math.sin(rad) * 8
        x2 = cx + 70 + math.cos(rad) * 22
        y2 = 129 + math.sin(rad) * 22
        c += f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#FF4444" stroke-width="3" stroke-linecap="round"/>'

    # Neck + head
    c += rounded_rect(cx-8, 88, 20, 18, 5, fill="#1a1a1a")
    c += circle(cx, 62, 42, fill="#2a2a2a")
    c += circle(cx-16, 56, 11, fill="white")
    c += circle(cx+16, 56, 11, fill="white")
    c += circle(cx-14, 58, 6, fill="#111")
    c += circle(cx+18, 58, 6, fill="#111")
    c += circle(cx-12, 55, 2, fill="white")
    c += circle(cx+20, 55, 2, fill="white")
    c += f'<line x1="{cx-26}" y1="43" x2="{cx-6}" y2="46" stroke="#111" stroke-width="4" stroke-linecap="round"/>'
    c += f'<line x1="{cx+6}" y1="46" x2="{cx+26}" y2="43" stroke="#111" stroke-width="4" stroke-linecap="round"/>'
    c += f'<path d="M {cx-12} 74 Q {cx} 82 {cx+12} 74" stroke="#111" stroke-width="3" fill="none" stroke-linecap="round"/>'
    hair = [(cx-22,20),(cx-8,14),(cx+8,14),(cx+22,20)]
    roots = [(cx-26,30),(cx-10,24),(cx+8,22),(cx+22,28)]
    for (hx,hy),(rx,ry) in zip(hair,roots):
        c += f'<line x1="{rx}" y1="{ry}" x2="{hx}" y2="{hy}" stroke="#111" stroke-width="6" stroke-linecap="round"/>'

    return svg(W, H, c)


def make_full_character_run():
    W, H = 180, 300
    c = f'<rect width="{W}" height="{H}" fill="none"/>'
    cx = 80

    # Run pose A — left foot forward, right arm forward
    # Back arm (right — behind body, going back)
    c += line(cx+26, 108, cx+58, 152, sw=15, stroke="#1a1a1a")
    c += line(cx+58, 152, cx+62, 196, sw=13, stroke="#1a1a1a")
    c += rounded_rect(cx+52, 194, 20, 14, 5, fill="#1a1a1a")

    # Back leg (right — behind, straight back)
    c += line(cx+8, 178, cx+28, 234, sw=18, stroke="#1a1a1a")
    c += line(cx+28, 234, cx+38, 278, sw=15, stroke="#1a1a1a")
    c += rounded_rect(cx+28, 274, 36, 14, 7, fill="#1a1a1a")

    # Torso (leaning forward)
    c += rounded_rect(cx-26, 98, 58, 86, 14, fill="#1a1a1a")

    # Front leg (left — forward, knee up)
    c += line(cx-6, 178, cx-28, 220, sw=18, stroke="#1a1a1a")
    c += line(cx-28, 220, cx-14, 266, sw=15, stroke="#1a1a1a")
    c += rounded_rect(cx-22, 262, 36, 14, 7, fill="#1a1a1a")

    # Front arm (left — forward, reaching)
    c += line(cx-24, 108, cx-52, 148, sw=15, stroke="#1a1a1a")
    c += line(cx-52, 148, cx-56, 192, sw=13, stroke="#1a1a1a")
    c += rounded_rect(cx-66, 190, 20, 14, 5, fill="#1a1a1a")

    # Neck + head (tilted forward)
    c += rounded_rect(cx-9, 86, 20, 18, 5, fill="#1a1a1a")
    c += circle(cx+2, 60, 40, fill="#2a2a2a")
    c += circle(cx-14, 54, 10, fill="white")
    c += circle(cx+18, 56, 10, fill="white")
    c += circle(cx-12, 56, 5, fill="#111")
    c += circle(cx+20, 58, 5, fill="#111")
    c += circle(cx-10, 53, 2, fill="white")
    c += circle(cx+22, 55, 2, fill="white")
    c += f'<line x1="{cx-24}" y1="42" x2="{cx-4}" y2="46" stroke="#111" stroke-width="4" stroke-linecap="round"/>'
    c += f'<line x1="{cx+8}" y1="46" x2="{cx+28}" y2="42" stroke="#111" stroke-width="4" stroke-linecap="round"/>'
    c += f'<path d="M {cx-10} 72 Q {cx+2} 78 {cx+14} 72" stroke="#111" stroke-width="3" fill="none" stroke-linecap="round"/>'
    hair = [(cx-18,20),(cx-4,14),(cx+10,14),(cx+24,20)]
    roots = [(cx-20,30),(cx-4,22),(cx+10,22),(cx+24,28)]
    for (hx,hy),(rx,ry) in zip(hair,roots):
        c += f'<line x1="{rx}" y1="{ry}" x2="{hx}" y2="{hy}" stroke="#111" stroke-width="6" stroke-linecap="round"/>'

    return svg(W, H, c)


def make_full_character_jump():
    W, H = 200, 300
    c = f'<rect width="{W}" height="{H}" fill="none"/>'
    cx = 100

    # Both arms up
    c += line(cx-28, 108, cx-62, 62, sw=15, stroke="#1a1a1a")
    c += line(cx-62, 62, cx-70, 20, sw=13, stroke="#1a1a1a")
    c += rounded_rect(cx-80, 14, 20, 14, 5, fill="#1a1a1a")
    c += line(cx+28, 108, cx+62, 62, sw=15, stroke="#1a1a1a")
    c += line(cx+62, 62, cx+70, 20, sw=13, stroke="#1a1a1a")
    c += rounded_rect(cx+60, 14, 20, 14, 5, fill="#1a1a1a")

    # Torso
    c += rounded_rect(cx-30, 100, 60, 86, 14, fill="#1a1a1a")

    # Legs tucked up
    c += line(cx-10, 180, cx-32, 218, sw=18, stroke="#1a1a1a")
    c += line(cx-32, 218, cx-20, 258, sw=15, stroke="#1a1a1a")
    c += rounded_rect(cx-28, 254, 34, 13, 6, fill="#1a1a1a")
    c += line(cx+10, 180, cx+32, 218, sw=18, stroke="#1a1a1a")
    c += line(cx+32, 218, cx+20, 258, sw=15, stroke="#1a1a1a")
    c += rounded_rect(cx+6, 254, 34, 13, 6, fill="#1a1a1a")

    # Neck + head
    c += rounded_rect(cx-10, 88, 20, 18, 5, fill="#1a1a1a")
    c += circle(cx, 62, 42, fill="#2a2a2a")
    c += circle(cx-16, 56, 11, fill="white")
    c += circle(cx+16, 56, 11, fill="white")
    c += circle(cx-14, 58, 7, fill="#111")
    c += circle(cx+18, 58, 7, fill="#111")
    c += circle(cx-11, 55, 2, fill="white")
    c += circle(cx+21, 55, 2, fill="white")
    # Excited eyebrows
    c += f'<line x1="{cx-28}" y1="40" x2="{cx-6}" y2="44" stroke="#111" stroke-width="5" stroke-linecap="round"/>'
    c += f'<line x1="{cx+6}" y1="44" x2="{cx+28}" y2="40" stroke="#111" stroke-width="5" stroke-linecap="round"/>'
    c += f'<path d="M {cx-12} 74 Q {cx} 84 {cx+12} 74" stroke="#111" stroke-width="3" fill="none" stroke-linecap="round"/>'
    hair = [(cx-22,16),(cx-6,8),(cx+8,8),(cx+24,16),(cx+32,26)]
    roots = [(cx-26,28),(cx-8,20),(cx+8,20),(cx+24,26),(cx+32,36)]
    for (hx,hy),(rx,ry) in zip(hair,roots):
        c += f'<line x1="{rx}" y1="{ry}" x2="{hx}" y2="{hy}" stroke="#111" stroke-width="6" stroke-linecap="round"/>'

    return svg(W, H, c)


def make_full_character_death():
    W, H = 320, 180
    c = f'<rect width="{W}" height="{H}" fill="none"/>'

    # Lying flat (horizontal)
    # Head on left
    c += circle(50, 100, 42, fill="#2a2a2a")
    # X eyes (knocked out)
    for ex, ey in [(36, 94), (64, 94)]:
        c += f'<line x1="{ex-7}" y1="{ey-7}" x2="{ex+7}" y2="{ey+7}" stroke="#111" stroke-width="4" stroke-linecap="round"/>'
        c += f'<line x1="{ex+7}" y1="{ey-7}" x2="{ex-7}" y2="{ey+7}" stroke="#111" stroke-width="4" stroke-linecap="round"/>'
    c += f'<path d="M 38 112 Q 50 106 62 112" stroke="#111" stroke-width="3" fill="none" stroke-linecap="round"/>'
    hair = [(30,60),(44,54),(60,56),(72,64)]
    roots = [(28,72),(44,64),(60,66),(74,74)]
    for (hx,hy),(rx,ry) in zip(hair,roots):
        c += f'<line x1="{rx}" y1="{ry}" x2="{hx}" y2="{hy}" stroke="#111" stroke-width="5" stroke-linecap="round"/>'

    # Neck
    c += rounded_rect(88, 90, 18, 20, 5, fill="#1a1a1a")

    # Torso (horizontal)
    c += rounded_rect(102, 86, 86, 58, 14, fill="#1a1a1a")

    # Arms flopped
    c += line(110, 88, 118, 54, sw=14, stroke="#1a1a1a")
    c += line(118, 54, 140, 40, sw=12, stroke="#1a1a1a")
    c += rounded_rect(136, 34, 18, 12, 4, fill="#1a1a1a")
    c += line(178, 88, 186, 54, sw=14, stroke="#1a1a1a")
    c += line(186, 54, 208, 42, sw=12, stroke="#1a1a1a")
    c += rounded_rect(204, 36, 18, 12, 4, fill="#1a1a1a")

    # Legs stretched out to right
    c += line(182, 140, 236, 138, sw=18, stroke="#1a1a1a")
    c += line(236, 138, 290, 136, sw=15, stroke="#1a1a1a")
    c += rounded_rect(286, 130, 26, 14, 6, fill="#1a1a1a")
    c += line(114, 140, 168, 142, sw=18, stroke="#1a1a1a")
    c += line(168, 142, 222, 144, sw=15, stroke="#1a1a1a")
    c += rounded_rect(218, 138, 26, 14, 6, fill="#1a1a1a")

    # Stars around head
    for ang in range(0, 360, 60):
        rad = math.radians(ang)
        sx = 50 + math.cos(rad) * 54
        sy = 100 + math.sin(rad) * 54
        c += circle(int(sx), int(sy), 5, fill="#FFD700")

    return svg(W, H, c)


# ── Generate All ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating Rico-style SVG assets for Wick Editor...")
    save("rico_idle.svg",  make_full_character_idle())
    save("rico_punch.svg", make_full_character_punch())
    save("rico_kick.svg",  make_full_character_kick())
    save("rico_run.svg",   make_full_character_run())
    save("rico_jump.svg",  make_full_character_jump())
    save("rico_death.svg", make_full_character_death())
    # Individual parts for rigging
    save("part_head.svg",       make_head())
    save("part_torso.svg",      make_torso())
    save("part_upper_arm.svg",  make_upper_arm())
    save("part_lower_arm.svg",  make_lower_arm())
    save("part_upper_leg.svg",  make_upper_leg())
    save("part_lower_leg.svg",  make_lower_leg())
    save("part_neck.svg",       make_neck())
    print(f"\nDone! All files saved to '{OUT}/'")
    print("\nFiles to import into Wick Editor:")
    print("  rico_idle.svg  → your starting pose")
    print("  rico_punch.svg → punch keyframe")
    print("  rico_kick.svg  → kick keyframe")
    print("  rico_run.svg   → run keyframe")
    print("  rico_jump.svg  → jump keyframe")
    print("  rico_death.svg → death pose")
