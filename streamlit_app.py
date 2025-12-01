import streamlit as st
import pandas as pd
import datetime
import calendar
from PIL import Image, ImageDraw, ImageFont

# ------------------------------
#  FUENTE SEGURA PARA STREAMLIT
# ------------------------------
def cargar_fuente(size):
    try:
        # DejaVuSans viene incluida con Pillow → NO falla en Streamlit Cloud
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

# ------------------------------
#  FERIADOS 2026 ARGENTINA
# ------------------------------
feriados_2026 = [
    "2026-01-01", "2026-02-16", "2026-02-17", "2026-03-24",
    "2026-04-02", "2026-04-03", "2026-05-01", "2026-05-25",
    "2026-06-20", "2026-07-09", "2026-08-17", "2026-10-12",
    "2026-11-16", "2026-12-08", "2026-12-25"
]
feriados_2026 = [datetime.datetime.strptime(f, "%Y-%m-%d").date() for f in feriados_2026]

# ------------------------------
#  FUNCIÓN PRINCIPAL DEL CALENDARIO
# ------------------------------
def generar_calendario(mes, anio, df_eventos):

    # Limpiar DataFrame → evitar KeyError
    df_eventos = df_eventos.rename(columns=lambda x: x.strip().title())

    if "Inicio" not in df_eventos.columns or "Fin" not in df_eventos.columns:
        st.error("❌ Error: el archivo debe tener columnas 'Inicio' y 'Fin'")
        return None

    # Crear base de imagen
    img = Image.new("RGB", (1200, 900), "white")
    draw = ImageDraw.Draw(img)

    font_titulo = cargar_fuente(40)
    font_dia = cargar_fuente(28)
    font_num = cargar_fuente(26)
    font_event = cargar_fuente(20)

    # Nombre del mes
    nombre_mes = calendar.month_name[mes].upper()
    draw.text((600, 40), f"{nombre_mes} {anio}", fill="black", anchor="mm", font=font_titulo)

    # Días de la semana
    dias = ["L", "M", "M", "J", "V", "S", "D"]
    x_offset = 100
    for i, d in enumerate(dias):
        draw.text((x_offset + i * 150, 120), d, fill="black", anchor="mm", font=font_dia)

    # Calcular matriz del mes
    cal = calendar.monthcalendar(anio, mes)

    # Recorrer las semanas/días
    y = 180
    for week in cal:
        x = 100
        for day in week:

            if day != 0:
                fecha_actual = datetime.date(anio, mes, day)

                # Chequear si es feriado
                es_feriado = fecha_actual in feriados_2026

                # Fondo de feriado
                if es_feriado:
                    draw.rectangle([x - 60, y - 20, x + 60, y + 40], fill=(255, 230, 230))

                # Número del día
                draw.text((x, y), str(day), fill="black", anchor="mm", font=font_num)

                # Eventos del día
                for _, row in df_eventos.iterrows():

                    try:
                        inicio = datetime.datetime.strptime(str(row["Inicio"]), "%Y-%m-%d").date()
                        fin = datetime.datetime.strptime(str(row["Fin"]), "%Y-%m-%d").date()
                    except:
                        continue  # Saltear si hay datos inválidos

                    if inicio <= fecha_actual <= fin:
                        texto = row.get("Nombre", "Vacación")
                        draw.text((x, y + 30), texto[:12], fill="blue", anchor="mm", font=font_event)

            x += 150
        y += 120

    return img

# ------------------------------
#  INTERFAZ STREAMLIT
# ------------------------------
st.title("📅 Calendario con Vacaciones + Feriados 2026")

# Inputs
mes = st.selectbox("Mes", list(range(1, 13)), index=datetime.date.today().month - 1)
anio = st.number_input("Año", min_value=2024, max_value=2030, value=2026, step=1)

archivo = st.file_uploader("Cargar archivo Excel con vacaciones", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
else:
    # DataFrame vacío como fallback
    df = pd.DataFrame(columns=["Nombre", "Inicio", "Fin"])

# Botón generar
if st.button("Generar Calendario"):
    img = generar_calendario(mes, anio, df)
    if img:
        st.image(img, caption="Calendario generado", use_column_width=True)
