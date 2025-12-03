import streamlit as st
import pandas as pd
import calendar
import datetime
import os
from io import BytesIO

# ============================================================
#             CONFIG: ARCHIVO GLOBAL DE VACACIONES
# ============================================================
ARCHIVO_GLOBAL = "vacaciones_global.csv"
SONIDO_ERROR = "WhatsApp Ptt 2025-12-03 at 3.25.14 PM.ogg"

# ============================================================
#                CARGA O CREACIÓN DEL CSV
# ============================================================
def cargar_datos():
    if os.path.exists(ARCHIVO_GLOBAL):
        return pd.read_csv(ARCHIVO_GLOBAL)
    else:
        df = pd.DataFrame(columns=["nombre", "desde", "hasta"])
        df.to_csv(ARCHIVO_GLOBAL, index=False)
        return df

def guardar_datos(df):
    df.to_csv(ARCHIVO_GLOBAL, index=False)

# ============================================================
#                INTERFAZ PRINCIPAL DE STREAMLIT
# ============================================================
st.title("📅 Registro Permanente de Vacaciones")

df = cargar_datos()

st.subheader("➕ Cargar nuevas vacaciones")

nombre = st.text_input("Nombre del empleado")
desde = st.date_input("Desde")
hasta = st.date_input("Hasta")

# ============================================================
#          REGLA: NO PERMITIR VACACIONES NO VÁLIDAS
# ============================================================
def vacaciones_invalidas(nuevo_desde, nuevo_hasta):
    if nuevo_hasta < nuevo_desde:
        return True

    for _, row in df.iterrows():
        r_desde = datetime.datetime.strptime(row["desde"], "%Y-%m-%d").date()
        r_hasta = datetime.datetime.strptime(row["hasta"], "%Y-%m-%d").date()

        # Si se superponen fechas
        if (nuevo_desde <= r_hasta) and (nuevo_hasta >= r_desde):
            return True

    return False

# ============================================================
#                    BOTÓN DE CARGA
# ============================================================
if st.button("Guardar vacaciones"):
    if vacaciones_invalidas(desde, hasta):
        st.error("❌ Estas vacaciones NO pueden ser tomadas.")

        # 🔊 Reproducir sonido de error
        try:
            audio_bytes = open(SONIDO_ERROR, "rb").read()
            st.audio(audio_bytes, format="audio/ogg")
        except:
            st.warning("⚠️ No se encontró el archivo de sonido.")

    else:
        nuevo = pd.DataFrame({"nombre": [nombre], "desde": [str(desde)], "hasta": [str(hasta)]})
        df = pd.concat([df, nuevo], ignore_index=True)
        guardar_datos(df)
        st.success("✔️ Vacaciones cargadas correctamente.")

# ============================================================
#               MOSTRAR REGISTRO PERMANENTE
# ============================================================
st.subheader("📘 Registro histórico de vacaciones")
st.dataframe(df)

