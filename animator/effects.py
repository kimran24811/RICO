
import math
import random
from PIL import ImageDraw, Image, ImageFont


# ── Speed Lines ───────────────────────────────────────────────────────────────

def draw_speed_lines(img, cx, cy, direction="right", intensity=1.0, count=14):
    draw = ImageDraw.Draw(img, "RGBA")
    length_range = (60, 180)
    for _ in range(count):
        angle = random.uniform(-35, 35)
        if direction == "right":
            angle += 0
        elif direction == "left":
            angle += 180
        elif direction == "up":
            angle += 270
        rad = math.radians(angle)
        length = random.uniform(*length_range) * intensity
        gap = random.uniform(10, 90)
        sx = cx + math.cos(rad) * gap
        sy = cy + math.sin(rad) * gap
        ex = sx + math.cos(rad) * length
        ey = sy + math.sin(rad) * length
        alpha = int(random.uniform(60, 140) * intensity)
        width = random.randint(1, 3)
        draw.line([(sx, sy), (ex, ey)], fill=(255, 255, 255, alpha), width=width)


# ── Camera Shake ──────────────────────────────────────────────────────────────

def get_shake_offset(frame_index, intensity=8, decay=0.7):
    if intensity < 1:
        return (0, 0)
    amp = intensity * (decay ** frame_index)
    if amp < 0.5:
        return (0, 0)
    dx = math.sin(frame_index * 3.7) * amp
    dy = math.cos(frame_index * 2.9) * amp
    return (int(dx), int(dy))


# ── SFX Text Labels ───────────────────────────────────────────────────────────

SFX_STYLES = {
    "POW!":    {"color": (255, 60,  20),  "size": 52, "outline": (255, 220, 0)},
    "BAM!":    {"color": (255, 30,  80),  "size": 48, "outline": (255, 255, 0)},
    "WHAM!":   {"color": (255, 140, 0),   "size": 48, "outline": (200, 50,  0)},
    "WHOOSH!": {"color": (80,  180, 255), "size": 40, "outline": (255, 255, 255)},
    "CRACK!":  {"color": (255, 255, 80),  "size": 44, "outline": (180, 100, 0)},
    "KA-POW!": {"color": (255, 50,  200), "size": 52, "outline": (255, 255, 0)},
    "UGH!":    {"color": (150, 255, 100), "size": 36, "outline": (40,  120, 20)},
    "DODGE!":  {"color": (100, 200, 255), "size": 36, "outline": (0,   80,  160)},
}


def draw_sfx(img, text, x, y):
    style = SFX_STYLES.get(text, {"color": (255, 255, 0), "size": 44, "outline": (0, 0, 0)})
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arialbd.ttf", style["size"])
    except Exception:
        font = ImageFont.load_default()

    # Outline
    oc = style["outline"]
    for dx, dy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,-2),(-2,2),(2,2)]:
        draw.text((x+dx, y+dy), text, fill=oc, font=font)
    draw.text((x, y), text, fill=style["color"], font=font)


# ── Particles ─────────────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, vx, vy, life, color, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.4  # gravity
        self.vx *= 0.92
        self.life -= 1
        self.size = max(1, self.size * 0.94)

    def alive(self):
        return self.life > 0

    def draw(self, draw):
        alpha = int(255 * (self.life / self.max_life))
        r, g, b = self.color
        s = int(self.size)
        draw.ellipse([int(self.x)-s, int(self.y)-s,
                      int(self.x)+s, int(self.y)+s],
                     fill=(r, g, b, alpha))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_dust(self, x, y, count=12):
        for _ in range(count):
            vx = random.uniform(-3, 3)
            vy = random.uniform(-4, -1)
            life = random.randint(12, 22)
            size = random.uniform(3, 8)
            gray = random.randint(140, 200)
            self.particles.append(Particle(x, y, vx, vy, life, (gray, gray-10, gray-20), size))

    def emit_sparks(self, x, y, count=16):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 9)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 2
            life = random.randint(8, 18)
            size = random.uniform(2, 5)
            r = 255
            g = random.randint(140, 220)
            self.particles.append(Particle(x, y, vx, vy, life, (r, g, 30), size))

    def emit_smoke(self, x, y, count=8):
        for _ in range(count):
            vx = random.uniform(-1.5, 1.5)
            vy = random.uniform(-2.5, -0.5)
            life = random.randint(18, 30)
            size = random.uniform(5, 12)
            gray = random.randint(180, 220)
            self.particles.append(Particle(x, y, vx, vy, life, (gray, gray, gray), size))

    def update(self):
        self.particles = [p for p in self.particles if p.alive()]
        for p in self.particles:
            p.update()

    def draw(self, img):
        if not self.particles:
            return
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")
        for p in self.particles:
            p.draw(draw)
        img.paste(overlay, (0, 0), overlay)
