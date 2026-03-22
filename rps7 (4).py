"""
PIEDRA · PAPEL · TIJERA · LAGARTO · SPOCK · FUEGO · AGUA
7 Variables — 2 Jugadores o vs CPU
"""

import tkinter as tk
from tkinter import ttk
import random, datetime

# ═══════════════════════════════════════════════════════════════
#  DATOS DEL JUEGO
# ═══════════════════════════════════════════════════════════════

CHOICES = ["Piedra", "Papel", "Tijera", "Lagarto", "Spock", "Fuego", "Agua"]

EMOJIS = {
    "Piedra":  "✊", "Papel": "✋", "Tijera": "✌️",
    "Lagarto": "🦎", "Spock": "🖖", "Fuego":  "🔥", "Agua": "💧",
}

COLORS = {
    "Piedra": "#8B7355", "Papel":   "#4A9EBD", "Tijera":  "#C0392B",
    "Lagarto":"#27AE60", "Spock":   "#8E44AD", "Fuego":   "#E67E22",
    "Agua":   "#2980B9",
}

LIGHT_COLORS = {
    "Piedra": "#D4C5AA", "Papel":   "#ADE4F5", "Tijera":  "#F1948A",
    "Lagarto":"#82E0AA", "Spock":   "#C39BD3", "Fuego":   "#FAD7A0",
    "Agua":   "#85C1E9",
}

WINS = {
    "Piedra":  [("Tijera","aplasta la Tijera"),   ("Lagarto","aplasta al Lagarto"), ("Fuego","apaga el Fuego")],
    "Papel":   [("Piedra","cubre la Piedra"),      ("Spock","desaprueba a Spock"),   ("Agua","absorbe el Agua")],
    "Tijera":  [("Papel","corta el Papel"),        ("Lagarto","decapita al Lagarto"),("Fuego","corta el Fuego")],
    "Lagarto": [("Spock","envenena a Spock"),      ("Papel","come el Papel"),        ("Agua","bebe el Agua")],
    "Spock":   [("Tijera","destruye la Tijera"),   ("Piedra","vaporiza la Piedra"),  ("Fuego","dispersa el Fuego")],
    "Fuego":   [("Papel","quema el Papel"),        ("Lagarto","quema al Lagarto"),   ("Agua","evapora el Agua")],
    "Agua":    [("Piedra","erosiona la Piedra"),   ("Tijera","oxida la Tijera"),     ("Spock","apaga a Spock")],
}

CPU_MSGS = ["🧠 Calculando...", "👀 Analizando...", "⚙️ Procesando...", "🎯 Eligiendo..."]

# Récords solo en memoria — se pierden al cerrar
_RECORDS = []


def load_records():
    return list(_RECORDS)


def save_record(entry):
    _RECORDS.append(entry)
    _RECORDS.sort(key=lambda r: r.get("wins", 0), reverse=True)
    del _RECORDS[50:]



def get_result(a, b):
    if a == b:
        return "tie", ""
    for loser, phrase in WINS[a]:
        if loser == b:
            return "win", phrase
    for loser, phrase in WINS[b]:
        if loser == a:
            return "lose", phrase
    return "tie", ""


def cpu_choose(history):
    """50% contrarresta la jugada mas frecuente del humano, 50% aleatoria."""
    if not history or random.random() < 0.5:
        return random.choice(CHOICES)
    most = max(set(history), key=history.count)
    beaters = [c for c, vs in WINS.items() if any(v[0] == most for v in vs)]
    return random.choice(beaters) if beaters else random.choice(CHOICES)


# ═══════════════════════════════════════════════════════════════
#  PALETA / HELPERS
# ═══════════════════════════════════════════════════════════════

BG     = "#0F1923"
BG2    = "#182232"
BG3    = "#1E2D42"
ACCENT = "#00D4AA"
ACC2   = "#FF6B6B"
GOLD   = "#FFD700"
PURP   = "#8E44AD"
TEXT   = "#E8EDF3"
TEXTL  = "#7A9BB5"
BORDER = "#2A3F55"
FS     = ("Segoe UI", 11)


def _lt(h, f=1.15):
    h = h.lstrip("#")
    return "#{:02x}{:02x}{:02x}".format(
        min(255, int(int(h[0:2], 16) * f)),
        min(255, int(int(h[2:4], 16) * f)),
        min(255, int(int(h[4:6], 16) * f)))


def mkbtn(parent, text, cmd, bg, fg=None, **kw):
    fg = fg or (BG if bg not in (BG, BG2, BG3, "#718096") else TEXT)
    kw.setdefault("padx", 14)
    kw.setdefault("pady", 7)
    kw.setdefault("font", ("Segoe UI", 11, "bold"))
    b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                  relief="flat", cursor="hand2",
                  activebackground=_lt(bg), activeforeground=fg, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=_lt(bg)))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


# ═══════════════════════════════════════════════════════════════
#  BOTÓN DE ELECCIÓN
# ═══════════════════════════════════════════════════════════════

class ChoiceBtn(tk.Frame):
    def __init__(self, parent, choice, on_click, accent):
        super().__init__(parent, bg=BG3, cursor="hand2",
                         highlightbackground=BORDER, highlightthickness=1)
        self.choice = choice
        self._sel   = False
        self._e = tk.Label(self, text=EMOJIS[choice], bg=BG3, font=("Segoe UI Emoji", 26))
        self._e.pack(pady=(6, 1))
        self._n = tk.Label(self, text=choice, bg=BG3, fg=TEXTL, font=("Segoe UI", 9, "bold"))
        self._n.pack(pady=(0, 6))
        for w in [self, self._e, self._n]:
            w.bind("<Button-1>", lambda e, c=choice: on_click(c))
            w.bind("<Enter>", self._hi)
            w.bind("<Leave>", self._lo)

    def _hi(self, e=None):
        if not self._sel:
            lc = LIGHT_COLORS[self.choice]
            self.config(bg=lc, highlightbackground=COLORS[self.choice])
            self._e.config(bg=lc)
            self._n.config(bg=lc)

    def _lo(self, e=None):
        if not self._sel:
            self.config(bg=BG3, highlightbackground=BORDER)
            self._e.config(bg=BG3)
            self._n.config(bg=BG3, fg=TEXTL)

    def select(self, on):
        self._sel = on
        if on:
            lc = LIGHT_COLORS[self.choice]
            self.config(bg=lc, highlightbackground=COLORS[self.choice])
            self._e.config(bg=lc)
            self._n.config(bg=lc, fg=BG)
        else:
            self._lo()
            self._n.config(fg=TEXTL)

    def bounce(self):
        steps = [2, 5, 8, 5, 2, 0]
        def step(i=0):
            if not self.winfo_exists():
                return
            if i < len(steps):
                self._e.config(pady=steps[i])
                self.after(40, lambda: step(i + 1))
            else:
                self._e.config(pady=0)
        step()


# ═══════════════════════════════════════════════════════════════
#  PANTALLA 1 — REGISTRO
# ═══════════════════════════════════════════════════════════════

class RegistroScreen(tk.Frame):
    def __init__(self, master, on_start):
        super().__init__(master, bg=BG)
        self.on_start = on_start
        self._mode    = "2p"
        self._p2_box  = None
        self._build()

    def _build(self):
        self._cv = tk.Canvas(self, bg=BG, highlightthickness=0)
        self._cv.place(relwidth=1, relheight=1)
        self._ptcls = [{"e": random.choice(list(EMOJIS.values())),
                        "x": random.randint(0, 1200), "y": random.randint(0, 800),
                        "dx": random.uniform(-.5, .5), "dy": random.uniform(-.8, -.2)}
                       for _ in range(28)]
        self._tick_particles()

        box = tk.Frame(self, bg=BG2)
        box.place(relx=.5, rely=.5, anchor="center", width=610, height=610)
        tk.Frame(box, bg=ACCENT, height=4).pack(fill=tk.X)

        tk.Label(box, text="✊ ✋ ✌️", bg=BG2, fg=ACCENT,
                 font=("Segoe UI Emoji", 28)).pack(pady=(12, 2))
        tk.Label(box, text="PIEDRA PAPEL TIJERA", bg=BG2, fg=TEXT,
                 font=("Segoe UI", 21, "bold")).pack()
        tk.Label(box, text="7 VARIABLES  ·  🦎 🖖 🔥 💧", bg=BG2, fg=TEXTL,
                 font=("Segoe UI Emoji", 13)).pack(pady=(2, 8))
        tk.Frame(box, bg=BORDER, height=1).pack(fill=tk.X, padx=28, pady=3)

        # Selector de modo
        mf = tk.Frame(box, bg=BG2)
        mf.pack(pady=7)
        tk.Label(mf, text="Modo:", bg=BG2, fg=TEXTL, font=FS).pack(side=tk.LEFT, padx=8)
        self._btn2p  = mkbtn(mf, "👥 2 Jugadores", lambda: self._set_mode("2p"),  ACCENT, padx=12, pady=5)
        self._btncpu = mkbtn(mf, "🤖 vs CPU",       lambda: self._set_mode("cpu"), BG3,    padx=12, pady=5)
        self._btn2p.pack(side=tk.LEFT, padx=4)
        self._btncpu.pack(side=tk.LEFT, padx=4)

        # Paneles jugadores
        pf = tk.Frame(box, bg=BG2)
        pf.pack(fill=tk.X, padx=28, pady=8)
        pf.columnconfigure(0, weight=1)
        pf.columnconfigure(1, weight=1)

        self.p1_name   = tk.StringVar()
        self.p2_name   = tk.StringVar()
        self.p1_gender = tk.StringVar(value="Masculino")
        self.p2_gender = tk.StringVar(value="Femenino")

        self._build_p1(pf)
        self._p2_col = tk.Frame(pf, bg=BG2)
        self._p2_col.grid(row=0, column=1, padx=6, sticky="nsew")
        self._draw_p2_human()

        tk.Frame(box, bg=BORDER, height=1).pack(fill=tk.X, padx=28, pady=6)

        # Rondas
        rf = tk.Frame(box, bg=BG2)
        rf.pack()
        tk.Label(rf, text="Rondas:", bg=BG2, fg=TEXTL, font=FS).pack(side=tk.LEFT, padx=8)
        self._rondas = tk.IntVar(value=5)
        for r in [3, 5, 7, 10]:
            tk.Radiobutton(rf, text=str(r), variable=self._rondas, value=r,
                           bg=BG2, fg=TEXT, selectcolor=BG2,
                           activebackground=BG2, activeforeground=ACCENT,
                           font=("Segoe UI", 12, "bold"), cursor="hand2").pack(side=tk.LEFT, padx=6)

        sb = mkbtn(box, "⚡  COMENZAR  ⚡", self._start, ACCENT, padx=32, pady=11,
                   font=("Segoe UI", 14, "bold"))
        sb.pack(pady=14)

    def _build_p1(self, parent):
        fr = tk.Frame(parent, bg=BG3)
        fr.grid(row=0, column=0, padx=6, sticky="nsew")
        tk.Frame(fr, bg=ACCENT, height=3).pack(fill=tk.X)
        tk.Label(fr, text="🎮 Jugador 1", bg=BG3, fg=ACCENT,
                 font=("Segoe UI", 12, "bold")).pack(pady=(10, 4))
        tk.Label(fr, text="Nombre:", bg=BG3, fg=TEXTL, font=FS).pack(anchor="w", padx=14)
        tk.Entry(fr, textvariable=self.p1_name, font=("Segoe UI", 12),
                 bg=BG2, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=0, highlightthickness=1,
                 highlightcolor=ACCENT, highlightbackground=BORDER
                 ).pack(fill=tk.X, padx=14, ipady=6, pady=(2, 10))
        tk.Label(fr, text="Género:", bg=BG3, fg=TEXTL, font=FS).pack(anchor="w", padx=14)
        gf = tk.Frame(fr, bg=BG3)
        gf.pack(padx=14, pady=(2, 14), anchor="w")
        for g in ["Masculino", "Femenino", "Otro"]:
            tk.Radiobutton(gf, text=g, variable=self.p1_gender, value=g,
                           bg=BG3, fg=TEXT, selectcolor=BG3,
                           activebackground=BG3, activeforeground=ACCENT,
                           font=FS, cursor="hand2").pack(side=tk.LEFT, padx=3)

    def _draw_p2_human(self):
        if self._p2_box:
            self._p2_box.destroy()
        fr = tk.Frame(self._p2_col, bg=BG3)
        fr.pack(fill=tk.BOTH, expand=True)
        self._p2_box = fr
        tk.Frame(fr, bg=ACC2, height=3).pack(fill=tk.X)
        tk.Label(fr, text="🎮 Jugador 2", bg=BG3, fg=ACC2,
                 font=("Segoe UI", 12, "bold")).pack(pady=(10, 4))
        tk.Label(fr, text="Nombre:", bg=BG3, fg=TEXTL, font=FS).pack(anchor="w", padx=14)
        tk.Entry(fr, textvariable=self.p2_name, font=("Segoe UI", 12),
                 bg=BG2, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=0, highlightthickness=1,
                 highlightcolor=ACC2, highlightbackground=BORDER
                 ).pack(fill=tk.X, padx=14, ipady=6, pady=(2, 10))
        tk.Label(fr, text="Género:", bg=BG3, fg=TEXTL, font=FS).pack(anchor="w", padx=14)
        gf = tk.Frame(fr, bg=BG3)
        gf.pack(padx=14, pady=(2, 14), anchor="w")
        for g in ["Masculino", "Femenino", "Otro"]:
            tk.Radiobutton(gf, text=g, variable=self.p2_gender, value=g,
                           bg=BG3, fg=TEXT, selectcolor=BG3,
                           activebackground=BG3, activeforeground=ACC2,
                           font=FS, cursor="hand2").pack(side=tk.LEFT, padx=3)

    def _draw_p2_cpu(self):
        if self._p2_box:
            self._p2_box.destroy()
        fr = tk.Frame(self._p2_col, bg=BG3)
        fr.pack(fill=tk.BOTH, expand=True)
        self._p2_box = fr
        tk.Frame(fr, bg=PURP, height=3).pack(fill=tk.X)
        tk.Label(fr, text="🤖 CPU", bg=BG3, fg=PURP,
                 font=("Segoe UI", 12, "bold")).pack(pady=(10, 4))
        tk.Label(fr, text="Inteligencia Artificial", bg=BG3, fg=TEXT,
                 font=("Segoe UI", 11)).pack()
        tk.Label(fr, text="Analiza tus jugadas\ny elige automáticamente",
                 bg=BG3, fg=TEXTL, font=("Segoe UI", 9, "italic"),
                 justify="center").pack(pady=(6, 0))
        af = tk.Frame(fr, bg=BG3)
        af.pack(pady=10)
        self._cpu_reg_icons = []
        for ch in CHOICES:
            l = tk.Label(af, text=EMOJIS[ch], bg=BG3, font=("Segoe UI Emoji", 15))
            l.pack(side=tk.LEFT, padx=2)
            self._cpu_reg_icons.append(l)
        self._creg_idx = 0
        self._tick_cpu_reg()

    def _tick_cpu_reg(self):
        if not self.winfo_exists() or self._mode != "cpu":
            return
        if not hasattr(self, "_cpu_reg_icons"):
            return
        for i, l in enumerate(self._cpu_reg_icons):
            try:
                l.config(fg=PURP if i == self._creg_idx % len(CHOICES) else "#2A3F55")
            except tk.TclError:
                return
        self._creg_idx += 1
        self.after(190, self._tick_cpu_reg)

    def _set_mode(self, mode):
        self._mode = mode
        if mode == "2p":
            self._btn2p.config(bg=ACCENT, fg=BG)
            self._btncpu.config(bg=BG3, fg=TEXT)
            self._draw_p2_human()
        else:
            self._btn2p.config(bg=BG3, fg=TEXT)
            self._btncpu.config(bg=PURP, fg=BG)
            self._draw_p2_cpu()

    def _start(self):
        n1 = self.p1_name.get().strip() or "Jugador 1"
        if self._mode == "cpu":
            n2, g2 = "CPU 🤖", "Otro"
        else:
            n2 = self.p2_name.get().strip() or "Jugador 2"
            g2 = self.p2_gender.get()
        self.on_start({
            "p1":     {"name": n1, "gender": self.p1_gender.get()},
            "p2":     {"name": n2, "gender": g2},
            "rondas": self._rondas.get(),
            "vs_cpu": self._mode == "cpu",
        })

    def _tick_particles(self):
        if not self.winfo_exists():
            return
        self._cv.delete("p")
        w = self.winfo_width() or 1200
        h = self.winfo_height() or 800
        for p in self._ptcls:
            p["y"] += p["dy"]
            p["x"] += p["dx"]
            if p["y"] < -40:
                p["y"] = h + 20
                p["x"] = random.randint(0, w)
            self._cv.create_text(p["x"], p["y"], text=p["e"],
                                 font=("Segoe UI Emoji", 16), fill="#1E3352", tags="p")
        self.after(50, self._tick_particles)


# ═══════════════════════════════════════════════════════════════
#  PANTALLA 2 — CUENTA REGRESIVA
# ═══════════════════════════════════════════════════════════════

class CountdownScreen(tk.Frame):
    def __init__(self, master, on_done):
        super().__init__(master, bg=BG)
        self.on_done = on_done
        self._steps  = ["3", "2", "1", "¡YA!"]
        self._idx    = 0
        self._lbl    = tk.Label(self, text="", bg=BG, fg=ACCENT,
                                font=("Segoe UI", 110, "bold"))
        self._lbl.place(relx=.5, rely=.44, anchor="center")
        tk.Label(self, text="¡Prepárate!", bg=BG, fg=TEXTL,
                 font=("Segoe UI", 18)).place(relx=.5, rely=.72, anchor="center")
        self._tick()

    def _tick(self):
        if self._idx >= len(self._steps):
            self.after(200, self.on_done)
            return
        v   = self._steps[self._idx]
        col = GOLD if v == "¡YA!" else ACCENT
        self._lbl.config(text=v, fg=col, font=("Segoe UI", 130, "bold"))
        self.after(130, lambda: self._lbl.config(font=("Segoe UI", 110, "bold")))
        self._idx += 1
        self.after(800, self._tick)


# ═══════════════════════════════════════════════════════════════
#  PANTALLA 3 — JUEGO
# ═══════════════════════════════════════════════════════════════

class GameScreen(tk.Frame):
    def __init__(self, master, players, rondas, vs_cpu, on_end):
        super().__init__(master, bg=BG)
        self.players = players
        self.rondas  = rondas
        self.vs_cpu  = vs_cpu
        self.on_end  = on_end

        self.scores   = {"p1": 0, "p2": 0, "tie": 0}
        self.round    = 0
        self.choices  = {"p1": None, "p2": None}
        self._locked  = {"p1": False, "p2": False}
        self._btns    = {"p1": {}, "p2": {}}
        self._history = []      # jugadas del humano
        self._cpu_fast = False
        self._cpu_idx  = 0

        self._build()
        self._new_round()

    # ─── CONSTRUCCION UI ────────────────────────────────────

    def _build(self):
        # — Marcador superior —
        top = tk.Frame(self, bg=BG2, height=88)
        top.pack(fill=tk.X)
        top.pack_propagate(False)

        p1f = tk.Frame(top, bg=BG2)
        p1f.pack(side=tk.LEFT, padx=18, pady=8)
        tk.Frame(p1f, bg=ACCENT, height=3).pack(fill=tk.X)
        tk.Label(p1f, text=f"{self._icon(1)} {self.players['p1']['name']}",
                 bg=BG2, fg=ACCENT, font=("Segoe UI", 12, "bold")).pack()
        self._pts1 = tk.Label(p1f, text="0 pts", bg=BG2, fg=TEXT,
                              font=("Segoe UI", 22, "bold"))
        self._pts1.pack()

        cf = tk.Frame(top, bg=BG2)
        cf.pack(side=tk.LEFT, expand=True)
        self._lbl_rnd = tk.Label(cf, text="", bg=BG2, fg=TEXTL, font=("Segoe UI", 10))
        self._lbl_rnd.pack()
        tk.Label(cf, text="VS", bg=BG2, fg=GOLD, font=("Segoe UI", 26, "bold")).pack()
        self._lbl_tie = tk.Label(cf, text="Empates: 0", bg=BG2, fg=TEXTL, font=("Segoe UI", 10))
        self._lbl_tie.pack()

        p2col = PURP if self.vs_cpu else ACC2
        p2f   = tk.Frame(top, bg=BG2)
        p2f.pack(side=tk.RIGHT, padx=18, pady=8)
        tk.Frame(p2f, bg=p2col, height=3).pack(fill=tk.X)
        tk.Label(p2f, text=f"{self.players['p2']['name']} {self._icon(2)}",
                 bg=BG2, fg=p2col, font=("Segoe UI", 12, "bold")).pack()
        self._pts2 = tk.Label(p2f, text="0 pts", bg=BG2, fg=TEXT,
                              font=("Segoe UI", 22, "bold"))
        self._pts2.pack()

        # — Arena —
        arena = tk.Frame(self, bg=BG)
        arena.pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        arena.columnconfigure(0, weight=1)
        arena.columnconfigure(1, weight=0)
        arena.columnconfigure(2, weight=1)

        self._build_human_panel(arena, "p1", 0, ACCENT)
        self._build_center_panel(arena)
        if self.vs_cpu:
            self._build_cpu_panel(arena)
        else:
            self._build_human_panel(arena, "p2", 2, ACC2)

        # — Estado —
        self._lbl_st = tk.Label(self, text="", bg=BG, fg=GOLD,
                                font=("Segoe UI", 13, "bold"), wraplength=900)
        self._lbl_st.pack(pady=(0, 4))

        # — Reglas —
        self._build_rules()

    def _icon(self, n):
        g = self.players[f"p{n}"]["gender"]
        return "👨" if g == "Masculino" else "👩" if g == "Femenino" else "🧑"

    def _build_human_panel(self, parent, pid, col, color):
        fr = tk.Frame(parent, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        fr.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)
        tk.Frame(fr, bg=color, height=3).pack(fill=tk.X)
        tk.Label(fr, text=f"{self._icon(int(pid[1]))} {self.players[pid]['name']}",
                 bg=BG2, fg=color, font=("Segoe UI", 12, "bold")).pack(pady=(8, 4))
        tk.Label(fr, text="Elige tu jugada:", bg=BG2, fg=TEXTL, font=FS).pack()

        grid = tk.Frame(fr, bg=BG2)
        grid.pack(padx=8, pady=8)
        for i, ch in enumerate(CHOICES):
            r, c = divmod(i, 4)
            b = ChoiceBtn(grid, ch, lambda x, p=pid: self._pick(p, x), color)
            b.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            self._btns[pid][ch] = b

        lbl = tk.Label(fr, text="❓", bg=BG2, fg=TEXTL, font=("Segoe UI Emoji", 34))
        lbl.pack(pady=4)
        setattr(self, f"_em_{pid}", lbl)

        lck = tk.Label(fr, text="", bg=BG2, fg=color, font=("Segoe UI", 10, "bold"))
        lck.pack(pady=(0, 8))
        setattr(self, f"_lk_{pid}", lck)

    def _build_cpu_panel(self, parent):
        fr = tk.Frame(parent, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        fr.grid(row=0, column=2, sticky="nsew", padx=6, pady=4)
        tk.Frame(fr, bg=PURP, height=3).pack(fill=tk.X)
        tk.Label(fr, text=f"🤖 {self.players['p2']['name']}",
                 bg=BG2, fg=PURP, font=("Segoe UI", 12, "bold")).pack(pady=(8, 4))
        tk.Label(fr, text="Esperando tu jugada...", bg=BG2, fg=TEXTL, font=FS).pack()

        af = tk.Frame(fr, bg=BG2)
        af.pack(pady=10)
        self._cpu_icons = []
        for ch in CHOICES:
            l = tk.Label(af, text=EMOJIS[ch], bg=BG2, font=("Segoe UI Emoji", 20))
            l.pack(side=tk.LEFT, padx=3)
            self._cpu_icons.append(l)
        self._tick_cpu_anim()

        self._em_p2 = tk.Label(fr, text="❓", bg=BG2, fg=TEXTL, font=("Segoe UI Emoji", 34))
        self._em_p2.pack(pady=4)
        self._lk_p2 = tk.Label(fr, text="", bg=BG2, fg=PURP, font=("Segoe UI", 10, "bold"))
        self._lk_p2.pack(pady=(0, 8))

    def _tick_cpu_anim(self):
        if not self.winfo_exists() or not hasattr(self, "_cpu_icons"):
            return
        delay = 80 if self._cpu_fast else 210
        for i, l in enumerate(self._cpu_icons):
            try:
                active = i == self._cpu_idx % len(CHOICES)
                l.config(fg=(ACC2 if self._cpu_fast else PURP) if active else "#2A3F55")
            except tk.TclError:
                return
        self._cpu_idx += 1
        self.after(delay, self._tick_cpu_anim)

    def _build_center_panel(self, parent):
        cf = tk.Frame(parent, bg=BG, width=155)
        cf.grid(row=0, column=1, sticky="nsew", padx=4)
        cf.pack_propagate(False)

        tk.Label(cf, text="⚔️", bg=BG, font=("Segoe UI Emoji", 26)).pack(pady=(28, 4))
        self._res_em = tk.Label(cf, text="", bg=BG, font=("Segoe UI Emoji", 46))
        self._res_em.pack(pady=4)
        self._res_tx = tk.Label(cf, text="", bg=BG, fg=GOLD,
                                font=("Segoe UI", 12, "bold"),
                                wraplength=145, justify="center")
        self._res_tx.pack(pady=4)

        self._btn_rev = tk.Button(cf, text="▶ REVELAR", command=self._reveal,
                                  bg=GOLD, fg=BG, font=("Segoe UI", 11, "bold"),
                                  relief="flat", cursor="hand2",
                                  padx=12, pady=8, state="disabled")
        self._btn_rev.pack(pady=8)

        self._btn_nxt = tk.Button(cf, text="▶ SIGUIENTE", command=self._next,
                                  bg=ACCENT, fg=BG, font=("Segoe UI", 11, "bold"),
                                  relief="flat", cursor="hand2", padx=12, pady=8)
        self._btn_nxt.pack(pady=4)
        self._btn_nxt.pack_forget()

    def _build_rules(self):
        rf  = tk.Frame(self, bg=BG3)
        rf.pack(fill=tk.X, padx=14, pady=(0, 8))
        hdr = tk.Frame(rf, bg=BG3)
        hdr.pack(fill=tk.X)
        lbl = tk.Label(hdr, text="📖 Reglas — click para expandir",
                       bg=BG3, fg=TEXTL, font=FS, cursor="hand2")
        lbl.pack(side=tk.LEFT, padx=10, pady=4)
        body = tk.Frame(rf, bg=BG3)
        lines = "\n".join(
            f"  {EMOJIS[c]} {c:8} → vence a: {', '.join(v[0] for v in vs)}"
            for c, vs in WINS.items())
        tk.Label(body, text=lines, bg=BG3, fg=TEXTL,
                 font=("Consolas", 9), justify="left").pack(padx=14, pady=4)
        vis = [False]
        def toggle(e=None):
            vis[0] = not vis[0]
            body.pack(fill=tk.X) if vis[0] else body.pack_forget()
        hdr.bind("<Button-1>", toggle)
        lbl.bind("<Button-1>", toggle)

    # ─── LÓGICA DE RONDA ────────────────────────────────────

    def _new_round(self):
        self.round  += 1
        self.choices = {"p1": None, "p2": None}
        self._locked = {"p1": False, "p2": False}
        self._cpu_fast = False
        self._lbl_rnd.config(text=f"Ronda {self.round} de {self.rondas}")
        self._res_em.config(text="")
        self._res_tx.config(text="")
        self._btn_rev.config(state="disabled")
        self._btn_nxt.pack_forget()
        self._btn_rev.pack(pady=8)
        self._lbl_st.config(
            text="✊ Elige tu jugada — ¡la CPU está esperando!" if self.vs_cpu
            else "Ambos jugadores eligen su jugada...")

        for pid in ["p1", "p2"]:
            for b in self._btns[pid].values():
                b.select(False)
            try:
                getattr(self, f"_em_{pid}").config(text="❓", fg=TEXTL)
                getattr(self, f"_lk_{pid}").config(text="")
            except AttributeError:
                pass

    def _pick(self, pid, choice):
        if self._locked[pid]:
            return
        self._locked[pid] = True
        self.choices[pid] = choice

        for ch, b in self._btns[pid].items():
            b.select(ch == choice)
        self._btns[pid][choice].bounce()

        col = ACCENT if pid == "p1" else ACC2
        getattr(self, f"_em_{pid}").config(text=EMOJIS[choice], fg=col)
        getattr(self, f"_lk_{pid}").config(text=f"✅ {choice} elegido")

        if self.vs_cpu and pid == "p1":
            self._history.append(choice)
            self._cpu_turn()
        elif not self.vs_cpu:
            if self.choices["p1"] and self.choices["p2"]:
                self._btn_rev.config(state="normal")
                self._lbl_st.config(text="¡Ambos listos! Presiona ▶ REVELAR")
            else:
                other = "p2" if pid == "p1" else "p1"
                self._lbl_st.config(
                    text=f"⏳ {self.players[other]['name']} aún no elige...")

    def _cpu_turn(self):
        self._cpu_fast = True
        self._lbl_st.config(text=f"🤖 {random.choice(CPU_MSGS)}")
        self._em_p2.config(text="🤔")
        self._lk_p2.config(text="CPU pensando...")
        self.after(random.randint(700, 1100), self._cpu_commit)

    def _cpu_commit(self):
        choice = cpu_choose(self._history[:-1])
        self.choices["p2"] = choice
        self._locked["p2"] = True
        self._cpu_fast     = False
        self._em_p2.config(text="❓", fg=TEXTL)
        self._lk_p2.config(text="✅ ¡CPU lista!")
        self._btn_rev.config(state="normal")
        self._lbl_st.config(text="¡La CPU ya eligió! Presiona ▶ REVELAR")

    def _reveal(self):
        c1, c2 = self.choices["p1"], self.choices["p2"]
        if not c1 or not c2:
            return
        self._btn_rev.pack_forget()
        if self.vs_cpu:
            self._ruleta(c2, lambda: self._resolve(c1, c2))
        else:
            self._resolve(c1, c2)

    def _ruleta(self, final, callback):
        emojis = list(EMOJIS.values())
        delays = [55, 70, 90, 120, 160, 210, 280]
        idx    = [0]

        def frame():
            if idx[0] < len(delays):
                self._em_p2.config(text=random.choice(emojis), fg=ACC2)
                self.after(delays[idx[0]], frame)
                idx[0] += 1
            else:
                self._em_p2.config(text=EMOJIS[final], fg=PURP)
                self._lk_p2.config(text=f"🤖 {final}")
                self.after(250, callback)
        frame()

    def _resolve(self, c1, c2):
        result, phrase = get_result(c1, c2)
        n1 = self.players["p1"]["name"]
        n2 = self.players["p2"]["name"]

        if result == "win":
            self.scores["p1"] += 1
            msg = f"¡{n1} gana!  {EMOJIS[c1]} {phrase} {EMOJIS[c2]}"
            self._res_em.config(text="🏆")
            self._res_tx.config(text=msg, fg=ACCENT)
            self._flash_pts("p1")
        elif result == "lose":
            self.scores["p2"] += 1
            msg = f"¡{n2} gana!  {EMOJIS[c2]} {phrase} {EMOJIS[c1]}"
            self._res_em.config(text="🏆")
            self._res_tx.config(text=msg, fg=PURP if self.vs_cpu else ACC2)
            self._flash_pts("p2")
        else:
            self.scores["tie"] += 1
            msg = f"¡Empate!  {EMOJIS[c1]} vs {EMOJIS[c2]}"
            self._res_em.config(text="🤝")
            self._res_tx.config(text=msg, fg=GOLD)

        self._pts1.config(text=f"{self.scores['p1']} pts")
        self._pts2.config(text=f"{self.scores['p2']} pts")
        self._lbl_tie.config(text=f"Empates: {self.scores['tie']}")
        self._lbl_st.config(text=msg)
        self._btn_nxt.pack(pady=4)

        if self.round >= self.rondas:
            self._btn_nxt.config(text="🏁 VER RESULTADO FINAL", command=self._finish)
        else:
            self._btn_nxt.config(text="▶ SIGUIENTE RONDA", command=self._next)

    def _flash_pts(self, pid):
        lbl = self._pts1 if pid == "p1" else self._pts2
        lbl.config(fg=GOLD, font=("Segoe UI", 30, "bold"))
        self.after(400, lambda: lbl.config(fg=TEXT, font=("Segoe UI", 22, "bold")))

    def _next(self):
        self._new_round()

    def _finish(self):
        self.on_end(self.players, self.scores, self.rondas, self.vs_cpu)


# ═══════════════════════════════════════════════════════════════
#  PANTALLA 4 — RESULTADO FINAL
# ═══════════════════════════════════════════════════════════════

class ResultScreen(tk.Frame):
    def __init__(self, master, players, scores, rondas, vs_cpu, on_restart, on_records):
        super().__init__(master, bg=BG)
        self.players    = players
        self.scores     = scores
        self.rondas     = rondas
        self.vs_cpu     = vs_cpu
        self.on_restart = on_restart
        self.on_records = on_records
        self._winner    = ("p1" if scores["p1"] > scores["p2"] else
                           "p2" if scores["p2"] > scores["p1"] else "tie")
        self._lb        = None
        self._ll        = None
        self._build()
        self._save()
        self._start_confetti()

    def _build(self):
        self._cv = tk.Canvas(self, bg=BG, highlightthickness=0)
        self._cv.place(relwidth=1, relheight=1)

        box = tk.Frame(self, bg=BG2)
        box.place(relx=.5, rely=.5, anchor="center", width=660, height=570)
        tk.Frame(box, bg=GOLD, height=4).pack(fill=tk.X)

        if self._winner == "tie":
            title, sub, tc = "🤝 ¡EMPATE!", "¡Nadie pudo con el otro!", GOLD
        else:
            wn  = self.players[self._winner]["name"]
            lk  = "p2" if self._winner == "p1" else "p1"
            ln  = self.players[lk]["name"]
            title = f"🏆 ¡{wn.upper()} GANA!"
            sub   = f"¡{ln} no pudo contra ti!"
            tc    = ACCENT if self._winner == "p1" else (PURP if self.vs_cpu else ACC2)

        tk.Label(box, text=title, bg=BG2, fg=tc,   font=("Segoe UI", 25, "bold")).pack(pady=(18, 4))
        tk.Label(box, text=sub,   bg=BG2, fg=TEXTL, font=("Segoe UI", 13)).pack()

        cards = tk.Frame(box, bg=BG2)
        cards.pack(padx=28, pady=14, fill=tk.X)
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        for col, (pid, color) in enumerate([("p1", ACCENT), ("p2", PURP if self.vs_cpu else ACC2)]):
            is_w = self._winner == pid
            cf   = tk.Frame(cards, bg=BG3,
                            highlightbackground=color if is_w else BORDER,
                            highlightthickness=2 if is_w else 1)
            cf.grid(row=0, column=col, padx=10, sticky="nsew")
            if is_w:
                tk.Label(cf, text="🏆 GANADOR", bg=color, fg=BG,
                         font=("Segoe UI", 9, "bold")).pack(fill=tk.X)
            g    = self.players[pid]["gender"]
            icon = ("🤖" if pid == "p2" and self.vs_cpu else
                    "👨" if g == "Masculino" else "👩" if g == "Femenino" else "🧑")
            tk.Label(cf, text=f"{icon} {self.players[pid]['name']}", bg=BG3, fg=color,
                     font=("Segoe UI", 13, "bold")).pack(pady=(10, 2))
            tk.Label(cf, text=str(self.scores[pid]), bg=BG3, fg=TEXT,
                     font=("Segoe UI", 48, "bold")).pack()
            tk.Label(cf, text="victorias", bg=BG3, fg=TEXTL, font=FS).pack(pady=(0, 12))

        tk.Label(box, text=f"🤝 Empates: {self.scores['tie']}   |   📊 Rondas: {self.rondas}",
                 bg=BG2, fg=TEXTL, font=FS).pack()

        if self._winner != "tie":
            lk  = "p2" if self._winner == "p1" else "p1"
            lnm = self.players[lk]["name"]
            self._lb = tk.Frame(box, bg="#3D0000",
                                highlightbackground=ACC2, highlightthickness=1)
            self._lb.pack(fill=tk.X, padx=28, pady=10)
            self._ll = tk.Label(self._lb, text=f"💀  {lnm.upper()}, PERDISTE  💀",
                                bg="#3D0000", fg=ACC2, font=("Segoe UI", 14, "bold"))
            self._ll.pack(pady=7)
            self._flash_lose()

        bf = tk.Frame(box, bg=BG2)
        bf.pack(pady=14)
        mkbtn(bf, "🔄 Nueva partida",    self.on_restart, ACCENT).pack(side=tk.LEFT, padx=6)
        mkbtn(bf, "🏅 Tabla de récords", self.on_records, GOLD).pack(side=tk.LEFT, padx=6)

    def _flash_lose(self):
        if not self.winfo_exists() or not self._lb:
            return
        ts  = int(datetime.datetime.now().timestamp() * 2)
        col = "#5A0000" if ts % 2 else "#3D0000"
        try:
            self._lb.config(bg=col)
            self._ll.config(bg=col)
        except tk.TclError:
            return
        self.after(500, self._flash_lose)

    def _save(self):
        for pid in ["p1", "p2"]:
            lk = "p2" if pid == "p1" else "p1"
            save_record({
                "name":   self.players[pid]["name"],
                "gender": self.players[pid]["gender"],
                "wins":   self.scores[pid],
                "losses": self.scores[lk],
                "ties":   self.scores["tie"],
                "rondas": self.rondas,
                "result": ("win" if self._winner == pid else
                           "tie" if self._winner == "tie" else "lose"),
                "vs":     self.players[lk]["name"],
                "mode":   "vs CPU" if self.vs_cpu and pid == "p1" else "2 Jugadores",
                "date":   datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            })

    def _start_confetti(self):
        cs = [ACCENT, ACC2, GOLD, "#FF88AA", "#88FFCC", "#AABBFF"]
        self._conf = [{"x": random.randint(0, 1200), "y": random.randint(-200, 0),
                       "dx": random.uniform(-2, 2),  "dy": random.uniform(3, 7),
                       "c": random.choice(cs),        "s": random.randint(6, 13)}
                      for _ in range(50)]
        self._tick_conf()

    def _tick_conf(self):
        if not self.winfo_exists():
            return
        self._cv.delete("c")
        h = self.winfo_height() or 800
        for p in self._conf:
            p["y"] += p["dy"]
            p["x"] += p["dx"]
            if p["y"] > h:
                p["y"] = -20
                p["x"] = random.randint(0, 1200)
            s = p["s"]
            self._cv.create_rectangle(p["x"]-s, p["y"]-s, p["x"]+s, p["y"]+s,
                                       fill=p["c"], outline="", tags="c")
        self.after(40, self._tick_conf)


# ═══════════════════════════════════════════════════════════════
#  PANTALLA 5 — RÉCORDS
# ═══════════════════════════════════════════════════════════════

class RecordsScreen(tk.Frame):
    def __init__(self, master, on_back):
        super().__init__(master, bg=BG)
        self.on_back = on_back
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG2, height=68)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🏅  TABLA DE RÉCORDS", bg=BG2, fg=GOLD,
                 font=("Segoe UI", 19, "bold")).pack(side=tk.LEFT, padx=20, pady=14)
        mkbtn(hdr, "← Volver", self.on_back, BG3, TEXT, pady=5).pack(
            side=tk.RIGHT, padx=20, pady=16)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("R.Treeview", background=BG2, fieldbackground=BG2,
                        foreground=TEXT, rowheight=30, font=("Segoe UI", 10))
        style.configure("R.Treeview.Heading", background=BG3, foreground=GOLD,
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("R.Treeview",
                  background=[("selected", BG3)],
                  foreground=[("selected", ACCENT)])

        cols = ("#", "Jugador", "Género", "Victorias", "Derrotas",
                "Empates", "Rondas", "Resultado", "Vs", "Modo", "Fecha")
        tree = ttk.Treeview(self, columns=cols, show="headings",
                            style="R.Treeview", height=20)
        widths = [36, 120, 75, 75, 75, 75, 65, 85, 120, 90, 120]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w,
                        anchor="w" if col in ("Jugador", "Vs") else "center")

        vsb = ttk.Scrollbar(self, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        icons = {"win": "🏆 Ganó", "lose": "💀 Perdió", "tie": "🤝 Empate"}
        recs  = load_records()
        for i, r in enumerate(recs, 1):
            tree.insert("", "end", tags=(r.get("result", ""),),
                        values=(i,
                                r.get("name", "?"),   r.get("gender", "?"),
                                r.get("wins", 0),     r.get("losses", 0),
                                r.get("ties", 0),     r.get("rondas", "?"),
                                icons.get(r.get("result", ""), "—"),
                                r.get("vs", "?"),     r.get("mode", "?"),
                                r.get("date", "?")))
        tree.tag_configure("win",  foreground=ACCENT)
        tree.tag_configure("lose", foreground=ACC2)
        tree.tag_configure("tie",  foreground=GOLD)

        if not recs:
            tk.Label(self, text="Aún no hay récords.\n¡Juega tu primera partida!",
                     bg=BG, fg=TEXTL, font=("Segoe UI", 14)).pack(expand=True)


# ═══════════════════════════════════════════════════════════════
#  APP PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("✊✋✌️  PPT 7 Variables")
        self.configure(bg=BG)
        self.geometry("1100x740")
        self.minsize(960, 680)
        self._screen = None
        self._data   = {}
        self._last   = {}
        self._show(RegistroScreen, on_start=self._on_start)

    def _show(self, cls, **kw):
        if self._screen:
            self._screen.destroy()
        self._screen = cls(self, **kw)
        self._screen.pack(fill=tk.BOTH, expand=True)

    def _on_start(self, data):
        self._data = data
        self._show(CountdownScreen, on_done=self._on_countdown)

    def _on_countdown(self):
        self._show(GameScreen,
                   players={"p1": self._data["p1"], "p2": self._data["p2"]},
                   rondas=self._data["rondas"],
                   vs_cpu=self._data["vs_cpu"],
                   on_end=self._on_end)

    def _on_end(self, players, scores, rondas, vs_cpu):
        self._last = dict(players=players, scores=scores, rondas=rondas, vs_cpu=vs_cpu)
        self._show_result()

    def _show_result(self):
        self._show(ResultScreen,
                   players=self._last["players"],
                   scores=self._last["scores"],
                   rondas=self._last["rondas"],
                   vs_cpu=self._last["vs_cpu"],
                   on_restart=lambda: self._show(RegistroScreen, on_start=self._on_start),
                   on_records=self._show_records)

    def _show_records(self):
        self._show(RecordsScreen, on_back=self._show_result)


if __name__ == "__main__":
    App().mainloop()
