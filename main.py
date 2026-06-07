
import os
import sys
import json
import copy
import math
import random
import threading
from collections import deque
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk, ImageFont, ImageFilter

from animator.poses import POSES, MOVE_SEQUENCES
from animator.tween import generate_frames, EASINGS
from animator.figure import draw_figure
from animator.effects import (draw_speed_lines, get_shake_offset,
                               draw_sfx, ParticleSystem)
from animator.backgrounds import build_background, SCENE_BUILDERS
from animator.sprite import SpriteEntry, composite_sprite
from gui.exporter import export_mp4, export_gif, export_png_sequence
from project.save_load import save_project, load_project, COMBOS

CANVAS_W = 680
CANVAS_H = 500
FPS_DEFAULT = 24

FIG_COLORS = {
    "Black":  (20,  20,  20),
    "White":  (235, 235, 235),
    "Red":    (210, 40,  40),
    "Blue":   (40,  90,  210),
    "Green":  (40,  170, 80),
    "Gold":   (210, 160, 30),
    "Purple": (140, 40,  200),
    "Cyan":   (30,  190, 210),
    "Orange": (230, 110, 30),
}

MOVE_GROUPS = {
    "Basic":    ["idle", "run", "jump", "land", "guard"],
    "Attack":   ["punch", "kick", "uppercut", "spin"],
    "Special":  ["flip", "slide", "walljump", "dodge"],
    "Finisher": ["taunt", "death"],
}
MOVE_ICONS = {
    "idle": "🧍", "run": "🏃", "jump": "🦘", "land": "⬇",
    "punch": "👊", "kick": "🦵", "uppercut": "⬆", "spin": "🌀",
    "flip": "🔄", "slide": "💨", "walljump": "🧱", "dodge": "↩",
    "taunt": "😎", "guard": "🛡", "death": "💀",
}
FAST_MOVES  = {"punch", "kick", "uppercut", "spin"}
FLASH_MOVES = {"punch", "kick", "uppercut"}
GLOW_MOVES  = {"spin", "flip"}
DUST_MOVES  = {"land", "slide"}
SPARK_MOVES = {"punch", "kick", "uppercut"}
SMOKE_MOVES = {"spin", "flip"}
SHAKE_MOVES = {"punch", "kick", "uppercut", "death"}

SPRITE_MODES = ["bounce", "run_along", "spin", "float", "fight", "slam"]


# ── Rendering ─────────────────────────────────────────────────────────────────

def render_frame(joints, bg_name, fig_color, frame_index=0,
                 flash=False, glow=False, blur_trail=False,
                 shake_offset=(0, 0), speed_lines=False,
                 particles=None, sfx_events=None,
                 sprites=None, total_frames=1,
                 onion_img=None, onion_alpha=0.3,
                 scale=1.25, x_offset=0, custom_bg_img=None):

    base_img = build_background(bg_name, CANVAS_W, CANVAS_H, custom_bg_img)
    img = base_img.convert("RGBA")

    # Onion skin ghost
    if onion_img is not None:
        ghost = onion_img.convert("RGBA")
        ghost.putalpha(int(255 * onion_alpha))
        img = Image.alpha_composite(img, ghost)

    draw = ImageDraw.Draw(img, "RGBA")

    cx = CANVAS_W // 2 + x_offset + shake_offset[0]
    cy = int(CANVAS_H * 0.58) + shake_offset[1]

    if speed_lines:
        speed_img = img.convert("RGBA")
        draw_speed_lines(speed_img, cx, cy, "right", intensity=0.8)
        img = speed_img

    draw = ImageDraw.Draw(img, "RGBA")
    draw_figure(draw, joints, cx, cy, scale=scale,
                color=fig_color, flash=flash, shadow=True, glow=glow)

    # Particles
    if particles:
        particles.draw(img)

    # SFX labels
    if sfx_events:
        rgb = img.convert("RGB")
        for ev in sfx_events:
            draw_sfx(rgb, ev["text"], ev["x"], ev["y"])
        img = rgb.convert("RGBA")

    result = img.convert("RGB")

    # Sprites on top
    if sprites:
        for sp in sprites:
            result = composite_sprite(result, sp, frame_index, total_frames,
                                      joints, CANVAS_W, CANVAS_H)

    if blur_trail:
        result = result.filter(ImageFilter.GaussianBlur(radius=1))

    return result


def build_all_frames(timeline_entries, bg_name, fig_color, speed,
                     loop=False, onion=False, camera_shake=True,
                     speed_lines_on=True, particles_on=True,
                     scale=1.25, x_offset=0, custom_bg_img=None,
                     sfx_events=None, sprites=None):

    all_frames = []
    psys = ParticleSystem() if particles_on else None

    for entry in timeline_entries:
        move      = entry["move"]
        repeat    = entry.get("repeat", 1)
        easing    = entry.get("easing", "smooth")

        seq_def = MOVE_SEQUENCES.get(move, MOVE_SEQUENCES["idle"])

        for _rep in range(repeat):
            pose_seq = []
            for pd in seq_def:
                pname = pd[0]
                n     = max(2, int(pd[1] / speed))
                pose_seq.append((POSES[pname], n, easing))

            tweened = generate_frames(pose_seq)
            total   = len(tweened)
            mid     = total // 2

            for i, joints in enumerate(tweened):
                flash  = move in FLASH_MOVES and abs(i - mid) < 3
                glow   = move in GLOW_MOVES
                blur   = move in FAST_MOVES and abs(i - mid) < 5
                use_sl = speed_lines_on and move in FAST_MOVES and abs(i - mid) < 6
                shake  = (0, 0)
                if camera_shake and move in SHAKE_MOVES and abs(i - mid) < 8:
                    shake = get_shake_offset(abs(i - mid), intensity=6)

                if psys and particles_on:
                    ankle_j = joints.get("r_ankle", (0, 40))
                    floor_y = int(CANVAS_H * 0.58)
                    ax = int(CANVAS_W // 2 + ankle_j[0] * 1.25 + x_offset)
                    ay = int(floor_y + ankle_j[1] * 1.25)
                    if move in DUST_MOVES and i < 6:
                        psys.emit_dust(ax, ay, count=10)
                    wrist_j = joints.get("r_wrist", (0, -50))
                    wx = int(CANVAS_W // 2 + wrist_j[0] * 1.25)
                    wy = int(floor_y + wrist_j[1] * 1.25)
                    if move in SPARK_MOVES and abs(i - mid) < 3:
                        psys.emit_sparks(wx, wy, count=14)
                    if move in SMOKE_MOVES and i % 4 == 0:
                        psys.emit_smoke(CANVAS_W // 2, floor_y - 60)
                    psys.update()

                onion_img = all_frames[-1] if onion and all_frames else None

                frame_sfx = None
                if sfx_events:
                    fi = len(all_frames)
                    frame_sfx = [e for e in sfx_events
                                 if e.get("frame") == fi]

                frame = render_frame(
                    joints, bg_name, fig_color,
                    frame_index=len(all_frames),
                    flash=flash, glow=glow, blur_trail=blur,
                    shake_offset=shake, speed_lines=use_sl,
                    particles=psys if particles_on else None,
                    sfx_events=frame_sfx,
                    sprites=sprites,
                    total_frames=9999,
                    onion_img=onion_img,
                    onion_alpha=0.25,
                    scale=scale, x_offset=x_offset,
                    custom_bg_img=custom_bg_img,
                )
                all_frames.append(frame)

    if loop and len(all_frames) > 2:
        all_frames = all_frames + list(reversed(all_frames[1:-1]))

    return all_frames


# ── Tooltip ───────────────────────────────────────────────────────────────────

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, "bbox") else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, bg="#1f2937", fg="#f9fafb",
                 font=("Arial", 9), relief="solid", bd=1,
                 padx=6, pady=3).pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ── Main App ──────────────────────────────────────────────────────────────────

class RicoAnimator:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ RICO ANIMATOR — Pro Edition")
        self.root.configure(bg="#0d0d1a")
        self.root.resizable(True, True)
        self.root.minsize(1100, 700)

        # State
        self.timeline      = []        # list of dicts: {move, repeat, easing}
        self.undo_stack    = deque(maxlen=50)
        self.redo_stack    = deque(maxlen=50)
        self.all_frames    = []
        self.current_frame = 0
        self.playing       = False
        self.sfx_events    = []        # {text, x, y, frame}
        self.sprites       = []        # list of SpriteEntry
        self.custom_bg_img = None
        self._tk_img       = None
        self._onion_frame  = None

        # Vars
        self.bg_var        = tk.StringVar(value="White")
        self.fig_var       = tk.StringVar(value="Black")
        self.speed_var     = tk.DoubleVar(value=1.0)
        self.fps_var       = tk.IntVar(value=24)
        self.scale_var     = tk.DoubleVar(value=1.25)
        self.xoff_var      = tk.IntVar(value=0)
        self.loop_var      = tk.BooleanVar(value=False)
        self.onion_var     = tk.BooleanVar(value=False)
        self.shake_var     = tk.BooleanVar(value=True)
        self.particles_var = tk.BooleanVar(value=True)
        self.speedlines_var= tk.BooleanVar(value=True)
        self.easing_var    = tk.StringVar(value="smooth")

        self._build_ui()
        self._show_idle()
        self._loop()
        self.root.bind("<Control-z>", self._undo)
        self.root.bind("<Control-y>", self._redo)
        self.root.bind("<Control-s>", lambda e: self._save_project())
        self.root.bind("<space>", lambda e: self._toggle_play())

    # ── UI Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Menu bar
        menubar = tk.Menu(self.root, bg="#1f2937", fg="white", relief="flat")
        self.root.config(menu=menubar)
        fm = tk.Menu(menubar, tearoff=0, bg="#1f2937", fg="white")
        menubar.add_cascade(label="File", menu=fm)
        fm.add_command(label="💾 Save Project  Ctrl+S", command=self._save_project)
        fm.add_command(label="📂 Load Project",         command=self._load_project)
        fm.add_separator()
        fm.add_command(label="❌ Exit",                  command=self.root.destroy)

        em = tk.Menu(menubar, tearoff=0, bg="#1f2937", fg="white")
        menubar.add_cascade(label="Edit", menu=em)
        em.add_command(label="↩ Undo  Ctrl+Z", command=self._undo)
        em.add_command(label="↪ Redo  Ctrl+Y", command=self._redo)
        em.add_command(label="🗑 Clear Timeline", command=self._clear)

        hm = tk.Menu(menubar, tearoff=0, bg="#1f2937", fg="white")
        menubar.add_cascade(label="Help", menu=hm)
        hm.add_command(label="📖 Quick Guide", command=self._show_help)

        # Header
        hdr = tk.Frame(self.root, bg="#0d0d1a")
        hdr.pack(fill="x", padx=12, pady=(6, 2))
        tk.Label(hdr, text="⚡  RICO ANIMATOR  —  Pro Edition",
                 bg="#0d0d1a", fg="#e94560",
                 font=("Arial Black", 14, "bold")).pack(side="left")
        tk.Button(hdr, text="💾 Save", bg="#1f2937", fg="white", relief="flat",
                  font=("Arial", 9), cursor="hand2",
                  command=self._save_project).pack(side="right", padx=4)
        tk.Button(hdr, text="📂 Load", bg="#1f2937", fg="white", relief="flat",
                  font=("Arial", 9), cursor="hand2",
                  command=self._load_project).pack(side="right", padx=4)

        # Main area
        main = tk.Frame(self.root, bg="#0d0d1a")
        main.pack(fill="both", expand=True, padx=8)

        # Canvas
        left = tk.Frame(main, bg="#0d0d1a")
        left.pack(side="left", fill="both", expand=True)

        self.canvas_lbl = tk.Label(left, bg="#111", bd=2, relief="ridge",
                                   cursor="crosshair")
        self.canvas_lbl.pack(pady=4)

        # Status
        sf = tk.Frame(left, bg="#111827")
        sf.pack(fill="x")
        self.status_var = tk.StringVar(value="Ready — add moves below and press PLAY ▶")
        tk.Label(sf, textvariable=self.status_var, bg="#111827",
                 fg="#9ca3af", font=("Consolas", 9)).pack(side="left", padx=8, pady=2)
        self.frame_var = tk.StringVar(value="Frame 0 / 0")
        tk.Label(sf, textvariable=self.frame_var, bg="#111827",
                 fg="#6b7280", font=("Consolas", 9)).pack(side="right", padx=8)

        # Right scrollable panel
        right_outer = tk.Frame(main, bg="#0d0d1a", width=280)
        right_outer.pack(side="right", fill="y", padx=(8, 0))
        right_outer.pack_propagate(False)

        canvas_r = tk.Canvas(right_outer, bg="#111827", highlightthickness=0)
        sb_r = tk.Scrollbar(right_outer, orient="vertical", command=canvas_r.yview)
        canvas_r.configure(yscrollcommand=sb_r.set)
        sb_r.pack(side="right", fill="y")
        canvas_r.pack(side="left", fill="both", expand=True)

        self.right_panel = tk.Frame(canvas_r, bg="#111827")
        canvas_r.create_window((0, 0), window=self.right_panel, anchor="nw", width=260)
        self.right_panel.bind("<Configure>",
            lambda e: canvas_r.configure(scrollregion=canvas_r.bbox("all")))

        self._build_move_panel()
        self._build_combo_panel()
        self._build_style_panel()
        self._build_effects_panel()
        self._build_image_panel()
        self._build_sfx_panel()
        self._build_playback_panel()

        # Timeline
        self._build_timeline()

        # Bottom buttons
        self._build_bottom_buttons()

    def _section_label(self, text):
        f = tk.Frame(self.right_panel, bg="#111827")
        f.pack(fill="x", padx=6, pady=(10, 2))
        tk.Label(f, text=text, bg="#111827", fg="#e94560",
                 font=("Arial Black", 10, "bold")).pack(side="left")
        tk.Frame(f, bg="#374151", height=1).pack(side="left", fill="x",
                                                  expand=True, padx=(8, 0))

    def _build_move_panel(self):
        self._section_label("🎬  MOVES")

        # Easing for new moves
        ef = tk.Frame(self.right_panel, bg="#111827")
        ef.pack(fill="x", padx=6, pady=(0, 4))
        tk.Label(ef, text="Easing:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 8)).pack(side="left")
        cb = ttk.Combobox(ef, textvariable=self.easing_var,
                          values=list(EASINGS.keys()), width=10, state="readonly")
        cb.pack(side="left", padx=4)
        Tooltip(cb, "How the movement accelerates/decelerates")

        nb = ttk.Notebook(self.right_panel)
        nb.pack(fill="x", padx=4, pady=2)
        s = ttk.Style()
        s.configure("TNotebook",     background="#111827", borderwidth=0)
        s.configure("TNotebook.Tab", background="#1f2937", foreground="#9ca3af",
                    font=("Arial", 8, "bold"), padding=[5, 2])
        s.map("TNotebook.Tab", background=[("selected", "#e94560")],
              foreground=[("selected", "white")])

        for group, moves in MOVE_GROUPS.items():
            tab = tk.Frame(nb, bg="#111827", pady=2)
            nb.add(tab, text=group)
            for i, move in enumerate(moves):
                icon = MOVE_ICONS.get(move, "")
                btn = tk.Button(tab, text=f"{icon} {move.upper()}",
                                width=11, height=2,
                                bg="#1f2937", fg="#f3f4f6",
                                activebackground="#e94560", activeforeground="white",
                                font=("Arial", 8, "bold"), relief="flat",
                                cursor="hand2",
                                command=lambda m=move: self._add_move(m))
                btn.grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")
                Tooltip(btn, f"Add {move} to timeline")

    def _build_combo_panel(self):
        self._section_label("🔥  COMBOS")
        f = tk.Frame(self.right_panel, bg="#111827")
        f.pack(fill="x", padx=6, pady=2)
        self.combo_var = tk.StringVar(value=list(COMBOS.keys())[0])
        cb = ttk.Combobox(f, textvariable=self.combo_var,
                          values=list(COMBOS.keys()), width=18, state="readonly")
        cb.pack(side="left", padx=2)
        btn = tk.Button(f, text="Add Combo ➕", bg="#7c3aed", fg="white",
                        font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
                        command=self._add_combo)
        btn.pack(side="left", padx=4)
        Tooltip(btn, "Add a predefined combo sequence to timeline")

    def _build_style_panel(self):
        self._section_label("🎨  STYLE")
        p = self.right_panel

        tk.Label(p, text="Background Scene:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w", padx=8)
        cb = ttk.Combobox(p, textvariable=self.bg_var,
                          values=list(SCENE_BUILDERS.keys()), width=20, state="readonly")
        cb.pack(padx=8, pady=2, fill="x")
        self.bg_var.trace_add("write", self._on_style)
        Tooltip(cb, "Choose a background scene")

        tk.Button(p, text="🖼 Import Custom Background", bg="#1f2937", fg="#9ca3af",
                  font=("Arial", 8), relief="flat", cursor="hand2",
                  command=self._import_bg).pack(padx=8, pady=2, fill="x")

        tk.Label(p, text="Figure Color:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w", padx=8, pady=(6, 0))
        cb2 = ttk.Combobox(p, textvariable=self.fig_var,
                           values=list(FIG_COLORS.keys()), width=20, state="readonly")
        cb2.pack(padx=8, pady=2, fill="x")
        self.fig_var.trace_add("write", self._on_style)

        tk.Label(p, text="Animation Speed:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w", padx=8, pady=(6, 0))
        sp = tk.Scale(p, from_=0.2, to=3.0, resolution=0.1, orient="horizontal",
                      variable=self.speed_var, bg="#111827", fg="white",
                      highlightthickness=0, troughcolor="#e94560", length=220,
                      command=self._on_style)
        sp.pack(padx=8)
        Tooltip(sp, "Higher = faster animation")

        tk.Label(p, text="Figure Size:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w", padx=8, pady=(4, 0))
        tk.Scale(p, from_=0.5, to=2.5, resolution=0.05, orient="horizontal",
                 variable=self.scale_var, bg="#111827", fg="white",
                 highlightthickness=0, troughcolor="#4ecca3", length=220,
                 command=self._on_style).pack(padx=8)

        tk.Label(p, text="Horizontal Position:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w", padx=8, pady=(4, 0))
        tk.Scale(p, from_=-200, to=200, resolution=5, orient="horizontal",
                 variable=self.xoff_var, bg="#111827", fg="white",
                 highlightthickness=0, troughcolor="#4ecca3", length=220,
                 command=self._on_style).pack(padx=8)

    def _build_effects_panel(self):
        self._section_label("✨  EFFECTS")
        p = self.right_panel
        checks = [
            (self.shake_var,      "Camera Shake on impacts"),
            (self.particles_var,  "Particles (dust, sparks, smoke)"),
            (self.speedlines_var, "Speed Lines on fast moves"),
            (self.onion_var,      "Onion Skin (ghost trail)"),
        ]
        for var, label in checks:
            f = tk.Frame(p, bg="#111827")
            f.pack(fill="x", padx=8, pady=1)
            cb = tk.Checkbutton(f, text=label, variable=var,
                                bg="#111827", fg="#d1d5db",
                                selectcolor="#374151", activebackground="#111827",
                                activeforeground="white", font=("Arial", 9),
                                cursor="hand2")
            cb.pack(side="left")

    def _build_image_panel(self):
        self._section_label("🖼  IMAGE SPRITE")
        p = self.right_panel

        info = tk.Label(p, text="Import any image and animate it!",
                        bg="#111827", fg="#6b7280", font=("Arial", 8),
                        wraplength=230, justify="left")
        info.pack(anchor="w", padx=8, pady=(0, 4))

        self.sprite_thumb = tk.Label(p, bg="#1f2937", width=8, height=4,
                                     relief="groove", text="No image",
                                     fg="#6b7280", font=("Arial", 8))
        self.sprite_thumb.pack(padx=8, pady=2, anchor="w")

        tk.Button(p, text="📁 Import Image (PNG/JPG)",
                  bg="#7c3aed", fg="white", font=("Arial", 9, "bold"),
                  relief="flat", cursor="hand2",
                  command=self._import_sprite).pack(padx=8, pady=2, fill="x")

        tk.Label(p, text="Animation Style:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w", padx=8, pady=(4, 0))
        self.sprite_mode_var = tk.StringVar(value="bounce")
        sm = ttk.Combobox(p, textvariable=self.sprite_mode_var,
                          values=SPRITE_MODES, width=18, state="readonly")
        sm.pack(padx=8, pady=2, fill="x")
        Tooltip(sm, "How the image moves during animation:\nbounce=up/down, run_along=side to side\nfight=follows punch hand, spin=rotates")

        tk.Label(p, text="Image Size:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w", padx=8, pady=(4, 0))
        self.sprite_scale_var = tk.DoubleVar(value=1.0)
        tk.Scale(p, from_=0.2, to=2.0, resolution=0.05, orient="horizontal",
                 variable=self.sprite_scale_var, bg="#111827", fg="white",
                 highlightthickness=0, troughcolor="#7c3aed", length=220).pack(padx=8)

        self.remove_bg_var = tk.BooleanVar(value=False)
        tk.Checkbutton(p, text="Remove white background", variable=self.remove_bg_var,
                       bg="#111827", fg="#d1d5db", selectcolor="#374151",
                       activebackground="#111827", font=("Arial", 9),
                       cursor="hand2").pack(anchor="w", padx=8, pady=2)

        self._pending_sprite_img = None
        self._pending_sprite_path = None

        tk.Button(p, text="✨ ANIMATE IT!",
                  bg="#e94560", fg="white", font=("Arial Black", 11),
                  relief="flat", cursor="hand2", height=2,
                  command=self._add_sprite).pack(padx=8, pady=6, fill="x")

        # Active sprites list
        tk.Label(p, text="Active Sprites:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 8)).pack(anchor="w", padx=8)
        self.sprite_list_frame = tk.Frame(p, bg="#111827")
        self.sprite_list_frame.pack(fill="x", padx=8)

    def _build_sfx_panel(self):
        self._section_label("💥  SFX LABELS")
        p = self.right_panel
        tk.Label(p, text="Add comic-style text at a frame:",
                 bg="#111827", fg="#6b7280", font=("Arial", 8)).pack(anchor="w", padx=8)

        f = tk.Frame(p, bg="#111827")
        f.pack(fill="x", padx=8, pady=2)
        self.sfx_text_var = tk.StringVar(value="POW!")
        sfx_texts = list(["POW!", "BAM!", "WHAM!", "WHOOSH!", "CRACK!", "KA-POW!", "UGH!", "DODGE!"])
        ttk.Combobox(f, textvariable=self.sfx_text_var,
                     values=sfx_texts, width=10, state="readonly").pack(side="left", padx=2)

        tk.Label(f, text="at frame:", bg="#111827", fg="#9ca3af",
                 font=("Arial", 8)).pack(side="left", padx=4)
        self.sfx_frame_var = tk.IntVar(value=0)
        tk.Spinbox(f, from_=0, to=9999, textvariable=self.sfx_frame_var,
                   width=5, bg="#1f2937", fg="white",
                   insertbackground="white").pack(side="left")

        tk.Button(p, text="Add SFX Label", bg="#374151", fg="white",
                  font=("Arial", 9), relief="flat", cursor="hand2",
                  command=self._add_sfx).pack(padx=8, pady=2, fill="x")

        self.sfx_list_frame = tk.Frame(p, bg="#111827")
        self.sfx_list_frame.pack(fill="x", padx=8)

    def _build_playback_panel(self):
        self._section_label("▶  PLAYBACK")
        p = self.right_panel

        tk.Label(p, text="Frames Per Second (FPS):", bg="#111827", fg="#9ca3af",
                 font=("Arial", 9)).pack(anchor="w", padx=8)
        tk.Scale(p, from_=8, to=60, resolution=1, orient="horizontal",
                 variable=self.fps_var, bg="#111827", fg="white",
                 highlightthickness=0, troughcolor="#4ecca3", length=220).pack(padx=8)

        tk.Checkbutton(p, text="Loop animation (ping-pong)",
                       variable=self.loop_var,
                       bg="#111827", fg="#d1d5db", selectcolor="#374151",
                       activebackground="#111827", font=("Arial", 9),
                       cursor="hand2").pack(anchor="w", padx=8, pady=4)

    def _build_timeline(self):
        outer = tk.Frame(self.root, bg="#0d0d1a")
        outer.pack(fill="x", padx=8, pady=(4, 0))

        tk.Label(outer, text="⏱  TIMELINE", bg="#0d0d1a", fg="#e94560",
                 font=("Arial Black", 9, "bold")).pack(side="left", padx=(0, 8))

        tl_bg = tk.Frame(outer, bg="#1f2937", height=58, relief="sunken", bd=1)
        tl_bg.pack(side="left", fill="x", expand=True)

        cv = tk.Canvas(tl_bg, bg="#1f2937", height=58, highlightthickness=0)
        cv.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(tl_bg, orient="horizontal", command=cv.xview)
        sb.pack(side="bottom", fill="x")
        cv.configure(xscrollcommand=sb.set)

        self.tl_inner = tk.Frame(cv, bg="#1f2937")
        cv.create_window((0, 0), window=self.tl_inner, anchor="nw")
        self.tl_inner.bind("<Configure>",
            lambda e: cv.configure(scrollregion=cv.bbox("all")))

    def _build_bottom_buttons(self):
        row = tk.Frame(self.root, bg="#0d0d1a")
        row.pack(pady=8)
        btns = [
            ("▶  PLAY",           "#4ecca3", "#0d0d1a", self._play),
            ("⏸  PAUSE",          "#6b7280", "white",   self._stop),
            ("🗑  CLEAR",          "#374151", "white",   self._clear),
            ("⬅  UNDO  Ctrl+Z",   "#1f2937", "#9ca3af", self._undo),
            ("➡  REDO  Ctrl+Y",   "#1f2937", "#9ca3af", self._redo),
            ("💾  Export MP4",     "#e94560", "white",   self._export_mp4),
            ("🎞  Export GIF",     "#7c3aed", "white",   self._export_gif),
            ("📷  Export Frames",  "#059669", "white",   self._export_png),
        ]
        for text, bg, fg, cmd in btns:
            tk.Button(row, text=text, height=2, padx=10,
                      bg=bg, fg=fg, activebackground=bg,
                      font=("Arial", 9, "bold"), relief="flat",
                      cursor="hand2", command=cmd).pack(side="left", padx=3)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_style(self, *_):
        self._show_idle()

    def _push_undo(self):
        self.undo_stack.append(copy.deepcopy(self.timeline))
        self.redo_stack.clear()

    def _undo(self, _=None):
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(self.timeline))
            self.timeline = self.undo_stack.pop()
            self._refresh_tl()
            self.status_var.set("Undo")

    def _redo(self, _=None):
        if self.redo_stack:
            self.undo_stack.append(copy.deepcopy(self.timeline))
            self.timeline = self.redo_stack.pop()
            self._refresh_tl()
            self.status_var.set("Redo")

    def _add_move(self, move):
        self._push_undo()
        self.timeline.append({
            "move":   move,
            "repeat": 1,
            "easing": self.easing_var.get(),
        })
        self._refresh_tl()
        self.status_var.set(f"Added {MOVE_ICONS.get(move,'')} {move.upper()}  "
                            f"—  {len(self.timeline)} move(s)")

    def _add_combo(self):
        combo_name = self.combo_var.get()
        moves = COMBOS.get(combo_name, [])
        self._push_undo()
        for m in moves:
            self.timeline.append({"move": m, "repeat": 1, "easing": "smooth"})
        self._refresh_tl()
        self.status_var.set(f"Added combo: {combo_name}  ({len(moves)} moves)")

    def _refresh_tl(self):
        for w in self.tl_inner.winfo_children():
            w.destroy()
        for i, entry in enumerate(self.timeline):
            move   = entry["move"]
            repeat = entry.get("repeat", 1)
            icon   = MOVE_ICONS.get(move, "")
            cell   = tk.Frame(self.tl_inner, bg="#374151", padx=1)
            cell.pack(side="left", padx=2, pady=6)

            tk.Label(cell, text=f"{icon} {move.upper()}",
                     bg="#e94560", fg="white",
                     font=("Arial", 8, "bold"),
                     padx=5, pady=3).pack(side="left")

            # Repeat
            if repeat > 1:
                tk.Label(cell, text=f"×{repeat}",
                         bg="#991b1b", fg="#fca5a5",
                         font=("Arial", 8)).pack(side="left")

            tk.Button(cell, text="+", bg="#1f2937", fg="#9ca3af",
                      font=("Arial", 7), relief="flat", padx=2,
                      cursor="hand2",
                      command=lambda idx=i: self._change_repeat(idx, 1)
                      ).pack(side="left")
            tk.Button(cell, text="−", bg="#1f2937", fg="#9ca3af",
                      font=("Arial", 7), relief="flat", padx=2,
                      cursor="hand2",
                      command=lambda idx=i: self._change_repeat(idx, -1)
                      ).pack(side="left")
            tk.Button(cell, text="✕", bg="#7f1d1d", fg="white",
                      font=("Arial", 7), relief="flat", padx=2,
                      cursor="hand2",
                      command=lambda idx=i: self._remove(idx)
                      ).pack(side="left")

    def _change_repeat(self, idx, delta):
        if 0 <= idx < len(self.timeline):
            self._push_undo()
            self.timeline[idx]["repeat"] = max(1, self.timeline[idx].get("repeat", 1) + delta)
            self._refresh_tl()

    def _remove(self, idx):
        if 0 <= idx < len(self.timeline):
            self._push_undo()
            self.timeline.pop(idx)
            self._refresh_tl()

    def _clear(self):
        self._push_undo()
        self.timeline.clear()
        self.all_frames.clear()
        self.playing = False
        self._refresh_tl()
        self._show_idle()
        self.status_var.set("Timeline cleared")
        self.frame_var.set("Frame 0 / 0")

    def _toggle_play(self):
        if self.playing:
            self._stop()
        else:
            self._play()

    # ── Image & Sprite ────────────────────────────────────────────────────────

    def _import_sprite(self):
        path = filedialog.askopenfilename(
            title="Import Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.webp *.gif")])
        if not path:
            return
        try:
            img = Image.open(path)
            # Fit thumbnail
            thumb = img.copy()
            thumb.thumbnail((80, 64))
            self._tk_thumb = ImageTk.PhotoImage(thumb)
            self.sprite_thumb.config(image=self._tk_thumb, text="", bg="#1f2937")
            self._pending_sprite_img  = img
            self._pending_sprite_path = path
            self.status_var.set(f"Image loaded: {os.path.basename(path)} — "
                                f"choose style and press ANIMATE IT!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image:\n{e}")

    def _add_sprite(self):
        if self._pending_sprite_img is None:
            messagebox.showinfo("No Image", "Import an image first using the Import button.")
            return
        if len(self.sprites) >= 3:
            messagebox.showinfo("Limit", "Maximum 3 active sprites. Remove one first.")
            return
        entry = SpriteEntry(
            path=self._pending_sprite_path,
            pil_image=self._pending_sprite_img.copy(),
            animation_mode=self.sprite_mode_var.get(),
            base_scale=self.sprite_scale_var.get(),
            remove_bg=self.remove_bg_var.get(),
            bg_tolerance=30,
        )
        self.sprites.append(entry)
        self._refresh_sprite_list()
        self.status_var.set(f"Sprite added with '{entry.animation_mode}' mode — press PLAY!")

    def _refresh_sprite_list(self):
        for w in self.sprite_list_frame.winfo_children():
            w.destroy()
        for i, sp in enumerate(self.sprites):
            f = tk.Frame(self.sprite_list_frame, bg="#374151")
            f.pack(fill="x", pady=1)
            name = os.path.basename(sp.path)[:18]
            tk.Label(f, text=f"🖼 {name} [{sp.animation_mode}]",
                     bg="#374151", fg="#d1d5db",
                     font=("Arial", 8)).pack(side="left", padx=4)
            tk.Button(f, text="✕", bg="#7f1d1d", fg="white",
                      font=("Arial", 7), relief="flat", cursor="hand2",
                      command=lambda idx=i: self._remove_sprite(idx)
                      ).pack(side="right", padx=2)

    def _remove_sprite(self, idx):
        if 0 <= idx < len(self.sprites):
            self.sprites.pop(idx)
            self._refresh_sprite_list()

    def _import_bg(self):
        path = filedialog.askopenfilename(
            title="Import Background Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if not path:
            return
        try:
            self.custom_bg_img = Image.open(path).convert("RGB")
            self.bg_var.set("Custom Image")
            self.status_var.set(f"Background set: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image:\n{e}")

    # ── SFX ───────────────────────────────────────────────────────────────────

    def _add_sfx(self):
        text  = self.sfx_text_var.get()
        frame = self.sfx_frame_var.get()
        ev = {"text": text, "x": 60, "y": 50, "frame": frame}
        self.sfx_events.append(ev)
        self._refresh_sfx_list()
        self.status_var.set(f"SFX '{text}' added at frame {frame}")

    def _refresh_sfx_list(self):
        for w in self.sfx_list_frame.winfo_children():
            w.destroy()
        for i, ev in enumerate(self.sfx_events):
            f = tk.Frame(self.sfx_list_frame, bg="#374151")
            f.pack(fill="x", pady=1)
            tk.Label(f, text=f"💥 {ev['text']} @ fr{ev['frame']}",
                     bg="#374151", fg="#fbbf24", font=("Arial", 8)).pack(side="left", padx=4)
            tk.Button(f, text="✕", bg="#7f1d1d", fg="white",
                      font=("Arial", 7), relief="flat", cursor="hand2",
                      command=lambda idx=i: self._remove_sfx(idx)
                      ).pack(side="right", padx=2)

    def _remove_sfx(self, idx):
        if 0 <= idx < len(self.sfx_events):
            self.sfx_events.pop(idx)
            self._refresh_sfx_list()

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _show_pil(self, img):
        self._tk_img = ImageTk.PhotoImage(img)
        self.canvas_lbl.config(image=self._tk_img)

    def _show_idle(self):
        bg  = self.bg_var.get()
        fig = FIG_COLORS.get(self.fig_var.get(), (20, 20, 20))
        sc  = self.scale_var.get()
        xo  = self.xoff_var.get()
        img = render_frame(POSES["idle"], bg, fig, scale=sc, x_offset=xo,
                           custom_bg_img=self.custom_bg_img)
        self._show_pil(img)

    def _play(self):
        if not self.timeline:
            messagebox.showinfo("Empty", "Add some moves to the timeline first!")
            return
        self.status_var.set("Building frames… please wait")
        self.root.update_idletasks()
        frames = build_all_frames(
            self.timeline,
            bg_name=self.bg_var.get(),
            fig_color=FIG_COLORS.get(self.fig_var.get(), (20, 20, 20)),
            speed=self.speed_var.get(),
            loop=self.loop_var.get(),
            onion=self.onion_var.get(),
            camera_shake=self.shake_var.get(),
            speed_lines_on=self.speedlines_var.get(),
            particles_on=self.particles_var.get(),
            scale=self.scale_var.get(),
            x_offset=self.xoff_var.get(),
            custom_bg_img=self.custom_bg_img,
            sfx_events=self.sfx_events,
            sprites=self.sprites,
        )
        self.all_frames    = frames
        self.current_frame = 0
        self.playing       = True
        self.status_var.set(f"Playing — {len(frames)} frames  (Space to pause)")

    def _stop(self):
        self.playing = False
        self.status_var.set("Paused — press Play to resume or Export to save")

    def _loop(self):
        if self.playing and self.all_frames:
            if self.current_frame < len(self.all_frames):
                self._show_pil(self.all_frames[self.current_frame])
                self.frame_var.set(
                    f"Frame {self.current_frame+1} / {len(self.all_frames)}")
                self.current_frame += 1
            else:
                if self.loop_var.get():
                    self.current_frame = 0
                else:
                    self.playing = False
                    self.status_var.set("✅ Done — press Export to save your video!")
        interval = max(16, int(1000 / self.fps_var.get()))
        self.root.after(interval, self._loop)

    # ── Export ────────────────────────────────────────────────────────────────

    def _get_frames(self):
        if not self.timeline:
            messagebox.showinfo("Empty", "Add some moves to the timeline first!")
            return None
        self.status_var.set("Rendering frames…")
        self.root.update_idletasks()
        return build_all_frames(
            self.timeline,
            bg_name=self.bg_var.get(),
            fig_color=FIG_COLORS.get(self.fig_var.get(), (20, 20, 20)),
            speed=self.speed_var.get(),
            loop=self.loop_var.get(),
            onion=False,
            camera_shake=self.shake_var.get(),
            speed_lines_on=self.speedlines_var.get(),
            particles_on=self.particles_var.get(),
            scale=self.scale_var.get(),
            x_offset=self.xoff_var.get(),
            custom_bg_img=self.custom_bg_img,
            sfx_events=self.sfx_events,
            sprites=self.sprites,
        )

    def _export_mp4(self):
        frames = self._get_frames()
        if not frames:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4")],
            initialfile="rico_animation.mp4",
            initialdir=os.path.expanduser("~/Desktop"),
            title="Save MP4")
        if not path:
            return
        self.status_var.set("Exporting MP4…")
        self.root.update_idletasks()
        if export_mp4(frames, path, fps=self.fps_var.get()):
            self.status_var.set(f"✅ Saved: {os.path.basename(path)}")
            messagebox.showinfo("Done!", f"MP4 saved!\n{path}")
            try:
                os.startfile(os.path.dirname(path))
            except Exception:
                pass
        else:
            messagebox.showerror("Error", "MP4 export failed.")

    def _export_gif(self):
        frames = self._get_frames()
        if not frames:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF", "*.gif")],
            initialfile="rico_animation.gif",
            initialdir=os.path.expanduser("~/Desktop"),
            title="Save GIF")
        if not path:
            return
        self.status_var.set("Exporting GIF…")
        self.root.update_idletasks()
        if export_gif(frames, path, fps=self.fps_var.get()):
            self.status_var.set(f"✅ Saved: {os.path.basename(path)}")
            messagebox.showinfo("Done!", f"GIF saved!\n{path}")
            try:
                os.startfile(os.path.dirname(path))
            except Exception:
                pass
        else:
            messagebox.showerror("Error", "GIF export failed.")

    def _export_png(self):
        frames = self._get_frames()
        if not frames:
            return
        folder = filedialog.askdirectory(title="Select folder for PNG frames",
                                         initialdir=os.path.expanduser("~/Desktop"))
        if not folder:
            return
        self.status_var.set("Exporting PNG frames…")
        self.root.update_idletasks()
        out_folder = os.path.join(folder, "rico_frames")
        if export_png_sequence(frames, out_folder):
            self.status_var.set(f"✅ {len(frames)} frames saved to rico_frames/")
            messagebox.showinfo("Done!", f"PNG frames saved!\n{out_folder}")
            try:
                os.startfile(out_folder)
            except Exception:
                pass

    # ── Save / Load ───────────────────────────────────────────────────────────

    def _save_project(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".rico",
            filetypes=[("RICO Project", "*.rico"), ("JSON", "*.json")],
            initialfile="my_animation.rico",
            initialdir=os.path.expanduser("~/Desktop"),
            title="Save Project")
        if not path:
            return
        state = {
            "timeline":    self.timeline,
            "bg":          self.bg_var.get(),
            "fig_color":   self.fig_var.get(),
            "speed":       self.speed_var.get(),
            "fps":         self.fps_var.get(),
            "scale":       self.scale_var.get(),
            "xoffset":     self.xoff_var.get(),
            "loop":        self.loop_var.get(),
            "easing":      self.easing_var.get(),
            "shake":       self.shake_var.get(),
            "particles":   self.particles_var.get(),
            "speedlines":  self.speedlines_var.get(),
            "onion":       self.onion_var.get(),
            "sfx_events":  self.sfx_events,
            "sprites":     [s.to_dict() for s in self.sprites],
        }
        try:
            save_project(path, state)
            self.status_var.set(f"✅ Project saved: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed:\n{e}")

    def _load_project(self):
        path = filedialog.askopenfilename(
            filetypes=[("RICO Project", "*.rico"), ("JSON", "*.json")],
            title="Load Project")
        if not path:
            return
        try:
            state = load_project(path)
            self.timeline = state.get("timeline", [])
            self.bg_var.set(state.get("bg", "White"))
            self.fig_var.set(state.get("fig_color", "Black"))
            self.speed_var.set(state.get("speed", 1.0))
            self.fps_var.set(state.get("fps", 24))
            self.scale_var.set(state.get("scale", 1.25))
            self.xoff_var.set(state.get("xoffset", 0))
            self.loop_var.set(state.get("loop", False))
            self.easing_var.set(state.get("easing", "smooth"))
            self.shake_var.set(state.get("shake", True))
            self.particles_var.set(state.get("particles", True))
            self.speedlines_var.set(state.get("speedlines", True))
            self.onion_var.set(state.get("onion", False))
            self.sfx_events = state.get("sfx_events", [])
            # Reload sprites
            self.sprites = []
            for sd in state.get("sprites", []):
                p = sd.get("path", "")
                if os.path.exists(p):
                    try:
                        img = Image.open(p)
                        sp = SpriteEntry(p, img,
                                         sd.get("animation_mode", "bounce"),
                                         sd.get("base_scale", 1.0),
                                         sd.get("x_offset", 0),
                                         sd.get("y_offset", 0))
                        self.sprites.append(sp)
                    except Exception:
                        pass
            self._refresh_tl()
            self._refresh_sfx_list()
            self._refresh_sprite_list()
            self._show_idle()
            self.status_var.set(f"✅ Project loaded: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Load failed:\n{e}")

    # ── Help ──────────────────────────────────────────────────────────────────

    def _show_help(self):
        win = tk.Toplevel(self.root)
        win.title("Quick Guide — RICO Animator")
        win.configure(bg="#111827")
        win.geometry("500x520")
        text = (
            "⚡ RICO ANIMATOR — Pro Edition Quick Guide\n"
            "═══════════════════════════════════════════\n\n"
            "1️⃣  ADDING MOVES\n"
            "   Click any button in the MOVES panel (Basic / Attack / Special / Finisher)\n"
            "   Or pick a combo from the COMBOS dropdown and click 'Add Combo'\n\n"
            "2️⃣  TIMELINE\n"
            "   Your moves appear at the bottom.\n"
            "   + / − buttons change how many times each move repeats.\n"
            "   ✕ removes a move. Ctrl+Z to undo.\n\n"
            "3️⃣  STYLE\n"
            "   Change background scene, figure color, speed, size, and position.\n"
            "   Import your own background image with 'Import Custom Background'.\n\n"
            "4️⃣  EFFECTS\n"
            "   Camera Shake, Particles (dust/sparks/smoke), Speed Lines, Onion Skin\n"
            "   — all auto-applied based on the move type. Toggle each on/off.\n\n"
            "5️⃣  IMAGE SPRITE\n"
            "   Click 'Import Image' → choose any PNG or JPG.\n"
            "   Pick an animation style:\n"
            "   • bounce  = image bobs up/down\n"
            "   • run_along = slides across screen\n"
            "   • fight   = follows the punch hand!\n"
            "   • spin    = rotates full 360°\n"
            "   • float   = gentle floating drift\n"
            "   Click ANIMATE IT! — your image moves with the animation.\n\n"
            "6️⃣  SFX LABELS\n"
            "   Add POW!, BAM!, WHOOSH! text at any frame number.\n\n"
            "7️⃣  EXPORT\n"
            "   MP4 = video file  |  GIF = animated image  |  PNG Frames = image sequence\n"
            "   File opens automatically after saving.\n\n"
            "8️⃣  SAVE / LOAD\n"
            "   File → Save Project saves your whole animation as a .rico file.\n"
            "   Load it later to continue where you left off.\n\n"
            "⌨️  SHORTCUTS\n"
            "   Space = Play/Pause  |  Ctrl+Z = Undo  |  Ctrl+Y = Redo  |  Ctrl+S = Save"
        )
        t = tk.Text(win, bg="#111827", fg="#e5e7eb", font=("Consolas", 10),
                    padx=16, pady=12, relief="flat", wrap="word")
        t.insert("1.0", text)
        t.config(state="disabled")
        t.pack(fill="both", expand=True)
        tk.Button(win, text="Close", bg="#e94560", fg="white",
                  font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
                  command=win.destroy).pack(pady=8)


def main():
    root = tk.Tk()
    RicoAnimator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
