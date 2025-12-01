import streamlit as st
import pandas as pd
import datetime
import calendar
from PIL import Image, ImageDraw, ImageFont
import random

FILE = "vacaciones.csv"

# ================================
# FERIADOS ARGENTINA 2025 + 2026
# ================================
FERIADOS = {
    # ---- 2025 ----
    "2025-01-01", "2025-03-03", "2025-03-04", "2025-03-24",
    "2025-04-18", "2025-05-01", "2025-05-25", "2025-06-20",
    "2025-06-16", "2025-07-09", "2025-08-18", "2025-10-13",
    "2025-11-17", "2025-12-08", "2025-12-25",

    # ---- 2026 ----
    "2026-01-01", "2026-02-16", "2026-02-17", "2026-03-24",
    "2026-04-02", "2026-04-03", "2026-05-01", "2026-05-25",
    "2026-06-17", "2026-06-20", "2026-07-09", "2026-08-17",
    "2026-10-12", "2026-11-23", "2026-12-08", "2026-12-25",
}


# =====================================================
# CARGA Y REPARACIÓN AUTOMÁTICA DEL CSV
# =====================================================
def cargar_datos():
    columnas = ["Empleado", "Sector", "Inicio", "Fin", "Color"]

    try:
        df = pd.read_csv(FILE)
        for c in columnas:
            if c not in df.columns:
                df[c] = ""
        return df[columnas]
    except:
        df = pd.DataFrame(columns=columnas)
        df.to_csv(FILE, index=False)
        return df


def guardar_datos(df):
    df.to_csv(FILE, index=False)


# ================================
# VALIDACIONES
# ================================
def hay_solapamiento(df, inicio, fin, sector):
    """No permite solapamiento dentro del mismo sector."""

    for _, row in df.iterrows():
        if row["Sector"] != sector:
            continue
        
        try:
            ri = datetime.datetime.strptime(row["Inicio"], "%Y-%m-%d").date()
            rf = datetime.datetime.strptime(row["Fin"], "%Y-%m-%d").date()
        except:
            continue

        if (inicio <= rf) and (fin >= ri):
            return True, row["Empleado"]

    return False, None


def toca_feriado_extremo(inicio, fin):
    """No puede empezar ni terminar pegado a feriado."""

    inicio_str = inicio.strftime("%Y-%m-%d")
    fin_str = fin.strftime("%Y-%m-%d")

    if inicio_str in FERIADOS:
        return True

    if fin_str in FERIADOS:
        return True

    # Día previo al inicio
    dia_prev = (inicio - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    if dia_prev in FERIADOS:
        return True

    # Día siguiente al fin
    dia_sig = (fin + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    if dia_sig in FERIADOS:
        return True

    return False


# ================================
# CALENDARIO GRÁFICO
# ================================
def generar_calendario(mes, anio, df):
    ancho = 900
    alto = 650
    cell_w = ancho // 7
    cell_h = 80

    img = Image.new("RGB", (ancho, alto), "white")
    draw = ImageDraw.Draw(img)

    # Título del mes
    font_titulo = ImageFont.truetype("arial.ttf", 32)
    draw.text((10, 10), f"{calendar.month_name[mes]} {anio}", fill="black", font=font_titulo)

    # Días de la semana
    font_dias = ImageFont.truetype("arial.ttf", 20)
    dias_sem = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    for i, d in enumerate(dias_sem):
        draw.text((i * cell_w + 10, 60), d, fill="black", font=font_dias)

    # Calendario
    cal = calendar.monthcalendar(anio, mes)

    font_num = ImageFont.truetype("arial.ttf", 18)

    for fila, semana in enumerate(cal):
        for col, dia in enumerate(semana):
            if dia == 0:
                continue

            x = col * cell_w
            y = 100 + fila * cell_h
            fecha_str = f"{anio}-{mes:02d}-{dia:02d}"

            # Feriado
            if fecha_str in FERIADOS:
                draw.rectangle([(x, y), (x + cell_w, y + cell_h)], fill="#ffb3b3")

            # Vacaciones
            for _, row in df.iterrows():
                if pd.isna(row["Inicio"]) or pd.isna(row["Fin"]):
                    continue

                inicio = datetime.datetime.strptime(row["Inicio"], "%Y-%m-%d").date()
                fin = datetime.datetime.strptime(row["Fin"], "%Y-%m-%d").date()
                fecha_actual = datetime.date(anio, mes, dia)

                if inicio <= fecha_actual <= fin:
                    draw.rectangle([(x, y), (x + cell_w, y + cell_h)], fill=row["Color"])

            # Número del día
            draw.text((x + 5, y + 5), str(dia), fill="black", font=font_num)

    return img


# ================================
# STREAMLIT UI
# ================================
st.set_page_config(layout="wide", page_title="Calendario Vacaciones")

df = cargar_datos()

st.title("📅 Calendario de Vacaciones Empresarial")

col1, col2 = st.columns(2)

with col1:
    nombre = st.text_input("Empleado")
    sector = st.selectbox("Sector", ["LABORATORIO", "PRODUCCION", "COMERCIAL",
                                     "FACTURACION", "COMPRAS", "CONTABLE", "SOCIOS"])
    inicio = st.date_input("Fecha inicio")
    dur = st.radio("Duración", ["1 semana", "2 semanas"])
    dias = 7 if dur == "1 semana" else 14
    fin = inicio + datetime.timedelta(days=dias - 1)

    st.write(f"Finaliza el: **{fin}**")

with col2:
    colores = ["lightblue", "lightgreen", "lightpink", "khaki", "peachpuff", "lightgray"]
    color = random.choice(colores)

    if st.button("Registrar vacaciones"):
        if nombre.strip() == "":
            st.error("Debe ingresar nombre.")
        else:
            # Validaciones
            superp, quien = hay_solapamiento(df, inicio, fin, sector)
            if superp:
                st.error(f"Solapamiento con {quien} del mismo sector.")
            elif toca_feriado_extremo(inicio, fin):
                st.error("Las vacaciones no pueden empezar o terminar pegadas a feriados.")
            else:
                nuevo = pd.DataFrame({
                    "Empleado": [nombre],
                    "Sector": [sector],
                    "Inicio": [inicio.strftime("%Y-%m-%d")],
                    "Fin": [fin.strftime("%Y-%m-%d")],
                    "Color": [color]
                })
                df = pd.concat([df, nuevo], ignore_index=True)
                guardar_datos(df)
                st.success("Vacaciones registradas correctamente.")


# ================================
# ELIMINAR VACACIONES
# ================================
st.subheader("🗑 Borrar vacaciones registradas")

if len(df) > 0:
    borrar = st.selectbox("Seleccionar registro", df.index.astype(str))
    if st.button("Eliminar"):
        df = df.drop(int(borrar))
        guardar_datos(df)
        st.success("Registro eliminado.")


# ================================
# CALENDARIO NAVEGABLE
# ================================
st.subheader("📆 Calendario gráfico")

if "mes" not in st.session_state:
    st.session_state.mes = datetime.date.today().month
if "anio" not in st.session_state:
    st.session_state.anio = datetime.date.today().year

c1, c2, c3 = st.columns([1, 2, 1])

with c1:
    if st.button("⬅ Mes anterior"):
        st.session_state.mes -= 1
        if st.session_state.mes == 0:
            st.session_state.mes = 12
            st.session_state.anio -= 1

with c3:
    if st.button("➡ Mes siguiente"):
        st.session_state.mes += 1
        if st.session_state.mes == 13:
            st.session_state.mes = 1
            st.session_state.anio += 1

img = generar_calendario(st.session_state.mes, st.session_state.anio, df)

st.image(img, use_column_width=True)

