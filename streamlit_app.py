# app.py
import streamlit as st
import pandas as pd
import datetime
import calendar
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

# ---------------------------
# Configuración y helpers
# ---------------------------
st.set_page_config(page_title="App Vacaciones", layout="wide")

# Fuente segura (DejaVu incluida con Pillow)
def cargar_fuente(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

# Feriados 2025 y 2026 (YYYY-MM-DD)
FERIADOS_STR = {
    # 2025
    "2025-01-01","2025-03-03","2025-03-04","2025-03-24","2025-04-18","2025-04-19",
    "2025-05-01","2025-05-25","2025-06-16","2025-06-20","2025-07-09","2025-08-18",
    "2025-10-13","2025-11-17","2025-12-08","2025-12-25",
    # 2026
    "2026-01-01","2026-02-16","2026-02-17","2026-03-24","2026-04-02","2026-04-03",
    "2026-05-01","2026-05-25","2026-06-17","2026-06-20","2026-07-09","2026-08-17",
    "2026-10-12","2026-11-23","2026-12-08","2026-12-25"
}
FERIADOS = {datetime.datetime.strptime(s, "%Y-%m-%d").date() for s in FERIADOS_STR}

SECTORES = ["LABORATORIO", "PRODUCCION", "COMERCIAL", "FACTURACION", "COMPRAS", "CONTABLE", "SOCIOS"]
PALETTE = ["#6EC6FF", "#81C784", "#FFF176", "#F48FB1", "#CE93D8", "#FFCC80", "#80CBC4", "#E6EE9C"]

CSV_FILE = "vacaciones.csv"  # opcional: guarda en disco además de en session_state

# ---------------------------
# Session state init
# ---------------------------
if "vacaciones" not in st.session_state:
    st.session_state.vacaciones = []  # lista de dicts: {Nombre, Sector, Inicio(str ISO), Fin(str ISO), Color}

if "mes" not in st.session_state:
    hoy = datetime.date.today()
    st.session_state.mes = hoy.month
if "anio" not in st.session_state:
    st.session_state.anio = hoy.year

# ---------------------------
# I/O opcional CSV
# ---------------------------
def guardar_csv_local():
    try:
        df = pd.DataFrame(st.session_state.vacaciones)
        df.to_csv(CSV_FILE, index=False)
        return True
    except Exception as e:
        return False

def cargar_csv_local():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # asegurar columnas y formato (Inicio/Fin ISO)
            required = ["Nombre","Sector","Inicio","Fin","Color"]
            for c in required:
                if c not in df.columns:
                    df[c] = ""
            # convertir a lista de dicts
            st.session_state.vacaciones = df[required].to_dict(orient="records")
            return True
        except:
            return False
    return False

# intentar cargar CSV al inicio si session vacía
if len(st.session_state.vacaciones) == 0:
    cargar_csv_local()

# ---------------------------
# Utilidades de validación
# ---------------------------
def es_feriado(fecha: datetime.date) -> bool:
    return fecha in FERIADOS

def feriado_en_puntas(inicio: datetime.date, fin: datetime.date):
    """
    Reglas prohibidas:
     - inicio es feriado
     - fin es feriado
     - inicio un dia después de feriado (i.e. dia anterior inicio es feriado)
     - fin un dia antes de feriado (i.e. dia siguiente fin es feriado)
    """
    if inicio in FERIADOS:
        return True, f"El primer día ({inicio}) es feriado."
    if fin in FERIADOS:
        return True, f"El último día ({fin}) es feriado."
    if (inicio - datetime.timedelta(days=1)) in FERIADOS:
        prev = (inicio - datetime.timedelta(days=1))
        return True, f"No podés iniciar el {inicio} porque el día anterior ({prev}) es feriado."
    if (fin + datetime.timedelta(days=1)) in FERIADOS:
        nxt = (fin + datetime.timedelta(days=1))
        return True, f"No podés finalizar el {fin} porque el día siguiente ({nxt}) es feriado."
    return False, ""

def ajustar_si_fin_de_semana(inicio: datetime.date, dias:int):
    """
    Si inicio cae en sábado/domingo desplazalo al lunes siguiente.
    Ajusta fin manteniendo la duración.
    Devuelve (inicio_ajustado, fin_ajustado, mensaje) — mensaje si se ajustó.
    """
    msg = ""
    inicio_new = inicio
    if inicio.weekday() == 5:  # sábado
        delta = 2
        inicio_new = inicio + datetime.timedelta(days=delta)
        msg = f"El inicio cayó en sábado; se desplazó al lunes {inicio_new}."
    elif inicio.weekday() == 6:  # domingo
        delta = 1
        inicio_new = inicio + datetime.timedelta(days=delta)
        msg = f"El inicio cayó en domingo; se desplazó al lunes {inicio_new}."
    fin_new = inicio_new + datetime.timedelta(days=dias-1)
    return inicio_new, fin_new, msg

def solapamiento_mismo_sector(inicio: datetime.date, fin: datetime.date, sector: str):
    for rec in st.session_state.vacaciones:
        if rec.get("Sector","").strip().upper() != sector.strip().upper():
            continue
        # parse stored dates
        try:
            ri = datetime.datetime.strptime(rec["Inicio"], "%Y-%m-%d").date()
            rf = datetime.datetime.strptime(rec["Fin"], "%Y-%m-%d").date()
        except:
            continue
        # overlap check
        if (inicio <= rf) and (fin >= ri):
            return True, rec["Nombre"]
    return False, None

# ---------------------------
# UI - Sidebar: registrar
# ---------------------------
st.title("📅 Gestión de Vacaciones - Versión B (Integrada)")
with st.sidebar:
    st.header("Registrar vacaciones")
    nombre = st.text_input("Nombre del empleado")
    sector = st.selectbox("Sector", SECTORES)
    fecha_inicio = st.date_input("Fecha de inicio", value=datetime.date.today())
    dur = st.radio("Duración", ["1 semana (7 días)","2 semanas (14 días)"])
    dias = 7 if dur.startswith("1") else 14

    # sugerir color por empleado si ya existe
    color_sugerido = None
    for r in st.session_state.vacaciones:
        if r.get("Nombre","").strip().lower() == nombre.strip().lower() and r.get("Color"):
            color_sugerido = r["Color"]
            break
    if not color_sugerido:
        color_sugerido = random.choice(PALETTE)
    color = st.color_picker("Color", value=color_sugerido)

    st.write("") 
    st.checkbox_label = st.checkbox("Guardar también localmente en vacations CSV (opcional)", value=True, key="guardar_local_opt")
    if st.button("Registrar"):
        if not nombre.strip():
            st.error("Ingresá un nombre.")
        else:
            # ajustar fin de semana si aplica
            inicio_aj, fin_aj, msg_aj = ajustar_si_fin_de_semana(fecha_inicio, dias)
            if msg_aj:
                st.info(msg_aj)

            # validar feriados en puntas
            err, msg = feriado_en_puntas(inicio_aj, fin_aj)
            if err:
                st.error(msg)
            else:
                # validar solapamiento
                sup, quien = solapamiento_mismo_sector(inicio_aj, fin_aj, sector)
                if sup:
                    st.error(f"Solapamiento con {quien} del mismo sector.")
                else:
                    # grabar
                    rec = {
                        "Nombre": nombre.strip(),
                        "Sector": sector,
                        "Inicio": inicio_aj.isoformat(),
                        "Fin": fin_aj.isoformat(),
                        "Color": color
                    }
                    st.session_state.vacaciones.append(rec)
                    # opcional guardar local
                    if st.session_state.get("guardar_local_opt", True):
                        guardar_csv_local()
                    st.success(f"Registrado: {nombre} ({inicio_aj} → {fin_aj})")

# ---------------------------
# UI principal: registros y acciones
# ---------------------------
st.subheader("Registros actuales")
if len(st.session_state.vacaciones) == 0:
    st.info("No hay vacaciones registradas.")
else:
    df_show = pd.DataFrame(st.session_state.vacaciones)
    with st.expander("Ver tabla completa"):
        st.dataframe(df_show)

    # eliminar
    st.markdown("### 🗑 Eliminar registro")
    options = [f"{i} - {r['Nombre']} ({r['Inicio']}) - {r['Sector']}" for i, r in enumerate(st.session_state.vacaciones)]
    sel = st.selectbox("Seleccioná registro para eliminar", options)
    if st.button("Eliminar seleccionado"):
        idx = int(sel.split(" - ")[0])
        eliminado = st.session_state.vacaciones.pop(idx)
        # actualizar CSV local
        if st.session_state.get("guardar_local_opt", True):
            guardar_csv_local()
        st.success(f"Eliminado: {eliminado['Nombre']} ({eliminado['Inicio']})")

    # export CSV desde memoria
    def export_csv_bytes(data):
        df = pd.DataFrame(data)
        return df.to_csv(index=False).encode("utf-8")
    csv_bytes = export_csv_bytes(st.session_state.vacaciones)
    st.download_button("📥 Descargar CSV (memoria)", data=csv_bytes, file_name="vacaciones_memoria.csv", mime="text/csv")

# ---------------------------
# Construir mapa días -> eventos
# ---------------------------
def construir_map_dias():
    mapa = {}  # date -> list of (nombre,color,sector)
    for rec in st.session_state.vacaciones:
        try:
            inicio = datetime.datetime.strptime(rec["Inicio"], "%Y-%m-%d").date()
            fin = datetime.datetime.strptime(rec["Fin"], "%Y-%m-%d").date()
        except:
            continue
        d = inicio
        while d <= fin:
            if d not in mapa:
                mapa[d] = []
            mapa[d].append((rec["Nombre"], rec["Color"], rec["Sector"]))
            d += datetime.timedelta(days=1)
    return mapa

mapa_dias = construir_map_dias()

# ---------------------------
# Calendario navegable y render
# ---------------------------
st.subheader("Calendario gráfico")
col_left, col_mid, col_right = st.columns([1,2,1])
with col_left:
    if st.button("⬅ Mes anterior"):
        st.session_state.mes -= 1
        if st.session_state.mes == 0:
            st.session_state.mes = 12
            st.session_state.anio -= 1
with col_mid:
    mes_sel = st.selectbox("Mes", list(range(1,13)), index=st.session_state.mes - 1, format_func=lambda x: calendar.month_name[x])
    anio_sel = st.number_input("Año", min_value=2024, max_value=2035, value=st.session_state.anio)
    st.session_state.mes = mes_sel
    st.session_state.anio = anio_sel
with col_right:
    if st.button("Mes siguiente ➡"):
        st.session_state.mes += 1
        if st.session_state.mes == 13:
            st.session_state.mes = 1
            st.session_state.anio += 1

vista = st.selectbox("Vista", ["Mensual","Semanal"], index=0)

# idiomas esp
MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
DIAS_ES = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

# dibujar calendario mens/sem
def dibujar_calendario_mensual(mes, anio, mapa):
    # canvas
    ancho = 1000
    alto = 720
    margin_x = 40
    margin_y = 120
    cell_w = (ancho - margin_x*2) // 7
    cell_h = 110

    img = Image.new("RGB", (ancho, alto), "white")
    draw = ImageDraw.Draw(img)
    font_title = cargar_fuente(36)
    font_header = cargar_fuente(18)
    font_num = cargar_fuente(16)
    font_name = cargar_fuente(14)

    # titulo centrado
    titulo = f"{MESES_ES[mes-1]} {anio}"
    draw.text((ancho//2, 30), titulo, fill="black", anchor="mm", font=font_title)

    # headers dias
    for i, d in enumerate(DIAS_ES):
        x = margin_x + i*cell_w + cell_w//2
        draw.text((x, 85), d, fill="black", anchor="mm", font=font_header)

    cal = calendar.monthcalendar(anio, mes)
    y = margin_y
    for semana in cal:
        x = margin_x
        for dia in semana:
            rect = [x+6, y+6, x+cell_w-6, y+cell_h-6]
            if dia == 0:
                draw.rectangle(rect, outline="#EFEFEF", fill="#FAFAFA")
            else:
                fecha = datetime.date(anio, mes, dia)
                # feriado?
                if fecha in FERIADOS:
                    draw.rectangle(rect, fill="#FF6B6B", outline="#B22222")
                else:
                    draw.rectangle(rect, fill="#FFFFFF", outline="#E6E6E6")

                # si hay vacaciones mostrar franjas
                if fecha in mapa:
                    ocup = mapa[fecha][:4]  # hasta 4
                    stripe_h = 16
                    y0 = y + 28
                    for idx, (nombre, color, sector) in enumerate(ocup):
                        bx1 = x + 10
                        by1 = y0 + idx*(stripe_h+6)
                        bx2 = x + cell_w - 20
                        by2 = by1 + stripe_h
                        draw.rectangle([bx1, by1, bx2, by2], fill=color, outline="#555")
                        txt = nombre if len(nombre) <= 18 else nombre[:15] + "..."
                        draw.text((bx1 + 6, by1 + 1), txt, fill="black", font=font_name)

                # día número
                draw.text((x + cell_w - 22, y + 10), str(dia), fill="black", font=font_num)

            x += cell_w
        y += cell_h

    return img

def dibujar_calendario_semanal(mes, anio, semana_idx, mapa):
    cal = calendar.monthcalendar(anio, mes)
    if semana_idx < 1 or semana_idx > len(cal):
        semana_idx = 1
    semana = cal[semana_idx-1]

    ancho = 1000
    alto = 360
    img = Image.new("RGB", (ancho, alto), "white")
    draw = ImageDraw.Draw(img)
    font_title = cargar_fuente(20)
    font_num = cargar_fuente(16)
    font_name = cargar_fuente(14)

    # encabezados dias
    titulo = f"Semana {semana_idx} - {MESES_ES[mes-1]} {anio}"
    draw.text((ancho//2, 20), titulo, fill="black", anchor="mm", font=font_title)

    cell_w = (ancho - 80) // 7
    x = 40
    for i, dia in enumerate(semana):
        rect = [x, 60, x + cell_w - 10, alto - 40]
        if dia == 0:
            draw.rectangle(rect, fill="#F5F5F5", outline="#DDD")
        else:
            fecha = datetime.date(anio, mes, dia)
            if fecha in FERIADOS:
                draw.rectangle(rect, fill="#FF6B6B", outline="#B22222")
            else:
                draw.rectangle(rect, fill="#FFFFFF", outline="#DDD")
            # número
            draw.text((x + 8, 66), str(dia), fill="black", font=font_num)
            if fecha in mapa:
                occ = mapa[fecha][:6]
                y_text = 96
                for (nombre, color, sector) in occ:
                    draw.rectangle([x+8, y_text, x+cell_w-20, y_text+18], fill=color, outline="#333")
                    txt = nombre if len(nombre) <= 26 else nombre[:23] + "..."
                    draw.text((x+12, y_text+2), txt, fill="black", font=font_name)
                    y_text += 22
        x += cell_w

    return img

# renderizar
if vista == "Mensual":
    img = dibujar_calendario_mensual(st.session_state.mes, st.session_state.anio, mapa_dias)
    st.image(img, use_column_width=True)
else:
    cal = calendar.monthcalendar(st.session_state.anio, st.session_state.mes)
    num_sem = len(cal)
    semana_sel = st.number_input("Semana del mes", min_value=1, max_value=num_sem, value=1)
    img = dibujar_calendario_semanal(st.session_state.mes, st.session_state.anio, semana_sel, mapa_dias)
    st.image(img, use_column_width=True)

st.markdown("---")
st.caption("Feriados (fondo rojo). Reglas: feriados no pueden estar en las puntas ni adyacentes; "
           "solapamiento solo si distinto sector. Datos guardados en memoria y opcionalmente en vacations CSV.")
