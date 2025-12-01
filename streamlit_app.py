import streamlit as st
import calendar
import datetime
import json
import os

# ======================
# Funciones de Guardado
# ======================

FILE_PATH = "vacaciones.json"

def cargar_registros():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as f:
            return json.load(f)
    return []

def guardar_registros(data):
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)

# ======================
# Generador del Calendario
# ======================

def generar_calendario(anio, mes):
    cal = calendar.Calendar()
    semanas = cal.monthdayscalendar(anio, mes)  # devuelve semanas completas
    return semanas

# ======================
# INTERFAZ STREAMLIT
# ======================

st.set_page_config(page_title="Vacaciones", page_icon="🌴", layout="centered")

st.title("🌴 Gestor de Vacaciones")
st.write("Seleccioná tus días y guardalos para compartir el registro.")

# Año y mes
hoy = datetime.date.today()
colA, colB = st.columns(2)

anio = colA.number_input("Año", min_value=2020, max_value=2100, value=hoy.year)
mes = colB.selectbox(
    "Mes",
    options=list(range(1, 13)),
    index=hoy.month - 1,
    format_func=lambda x: calendar.month_name[x].capitalize()
)

# Generar calendario
semanas = generar_calendario(anio, mes)

st.subheader(f"📅 Calendario de {calendar.month_name[mes].capitalize()} {anio}")

# ====== DISEÑO DEL CALENDARIO ======
dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
cols = st.columns(7)

for i, d in enumerate(dias_semana):
    cols[i].markdown(f"<div style='text-align:center;font-weight:bold;font-size:14px'>{d}</div>", unsafe_allow_html=True)

for semana in semanas:
    cols = st.columns(7)
    for i, dia in enumerate(semana):
        if dia == 0:
            cols[i].markdown("<div style='height:25px'></div>", unsafe_allow_html=True)
        else:
            cols[i].markdown(
                f"""
                <div style='
                    text-align:center;
                    padding:6px;
                    border-radius:6px;
                    border:1px solid #ddd;
                    font-size:13px;
                    width:38px;
                    margin:auto;
                '>{dia}</div>
                """,
                unsafe_allow_html=True
            )

# ======================
# Selección de días
# ======================

st.subheader("📝 Registrar día de Vacaciones")

col1, col2 = st.columns(2)
dia_seleccionado = col1.number_input("Día", min_value=1, max_value=31, value=hoy.day)
motivo = col2.text_input("Motivo / Comentario")

if st.button("➕ Guardar día"):
    registros = cargar_registros()

    nuevo = {
        "anio": anio,
        "mes": mes,
        "dia": int(dia_seleccionado),
        "motivo": motivo
    }

    registros.append(nuevo)
    guardar_registros(registros)
    st.success("Día guardado correctamente 🎉")

# ======================
# Mostrar registro guardado
# ======================

st.subheader("📚 Registro Guardado")

registros = cargar_registros()

if len(registros) == 0:
    st.info("No hay registros guardados todavía.")
else:
    for r in registros:
        st.markdown(f"""
        <div style='padding:10px;border:1px solid #ccc;border-radius:8px;margin-bottom:8px;'>
            <b>{r['dia']}/{r['mes']}/{r['anio']}</b><br>
            {r['motivo']}
        </div>
        """, unsafe_allow_html=True)

# ======================
# Opción de borrar todo
# ======================

if st.button("🗑️ Borrar todos los registros"):
    guardar_registros([])
    st.warning("Todos los registros fueron eliminados.")

