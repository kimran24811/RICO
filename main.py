
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from PIL import Image, ImageDraw, ImageTk, ImageFilter

from animator.poses import POSES, MOVE_SEQUENCES
from animator.tween import generate_frames
from animator.figure import draw_figure
from gui.exporter import export_mp4

CANVAS_W = 640
CANVAS_H = 480
FPS = 24

BACKGROUNDS = {
    "White":       (255, 255, 255),
    "Black":       (12,  12,  18),
    "Dojo":        (30,  20,  10),
    "City Night":  (10,  14,  40),
    "Red Arena":   (60,  10,  10),
    "Forest":      (15,  40,  20),
}
FIG_COLORS = {
    "Black":  (20,  20,  20),
    "White":  (235, 235, 235),
    "Red":    (210, 40,  40),
    "Blue":   (40,  90,  210),
    "Green":  (40,  170, 80),
    "Gold":   (210, 160, 30),
    "Purple": (140, 40,  200),
}

MOVE_GROUPS = {
    "Basic": ["idle", "run", "jump", "land", "guard"],
    "Attack": ["punch", "kick", "uppercut", "spin"],
    "Special": ["flip", "slide", "walljump", "dodge"],
    "Finisher": ["taunt", "death"],
}

MOVE_ICONS = {
    "idle": "🧍", "run": "🏃", "jump": "🦘", "land": "⬇",
    "punch": "👊", "kick": "🦵", "uppercut": "⬆", "spin": "🌀",
    "flip": "🔄", "slide": "💨", "walljump": "🧱", "dodge": "↩",
    "taunt": "😎", "guard": "🛡", "death": "💀",
}

FAST_MOVES = {"punch", "kick", "uppercut", "spin"}
FLASH_MOVES = {"punch", "kick", "uppercut"}
GLOW_MOVES  = {"spin", "flip"}


def render_frame(joints, bg_color, fig_color, flash=False, glow=False, blur_trail=False):
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), bg_color + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # Ground line
    gy = int(CANVAS_H * 0.82)
    gc = tuple(max(0, c - 20) for c in bg_color)
    draw.line([(0, gy), (CANVAS_W, gy)], fill=gc + (180,), width=2)

    draw_figure(draw, joints, CANVAS_W // 2, int(CANVAS_H * 0.55),
                scale=1.25, color=fig_color, flash=flash, shadow=True, glow=glow)

    result = img.convert("RGB")
    if blur_trail:
        result = result.filter(ImageFilter.GaussianBlur(radius=1))
    return result


def build_all_frames(move_list, bg_color, fig_color, speed, loop=False):
    frames = []
    for move in move_list:
        seq_def = MOVE_SEQUENCES.get(move, MOVE_SEQUENCES["idle"])
        pose_seq = []
        for entry in seq_def:
            pose_name = entry[0]
            n = entry[1]
            mode = entry[2] if len(entry) > 2 else "smooth"
            adjusted = max(2, int(n / speed))
            pose_seq.append((POSES[pose_name], adjusted, mode))

        tweened = generate_frames(pose_seq)
        total = len(tweened)
        mid = total // 2

        for i, joints in enumerate(tweened):
            flash = move in FLASH_MOVES and abs(i - mid) < 3
            glow  = move in GLOW_MOVES
            blur  = move in FAST_MOVES and abs(i - mid) < 4
            frames.append(render_frame(joints, bg_color, fig_color,
                                       flash=flash, glow=glow, blur_trail=blur))

    if loop and frames:
        frames = frames + list(reversed(frames[1:-1]))
    return frames


class RicoAnimator:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ RICO ANIMATOR — Advanced Edition")
        self.root.configure(bg="#0d0d1a")
        self.root.resizable(True, True)

        self.timeline  = []
        self.all_frames = []
        self.current_frame = 0
        self.playing   = False
        self.loop_var  = tk.BooleanVar(value=False)
        self.bg_color  = (255, 255, 255)
        self.fig_color = (20, 20, 20)
        self.speed     = 1.0
        self.fps_var   = tk.IntVar(value=24)
        self._tk_img   = None
        self._after_id = None

        self._build_ui()
        self._show_idle()
        self._loop()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Title bar
        tk.Label(self.root, text="⚡  RICO ANIMATOR  —  Advanced Edition",
                 bg="#0d0d1a", fg="#e94560",
                 font=("Arial Black", 15, "bold")).pack(pady=(10, 4))

        main = tk.Frame(self.root, bg="#0d0d1a")
        main.pack(fill="both", expand=True, padx=10)

        # Left: canvas
        left = tk.Frame(main, bg="#0d0d1a")
        left.pack(side="left", fill="both", expand=True)

        self.canvas_lbl = tk.Label(left, bg="#111", bd=2, relief="ridge",
                                   cursor="crosshair")
        self.canvas_lbl.pack(pady=4)

        # Canvas status bar
        status = tk.Frame(left, bg="#111827")
        status.pack(fill="x")
        self.status_var = tk.StringVar(value="Ready — add moves and press Play")
        tk.Label(status, textvariable=self.status_var, bg="#111827",
                 fg="#9ca3af", font=("Consolas", 9)).pack(side="left", padx=6, pady=2)
        self.frame_var = tk.StringVar(value="Frame: 0 / 0")
        tk.Label(status, textvariable=self.frame_var, bg="#111827",
                 fg="#6b7280", font=("Consolas", 9)).pack(side="right", padx=6)

        # Right panel
        right = tk.Frame(main, bg="#111827", padx=8, pady=8, width=240)
        right.pack(side="right", fill="y", padx=(8, 0))
        right.pack_propagate(False)

        self._build_action_panel(right)
        self._build_style_panel(right)
        self._build_playback_panel(right)

        # Bottom timeline
        self._build_timeline()

        # Bottom buttons
        self._build_bottom_buttons()

    def _section(self, parent, title):
        tk.Label(parent, text=title, bg="#111827", fg="#e94560",
                 font=("Arial Black", 10, "bold")).pack(pady=(10, 4), anchor="w")

    def _build_action_panel(self, parent):
        self._section(parent, "MOVES")
        nb = ttk.Notebook(parent)
        nb.pack(fill="x")

        style = ttk.Style()
        style.configure("TNotebook", background="#111827", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1f2937", foreground="#9ca3af",
                        font=("Arial", 8, "bold"), padding=[6, 3])
        style.map("TNotebook.Tab", background=[("selected", "#e94560")],
                  foreground=[("selected", "white")])

        for group, moves in MOVE_GROUPS.items():
            tab = tk.Frame(nb, bg="#111827", pady=4)
            nb.add(tab, text=group)
            for i, move in enumerate(moves):
                icon = MOVE_ICONS.get(move, "")
                tk.Button(tab, text=f"{icon} {move.upper()}",
                          width=12, height=2,
                          bg="#1f2937", fg="#f3f4f6",
                          activebackground="#e94560", activeforeground="white",
                          font=("Arial", 9, "bold"), relief="flat",
                          cursor="hand2", bd=0,
                          command=lambda m=move: self._add_move(m)
                          ).grid(row=i // 2, column=i % 2, padx=3, pady=2)

    def _build_style_panel(self, parent):
        self._section(parent, "STYLE")

        tk.Label(parent, text="Background:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w")
        self.bg_var = tk.StringVar(value="White")
        ttk.Combobox(parent, textvariable=self.bg_var, values=list(BACKGROUNDS),
                     width=16, state="readonly").pack(fill="x", pady=2)
        self.bg_var.trace_add("write", self._style_changed)

        tk.Label(parent, text="Figure Color:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w", pady=(6, 0))
        self.fig_var = tk.StringVar(value="Black")
        ttk.Combobox(parent, textvariable=self.fig_var, values=list(FIG_COLORS),
                     width=16, state="readonly").pack(fill="x", pady=2)
        self.fig_var.trace_add("write", self._style_changed)

        tk.Label(parent, text="Speed:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w", pady=(6, 0))
        self.speed_var = tk.DoubleVar(value=1.0)
        tk.Scale(parent, from_=0.3, to=3.0, resolution=0.1, orient="horizontal",
                 variable=self.speed_var, bg="#111827", fg="white",
                 highlightthickness=0, troughcolor="#e94560", length=190,
                 command=self._style_changed).pack()

    def _build_playback_panel(self, parent):
        self._section(parent, "PLAYBACK")

        tk.Label(parent, text="FPS:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w")
        tk.Scale(parent, from_=8, to=60, resolution=1, orient="horizontal",
                 variable=self.fps_var, bg="#111827", fg="white",
                 highlightthickness=0, troughcolor="#4ecca3", length=190).pack()

        tk.Checkbutton(parent, text="Loop animation",
                       variable=self.loop_var,
                       bg="#111827", fg="#9ca3af",
                       selectcolor="#1f2937",
                       activebackground="#111827",
                       font=("Arial", 9)).pack(anchor="w", pady=4)

    def _build_timeline(self):
        tl_outer = tk.Frame(self.root, bg="#0d0d1a")
        tl_outer.pack(fill="x", padx=10, pady=(4, 0))

        tk.Label(tl_outer, text="TIMELINE", bg="#0d0d1a", fg="#e94560",
                 font=("Arial Black", 9, "bold")).pack(side="left", padx=(0, 8))

        tl_scroll_frame = tk.Frame(tl_outer, bg="#1f2937", height=52, relief="sunken", bd=1)
        tl_scroll_frame.pack(side="left", fill="x", expand=True)

        canvas_tl = tk.Canvas(tl_scroll_frame, bg="#1f2937", height=52,
                              highlightthickness=0)
        canvas_tl.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(tl_scroll_frame, orient="horizontal",
                          command=canvas_tl.xview)
        sb.pack(side="bottom", fill="x")
        canvas_tl.configure(xscrollcommand=sb.set)

        self.tl_inner = tk.Frame(canvas_tl, bg="#1f2937")
        canvas_tl.create_window((0, 0), window=self.tl_inner, anchor="nw")
        self.tl_inner.bind("<Configure>",
            lambda e: canvas_tl.configure(scrollregion=canvas_tl.bbox("all")))
        self._tl_canvas = canvas_tl

    def _build_bottom_buttons(self):
        row = tk.Frame(self.root, bg="#0d0d1a")
        row.pack(pady=8)

        btns = [
            ("▶  PLAY", "#4ecca3", "#0d0d1a", self._play),
            ("⏹  STOP", "#6b7280", "white",   self._stop),
            ("🗑  CLEAR", "#374151", "white",  self._clear),
            ("💾  EXPORT MP4", "#e94560", "white", self._export),
            ("🖼  EXPORT GIF", "#7c3aed", "white", self._export_gif),
        ]
        for text, bg, fg, cmd in btns:
            tk.Button(row, text=text, height=2, padx=14,
                      bg=bg, fg=fg, activebackground=bg,
                      font=("Arial Black", 9), relief="flat",
                      cursor="hand2", command=cmd).pack(side="left", padx=4)

    # ── State ─────────────────────────────────────────────────────────────────

    def _style_changed(self, *_):
        self.bg_color  = BACKGROUNDS[self.bg_var.get()]
        self.fig_color = FIG_COLORS[self.fig_var.get()]
        self.speed     = self.speed_var.get()
        self._show_idle()

    def _add_move(self, move):
        self.timeline.append(move)
        self._refresh_tl()
        self.status_var.set(f"Added: {move.upper()}  |  {len(self.timeline)} move(s) in timeline")

    def _refresh_tl(self):
        for w in self.tl_inner.winfo_children():
            w.destroy()
        for i, move in enumerate(self.timeline):
            icon = MOVE_ICONS.get(move, "")
            cell = tk.Frame(self.tl_inner, bg="#374151", padx=1)
            cell.pack(side="left", padx=2, pady=4)
            tk.Label(cell, text=f"{icon} {move.upper()}", bg="#e94560", fg="white",
                     font=("Arial", 8, "bold"), padx=5, pady=3).pack(side="left")
            tk.Button(cell, text="✕", bg="#991b1b", fg="white", font=("Arial", 7),
                      relief="flat", cursor="hand2", padx=2,
                      command=lambda idx=i: self._remove(idx)).pack(side="left")

    def _remove(self, idx):
        if 0 <= idx < len(self.timeline):
            self.timeline.pop(idx)
            self._refresh_tl()

    def _clear(self):
        self.timeline.clear()
        self.all_frames.clear()
        self.playing = False
        self._refresh_tl()
        self._show_idle()
        self.status_var.set("Timeline cleared")
        self.frame_var.set("Frame: 0 / 0")

    def _show_pil(self, img):
        self._tk_img = ImageTk.PhotoImage(img)
        self.canvas_lbl.config(image=self._tk_img)

    def _show_idle(self):
        bg  = BACKGROUNDS.get(self.bg_var.get(), (255, 255, 255))
        fig = FIG_COLORS.get(self.fig_var.get(), (20, 20, 20))
        img = render_frame(POSES["idle"], bg, fig)
        self._show_pil(img)

    def _play(self):
        if not self.timeline:
            messagebox.showinfo("Empty", "Add some moves to the timeline first!")
            return
        self.status_var.set("Building frames…")
        self.root.update_idletasks()
        self.bg_color  = BACKGROUNDS[self.bg_var.get()]
        self.fig_color = FIG_COLORS[self.fig_var.get()]
        self.speed     = self.speed_var.get()
        self.all_frames = build_all_frames(
            self.timeline, self.bg_color, self.fig_color,
            self.speed, loop=self.loop_var.get())
        self.current_frame = 0
        self.playing = True
        self.status_var.set(f"Playing — {len(self.all_frames)} frames")

    def _stop(self):
        self.playing = False
        self.status_var.set("Stopped")

    def _loop(self):
        if self.playing and self.all_frames:
            if self.current_frame < len(self.all_frames):
                self._show_pil(self.all_frames[self.current_frame])
                self.frame_var.set(
                    f"Frame: {self.current_frame+1} / {len(self.all_frames)}")
                self.current_frame += 1
            else:
                if self.loop_var.get():
                    self.current_frame = 0
                else:
                    self.playing = False
                    self.status_var.set("Done — ready to export")
        interval = max(16, int(1000 / self.fps_var.get()))
        self.root.after(interval, self._loop)

    def _export(self):
        self._do_export("mp4")

    def _export_gif(self):
        self._do_export("gif")

    def _do_export(self, fmt):
        if not self.timeline:
            messagebox.showinfo("Empty", "Add some moves to the timeline first!")
            return
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        ext = f".{fmt}"
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f"{fmt.upper()} file", f"*{ext}")],
            initialfile=f"rico_animation{ext}",
            initialdir=desktop, title="Save Animation")
        if not path:
            return
        self.bg_color  = BACKGROUNDS[self.bg_var.get()]
        self.fig_color = FIG_COLORS[self.fig_var.get()]
        self.speed     = self.speed_var.get()
        self.status_var.set("Rendering frames…")
        self.root.update_idletasks()
        frames = build_all_frames(self.timeline, self.bg_color, self.fig_color,
                                  self.speed, loop=self.loop_var.get())
        self.status_var.set("Exporting…")
        self.root.update_idletasks()

        if fmt == "mp4":
            from gui.exporter import export_mp4
            ok = export_mp4(frames, path, fps=self.fps_var.get())
        else:
            ok = self._save_gif(frames, path)

        if ok:
            self.status_var.set(f"Saved: {os.path.basename(path)}")
            messagebox.showinfo("Done!", f"Animation saved!\n{path}")
        else:
            messagebox.showerror("Error", "Export failed.")

    def _save_gif(self, frames, path):
        try:
            dur = int(1000 / self.fps_var.get())
            frames[0].save(path, save_all=True, append_images=frames[1:],
                           loop=0, duration=dur, optimize=False)
            return True
        except Exception as e:
            print(e)
            return False


def main():
    root = tk.Tk()
    RicoAnimator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
