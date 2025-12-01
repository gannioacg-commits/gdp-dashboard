import streamlit as st
import pandas as pd
import datetime
import calendar
import os

st.set_page_config(page_title="Gestor de Vacaciones", layout="centered")

# ---------- FUNCIONES ----------

def cargar_datos():
    if os.path.exists("vacaciones.csv"):
        return pd.read_csv("vacaciones.csv")
    else:
        df = pd.DataFrame(columns=["Nombre", "Fecha Inicio", "Fecha Fin", "Días"])
        df.to_csv("vacaciones.csv", index=False)
        return df

def guardar_datos(df):
    df.to_csv("vacaciones.csv", index=False)

def generar_calendario(anio, mes):
    cal = calendar.Calendar(firstweekday=0)
    dias = cal.itermonthdays(anio, mes)

    semanas = []
    semana = []

    for d in dias:
        if d == 0:
            semana.append("")
        else:
            semana.append(str(d))
        if len(week) == 7:
            semanas.append(semana)
            semana = []
    if semana:
        semanas.append(semana)

    return semanas

# ---------- INTERFAZ PRINCIPAL ----------

st.title("📅 Gestor de Vacaciones")

st.subheader("Registrar Vacaciones")

df = cargar_datos()

col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre del empleado")
with col2:
    fecha_inicio = st.date_input("Fecha de inicio", datetime.date.today())

fecha_fin = st.date_input("Fecha de fin", datetime.date.today())
dias = (fecha_fin - fecha_inicio).days + 1

if st.button("Agregar Vacaciones"):
    if nombre.strip() == "":
        st.error("El nombre no puede estar vacío.")
    elif fecha_fin < fecha_inicio:
        st.error("La fecha fin no puede ser menor que inicio.")
    else:
        nuevo = pd.DataFrame([[nombre, fecha_inicio, fecha_fin, dias]],
                             columns=["Nombre", "Fecha Inicio", "Fecha Fin", "Días"])
        df = pd.concat([df, nuevo], ignore_index=True)
        guardar_datos(df)
        st.success("Vacaciones registradas correctamente.")

# ---------- MOSTRAR REGISTROS ----------
st.subheader("Registros guardados")
st.dataframe(df, use_container_width=True)

# ---------- CALENDARIO ----------

st.subheader("📆 Calendario del mes")

hoy = datetime.date.today()
mes = st.selectbox("Mes", list(range(1, 13)), index=hoy.month - 1)
anio = st.number_input("Año", min_value=1900, max_value=2100, value=hoy.year)

cal_data = generar_calendario(anio, mes)

st.markdown(
    """
    <style>
    .calendar {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
        max-width: 420px;  /* CALENDARIO MÁS CHICO */
        margin: auto;
        text-align: center;
    }
    .day-header {
        font-weight: bold;
        padding: 4px;
        background-color: #222;
        color: white;
        border-radius: 6px;
    }
    .day-cell {
        padding: 6px;
        background-color: #f1f1f1;
        border-radius: 6px;
        min-height: 35px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

st.markdown("<div class='calendar'>", unsafe_allow_html=True)

for d in dias_semana:
    st.markdown(f"<div class='day-header'>{d}</div>", unsafe_allow_html=True)

for semana in cal_data:
    for dia in semana:
        st.markdown(f"<div class='day-cell'>{dia}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
