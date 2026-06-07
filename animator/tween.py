
def ease_in_out(t):
    return t * t * (3 - 2 * t)

def ease_out(t):
    return 1 - (1 - t) ** 2

def tween_poses(pose_a, pose_b, t, mode="smooth"):
    if mode == "smooth":
        t = ease_in_out(max(0.0, min(1.0, t)))
    elif mode == "snap":
        t = ease_out(max(0.0, min(1.0, t)))
    else:
        t = max(0.0, min(1.0, t))
    result = {}
    for joint in pose_a:
        ax, ay = pose_a[joint]
        bx, by = pose_b[joint]
        result[joint] = (ax + (bx - ax) * t, ay + (by - ay) * t)
    return result

def generate_frames(pose_sequence):
    """pose_sequence: list of (pose_dict, n_frames, mode)"""
    frames = []
    for i, entry in enumerate(pose_sequence):
        pose = entry[0]
        n = entry[1]
        mode = entry[2] if len(entry) > 2 else "smooth"
        if i + 1 < len(pose_sequence):
            next_pose = pose_sequence[i + 1][0]
        else:
            next_pose = pose
        for f in range(n):
            t = f / max(n - 1, 1)
            frames.append(tween_poses(pose, next_pose, t, mode))
    return frames
