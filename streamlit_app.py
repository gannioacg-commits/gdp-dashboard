# app.py
import streamlit as st
import pandas as pd
import calendar
import datetime
import os
import random
import shutil
import json
import re
from PIL import Image, ImageDraw, ImageFont

# ===================================================================
#                CONFIG: ARCHIVO GLOBAL COMPARTIDO
# ===================================================================
ARCHIVO_GLOBAL = "vacaciones_global.csv"
ARCHIVO_BACKUP = "vacaciones_global.csv.bak"
APP_SOURCE = __file__

# ===================================================================
#        BLOQUE EMBEBIDO DE REGISTROS (persistencia interna)
# ===================================================================
# BEGIN EMBED_REGISTROS
EMBED_REGISTROS = []
# END EMBED_REGISTROS

# ===================================================================
#                CARGA Y GUARDADO PERMANENTE
# ===================================================================
def cargar_registros_globales():
    try:
        if os.path.exists(ARCHIVO_GLOBAL) and os.path.getsize(ARCHIVO_GLOBAL) > 10:
            df = pd.read_csv(ARCHIVO_GLOBAL)
            if not df.empty:
                return df.to_dict(orient="records")
    except:
        pass

    try:
        if os.path.exists(ARCHIVO_BACKUP) and os.path.getsize(ARCHIVO_BACKUP) > 10:
            df = pd.read_csv(ARCHIVO_BACKUP)
            if not df.empty:
                return df.to_dict(orient="records")
    except:
        pass

    if isinstance(EMBED_REGISTROS, list) and len(EMBED_REGISTROS) > 0:
        return EMBED_REGISTROS

    return []

def guardar_registros_globales(lista):
    if len(lista) == 0:
        st.warning("No se puede guardar un archivo vacío.")
        return

    try:
        if os.path.exists(ARCHIVO_GLOBAL):
            shutil.copy(ARCHIVO_GLOBAL, ARCHIVO_BACKUP)
        pd.DataFrame(lista).to_csv(ARCHIVO_GLOBAL, index=False)
    except Exception as e:
        st.error(f"Error guardando CSV: {e}")

    try:
        embed_registros_en_codigo(lista)
    except Exception as e:
        st.warning(f"No se pudo actualizar el código: {e}")

def embed_registros_en_codigo(lista):
    if not os.path.exists(APP_SOURCE):
        raise FileNotFoundError(APP_SOURCE)

    with open(APP_SOURCE, "r", encoding="utf-8") as f:
        src = f.read()

    json_block = json.dumps(lista, ensure_ascii=False, indent=4)
    replacement = f"# BEGIN EMBED_REGISTROS\nEMBED_REGISTROS = {json_block}\n# END EMBED_REGISTROS"

    pattern = re.compile(
        r"# BEGIN EMBED_REGISTROS\s*.*?# END EMBED_REGISTROS",
        re.DOTALL | re.UNICODE
    )

    if not pattern.search(src):
        new_src = replacement + "\n\n" + src
        with open(APP_SOURCE, "w", encoding="utf-8") as f:
            f.write(new_src)
        return

    shutil.copy(APP_SOURCE, APP_SOURCE + ".bak_src")
    new_src = pattern.sub(replacement, src)

    with open(APP_SOURCE, "w", encoding="utf-8") as f:
        f.write(new_src)

# ===================================================================
#                Helpers
# ===================================================================
def cargar_fuente(size, bold=False):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

# ===================================================================
#                Feriados
# ===================================================================
FERIADOS_STR = {
    "2025-01-01","2025-03-03","2025-03-04","2025-03-24",
    "2025-04-18","2025-04-19","2025-05-01","2025-05-25",
    "2025-06-16","2025-06-20","2025-07-09","2025-08-18",
    "2025-10-13","2025-11-17","2025-12-08","2025-12-25",
    "2026-01-01","2026-02-16","2026-02-17","2026-03-24",
    "2026-04-02","2026-04-03","2026-05-01","2026-05-25",
    "2026-06-17","2026-06-20","2026-07-09","2026-08-17",
    "2026-10-12","2026-11-23","2026-12-08","2026-12-25"
}
FERIADOS = {datetime.datetime.strptime(s, "%Y-%m-%d").date() for s in FERIADOS_STR}

SECTORES = [
    "LABORATORIO", "PRODUCCION", "COMERCIAL", "FACTURACION",
    "COMPRAS", "CONTABLE", "SOCIOS", "SISTEMAS"
]

PALETTE = ["#6EC6FF", "#81C784", "#FFF176", "#F48FB1", "#CE93D8",
           "#FFCC80", "#80CBC4", "#E6EE9C"]

st.set_page_config(page_title="App Vacaciones - Global", layout="wide")

# ===================================================================
#                Session State
# ===================================================================
if "vacaciones" not in st.session_state:
    st.session_state.vacaciones = cargar_registros_globales()

hoy = datetime.date.today()
st.session_state.setdefault("mes", hoy.month)
st.session_state.setdefault("anio", hoy.year)

# ===================================================================
#                Validaciones
# ===================================================================
def feriado_en_puntas(inicio, fin):
    if inicio in FERIADOS:
        return True, f"Inicio {inicio} es feriado."
    if fin in FERIADOS:
        return True, f"Fin {fin} es feriado."
    if (inicio - datetime.timedelta(days=1)) in FERIADOS:
        return True, "El día anterior al inicio es feriado."
    if (fin + datetime.timedelta(days=1)) in FERIADOS:
        return True, "El día siguiente al fin es feriado."
    return False, ""

def ajustar_inicio_por_fin_de_semana(inicio, dias):
    inicio_new = inicio
    msg = ""

    if inicio.weekday() == 5:
        inicio_new += datetime.timedelta(days=2)
        msg = f"Inicio movido de sábado a lunes {inicio_new}"
    elif inicio.weekday() == 6:
        inicio_new += datetime.timedelta(days=1)
        msg = f"Inicio movido de domingo a lunes {inicio_new}"

    fin_new = inicio_new + datetime.timedelta(days=dias-1)
    return inicio_new, fin_new, msg

def solapamiento_mismo_sector(inicio, fin, sector):
    for r in st.session_state.vacaciones:
        if r["Sector"].upper() != sector.upper():
            continue
        ri = datetime.datetime.strptime(r["Inicio"], "%Y-%m-%d").date()
        rf = datetime.datetime.strptime(r["Fin"], "%Y-%m-%d").date()
        if inicio <= rf and fin >= ri:
            return True, r["Nombre"]
    return False, None

# ===================================================================
#                Sidebar — Registrar vacaciones
# ===================================================================
with st.sidebar:
    st.header("Registrar vacaciones")

    nombre = st.text_input("Nombre")
    sector = st.selectbox("Sector", SECTORES)
    fecha_inicio = st.date_input("Inicio", value=hoy)
    dur = st.radio("Duración", ["1 semana (7 días)", "2 semanas (14 días)"])
    dias = 7 if "1" in dur else 14

    existing_colors = {v["Nombre"]: v["Color"] for v in st.session_state.vacaciones}
    color_default = existing_colors.get(nombre, random.choice(PALETTE))
    color = st.color_picker("Color", value=color_default)

    if st.button("Registrar"):
        if not nombre.strip():
            st.error("Ingresá un nombre.")
        else:
            inicio_adj, fin_adj, msg_adj = ajustar_inicio_por_fin_de_semana(fecha_inicio, dias)
            if msg_adj:
                st.info(msg_adj)

            err, msg = feriado_en_puntas(inicio_adj, fin_adj)
            if err:
                st.error(msg)
            else:
                sup, quien = solapamiento_mismo_sector(inicio_adj, fin_adj, sector)
                if sup:
                    st.error(f"Superposición con {quien}")
                else:
                    rec = {
                        "Nombre": nombre,
                        "Sector": sector,
                        "Inicio": inicio_adj.isoformat(),
                        "Fin": fin_adj.isoformat(),
                        "Color": color
                    }
                    st.session_state.vacaciones.append(rec)
                    guardar_registros_globales(st.session_state.vacaciones)
                    st.success("Registrado ✔")

# ===================================================================
#                Tabla + Eliminar
# ===================================================================
st.title("📅 App de Vacaciones — Registros Globales")

if len(st.session_state.vacaciones) == 0:
    st.info("Sin registros.")
else:
    df = pd.DataFrame(st.session_state.vacaciones)
    st.dataframe(df)

    st.subheader("Eliminar registro")
    opts = [f"{i} · {r['Nombre']} ({r['Inicio']})" for i, r in enumerate(st.session_state.vacaciones)]
    sel = st.selectbox("Seleccionar registro", opts)

    if st.button("Eliminar"):
        idx = int(sel.split(" · ")[0])
        eliminado = st.session_state.vacaciones.pop(idx)
        guardar_registros_globales(st.session_state.vacaciones)
        st.success(f"Eliminado: {eliminado['Nombre']}")

# ===================================================================
#                Construir mapa
# ===================================================================
def construir_map_dias():
    mapa = {}
    for r in st.session_state.vacaciones:
        inicio = datetime.datetime.strptime(r["Inicio"], "%Y-%m-%d").date()
        fin = datetime.datetime.strptime(r["Fin"], "%Y-%m-%d").date()
        d = inicio
        while d <= fin:
            mapa.setdefault(d, []).append((r["Nombre"], r["Color"], r["Sector"]))
            d += datetime.timedelta(days=1)
    return mapa

mapa_dias = construir_map_dias()

# ===================================================================
#                Generar calendario
# ===================================================================
def generar_calendario_reducido(mes, anio, mapa, feriados):
    nombres_meses = [
        "Enero","Febrero","Marzo","Abril","Mayo","Junio",
        "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
    ]
    dias_sem = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

    cell_w = 86
    cell_h = 62
    margin_x = 24
    margin_y = 110

    width = margin_x*2 + cell_w*7
    height = margin_y + cell_h*6 + 20

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    font_title = cargar_fuente(20, bold=True)
    font_header = cargar_fuente(12)
    font_num = cargar_fuente(14)
    font_name = cargar_fuente(11)

    draw.text((width//2, 18), f"{nombres_meses[mes-1]} {anio}", fill="black", anchor="mm", font=font_title)

    for i, d in enumerate(dias_sem):
        x = margin_x + i*cell_w + cell_w//2
        draw.text((x, 60), d, fill="black", anchor="mm", font=font_header)

    cal = calendar.monthcalendar(anio, mes)

    y = margin_y
    for week in cal:
        x = margin_x
        for day in week:
            rect = [x+4, y+4, x+cell_w-4, y+cell_h-4]

            if day == 0:
                draw.rectangle(rect, fill="#FAFAFA", outline="#EFEFEF")
            else:
                fecha = datetime.date(anio, mes, day)

                if fecha in feriados:
                    draw.rectangle(rect, fill="#FF6B6B", outline="#B22222")
                else:
                    draw.rectangle(rect, fill="#FFF", outline="#CCC")

                if fecha in mapa:
                    for i,(nombre,color,_) in enumerate(mapa[fecha][:3]):
                        y1 = y + 26 + i*18
                        draw.rectangle([x+8, y1, x+cell_w-12, y1+14], fill=color, outline="#444")
                        txt = nombre if len(nombre)<=14 else nombre[:11]+"..."
                        draw.text((x+10, y1+1), txt, fill="black", font=font_name)

                draw.text((x+cell_w-14, y+6), str(day), fill="black", font=font_num)

            x += cell_w
        y += cell_h

    return img

# ===================================================================
#                Navegación de meses
# ===================================================================
c1, _, c3 = st.columns([1,1,1])

with c1:
    if st.button("⬅ Mes anterior"):
        st.session_state.mes -= 1
        if st.session_state.mes == 0:
            st.session_state.mes = 12
            st.session_state.anio -= 1

with c3:
    if st.button("Mes siguiente ➡"):
        st.session_state.mes += 1
        if st.session_state.mes == 13:
            st.session_state.mes = 1
            st.session_state.anio += 1

# ===================================================================
#                Render calendario
# ===================================================================
st.subheader("Calendario Global (Reducido)")

img = generar_calendario_reducido(
    st.session_state.mes,
    st.session_state.anio,
    mapa_dias,
    FERIADOS
)

st.image(img, width=min(900, img.width))


