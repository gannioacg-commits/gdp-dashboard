import streamlit as st
import pandas as pd
import calendar
import datetime
import os

# ===================================================================
#                CONFIG: ARCHIVO GLOBAL COMPARTIDO
# ===================================================================
ARCHIVO_GLOBAL = "vacaciones_global.csv"


# ===================================================================
#                    FUNCIONES DE PERSISTENCIA
# ===================================================================
def cargar_registros():
    """Carga el archivo CSV persistente, o lo crea si no existe."""
    if os.path.exists(ARCHIVO_GLOBAL):
        return pd.read_csv(ARCHIVO_GLOBAL)
    else:
        df = pd.DataFrame(columns=["fecha", "nombre", "motivo"])
        df.to_csv(ARCHIVO_GLOBAL, index=False)
        return df


def guardar_registros(df):
    """Guarda el CSV de manera permanente."""
    df.to_csv(ARCHIVO_GLOBAL, index=False)


# ===================================================================
#                 APLICACIÓN STREAMLIT PRINCIPAL
# ===================================================================

st.title("📅 Registro de Vacaciones — Persistencia Total")

# Cargar datos persistentes
registros = cargar_registros()

# =======================
# Selección de mes / año
# =======================
hoy = datetime.date.today()

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("⬅️ Mes anterior"):
        nuevo_mes = hoy.month - 1 or 12
        nuevo_anio = hoy.year - 1 if hoy.month == 1 else hoy.year
        hoy = hoy.replace(year=nuevo_anio, month=nuevo_mes)

with col3:
    if st.button("➡️ Mes siguiente"):
        nuevo_mes = hoy.month + 1 if hoy.month < 12 else 1
        nuevo_anio = hoy.year + 1 if hoy.month == 12 else hoy.year
        hoy = hoy.replace(year=nuevo_anio, month=nuevo_mes)

anio = st.sidebar.number_input("Año", 2020, 2100, hoy.year)
mes = st.sidebar.number_input("Mes", 1, 12, hoy.month)

cal = calendar.monthcalendar(anio, mes)

st.subheader(f"📆 {calendar.month_name[mes]} {anio}")

# =======================
# Mostrar calendario
# =======================
dias_semana = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]

for semana in cal:
    cols = st.columns(7)

    # Encabezado
    for i, d in enumerate(dias_semana):
        cols[i].markdown(f"**{d}**")

    cols = st.columns(7)

    # Días del calendario
    for i, dia in enumerate(semana):
        with cols[i]:
            if dia != 0:
                fecha_str = f"{anio}-{mes:02d}-{dia:02d}"
                st.markdown(f"### {dia}")

                # Filtrar registros del día
                dia_regs = registros[registros["fecha"] == fecha_str]

                # Mostrar registros con opción de eliminar
                for idx, row in dia_regs.iterrows():
                    st.markdown(
                        f"🟨 **{row['nombre']}** — {row['motivo']}"
                    )
                    if st.button("Eliminar", key=f"del_{idx}"):
                        registros = registros.drop(idx)
                        guardar_registros(registros)
                        st.rerun()
            else:
                st.write("")


# =======================
# Agregar un nuevo registro
# =======================
st.subheader("➕ Agregar registro de vacaciones")

colA, colB = st.columns(2)

with colA:
    nombre = st.text_input("Nombre")

with colB:
    motivo = st.text_input("Motivo")

fecha_sel = st.date_input("Fecha", hoy)

if st.button("Guardar registro"):
    nueva_fila = pd.DataFrame({
        "fecha": [fecha_sel.strftime("%Y-%m-%d")],
        "nombre": [nombre],
        "motivo": [motivo]
    })
    registros = pd.concat([registros, nueva_fila], ignore_index=True)
    guardar_registros(registros)
    st.success("Registro guardado permanentemente ✔️")
    st.rerun()

# =======================
# Ver registros completos
# =======================
st.divider()
st.subheader("📄 Todos los registros actuales")
st.dataframe(registros)

# =======================
# Eliminar todo
# =======================
if st.button("🗑️ Borrar TODOS los registros"):
    registros = pd.DataFrame(columns=["fecha", "nombre", "motivo"])
    guardar_registros(registros)
    st.warning("Todos los registros fueron eliminados permanentemente.")
    st.rerun()

