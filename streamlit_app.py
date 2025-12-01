
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import random
import calendar

ARCHIVO = "vacaciones.csv"

FERIADOS = {
    "2025-01-01","2025-02-03","2025-02-04","2025-03-04","2025-03-24",
    "2025-04-18","2025-05-01","2025-05-25","2025-06-20","2025-07-09",
    "2025-12-08","2025-12-25"
}

SECTORES = ["LABORATORIO", "PRODUCCION", "COMERCIAL", "FACTURACION", "COMPRAS", "CONTABLE", "SOCIOS"]

def cargar_base():
    try:
        return pd.read_csv(ARCHIVO)
    except:
        df = pd.DataFrame(columns=["Nombre", "Sector", "Desde", "Hasta", "Días", "Color"])
        df.to_csv(ARCHIVO, index=False)
        return df

df = cargar_base()

def hay_superposicion(df, inicio, fin, sector):
    for _, row in df.iterrows():
        if row["Sector"] != sector:
            continue
        start = pd.to_datetime(row["Desde"])
        end = pd.to_datetime(row["Hasta"])
        if (inicio <= end) and (fin >= start):
            return True, row["Nombre"]
    return False, None

def feriado_en_punta(inicio, fin):
    if str(inicio) in FERIADOS: 
        return "El día de inicio es feriado"
    if str(fin) in FERIADOS:
        return "El día de fin es feriado"
    return None

st.set_page_config(page_title="Calendario de Vacaciones", layout="wide")
st.title("📅 Calendario de Vacaciones – Empresa")

st.sidebar.header("Registrar vacaciones")

nombre = st.sidebar.text_input("Empleado:")
sector = st.sidebar.selectbox("Sector:", SECTORES)
fecha_inicio = st.sidebar.date_input("Inicio:", value=date.today())

opcion = st.sidebar.radio("Duración:", ["1 semana (7 días)", "2 semanas (14 días)"])
dias = 7 if opcion.startswith("1") else 14

colores = ["#6EC6FF", "#81C784", "#FFF176", "#F48FB1", "#CE93D8", "#FFCC80"]
color = random.choice(colores)

if st.sidebar.button("Registrar vacaciones"):
    if nombre.strip() == "":
        st.sidebar.error("Ingresar nombre.")
    else:
        fecha_fin = fecha_inicio + timedelta(days=dias - 1)

        msj = feriado_en_punta(fecha_inicio, fecha_fin)
        if msj:
            st.sidebar.error("❌ No permitido: " + msj)
        else:
            superpuesto, quien = hay_superposicion(df, fecha_inicio, fecha_fin, sector)
            if superpuesto:
                st.sidebar.error(f"❌ Se superpone con {quien}.")
            else:
                nuevo = pd.DataFrame({
                    "Nombre":[nombre], "Sector":[sector],
                    "Desde":[fecha_inicio], "Hasta":[fecha_fin],
                    "Días":[dias], "Color":[color]
                })
                df = pd.concat([df, nuevo], ignore_index=True)
                df.to_csv(ARCHIVO, index=False)
                st.sidebar.success("✔ Registrado correctamente")

st.subheader("🗂 Tabla de registros")
st.dataframe(df)

st.subheader("🗑 Eliminar vacaciones")
if not df.empty:
    empleado_borrar = st.selectbox("Seleccionar registro:", df["Nombre"] + " (" + df["Desde"] + ")")
    if st.button("Eliminar"):
        idx = df[df["Nombre"] + " (" + df["Desde"] + ")" == empleado_borrar].index
        df = df.drop(idx)
        df.to_csv(ARCHIVO, index=False)
        st.success("🗑 Registro eliminado.")

st.subheader("📆 Calendario estilo Google Calendar")

def mostrar_mes(m, a):
    cal = calendar.monthcalendar(a, m)
    st.markdown(f"### {calendar.month_name[m]} {a}")

    df_mes = pd.DataFrame(cal, columns=["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"])
    for col in df_mes.columns:
        df_mes[col] = df_mes[col].apply(lambda x: "" if x == 0 else x)

    eventos = {}
    for _, row in df.iterrows():
        inicio = pd.to_datetime(row["Desde"])
        fin = pd.to_datetime(row["Hasta"])
        for d in pd.date_range(inicio, fin):
            if d.month == m and d.year == a:
                eventos[d.day] = row["Color"]

    feriados_mes = {int(f.split("-")[2]) for f in FERIADOS if int(f.split("-")[1]) == m}

    st.write("")

    for semana in cal:
        cols = st.columns(7)
        dias = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
        for i, num in enumerate(semana):
            if num == 0:
                cols[i].markdown(" ")
            else:
                bg = "#FFFFFF"
                border = ""
                txt = f"<b>{num}</b>"
                if num in feriados_mes:
                    bg = "#FFD1D1"
                    border = "3px solid red"
                if num in eventos:
                    bg = eventos[num]
                    border = "2px solid black"
                cols[i].markdown(
                    f"<div style='background:{bg}; padding:10px; text-align:center; border-radius:6px; border:{border}'>{txt}</div>",
                    unsafe_allow_html=True
                )

hoy = date.today()
mostrar_mes(hoy.month, hoy.year)
