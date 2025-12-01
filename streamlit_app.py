import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import random
import calendar

ARCHIVO = "vacaciones.csv"

SECTORES = [
    "LABORATORIO", "PRODUCCION", "COMERCIAL",
    "FACTURACION", "COMPRAS", "CONTABLE", "SOCIOS"
]

# -------------------------
# Cargar o crear archivo
# -------------------------
def cargar_base():
    try:
        df = pd.read_csv(ARCHIVO)
        if "Sector" not in df.columns:
            df["Sector"] = ""
        return df
    except:
        df = pd.DataFrame(columns=[
            "Nombre", "Sector", "Desde", "Hasta", "Días", "Color"
        ])
        df.to_csv(ARCHIVO, index=False)
        return df

df = cargar_base()

# -------------------------
# Comprobar superposición
# -------------------------
def hay_superposicion(df, inicio, fin, sector_empleado):
    if hasattr(inicio, "date"):
        inicio = inicio.date()
    if hasattr(fin, "date"):
        fin = fin.date()

    for _, row in df.iterrows():
        start = pd.to_datetime(row["Desde"]).date()
        end = pd.to_datetime(row["Hasta"]).date()
        sector_row = row.get("Sector", "")

        # Solo bloquear si es el mismo sector
        if sector_row.strip().upper() != sector_empleado.strip().upper():
            continue

        if (inicio <= end) and (fin >= start):
            return True, row["Nombre"]

    return False, None


# -------------------------
# Configuración
# -------------------------
st.set_page_config(page_title="Calendario de Vacaciones", layout="wide")
st.title("📅 Calendario de Vacaciones")

# -------------------------
# FORMULARIO REGISTRO
# -------------------------
st.sidebar.header("Registrar vacaciones")

nombre = st.sidebar.text_input("Nombre del empleado:")
sector = st.sidebar.selectbox("Sector del empleado:", SECTORES)
fecha_inicio = st.sidebar.date_input("Fecha de inicio:", value=date.today())

opcion = st.sidebar.radio("Duración:", ["1 semana (7 días)", "2 semanas (14 días)"])
dias = 7 if opcion.startswith("1") else 14

colores = ["lightblue", "lightgreen", "lightyellow", "lightpink", "lavender", "peachpuff"]
color = random.choice(colores)

# -------------------------
# Botón registrar
# -------------------------
if st.sidebar.button("Registrar vacaciones"):

    if nombre.strip() == "":
        st.sidebar.error("Ingresá un nombre.")
    else:
        fecha_fin = fecha_inicio + timedelta(days=dias - 1)
        superpuesto, quien = hay_superposicion(df, fecha_inicio, fecha_fin, sector)

        if superpuesto:
            st.sidebar.error(f"❌ Se superpone con {quien} (mismo sector).")
        else:
            nuevo = pd.DataFrame({
                "Nombre": [nombre],
                "Sector": [sector],
                "Desde": [fecha_inicio],
                "Hasta": [fecha_fin],
                "Días": [dias],
                "Color": [color],
            })

            df = pd.concat([df, nuevo], ignore_index=True)
            df.to_csv(ARCHIVO, index=False)
            st.sidebar.success("✔ Vacaciones registradas correctamente.")


# -------------------------
# ELIMINAR VACACIONES
# -------------------------
st.sidebar.header("Eliminar vacaciones")

if len(df) > 0:
    empleados = df["Nombre"].unique()
    empleado_borrar = st.sidebar.selectbox("Seleccioná un empleado:", empleados)

    if st.sidebar.button("🗑 Borrar vacaciones"):
        df = df[df["Nombre"] != empleado_borrar]
        df.to_csv(ARCHIVO, index=False)
        st.sidebar.success(f"✔ Vacaciones de {empleado_borrar} eliminadas.")
else:
    st.sidebar.info("No hay vacaciones registradas.")


# -------------------------
# TABLA COMPLETA
# -------------------------
st.subheader("📄 Tabla de vacaciones registradas")

if df.empty:
    st.info("Todavía no hay vacaciones registradas.")
else:
    st.dataframe(df)


# -------------------------
# CALENDARIO GRÁFICO
# -------------------------
st.subheader("📆 Calendario gráfico por mes")

# Seleccionar mes y año
col1, col2 = st.columns(2)
año = col1.number_input("Año:", min_value=2020, max_value=2050, value=date.today().year)
mes = col2.selectbox("Mes:", list(range(1, 13)), index=date.today().month - 1)

# Crear matriz calendario
cal = calendar.monthcalendar(año, mes)

# Expandir datos por día
df_dias = []

for _, row in df.iterrows():
    ini = pd.to_datetime(row["Desde"]).date()
    fin = pd.to_datetime(row["Hasta"]).date()

    actual = ini
    while actual <= fin:
        df_dias.append({
            "Fecha": actual,
            "Nombre": row["Nombre"],
            "Color": row["Color"]
        })
        actual += timedelta(days=1)

df_dias = pd.DataFrame(df_dias)

# Render calendario
st.write(f"### {calendar.month_name[mes]} {año}")

for semana in cal:
    cols = st.columns(7)
    for i, dia in enumerate(semana):
        if dia == 0:
            cols[i].markdown("<div style='height:70px'></div>", unsafe_allow_html=True)
            continue

        fecha_actual = date(año, mes, dia)

        ocupantes = df_dias[df_dias["Fecha"] == fecha_actual]

        if len(ocupantes) == 0:
            bg = "white"
            contenido = f"<b>{dia}</b><br><span style='color:gray'>Libre</span>"
        else:
            # Si hay varios empleados ese día, mostrar hasta 3 colores
            colors_html = "".join(
                [f"<div style='width:12px;height:12px;background:{c};display:inline-block;margin-right:3px'></div>"
                 for c in ocupantes['Color'].head(3)]
            )
            nombres = "<br>".join(ocupantes["Nombre"].unique())

            bg = "#f0f0f0"
            contenido = f"<b>{dia}</b><br>{colors_html}<br>{nombres}"

        cols[i].markdown(
            f"""
            <div style="
                border:1px solid #ccc;
                padding:6px;
                height:110px;
                background:{bg};
                border-radius:5px;
                text-align:center;
                font-size:13px;
            ">
                {contenido}
            </div>
            """,
            unsafe_allow_html=True
        )
