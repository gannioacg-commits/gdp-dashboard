import streamlit as st
import pandas as pd
import calendar
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# 🟥 FERIADOS ARGENTINA 2026
# ============================================================

feriados_2026 = [
    "2026-01-01", "2026-02-16", "2026-02-17", "2026-03-24",
    "2026-04-02", "2026-04-03", "2026-05-01", "2026-05-25",
    "2026-06-20", "2026-07-09", "2026-08-17",
    "2026-10-12", "2026-11-23", "2026-12-08", "2026-12-25"
]

# ============================================================
# 📌 INICIALIZACIÓN DE SESSION_STATE
# ============================================================

if "vacaciones" not in st.session_state:
    st.session_state.vacaciones = pd.DataFrame(columns=["fecha"])

if "anio" not in st.session_state:
    st.session_state.anio = 2026

if "mes" not in st.session_state:
    st.session_state.mes = 1


# ============================================================
# 📌 FUNCIÓN PARA GENERAR EL CALENDARIO (VERSIÓN PEQUEÑA)
# ============================================================

def generar_calendario(mes, anio, df_vacaciones, feriados):
    calendar.setfirstweekday(calendar.MONDAY)
    nombres_meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    nombres_dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    # Tamaño más pequeño
    cell_w = 90
    cell_h = 60
    header_h = 80
    width = cell_w * 7 + 40
    height = header_h + cell_h * 6 + 40

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_titulo = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
        font_dias = ImageFont.truetype("DejaVuSans.ttf", 20)
        font_nums = ImageFont.truetype("DejaVuSans.ttf", 24)
    except:
        font_titulo = ImageFont.load_default()
        font_dias = ImageFont.load_default()
        font_nums = ImageFont.load_default()

    # TÍTULO
    titulo = f"{nombres_meses[mes-1]} {anio}"
    tw, th = draw.textsize(titulo, font=font_titulo)
    draw.text(((width - tw) / 2, 10), titulo, fill="black", font=font_titulo)

    x_offset = 20
    y_offset = 60

    # Encabezado de días
    for i, dia in enumerate(nombres_dias):
        draw.text((x_offset + i * cell_w + 25, y_offset), dia, fill="black", font=font_dias)

    # Días del mes
    cal = calendar.monthcalendar(anio, mes)

    for fila, semana in enumerate(cal):
        for col, dia_num in enumerate(semana):
            if dia_num == 0:
                continue

            x = x_offset + col * cell_w
            y = y_offset + 40 + fila * cell_h

            fecha_str = f"{anio}-{mes:02}-{dia_num:02}"

            # Colores
            if fecha_str in feriados:
                color = (255, 120, 120)  # Feriado
            elif fecha_str in df_vacaciones["fecha"].values:
                color = (120, 200, 255)  # Vacaciones
            else:
                color = (235, 235, 235)  # Normal

            draw.rectangle([x, y, x + cell_w - 5, y + cell_h - 5], fill=color, outline="black")
            draw.text((x + 10, y + 10), str(dia_num), fill="black", font=font_nums)

    return img


# ============================================================
# 🧩 INTERFAZ STREAMLIT – APP DE VACACIONES
# ============================================================

st.title("📅 Selección de Vacaciones 2026")
st.write("Seleccioná tus días y visualizalos en el calendario con feriados resaltados en rojo.")

# ---------------------------- SIDEBAR ----------------------------
st.sidebar.header("📌 Selección")

# Año fijo en 2026
st.sidebar.write("Año: **2026**")

# Selección del mes
mes_elegido = st.sidebar.selectbox("Mes", list(range(1, 13)), index=0)
st.session_state.mes = mes_elegido

# Selección de fechas
fecha = st.sidebar.date_input("Elegí un día", value=None)

if st.sidebar.button("➕ Agregar día"):
    if fecha is not None:
        nueva_fila = pd.DataFrame({"fecha": [fecha.strftime("%Y-%m-%d")]})
        st.session_state.vacaciones = pd.concat([st.session_state.vacaciones, nueva_fila], ignore_index=True)
        st.success("Día agregado correctamente.")
    else:
        st.warning("Seleccioná una fecha antes de agregar.")

# Mostrar lista cargada
st.subheader("📘 Tus días seleccionados")
st.dataframe(st.session_state.vacaciones)

# Botón para limpiar
if st.button("🗑 Borrar todos los días"):
    st.session_state.vacaciones = pd.DataFrame(columns=["fecha"])
    st.warning("Se eliminaron todos los días seleccionados.")


# ---------------------------- CALENDARIO ----------------------------

st.subheader("🗓 Calendario del mes")

img = generar_calendario(
    st.session_state.mes,
    st.session_state.anio,
    st.session_state.vacaciones,
    feriados_2026
)

st.image(img, use_column_width=False)


# Leyenda
st.markdown("""
### 🔍 Leyenda
🟥 **Feriado**  
🟦 **Vacaciones solicitadas**  
⬜ **Día normal**
""")

