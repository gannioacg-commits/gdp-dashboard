import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
import os

# -------------------------------------------
# 1. FUNCION PARA GENERAR CALENDARIO ORDENADO
# -------------------------------------------
def generar_calendario(anio, mes):
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(anio, mes)
    return weeks

# -------------------------------------------
# 2. FUNCION PARA CARGAR O CREAR REGISTRO
# -------------------------------------------
def cargar_registro():
    if os.path.exists("registro_vacaciones.csv"):
        return pd.read_csv("registro_vacaciones.csv")
    else:
        df = pd.DataFrame(columns=["Empleado", "Fecha", "Motivo"])
        df.to_csv("registro_vacaciones.csv", index=False)
        return df

# -------------------------------------------
# 3. FUNCION PARA GUARDAR REGISTRO
# -------------------------------------------
def guardar_registro(df):
    df.to_csv("registro_vacaciones.csv", index=False)

# -------------------------------------------
# INICIO DE LA APP
# -------------------------------------------
st.set_page_config(page_title="Gestor de Vacaciones", layout="centered")

st.title("🏖️ Gestor de Vacaciones")
st.subheader("Registro y visualización de vacaciones del personal")

st.divider()

# -------------------------------------------
# SECCIÓN: CALENDARIO
# -------------------------------------------
st.header("📅 Calendario")

col1, col2 = st.columns(2)
with col1:
    anio = st.number_input("Año", min_value=2020, max_value=2100, value=datetime.now().year)

with col2:
    mes = st.number_input("Mes", min_value=1, max_value=12, value=datetime.now().month)

weeks = generar_calendario(anio, mes)

# Mostrar calendario más estético
st.write(f"### {calendar.month_name[mes]} {anio}")

# Crear tabla del calendario
cal_df = pd.DataFrame(weeks, columns=["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"])

# Reemplazar ceros por vacío
cal_df = cal_df.replace(0, "")

# Mostrar centrado y más pequeño
st.table(cal_df.style.set_table_styles([
    {"selector": "th", "props": [("text-align", "center"), ("font-size", "16px")]},
    {"selector": "td", "props": [("text-align", "center"), ("font-size", "14px")]}
]))


st.divider()

# -------------------------------------------
# SECCIÓN: REGISTRO DE VACACIONES
# -------------------------------------------
st.header("✍️ Registrar Vacaciones")

df = cargar_registro()

empleado = st.text_input("Empleado")
fecha = st.date_input("Fecha de vacaciones")
motivo = st.text_input("Motivo (opcional)")

if st.button("Guardar registro"):
    if empleado.strip() == "":
        st.error("Debes ingresar un nombre.")
    else:
        nuevo = pd.DataFrame([[empleado, fecha, motivo]], 
                             columns=["Empleado", "Fecha", "Motivo"])
        df = pd.concat([df, nuevo], ignore_index=True)
        guardar_registro(df)
        st.success("Registro guardado correctamente.")

st.divider()

# -------------------------------------------
# SECCIÓN: VISUALIZAR REGISTRO
# -------------------------------------------
st.header("📂 Registros guardados")

if df.empty:
    st.info("No hay registros todavía.")
else:
    st.dataframe(df)

    # Botón de descarga
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar Registro",
        data=csv,
        file_name="registro_vacaciones.csv",
        mime="text/csv"
    )
