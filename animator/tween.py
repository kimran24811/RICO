
import numpy as np


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def tween_poses(pose_a, pose_b, t):
    t = ease_in_out(max(0.0, min(1.0, t)))
    result = {}
    for joint in pose_a:
        ax, ay = pose_a[joint]
        bx, by = pose_b[joint]
        result[joint] = (ax + (bx - ax) * t, ay + (by - ay) * t)
    return result


def generate_frames(pose_sequence):
    """pose_sequence: list of (pose_dict, n_frames)"""
    frames = []
    for i, (pose, n) in enumerate(pose_sequence):
        if i + 1 < len(pose_sequence):
            next_pose = pose_sequence[i + 1][0]
        else:
            next_pose = pose
        for f in range(n):
            t = f / max(n - 1, 1)
            frames.append(tween_poses(pose, next_pose, t))
    return frames
