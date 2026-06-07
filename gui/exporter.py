
import cv2
import numpy as np
import os
from PIL import Image


def export_mp4(frames_pil, output_path, fps=24):
    if not frames_pil:
        return False
    w, h = frames_pil[0].size
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    for img in frames_pil:
        bgr = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
        out.write(bgr)
    out.release()
    return True


def export_gif(frames_pil, output_path, fps=24):
    if not frames_pil:
        return False
    dur = int(1000 / fps)
    frames_pil[0].save(
        output_path, save_all=True,
        append_images=frames_pil[1:],
        loop=0, duration=dur, optimize=False
    )
    return True


def export_png_sequence(frames_pil, folder):
    if not frames_pil:
        return False
    os.makedirs(folder, exist_ok=True)
    for i, img in enumerate(frames_pil):
        img.save(os.path.join(folder, f"frame_{i:04d}.png"))
    return True
