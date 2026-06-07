
import pygame

LIMBS = [
    ("head", "neck"),
    ("neck", "r_shoulder"), ("neck", "l_shoulder"),
    ("r_shoulder", "r_elbow"), ("r_elbow", "r_wrist"),
    ("l_shoulder", "l_elbow"), ("l_elbow", "l_wrist"),
    ("r_shoulder", "r_hip"), ("l_shoulder", "l_hip"),
    ("r_hip", "l_hip"),
    ("r_hip", "r_knee"), ("r_knee", "r_ankle"),
    ("l_hip", "l_knee"), ("l_knee", "l_ankle"),
]

HEAD_RADIUS = 12


def draw_figure(surface, joints, cx, cy, scale=1.0, color=(30, 30, 30), blur=False, flash=False):
    def to_screen(jx, jy):
        return (int(cx + jx * scale), int(cy + jy * scale))

    if flash:
        flash_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(flash_surf, (255, 220, 50, 80),
                           to_screen(*joints["r_wrist"]), 30)
        surface.blit(flash_surf, (0, 0))

    for a, b in LIMBS:
        if a == "head":
            continue
        pa = to_screen(*joints[a])
        pb = to_screen(*joints[b])
        width = max(2, int(4 * scale))
        if blur:
            for offset in [(1, 0), (-1, 0), (0, 1)]:
                shifted_a = (pa[0] + offset[0]*3, pa[1] + offset[1]*3)
                shifted_b = (pb[0] + offset[0]*3, pb[1] + offset[1]*3)
                blur_color = (*color[:3], 60)
                s = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                pygame.draw.line(s, blur_color, shifted_a, shifted_b, width)
                surface.blit(s, (0, 0))
        pygame.draw.line(surface, color, pa, pb, width)
        pygame.draw.circle(surface, color, pb, max(2, int(3 * scale)))

    hx, hy = to_screen(*joints["head"])
    r = max(8, int(HEAD_RADIUS * scale))
    pygame.draw.circle(surface, color, (hx, hy), r, max(2, int(3 * scale)))
