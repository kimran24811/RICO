
import math


def ease_linear(t):
    return t

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def ease_out(t):
    return 1 - (1 - t) ** 2

def ease_in(t):
    return t * t

def ease_bounce(t):
    if t < 1/2.75:
        return 7.5625 * t * t
    elif t < 2/2.75:
        t -= 1.5/2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5/2.75:
        t -= 2.25/2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625/2.75
        return 7.5625 * t * t + 0.984375

def ease_elastic(t):
    if t == 0 or t == 1:
        return t
    return -(2 ** (10 * (t - 1))) * math.sin((t - 1.1) * (2 * math.pi) / 0.4)

EASINGS = {
    "smooth":  ease_in_out,
    "snap":    ease_out,
    "linear":  ease_linear,
    "ease_in": ease_in,
    "bounce":  ease_bounce,
    "elastic": ease_elastic,
}


def tween_poses(pose_a, pose_b, t, mode="smooth"):
    fn = EASINGS.get(mode, ease_in_out)
    t = fn(max(0.0, min(1.0, t)))
    result = {}
    for joint in pose_a:
        ax, ay = pose_a[joint]
        bx, by = pose_b[joint]
        result[joint] = (ax + (bx - ax) * t, ay + (by - ay) * t)
    return result


def generate_frames(pose_sequence):
    """pose_sequence: list of (pose_dict, n_frames) or (pose_dict, n_frames, easing)"""
    frames = []
    for i, entry in enumerate(pose_sequence):
        pose = entry[0]
        n = entry[1]
        mode = entry[2] if len(entry) > 2 else "smooth"
        next_pose = pose_sequence[i + 1][0] if i + 1 < len(pose_sequence) else pose
        for f in range(n):
            t = f / max(n - 1, 1)
            frames.append(tween_poses(pose, next_pose, t, mode))
    return frames
