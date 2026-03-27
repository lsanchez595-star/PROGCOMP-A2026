"""
╔══════════════════════════════════════════════════════════════════╗
║          ASESOR DE ENERGÍA RENOVABLE — EnergyMap v2.0            ║
║          Herramienta de análisis para ingenieros energéticos     ║
╚══════════════════════════════════════════════════════════════════╝

Evalúa 9 tecnologías de generación eléctrica y recomienda la más
conveniente para un territorio dado, según sus recursos naturales,
condiciones económicas y restricciones técnicas.

Uso: python energy_advisor.py
"""

import sys
import os
import math

# ─────────────────────────────────────────────
#  UTILIDADES DE CONSOLA
# ─────────────────────────────────────────────

class Color:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    RED     = "\033[91m"
    DIM     = "\033[2m"
    WHITE   = "\033[97m"
    MAGENTA = "\033[95m"
    BLUE    = "\033[94m"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def header():
    print(f"{Color.GREEN}{Color.BOLD}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          ASESOR DE ENERGÍA RENOVABLE  —  EnergyMap v2.0         ║")
    print("║          Para ingenieros energéticos                            ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{Color.RESET}")


def seccion(num, total, titulo, descripcion=""):
    print(f"\n{Color.DIM}{'─'*66}{Color.RESET}")
    print(f"{Color.CYAN}{Color.BOLD}  [{num}/{total}] {titulo.upper()}{Color.RESET}")
    if descripcion:
        print(f"  {Color.DIM}{descripcion}{Color.RESET}")
    print(f"{Color.DIM}{'─'*66}{Color.RESET}\n")


def progreso(paso, total):
    lleno = int((paso / total) * 50)
    barra = "█" * lleno + "░" * (50 - lleno)
    pct   = int((paso / total) * 100)
    print(f"\n  {Color.GREEN}{barra}{Color.RESET}  {Color.BOLD}{pct}%{Color.RESET}  Paso {paso}/{total}\n")


def pedir_texto(pregunta, obligatorio=True):
    while True:
        val = input(f"  {Color.WHITE}{pregunta}: {Color.RESET}").strip()
        if val or not obligatorio:
            return val
        print(f"  {Color.RED}⚠  Campo obligatorio.{Color.RESET}")


def pedir_numero(pregunta, minimo=None, maximo=None, defecto=None, decimales=False):
    hint = ""
    if defecto is not None:
        hint = f" [{Color.DIM}default {defecto}{Color.RESET}]"
    while True:
        raw = input(f"  {Color.WHITE}{pregunta}{hint}: {Color.RESET}").strip()
        if raw == "" and defecto is not None:
            return defecto
        try:
            val = float(raw) if decimales else int(float(raw))
            if minimo is not None and val < minimo:
                print(f"  {Color.RED}⚠  Mínimo permitido: {minimo}{Color.RESET}")
                continue
            if maximo is not None and val > maximo:
                print(f"  {Color.RED}⚠  Máximo permitido: {maximo}{Color.RESET}")
                continue
            return val
        except ValueError:
            print(f"  {Color.RED}⚠  Ingresa un número válido.{Color.RESET}")


def pedir_opcion(pregunta, opciones):
    """
    opciones: lista de tuplas (clave, etiqueta)
    Retorna la clave seleccionada.
    """
    print(f"  {Color.WHITE}{pregunta}{Color.RESET}")
    for i, (clave, etiqueta) in enumerate(opciones, 1):
        print(f"    {Color.CYAN}{i}{Color.RESET}. {etiqueta}")
    while True:
        raw = input(f"  {Color.WHITE}Opción (1-{len(opciones)}): {Color.RESET}").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(opciones):
                return opciones[idx][0]
        except ValueError:
            pass
        print(f"  {Color.RED}⚠  Selecciona un número entre 1 y {len(opciones)}.{Color.RESET}")


def pedir_slider(pregunta, minimo, maximo, defecto, paso=1, unidad=""):
    """Simula un slider con input numérico."""
    rango = f"{minimo}–{maximo}{unidad}"
    print(f"  {Color.WHITE}{pregunta}{Color.RESET}")
    print(f"    {Color.DIM}Rango: {rango}   Default: {defecto}{unidad}{Color.RESET}")
    return pedir_numero(f"  → Valor", minimo=minimo, maximo=maximo, defecto=defecto, decimales=True)


def pedir_multiopcion(pregunta, opciones):
    """
    opciones: lista de tuplas (clave, etiqueta)
    Retorna lista de claves seleccionadas.
    """
    print(f"  {Color.WHITE}{pregunta}{Color.RESET}")
    for i, (clave, etiqueta) in enumerate(opciones, 1):
        print(f"    {Color.CYAN}{i}{Color.RESET}. {etiqueta}")
    print(f"    {Color.DIM}Separa con comas. Ej: 1,3,4   |  0 = Ninguna{Color.RESET}")
    while True:
        raw = input(f"  {Color.WHITE}Selección: {Color.RESET}").strip()
        if raw == "0":
            return []
        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",")]
            if all(0 <= idx < len(opciones) for idx in indices):
                return [opciones[idx][0] for idx in indices]
        except ValueError:
            pass
        print(f"  {Color.RED}⚠  Ingresa números válidos separados por comas.{Color.RESET}")


# ─────────────────────────────────────────────
#  MOTOR DE PUNTUACIÓN
# ─────────────────────────────────────────────

TECNOLOGIAS = {
    "solar_fv": {
        "nombre": "Solar Fotovoltaica",
        "icono":  "☀",
        "lcoe":   "30–60 USD/MWh",
        "tipo":   "Variable diurna",
        "desc":   "Paneles solares en campo o tejado. Bajo mantenimiento, alta escalabilidad y despliegue rápido.",
    },
    "eolica_tierra": {
        "nombre": "Eólica Terrestre",
        "icono":  "⊕",
        "lcoe":   "25–50 USD/MWh",
        "tipo":   "Variable intermitente",
        "desc":   "Aerogeneradores en tierra. Alta densidad de potencia por hectárea y muy bajo LCOE.",
    },
    "mini_hidro": {
        "nombre": "Mini / Pequeña Hidráulica",
        "icono":  "~",
        "lcoe":   "40–90 USD/MWh",
        "tipo":   "Base continua",
        "desc":   "Turbinas en ríos. Generación base confiable sin grandes represas ni impacto ambiental severo.",
    },
    "hidro_grande": {
        "nombre": "Hidráulica a Gran Escala",
        "icono":  "#",
        "lcoe":   "20–50 USD/MWh",
        "tipo":   "Base / regulable",
        "desc":   "Embalses y represas. Alto CAPEX pero muy bajo LCOE a largo plazo. Alto impacto territorial.",
    },
    "geotermia": {
        "nombre": "Geotermia",
        "icono":  "^",
        "lcoe":   "50–100 USD/MWh",
        "tipo":   "Base continua 24/7",
        "desc":   "Aprovecha calor del subsuelo. Sin emisiones, carga base perfecta, requiere recurso específico.",
    },
    "biomasa": {
        "nombre": "Biomasa / Biogás",
        "icono":  "*",
        "lcoe":   "60–120 USD/MWh",
        "tipo":   "Flexible / base",
        "desc":   "Combustión de residuos orgánicos. Flexible, gestionable y con beneficio de economía circular.",
    },
    "eolica_marina": {
        "nombre": "Eólica Marina (Offshore)",
        "icono":  "~^",
        "lcoe":   "60–120 USD/MWh",
        "tipo":   "Variable alto factor",
        "desc":   "Parques eólicos en mar. Factores de capacidad superiores al 40%, mayor velocidad de viento.",
    },
    "solar_csp": {
        "nombre": "Solar Térmica CSP",
        "icono":  "O",
        "lcoe":   "80–150 USD/MWh",
        "tipo":   "Base c/ almacenamiento",
        "desc":   "Concentración solar con almacenamiento térmico. Despacho controlable, alta irradiación directa.",
    },
    "hibrido": {
        "nombre": "Sistema Híbrido Solar+Eólico",
        "icono":  "SxW",
        "lcoe":   "35–65 USD/MWh",
        "tipo":   "Complementario",
        "desc":   "Complementariedad diurna/nocturna y estacional. Mayor factor de capacidad combinado.",
    },
}


def normalizar(val, minimo, maximo):
    return min(1.0, max(0.0, (val - minimo) / (maximo - minimo)))


def clamp(val, lo=0, hi=100):
    return min(hi, max(lo, val))


def calcular_scores(d):
    scores = {}

    # ── SOLAR FV ──
    s = 0
    s += normalizar(d["solar"], 1, 9) * 35
    s += normalizar(d["area"], 10, 5000) * 15
    if d["terreno"] == "desierto":  s += 15
    if d["terreno"] == "plano":     s += 8
    if d["temperatura"] < 35:       s += 5
    if "aves" in d["restricciones"]:       s -= 5
    if d["prioridad"] == "rapido":         s += 10
    if d["prioridad"] == "ambiental":      s += d["peso_ambiental"] * 8
    if d["presupuesto"] < 20 and d["demanda"] < 20: s += 5
    if "solar" in d["existentes"]:  s -= 8
    scores["solar_fv"] = clamp(s)

    # ── EÓLICA TERRESTRE ──
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

    # ── MINI HIDRO ──
    s = 0
    s += normalizar(d["hidro"], 0, 200) * 30
    if d["hidro"] >= 2:     s += 20
    if d["hidro"] >= 10:    s += 15
    if d["terreno"] in ("montaña", "valles"): s += 15
    if "agua" in d["restricciones"]:           s -= 20
    if d["fiabilidad"] == "alta":              s += 12
    if d["precipitacion"] > 1000:              s += 8
    if "inundaciones" in d["restricciones"]:   s -= 5
    scores["mini_hidro"] = clamp(s)

    # ── HIDRO GRANDE ──
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

    # ── GEOTERMIA ──
    s = 0
    geo_map = {"nula": 0, "baja": 20, "media": 50, "alta": 80}
    s += geo_map.get(d["geotermia"], 0)
    if d["fiabilidad"] == "alta":        s += 15
    if d["geotermia"] == "alta":         s += 20
    if "sismica" in d["restricciones"]:  s -= 10
    if d["terreno"] == "montaña":        s += 5
    if d["presupuesto"] >= 100:          s += 5
    scores["geotermia"] = clamp(s)

    # ── BIOMASA ──
    s = 0
    bio_map = {"nula": 0, "baja": 15, "media": 40, "alta": 70}
    s += bio_map.get(d["biomasa"], 0)
    if d["tipo_demanda"] == "industrial": s += 15
    if d["fiabilidad"] == "alta":         s += 10
    if d["red_nacional"] == "no":         s += 10
    if d["prioridad"] == "empleo":        s += 10
    if d["prioridad"] == "ambiental":     s -= d["peso_ambiental"] * 10
    scores["biomasa"] = clamp(s)

    # ── EÓLICA MARINA ──
    s = 0
    mar_map = {"no": 0, "olas": 20, "mareas": 40, "alto": 70}
    s += mar_map.get(d["marino"], 0)
    s += normalizar(d["viento"], 0, 15) * 20
    if d["marino"] != "no" and d["viento"] >= 7: s += 20
    if d["presupuesto"] >= 300:                  s += 10
    if d["area"] >= 2000:                        s += 5
    scores["eolica_marina"] = clamp(s)

    # ── SOLAR CSP ──
    s = 0
    s += normalizar(d["solar"], 1, 9) * 30
    if d["solar"] >= 6:              s += 20
    if d["terreno"] == "desierto":   s += 20
    if d["area"] >= 500:             s += 10
    if d["fiabilidad"] == "alta":    s += 10
    if d["temperatura"] >= 20:       s += 8
    if d["presupuesto"] >= 150:      s += 5
    scores["solar_csp"] = clamp(s)

    # ── HÍBRIDO SOLAR+EÓLICO ──
    s = 0
    sn = normalizar(d["solar"], 1, 9)
    vn = normalizar(d["viento"], 0, 15)
    s = sn * 25 + vn * 25
    if sn > 0.4 and vn > 0.3:                               s += 20
    if d["fiabilidad"] == "alta" or d["red_nacional"] == "no": s += 10
    if d["prioridad"] == "confiabilidad":                    s += 10
    if d["area"] >= 200:                                     s += 5
    if "solar" in d["existentes"] or "eolica" in d["existentes"]: s += 5
    scores["hibrido"] = clamp(s)

    # ─── Ajustes por prioridad ───
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
#  VISUALIZACIÓN DE RESULTADOS
# ─────────────────────────────────────────────

def barra(valor, maximo, ancho=30, color=Color.GREEN):
    lleno = int((valor / maximo) * ancho) if maximo > 0 else 0
    vacio = ancho - lleno
    return f"{color}{'█' * lleno}{Color.DIM}{'░' * vacio}{Color.RESET}"


def mostrar_resultados(scores, datos):
    clear()
    header()

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    max_score = ranked[0][1] if ranked else 1

    winner_key, winner_score = ranked[0]
    winner = TECNOLOGIAS[winner_key]

    # ── GANADOR ──
    print(f"\n  {Color.GREEN}{'═'*64}{Color.RESET}")
    print(f"  {Color.BOLD}{Color.GREEN}  ★  TECNOLOGÍA RECOMENDADA{Color.RESET}")
    print(f"  {Color.GREEN}{'═'*64}{Color.RESET}")
    print(f"\n  {Color.BOLD}{Color.WHITE}  {winner['icono']}  {winner['nombre']}{Color.RESET}")
    print(f"     {Color.DIM}{winner['desc']}{Color.RESET}")
    print(f"\n     LCOE estimado : {Color.YELLOW}{winner['lcoe']}{Color.RESET}")
    print(f"     Tipo de carga : {Color.CYAN}{winner['tipo']}{Color.RESET}")
    print(f"     Score         : {Color.GREEN}{Color.BOLD}{winner_score}/100{Color.RESET}")
    print()

    # ── RANKING COMPLETO ──
    print(f"  {Color.DIM}{'─'*64}{Color.RESET}")
    print(f"  {Color.BOLD}  RANKING COMPLETO{Color.RESET}\n")

    medallas = ["★", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"]
    colores   = [Color.GREEN, Color.YELLOW, Color.CYAN,
                 Color.WHITE, Color.DIM, Color.DIM, Color.DIM, Color.DIM, Color.DIM]

    for i, (key, score) in enumerate(ranked):
        tec    = TECNOLOGIAS[key]
        med    = medallas[i] if i < len(medallas) else f"{i+1}."
        col    = colores[i] if i < len(colores) else Color.DIM
        bar    = barra(score, max_score, 28, col)
        nombre = tec["nombre"].ljust(28)
        print(f"  {col}{med}{Color.RESET}  {nombre}  {bar}  {col}{score:3d}{Color.RESET}")

    print()

    # ── ANÁLISIS CLAVE ──
    print(f"  {Color.DIM}{'─'*64}{Color.RESET}")
    print(f"  {Color.BOLD}  FACTORES DETERMINANTES{Color.RESET}\n")

    region = datos.get("region", "el territorio")
    solar  = datos["solar"]
    viento = datos["viento"]
    hidro  = datos["hidro"]
    pres   = datos["presupuesto"]

    factores = [
        ("Solar", f"{solar} kWh/m²/día", solar >= 5),
        ("Viento", f"{viento} m/s",       viento >= 6),
        ("Hidro",  f"{hidro} m³/s",        hidro >= 5),
        ("Presupuesto", f"{pres} MUSD",    pres >= 50),
    ]

    for nombre_f, valor_f, bueno in factores:
        icono = f"{Color.GREEN}✓{Color.RESET}" if bueno else f"{Color.DIM}·{Color.RESET}"
        print(f"    {icono}  {nombre_f:<14} {Color.CYAN}{valor_f}{Color.RESET}")

    restricciones = datos.get("restricciones", [])
    if restricciones:
        print(f"\n  {Color.YELLOW}  Restricciones activas: {', '.join(restricciones)}{Color.RESET}")
    else:
        print(f"\n  {Color.DIM}  Sin restricciones críticas.{Color.RESET}")

    print()

    # ── RESUMEN EJECUTIVO ──
    alt2 = TECNOLOGIAS[ranked[1][0]]["nombre"]
    alt3 = TECNOLOGIAS[ranked[2][0]]["nombre"]
    print(f"  {Color.DIM}{'─'*64}{Color.RESET}")
    print(f"  {Color.BOLD}  RESUMEN EJECUTIVO{Color.RESET}\n")
    print(f"  Para {Color.WHITE}{region}{Color.RESET}, el análisis de 9 tecnologías indica que")
    print(f"  {Color.GREEN}{Color.BOLD}{winner['nombre']}{Color.RESET} es la opción más conveniente")
    print(f"  (score {winner_score}/100). Como alternativas se evalúan {Color.YELLOW}{alt2}{Color.RESET}")
    print(f"  ({ranked[1][1]} pts) y {Color.CYAN}{alt3}{Color.RESET} ({ranked[2][1]} pts).")
    print(f"\n  {Color.DIM}Se recomienda complementar con estudios de prefactibilidad")
    print(f"  y medición in-situ antes de la decisión de inversión.{Color.RESET}")
    print()
    print(f"  {Color.GREEN}{'═'*64}{Color.RESET}\n")


# ─────────────────────────────────────────────
#  FLUJO DE INPUTS — 5 SECCIONES
# ─────────────────────────────────────────────

def seccion_1_geografia():
    seccion(1, 5, "Geografía del Territorio",
            "Condiciones físicas y geográficas del área de instalación.")

    region = pedir_texto("Región / País (ej: Guajira, Colombia)")

    area = pedir_numero("Área disponible (ha)", minimo=1, defecto=500)

    lat = pedir_numero("Latitud aproximada (°, negativo = sur)",
                       minimo=-90, maximo=90, defecto=10, decimales=True)

    altitud = pedir_numero("Altitud (msnm)", minimo=0, defecto=500)

    terreno = pedir_opcion("Tipo de terreno:", [
        ("plano",    "Plano / llanura"),
        ("costa",    "Costa / litoral"),
        ("montaña",  "Montaña / sierra"),
        ("valles",   "Valles / cuencas"),
        ("desierto", "Desierto / árido"),
        ("selva",    "Selva / húmedo tropical"),
    ])

    densidad_pob = pedir_opcion("Densidad de población cercana:", [
        ("baja",  "Baja  — rural, despoblado"),
        ("media", "Media — pequeñas comunidades"),
        ("alta",  "Alta  — urbano / periurbano"),
    ])

    return {
        "region": region, "area": area, "lat": lat,
        "altitud": altitud, "terreno": terreno, "densidad_pob": densidad_pob,
    }


def seccion_2_recursos():
    seccion(2, 5, "Recursos Naturales",
            "Disponibilidad y calidad de los recursos energéticos del territorio.")

    solar = pedir_slider(
        "Irradiación solar  (kWh/m²/día)  [1=muy bajo · 9=desierto Atacama]",
        minimo=1.0, maximo=9.0, defecto=4.5, unidad=" kWh/m²/día"
    )

    viento = pedir_slider(
        "Velocidad media del viento  (m/s)  [0=sin viento · 15=costero/montaña]",
        minimo=0.0, maximo=15.0, defecto=5.0, unidad=" m/s"
    )

    hidro = pedir_slider(
        "Caudal hídrico disponible  (m³/s)  [0=sin ríos · 200=río grande]",
        minimo=0.0, maximo=200.0, defecto=10.0, unidad=" m³/s"
    )

    geotermia = pedir_opcion("Actividad geotérmica:", [
        ("nula",  "Nula — sin evidencia"),
        ("baja",  "Baja / posible"),
        ("media", "Media — gradiente conocido"),
        ("alta",  "Alta — fuentes termales activas"),
    ])

    marino = pedir_opcion("Potencial marino:", [
        ("no",     "Sin acceso al mar"),
        ("olas",   "Oleaje moderado"),
        ("mareas", "Mareas significativas"),
        ("alto",   "Offshore potente"),
    ])

    biomasa = pedir_opcion("Disponibilidad de biomasa / residuos agrícolas:", [
        ("nula",  "Nula"),
        ("baja",  "Baja"),
        ("media", "Media"),
        ("alta",  "Alta — zona agroindustrial"),
    ])

    return {
        "solar": solar, "viento": viento, "hidro": hidro,
        "geotermia": geotermia, "marino": marino, "biomasa": biomasa,
    }


def seccion_3_demanda():
    seccion(3, 5, "Demanda y Red Eléctrica",
            "Consumo del territorio e infraestructura existente.")

    demanda = pedir_numero("Demanda estimada (MW)", minimo=0.1, defecto=50, decimales=True)

    tipo_demanda = pedir_opcion("Tipo de demanda principal:", [
        ("residencial", "Residencial"),
        ("industrial",  "Industrial"),
        ("rural",       "Rural / comunidades aisladas"),
        ("mixta",       "Mixta"),
    ])

    red_nacional = pedir_opcion("Conexión a red nacional:", [
        ("si",    "Sí — conectado al SIN"),
        ("debil", "Débil / inestable"),
        ("no",    "No — zona aislada"),
    ])

    fiabilidad = pedir_opcion("Fiabilidad requerida:", [
        ("alta",  "Alta — 24/7 sin interrupciones"),
        ("media", "Media — interrupciones toleradas"),
        ("baja",  "Baja — suministro parcial"),
    ])

    return {
        "demanda": demanda, "tipo_demanda": tipo_demanda,
        "red_nacional": red_nacional, "fiabilidad": fiabilidad,
    }


def seccion_4_economia():
    seccion(4, 5, "Economía y Restricciones",
            "Presupuesto, horizonte de proyecto y limitaciones del territorio.")

    presupuesto = pedir_numero("Presupuesto disponible (MUSD)", minimo=1, defecto=100)

    horizonte = pedir_numero("Horizonte del proyecto (años)", minimo=5, maximo=50, defecto=20)

    prioridad = pedir_opcion("Prioridad principal del proyecto:", [
        ("costo",         "Minimizar costo — LCOE más bajo"),
        ("confiabilidad", "Maximizar confiabilidad de suministro"),
        ("ambiental",     "Impacto ambiental mínimo"),
        ("rapido",        "Despliegue rápido"),
        ("empleo",        "Generación de empleo local"),
    ])

    restricciones = pedir_multiopcion(
        "Restricciones o factores negativos del territorio (0 = Ninguna):",
        [
            ("sismica",     "Zona sísmica de alta actividad"),
            ("inundaciones","Riesgo de inundaciones"),
            ("patrimonio",  "Área protegida / patrimonio ambiental"),
            ("aves",        "Corredor migratorio de aves"),
            ("conflicto",   "Conflicto social o minero"),
            ("agua",        "Escasez hídrica severa"),
            ("transporte",  "Acceso vial deficiente"),
        ]
    )

    return {
        "presupuesto": presupuesto, "horizonte": horizonte,
        "prioridad": prioridad, "restricciones": restricciones,
    }


def seccion_5_preferencias():
    seccion(5, 5, "Parámetros Finales",
            "Últimos datos para calibrar la recomendación.")

    temperatura = pedir_numero(
        "Temperatura promedio anual (°C)", minimo=-20, maximo=55, defecto=24, decimales=True
    )

    precipitacion = pedir_numero(
        "Precipitación anual (mm)", minimo=0, defecto=700
    )

    existentes = pedir_multiopcion(
        "Tecnologías ya instaladas en la zona (0 = Ninguna):",
        [
            ("solar",   "Solar fotovoltaica"),
            ("eolica",  "Eólica terrestre"),
            ("hidro",   "Hidráulica"),
            ("termica", "Térmica convencional"),
        ]
    )

    experiencia = pedir_opcion("Experiencia técnica local:", [
        ("ninguna", "Ninguna — equipo externo necesario"),
        ("basica",  "Básica — electricistas/técnicos generales"),
        ("media",   "Media — ingenieros locales disponibles"),
        ("alta",    "Alta — industria energética establecida"),
    ])

    peso_ambiental = pedir_slider(
        "Peso que das a la sostenibilidad ambiental (0=ignorar · 100=prioritario)",
        minimo=0, maximo=100, defecto=60, unidad="%"
    ) / 100.0

    return {
        "temperatura": temperatura, "precipitacion": precipitacion,
        "existentes": existentes, "experiencia": experiencia,
        "peso_ambiental": peso_ambiental,
    }


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    clear()
    header()

    print(f"  {Color.DIM}Este programa evalúa 9 tecnologías de generación eléctrica y")
    print(f"  recomienda la más conveniente según las condiciones de tu territorio.{Color.RESET}")
    print(f"\n  {Color.CYAN}Responde las 5 secciones de preguntas y obtén el análisis.{Color.RESET}\n")
    input(f"  {Color.GREEN}Presiona ENTER para comenzar...{Color.RESET}")

    datos = {}

    clear(); header(); progreso(1, 5)
    datos.update(seccion_1_geografia())

    clear(); header(); progreso(2, 5)
    datos.update(seccion_2_recursos())

    clear(); header(); progreso(3, 5)
    datos.update(seccion_3_demanda())

    clear(); header(); progreso(4, 5)
    datos.update(seccion_4_economia())

    clear(); header(); progreso(5, 5)
    datos.update(seccion_5_preferencias())

    print(f"\n  {Color.GREEN}Calculando...{Color.RESET}")
    scores = calcular_scores(datos)

    mostrar_resultados(scores, datos)

    while True:
        r = input(f"  {Color.DIM}¿Deseas realizar otra evaluación? (s/n): {Color.RESET}").strip().lower()
        if r == "s":
            main()
            return
        elif r == "n":
            print(f"\n  {Color.GREEN}Gracias por usar EnergyMap. Buena suerte con tu proyecto.{Color.RESET}\n")
            sys.exit(0)


if __name__ == "__main__":
    main()