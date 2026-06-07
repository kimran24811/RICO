
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pygame
import threading
import time
from PIL import Image, ImageTk

from animator.poses import POSES, MOVE_SEQUENCES
from animator.tween import generate_frames
from animator.figure import draw_figure
from gui.exporter import export_mp4

CANVAS_W = 480
CANVAS_H = 380
FPS = 24
BG_COLORS = {
    "White":  (255, 255, 255),
    "Black":  (15,  15,  15),
    "Blue":   (30,  60,  120),
    "Red":    (120, 30,  30),
}
FIG_COLORS = {
    "Black":  (20,  20,  20),
    "White":  (240, 240, 240),
    "Red":    (200, 40,  40),
    "Blue":   (40,  80,  200),
    "Green":  (40,  160, 80),
}
MOVE_NAMES = ["idle", "run", "jump", "land", "punch", "kick", "dodge", "spin", "death"]
MOVE_EMOJIS = {
    "idle": "🧍", "run": "🏃", "jump": "🦘", "land": "⬇️",
    "punch": "👊", "kick": "🦵", "dodge": "↩️", "spin": "🌀", "death": "💀",
}


def build_all_frames(move_list, bg_color, fig_color, speed):
    all_surfaces = []
    for move in move_list:
        seq = MOVE_SEQUENCES.get(move, MOVE_SEQUENCES["idle"])
        pose_seq = []
        for pose_name, n_frames in seq:
            adjusted = max(2, int(n_frames / speed))
            pose_seq.append((POSES[pose_name], adjusted))
        frames = generate_frames(pose_seq)
        fast_moves = {"punch", "kick", "spin"}
        for i, joints in enumerate(frames):
            surf = pygame.Surface((CANVAS_W, CANVAS_H))
            surf.fill(bg_color)
            blur = move in fast_moves
            flash = move in {"punch", "kick"} and i == len(frames) // 2
            draw_figure(surf, joints, CANVAS_W // 2, CANVAS_H // 2 + 20,
                        scale=1.1, color=fig_color, blur=blur, flash=flash)
            all_surfaces.append(surf)
    return all_surfaces


class RicoAnimator:
    def __init__(self, root):
        self.root = root
        self.root.title("RICO ANIMATOR")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)

        self.timeline = []
        self.all_frames = []
        self.current_frame = 0
        self.playing = False
        self.bg_color = (255, 255, 255)
        self.fig_color = (20, 20, 20)
        self.speed = 1.0
        self.preview_thread = None

        pygame.init()
        self._build_ui()
        self._render_idle()
        self._animate_loop()

    def _build_ui(self):
        title = tk.Label(self.root, text="⚡ RICO ANIMATOR",
                         bg="#1a1a2e", fg="#e94560",
                         font=("Arial Black", 16, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(10, 5))

        # Canvas area
        self.canvas_label = tk.Label(self.root, bg="#1a1a2e", bd=3, relief="ridge")
        self.canvas_label.grid(row=1, column=0, padx=10, pady=5)

        # Right panel
        right = tk.Frame(self.root, bg="#16213e", padx=10, pady=10)
        right.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=5)

        tk.Label(right, text="ACTIONS", bg="#16213e", fg="#e94560",
                 font=("Arial Black", 11, "bold")).pack(pady=(0, 5))

        btn_frame = tk.Frame(right, bg="#16213e")
        btn_frame.pack()
        for i, move in enumerate(MOVE_NAMES):
            emoji = MOVE_EMOJIS.get(move, "")
            b = tk.Button(btn_frame, text=f"{emoji} {move.upper()}",
                          width=12, height=2,
                          bg="#e94560", fg="white",
                          activebackground="#c73652",
                          font=("Arial", 9, "bold"),
                          relief="flat", cursor="hand2",
                          command=lambda m=move: self._add_move(m))
            b.grid(row=i // 2, column=i % 2, padx=3, pady=3)

        tk.Label(right, text="STYLE", bg="#16213e", fg="#e94560",
                 font=("Arial Black", 10, "bold")).pack(pady=(12, 2))

        tk.Label(right, text="Background:", bg="#16213e", fg="white",
                 font=("Arial", 9)).pack(anchor="w")
        self.bg_var = tk.StringVar(value="White")
        bg_combo = ttk.Combobox(right, textvariable=self.bg_var,
                                values=list(BG_COLORS.keys()), width=14, state="readonly")
        bg_combo.pack(pady=2)
        bg_combo.bind("<<ComboboxSelected>>", self._on_style_change)

        tk.Label(right, text="Figure Color:", bg="#16213e", fg="white",
                 font=("Arial", 9)).pack(anchor="w", pady=(5, 0))
        self.fig_var = tk.StringVar(value="Black")
        fig_combo = ttk.Combobox(right, textvariable=self.fig_var,
                                 values=list(FIG_COLORS.keys()), width=14, state="readonly")
        fig_combo.pack(pady=2)
        fig_combo.bind("<<ComboboxSelected>>", self._on_style_change)

        tk.Label(right, text="Speed:", bg="#16213e", fg="white",
                 font=("Arial", 9)).pack(anchor="w", pady=(5, 0))
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_slider = tk.Scale(right, from_=0.5, to=2.5, resolution=0.1,
                                orient="horizontal", variable=self.speed_var,
                                bg="#16213e", fg="white", highlightthickness=0,
                                troughcolor="#e94560", length=130,
                                command=self._on_style_change)
        speed_slider.pack()

        # Bottom timeline
        bottom = tk.Frame(self.root, bg="#0f3460", pady=8)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5))

        tk.Label(bottom, text="TIMELINE:", bg="#0f3460", fg="#e94560",
                 font=("Arial Black", 10, "bold")).pack(side="left", padx=8)

        self.timeline_frame = tk.Frame(bottom, bg="#0f3460")
        self.timeline_frame.pack(side="left", fill="x", expand=True)

        btn_row = tk.Frame(self.root, bg="#1a1a2e")
        btn_row.grid(row=3, column=0, columnspan=2, pady=(0, 10))

        tk.Button(btn_row, text="▶  PLAY PREVIEW", width=16, height=2,
                  bg="#4ecca3", fg="#1a1a2e", font=("Arial Black", 10),
                  relief="flat", cursor="hand2",
                  command=self._play_preview).pack(side="left", padx=6)

        tk.Button(btn_row, text="🗑  CLEAR", width=10, height=2,
                  bg="#555", fg="white", font=("Arial", 10),
                  relief="flat", cursor="hand2",
                  command=self._clear_timeline).pack(side="left", padx=6)

        tk.Button(btn_row, text="💾  EXPORT MP4", width=14, height=2,
                  bg="#e94560", fg="white", font=("Arial Black", 10),
                  relief="flat", cursor="hand2",
                  command=self._export).pack(side="left", padx=6)

    def _add_move(self, move):
        self.timeline.append(move)
        self._refresh_timeline()

    def _refresh_timeline(self):
        for w in self.timeline_frame.winfo_children():
            w.destroy()
        for i, move in enumerate(self.timeline):
            emoji = MOVE_EMOJIS.get(move, "")
            f = tk.Frame(self.timeline_frame, bg="#0f3460")
            f.pack(side="left", padx=2)
            tk.Label(f, text=f"{emoji}{move}", bg="#e94560", fg="white",
                     font=("Arial", 8, "bold"), padx=4, pady=2).pack(side="left")
            tk.Button(f, text="✕", bg="#c73652", fg="white", font=("Arial", 7),
                      relief="flat", cursor="hand2", padx=2,
                      command=lambda idx=i: self._remove_move(idx)).pack(side="left")

    def _remove_move(self, idx):
        if 0 <= idx < len(self.timeline):
            self.timeline.pop(idx)
            self._refresh_timeline()

    def _clear_timeline(self):
        self.timeline.clear()
        self._refresh_timeline()
        self._render_idle()

    def _on_style_change(self, *_):
        self.bg_color = BG_COLORS[self.bg_var.get()]
        self.fig_color = FIG_COLORS[self.fig_var.get()]
        self.speed = self.speed_var.get()
        self._render_idle()

    def _render_idle(self):
        surf = pygame.Surface((CANVAS_W, CANVAS_H))
        surf.fill(self.bg_color)
        draw_figure(surf, POSES["idle"], CANVAS_W // 2, CANVAS_H // 2 + 20,
                    scale=1.1, color=self.fig_color)
        self._show_surface(surf)

    def _show_surface(self, surf):
        raw = pygame.surfarray.array3d(surf)
        import numpy as np
        raw = np.transpose(raw, (1, 0, 2))
        img = Image.fromarray(raw.astype("uint8"), "RGB")
        self._tk_img = ImageTk.PhotoImage(img)
        self.canvas_label.config(image=self._tk_img)

    def _play_preview(self):
        if not self.timeline:
            messagebox.showinfo("Empty", "Add some moves to the timeline first!")
            return
        self.playing = True
        moves = list(self.timeline)
        self.bg_color = BG_COLORS[self.bg_var.get()]
        self.fig_color = FIG_COLORS[self.fig_var.get()]
        self.speed = self.speed_var.get()
        self.all_frames = build_all_frames(moves, self.bg_color, self.fig_color, self.speed)
        self.current_frame = 0

    def _animate_loop(self):
        if self.playing and self.all_frames:
            if self.current_frame < len(self.all_frames):
                self._show_surface(self.all_frames[self.current_frame])
                self.current_frame += 1
            else:
                self.playing = False
        self.root.after(int(1000 / FPS), self._animate_loop)

    def _export(self):
        if not self.timeline:
            messagebox.showinfo("Empty", "Add some moves to the timeline first!")
            return
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        default_path = os.path.join(desktop, "rico_animation.mp4")
        path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4")],
            initialfile="rico_animation.mp4",
            initialdir=desktop,
            title="Save Animation"
        )
        if not path:
            return
        self.bg_color = BG_COLORS[self.bg_var.get()]
        self.fig_color = FIG_COLORS[self.fig_var.get()]
        self.speed = self.speed_var.get()
        frames = build_all_frames(list(self.timeline), self.bg_color, self.fig_color, self.speed)
        messagebox.showinfo("Exporting", "Exporting video... please wait.")
        success = export_mp4(frames, path, fps=FPS)
        if success:
            messagebox.showinfo("Done!", f"Animation saved to:\n{path}")
        else:
            messagebox.showerror("Error", "Export failed. Make sure opencv-python is installed.")


def main():
    root = tk.Tk()
    app = RicoAnimator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
