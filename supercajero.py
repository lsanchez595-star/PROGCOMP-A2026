"""
S U P E R C A J E R O  —  versión con personajes + escáner de cámara
Escáner: OpenCV + pyzbar via celular (DroidCam u otra cámara IP/USB)
"""

# ─────────────────────────────────────────────────────────────────
#  IMPORTS
# ─────────────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import csv, json, os, sys, math, datetime, threading, queue, base64, io
from pathlib import Path

try:
    from PIL import Image, ImageTk, ImageDraw, ImageOps
    PIL_OK = True
except ImportError:
    PIL_OK = False

# Escáner de códigos de barras
try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False

try:
    from pyzbar import pyzbar
    PYZBAR_OK = True
except ImportError:
    PYZBAR_OK = False


# ─────────────────────────────────────────────────────────────────
#  IMÁGENES DE PERSONAJES (base64 embebido)
# ─────────────────────────────────────────────────────────────────
# Importamos desde img_data.py generado aparte
try:
    from img_data import IMG_MAYA, IMG_TOMAS, IMG_ROSA, IMG_VALENTINA, IMG_ELENA
    IMGS_OK = True
except ImportError:
    IMGS_OK = False


def b64_to_pil(b64_str: str, size=(60, 60)) -> "Image.Image | None":
    """Convierte base64 a imagen PIL recortada en círculo."""
    if not PIL_OK or not b64_str:
        return None
    try:
        data = base64.b64decode(b64_str)
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        # Recortar región superior (cara)
        w, h = img.size
        crop_h = int(h * 0.65)
        img = img.crop((0, 0, w, crop_h))
        img = img.resize(size, Image.LANCZOS)
        # Máscara circular
        mask = Image.new("L", size, 0)
        d = ImageDraw.Draw(mask)
        d.ellipse((0, 0, size[0]-1, size[1]-1), fill=255)
        output = Image.new("RGBA", size, (0, 0, 0, 0))
        output.paste(img, (0, 0), mask)
        return output
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────
#  PERSONAJES
# ─────────────────────────────────────────────────────────────────
CUSTOMERS_DATA = [
    {"id": 1, "name": "Maya",      "emoji": "💙", "role": "Clienta habitual",   "b64_key": "IMG_MAYA"},
    {"id": 2, "name": "Tomás",     "emoji": "💚", "role": "Cliente frecuente",  "b64_key": "IMG_TOMAS"},
    {"id": 3, "name": "Rosa",      "emoji": "💜", "role": "Clienta fiel",       "b64_key": "IMG_ROSA"},
    {"id": 4, "name": "Valentina", "emoji": "🌸", "role": "Clienta challenge",  "b64_key": "IMG_VALENTINA"},
    {"id": 5, "name": "Elena",     "emoji": "☕", "role": "Clienta tranquila",  "b64_key": "IMG_ELENA"},
]


# ─────────────────────────────────────────────────────────────────
#  DOMINIO
# ─────────────────────────────────────────────────────────────────
class Producto:
    def __init__(self, codigo, nombre, precio, categoria="", emoji="📦"):
        self.codigo    = codigo
        self.nombre    = nombre
        self.precio    = float(precio)
        self.categoria = categoria
        self.emoji     = emoji

    def to_dict(self):
        return {"codigo": self.codigo, "nombre": self.nombre,
                "precio": self.precio, "categoria": self.categoria, "emoji": self.emoji}


class ItemCarrito:
    def __init__(self, producto, cantidad=1):
        self.producto = producto
        self.cantidad = cantidad

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad

    def to_dict(self):
        return {**self.producto.to_dict(), "cantidad": self.cantidad, "subtotal": self.subtotal}


class Carrito:
    IVA_RATE = 0.19

    def __init__(self):
        self._items: dict[str, ItemCarrito] = {}

    def agregar(self, producto, cantidad=1):
        if producto.codigo in self._items:
            self._items[producto.codigo].cantidad += cantidad
        else:
            self._items[producto.codigo] = ItemCarrito(producto, cantidad)

    def eliminar(self, codigo):
        self._items.pop(codigo, None)

    def actualizar_cantidad(self, codigo, cantidad):
        if cantidad <= 0:
            self.eliminar(codigo)
        elif codigo in self._items:
            self._items[codigo].cantidad = cantidad

    def vaciar(self):
        self._items.clear()

    @property
    def items(self):
        return list(self._items.values())

    @property
    def subtotal_sin_iva(self):
        return sum(i.subtotal for i in self.items)

    @property
    def iva(self):
        return self.subtotal_sin_iva * self.IVA_RATE

    @property
    def total(self):
        return self.subtotal_sin_iva + self.iva

    @property
    def num_productos(self):
        return sum(i.cantidad for i in self.items)

    def esta_vacio(self):
        return len(self._items) == 0


class Factura:
    _counter = 1

    def __init__(self, carrito, metodo_pago="Efectivo", cliente=None):
        self.numero      = f"FAC-{datetime.date.today().strftime('%Y%m%d')}-{Factura._counter:04d}"
        Factura._counter += 1
        self.fecha       = datetime.datetime.now()
        self.items       = [ItemCarrito(i.producto, i.cantidad) for i in carrito.items]
        self.subtotal    = carrito.subtotal_sin_iva
        self.iva         = carrito.iva
        self.total       = carrito.total
        self.metodo_pago = metodo_pago
        self.cliente     = cliente   # dict con name/emoji/role o None
        self.pagado      = 0.0
        self.cambio      = 0.0

    def registrar_pago(self, monto):
        self.pagado = monto
        self.cambio = max(0, monto - self.total)

    def texto_recibo(self):
        sep  = "─" * 46
        sep2 = "═" * 46
        lines = [
            "SUPERMERCADO CLAUDE",
            "NIT: 900.123.456-7   Tel: (607) 555-0199",
            sep2,
            f"Factura : {self.numero}",
            f"Fecha   : {self.fecha.strftime('%d/%m/%Y  %H:%M')}",
            f"Pago    : {self.metodo_pago}",
        ]
        if self.cliente:
            lines.append(f"Cliente : {self.cliente['emoji']} {self.cliente['name']} ({self.cliente['role']})")
        lines += [
            sep,
            f"{'PRODUCTO':<24} {'CANT':>4} {'PRECIO':>9} {'SUBTOT':>9}",
            sep,
        ]
        for item in self.items:
            n = (item.producto.emoji + " " + item.producto.nombre)[:23]
            lines.append(f"{n:<24} {item.cantidad:>4} {item.producto.precio:>9,.0f} {item.subtotal:>9,.0f}")
        lines += [
            sep,
            f"{'Subtotal (sin IVA)':>34}  {self.subtotal:>9,.0f}",
            f"{'IVA (19%)':>34}  {self.iva:>9,.0f}",
            sep2,
            f"{'TOTAL':>34}  {self.total:>9,.0f}",
            sep,
            f"{'Pagado':>34}  {self.pagado:>9,.0f}",
            f"{'Cambio':>34}  {self.cambio:>9,.0f}",
            sep2,
            "",
            "  ¡Gracias por su compra!",
            "  Conserve su factura.",
            sep2,
        ]
        return "\n".join(lines)


class RegistroDiario:
    def __init__(self):
        self.facturas: list[Factura] = []
        self.fecha = datetime.date.today()

    def registrar(self, factura):
        self.facturas.append(factura)

    @property
    def total_ventas(self):
        return sum(f.total for f in self.facturas)

    @property
    def num_transacciones(self):
        return len(self.facturas)

    def exportar_csv(self, ruta):
        rows = []
        for f in self.facturas:
            for item in f.items:
                rows.append({
                    "factura": f.numero, "fecha": f.fecha.strftime("%Y-%m-%d %H:%M:%S"),
                    "codigo": item.producto.codigo, "producto": item.producto.nombre,
                    "categoria": item.producto.categoria, "cantidad": item.cantidad,
                    "precio_unit": item.producto.precio, "subtotal": item.subtotal,
                    "iva_factura": f.iva, "total_factura": f.total,
                    "metodo_pago": f.metodo_pago,
                    "cliente": f.cliente["name"] if f.cliente else "Anónimo",
                })
        with open(ruta, "w", newline="", encoding="utf-8") as fp:
            if not rows:
                fp.write("Sin transacciones\n"); return
            w = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)

    def resumen_texto(self):
        sep = "═" * 46
        lines = [sep, f"  RESUMEN DEL DÍA  {self.fecha.strftime('%d/%m/%Y')}", sep,
                 f"  Transacciones : {self.num_transacciones}",
                 f"  Total ventas  : ${self.total_ventas:>12,.0f}", sep]
        conteo = {}
        for f in self.facturas:
            for item in f.items:
                k = item.producto.codigo
                if k not in conteo:
                    conteo[k] = {"nombre": item.producto.nombre, "qty": 0, "rev": 0.0}
                conteo[k]["qty"] += item.cantidad
                conteo[k]["rev"] += item.subtotal
        if conteo:
            top = sorted(conteo.values(), key=lambda x: x["rev"], reverse=True)[:5]
            lines.append("  TOP 5 PRODUCTOS POR INGRESOS")
            lines.append("─" * 46)
            for i, t in enumerate(top, 1):
                lines.append(f"  {i}. {t['nombre'][:26]:<26} ${t['rev']:>10,.0f}")
        lines.append(sep)
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
#  ESCÁNER DE CÁMARA  (hilo separado)
# ─────────────────────────────────────────────────────────────────
class EscanerCamara:
    """
    Lee frames de OpenCV (webcam local o DroidCam IP/USB) y detecta
    códigos de barras con pyzbar. Pone los resultados en una cola.
    """
    def __init__(self, source=0):
        self.source   = source   # 0=webcam, URL=DroidCam IP, 1/2=otro índice
        self.cola     = queue.Queue()
        self._running = False
        self._thread  = None
        self._cap     = None

    def iniciar(self, source=None):
        if source is not None:
            self.source = source
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def detener(self):
        self._running = False
        if self._cap:
            self._cap.release()
            self._cap = None

    def _loop(self):
        try:
            self._cap = cv2.VideoCapture(self.source)
            if not self._cap.isOpened():
                self.cola.put(("ERROR", f"No se pudo abrir la fuente: {self.source}"))
                return
            self.cola.put(("LISTO", "Cámara conectada"))
            last_code = None
            cooldown  = 0
            while self._running:
                ret, frame = self._cap.read()
                if not ret:
                    continue
                # Escalar para velocidad
                h, w = frame.shape[:2]
                scale = min(1.0, 640 / w)
                if scale < 1.0:
                    frame = cv2.resize(frame, (int(w*scale), int(h*scale)))
                # Enviar frame a la GUI para previsualización
                self.cola.put(("FRAME", frame))
                # Decodificar
                if cooldown > 0:
                    cooldown -= 1
                    continue
                barcodes = pyzbar.decode(frame)
                for bc in barcodes:
                    code = bc.data.decode("utf-8")
                    if code != last_code:
                        last_code = code
                        cooldown  = 20   # ~0.7s de pausa para no repetir
                        self.cola.put(("CODIGO", code))
        except Exception as e:
            self.cola.put(("ERROR", str(e)))
        finally:
            if self._cap:
                self._cap.release()


# ─────────────────────────────────────────────────────────────────
#  COLORES Y FUENTES
# ─────────────────────────────────────────────────────────────────
BG      = "#f5f7fa"
BG2     = "#ffffff"
SIDEBAR = "#1a2332"
ACCENT  = "#00b86b"
ACCENT2 = "#0077cc"
DANGER  = "#e53e3e"
GOLD    = "#f6ad55"
TEXT    = "#1a202c"
TEXTL   = "#718096"
BORDER  = "#e2e8f0"
PINK    = "#e879a0"

FONT_TITLE = ("Georgia", 20, "bold")
FONT_BIG   = ("Helvetica", 13, "bold")
FONT_BODY  = ("Helvetica", 10)
FONT_MONO  = ("Courier New", 10)
FONT_SM    = ("Helvetica", 9)
FONT_CHAR  = ("Helvetica", 9, "bold")


def btn(parent, text, cmd, color=ACCENT, fg="white", **kw):
    kw.setdefault("padx", 12); kw.setdefault("pady", 6)
    b = tk.Button(parent, text=text, command=cmd, bg=color, fg=fg,
                  relief="flat", font=("Helvetica", 10, "bold"),
                  cursor="hand2", activebackground=_dk(color), activeforeground=fg, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=_dk(color)))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b

def _dk(h, f=0.85):
    h = h.lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

def sep(parent, color=BORDER):
    tk.Frame(parent, bg=color, height=1).pack(fill=tk.X, pady=4)


# ─────────────────────────────────────────────────────────────────
#  PANEL DE PERSONAJES
# ─────────────────────────────────────────────────────────────────
class CustomerBar(tk.Frame):
    """Barra horizontal con los 5 personajes + botón anónimo."""

    AVATAR_SIZE = (54, 54)

    def __init__(self, parent, on_select):
        super().__init__(parent, bg=BG2, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self.on_select       = on_select
        self.selected_id     = None
        self._photo_refs     = {}   # evitar GC
        self._btn_refs       = {}
        self._build()

    def _build(self):
        tk.Label(self, text="Cliente:", bg=BG2, fg=TEXTL,
                 font=FONT_SM).pack(side=tk.LEFT, padx=(10, 6), pady=8)

        # Botón anónimo
        self._add_customer_btn(None, "👤", "Anónimo", None)

        # Personajes
        for c in CUSTOMERS_DATA:
            b64 = globals().get(c["b64_key"]) if IMGS_OK else None
            img = b64_to_pil(b64, self.AVATAR_SIZE) if b64 else None
            self._add_customer_btn(c["id"], c["emoji"], c["name"], img)

        # Badge del cliente activo (lado derecho)
        self._badge = tk.Frame(self, bg="#e8f7ef", bd=1, relief="solid",
                               highlightbackground=ACCENT, highlightthickness=1)
        self._badge.pack(side=tk.RIGHT, padx=10, pady=6, ipadx=8, ipady=4)
        self._badge_img_lbl = tk.Label(self._badge, bg="#e8f7ef")
        self._badge_img_lbl.pack(side=tk.LEFT, padx=(4, 6))
        bf = tk.Frame(self._badge, bg="#e8f7ef")
        bf.pack(side=tk.LEFT)
        tk.Label(bf, text="Atendiendo a:", bg="#e8f7ef", fg=TEXTL,
                 font=("Helvetica", 8)).pack(anchor="w")
        self._badge_name = tk.Label(bf, text="—", bg="#e8f7ef",
                                    fg=ACCENT, font=("Helvetica", 11, "bold"))
        self._badge_name.pack(anchor="w")
        self._badge.pack_forget()   # oculto al inicio

    def _add_customer_btn(self, cid, emoji, name, pil_img):
        frame = tk.Frame(self, bg=BG2, cursor="hand2", bd=1,
                         relief="solid", highlightbackground=BORDER,
                         highlightthickness=1)
        frame.pack(side=tk.LEFT, padx=3, pady=6, ipadx=4, ipady=3)

        if pil_img and PIL_OK:
            photo = ImageTk.PhotoImage(pil_img)
            self._photo_refs[cid] = photo
            lbl_img = tk.Label(frame, image=photo, bg=BG2)
            lbl_img.pack()
        else:
            tk.Label(frame, text=emoji, bg=BG2,
                     font=("Segoe UI Emoji", 22)).pack()

        tk.Label(frame, text=name, bg=BG2, fg=TEXT,
                 font=FONT_CHAR).pack()

        for w in [frame] + list(frame.winfo_children()):
            w.bind("<Button-1>", lambda e, i=cid: self._select(i))
            w.bind("<Enter>",    lambda e, f=frame: f.config(bg="#e8f7ef", highlightbackground=ACCENT))
            w.bind("<Leave>",    lambda e, f=frame: self._restore_frame(f, f._cid if hasattr(f,'_cid') else None))

        frame._cid = cid
        self._btn_refs[cid] = frame

    def _restore_frame(self, frame, cid):
        if cid == self.selected_id:
            frame.config(bg="#d4f0e4", highlightbackground=ACCENT)
        else:
            frame.config(bg=BG2, highlightbackground=BORDER)

    def _select(self, cid):
        # Resetear todos
        for fid, frame in self._btn_refs.items():
            frame.config(bg=BG2, highlightbackground=BORDER)
            for w in frame.winfo_children():
                w.config(bg=BG2)
        # Marcar seleccionado
        self.selected_id = cid
        if cid in self._btn_refs:
            f = self._btn_refs[cid]
            f.config(bg="#d4f0e4", highlightbackground=ACCENT)
            for w in f.winfo_children():
                w.config(bg="#d4f0e4")
        # Badge
        cdata = next((c for c in CUSTOMERS_DATA if c["id"]==cid), None)
        if cdata:
            self._badge.pack(side=tk.RIGHT, padx=10, pady=6, ipadx=8, ipady=4)
            self._badge_name.config(text=f"{cdata['emoji']} {cdata['name']}")
            photo = self._photo_refs.get(cid)
            if photo:
                self._badge_img_lbl.config(image=photo)
        else:
            self._badge.pack_forget()
        self.on_select(cdata)

    def get_selected(self):
        return next((c for c in CUSTOMERS_DATA if c["id"]==self.selected_id), None)


# ─────────────────────────────────────────────────────────────────
#  VENTANA DE ESCÁNER
# ─────────────────────────────────────────────────────────────────
class ScannerWindow(tk.Toplevel):
    """
    Ventana flotante con previsualización de la cámara y detección
    de códigos de barras en tiempo real.
    """
    PREVIEW_W = 480
    PREVIEW_H = 320

    def __init__(self, master, catalogo: list, on_detected):
        super().__init__(master)
        self.title("📷 Escáner de Código de Barras")
        self.configure(bg=BG)
        self.geometry("520x500")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.catalogo    = catalogo
        self.on_detected = on_detected
        self.escaner     = EscanerCamara()
        self._running    = False
        self._photo_ref  = None

        self._build()
        self._ask_source()

    # ── UI ───────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=ACCENT, padx=14, pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="📷  Escáner de Cámara", bg=ACCENT, fg="white",
                 font=("Georgia", 13, "bold")).pack(side=tk.LEFT)
        self._status_lbl = tk.Label(hdr, text="Configurando...", bg=ACCENT,
                                    fg="#c6f6d5", font=FONT_SM)
        self._status_lbl.pack(side=tk.RIGHT)

        # Canvas de previsualización
        self._canvas = tk.Canvas(self, width=self.PREVIEW_W, height=self.PREVIEW_H,
                                 bg="#0d1b2a", highlightthickness=0)
        self._canvas.pack(pady=8)
        self._canvas.create_text(self.PREVIEW_W//2, self.PREVIEW_H//2,
                                 text="Esperando cámara...", fill="#4a7fa5",
                                 font=("Helvetica", 13))
        # Marco de escaneo animado
        m = 30
        for coords, color in [
            ((m, m, m+20, m), "#00b86b"), ((m, m, m, m+20), "#00b86b"),
            ((self.PREVIEW_W-m, m, self.PREVIEW_W-m-20, m), "#00b86b"),
            ((self.PREVIEW_W-m, m, self.PREVIEW_W-m, m+20), "#00b86b"),
            ((m, self.PREVIEW_H-m, m+20, self.PREVIEW_H-m), "#00b86b"),
            ((m, self.PREVIEW_H-m, m, self.PREVIEW_H-m-20), "#00b86b"),
            ((self.PREVIEW_W-m, self.PREVIEW_H-m, self.PREVIEW_W-m-20, self.PREVIEW_H-m), "#00b86b"),
            ((self.PREVIEW_W-m, self.PREVIEW_H-m, self.PREVIEW_W-m, self.PREVIEW_H-m-20), "#00b86b"),
        ]:
            self._canvas.create_line(*coords, fill=color, width=3)

        # Último código detectado
        det_f = tk.Frame(self, bg=BG2, bd=1, relief="solid", padx=12, pady=8)
        det_f.pack(fill=tk.X, padx=14)
        tk.Label(det_f, text="Último código detectado:", bg=BG2,
                 fg=TEXTL, font=FONT_SM).pack(anchor="w")
        self._code_lbl = tk.Label(det_f, text="—", bg=BG2, fg=TEXT,
                                  font=("Courier New", 14, "bold"))
        self._code_lbl.pack(anchor="w")
        self._prod_lbl = tk.Label(det_f, text="", bg=BG2, fg=ACCENT,
                                  font=("Helvetica", 10, "bold"))
        self._prod_lbl.pack(anchor="w")

        # Controles
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(pady=10)
        self._btn_toggle = btn(ctrl, "⏹ Detener", self._toggle, DANGER)
        self._btn_toggle.pack(side=tk.LEFT, padx=4)
        btn(ctrl, "🔄 Cambiar fuente", self._ask_source, ACCENT2).pack(side=tk.LEFT, padx=4)
        btn(ctrl, "✖ Cerrar", self._on_close, "#718096").pack(side=tk.LEFT, padx=4)

    # ── FUENTE ───────────────────────────────────────────────────
    def _ask_source(self):
        self._stop_scanner()
        dlg = tk.Toplevel(self)
        dlg.title("Fuente de cámara")
        dlg.configure(bg=BG)
        dlg.geometry("360x260")
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="📷 Selecciona la fuente", bg=BG, fg=TEXT,
                 font=("Georgia", 12, "bold")).pack(pady=(16, 4))
        tk.Label(dlg, text="Para DroidCam: ingresa la URL de video\n(ej: http://192.168.1.X:4747/video)",
                 bg=BG, fg=TEXTL, font=FONT_SM, justify="center").pack()

        source_var = tk.StringVar(value="0")

        opts = tk.Frame(dlg, bg=BG)
        opts.pack(pady=8)
        for label, val in [("Cámara 0 (webcam)", "0"),
                            ("Cámara 1", "1"),
                            ("DroidCam / URL personalizada", "url")]:
            tk.Radiobutton(opts, text=label, variable=source_var, value=val,
                           bg=BG, fg=TEXT, selectcolor=BG, font=FONT_SM,
                           activebackground=BG).pack(anchor="w", padx=20)

        url_f = tk.Frame(dlg, bg=BG)
        url_f.pack(fill=tk.X, padx=20)
        tk.Label(url_f, text="URL:", bg=BG, fg=TEXTL, font=FONT_SM).pack(side=tk.LEFT)
        url_entry = tk.Entry(url_f, font=FONT_BODY, relief="solid",
                             bg=BG2, fg=TEXT, bd=1)
        url_entry.insert(0, "http://192.168.1.X:4747/video")
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, ipady=4)

        def ok():
            val = source_var.get()
            if val == "url":
                source = url_entry.get().strip()
            elif val.isdigit():
                source = int(val)
            else:
                source = val
            dlg.destroy()
            self._start_scanner(source)

        btn(dlg, "✅ Conectar", ok, ACCENT).pack(pady=8)

    # ── CICLO ────────────────────────────────────────────────────
    def _start_scanner(self, source):
        if not CV2_OK or not PYZBAR_OK:
            missing = []
            if not CV2_OK:    missing.append("opencv-python")
            if not PYZBAR_OK: missing.append("pyzbar  +  libzbar0")
            messagebox.showerror("Librerías faltantes",
                f"Instala:\n  pip install {' '.join(missing)}\n\n"
                "Para libzbar en Windows descarga: https://sourceforge.net/projects/zbar/",
                parent=self)
            return

        self._running = True
        self._btn_toggle.config(text="⏹ Detener", bg=DANGER,
                                activebackground=_dk(DANGER))
        self._status_lbl.config(text="Conectando...")
        self.escaner.iniciar(source)
        self._poll()

    def _poll(self):
        if not self._running:
            return
        try:
            while True:
                tipo, dato = self.escaner.cola.get_nowait()
                if tipo == "FRAME":
                    self._mostrar_frame(dato)
                elif tipo == "CODIGO":
                    self._handle_code(dato)
                elif tipo == "LISTO":
                    self._status_lbl.config(text="✅ Cámara activa")
                elif tipo == "ERROR":
                    self._status_lbl.config(text=f"❌ {dato}")
                    messagebox.showerror("Error de cámara", dato, parent=self)
                    self._stop_scanner()
                    return
        except queue.Empty:
            pass
        self.after(30, self._poll)   # ~33 fps

    def _mostrar_frame(self, frame):
        if not PIL_OK:
            return
        # BGR → RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((self.PREVIEW_W, self.PREVIEW_H), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self._photo_ref = photo
        self._canvas.delete("frame")
        self._canvas.create_image(0, 0, anchor="nw", image=photo, tags="frame")
        self._canvas.tag_lower("frame")   # corners encima

    def _handle_code(self, code):
        self._code_lbl.config(text=code)
        # Buscar en catálogo: exacto o últimos 4 dígitos
        prod = next((p for p in self.catalogo if p.codigo == code), None)
        if not prod and len(code) >= 4:
            tail = code[-4:]
            prod = next((p for p in self.catalogo if p.codigo[-4:] == tail), None)
        if prod:
            self._prod_lbl.config(text=f"✅ {prod.emoji} {prod.nombre} — ${prod.precio:,.0f}")
            self._status_lbl.config(text=f"Agregado: {prod.nombre}")
            self._flash_green()
            self.on_detected(prod)
        else:
            self._prod_lbl.config(text="⚠️ Código no encontrado en catálogo")
            self._status_lbl.config(text=f"No encontrado: {code}")

    def _flash_green(self):
        self._canvas.config(highlightbackground=ACCENT, highlightthickness=3)
        self.after(300, lambda: self._canvas.config(highlightthickness=0))

    def _toggle(self):
        if self._running:
            self._stop_scanner()
        else:
            self._ask_source()

    def _stop_scanner(self):
        self._running = False
        self.escaner.detener()
        self._btn_toggle.config(text="▶ Iniciar", bg=ACCENT,
                                activebackground=_dk(ACCENT))
        self._status_lbl.config(text="Detenido")

    def _on_close(self):
        self._stop_scanner()
        self.destroy()


# ─────────────────────────────────────────────────────────────────
#  VENTANA PRINCIPAL
# ─────────────────────────────────────────────────────────────────
class CajeroApp(tk.Tk):
    CSV_DEFAULT = Path(__file__).parent / "productos.csv"

    def __init__(self):
        super().__init__()
        self.title("🛒  SuperCajero — Autoservicio")
        self.configure(bg=BG)
        self.geometry("1160x820")
        self.minsize(980, 700)

        self.catalogo: list[Producto] = []
        self.carrito   = Carrito()
        self.registro  = RegistroDiario()
        self._busqueda = tk.StringVar()
        self._busqueda.trace_add("write", self._filtrar_catalogo)
        self._scanner_win = None
        self._current_customer = None   # dict de CUSTOMERS_DATA o None

        if self.CSV_DEFAULT.exists():
            try:
                self.catalogo = self._cargar_csv_ruta(str(self.CSV_DEFAULT))
            except Exception:
                self._catalogo_demo()
        else:
            self._catalogo_demo()

        self._build_ui()
        self._refrescar_catalogo()

    def _catalogo_demo(self):
        demo = [
            ("P001","Arroz Premium 1kg",    4500,"Granos",    "🌾"),
            ("P002","Aceite Girasol 1L",    8900,"Aceites",   "🫙"),
            ("P003","Leche Entera 1L",      3200,"Lácteos",   "🥛"),
            ("P004","Pan Tajado Integral",  5600,"Panadería", "🍞"),
            ("P005","Huevos x12",           9800,"Lácteos",   "🥚"),
            ("P006","Pollo Entero 1kg",    12500,"Carnes",    "🍗"),
            ("P007","Tomate Chonto kg",     3800,"Verduras",  "🍅"),
            ("P008","Cebolla Cabezona kg",  2900,"Verduras",  "🧅"),
            ("P009","Papa Criolla kg",      3500,"Verduras",  "🥔"),
            ("P010","Aguacate Hass x3",     7200,"Frutas",    "🥑"),
            ("P011","Café Molido 250g",    11200,"Bebidas",   "☕"),
            ("P012","Gaseosa 1.5L",         5400,"Bebidas",   "🥤"),
            ("P013","Yogur Natural 200g",   2800,"Lácteos",   "🫐"),
            ("P014","Jabón Barra x3",       6500,"Aseo",      "🧼"),
            ("P015","Azúcar 1kg",           4200,"Granos",    "🍬"),
        ]
        self.catalogo = [Producto(*d) for d in demo]

    # ── BUILD UI ─────────────────────────────────────────────────
    def _build_ui(self):
        # TOPBAR
        topbar = tk.Frame(self, bg=SIDEBAR, height=58)
        topbar.pack(fill=tk.X)
        topbar.pack_propagate(False)
        tk.Label(topbar, text="🛒  SuperCajero",
                 bg=SIDEBAR, fg="white",
                 font=("Georgia", 18, "bold")).pack(side=tk.LEFT, padx=20, pady=10)
        tk.Label(topbar, text="Autoservicio · Personajes · Escáner QR",
                 bg=SIDEBAR, fg="#8899aa",
                 font=("Helvetica", 9, "italic")).pack(side=tk.LEFT)
        self._fecha_lbl = tk.Label(topbar, text="", bg=SIDEBAR, fg="#aabbcc",
                                   font=("Helvetica", 9))
        self._fecha_lbl.pack(side=tk.RIGHT, padx=20)
        self._tick_clock()

        # BARRA DE PERSONAJES
        self._customer_bar = CustomerBar(self, self._on_customer_select)
        self._customer_bar.pack(fill=tk.X, padx=14, pady=(10, 0))

        # BODY
        body = tk.Frame(self, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        left = tk.Frame(body, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = tk.Frame(body, bg=BG, width=350)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right.pack_propagate(False)

        self._build_catalogo_panel(left)
        self._build_carrito_panel(right)

    def _tick_clock(self):
        self._fecha_lbl.config(
            text=datetime.datetime.now().strftime("📅  %d/%m/%Y   🕐  %H:%M"))
        self.after(30000, self._tick_clock)

    def _on_customer_select(self, cdata):
        self._current_customer = cdata
        if cdata:
            self._set_status(f"👋 Hola {cdata['emoji']} {cdata['name']}! ({cdata['role']})", ACCENT)
        else:
            self._set_status("", BG)

    # ── CATÁLOGO ─────────────────────────────────────────────────
    def _build_catalogo_panel(self, parent):
        hdr = tk.Frame(parent, bg=BG)
        hdr.pack(fill=tk.X, pady=(0, 8))
        tk.Label(hdr, text="Catálogo de Productos",
                 bg=BG, fg=TEXT, font=FONT_BIG).pack(side=tk.LEFT)
        bf = tk.Frame(hdr, bg=BG)
        bf.pack(side=tk.RIGHT)
        btn(bf, "📷 Escáner cámara",  self._abrir_scanner,  PINK).pack(side=tk.LEFT, padx=2)
        btn(bf, "📂 Cargar CSV",      self._cargar_csv,     ACCENT2).pack(side=tk.LEFT, padx=2)
        btn(bf, "📊 Resumen día",     self._ver_resumen,    GOLD, fg=TEXT).pack(side=tk.LEFT, padx=2)
        btn(bf, "💾 Exportar día",    self._exportar_dia,   "#805ad5").pack(side=tk.LEFT, padx=2)

        # Búsqueda
        sf = tk.Frame(parent, bg=BG)
        sf.pack(fill=tk.X, pady=(0, 8))
        tk.Label(sf, text="🔍", bg=BG, font=("Helvetica", 12)).pack(side=tk.LEFT)
        entry = tk.Entry(sf, textvariable=self._busqueda, font=FONT_BODY,
                         relief="solid", bg=BG2, fg=TEXT, insertbackground=TEXT,
                         bd=1, highlightthickness=1,
                         highlightcolor=ACCENT, highlightbackground=BORDER)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=6)
        PLACEHOLDER = "Buscar producto o código..."
        entry.insert(0, PLACEHOLDER)
        entry.bind("<FocusIn>",  lambda e: entry.delete(0, tk.END) if entry.get()==PLACEHOLDER else None)
        entry.bind("<FocusOut>", lambda e: entry.insert(0, PLACEHOLDER) if not entry.get() else None)

        # Grid
        gw = tk.Frame(parent, bg=BORDER, bd=1, relief="solid")
        gw.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(gw, bg=BG2, highlightthickness=0)
        vsb = ttk.Scrollbar(gw, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._grid_frame = tk.Frame(canvas, bg=BG2)
        self._grid_win   = canvas.create_window((0, 0), window=self._grid_frame, anchor="nw")

        def on_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(self._grid_win, width=canvas.winfo_width())
        self._grid_frame.bind("<Configure>", on_cfg)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self._grid_win, width=e.width))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        self._catalogo_canvas = canvas

    # ── CARRITO ──────────────────────────────────────────────────
    def _build_carrito_panel(self, parent):
        tk.Label(parent, text="🧺  Carrito",
                 bg=BG, fg=TEXT, font=FONT_BIG).pack(anchor="w", pady=(0, 6))

        lw = tk.Frame(parent, bg=BORDER, bd=1, relief="solid")
        lw.pack(fill=tk.BOTH, expand=True)
        cols = ("Producto", "Cant", "Precio", "Total")
        self._tree = ttk.Treeview(lw, columns=cols, show="headings",
                                   selectmode="browse", height=13)
        style = ttk.Style()
        style.configure("Treeview", background=BG2, fieldbackground=BG2,
                        foreground=TEXT, rowheight=28, font=FONT_SM)
        style.configure("Treeview.Heading", background=SIDEBAR,
                        foreground="white", font=("Helvetica", 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)])
        for col, w in zip(cols, [135, 44, 74, 74]):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="center" if col!="Producto" else "w")
        sb = ttk.Scrollbar(lw, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(fill=tk.BOTH, expand=True)

        bc = tk.Frame(parent, bg=BG)
        bc.pack(fill=tk.X, pady=4)
        btn(bc, "✏️ Editar",  self._editar_cantidad, ACCENT2).pack(side=tk.LEFT, padx=2)
        btn(bc, "🗑️ Quitar",  self._quitar_item,     DANGER).pack(side=tk.LEFT, padx=2)
        btn(bc, "🧹 Vaciar",  self._vaciar_carrito,  "#718096").pack(side=tk.LEFT, padx=2)

        sep(parent)

        tf = tk.Frame(parent, bg=BG2, bd=1, relief="solid", padx=10, pady=8)
        tf.pack(fill=tk.X, pady=4)

        def row_total(text, attr, big=False):
            f = tk.Frame(tf, bg=BG2); f.pack(fill=tk.X, pady=1)
            font = ("Helvetica", 11, "bold") if big else FONT_SM
            tk.Label(f, text=text, bg=BG2, fg=TEXT if big else TEXTL,
                     font=font).pack(side=tk.LEFT)
            lv = tk.Label(f, text="$0", bg=BG2,
                          fg=ACCENT if big else TEXT, font=font)
            lv.pack(side=tk.RIGHT)
            setattr(self, attr, lv)

        row_total("Subtotal (sin IVA):", "_lbl_sub")
        row_total("IVA (19%):",          "_lbl_iva")
        tk.Frame(tf, bg=BORDER, height=1).pack(fill=tk.X, pady=3)
        row_total("TOTAL:",              "_lbl_total", big=True)

        sep(parent)

        # Método de pago
        tk.Label(parent, text="Método de pago:", bg=BG, fg=TEXTL,
                 font=FONT_SM).pack(anchor="w")
        self._metodo = tk.StringVar(value="Efectivo")
        mf = tk.Frame(parent, bg=BG)
        mf.pack(fill=tk.X, pady=3)
        for m in ["Efectivo", "Tarjeta", "Nequi", "PSE"]:
            tk.Radiobutton(mf, text=m, variable=self._metodo, value=m,
                           bg=BG, fg=TEXT, selectcolor=BG,
                           font=FONT_SM, activebackground=BG).pack(side=tk.LEFT)

        pf = tk.Frame(parent, bg=BG)
        pf.pack(fill=tk.X, pady=2)
        tk.Label(pf, text="Pago $:", bg=BG, fg=TEXTL,
                 font=FONT_SM).pack(side=tk.LEFT)
        self._pago_var = tk.StringVar(value="0")
        tk.Entry(pf, textvariable=self._pago_var, font=FONT_MONO,
                 width=12, relief="solid", bg=BG2, fg=TEXT, bd=1).pack(side=tk.LEFT, padx=6, ipady=4)
        btn(pf, "= Exacto", self._pago_exacto, "#4a5568", pady=4).pack(side=tk.LEFT)

        sep(parent)

        # Barra de estado cliente
        self._status_bar = tk.Label(parent, text="", bg=BG, fg=ACCENT,
                                    font=("Helvetica", 9, "bold"), wraplength=330)
        self._status_bar.pack(anchor="w")

        btn(parent, "✅  COBRAR Y GENERAR FACTURA",
            self._cobrar, ACCENT, width=32).pack(fill=tk.X, ipady=4)

        self._lbl_items = tk.Label(parent, text="Productos en carrito: 0",
                                   bg=BG, fg=TEXTL, font=FONT_SM)
        self._lbl_items.pack(pady=2)

    def _set_status(self, text, color=BG):
        self._status_bar.config(text=text, fg=color if color != BG else ACCENT)

    # ── SCANNER ──────────────────────────────────────────────────
    def _abrir_scanner(self):
        if self._scanner_win and self._scanner_win.winfo_exists():
            self._scanner_win.lift()
            return
        self._scanner_win = ScannerWindow(self, self.catalogo, self._agregar_desde_scanner)

    def _agregar_desde_scanner(self, producto: Producto):
        """Callback cuando el escáner detecta un producto válido."""
        self.carrito.agregar(producto, 1)
        self._refrescar_tree()
        self._flash_total()
        # Notificación
        self._set_status(f"📷 Escaneado: {producto.emoji} {producto.nombre}", ACCENT)

    # ── CATÁLOGO GRID ────────────────────────────────────────────
    def _refrescar_catalogo(self, filtro=""):
        for w in self._grid_frame.winfo_children():
            w.destroy()
        prods = [p for p in self.catalogo
                 if not filtro
                 or filtro.lower() in p.nombre.lower()
                 or filtro.lower() in p.codigo.lower()
                 or filtro.lower() in p.categoria.lower()]
        cols = 3
        for i, prod in enumerate(prods):
            r, c = divmod(i, cols)
            card = self._make_card(self._grid_frame, prod)
            card.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
        for c in range(cols):
            self._grid_frame.columnconfigure(c, weight=1)

    def _filtrar_catalogo(self, *_):
        if not hasattr(self, "_grid_frame"): return
        txt = self._busqueda.get()
        if txt.startswith("Buscar"): txt = ""
        self._refrescar_catalogo(txt)

    def _make_card(self, parent, prod):
        card = tk.Frame(parent, bg=BG2, bd=1, relief="solid",
                        cursor="hand2", padx=8, pady=8,
                        highlightbackground=BORDER, highlightthickness=1)

        def hi(e):  card.config(bg="#f0fff4", highlightbackground=ACCENT)
        def lo(e):  card.config(bg=BG2,      highlightbackground=BORDER)
        def click(e): self._agregar_producto(prod)

        for w in [card]:
            w.bind("<Enter>", hi); w.bind("<Leave>", lo); w.bind("<Button-1>", click)

        def bind_all(widget):
            widget.bind("<Enter>", hi); widget.bind("<Leave>", lo)
            widget.bind("<Button-1>", click)

        wl = [
            tk.Label(card, text=prod.emoji, bg=BG2, font=("Segoe UI Emoji", 22)),
            tk.Label(card, text=prod.nombre, bg=BG2, fg=TEXT,
                     font=("Helvetica", 9, "bold"), wraplength=130, justify="center"),
            tk.Label(card, text=prod.codigo, bg=BG2, fg=TEXTL, font=("Courier New", 7)),
            tk.Label(card, text=prod.categoria, bg=BG2, fg=TEXTL, font=("Helvetica", 7, "italic")),
            tk.Label(card, text=f"${prod.precio:,.0f}", bg=BG2,
                     fg=ACCENT, font=("Helvetica", 12, "bold")),
        ]
        for w in wl: w.pack(); bind_all(w)

        add = tk.Label(card, text="+ Agregar", bg=ACCENT, fg="white",
                       font=("Helvetica", 8, "bold"), padx=8, pady=3, cursor="hand2")
        add.pack(pady=(4, 0))
        add.bind("<Button-1>", click)
        add.bind("<Enter>", lambda e: add.config(bg=_dk(ACCENT)))
        add.bind("<Leave>", lambda e: add.config(bg=ACCENT))
        return card

    # ── AGREGAR (click en card) ───────────────────────────────────
    def _agregar_producto(self, prod):
        dlg = tk.Toplevel(self)
        dlg.title("Cantidad")
        dlg.configure(bg=BG)
        dlg.geometry("280x170")
        dlg.resizable(False, False)
        dlg.grab_set(); dlg.transient(self)

        tk.Label(dlg, text=f"{prod.emoji}  {prod.nombre}", bg=BG, fg=TEXT,
                 font=("Helvetica", 11, "bold"), wraplength=240).pack(pady=(16, 4))
        tk.Label(dlg, text=f"${prod.precio:,.0f} c/u", bg=BG,
                 fg=ACCENT, font=("Helvetica", 10)).pack()

        var = tk.IntVar(value=1)
        sf2 = tk.Frame(dlg, bg=BG); sf2.pack(pady=8)
        tk.Label(sf2, text="Cantidad:", bg=BG, fg=TEXT, font=FONT_SM).pack(side=tk.LEFT)
        spin = tk.Spinbox(sf2, from_=1, to=99, textvariable=var,
                          width=5, font=FONT_BODY, relief="solid")
        spin.pack(side=tk.LEFT, padx=8)

        def ok():
            try:
                qty = int(var.get())
                self.carrito.agregar(prod, qty)
                self._refrescar_tree()
                dlg.destroy()
                self._flash_total()
            except ValueError:
                messagebox.showerror("Error", "Cantidad inválida", parent=dlg)

        bf2 = tk.Frame(dlg, bg=BG); bf2.pack()
        btn(bf2, "✅ Agregar", ok, ACCENT).pack(side=tk.LEFT, padx=6)
        btn(bf2, "Cancelar",  dlg.destroy, "#718096").pack(side=tk.LEFT)
        spin.focus_set()
        dlg.bind("<Return>", lambda e: ok())

    def _flash_total(self):
        self._lbl_total.config(fg="#ffd700")
        self.after(300, lambda: self._lbl_total.config(fg=ACCENT))

    # ── TREE ─────────────────────────────────────────────────────
    def _refrescar_tree(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        for item in self.carrito.items:
            self._tree.insert("", "end", iid=item.producto.codigo,
                values=(f"{item.producto.emoji} {item.producto.nombre[:20]}",
                        item.cantidad,
                        f"${item.producto.precio:,.0f}",
                        f"${item.subtotal:,.0f}"))
        self._lbl_sub.config(text=f"${self.carrito.subtotal_sin_iva:,.0f}")
        self._lbl_iva.config(text=f"${self.carrito.iva:,.0f}")
        self._lbl_total.config(text=f"${self.carrito.total:,.0f}")
        self._lbl_items.config(text=f"Productos en carrito: {self.carrito.num_productos}")

    def _editar_cantidad(self):
        sel = self._tree.selection()
        if not sel: return
        codigo = sel[0]
        item = next((i for i in self.carrito.items if i.producto.codigo == codigo), None)
        if not item: return
        dlg = tk.Toplevel(self)
        dlg.title("Editar cantidad"); dlg.configure(bg=BG)
        dlg.geometry("240x130"); dlg.resizable(False, False); dlg.grab_set()
        tk.Label(dlg, text=item.producto.nombre, bg=BG, fg=TEXT,
                 font=("Helvetica", 10, "bold")).pack(pady=(14, 4))
        var = tk.IntVar(value=item.cantidad)
        sf3 = tk.Frame(dlg, bg=BG); sf3.pack()
        tk.Label(sf3, text="Nueva cantidad:", bg=BG, font=FONT_SM).pack(side=tk.LEFT)
        tk.Spinbox(sf3, from_=0, to=99, textvariable=var,
                   width=5, font=FONT_BODY, relief="solid").pack(side=tk.LEFT, padx=6)
        def ok():
            self.carrito.actualizar_cantidad(codigo, var.get())
            self._refrescar_tree(); dlg.destroy()
        btn(dlg, "✅ Actualizar", ok, ACCENT).pack(pady=8)

    def _quitar_item(self):
        sel = self._tree.selection()
        if not sel: return
        self.carrito.eliminar(sel[0]); self._refrescar_tree()

    def _vaciar_carrito(self):
        if self.carrito.esta_vacio(): return
        if messagebox.askyesno("Vaciar carrito", "¿Vaciar todo el carrito?"):
            self.carrito.vaciar(); self._refrescar_tree()

    def _pago_exacto(self):
        self._pago_var.set(str(int(self.carrito.total)))

    # ── COBRAR ───────────────────────────────────────────────────
    def _cobrar(self):
        if self.carrito.esta_vacio():
            messagebox.showwarning("Carrito vacío", "Agregue productos primero."); return
        try:
            monto = float(self._pago_var.get().replace(",", ""))
        except ValueError:
            monto = 0.0
        if self._metodo.get() == "Efectivo" and monto < self.carrito.total:
            messagebox.showerror("Pago insuficiente",
                f"Total: ${self.carrito.total:,.0f}\nIngrese el monto correcto."); return

        factura = Factura(self.carrito, self._metodo.get(), self._current_customer)
        factura.registrar_pago(monto if self._metodo.get() == "Efectivo" else self.carrito.total)
        self.registro.registrar(factura)
        self.carrito.vaciar(); self._refrescar_tree()
        self._pago_var.set("0")
        FacturaWindow(self, factura)

    # ── CSV ──────────────────────────────────────────────────────
    def _cargar_csv_ruta(self, ruta):
        prods = []
        with open(ruta, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    prods.append(Producto(
                        row["codigo"].strip(), row["nombre"].strip(),
                        float(row["precio"]),
                        row.get("categoria", "").strip(),
                        row.get("emoji", "📦").strip()))
                except (KeyError, ValueError):
                    continue
        return prods

    def _cargar_csv(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar catálogo CSV",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if not ruta: return
        try:
            self.catalogo = self._cargar_csv_ruta(ruta)
            self._refrescar_catalogo()
            messagebox.showinfo("Éxito", f"✅ {len(self.catalogo)} productos cargados.")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _exportar_dia(self):
        if not self.registro.facturas:
            messagebox.showinfo("Sin datos", "No hay transacciones hoy."); return
        ruta = filedialog.asksaveasfilename(
            title="Exportar registro", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"ventas_{datetime.date.today()}.csv")
        if not ruta: return
        try:
            self.registro.exportar_csv(ruta)
            messagebox.showinfo("Exportado", f"✅ Guardado:\n{ruta}")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _ver_resumen(self):
        ResumenWindow(self, self.registro)


# ─────────────────────────────────────────────────────────────────
#  VENTANA FACTURA
# ─────────────────────────────────────────────────────────────────
class FacturaWindow(tk.Toplevel):
    def __init__(self, master, factura: Factura):
        super().__init__(master)
        self.title(f"Factura {factura.numero}")
        self.configure(bg=BG)
        self.geometry("680x560")
        self.grab_set()
        self.factura = factura
        self._build(factura)

    def _build(self, f):
        # Header verde
        hdr = tk.Frame(self, bg=ACCENT, padx=20, pady=14)
        hdr.pack(fill=tk.X)

        # Avatar del cliente
        if f.cliente and IMGS_OK and PIL_OK:
            b64 = globals().get(f"IMG_{f.cliente['b64_key'].upper()}", None)
            # Mapear nombre → clave
            key_map = {c["name"]: c["b64_key"] for c in CUSTOMERS_DATA}
            b64_key = key_map.get(f.cliente["name"], "")
            b64 = globals().get(b64_key) if b64_key else None
            if b64:
                img = b64_to_pil(b64, (52, 52))
                if img:
                    photo = ImageTk.PhotoImage(img)
                    self._ph = photo
                    tk.Label(hdr, image=photo, bg=ACCENT, bd=2,
                             relief="solid").pack(side=tk.LEFT, padx=(0, 10))

        title_f = tk.Frame(hdr, bg=ACCENT)
        title_f.pack(side=tk.LEFT)
        tk.Label(title_f, text="✅  Compra realizada con éxito",
                 bg=ACCENT, fg="white", font=("Georgia", 14, "bold")).pack(anchor="w")
        if f.cliente:
            tk.Label(title_f,
                     text=f"{f.cliente['emoji']} {f.cliente['name']} — {f.cliente['role']}",
                     bg=ACCENT, fg="#c6f6d5", font=("Helvetica", 9)).pack(anchor="w")

        tk.Label(hdr, text=f.numero, bg=ACCENT, fg="#c6f6d5",
                 font=("Courier New", 9)).pack(side=tk.RIGHT)

        # Recibo
        body = tk.Frame(self, bg=BG); body.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)
        tk.Label(body, text="RECIBO DE COMPRA", bg=BG, fg=TEXT,
                 font=("Georgia", 12, "bold")).pack(anchor="w")
        tf = tk.Frame(body, bg=SIDEBAR, bd=1, relief="solid")
        tf.pack(fill=tk.BOTH, expand=True, pady=6)
        txt = tk.Text(tf, font=("Courier New", 9), bg=SIDEBAR, fg="#e2f0ff",
                      wrap="none", relief="flat", padx=10, pady=10)
        vsb = ttk.Scrollbar(tf, command=txt.yview)
        txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y); txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", f.texto_recibo()); txt.config(state="disabled")

        # Botones
        sep(self)
        bf = tk.Frame(self, bg=BG); bf.pack(pady=(0, 10))
        btn(bf, "💾 Guardar recibo .txt", self._guardar, ACCENT2).pack(side=tk.LEFT, padx=6)
        btn(bf, "✖ Cerrar", self.destroy, "#718096").pack(side=tk.LEFT, padx=6)

    def _guardar(self):
        ruta = filedialog.asksaveasfilename(
            title="Guardar recibo", defaultextension=".txt",
            filetypes=[("Texto", "*.txt")],
            initialfile=f"{self.factura.numero}.txt")
        if not ruta: return
        with open(ruta, "w", encoding="utf-8") as fp:
            fp.write(self.factura.texto_recibo())
        messagebox.showinfo("Guardado", f"✅ Guardado:\n{ruta}")


# ─────────────────────────────────────────────────────────────────
#  VENTANA RESUMEN
# ─────────────────────────────────────────────────────────────────
class ResumenWindow(tk.Toplevel):
    def __init__(self, master, registro: RegistroDiario):
        super().__init__(master)
        self.title(f"Resumen — {registro.fecha}")
        self.configure(bg=BG)
        self.geometry("580x500")
        self.registro = registro
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=ACCENT2, padx=16, pady=12); hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"📊  Resumen del día  {self.registro.fecha.strftime('%d/%m/%Y')}",
                 bg=ACCENT2, fg="white", font=("Georgia", 13, "bold")).pack(side=tk.LEFT)
        # KPIs
        kf = tk.Frame(self, bg=BG); kf.pack(fill=tk.X, padx=16, pady=10)
        prods_vendidos = sum(i.cantidad for f in self.registro.facturas for i in f.items)
        for lbl, val, col in [
            ("🧾 Transacciones", str(self.registro.num_transacciones), ACCENT2),
            ("💰 Total ventas",  f"${self.registro.total_ventas:,.0f}", ACCENT),
            ("📦 Productos",     str(prods_vendidos), GOLD),
        ]:
            kcard = tk.Frame(kf, bg=col, padx=14, pady=10)
            kcard.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            tk.Label(kcard, text=lbl, bg=col, fg="white", font=FONT_SM).pack()
            tk.Label(kcard, text=val, bg=col, fg="white",
                     font=("Helvetica", 16, "bold")).pack()

        sep(self)
        tf = tk.Frame(self, bg=SIDEBAR, bd=1, relief="solid", padx=2, pady=2)
        tf.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        txt = tk.Text(tf, font=("Courier New", 9), bg=SIDEBAR, fg="#e2f0ff",
                      wrap="none", relief="flat", padx=10, pady=10)
        vsb = ttk.Scrollbar(tf, command=txt.yview)
        txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y); txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", self.registro.resumen_texto()); txt.config(state="disabled")

        sep(self)
        bf = tk.Frame(self, bg=BG); bf.pack(pady=(0, 10))
        btn(bf, "💾 Exportar CSV", self._exportar, "#805ad5").pack(side=tk.LEFT, padx=8)
        btn(bf, "✖ Cerrar", self.destroy, "#718096").pack(side=tk.LEFT, padx=8)

    def _exportar(self):
        if not self.registro.facturas:
            messagebox.showinfo("Sin datos", "No hay transacciones."); return
        ruta = filedialog.asksaveasfilename(
            title="Exportar CSV", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"ventas_{self.registro.fecha}.csv")
        if not ruta: return
        try:
            self.registro.exportar_csv(ruta); messagebox.showinfo("Exportado", f"✅ {ruta}")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))


# ─────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = CajeroApp()
    app.mainloop()
