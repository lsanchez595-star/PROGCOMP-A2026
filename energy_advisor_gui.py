"""
╔══════════════════════════════════════════════════════════════════╗
║          ASESOR DE ENERGÍA RENOVABLE — EnergyMap v2.0            ║
║          Interfaz gráfica con Tkinter + manejo de archivos       ║
╚══════════════════════════════════════════════════════════════════╝
Requisitos: Python 3.8+ (Tkinter viene incluido)
Uso: python energy_advisor_gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import math
import os
from datetime import datetime


# ─────────────────────────────────────────────
#  DATOS DE TECNOLOGÍAS
# ─────────────────────────────────────────────

TECNOLOGIAS = {
    "solar_fv": {
        "nombre": "Solar Fotovoltaica",
        "icono": "☀",
        "lcoe": "30–60 USD/MWh",
        "tipo": "Variable diurna",
        "desc": "Paneles solares en campo o tejado. Bajo mantenimiento, alta escalabilidad y despliegue rápido.",
        "color": "#e67e22",
    },
    "eolica_tierra": {
        "nombre": "Eólica Terrestre",
        "icono": "◎",
        "lcoe": "25–50 USD/MWh",
        "tipo": "Variable intermitente",
        "desc": "Aerogeneradores en tierra. Alta densidad de potencia por hectárea y muy bajo LCOE.",
        "color": "#2980b9",
    },
    "mini_hidro": {
        "nombre": "Mini / Pequeña Hidráulica",
        "icono": "〜",
        "lcoe": "40–90 USD/MWh",
        "tipo": "Base continua",
        "desc": "Turbinas en ríos. Generación base confiable sin grandes represas.",
        "color": "#27ae60",
    },
    "hidro_grande": {
        "nombre": "Hidráulica a Gran Escala",
        "icono": "▣",
        "lcoe": "20–50 USD/MWh",
        "tipo": "Base / regulable",
        "desc": "Embalses y represas. Alto CAPEX pero muy bajo LCOE a largo plazo.",
        "color": "#1a7a50",
    },
    "geotermia": {
        "nombre": "Geotermia",
        "icono": "△",
        "lcoe": "50–100 USD/MWh",
        "tipo": "Base continua 24/7",
        "desc": "Aprovecha calor del subsuelo. Sin emisiones, carga base perfecta.",
        "color": "#c0392b",
    },
    "biomasa": {
        "nombre": "Biomasa / Biogás",
        "icono": "✦",
        "lcoe": "60–120 USD/MWh",
        "tipo": "Flexible / base",
        "desc": "Combustión de residuos orgánicos. Flexible y con beneficio de economía circular.",
        "color": "#6d8c1a",
    },
    "eolica_marina": {
        "nombre": "Eólica Marina (Offshore)",
        "icono": "≋",
        "lcoe": "60–120 USD/MWh",
        "tipo": "Variable alto factor",
        "desc": "Parques eólicos en mar. Factores de capacidad superiores al 40%.",
        "color": "#1a5276",
    },
    "solar_csp": {
        "nombre": "Solar Térmica CSP",
        "icono": "⊙",
        "lcoe": "80–150 USD/MWh",
        "tipo": "Base c/ almacenamiento",
        "desc": "Concentración solar con almacenamiento térmico. Despacho controlable.",
        "color": "#b7770d",
    },
    "hibrido": {
        "nombre": "Sistema Híbrido Solar+Eólico",
        "icono": "⊕",
        "lcoe": "35–65 USD/MWh",
        "tipo": "Complementario",
        "desc": "Complementariedad diurna/nocturna y estacional. Mayor factor de capacidad.",
        "color": "#7d3c98",
    },
}

# ─────────────────────────────────────────────
#  MOTOR DE PUNTUACIÓN
# ─────────────────────────────────────────────

def normalizar(val, minimo, maximo):
    return min(1.0, max(0.0, (val - minimo) / (maximo - minimo)))

def clamp(val):
    return min(100, max(0, val))

def calcular_scores(d):
    scores = {}

    s = 0
    s += normalizar(d["solar"], 1, 9) * 35
    s += normalizar(d["area"], 10, 5000) * 15
    if d["terreno"] == "desierto": s += 15
    if d["terreno"] == "plano":    s += 8
    if d["temperatura"] < 35:      s += 5
    if "aves" in d["restricciones"]:      s -= 5
    if d["prioridad"] == "rapido":        s += 10
    if d["prioridad"] == "ambiental":     s += d["peso_ambiental"] * 8
    if d["presupuesto"] < 20 and d["demanda"] < 20: s += 5
    if "solar" in d["existentes"]: s -= 8
    scores["solar_fv"] = clamp(s)

    s = 0
    s += normalizar(d["viento"], 0, 15) * 40
    if d["viento"] >= 6:                   s += 15
    if d["terreno"] == "costa":             s += 12
    if d["terreno"] == "montaña":           s += 8
    if "aves" in d["restricciones"]:        s -= 15
    if "patrimonio" in d["restricciones"]:  s -= 10
    if d["prioridad"] == "ambiental":       s -= d["peso_ambiental"] * 5
    if "eolica" in d["existentes"]:         s -= 8
    if d["densidad_pob"] != "alta":         s += 5
    scores["eolica_tierra"] = clamp(s)

    s = 0
    s += normalizar(d["hidro"], 0, 200) * 30
    if d["hidro"] >= 2:  s += 20
    if d["hidro"] >= 10: s += 15
    if d["terreno"] in ("montaña", "valles"): s += 15
    if "agua" in d["restricciones"]:           s -= 20
    if d["fiabilidad"] == "alta":              s += 12
    if d["precipitacion"] > 1000:              s += 8
    if "inundaciones" in d["restricciones"]:   s -= 5
    scores["mini_hidro"] = clamp(s)

    s = 0
    s += normalizar(d["hidro"], 0, 200) * 35
    if d["hidro"] >= 50:                        s += 20
    if d["area"] >= 1000:                       s += 10
    if d["presupuesto"] >= 200:                 s += 15
    if d["horizonte"] >= 25:                    s += 10
    if "patrimonio" in d["restricciones"]:      s -= 20
    if "conflicto" in d["restricciones"]:       s -= 15
    if "agua" in d["restricciones"]:            s -= 30
    if d["prioridad"] == "ambiental":           s -= d["peso_ambiental"] * 15
    if "hidro" in d["existentes"]:              s -= 10
    scores["hidro_grande"] = clamp(s)

    geo_map = {"nula": 0, "baja": 20, "media": 50, "alta": 80}
    s = geo_map.get(d["geotermia"], 0)
    if d["fiabilidad"] == "alta":        s += 15
    if d["geotermia"] == "alta":         s += 20
    if "sismica" in d["restricciones"]:  s -= 10
    if d["terreno"] == "montaña":        s += 5
    if d["presupuesto"] >= 100:          s += 5
    scores["geotermia"] = clamp(s)

    bio_map = {"nula": 0, "baja": 15, "media": 40, "alta": 70}
    s = bio_map.get(d["biomasa"], 0)
    if d["tipo_demanda"] == "industrial": s += 15
    if d["fiabilidad"] == "alta":         s += 10
    if d["red_nacional"] == "no":         s += 10
    if d["prioridad"] == "empleo":        s += 10
    if d["prioridad"] == "ambiental":     s -= d["peso_ambiental"] * 10
    scores["biomasa"] = clamp(s)

    mar_map = {"no": 0, "olas": 20, "mareas": 40, "alto": 70}
    s = mar_map.get(d["marino"], 0)
    s += normalizar(d["viento"], 0, 15) * 20
    if d["marino"] != "no" and d["viento"] >= 7: s += 20
    if d["presupuesto"] >= 300:                  s += 10
    if d["area"] >= 2000:                        s += 5
    scores["eolica_marina"] = clamp(s)

    s = 0
    s += normalizar(d["solar"], 1, 9) * 30
    if d["solar"] >= 6:            s += 20
    if d["terreno"] == "desierto": s += 20
    if d["area"] >= 500:           s += 10
    if d["fiabilidad"] == "alta":  s += 10
    if d["temperatura"] >= 20:     s += 8
    if d["presupuesto"] >= 150:    s += 5
    scores["solar_csp"] = clamp(s)

    sn = normalizar(d["solar"], 1, 9)
    vn = normalizar(d["viento"], 0, 15)
    s  = sn * 25 + vn * 25
    if sn > 0.4 and vn > 0.3:                                   s += 20
    if d["fiabilidad"] == "alta" or d["red_nacional"] == "no":  s += 10
    if d["prioridad"] == "confiabilidad":                        s += 10
    if d["area"] >= 200:                                         s += 5
    if "solar" in d["existentes"] or "eolica" in d["existentes"]: s += 5
    scores["hibrido"] = clamp(s)

    adj = {
        "costo":         {"solar_fv": +5, "eolica_tierra": +5, "mini_hidro": +3,
                          "geotermia": -5, "eolica_marina": -10, "solar_csp": -5},
        "confiabilidad": {"mini_hidro": +8, "geotermia": +8, "biomasa": +5,
                          "hibrido": +5, "solar_fv": -5, "eolica_tierra": -3},
        "rapido":        {"solar_fv": +10, "eolica_tierra": +5, "mini_hidro": +3,
                          "hidro_grande": -15, "geotermia": -10},
        "empleo":        {"biomasa": +8, "mini_hidro": +5, "eolica_tierra": +5},
        "ambiental":     {},
    }
    for k, delta in adj.get(d["prioridad"], {}).items():
        scores[k] = clamp(scores[k] + delta)

    return scores


# ─────────────────────────────────────────────
#  APLICACIÓN TKINTER
# ─────────────────────────────────────────────

COLORES = {
    "bg":        "#1a1a2e",
    "panel":     "#16213e",
    "card":      "#0f3460",
    "acento":    "#e94560",
    "verde":     "#2ecc71",
    "amarillo":  "#f1c40f",
    "texto":     "#ecf0f1",
    "texto2":    "#bdc3c7",
    "borde":     "#2c3e6b",
    "entrada":   "#0d2137",
    "boton":     "#e94560",
    "boton_txt": "#ffffff",
    "slider_bg": "#2c3e6b",
}

FUENTE_TITULO  = ("Segoe UI", 16, "bold")
FUENTE_SUBTIT  = ("Segoe UI", 11, "bold")
FUENTE_NORMAL  = ("Segoe UI", 10)
FUENTE_SMALL   = ("Segoe UI", 9)
FUENTE_MONO    = ("Consolas", 10)


class Tooltip:
    """Tooltip flotante para widgets."""
    def __init__(self, widget, texto):
        self.widget = widget
        self.texto  = texto
        self.ventana = None
        widget.bind("<Enter>", self.mostrar)
        widget.bind("<Leave>", self.ocultar)

    def mostrar(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.ventana = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(tw, text=self.texto, background="#2c3e50", foreground="#ecf0f1",
                       font=FUENTE_SMALL, relief="flat", padx=8, pady=4, wraplength=280)
        lbl.pack()

    def ocultar(self, event=None):
        if self.ventana:
            self.ventana.destroy()
            self.ventana = None


class ScrollFrame(tk.Frame):
    """Frame con scrollbar vertical."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORES["bg"], **kwargs)
        canvas = tk.Canvas(self, bg=COLORES["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=COLORES["bg"])
        self.inner.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.canvas = canvas


class SliderVar(tk.Frame):
    """Slider con etiqueta y valor numérico en tiempo real."""
    def __init__(self, parent, label, from_, to, default, step=0.1, sufijo="", decimals=1, **kwargs):
        super().__init__(parent, bg=COLORES["bg"], **kwargs)
        self.decimals = decimals
        self.variable = tk.DoubleVar(value=default)

        tk.Label(self, text=label, bg=COLORES["bg"], fg=COLORES["texto2"],
                 font=FUENTE_SMALL).pack(anchor="w")

        row = tk.Frame(self, bg=COLORES["bg"])
        row.pack(fill="x")

        self.slider = tk.Scale(
            row, from_=from_, to=to, resolution=step, orient="horizontal",
            variable=self.variable, showvalue=False,
            bg=COLORES["bg"], fg=COLORES["texto"], troughcolor=COLORES["slider_bg"],
            activebackground=COLORES["acento"], highlightthickness=0,
            command=self._actualizar
        )
        self.slider.pack(side="left", fill="x", expand=True)

        self.lbl_val = tk.Label(row, text=f"{default:.{decimals}f}{sufijo}",
                                width=9, anchor="e",
                                bg=COLORES["bg"], fg=COLORES["acento"],
                                font=("Segoe UI", 10, "bold"))
        self.lbl_val.pack(side="right")
        self.sufijo = sufijo

    def _actualizar(self, val):
        v = float(val)
        self.lbl_val.config(text=f"{v:.{self.decimals}f}{self.sufijo}")

    def get(self):
        return self.variable.get()

    def set(self, val):
        self.variable.set(val)
        self._actualizar(val)


class ComboVar(tk.Frame):
    """Combobox estilizado."""
    def __init__(self, parent, label, opciones, default=None, **kwargs):
        super().__init__(parent, bg=COLORES["bg"], **kwargs)
        self.claves = [o[0] for o in opciones]
        etiquetas   = [o[1] for o in opciones]
        self.variable = tk.StringVar()

        tk.Label(self, text=label, bg=COLORES["bg"], fg=COLORES["texto2"],
                 font=FUENTE_SMALL).pack(anchor="w")

        style = ttk.Style()
        style.configure("Dark.TCombobox",
                        fieldbackground=COLORES["entrada"],
                        background=COLORES["entrada"],
                        foreground=COLORES["texto"],
                        selectbackground=COLORES["card"],
                        selectforeground=COLORES["texto"])

        self.combo = ttk.Combobox(self, textvariable=self.variable,
                                  values=etiquetas, state="readonly",
                                  style="Dark.TCombobox", font=FUENTE_NORMAL)
        self.combo.pack(fill="x", pady=(2, 0))

        idx = 0
        if default and default in self.claves:
            idx = self.claves.index(default)
        self.combo.current(idx)

    def get(self):
        idx = self.combo.current()
        return self.claves[idx] if idx >= 0 else self.claves[0]

    def set_by_key(self, key):
        if key in self.claves:
            self.combo.current(self.claves.index(key))


class CheckGroup(tk.Frame):
    """Grupo de checkboxes."""
    def __init__(self, parent, label, opciones, **kwargs):
        super().__init__(parent, bg=COLORES["bg"], **kwargs)
        self.opciones = opciones
        self.vars = {}

        tk.Label(self, text=label, bg=COLORES["bg"], fg=COLORES["texto2"],
                 font=FUENTE_SMALL).pack(anchor="w")

        grid = tk.Frame(self, bg=COLORES["bg"])
        grid.pack(fill="x", pady=(2, 0))
        for i, (clave, etiqueta) in enumerate(opciones):
            v = tk.BooleanVar()
            self.vars[clave] = v
            cb = tk.Checkbutton(grid, text=etiqueta, variable=v,
                                bg=COLORES["bg"], fg=COLORES["texto"],
                                selectcolor=COLORES["card"],
                                activebackground=COLORES["bg"],
                                activeforeground=COLORES["acento"],
                                font=FUENTE_SMALL)
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 10))

    def get(self):
        return [k for k, v in self.vars.items() if v.get()]

    def set(self, lista):
        for k, v in self.vars.items():
            v.set(k in lista)


class EntradaNum(tk.Frame):
    """Entry numérico estilizado."""
    def __init__(self, parent, label, default, sufijo="", **kwargs):
        super().__init__(parent, bg=COLORES["bg"], **kwargs)
        self.variable = tk.StringVar(value=str(default))

        row = tk.Frame(self, bg=COLORES["bg"])
        row.pack(fill="x")
        tk.Label(row, text=label, bg=COLORES["bg"], fg=COLORES["texto2"],
                 font=FUENTE_SMALL).pack(side="left")
        if sufijo:
            tk.Label(row, text=sufijo, bg=COLORES["bg"], fg=COLORES["acento"],
                     font=FUENTE_SMALL).pack(side="right")

        self.entry = tk.Entry(self, textvariable=self.variable,
                              bg=COLORES["entrada"], fg=COLORES["texto"],
                              insertbackground=COLORES["texto"],
                              font=FUENTE_NORMAL, relief="flat",
                              highlightbackground=COLORES["borde"],
                              highlightthickness=1)
        self.entry.pack(fill="x", pady=(2, 0))

    def get(self):
        try:
            return float(self.variable.get())
        except ValueError:
            return 0.0

    def set(self, val):
        self.variable.set(str(val))


def separador(parent, pady=6):
    tk.Frame(parent, bg=COLORES["borde"], height=1).pack(fill="x", pady=pady)


def titulo_seccion(parent, numero, texto):
    f = tk.Frame(parent, bg=COLORES["card"])
    f.pack(fill="x", pady=(12, 6))
    tk.Label(f, text=f"  {numero}  ", bg=COLORES["acento"], fg="#fff",
             font=("Segoe UI", 9, "bold"), padx=4).pack(side="left")
    tk.Label(f, text=f" {texto}", bg=COLORES["card"], fg=COLORES["texto"],
             font=FUENTE_SUBTIT).pack(side="left", padx=6, pady=4)


# ─────────────────────────────────────────────
#  VENTANA PRINCIPAL
# ─────────────────────────────────────────────

class EnergyMapApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EnergyMap v2.0 — Asesor de Energía Renovable")
        self.geometry("1200x780")
        self.minsize(900, 600)
        self.configure(bg=COLORES["bg"])

        # Historial de evaluaciones
        self.historial = []

        self._aplicar_estilos()
        self._construir_ui()

    # ── Estilos ttk ──────────────────────────
    def _aplicar_estilos(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("TFrame",  background=COLORES["bg"])
        st.configure("TLabel",  background=COLORES["bg"], foreground=COLORES["texto"])
        st.configure("TScrollbar", background=COLORES["card"], troughcolor=COLORES["bg"],
                     bordercolor=COLORES["borde"], arrowcolor=COLORES["texto"])
        st.configure("Treeview",
                     background=COLORES["panel"],
                     fieldbackground=COLORES["panel"],
                     foreground=COLORES["texto"],
                     rowheight=26, font=FUENTE_NORMAL)
        st.configure("Treeview.Heading",
                     background=COLORES["card"],
                     foreground=COLORES["texto"],
                     font=("Segoe UI", 9, "bold"))
        st.map("Treeview", background=[("selected", COLORES["acento"])],
               foreground=[("selected", "#fff")])

    # ── Estructura general ────────────────────
    def _construir_ui(self):
        # ── Cabecera ──
        header = tk.Frame(self, bg=COLORES["panel"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="⚡ EnergyMap v2.0",
                 bg=COLORES["panel"], fg=COLORES["acento"],
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=20, pady=10)
        tk.Label(header, text="Asesor de Energía Renovable",
                 bg=COLORES["panel"], fg=COLORES["texto2"],
                 font=("Segoe UI", 11)).pack(side="left")

        # Botones cabecera
        btn_frame = tk.Frame(header, bg=COLORES["panel"])
        btn_frame.pack(side="right", padx=16)
        for texto, cmd, tip in [
            ("💾 Guardar", self.guardar_evaluacion, "Guardar evaluación actual en JSON"),
            ("📂 Cargar",  self.cargar_archivo,     "Cargar evaluación o historial desde JSON"),
            ("📊 Historial", self.ver_historial,    "Ver y gestionar historial de evaluaciones"),
        ]:
            b = tk.Button(btn_frame, text=texto, command=cmd,
                          bg=COLORES["card"], fg=COLORES["texto"],
                          activebackground=COLORES["acento"], activeforeground="#fff",
                          relief="flat", font=FUENTE_SMALL, padx=12, pady=6, cursor="hand2")
            b.pack(side="left", padx=4)
            Tooltip(b, tip)

        # ── Notebook (pestañas) ──
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        style = ttk.Style()
        style.configure("TNotebook", background=COLORES["bg"], borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=COLORES["panel"], foreground=COLORES["texto"],
                        padding=[14, 6], font=FUENTE_SMALL)
        style.map("TNotebook.Tab",
                  background=[("selected", COLORES["card"])],
                  foreground=[("selected", COLORES["acento"])])

        # Pestaña Evaluación
        tab_eval = tk.Frame(nb, bg=COLORES["bg"])
        nb.add(tab_eval, text="  📋 Evaluación  ")
        self._construir_tab_evaluacion(tab_eval)

        # Pestaña Resultados
        tab_res = tk.Frame(nb, bg=COLORES["bg"])
        nb.add(tab_res, text="  📈 Resultados  ")
        self._construir_tab_resultados(tab_res)

        self.nb = nb

    # ── TAB: FORMULARIO ───────────────────────
    def _construir_tab_evaluacion(self, parent):
        # Panel izquierdo — formulario
        paned = tk.PanedWindow(parent, orient="horizontal",
                               bg=COLORES["bg"], sashwidth=4,
                               sashrelief="flat", sashpad=2)
        paned.pack(fill="both", expand=True)

        # ── Columna izquierda: formulario ──
        left = ScrollFrame(paned)
        paned.add(left, minsize=460)
        p = left.inner
        p.configure(padx=18)

        # ── Sección 1: Geografía ──
        titulo_seccion(p, "1", "Geografía del Territorio")

        self.w_region = EntradaNum(p, "Región / País", "", sufijo="")
        self.w_region.entry.config(width=40)
        # Reutilizar EntradaNum para texto
        self.w_region.variable = tk.StringVar(value="")
        self.w_region.entry.config(textvariable=self.w_region.variable)
        self.w_region.get = lambda: self.w_region.variable.get().strip()
        self.w_region.set = lambda v: self.w_region.variable.set(v)
        self.w_region.pack(fill="x", pady=3)

        row1 = tk.Frame(p, bg=COLORES["bg"])
        row1.pack(fill="x")
        self.w_area      = EntradaNum(row1, "Área disponible", 500, "ha")
        self.w_area.pack(side="left", fill="x", expand=True, padx=(0,8), pady=3)
        self.w_altitud   = EntradaNum(row1, "Altitud", 500, "msnm")
        self.w_altitud.pack(side="left", fill="x", expand=True, pady=3)

        self.w_terreno = ComboVar(p, "Tipo de terreno", [
            ("plano","Plano / llanura"), ("costa","Costa / litoral"),
            ("montaña","Montaña / sierra"), ("valles","Valles / cuencas"),
            ("desierto","Desierto / árido"), ("selva","Selva húmeda tropical"),
        ], default="plano")
        self.w_terreno.pack(fill="x", pady=3)

        self.w_densidad = ComboVar(p, "Densidad de población cercana", [
            ("baja","Baja — rural, despoblado"),
            ("media","Media — pequeñas comunidades"),
            ("alta","Alta — urbano / periurbano"),
        ], default="media")
        self.w_densidad.pack(fill="x", pady=3)

        # ── Sección 2: Recursos ──
        titulo_seccion(p, "2", "Recursos Naturales")

        self.w_solar = SliderVar(p, "Irradiación solar  [1=muy bajo · 9=Atacama]",
                                 1, 9, 4.5, step=0.1, sufijo=" kWh/m²/d")
        self.w_solar.pack(fill="x", pady=3)

        self.w_viento = SliderVar(p, "Velocidad media del viento  [0=sin viento · 15=costero]",
                                  0, 15, 5.0, step=0.1, sufijo=" m/s")
        self.w_viento.pack(fill="x", pady=3)

        self.w_hidro = SliderVar(p, "Caudal hídrico disponible  [0=sin ríos · 200=río grande]",
                                 0, 200, 10, step=1, sufijo=" m³/s", decimals=0)
        self.w_hidro.pack(fill="x", pady=3)

        self.w_geotermia = ComboVar(p, "Actividad geotérmica", [
            ("nula","Nula — sin evidencia"),("baja","Baja / posible"),
            ("media","Media — gradiente conocido"),("alta","Alta — fuentes termales activas"),
        ], default="nula")
        self.w_geotermia.pack(fill="x", pady=3)

        self.w_marino = ComboVar(p, "Potencial marino / offshore", [
            ("no","Sin acceso al mar"),("olas","Oleaje moderado"),
            ("mareas","Mareas significativas"),("alto","Offshore potente"),
        ], default="no")
        self.w_marino.pack(fill="x", pady=3)

        self.w_biomasa = ComboVar(p, "Disponibilidad de biomasa / residuos agrícolas", [
            ("nula","Nula"),("baja","Baja"),("media","Media"),
            ("alta","Alta — zona agroindustrial"),
        ], default="nula")
        self.w_biomasa.pack(fill="x", pady=3)

        # ── Sección 3: Demanda ──
        titulo_seccion(p, "3", "Demanda y Red Eléctrica")

        row2 = tk.Frame(p, bg=COLORES["bg"])
        row2.pack(fill="x")
        self.w_demanda = EntradaNum(row2, "Demanda estimada", 50, "MW")
        self.w_demanda.pack(side="left", fill="x", expand=True, padx=(0,8), pady=3)

        self.w_tipo_demanda = ComboVar(p, "Tipo de demanda principal", [
            ("residencial","Residencial"),("industrial","Industrial"),
            ("rural","Rural / comunidades aisladas"),("mixta","Mixta"),
        ], default="mixta")
        self.w_tipo_demanda.pack(fill="x", pady=3)

        self.w_red = ComboVar(p, "Conexión a red nacional", [
            ("si","Sí — conectado al SIN"),("debil","Débil / inestable"),
            ("no","No — zona aislada"),
        ], default="si")
        self.w_red.pack(fill="x", pady=3)

        self.w_fiabilidad = ComboVar(p, "Fiabilidad requerida", [
            ("alta","Alta — 24/7 sin interrupciones"),
            ("media","Media — interrupciones toleradas"),
            ("baja","Baja — suministro parcial"),
        ], default="media")
        self.w_fiabilidad.pack(fill="x", pady=3)

        # ── Sección 4: Economía ──
        titulo_seccion(p, "4", "Economía y Restricciones")

        row3 = tk.Frame(p, bg=COLORES["bg"])
        row3.pack(fill="x")
        self.w_presupuesto = EntradaNum(row3, "Presupuesto", 100, "MUSD")
        self.w_presupuesto.pack(side="left", fill="x", expand=True, padx=(0,8), pady=3)
        self.w_horizonte = EntradaNum(row3, "Horizonte", 20, "años")
        self.w_horizonte.pack(side="left", fill="x", expand=True, pady=3)

        self.w_prioridad = ComboVar(p, "Prioridad principal del proyecto", [
            ("costo","Minimizar costo — LCOE más bajo"),
            ("confiabilidad","Maximizar confiabilidad de suministro"),
            ("ambiental","Impacto ambiental mínimo"),
            ("rapido","Despliegue rápido"),
            ("empleo","Generación de empleo local"),
        ], default="costo")
        self.w_prioridad.pack(fill="x", pady=3)

        self.w_restricciones = CheckGroup(p, "Restricciones del territorio", [
            ("sismica","Zona sísmica"),("inundaciones","Riesgo inundaciones"),
            ("patrimonio","Área protegida"),("aves","Corredor aves migratorias"),
            ("conflicto","Conflicto social/minero"),("agua","Escasez hídrica severa"),
            ("transporte","Acceso vial deficiente"),
        ])
        self.w_restricciones.pack(fill="x", pady=3)

        # ── Sección 5: Parámetros finales ──
        titulo_seccion(p, "5", "Parámetros Finales")

        row4 = tk.Frame(p, bg=COLORES["bg"])
        row4.pack(fill="x")
        self.w_temp = EntradaNum(row4, "Temperatura promedio", 24, "°C")
        self.w_temp.pack(side="left", fill="x", expand=True, padx=(0,8), pady=3)
        self.w_precip = EntradaNum(row4, "Precipitación anual", 700, "mm")
        self.w_precip.pack(side="left", fill="x", expand=True, pady=3)

        self.w_existentes = CheckGroup(p, "Tecnologías ya instaladas en la zona", [
            ("solar","Solar fotovoltaica"),("eolica","Eólica terrestre"),
            ("hidro","Hidráulica"),("termica","Térmica convencional"),
        ])
        self.w_existentes.pack(fill="x", pady=3)

        self.w_experiencia = ComboVar(p, "Experiencia técnica local", [
            ("ninguna","Ninguna — equipo externo necesario"),
            ("basica","Básica — electricistas/técnicos generales"),
            ("media","Media — ingenieros locales disponibles"),
            ("alta","Alta — industria energética establecida"),
        ], default="basica")
        self.w_experiencia.pack(fill="x", pady=3)

        self.w_peso_amb = SliderVar(p, "Peso de sostenibilidad ambiental  [0=ignorar · 100=prioritario]",
                                    0, 100, 60, step=1, sufijo="%", decimals=0)
        self.w_peso_amb.pack(fill="x", pady=3)

        # Botones de acción
        separador(p, pady=12)
        btn_row = tk.Frame(p, bg=COLORES["bg"])
        btn_row.pack(fill="x", pady=(0, 16))

        btn_calc = tk.Button(btn_row, text="⚡  CALCULAR RECOMENDACIÓN",
                             command=self.calcular,
                             bg=COLORES["acento"], fg="#fff",
                             activebackground="#c0392b", activeforeground="#fff",
                             font=("Segoe UI", 11, "bold"), relief="flat",
                             padx=20, pady=10, cursor="hand2")
        btn_calc.pack(side="left", expand=True, fill="x", padx=(0,6))

        btn_limpiar = tk.Button(btn_row, text="↺ Limpiar",
                                command=self.limpiar_formulario,
                                bg=COLORES["card"], fg=COLORES["texto"],
                                activebackground=COLORES["borde"], activeforeground=COLORES["texto"],
                                font=FUENTE_NORMAL, relief="flat",
                                padx=14, pady=10, cursor="hand2")
        btn_limpiar.pack(side="right")

        # ── Columna derecha: resumen rápido ──
        right = tk.Frame(paned, bg=COLORES["panel"], padx=14, pady=14)
        paned.add(right, minsize=280)

        tk.Label(right, text="Resumen de parámetros",
                 bg=COLORES["panel"], fg=COLORES["acento"],
                 font=FUENTE_SUBTIT).pack(anchor="w", pady=(0, 10))

        self.texto_resumen = tk.Text(right, bg=COLORES["panel"], fg=COLORES["texto2"],
                                     font=FUENTE_MONO, relief="flat",
                                     state="disabled", wrap="word",
                                     height=30)
        self.texto_resumen.pack(fill="both", expand=True)

        # Actualizar resumen al cambiar sliders
        for w in [self.w_solar, self.w_viento, self.w_hidro, self.w_peso_amb]:
            w.slider.config(command=lambda v, _=None: self._actualizar_resumen())

    # ── TAB: RESULTADOS ───────────────────────
    def _construir_tab_resultados(self, parent):
        paned = tk.PanedWindow(parent, orient="horizontal",
                               bg=COLORES["bg"], sashwidth=4)
        paned.pack(fill="both", expand=True)

        # Panel izquierdo — ranking
        left = tk.Frame(paned, bg=COLORES["bg"], padx=14, pady=14)
        paned.add(left, minsize=360)

        tk.Label(left, text="Ranking de tecnologías",
                 bg=COLORES["bg"], fg=COLORES["acento"],
                 font=FUENTE_SUBTIT).pack(anchor="w", pady=(0, 8))

        # Canvas para barras
        self.canvas_ranking = tk.Canvas(left, bg=COLORES["bg"],
                                        highlightthickness=0, height=400)
        self.canvas_ranking.pack(fill="both", expand=True)

        # Panel derecho — detalle ganador + análisis
        right = ScrollFrame(paned)
        paned.add(right, minsize=340)
        rp = right.inner
        rp.configure(padx=14, pady=14)

        tk.Label(rp, text="Resultado y análisis",
                 bg=COLORES["bg"], fg=COLORES["acento"],
                 font=FUENTE_SUBTIT).pack(anchor="w", pady=(0, 8))

        # Card ganador
        self.card_ganador = tk.Frame(rp, bg=COLORES["card"],
                                     relief="flat", padx=14, pady=12)
        self.card_ganador.pack(fill="x", pady=(0, 10))
        self.lbl_ganador_icono = tk.Label(self.card_ganador, text="—",
                                          bg=COLORES["card"], fg=COLORES["amarillo"],
                                          font=("Segoe UI", 36))
        self.lbl_ganador_icono.pack(side="left", padx=(0, 12))
        info_frame = tk.Frame(self.card_ganador, bg=COLORES["card"])
        info_frame.pack(side="left", fill="x", expand=True)
        self.lbl_ganador_nombre = tk.Label(info_frame, text="Sin calcular",
                                           bg=COLORES["card"], fg=COLORES["texto"],
                                           font=("Segoe UI", 13, "bold"), anchor="w")
        self.lbl_ganador_nombre.pack(anchor="w")
        self.lbl_ganador_tipo = tk.Label(info_frame, text="",
                                         bg=COLORES["card"], fg=COLORES["texto2"],
                                         font=FUENTE_SMALL, anchor="w")
        self.lbl_ganador_tipo.pack(anchor="w")
        self.lbl_ganador_lcoe = tk.Label(info_frame, text="",
                                         bg=COLORES["card"], fg=COLORES["acento"],
                                         font=FUENTE_SMALL, anchor="w")
        self.lbl_ganador_lcoe.pack(anchor="w")
        self.lbl_ganador_score = tk.Label(self.card_ganador, text="—",
                                          bg=COLORES["card"], fg=COLORES["verde"],
                                          font=("Segoe UI", 26, "bold"))
        self.lbl_ganador_score.pack(side="right")

        # Factores clave
        separador(rp)
        tk.Label(rp, text="Factores determinantes",
                 bg=COLORES["bg"], fg=COLORES["texto2"],
                 font=FUENTE_SMALL).pack(anchor="w", pady=(0,6))
        self.frame_factores = tk.Frame(rp, bg=COLORES["bg"])
        self.frame_factores.pack(fill="x")

        # Resumen ejecutivo
        separador(rp)
        tk.Label(rp, text="Resumen ejecutivo",
                 bg=COLORES["bg"], fg=COLORES["texto2"],
                 font=FUENTE_SMALL).pack(anchor="w", pady=(0,6))
        self.txt_resumen_ejecutivo = tk.Text(rp, bg=COLORES["panel"], fg=COLORES["texto"],
                                             font=FUENTE_NORMAL, relief="flat",
                                             state="disabled", wrap="word", height=7,
                                             padx=10, pady=8)
        self.txt_resumen_ejecutivo.pack(fill="x", pady=(0,10))

        # Botones de exportar
        separador(rp)
        btn_exp = tk.Frame(rp, bg=COLORES["bg"])
        btn_exp.pack(fill="x", pady=6)
        for txt, cmd in [("📄 Exportar JSON", self.exportar_resultado_json),
                         ("📊 Exportar CSV", self.exportar_historial_csv),
                         ("📋 Exportar TXT", self.exportar_txt)]:
            tk.Button(btn_exp, text=txt, command=cmd,
                      bg=COLORES["card"], fg=COLORES["texto"],
                      activebackground=COLORES["borde"], activeforeground=COLORES["texto"],
                      font=FUENTE_SMALL, relief="flat", padx=10, pady=6,
                      cursor="hand2").pack(side="left", padx=(0,6))

    # ── LEER FORMULARIO ──────────────────────
    def _leer_datos(self):
        return {
            "region":       self.w_region.get(),
            "area":         self.w_area.get(),
            "altitud":      self.w_altitud.get(),
            "terreno":      self.w_terreno.get(),
            "densidad_pob": self.w_densidad.get(),
            "solar":        self.w_solar.get(),
            "viento":       self.w_viento.get(),
            "hidro":        self.w_hidro.get(),
            "geotermia":    self.w_geotermia.get(),
            "marino":       self.w_marino.get(),
            "biomasa":      self.w_biomasa.get(),
            "demanda":      self.w_demanda.get(),
            "tipo_demanda": self.w_tipo_demanda.get(),
            "red_nacional": self.w_red.get(),
            "fiabilidad":   self.w_fiabilidad.get(),
            "presupuesto":  self.w_presupuesto.get(),
            "horizonte":    self.w_horizonte.get(),
            "prioridad":    self.w_prioridad.get(),
            "restricciones":self.w_restricciones.get(),
            "temperatura":  self.w_temp.get(),
            "precipitacion":self.w_precip.get(),
            "existentes":   self.w_existentes.get(),
            "experiencia":  self.w_experiencia.get(),
            "peso_ambiental": self.w_peso_amb.get() / 100.0,
            "lat":          0,
        }

    def _cargar_datos(self, d):
        """Carga un dict de datos en todos los widgets del formulario."""
        self.w_region.set(d.get("region", ""))
        self.w_area.set(d.get("area", 500))
        self.w_altitud.set(d.get("altitud", 500))
        self.w_terreno.set_by_key(d.get("terreno", "plano"))
        self.w_densidad.set_by_key(d.get("densidad_pob", "media"))
        self.w_solar.set(d.get("solar", 4.5))
        self.w_viento.set(d.get("viento", 5.0))
        self.w_hidro.set(d.get("hidro", 10))
        self.w_geotermia.set_by_key(d.get("geotermia", "nula"))
        self.w_marino.set_by_key(d.get("marino", "no"))
        self.w_biomasa.set_by_key(d.get("biomasa", "nula"))
        self.w_demanda.set(d.get("demanda", 50))
        self.w_tipo_demanda.set_by_key(d.get("tipo_demanda", "mixta"))
        self.w_red.set_by_key(d.get("red_nacional", "si"))
        self.w_fiabilidad.set_by_key(d.get("fiabilidad", "media"))
        self.w_presupuesto.set(d.get("presupuesto", 100))
        self.w_horizonte.set(d.get("horizonte", 20))
        self.w_prioridad.set_by_key(d.get("prioridad", "costo"))
        self.w_restricciones.set(d.get("restricciones", []))
        self.w_temp.set(d.get("temperatura", 24))
        self.w_precip.set(d.get("precipitacion", 700))
        self.w_existentes.set(d.get("existentes", []))
        self.w_experiencia.set_by_key(d.get("experiencia", "basica"))
        self.w_peso_amb.set(int(d.get("peso_ambiental", 0.6) * 100))

    # ── CALCULAR ─────────────────────────────
    def calcular(self):
        datos = self._leer_datos()
        if not datos["region"]:
            messagebox.showwarning("Campo requerido", "Ingresa el nombre de la Región / País.")
            return

        scores = calcular_scores(datos)
        self.ultimo_scores = scores
        self.ultimos_datos = datos

        # Guardar en historial
        entrada = {
            "id":     len(self.historial) + 1,
            "fecha":  datetime.now().strftime("%d/%m/%Y %H:%M"),
            "datos":  datos,
            "scores": scores,
        }
        self.historial.append(entrada)

        self._mostrar_resultados(scores, datos)
        self._actualizar_resumen()
        self.nb.select(1)  # ir a pestaña Resultados

    # ── MOSTRAR RESULTADOS ───────────────────
    def _mostrar_resultados(self, scores, datos):
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        w_key, w_score = ranked[0]
        winner = TECNOLOGIAS[w_key]

        # Actualizar card ganador
        self.lbl_ganador_icono.config(text=winner["icono"])
        self.lbl_ganador_nombre.config(text=winner["nombre"])
        self.lbl_ganador_tipo.config(text=winner["tipo"])
        self.lbl_ganador_lcoe.config(text=f"LCOE estimado: {winner['lcoe']}")
        self.lbl_ganador_score.config(text=f"{w_score}/100")

        # Factores clave
        for widget in self.frame_factores.winfo_children():
            widget.destroy()
        factores = [
            ("Irradiación solar",  f"{datos['solar']:.1f} kWh/m²/d",  datos["solar"] >= 5),
            ("Velocidad viento",   f"{datos['viento']:.1f} m/s",       datos["viento"] >= 6),
            ("Caudal hídrico",     f"{datos['hidro']:.0f} m³/s",       datos["hidro"] >= 5),
            ("Presupuesto",        f"{datos['presupuesto']:.0f} MUSD",  datos["presupuesto"] >= 50),
        ]
        for nombre_f, valor_f, bueno in factores:
            row = tk.Frame(self.frame_factores, bg=COLORES["bg"])
            row.pack(fill="x", pady=2)
            ico = "✔" if bueno else "·"
            col = COLORES["verde"] if bueno else COLORES["texto2"]
            tk.Label(row, text=ico, bg=COLORES["bg"], fg=col,
                     font=FUENTE_NORMAL, width=2).pack(side="left")
            tk.Label(row, text=nombre_f, bg=COLORES["bg"], fg=COLORES["texto2"],
                     font=FUENTE_SMALL, width=18, anchor="w").pack(side="left")
            tk.Label(row, text=valor_f, bg=COLORES["bg"], fg=COLORES["texto"],
                     font=("Segoe UI", 9, "bold")).pack(side="left")

        if datos["restricciones"]:
            r_txt = "⚠ Restricciones: " + ", ".join(datos["restricciones"])
            tk.Label(self.frame_factores, text=r_txt, bg=COLORES["bg"],
                     fg=COLORES["amarillo"], font=FUENTE_SMALL, wraplength=300,
                     justify="left").pack(anchor="w", pady=(6,0))

        # Resumen ejecutivo
        alt2 = TECNOLOGIAS[ranked[1][0]]["nombre"]
        alt3 = TECNOLOGIAS[ranked[2][0]]["nombre"]
        region = datos["region"] or "el territorio evaluado"
        resumen = (
            f"Para {region}, el análisis de 9 tecnologías indica que "
            f"{winner['nombre']} es la opción más conveniente (score {w_score}/100).\n\n"
            f"Como alternativas se evalúan {alt2} ({ranked[1][1]} pts) y "
            f"{alt3} ({ranked[2][1]} pts).\n\n"
            "Se recomienda complementar con estudios de prefactibilidad y "
            "medición in-situ antes de la decisión de inversión."
        )
        self.txt_resumen_ejecutivo.config(state="normal")
        self.txt_resumen_ejecutivo.delete("1.0", "end")
        self.txt_resumen_ejecutivo.insert("end", resumen)
        self.txt_resumen_ejecutivo.config(state="disabled")

        # Dibujar barras ranking
        self._dibujar_ranking(ranked)

    def _dibujar_ranking(self, ranked):
        c = self.canvas_ranking
        c.delete("all")
        c.update_idletasks()
        W = c.winfo_width() or 400
        max_score = ranked[0][1] if ranked[0][1] > 0 else 1
        row_h = 40
        pad_x = 10
        lbl_w = 200
        bar_max = W - lbl_w - 70 - pad_x * 2
        medallas = ["★","②","③","④","⑤","⑥","⑦","⑧","⑨"]
        colores_rank = [
            COLORES["acento"], COLORES["amarillo"], "#5dade2",
            "#abebc6","#d2b4de","#a9cce3","#f9e79f","#f5cba7","#d7dbdd"
        ]

        for i, (key, score) in enumerate(ranked):
            tec = TECNOLOGIAS[key]
            y = pad_x + i * row_h + row_h // 2
            col = colores_rank[i] if i < len(colores_rank) else "#888"

            # Medalla
            c.create_text(pad_x + 12, y, text=medallas[i] if i<9 else str(i+1),
                          fill=col, font=("Segoe UI", 10, "bold"), anchor="center")
            # Icono + nombre
            c.create_text(pad_x + 26, y, text=f"{tec['icono']} {tec['nombre']}",
                          fill=COLORES["texto"] if i < 3 else COLORES["texto2"],
                          font=FUENTE_SMALL, anchor="w")
            # Barra
            bx = pad_x + lbl_w
            bw = int((score / max_score) * bar_max) if bar_max > 0 else 0
            c.create_rectangle(bx, y - 10, bx + bar_max, y + 10,
                                fill=COLORES["borde"], outline="")
            if bw > 0:
                c.create_rectangle(bx, y - 10, bx + bw, y + 10,
                                   fill=col, outline="")
            # Score
            c.create_text(bx + bar_max + 8, y, text=str(score),
                          fill=col if i < 3 else COLORES["texto2"],
                          font=("Segoe UI", 9, "bold"), anchor="w")

        total_h = pad_x * 2 + len(ranked) * row_h
        c.config(height=total_h)

    # ── RESUMEN EN TAB FORMULARIO ────────────
    def _actualizar_resumen(self):
        try:
            d = self._leer_datos()
        except Exception:
            return
        lineas = [
            f"  Región        : {d['region'] or '—'}",
            f"  Área          : {d['area']:.0f} ha",
            f"  Terreno       : {d['terreno']}",
            "",
            f"  Solar         : {d['solar']:.1f} kWh/m²/d",
            f"  Viento        : {d['viento']:.1f} m/s",
            f"  Caudal        : {d['hidro']:.0f} m³/s",
            f"  Geotermia     : {d['geotermia']}",
            f"  Marino        : {d['marino']}",
            f"  Biomasa       : {d['biomasa']}",
            "",
            f"  Demanda       : {d['demanda']:.0f} MW",
            f"  Red nacional  : {d['red_nacional']}",
            f"  Fiabilidad    : {d['fiabilidad']}",
            "",
            f"  Presupuesto   : {d['presupuesto']:.0f} MUSD",
            f"  Horizonte     : {d['horizonte']:.0f} años",
            f"  Prioridad     : {d['prioridad']}",
            "",
            f"  Temperatura   : {d['temperatura']:.1f} °C",
            f"  Precipitación : {d['precipitacion']:.0f} mm",
            f"  Sos. ambiental: {int(d['peso_ambiental']*100)}%",
        ]
        if d["restricciones"]:
            lineas += ["", f"  Restricciones :"]
            for r in d["restricciones"]:
                lineas.append(f"    · {r}")
        if d["existentes"]:
            lineas += ["", f"  Ya instaladas :"]
            for e in d["existentes"]:
                lineas.append(f"    · {e}")

        self.texto_resumen.config(state="normal")
        self.texto_resumen.delete("1.0", "end")
        self.texto_resumen.insert("end", "\n".join(lineas))
        self.texto_resumen.config(state="disabled")

    # ── LIMPIAR FORMULARIO ───────────────────
    def limpiar_formulario(self):
        if messagebox.askyesno("Limpiar", "¿Restablecer todos los campos al valor predeterminado?"):
            self._cargar_datos({
                "region":"", "area":500, "altitud":500, "terreno":"plano",
                "densidad_pob":"media", "solar":4.5, "viento":5.0, "hidro":10,
                "geotermia":"nula", "marino":"no", "biomasa":"nula",
                "demanda":50, "tipo_demanda":"mixta", "red_nacional":"si",
                "fiabilidad":"media", "presupuesto":100, "horizonte":20,
                "prioridad":"costo", "restricciones":[], "temperatura":24,
                "precipitacion":700, "existentes":[], "experiencia":"basica",
                "peso_ambiental":0.6,
            })

    # ── MANEJO DE ARCHIVOS ───────────────────

    def guardar_evaluacion(self):
        """Guarda la evaluación actual (formulario) en un JSON."""
        datos = self._leer_datos()
        payload = {
            "version": "EnergyMap v2.0",
            "tipo": "evaluacion",
            "exportado": datetime.now().isoformat(),
            "datos": datos,
        }
        ruta = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            initialfile=f"evaluacion_{datos['region'].replace(' ','_') or 'sin_region'}_{datetime.now().strftime('%Y%m%d')}.json",
            title="Guardar evaluación",
        )
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Guardado", f"Evaluación guardada en:\n{ruta}")

    def cargar_archivo(self):
        """Carga un JSON de evaluación individual o historial."""
        ruta = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            title="Cargar evaluación o historial",
        )
        if not ruta:
            return
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
            return

        if payload.get("tipo") == "historial":
            n = len(payload.get("historial", []))
            self.historial = payload["historial"]
            messagebox.showinfo("Cargado", f"Historial cargado: {n} evaluaciones.")
        elif payload.get("tipo") == "evaluacion" and "datos" in payload:
            self._cargar_datos(payload["datos"])
            self._actualizar_resumen()
            messagebox.showinfo("Cargado", "Evaluación cargada en el formulario.")
            self.nb.select(0)
        else:
            messagebox.showwarning("Formato no reconocido",
                                   "El archivo no tiene el formato EnergyMap esperado.")

    def exportar_resultado_json(self):
        """Exporta historial completo como JSON."""
        if not self.historial:
            messagebox.showwarning("Sin datos", "Realiza al menos una evaluación primero.")
            return
        payload = {
            "version": "EnergyMap v2.0",
            "tipo": "historial",
            "exportado": datetime.now().isoformat(),
            "total": len(self.historial),
            "historial": self.historial,
        }
        ruta = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            initialfile=f"energymap_historial_{datetime.now().strftime('%Y%m%d')}.json",
            title="Exportar historial JSON",
        )
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Exportado", f"Historial exportado en:\n{ruta}")

    def exportar_historial_csv(self):
        """Exporta historial como CSV."""
        if not self.historial:
            messagebox.showwarning("Sin datos", "Realiza al menos una evaluación primero.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile=f"energymap_{datetime.now().strftime('%Y%m%d')}.csv",
            title="Exportar historial CSV",
        )
        if not ruta:
            return
        cols = ["id","fecha","region","solar","viento","hidro","presupuesto",
                "horizonte","prioridad","restricciones","ganador","score_ganador",
                "2do","score_2do","3ro","score_3ro"]
        with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=cols)
            writer.writeheader()
            for e in self.historial:
                ranked = sorted(e["scores"].items(), key=lambda x: x[1], reverse=True)
                d = e["datos"]
                writer.writerow({
                    "id": e["id"],
                    "fecha": e["fecha"],
                    "region": d.get("region",""),
                    "solar": d.get("solar",""),
                    "viento": d.get("viento",""),
                    "hidro": d.get("hidro",""),
                    "presupuesto": d.get("presupuesto",""),
                    "horizonte": d.get("horizonte",""),
                    "prioridad": d.get("prioridad",""),
                    "restricciones": "|".join(d.get("restricciones",[])),
                    "ganador": TECNOLOGIAS[ranked[0][0]]["nombre"],
                    "score_ganador": ranked[0][1],
                    "2do": TECNOLOGIAS[ranked[1][0]]["nombre"],
                    "score_2do": ranked[1][1],
                    "3ro": TECNOLOGIAS[ranked[2][0]]["nombre"],
                    "score_3ro": ranked[2][1],
                })
        messagebox.showinfo("Exportado", f"CSV exportado en:\n{ruta}")

    def exportar_txt(self):
        """Exporta el informe del último resultado como TXT."""
        if not hasattr(self, "ultimo_scores"):
            messagebox.showwarning("Sin datos", "Realiza una evaluación primero.")
            return
        ranked = sorted(self.ultimo_scores.items(), key=lambda x: x[1], reverse=True)
        d = self.ultimos_datos
        w_key, w_score = ranked[0]
        winner = TECNOLOGIAS[w_key]
        lineas = [
            "╔══════════════════════════════════════════════════════════════════╗",
            "║          ASESOR DE ENERGÍA RENOVABLE — EnergyMap v2.0            ║",
            "╚══════════════════════════════════════════════════════════════════╝",
            f"  Fecha        : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"  Región       : {d['region'] or 'Sin especificar'}",
            "",
            "  ★ TECNOLOGÍA RECOMENDADA",
            f"  {winner['icono']}  {winner['nombre']}",
            f"     LCOE     : {winner['lcoe']}",
            f"     Tipo     : {winner['tipo']}",
            f"     Score    : {w_score}/100",
            "",
            "  RANKING COMPLETO",
        ]
        medallas = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨"]
        for i, (key, score) in enumerate(ranked):
            tec = TECNOLOGIAS[key]
            barra = "█" * int(score / 5) + "░" * (20 - int(score / 5))
            lineas.append(f"  {medallas[i]}  {tec['nombre']:<32} {barra}  {score:3d}")
        lineas += [
            "",
            "  FACTORES CLAVE",
            f"    Solar     : {d['solar']:.1f} kWh/m²/d",
            f"    Viento    : {d['viento']:.1f} m/s",
            f"    Hidro     : {d['hidro']:.0f} m³/s",
            f"    Presup.   : {d['presupuesto']:.0f} MUSD",
        ]
        if d["restricciones"]:
            lineas.append(f"    Restricciones: {', '.join(d['restricciones'])}")
        lineas += [
            "",
            "  RESUMEN EJECUTIVO",
            f"  Para {d['region'] or 'el territorio'}, el análisis de 9 tecnologías",
            f"  indica que {winner['nombre']} es la opción más conveniente",
            f"  (score {w_score}/100). Alternativas: {TECNOLOGIAS[ranked[1][0]]['nombre']}",
            f"  ({ranked[1][1]} pts) y {TECNOLOGIAS[ranked[2][0]]['nombre']} ({ranked[2][1]} pts).",
            "",
            "  Se recomienda complementar con estudios de prefactibilidad",
            "  y medición in-situ antes de la decisión de inversión.",
            "═" * 68,
        ]

        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
            initialfile=f"informe_{d['region'].replace(' ','_') or 'evaluacion'}_{datetime.now().strftime('%Y%m%d')}.txt",
            title="Exportar informe TXT",
        )
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("\n".join(lineas))
            messagebox.showinfo("Exportado", f"Informe exportado en:\n{ruta}")

    # ── VENTANA HISTORIAL ────────────────────
    def ver_historial(self):
        win = tk.Toplevel(self)
        win.title("Historial de evaluaciones — EnergyMap")
        win.geometry("820x480")
        win.configure(bg=COLORES["bg"])
        win.grab_set()

        tk.Label(win, text="Historial de evaluaciones",
                 bg=COLORES["bg"], fg=COLORES["acento"],
                 font=FUENTE_TITULO).pack(anchor="w", padx=16, pady=(14,8))

        cols = ("id","fecha","region","ganador","score","prioridad")
        tree = ttk.Treeview(win, columns=cols, show="headings", selectmode="browse")
        encabezados = {"id":"#","fecha":"Fecha","region":"Región","ganador":"Tecnología recomendada","score":"Score","prioridad":"Prioridad"}
        anchos      = {"id":35,"fecha":110,"region":140,"ganador":190,"score":55,"prioridad":110}
        for c in cols:
            tree.heading(c, text=encabezados[c])
            tree.column(c, width=anchos[c], anchor="center" if c in ("id","score") else "w")

        for e in reversed(self.historial):
            ranked = sorted(e["scores"].items(), key=lambda x: x[1], reverse=True)
            tree.insert("", "end",
                        values=(e["id"], e["fecha"],
                                e["datos"].get("region","—"),
                                TECNOLOGIAS[ranked[0][0]]["nombre"],
                                ranked[0][1],
                                e["datos"].get("prioridad","—")),
                        tags=(str(e["id"]),))

        scrollb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollb.set)
        tree.pack(side="left", fill="both", expand=True, padx=(16,0), pady=(0,12))
        scrollb.pack(side="left", fill="y", pady=(0,12), padx=(0,8))

        btn_frame = tk.Frame(win, bg=COLORES["bg"])
        btn_frame.pack(side="right", fill="y", padx=12, pady=8)

        def cargar_seleccion():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0])["values"]
            eid = int(vals[0])
            entry = next((e for e in self.historial if e["id"]==eid), None)
            if entry:
                self._cargar_datos(entry["datos"])
                self._mostrar_resultados(entry["scores"], entry["datos"])
                self._actualizar_resumen()
                self.nb.select(0)
                win.destroy()
                messagebox.showinfo("Cargado", f"Evaluación #{eid} restaurada al formulario.")

        def eliminar_seleccion():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0])["values"]
            eid = int(vals[0])
            if messagebox.askyesno("Eliminar", f"¿Eliminar evaluación #{eid}?"):
                self.historial = [e for e in self.historial if e["id"]!=eid]
                tree.delete(sel[0])

        for txt, cmd in [("📂 Cargar en formulario", cargar_seleccion),
                         ("🗑 Eliminar", eliminar_seleccion),
                         ("📄 Exportar JSON", lambda: (win.destroy(), self.exportar_resultado_json())),
                         ("📊 Exportar CSV",  lambda: (win.destroy(), self.exportar_historial_csv()))]:
            tk.Button(btn_frame, text=txt, command=cmd,
                      bg=COLORES["card"], fg=COLORES["texto"],
                      activebackground=COLORES["acento"], activeforeground="#fff",
                      font=FUENTE_SMALL, relief="flat", padx=10, pady=8,
                      cursor="hand2", width=22).pack(pady=4, fill="x")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = EnergyMapApp()
    app.mainloop()
