import streamlit as st
import pandas as pd
import datetime
import calendar
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Calendario de Vacaciones", layout="wide")

# -------------------------------------------------------------------
# FERIADOS 2025 & 2026 - ARGENTINA
# -------------------------------------------------------------------
FERIADOS = {
    2025: [
        "2025-01-01", "2025-03-03", "2025-03-04", "2025-03-24", "2025-04-18",
        "2025-04-19", "2025-05-01", "2025-05-25", "2025-06-16", "2025-06-20",
        "2025-07-09", "2025-08-18", "2025-10-13", "2025-11-17", "2025-12-08",
        "2025-12-25"
    ],
    2026: [
        "2026-01-01", "2026-02-16", "2026-02-17", "2026-03-24", "2026-04-03",
        "2026-04-04", "2026-05-01", "2026-05-25", "2026-06-20", "2026-07-09",
        "2026-08-17", "2026-10-12", "2026-11-16", "2026-12-08", "2026-12-25"
    ]
}


def es_feriado(fecha: datetime.date):
    return fecha.strftime("%Y-%m-%d") in FERIADOS.get(fecha.year, [])


# -------------------------------------------------------------------
# MANEJO DE ARCHIVO
# -------------------------------------------------------------------
FILE = "vacaciones.csv"

def cargar_datos():
    try:
        return pd.read_csv(FILE)
    except:
        return pd.DataFrame(columns=["Empleado", "Sector", "Inicio", "Fin", "Color"])

def guardar_datos(df):
    df.to_csv(FILE, index=False)

df_vac = cargar_datos()


# -------------------------------------------------------------------
# VALIDACIONES
# -------------------------------------------------------------------
def validar_feriados_puntas(inicio, fin):
    """Los feriados NO pueden estar al inicio ni al final, solo dentro del rango."""
    if es_feriado(inicio):
        return False, "El primer día NO puede ser feriado."
    if es_feriado(fin):
        return False, "El último día NO puede ser feriado."
    return True, ""

def validar_solapamiento(inicio, fin, sector, df):
    df_sector = df[df["Sector"] == sector]
    for _, row in df_sector.iterrows():
        r_inicio = datetime.datetime.strptime(row["Inicio"], "%Y-%m-%d").date()
        r_fin = datetime.datetime.strptime(row["Fin"], "%Y-%m-%d").date()
        if not (fin < r_inicio or inicio > r_fin):
            return False, f"Solapamiento con {row['Empleado']} del mismo sector."
    return True, ""


# -------------------------------------------------------------------
# GENERADOR DE CALENDARIO GRAFICO CON NAVEGACIÓN
# -------------------------------------------------------------------
def generar_calendario(mes, anio, df):
    w, h = 900, 650
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    font_day = ImageFont.load_default()
    font_header = ImageFont.load_default()

    nombre_mes = calendar.month_name[mes].upper()
    draw.text((10, 10), f"{nombre_mes} {anio}", fill="black", font=font_header)

    # Días de la semana
    dias = ["L", "M", "M", "J", "V", "S", "D"]
    for i, d in enumerate(dias):
        draw.text((50 + i * 110, 50), d, fill="black", font=font_header)

    cal = calendar.monthcalendar(anio, mes)

    for fila, semana in enumerate(cal):
        for col, dia in enumerate(semana):
            x = 40 + col * 110
            y = 100 + fila * 80
            rect = [x, y, x + 100, y + 70]

            # Feriados en rojo
            if dia != 0:
                fecha = datetime.date(anio, mes, dia)
                if es_feriado(fecha):
                    draw.rectangle(rect, fill="#FFB3B3")

            # Vacaciones: colorear
            for _, row in df.iterrows():
                inicio = datetime.datetime.strptime(row["Inicio"], "%Y-%m-%d").date()
                fin = datetime.datetime.strptime(row["Fin"], "%Y-%m-%d").date()
                if dia != 0 and inicio <= fecha <= fin:
                    draw.rectangle(rect, fill=row["Color"])

            draw.rectangle(rect, outline="black")

            if dia != 0:
                draw.text((x + 5, y + 5), str(dia), fill="black", font=font_day)

    return img


# -------------------------------------------------------------------
# UI
# -------------------------------------------------------------------
st.title("📅 Calendario de Vacaciones – Multi Sector")

col1, col2 = st.columns(2)

with col1:
    empleado = st.text_input("Empleado")
    sector = st.selectbox("Sector", ["LABORATORIO", "PRODUCCION", "COMERCIAL", "FACTURACION", "COMPRAS", "CONTABLE", "SOCIOS"])
    color = st.color_picker("Color para marcar", "#A2D2FF")

with col2:
    modo = st.selectbox("Tipo de vacaciones", ["1 semana", "2 semanas"])
    inicio = st.date_input("Fecha de inicio")

if st.button("Registrar vacaciones"):
    if modo == "1 semana":
        fin = inicio + datetime.timedelta(days=6)
    else:
        fin = inicio + datetime.timedelta(days=13)

    ok, msg = validar_feriados_puntas(inicio, fin)
    if not ok:
        st.error(msg)
    else:
        ok2, msg2 = validar_solapamiento(inicio, fin, sector, df_vac)
        if not ok2:
            st.error(msg2)
        else:
            df_vac.loc[len(df_vac)] = [empleado, sector, str(inicio), str(fin), color]
            guardar_datos(df_vac)
            st.success("Vacaciones registradas.")


# ------ BORRAR REGISTROS ------
st.subheader("🗑 Borrar vacaciones")
if len(df_vac) > 0:
    borrar = st.selectbox("Seleccionar registro", df_vac.index)
    if st.button("Eliminar"):
        df_vac = df_vac.drop(borrar)
        guardar_datos(df_vac)
        st.success("Eliminado.")

# ------ CALENDARIO GRAFICO CON NAVEGACIÓN ------
st.subheader("📆 Calendario gráfico de vacaciones")

if "mes" not in st.session_state:
    hoy = datetime.date.today()
    st.session_state.mes = hoy.month
    st.session_state.anio = hoy.year

colA, colB, colC = st.columns([1,3,1])

with colA:
    if st.button("⬅ Mes anterior"):
        st.session_state.mes -= 1
        if st.session_state.mes == 0:
            st.session_state.mes = 12
            st.session_state.anio -= 1

with colC:
    if st.button("Mes siguiente ➡"):
        st.session_state.mes += 1
        if st.session_state.mes == 13:
            st.session_state.mes = 1
            st.session_state.anio += 1

img = generar_calendario(st.session_state.mes, st.session_state.anio, df_vac)
st.image(img, use_column_width=True)
