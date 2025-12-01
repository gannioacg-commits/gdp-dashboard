# app.py
import streamlit as st
import pandas as pd
import calendar
import datetime
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# -------------------------
# Helpers (fuente segura)
# -------------------------
def cargar_fuente(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

# -------------------------
# Feriados 2025 + 2026 (como date)
# -------------------------
FERIADOS_STR = {
    # 2025
    "2025-01-01","2025-03-03","2025-03-04","2025-03-24","2025-04-18","2025-04-19",
    "2025-05-01","2025-05-25","2025-06-16","2025-06-20","2025-07-09","2025-08-18",
    "2025-10-13","2025-11-17","2025-12-08","2025-12-25",
    # 2026
    "2026-01-01","2026-02-16","2026-02-17","2026-03-24","2026-04-02","2026-04-03",
    "2026-05-01","2026-05-25","2026-06-17","2026-06-20","2026-07-09","2026-08-17",
    "2026-10-12","2026-11-23","2026-12-08","2026-12-25"
}
FERIADOS = {datetime.datetime.strptime(s, "%Y-%m-%d").date() for s in FERIADOS_STR}

# -------------------------
# Configuración general
# -------------------------
SECTORES = ["LABORATORIO", "PRODUCCION", "COMERCIAL", "FACTURACION", "COMPRAS", "CONTABLE", "SOCIOS"]
PALETTE = ["#6EC6FF", "#81C784", "#FFF176", "#F48FB1", "#CE93D8", "#FFCC80", "#80CBC4", "#E6EE9C"]

st.set_page_config(page_title="App Vacaciones (con calendario reducido)", layout="wide")

# -------------------------
# session_state inicial
# -------------------------
if "vacaciones" not in st.session_state:
    # cada registro: dict con Nombre, Sector, Inicio (ISO), Fin (ISO), Color
    st.session_state.vacaciones = []

if "mes" not in st.session_state:
    hoy = datetime.date.today()
    st.session_state.mes = hoy.month
if "anio" not in st.session_state:
    st.session_state.anio = hoy.year

# -------------------------
# Utilidades validación
# -------------------------
def es_feriado(fecha: datetime.date) -> bool:
    return fecha in FERIADOS

def feriado_en_puntas(inicio: datetime.date, fin: datetime.date):
    # inicio o fin en feriado
    if inicio in FERIADOS:
        return True, f"El día de inicio ({inicio}) es feriado."
    if fin in FERIADOS:
        return True, f"El día final ({fin}) es feriado."
    # inicio justo después de feriado (dia anterior inicio es feriado)
    if (inicio - datetime.timedelta(days=1)) in FERIADOS:
        prev = (inicio - datetime.timedelta(days=1))
        return True, f"No podés iniciar el {inicio} porque el día anterior ({prev}) es feriado."
    # fin justo antes de feriado (dia siguiente fin es feriado)
    if (fin + datetime.timedelta(days=1)) in FERIADOS:
        nxt = (fin + datetime.timedelta(days=1))
        return True, f"No podés finalizar el {fin} porque el día siguiente ({nxt}) es feriado."
    return False, ""

def ajustar_inicio_fin_por_fin_de_semana(inicio: datetime.date, dias:int):
    """Si inicio cae en sab/dom, opcionalmente desplazar al lunes siguiente y ajustar fin."""
    inicio_new = inicio
    msg = ""
    if inicio.weekday() == 5:  # sábado
        inicio_new = inicio + datetime.timedelta(days=2)
        msg = f"El inicio caía en sábado; se desplazó al lunes {inicio_new}."
    elif inicio.weekday() == 6:  # domingo
        inicio_new = inicio + datetime.timedelta(days=1)
        msg = f"El inicio caía en domingo; se desplazó al lunes {inicio_new}."
    fin_new = inicio_new + datetime.timedelta(days=dias - 1)
    return inicio_new, fin_new, msg

def solapamiento_mismo_sector(inicio: datetime.date, fin: datetime.date, sector: str):
    """Revisa si hay solapamiento con registros del mismo sector."""
    for rec in st.session_state.vacaciones:
        if rec.get("Sector","").strip().upper() != sector.strip().upper():
            continue
        try:
            ri = datetime.datetime.strptime(rec["Inicio"], "%Y-%m-%d").date()
            rf = datetime.datetime.strptime(rec["Fin"], "%Y-%m-%d").date()
        except:
            continue
        if (inicio <= rf) and (fin >= ri):
            return True, rec["Nombre"]
    return False, None

# -------------------------
# Barra lateral: registro
# -------------------------
with st.sidebar:
    st.header("Registrar vacaciones")
    nombre = st.text_input("Nombre del empleado")
    sector = st.selectbox("Sector", SECTORES)
    fecha_inicio = st.date_input("Fecha de inicio", value=datetime.date.today())
    dur = st.radio("Duración", ["1 semana (7 días)", "2 semanas (14 días)"])
    dias = 7 if dur.startswith("1") else 14

    # color sugerido si ya existe
    existing_colors = {v["Nombre"]: v["Color"] for v in st.session_state.vacaciones}
    color_default = existing_colors.get(nombre, random.choice(PALETTE))
    color = st.color_picker("Color (opcional)", value=color_default)

    opt_guardar_local = st.checkbox("Guardar también localmente en CSV (opcional)", value=False)

    if st.button("Registrar vacaciones"):
        if not nombre.strip():
            st.error("Ingresá el nombre del empleado.")
        else:
            # Ajustar por fin de semana si corresponde (se desplaza al lunes)
            inicio_aj, fin_aj, msg_adj = ajustar_inicio_fin_por_fin_de_semana(fecha_inicio, dias)
            if msg_adj:
                st.info(msg_adj)

            # Validar feriados en puntas
            err, mensaje = feriado_en_puntas(inicio_aj, fin_aj)
            if err:
                st.error(mensaje)
            else:
                # Validar solapamiento en mismo sector
                sup, quien = solapamiento_mismo_sector(inicio_aj, fin_aj, sector)
                if sup:
                    st.error(f"Solapamiento con {quien} del mismo sector.")
                else:
                    # Guardar registro (fechas ISO)
                    rec = {
                        "Nombre": nombre.strip(),
                        "Sector": sector,
                        "Inicio": inicio_aj.isoformat(),
                        "Fin": fin_aj.isoformat(),
                        "Color": color
                    }
                    st.session_state.vacaciones.append(rec)
                    st.success(f"Vacaciones registradas: {nombre} ({inicio_aj} → {fin_aj})")
                    # guardar local opcional (simple CSV)
                    if opt_guardar_local:
                        try:
                            df_local = pd.DataFrame(st.session_state.vacaciones)
                            df_local.to_csv("vacaciones.csv", index=False)
                            st.info("Guardado local en vacaciones.csv")
                        except Exception as e:
                            st.warning("No se pudo guardar localmente: " + str(e))

# -------------------------
# Panel central: registros / acciones
# -------------------------
st.title("📅 App de Vacaciones — Calendario reducido")

st.subheader("Registros actuales")
if len(st.session_state.vacaciones) == 0:
    st.info("No hay vacaciones registradas.")
else:
    df_show = pd.DataFrame(st.session_state.vacaciones)
    # mostrar tabla con fechas legibles
    with st.expander("Ver tabla completa"):
        df_show_pretty = df_show.copy()
        # convertir a fechas para mostrar
        df_show_pretty["Inicio"] = pd.to_datetime(df_show_pretty["Inicio"]).dt.date
        df_show_pretty["Fin"] = pd.to_datetime(df_show_pretty["Fin"]).dt.date
        st.dataframe(df_show_pretty)

    # eliminar registro
    st.markdown("### 🗑 Eliminar registro")
    options = [f"{i} · {r['Nombre']} ({r['Inicio']}) - {r['Sector']}" for i, r in enumerate(st.session_state.vacaciones)]
    sel = st.selectbox("Seleccioná registro para eliminar", options) if options else None
    if sel and st.button("Eliminar seleccionado"):
        idx = int(sel.split(" · ")[0])
        eliminado = st.session_state.vacaciones.pop(idx)
        st.success(f"Eliminado: {eliminado['Nombre']} ({eliminado['Inicio']})")

    # exportar CSV memoria
    def export_csv_bytes(data):
        df = pd.DataFrame(data)
        return df.to_csv(index=False).encode("utf-8")
    csv_bytes = export_csv_bytes(st.session_state.vacaciones)
    st.download_button("📥 Descargar CSV (memoria)", data=csv_bytes, file_name="vacaciones_memoria.csv", mime="text/csv")

# -------------------------
# Construir mapa días -> eventos
# -------------------------
def construir_map_dias():
    mapa = {}
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

# -------------------------
# Calendario reducido (dibujo PIL)
# -------------------------
def generar_calendario_reducido(mes, anio, mapa_dias, feriados):
    # español
    nombres_meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    nombres_dias = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

    # dimensiones pequeñas
    cell_w = 90
    cell_h = 60
    header_h = 80
    width = cell_w * 7 + 40
    height = header_h + cell_h * 6 + 40

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # fuentes
    font_title = cargar_fuente(22)
    font_header = cargar_fuente(14)
    font_num = cargar_fuente(16)
    font_name = cargar_fuente(12)

    # título
    titulo = f"{nombres_meses[mes-1]} {anio}"
    draw.text(((width)//2 - 10, 12), titulo, fill="black", font=font_title)

    # headers dias
    x_offset = 20
    y_offset = 60
    for i, d in enumerate(nombres_dias):
        draw.text((x_offset + i*cell_w + 25, y_offset), d, fill="black", font=font_header)

    # mes matrix
    cal = calendar.monthcalendar(anio, mes)

    # pintar celdas
    for fila, semana in enumerate(cal):
        for col, dia in enumerate(semana):
            x = x_offset + col * cell_w
            y = y_offset + 40 + fila * cell_h
            rect = [x, y, x + cell_w - 5, y + cell_h - 5]

            if dia == 0:
                # celda vacía
                draw.rectangle(rect, fill="#FAFAFA", outline="#EFEFEF")
                continue

            fecha = datetime.date(anio, mes, dia)
            fecha_iso = fecha.isoformat()

            # feriado?
            if fecha in feriados:
                draw.rectangle(rect, fill="#FF6B6B", outline="#B22222")  # fondo rojo
            else:
                draw.rectangle(rect, fill="#FFFFFF", outline="#E6E6E6")

            # dibujar franjas de vacaciones (hasta 3)
            if fecha in mapa_dias:
                ocup = mapa_dias[fecha][:3]
                stripe_h = 14
                y0 = y + 28
                for idx, (nombre, color, sector) in enumerate(ocup):
                    bx1 = x + 8
                    by1 = y0 + idx * (stripe_h + 4)
                    bx2 = x + cell_w - 16
                    by2 = by1 + stripe_h
                    draw.rectangle([bx1, by1, bx2, by2], fill=color, outline="#444")
                    txt = nombre if len(nombre) <= 16 else nombre[:13] + "..."
                    draw.text((bx1 + 4, by1 + 1), txt, fill="black", font=font_name)

            # número del día (arriba derecha)
            draw.text((x + cell_w - 16, y + 6), str(dia), fill="black", font=font_num)

    return img

# -------------------------
# Mostrar calendario navegable reducido
# -------------------------
st.subheader("Calendario (reducido)")

col1, col2, col3 = st.columns([1,2,1])
with col1:
    if st.button("⬅ Mes anterior"):
        st.session_state.mes -= 1
        if st.session_state.mes == 0:
            st.session_state.mes = 12
            st.session_state.anio -= 1
with col2:
    mes_sel = st.selectbox("Mes", list(range(1,13)), index=st.session_state.mes - 1, format_func=lambda x: calendar.month_name[x])
    anio_sel = st.number_input("Año", min_value=2024, max_value=2035, value=st.session_state.anio)
    st.session_state.mes = mes_sel
    st.session_state.anio = anio_sel
with col3:
    if st.button("Mes siguiente ➡"):
        st.session_state.mes += 1
        if st.session_state.mes == 13:
            st.session_state.mes = 1
            st.session_state.anio += 1

# render
img = generar_calendario_reducido(st.session_state.mes, st.session_state.anio, mapa_dias, FERIADOS)
st.image(img, use_column_width=False)

st.markdown("""
**Leyenda:**  
- 🟥 Feriado (fondo rojo) — no puede ser punta de vacaciones.  
- 🟦 Franjas azules = empleados con vacaciones en ese día.  
""")

