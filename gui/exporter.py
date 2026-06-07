
import cv2
import numpy as np
import pygame
import os


def export_mp4(frames_surfaces, output_path, fps=24):
    if not frames_surfaces:
        return False
    w, h = frames_surfaces[0].get_size()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    for surf in frames_surfaces:
        rgb = pygame.surfarray.array3d(surf)
        rgb = np.transpose(rgb, (1, 0, 2))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        out.write(bgr)
    out.release()
    return True
