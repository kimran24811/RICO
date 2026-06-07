
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageDraw, ImageTk

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
MOVE_LABELS = {
    "idle": "🧍 IDLE", "run": "🏃 RUN", "jump": "🦘 JUMP", "land": "⬇ LAND",
    "punch": "👊 PUNCH", "kick": "🦵 KICK", "dodge": "↩ DODGE",
    "spin": "🌀 SPIN", "death": "💀 DEATH",
}


def render_frame(joints, bg_color, fig_color, flash=False):
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), bg_color + (255,))
    draw = ImageDraw.Draw(img, "RGBA")
    draw_figure(draw, joints, CANVAS_W // 2, CANVAS_H // 2 + 20,
                scale=1.1, color=fig_color, flash=flash)
    return img.convert("RGB")


def build_all_frames(move_list, bg_color, fig_color, speed):
    frames = []
    for move in move_list:
        seq = MOVE_SEQUENCES.get(move, MOVE_SEQUENCES["idle"])
        pose_seq = []
        for pose_name, n in seq:
            pose_seq.append((POSES[pose_name], max(2, int(n / speed))))
        tweened = generate_frames(pose_seq)
        flash_moves = {"punch", "kick"}
        mid = len(tweened) // 2
        for i, joints in enumerate(tweened):
            flash = move in flash_moves and i == mid
            frames.append(render_frame(joints, bg_color, fig_color, flash=flash))
    return frames


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
        self._tk_img = None

        self._build_ui()
        self._show_idle()
        self._loop()

    def _build_ui(self):
        tk.Label(self.root, text="⚡ RICO ANIMATOR", bg="#1a1a2e", fg="#e94560",
                 font=("Arial Black", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 4))

        self.canvas_lbl = tk.Label(self.root, bg="#111", bd=3, relief="ridge")
        self.canvas_lbl.grid(row=1, column=0, padx=10, pady=5)

        right = tk.Frame(self.root, bg="#16213e", padx=10, pady=10)
        right.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=5)

        tk.Label(right, text="ACTIONS", bg="#16213e", fg="#e94560",
                 font=("Arial Black", 11, "bold")).pack(pady=(0, 6))

        btn_grid = tk.Frame(right, bg="#16213e")
        btn_grid.pack()
        for i, move in enumerate(MOVE_NAMES):
            tk.Button(btn_grid, text=MOVE_LABELS[move], width=13, height=2,
                      bg="#e94560", fg="white", activebackground="#c73652",
                      font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
                      command=lambda m=move: self._add_move(m)
                      ).grid(row=i // 2, column=i % 2, padx=3, pady=3)

        tk.Label(right, text="STYLE", bg="#16213e", fg="#e94560",
                 font=("Arial Black", 10, "bold")).pack(pady=(12, 2))

        tk.Label(right, text="Background:", bg="#16213e", fg="white",
                 font=("Arial", 9)).pack(anchor="w")
        self.bg_var = tk.StringVar(value="White")
        ttk.Combobox(right, textvariable=self.bg_var, values=list(BG_COLORS),
                     width=14, state="readonly").pack(pady=2)
        self.bg_var.trace_add("write", self._style_changed)

        tk.Label(right, text="Figure Color:", bg="#16213e", fg="white",
                 font=("Arial", 9)).pack(anchor="w", pady=(5, 0))
        self.fig_var = tk.StringVar(value="Black")
        ttk.Combobox(right, textvariable=self.fig_var, values=list(FIG_COLORS),
                     width=14, state="readonly").pack(pady=2)
        self.fig_var.trace_add("write", self._style_changed)

        tk.Label(right, text="Speed:", bg="#16213e", fg="white",
                 font=("Arial", 9)).pack(anchor="w", pady=(5, 0))
        self.speed_var = tk.DoubleVar(value=1.0)
        tk.Scale(right, from_=0.5, to=2.5, resolution=0.1, orient="horizontal",
                 variable=self.speed_var, bg="#16213e", fg="white",
                 highlightthickness=0, troughcolor="#e94560", length=130,
                 command=self._style_changed).pack()

        bottom = tk.Frame(self.root, bg="#0f3460", pady=8)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5))
        tk.Label(bottom, text="TIMELINE:", bg="#0f3460", fg="#e94560",
                 font=("Arial Black", 10, "bold")).pack(side="left", padx=8)
        self.tl_frame = tk.Frame(bottom, bg="#0f3460")
        self.tl_frame.pack(side="left", fill="x", expand=True)

        btns = tk.Frame(self.root, bg="#1a1a2e")
        btns.grid(row=3, column=0, columnspan=2, pady=(0, 12))
        tk.Button(btns, text="▶  PLAY PREVIEW", width=16, height=2,
                  bg="#4ecca3", fg="#1a1a2e", font=("Arial Black", 10),
                  relief="flat", cursor="hand2", command=self._play).pack(side="left", padx=6)
        tk.Button(btns, text="🗑  CLEAR", width=10, height=2,
                  bg="#555", fg="white", font=("Arial", 10),
                  relief="flat", cursor="hand2", command=self._clear).pack(side="left", padx=6)
        tk.Button(btns, text="💾  EXPORT MP4", width=14, height=2,
                  bg="#e94560", fg="white", font=("Arial Black", 10),
                  relief="flat", cursor="hand2", command=self._export).pack(side="left", padx=6)

    def _style_changed(self, *_):
        self.bg_color = BG_COLORS[self.bg_var.get()]
        self.fig_color = FIG_COLORS[self.fig_var.get()]
        self.speed = self.speed_var.get()
        self._show_idle()

    def _add_move(self, move):
        self.timeline.append(move)
        self._refresh_tl()

    def _refresh_tl(self):
        for w in self.tl_frame.winfo_children():
            w.destroy()
        for i, move in enumerate(self.timeline):
            f = tk.Frame(self.tl_frame, bg="#0f3460")
            f.pack(side="left", padx=2)
            tk.Label(f, text=MOVE_LABELS[move], bg="#e94560", fg="white",
                     font=("Arial", 8, "bold"), padx=4, pady=2).pack(side="left")
            tk.Button(f, text="✕", bg="#c73652", fg="white", font=("Arial", 7),
                      relief="flat", cursor="hand2", padx=2,
                      command=lambda idx=i: self._remove(idx)).pack(side="left")

    def _remove(self, idx):
        if 0 <= idx < len(self.timeline):
            self.timeline.pop(idx)
            self._refresh_tl()

    def _clear(self):
        self.timeline.clear()
        self._refresh_tl()
        self._show_idle()

    def _show_pil(self, img):
        self._tk_img = ImageTk.PhotoImage(img)
        self.canvas_lbl.config(image=self._tk_img)

    def _show_idle(self):
        img = render_frame(POSES["idle"], self.bg_color, self.fig_color)
        self._show_pil(img)

    def _play(self):
        if not self.timeline:
            messagebox.showinfo("Empty", "Add some moves to the timeline first!")
            return
        self.bg_color = BG_COLORS[self.bg_var.get()]
        self.fig_color = FIG_COLORS[self.fig_var.get()]
        self.speed = self.speed_var.get()
        self.all_frames = build_all_frames(self.timeline, self.bg_color, self.fig_color, self.speed)
        self.current_frame = 0
        self.playing = True

    def _loop(self):
        if self.playing and self.all_frames:
            if self.current_frame < len(self.all_frames):
                self._show_pil(self.all_frames[self.current_frame])
                self.current_frame += 1
            else:
                self.playing = False
        self.root.after(int(1000 / FPS), self._loop)

    def _export(self):
        if not self.timeline:
            messagebox.showinfo("Empty", "Add some moves to the timeline first!")
            return
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = filedialog.asksaveasfilename(
            defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4")],
            initialfile="rico_animation.mp4", initialdir=desktop, title="Save Animation")
        if not path:
            return
        self.bg_color = BG_COLORS[self.bg_var.get()]
        self.fig_color = FIG_COLORS[self.fig_var.get()]
        self.speed = self.speed_var.get()
        frames = build_all_frames(self.timeline, self.bg_color, self.fig_color, self.speed)
        messagebox.showinfo("Exporting", "Exporting... please wait a moment.")
        if export_mp4(frames, path, fps=FPS):
            messagebox.showinfo("Done!", f"Animation saved!\n{path}")
        else:
            messagebox.showerror("Error", "Export failed. Make sure opencv-python is installed.")


def main():
    root = tk.Tk()
    RicoAnimator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
