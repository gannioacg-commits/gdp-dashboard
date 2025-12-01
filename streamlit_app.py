# streamlit_app.py
import streamlit as st
import pandas as pd
import datetime
import calendar
import random
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# -------------------------
# Helpers: fuente segura
# -------------------------
def cargar_fuente(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

# -------------------------
# Feriados 2025 & 2026 (YYYY-MM-DD)
# -------------------------
FERIADOS = {
    # 2025
    "2025-01-01","2025-03-03","2025-03-04","2025-03-24","2025-04-18","2025-04-19",
    "2025-05-01","2025-05-25","2025-06-16","2025-06-20","2025-07-09","2025-08-18",
    "2025-10-13","2025-11-17","2025-12-08","2025-12-25",
    # 2026
    "2026-01-01","2026-02-16","2026-02-17","2026-03-24","2026-04-02","2026-04-03",
    "2026-05-01","2026-05-25","2026-06-17","2026-06-20","2026-07-09","2026-08-17",
    "2026-10-12","2026-11-23","2026-12-08","2026-12-25"
}
FERIADOS = {datetime.datetime.strptime(s, "%Y-%m-%d").date() for s in FERIADOS}

# -------------------------
# Config / sectores / colores
# -------------------------
SECTORES = ["LABORATORIO", "PRODUCCION", "COMERCIAL", "FACTURACION", "COMPRAS", "CONTABLE", "SOCIOS"]
PALETTE = ["#6EC6FF", "#81C784", "#FFF176", "#F48FB1", "#CE93D8", "#FFCC80", "#80CBC4", "#E6EE9C"]

# -------------------------
# Inicializar session_state
# -------------------------
if "vacaciones" not in st.session_state:
    # guardamos lista de dicts con claves: Nombre, Sector, Inicio (date), Fin (date), Color (hex)
    st.session_state.vacaciones = []

if "mes" not in st.session_state:
    hoy = datetime.date.today()
    st.session_state.mes = hoy.month
if "anio" not in st.session_state:
    st.session_state.anio = hoy.year

# -------------------------
# Utilitarios de validación
# -------------------------
def es_feriado(fecha: datetime.date) -> bool:
    return fecha in FERIADOS

def feriado_en_puntas(inicio: datetime.date, fin: datetime.date):
    """
    Prohíbe:
      - inicio sea feriado
      - fin sea feriado
      - inicio sea 1 día después de feriado (i.e. dia anterior inicio es feriado)
      - fin sea 1 día antes de feriado (i.e. dia siguiente fin es feriado)
    """
    if inicio in FERIADOS:
        return True, f"El día de inicio ({inicio}) es feriado."
    if fin in FERIADOS:
        return True, f"El día de fin ({fin}) es feriado."
    if (inicio - datetime.timedelta(days=1)) in FERIADOS:
        prev = (inicio - datetime.timedelta(days=1))
        return True, f"No podés iniciar el {inicio} porque el día anterior ({prev}) es feriado."
    if (fin + datetime.timedelta(days=1)) in FERIADOS:
        nxt = (fin + datetime.timedelta(days=1))
        return True, f"No podés finalizar el {fin} porque el día siguiente ({nxt}) es feriado."
    return False, ""

def hay_solapamiento(inicio: datetime.date, fin: datetime.date, sector: str):
    """
    Revisa solapamiento dentro del mismo sector.
    """
    for rec in st.session_state.vacaciones:
        if rec["Sector"].strip().upper() != sector.strip().upper():
            continue
        ri = rec["Inicio"]
        rf = rec["Fin"]
        # si las fechas almacenadas son strings, convertir
        if isinstance(ri, str):
            ri = datetime.datetime.strptime(ri, "%Y-%m-%d").date()
        if isinstance(rf, str):
            rf = datetime.datetime.strptime(rf, "%Y-%m-%d").date()
        # comprobar solapamiento
        if (inicio <= rf) and (fin >= ri):
            return True, rec["Nombre"]
    return False, None

# -------------------------
# UI Lateral - alta
# -------------------------
st.set_page_config(page_title="Calendario Vacaciones (integrado)", layout="wide")
st.title("📅 Calendario de Vacaciones — Integrado")

with st.sidebar:
    st.header("Registrar vacaciones")
    nombre = st.text_input("Nombre del empleado")
    sector = st.selectbox("Sector", SECTORES)
    fecha_inicio = st.date_input("Fecha de inicio", value=datetime.date.today())
    duracion = st.radio("Duración", ["1 semana (7 días)", "2 semanas (14 días)"])
    dias = 7 if duracion.startswith("1") else 14

    # Color sugerido por empleado (si ya existe, mantener mismo color)
    existing_colors = {v["Nombre"]: v["Color"] for v in st.session_state.vacaciones}
    color_default = existing_colors.get(nombre, random.choice(PALETTE))
    color = st.color_picker("Color (opcional)", value=color_default)

    if st.button("📥 Registrar"):
        inicio = fecha_inicio
        fin = inicio + datetime.timedelta(days=dias - 1)

        # Validaciones
        if not nombre.strip():
            st.error("Ingresá el nombre del empleado.")
        else:
            # feriados en puntas
            err, msg = feriado_en_puntas(inicio, fin)
            if err:
                st.error(msg)
            else:
                # solapamiento por sector
                sup, quien = hay_solapamiento(inicio, fin, sector)
                if sup:
                    st.error(f"Solapamiento con {quien} del mismo sector.")
                else:
                    # guardar (almacenamos fechas como ISO strings para facilidad)
                    rec = {
                        "Nombre": nombre.strip(),
                        "Sector": sector,
                        "Inicio": inicio.isoformat(),
                        "Fin": fin.isoformat(),
                        "Color": color
                    }
                    st.session_state.vacaciones.append(rec)
                    st.success(f"Vacaciones registradas: {nombre} ({inicio} → {fin})")

# -------------------------
# Acciones: eliminar / exportar
# -------------------------
st.subheader("🗂 Registros actuales")
if len(st.session_state.vacaciones) == 0:
    st.info("No hay vacaciones registradas.")
else:
    df_display = pd.DataFrame(st.session_state.vacaciones)
    # mostrar tabla
    with st.expander("Ver tabla completa"):
        # convertir fechas a ISO si no lo están
        df_display2 = df_display.copy()
        st.dataframe(df_display2)

    # eliminar selección por índice
    st.write("")
    st.markdown("### 🗑 Eliminar registro")
    options = [f"{i} — {r['Nombre']} ({r['Inicio']}) — {r['Sector']}" for i, r in enumerate(st.session_state.vacaciones)]
    sel = st.selectbox("Seleccioná registro para eliminar", options)
    if st.button("Eliminar selección"):
        idx = int(sel.split(" — ")[0])
        eliminado = st.session_state.vacaciones.pop(idx)
        st.success(f"Eliminado: {eliminado['Nombre']} ({eliminado['Inicio']})")

    # exportar CSV botón
    def df_to_csv_bytes(data):
        df = pd.DataFrame(data)
        return df.to_csv(index=False).encode("utf-8")

    bts = df_to_csv_bytes(st.session_state.vacaciones)
    st.download_button("📥 Descargar CSV", data=bts, file_name="vacaciones_export.csv", mime="text/csv")

# -------------------------
# Calendario navegable y render
# -------------------------
st.subheader("📆 Calendario gráfico (navegable)")

# controles mes/año y botones prev/next
col1, col2, col3, col4 = st.columns([1,2,1,1])
with col1:
    if st.button("⬅️ Mes anterior"):
        # decrementar mes
        st.session_state.mes -= 1
        if st.session_state.mes == 0:
            st.session_state.mes = 12
            st.session_state.anio -= 1
with col2:
    mes_sel = st.selectbox("Mes", list(range(1,13)), index=st.session_state.mes - 1, format_func=lambda x: calendar.month_name[x])
    anio_sel = st.number_input("Año", min_value=2024, max_value=2035, value=st.session_state.anio)
    # sincronizar sesiones
    st.session_state.mes = mes_sel
    st.session_state.anio = anio_sel
with col3:
    if st.button("Mes siguiente ➡️"):
        st.session_state.mes += 1
        if st.session_state.mes == 13:
            st.session_state.mes = 1
            st.session_state.anio += 1
with col4:
    vista = st.selectbox("Vista", ["Mensual", "Semanal"], index=0)

# preparar estructura de eventos por día
def construir_map_dias():
    mapa = {}  # key: date -> list of (nombre,color,sector)
    for rec in st.session_state.vacaciones:
        try:
            inicio = datetime.datetime.strptime(rec["Inicio"], "%Y-%m-%d").date()
            fin = datetime.datetime.strptime(rec["Fin"], "%Y-%m-%d").date()
        except:
            continue
        d = inicio
        while d <= fin:
            if d not in mapa:
                mapa[d] = []
            mapa[d].append((rec["Nombre"], rec["Color"], rec["Sector"]))
            d += datetime.timedelta(days=1)
    return mapa

mapa_dias = construir_map_dias()

# función para dibujar calendario (PIL image) — fondo rojo para feriados, colores para vacaciones
def dibujar_calendario(mes, anio, mapa):
    # tamaño y estilos
    ancho = 1100
    alto = 820
    left = 40
    top = 110
    cell_w = (ancho - left*2) // 7
    cell_h = 110

    img = Image.new("RGB", (ancho, alto), "white")
    draw = ImageDraw.Draw(img)

    font_t = cargar_fuente(36)
    font_header = cargar_fuente(20)
    font_num = cargar_fuente(18)
    font_name = cargar_fuente(14)

    # Título
    titulo = f"{calendar.month_name[mes]} {anio}"
    draw.text((ancho//2, 30), titulo, fill="black", anchor="mm", font=font_t)

    # Días de la semana
    dias_sem = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    for i, d in enumerate(dias_sem):
        x = left + i*cell_w + cell_w//2
        draw.text((x, 80), d, fill="black", anchor="mm", font=font_header)

    cal = calendar.monthcalendar(anio, mes)

    y = top
    for semana in cal:
        x = left
        for dia in semana:
            rect = [x, y, x+cell_w-6, y+cell_h-6]  # pequeño padding
            if dia == 0:
                # celda vacía
                draw.rectangle(rect, outline="#DDD", fill="#FFFFFF")
            else:
                fecha = datetime.date(anio, mes, dia)
                # feriado?
                if fecha in FERIADOS:
                    draw.rectangle(rect, fill="#FF6B6B", outline="#B22222")
                else:
                    draw.rectangle(rect, fill="#FFFFFF", outline="#DDD")

                # si hay vacaciones mostrar hasta 3 nombres (pequeñas barras)
                if fecha in mapa:
                    # si hay más de 3 ocupantes, tomar primeros 3
                    ocup = mapa[fecha][:3]
                    # dibujar pequeñas franjas en la parte inferior
                    stripe_h = 18
                    for idx, (nombre, color, sector) in enumerate(ocup):
                        bx1 = x + 6
                        by1 = y + 28 + idx*(stripe_h + 4)
                        bx2 = x + cell_w - 12
                        by2 = by1 + stripe_h
                        draw.rectangle([bx1, by1, bx2, by2], fill=color, outline="#444")
                        # nombre recortado
                        txt = nombre if len(nombre) <= 18 else nombre[:15] + "..."
                        draw.text((bx1 + 6, by1 + 2), txt, fill="black", font=font_name)

                # número del día arriba a la derecha
                draw.text((x+cell_w-14, y+6), str(dia), fill="black", anchor="rm", font=font_num)

            x += cell_w
        y += cell_h

    return img

# renderizar según vista
if vista == "Mensual":
    img = dibujar_calendario(st.session_state.mes, st.session_state.anio, mapa_dias)
    st.image(img, use_column_width=True)
else:
    # Vista Semanal: mostrar la semana donde hoy cae o semana seleccionada por usuario
    # Formular: pedir número de semana del mes (1..n)
    cal = calendar.monthcalendar(st.session_state.anio, st.session_state.mes)
    max_sem = len(cal)
    semana_sel = st.number_input("Semana del mes", min_value=1, max_value=max_sem, value=1)
    semana = cal[semana_sel-1]

    # construir imagen horizontal pequeña
    ancho = 1100
    alto = 320
    img = Image.new("RGB", (ancho, alto), "white")
    draw = ImageDraw.Draw(img)
    font_t = cargar_fuente(24)
    font_num = cargar_fuente(18)
    font_name = cargar_fuente(14)

    # encabezados por día
    for i, dia in enumerate(["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]):
        x = 40 + i*((ancho-80)//7)
        draw.text((x + ((ancho-80)//14), 20), dia, fill="black", font=font_t)

    # celdas
    for i, d in enumerate(semana):
        x = 40 + i*((ancho-80)//7)
        rect = [x, 70, x + ((ancho-80)//7) - 10, 270]
        if d == 0:
            draw.rectangle(rect, fill="#F5F5F5", outline="#DDD")
        else:
            fecha = datetime.date(st.session_state.anio, st.session_state.mes, d)
            if fecha in FERIADOS:
                draw.rectangle(rect, fill="#FF6B6B", outline="#B22222")
            else:
                draw.rectangle(rect, fill="#FFFFFF", outline="#DDD")
            # número día
            draw.text((x+8, 74), str(d), fill="black", font=font_num)
            if fecha in mapa_dias:
                occ = mapa_dias[fecha][:5]
                y_text = 100
                for (nombre, color, sector) in occ:
                    draw.rectangle([x+8, y_text, x + ((ancho-80)//7) - 18, y_text+18], fill=color, outline="#333")
                    txt = nombre if len(nombre) <= 22 else nombre[:19] + "..."
                    draw.text((x+12, y_text+2), txt, fill="black", font=font_name)
                    y_text += 22

    st.image(img, use_column_width=True)

# -------------------------
# Footer / ayuda
# -------------------------
st.markdown("---")
st.caption("Reglas: los feriados (fondo rojo) no pueden estar en las puntas de las vacaciones. "
           "Solapamiento permitido solo si es diferente sector. Los datos se guardan en la sesión de la app.")
