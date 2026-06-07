
import cv2
import numpy as np
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
