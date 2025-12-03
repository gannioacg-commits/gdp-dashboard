# app.py
import streamlit as st
import pandas as pd
import calendar
import datetime
import os
import random
import shutil
import base64
from PIL import Image, ImageDraw, ImageFont

# ===================================================================
#                CONFIG: ARCHIVO GLOBAL COMPARTIDO
# ===================================================================
ARCHIVO_GLOBAL = "vacaciones_global.csv"
ARCHIVO_BACKUP = "vacaciones_global.csv.bak"

# ===================================================================
#                RUTAS POSIBLES DE LOS AUDIOS (orden de prioridad)
# ===================================================================
# Rutas donde ya subiste los audios en el entorno (ej: /mnt/data)
POSSIBLE_PATHS = [
    "/mnt/data/WhatsApp Ptt 2025-12-03 at 3.25.14 PM.ogg",
    "/mnt/data/WhatsApp Audio 2025-11-18 at 10.12.57 AM.ogg",
    # rutas locales relativas (si decidís guardarlos al lado del app.py o en data/)
    "WhatsApp Ptt 2025-12-03 at 3.25.14 PM.ogg",
    "WhatsApp Audio 2025-11-18 at 10.12.57 AM.ogg",
    "data/WhatsApp Ptt 2025-12-03 at 3.25.14 PM.ogg",
    "data/WhatsApp Audio 2025-11-18 at 10.12.57 AM.ogg",
    "audio/WhatsApp Ptt 2025-12-03 at 3.25.14 PM.ogg",
    "audio/WhatsApp Audio 2025-11-18 at 10.12.57 AM.ogg",
]

# ===================================================================
#                Helpers para cargar/embeder audio (Base64)
# ===================================================================
def file_to_base64_dataurl(path):
    """Convierte un archivo de audio local a data-url base64 (tipo audio/ogg)."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        # Intentamos detectar el tipo por extensión (ogg/mp3/wav)
        ext = os.path.splitext(path)[1].lower()
        if ext == ".mp3":
            mime = "audio/mpeg"
        elif ext == ".wav":
            mime = "audio/wav"
        else:
            mime = "audio/ogg"
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None

def find_and_load_audio(preferred_name_fragments):
    """
    Busca en POSSIBLE_PATHS un archivo que contenga alguno de los fragments y lo convierte a data-url.
    preferred_name_fragments: list of strings to match in file name (e.g. ['Ptt 2025-12-03', 'Audio 2025-11-18'])
    """
    for frag in preferred_name_fragments:
        for p in POSSIBLE_PATHS:
            if frag in p and os.path.exists(p):
                url = file_to_base64_dataurl(p)
                if url:
                    return url
    # fallback: try any file in POSSIBLE_PATHS existing
    for p in POSSIBLE_PATHS:
        if os.path.exists(p):
            url = file_to_base64_dataurl(p)
            if url:
                return url
    return None

# Intentamos cargar ambos audios desde las rutas conocidas (orden lógico)
SONIDO_ERROR_DATAURL = find_and_load_audio(["Ptt 2025-12-03", "Ptt 2025-12-03 at 3.25.14"])
SONIDO_OK_DATAURL = find_and_load_audio(["Audio 2025-11-18", "10.12.57"])

# Si no se encontraron y querés, podés pegar aquí directamente el data-url como string:
# SONIDO_ERROR_DATAURL = "data:audio/ogg;base64,...."
# SONIDO_OK_DATAURL = "data:audio/ogg;base64,...."

def reproducir_dataurl(dataurl):
    """Inserta un tag <audio autoplay> con el dataurl. Usa st.markdown unsafe."""
    if not dataurl:
        return
    # Autoplay only works reliably if el browser permite el audio (algunos requieren interacción)
    st.markdown(
        f"""
        <audio autoplay>
            <source src="{dataurl}">
        </audio>
        """,
        unsafe_allow_html=True
    )

def reproducir_error():
    if SONIDO_ERROR_DATAURL:
        reproducir_dataurl(SONIDO_ERROR_DATAURL)
    else:
        # fallback: si no hay dataurl, no romper: puedes optar por st.audio si archivo está presente
        # (intento reproducir desde archivo si existe)
        for p in POSSIBLE_PATHS:
            if "Ptt" in p and os.path.exists(p):
                try:
                    st.audio(open(p, "rb").read(), format="audio/ogg")
                    return
                except:
                    pass
        # si no hay nada, no hace nada
        st.warning("")  # silencioso, evita mostrar error molesto

def reproducir_ok():
    if SONIDO_OK_DATAURL:
        reproducir_dataurl(SONIDO_OK_DATAURL)
    else:
        for p in POSSIBLE_PATHS:
            if "Audio" in p and os.path.exists(p):
                try:
                    # el tipo puede ser ogg o mp3; streamlit detecta por bytes
                    st.audio(open(p, "rb").read())
                    return
                except:
                    pass
        st.warning("")


# ===================================================================
#                CARGA Y GUARDADO SEGURO
# ===================================================================
def cargar_registros_globales():
    if os.path.exists(ARCHIVO_GLOBAL) and os.path.getsize(ARCHIVO_GLOBAL) > 10:
        try:
            df = pd.read_csv(ARCHIVO_GLOBAL)
            if df.empty:
                return []
            return df.to_dict(orient="records")
        except:
            if os.path.exists(ARCHIVO_BACKUP):
                try:
                    df = pd.read_csv(ARCHIVO_BACKUP)
                    return df.to_dict(orient="records")
                except:
                    return []
            return []
    return []


def guardar_registros_globales(lista):
    if len(lista) == 0:
        st.warning("Protección activada: no se guarda un archivo vacío.")
        return

    try:
        if os.path.exists(ARCHIVO_GLOBAL):
            shutil.copy(ARCHIVO_GLOBAL, ARCHIVO_BACKUP)

        pd.DataFrame(lista).to_csv(ARCHIVO_GLOBAL, index=False)
    except Exception as e:
        st.error(f"Error guardando archivo global: {e}")


# ===================================================================
#                Helpers (fuente segura)
# ===================================================================
def cargar_fuente(size, bold=False):
    try:
        if bold:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()


# ===================================================================
#                Feriados 2025 + 2026
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
#                Session State INIT
# ===================================================================
if "vacaciones" not in st.session_state:
    st.session_state.vacaciones = cargar_registros_globales()

hoy = datetime.date.today()
if "mes" not in st.session_state:
    st.session_state.mes = hoy.month
if "anio" not in st.session_state:
    st.session_state.anio = hoy.year


# ===================================================================
#                Utils
# ===================================================================
def feriado_en_puntas(inicio, fin):
    if inicio in FERIADOS:
        return True, f"El día de inicio ({inicio}) es feriado."
    if fin in FERIADOS:
        return True, f"El día final ({fin}) es feriado."
    if (inicio - datetime.timedelta(days=1)) in FERIADOS:
        return True, "El día anterior al inicio es feriado."
    if (fin + datetime.timedelta(days=1)) in FERIADOS:
        return True, "El día siguiente al fin es feriado."
    return False, ""


def ajustar_inicio_por_fin_de_semana(inicio, dias):
    inicio_new = inicio
    msg = ""
    if inicio.weekday() == 5:
        inicio_new = inicio + datetime.timedelta(days=2)
        msg = f"Inicio en sábado → movido al lunes {inicio_new}."
    elif inicio.weekday() == 6:
        inicio_new = inicio + datetime.timedelta(days=1)
        msg = f"Inicio en domingo → movido al lunes {inicio_new}."

    fin_new = inicio_new + datetime.timedelta(days=dias - 1)
    return inicio_new, fin_new, msg


def solapamiento_mismo_sector(inicio, fin, sector):
    for rec in st.session_state.vacaciones:
        if rec["Sector"].upper() != sector.upper():
            continue
        ri = datetime.datetime.strptime(rec["Inicio"], "%Y-%m-%d").date()
        rf = datetime.datetime.strptime(rec["Fin"], "%Y-%m-%d").date()
        if (inicio <= rf) and (fin >= ri):
            return True, rec["Nombre"]
    return False, None


# ===================================================================
#                Sidebar — Registrar vacaciones
# ===================================================================
with st.sidebar:
    st.header("Registrar vacaciones")

    nombre = st.text_input("Nombre del empleado")
    sector = st.selectbox("Sector", SECTORES)
    fecha_inicio = st.date_input("Fecha de inicio", value=datetime.date.today())
    dur = st.radio("Duración", ["1 semana (7 días)", "2 semanas (14 días)"])
    dias = 7 if dur.startswith("1") else 14

    existing_colors = {v["Nombre"]: v["Color"] for v in st.session_state.vacaciones}
    color_default = existing_colors.get(nombre, random.choice(PALETTE))
    color = st.color_picker("Color (opcional)", value=color_default)

    if st.button("Registrar"):

        # ❌ Validación nombre vacío
        if not nombre.strip():
            st.error("Ingresá el nombre.")
            reproducir_error()
        else:
            inicio_adj, fin_adj, msg_adj = ajustar_inicio_por_fin_de_semana(fecha_inicio, dias)
            if msg_adj:
                st.info(msg_adj)

            # ❌ Caso feriado
            err, msg = feriado_en_puntas(inicio_adj, fin_adj)
            if err:
                st.error(msg)
                # Solo reproducir error si es feriado o solapamiento
                reproducir_error()
            else:
                # ❌ Caso solapamiento
                sup, quien = solapamiento_mismo_sector(inicio_adj, fin_adj, sector)
                if sup:
                    st.error(f"Se superpone con {quien}.")
                    reproducir_error()
                else:
                    # ✔️ REGISTRO CORRECTO
                    rec = {
                        "Nombre": nombre,
                        "Sector": sector,
                        "Inicio": inicio_adj.isoformat(),
                        "Fin": fin_adj.isoformat(),
                        "Color": color
                    }

                    st.session_state.vacaciones.append(rec)
                    guardar_registros_globales(st.session_state.vacaciones)

                    st.success("Registrado correctamente")
                    reproducir_ok()


# ===================================================================
#                Tabla + Eliminar
# ===================================================================
st.title("📅 App de Vacaciones — Registros Globales")

if len(st.session_state.vacaciones) == 0:
    st.info("No hay registros cargados.")
else:
    df = pd.DataFrame(st.session_state.vacaciones)
    st.dataframe(df)

    st.subheader("Eliminar registro")
    opts = [f"{i} · {r['Nombre']} ({r['Inicio']})" for i, r in enumerate(st.session_state.vacaciones)]
    sel = st.selectbox("Seleccionar", opts)

    if st.button("Eliminar"):
        idx = int(sel.split(" · ")[0])
        eliminado = st.session_state.vacaciones.pop(idx)
        guardar_registros_globales(st.session_state.vacaciones)
        st.success(f"Eliminado: {eliminado['Nombre']}")

# ===================================================================
#                Construye mapa días
# ===================================================================
def construir_map_dias():
    mapa = {}
    for rec in st.session_state.vacaciones:
        inicio = datetime.datetime.strptime(rec["Inicio"], "%Y-%m-%d").date()
        fin = datetime.datetime.strptime(rec["Fin"], "%Y-%m-%d").date()
        d = inicio
        while d <= fin:
            mapa.setdefault(d, []).append((rec["Nombre"], rec["Color"], rec["Sector"]))
            d += datetime.timedelta(days=1)
    return mapa

mapa_dias = construir_map_dias()

# ===================================================================
#                Calendario reducido
# ===================================================================
def generar_calendario_reducido(mes, anio, mapa, feriados):

    nombres_meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                     "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    dias_sem = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

    cell_w = 86
    cell_h = 62
    margin_x = 24
    margin_y = 110
    header_h = 60

    width = margin_x * 2 + cell_w * 7
    height = margin_y + cell_h * 6 + 20

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    font_title = cargar_fuente(20, bold=True)
    font_header = cargar_fuente(12)
    font_num = cargar_fuente(14)
    font_name = cargar_fuente(11)

    draw.text((width//2, 18), f"{nombres_meses[mes-1]} {anio}",
              fill="black", anchor="mm", font=font_title)

    for i, d in enumerate(dias_sem):
        x = margin_x + i*cell_w + cell_w//2
        draw.text((x, 60), d, fill="black", anchor="mm", font=font_header)

    cal = calendar.monthcalendar(anio, mes)

    y = margin_y
    for week in cal:
        x = margin_x
        for day in week:
            rect = [x+4, y+4, x + cell_w - 4, y + cell_h - 4]

            if day == 0:
                draw.rectangle(rect, fill="#FAFAFA", outline="#EFEFEF")
            else:
                fecha = datetime.date(anio, mes, day)

                if fecha in feriados:
                    draw.rectangle(rect, fill="#FF6B6B", outline="#B22222")
                else:
                    draw.rectangle(rect, fill="#FFF", outline="#CCC")

                if fecha in mapa:
                    for i, (nombre, color, _) in enumerate(mapa[fecha][:3]):
                        y1 = y + 26 + i * 18
                        draw.rectangle(
                            [x+8, y1, x+cell_w-12, y1+14],
                            fill=color, outline="#444"
                        )
                        txt = nombre if len(nombre) <= 14 else nombre[:11] + "..."
                        draw.text((x+10, y1+1), txt, fill="black", font=font_name)

                draw.text(
                    (x + cell_w - 14, y + 6),
                    str(day),
                    fill="black",
                    font=font_num
                )

            x += cell_w
        y += cell_h

    return img


# ===================================================================
#                Navegación de meses
# ===================================================================
cola1, cola2, cola3 = st.columns([1, 1, 1])

with cola1:
    if st.button("⬅ Mes anterior"):
        st.session_state.mes -= 1
        if st.session_state.mes == 0:
            st.session_state.mes = 12
            st.session_state.anio -= 1

with cola3:
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

st.image(img, use_column_width=False, width=min(900, img.width))

