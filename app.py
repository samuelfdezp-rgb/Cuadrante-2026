import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import base64
import requests
import os
import glob
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from openpyxl import load_workbook
import tempfile
import shutil

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
st.set_page_config(page_title="Cuadrante 2026", layout="wide")

ADMIN_USER = "ADMIN"
ADMIN_PASS = "PoliciaLocal2021!"

USERS_FILE = "usuarios.csv"
HISTORIAL_FILE = "historial_cambios.csv"
CUADRANTES_DIR = "cuadrantes"

ESCUDO_FILE = "Placa.png"
CABECERA_FILE = "cabecera.png"

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# ==================================================
# GITHUB (PERSISTENCIA)
# ==================================================
GITHUB_USER = "samuelfdezp-rgb"
GITHUB_REPO = "Cuadrante-2026"
GITHUB_BRANCH = "main"

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

# ==================================================
# FUNCIONES BASE
# ==================================================
def normalizar_nip(nip):
    return str(nip).strip().zfill(6)

def listar_cuadrantes():
    archivos = sorted(glob.glob(f"{CUADRANTES_DIR}/*.csv"))
    resultado = {}

    for f in archivos:
        nombre = os.path.basename(f).replace(".csv", "")
        try:
            anio, mes = nombre.split("_")
            mes = int(mes)
            resultado[f"{MESES[mes]} {anio}"] = f
        except:
            continue

    return resultado

def cargar_cuadrantes():
    archivos = glob.glob(f"{CUADRANTES_DIR}/*.csv")
    if not archivos:
        st.error("No hay cuadrantes disponibles")
        st.stop()

    dfs = []

    for ruta in archivos:
        df_tmp = pd.read_csv(
            ruta,
            parse_dates=["Fecha"]
        )

        df_tmp["nip"] = df_tmp["NIP"].apply(normalizar_nip)
        df_tmp["fecha"] = df_tmp["Fecha"]
        df_tmp["dia"] = df_tmp["fecha"].dt.day
        df_tmp["mes"] = df_tmp["Mes"]
        df_tmp["anio"] = df_tmp["Año"]

        df_tmp = df_tmp.rename(columns={
            "Nombre y Apellidos": "nombre",
            "Categoría": "categoria",
            "Turno": "turno"
        })

        dfs.append(df_tmp)

    return pd.concat(dfs, ignore_index=True)

def aplicar_historial(df, df_hist):
    if df_hist.empty:
        return df

    df_hist = df_hist.sort_values("fecha_hora")

    for _, r in df_hist.iterrows():
        nip = normalizar_nip(r["nip_afectado"])
        fecha = pd.Timestamp(r["fecha_turno"])

        mask = (df["nip"] == nip) & (df["fecha"] == fecha)

        if mask.any():
            df.loc[mask, "turno"] = r["turno_nuevo"]
        else:
            df.loc[len(df)] = {
                "anio": fecha.year,
                "mes": fecha.month,
                "fecha": fecha,
                "dia": fecha.day,
                "nip": nip,
                "nombre": r.get("nombre_afectado", ""),
                "categoria": "",
                "turno": r["turno_nuevo"],
            }

    return df

def guardar_csv_en_github(df, ruta_repo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{ruta_repo}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    csv_content = df.to_csv(index=False)
    content_b64 = base64.b64encode(csv_content.encode()).decode()

    # Comprobar si existe
    r = requests.get(url, headers=headers)

    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]
    elif r.status_code not in (200, 404):
        st.error(f"❌ Error consultando GitHub: {r.status_code} - {r.text}")
        st.stop()

    payload = {
        "message": f"Actualiza {ruta_repo}",
        "content": content_b64,
        "branch": GITHUB_BRANCH
    }

    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=headers, json=payload)

    if r.status_code not in (200, 201):
        st.error("❌ Error guardando en GitHub")
        st.code(r.text)   # 🔥 AHORA VERÁS EL ERROR REAL
        st.stop()

def cargar_historial_desde_github():
    """
    Descarga historial_cambios.csv desde GitHub y lo devuelve como DataFrame.
    Si no existe todavía, devuelve DataFrame vacío.
    """
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{HISTORIAL_FILE}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        content_b64 = r.json()["content"]
        csv_content = base64.b64decode(content_b64).decode()
        from io import StringIO
        return pd.read_csv(
            StringIO(csv_content),
            parse_dates=["fecha_turno", "fecha_hora"]
        )

    # No existe todavía
    return pd.DataFrame(columns=[
        "fecha_hora", "usuario_admin", "nip_afectado",
        "nombre_afectado", "fecha_turno",
        "turno_anterior", "turno_nuevo", "observaciones"
    ])

def exportar_excel(df_mes, mes_sel):
    columnas = [
        "nombre", "categoria", "nip",
        "fecha", "dia", "turno"
    ]

    df_excel = (
        df_mes[columnas]
        .sort_values(["nombre", "fecha"])
        .copy()
    )

    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_excel.to_excel(
            writer,
            index=False,
            sheet_name=f"{MESES[mes_sel]} 2026"
        )

        workbook = writer.book
        worksheet = writer.sheets[f"{MESES[mes_sel]} 2026"]

        worksheet.set_column("A:A", 28)
        worksheet.set_column("B:B", 15)
        worksheet.set_column("C:C", 10)
        worksheet.set_column("D:D", 12)
        worksheet.set_column("E:E", 6)
        worksheet.set_column("F:F", 12)

        header = workbook.add_format({
            "bold": True,
            "align": "center",
            "border": 1
        })

        for col, name in enumerate(df_excel.columns):
            worksheet.write(0, col, name.upper(), header)

    output.seek(0)
    return output

from datetime import date

def es_festivo_pdf(fecha):
    festivos = {
        date(2026, 1, 1),
        date(2026, 1, 6),
        date(2026, 2, 17),
        date(2026, 3, 19),
    }
    return fecha in festivos

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from io import BytesIO
from datetime import date
import calendar
import os

def exportar_pdf_cuadrante(df_mes, mes_sel, mes_label):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=15,
        rightMargin=15,
        topMargin=15,
        bottomMargin=15
    )

    styles = getSampleStyleSheet()
    elementos = []

    # ==================================================
    # CABECERA (IMAGEN)
    # ==================================================
    if os.path.exists("cabecera.png"):
        elementos.append(Image("cabecera.png", width=760, height=80))
        elementos.append(Spacer(1, 10))

    # ==================================================
    # TÍTULO CENTRADO (COMO EL ORIGINAL)
    # ==================================================
    titulo_style = ParagraphStyle(
        "Titulo",
        parent=styles["Heading2"],
        alignment=TA_CENTER
    )

    elementos.append(
        Paragraph(
            f"<b>CUADRANTE DE SERVICIO PARA EL MES DE {mes_label.upper()}</b>",
            titulo_style
        )
    )
    elementos.append(Spacer(1, 12))

    # ==================================================
    # DÍAS DEL MES
    # ==================================================
    num_dias = calendar.monthrange(2026, mes_sel)[1]

    # ==================================================
    # CABECERA TABLA
    # ==================================================
    cabecera = ["Nombre y Apellidos", "Categoría", "N.I.P."]
    cabecera += [f"{d:02d}" for d in range(1, num_dias + 1)]
    data = [cabecera]

    # ==================================================
    # ORDEN EXACTO DE LA APP
    # ==================================================
    orden = df_mes[["nombre", "categoria", "nip"]].drop_duplicates()

    for _, ag in orden.iterrows():
        fila = [ag["nombre"], ag["categoria"], ag["nip"]]
        df_ag = df_mes[df_mes["nip"] == ag["nip"]]

        for d in range(1, num_dias + 1):
            turno = df_ag[df_ag["dia"] == d]["turno"]
            fila.append(turno.iloc[0] if not turno.empty else "")

        data.append(fila)

    # ==================================================
    # TABLA
    # ==================================================
    tabla = Table(data, repeatRows=1)
    estilo = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ])

    # ==================================================
    # ESTILOS DE DÍAS Y TURNOS (CLON DEL PDF ORIGINAL)
    # ==================================================
    for col_idx in range(3, 3 + num_dias):
        dia = col_idx - 2
        fecha = date(2026, mes_sel, dia)

        # ---- CABECERA
        if es_festivo_pdf(fecha):
            estilo.add("BACKGROUND", (col_idx, 0), (col_idx, 0), colors.HexColor("#92D050"))
            estilo.add("TEXTCOLOR", (col_idx, 0), (col_idx, 0), colors.red)
            estilo.add("FONTNAME", (col_idx, 0), (col_idx, 0), "Helvetica-Bold")
        elif fecha.weekday() == 6:
            estilo.add("TEXTCOLOR", (col_idx, 0), (col_idx, 0), colors.red)
            estilo.add("FONTNAME", (col_idx, 0), (col_idx, 0), "Helvetica-Bold")

        # ---- CELDAS DE TURNOS
        for fila_idx in range(1, len(data)):
            turno = data[fila_idx][col_idx]
            if not turno:
                continue

            e = estilo_turno(turno)

            estilo.add("BACKGROUND", (col_idx, fila_idx), (col_idx, fila_idx), colors.HexColor(e["bg"]))
            estilo.add("TEXTCOLOR", (col_idx, fila_idx), (col_idx, fila_idx), colors.HexColor(e["fg"]))

            if e.get("bold"):
                estilo.add("FONTNAME", (col_idx, fila_idx), (col_idx, fila_idx), "Helvetica-Bold")

            # Festivo pisa todo
            if es_festivo_pdf(fecha):
                estilo.add("BACKGROUND", (col_idx, fila_idx), (col_idx, fila_idx), colors.HexColor("#92D050"))
                estilo.add("TEXTCOLOR", (col_idx, fila_idx), (col_idx, fila_idx), colors.red)

            # Domingo: solo texto rojo
            elif fecha.weekday() == 6:
                estilo.add("TEXTCOLOR", (col_idx, fila_idx), (col_idx, fila_idx), colors.red)

    # ==================================================
    # ANCHOS
    # ==================================================
    tabla._argW = [130, 60, 50] + [18] * num_dias
    tabla.setStyle(estilo)

    elementos.append(tabla)
    doc.build(elementos)

    buffer.seek(0)
    return buffer

# ==================================================
# SESIÓN
# ==================================================
if "nip" not in st.session_state:
    st.session_state.nip = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ==================================================
# LOGIN
# ==================================================
if st.session_state.nip is None:
    with open(ESCUDO_FILE, "rb") as f:
        escudo = base64.b64encode(f.read()).decode()

    st.markdown(
        f"<div style='display:flex;justify-content:center'><img src='data:image/png;base64,{escudo}' width='220'></div>",
        unsafe_allow_html=True
    )

    st.markdown("<h2 style='text-align:center'>🔐 Acceso al cuadrante</h2>", unsafe_allow_html=True)

    usuario = st.text_input("Usuario (NIP)")
    password = st.text_input("Contraseña (DNI)", type="password")

    usuarios = pd.read_csv(USERS_FILE)
    usuarios["nip"] = usuarios["nip"].apply(normalizar_nip)

    if st.button("Entrar"):
        if usuario == ADMIN_USER and password == ADMIN_PASS:
            st.session_state.nip = ADMIN_USER
            st.session_state.is_admin = True
            st.rerun()

        nip = normalizar_nip(usuario)
        fila = usuarios[usuarios["nip"] == nip]

        if not fila.empty and fila.iloc[0]["dni"] == password:
            st.session_state.nip = nip
            st.session_state.is_admin = False
            st.rerun()

        st.error("Usuario o contraseña incorrectos")

    st.stop()

# ==================================================
# CABECERA
# ==================================================
with open(CABECERA_FILE, "rb") as f:
    cabecera = base64.b64encode(f.read()).decode()

st.markdown(
    f"<img src='data:image/png;base64,{cabecera}' style='width:100%;margin-bottom:10px'>",
    unsafe_allow_html=True
)

st.title("📅 Cuadrante 2026")

if st.button("🚪 Cerrar sesión"):
    st.session_state.nip = None
    st.session_state.is_admin = False
    st.rerun()

# ==================================================
# CARGA DE CUADRANTES
# ==================================================
cuadrantes = listar_cuadrantes()
if not cuadrantes:
    st.error("No hay cuadrantes disponibles")
    st.stop()

mes_label = st.selectbox("📅 Selecciona mes", list(cuadrantes.keys()))
df = cargar_cuadrantes()

df_hist = cargar_historial_desde_github()
df = aplicar_historial(df, df_hist)


anio_sel, mes_sel = mes_label.split()
mes_sel = list(MESES.keys())[list(MESES.values()).index(anio_sel)]
df_mes = df[df["mes"] == mes_sel]

st.success(f"Mostrando cuadrante de {mes_label}")

# ==================================================
# FESTIVOS
# ==================================================
festivos = {date(2026, 1, 1), date(2026, 1, 6), date(2026, 2, 17), date(2026, 3, 19)}

def es_festivo(fecha):
    return fecha in festivos

# ==================================================
# NOMBRES DE TURNOS
# ==================================================
NOMBRES_TURNO = {
    "1": "Mañana", "2": "Tarde", "3": "Noche", "L": "Laborable",
    "1ex": "Mañana extra", "2ex": "Tarde extra", "3ex": "Noche extra",
    "D": "Descanso", "Dc": "Descanso compensado",
    "Dcv": "Desc. comp. verano", "Dcc": "Desc. comp. curso",
    "Dct": "Desc. comp. tiro", "Dcj": "Desc. comp. juicio",
    "Vac": "Vacaciones", "perm": "Permiso", "BAJA": "Baja",
    "Ts": "Tiempo sindical", "AP": "Asuntos particulares",
    "JuB": "Juicio Betanzos", "JuC": "Juicio Coruña",
    "Curso": "Curso", "indisp": "Indisposición",
}

def nombre_turno(c):
    return NOMBRES_TURNO.get(c, c)

# ==================================================
# ESTILOS DE TURNOS
# ==================================================
def estilo_turno(t):
    if pd.isna(t):
        return {"bg": "#FFFFFF", "fg": "#000000", "bold": False, "italic": False}

    t = str(t)

    base = {
        "1": ("#BDD7EE", "#0070C0"),
        "L": ("#BDD7EE", "#0070C0"),
        "2": ("#FFE699", "#0070C0"),
        "3": ("#F8CBAD", "#FF0000"),
        "1ex": ("#00B050", "#FF0000"),
        "2ex": ("#00B050", "#FF0000"),
        "3ex": ("#00B050", "#FF0000"),
        "D": ("#C6E0B4", "#00B050"),
        "Dc": ("#C6E0B4", "#00B050"),
        "Dcv": ("#C6E0B4", "#00B050"),
        "Dcc": ("#C6E0B4", "#00B050"),
        "Dct": ("#C6E0B4", "#00B050"),
        "Dcj": ("#C6E0B4", "#00B050"),
        "Vac": ("#FFFFFF", "#FF0000"),
        "perm": ("#FFFFFF", "#FF0000"),
        "indisp": ("#FFFFFF", "#FF0000"),
        "curso": ("#FFFFFF", "#FF0000"),
        "BAJA": ("#FFFFFF", "#FF0000"),
        "Ts": ("#FFFFFF", "#FF0000"),
        "JuB": ("#FFFFFF", "#FF0000"),
        "JuC": ("#FFFFFF", "#FF0000"),
        "1yJuB": ("#BDD7EE", "#FF0000"),
        "3yJuC": ("#BDD7EE", "#FF0000"),
        "AP": ("#FFFFFF", "#0070C0"),
        "1y2ex": ("#00B050", "#FF0000"),
        "2y3ex": ("#00B050", "#FF0000"),
        "1y3ex": ("#00B050", "#FF0000"),
        "1|2ex": ("#00B050", "#FF0000"),
        "1|3ex": ("#00B050", "#FF0000"),
        "2|1ex": ("#00B050", "#FF0000"),
        "2|3ex": ("#00B050", "#FF0000"),
        "3|1ex": ("#00B050", "#FF0000"),
        "3|2ex": ("#00B050", "#FF0000"),
        "AP|1ex": ("#00B050", "#FF0000"),
        "AP|2ex": ("#00B050", "#FF0000"),
        "AP|3ex": ("#00B050", "#FF0000"),
    }

    # Turnos dobles normales
    if t in {"1y2", "1y3", "2y3", "3yJuC", "1yJuB"}:
        return {"bg": "#DBDBDB", "fg": "#FF0000", "bold": True, "italic": False}

    # Turnos dobles con extra
    if "ex" in t and ("y" in t or "|" in t):
        return {"bg": "#00B050", "fg": "#FF0000", "bold": True, "italic": False}

    bg, fg = base.get(t, ("#FFFFFF", "#000000"))

    # ---- NEGRITA
    bold = (
        t in {"perm", "Ts", "JuB", "JuC", "AP", "Ts", "Vac", "BAJA", "indisp", "curso", "1yJuB", "3yJuC"} or
        "ex" in t or               # cualquier extra
        t in {"1y2", "1y3", "2y3"}
    )

    # ---- CURSIVA
    italic = t in {"Vac", "BAJA"}

    return {
        "bg": bg,
        "fg": fg,
        "bold": bold,
        "italic": italic
    }

# ==================================================
# PESTAÑAS
# ==================================================
if st.session_state.is_admin:
    tab_general, tab_mis_turnos, tab_historial = st.tabs(
        ["📋 Cuadrante general", "📆 Mis turnos", "📜 Historial"]
    )
else:
    tab_general, tab_mis_turnos = st.tabs(
        ["📋 Cuadrante general", "📆 Mis turnos"]
    )

# ==================================================
# TAB 1 — CUADRANTE GENERAL (MODO MÓVIL + ZOOM)
# ==================================================
with tab_general:
    st.subheader("📋 Cuadrante general")

    modo_movil = st.checkbox("📱 Modo móvil")

    zoom = 1.0
    if modo_movil:
        zoom = st.slider("🔍 Zoom", 0.3, 1.5, 0.5, 0.05)

    # ---------- CUADRANTE ----------
    if modo_movil:
        index_cols = ["nip"]
        orden = df_mes["nip"].drop_duplicates()
    else:
        index_cols = ["nombre", "categoria", "nip"]
        orden = df_mes[index_cols].drop_duplicates()

    tabla = (
        df_mes
        .pivot_table(
            index=index_cols,
            columns="dia",
            values="turno",
            aggfunc="first"
        )
        .reindex(orden)
    )

    nip_usuario = st.session_state.nip

    hoy = date.today()
    es_hoy_mes = (hoy.year == 2026 and hoy.month == mes_sel)
    dia_hoy = hoy.day if es_hoy_mes else None

    # ---------- HTML + CSS ----------
    html = f"""
    <style>
        .wrapper {{
            transform: scale({zoom});
            transform-origin: top left;
            width: fit-content;
        }}

        table {{
            border-collapse: collapse;
            font-size: 16px;
        }}

        th, td {{
            border: 1px solid #000;
            padding: 6px;
            text-align: center;
            white-space: nowrap;
        }}

        td {{
            font-weight: 600;
        }}

        /* CABECERA FIJA */
        thead th {{
            position: sticky;
            top: 0;
            z-index: 10;
            background: #111;
            color: white;
        }}

        /* SOLO CELDA DEL DÍA ACTUAL */
        .th-hoy {{
            background: #00B0F0 !important;
            color: #000 !important;
            font-weight: bold;
        }}

        /* FILA USUARIO */
        tr.usuario td {{
            border-top: 3px solid #000 !important;
            border-bottom: 3px solid #000 !important;
        }}

        tr.usuario td:first-child {{
            border-left: 3px solid #000 !important;
        }}

        tr.usuario td:last-child {{
            border-right: 3px solid #000 !important;
        }}
    </style>

    <div style="overflow:auto; max-height:75vh">
      <div class="wrapper">
        <table>
          <thead>
            <tr>
    """

    if modo_movil:
        html += "<th>NIP</th>"
    else:
        html += "<th>Nombre y apellidos</th><th>Categoría</th><th>NIP</th>"

    for d in tabla.columns:
        fecha = date(2026, mes_sel, d)
        clase_hoy = "th-hoy" if dia_hoy == d else ""

        if es_festivo(fecha) or fecha.weekday() == 6:
            html += f"<th class='{clase_hoy}' style='background:#92D050;color:#FF0000'>{d}</th>"
        else:
            html += f"<th class='{clase_hoy}'>{d}</th>"

    html += """
            </tr>
          </thead>
          <tbody>
    """

    # ---------- FILAS DEL CUADRANTE ----------
    for idx, fila in tabla.iterrows():

        nip_fila = str(idx) if modo_movil else idx[2]
        clase_usuario = "usuario" if nip_fila == nip_usuario else ""

        html += f"<tr class='{clase_usuario}'>"

        if modo_movil:
            html += f"<td>{nip_fila}</td>"
        else:
            nombre, cat, nip = idx
            html += f"<td>{nombre}</td><td>{cat}</td><td>{nip}</td>"

        for v in fila:
            e = estilo_turno(v)
            txt = "" if pd.isna(v) else v

            html += (
                f"<td style='background:{e['bg']};"
                f"color:{e['fg']};"
                f"font-weight:{'bold' if e.get('bold') else 'normal'};"
                f"font-style:{'italic' if e.get('italic') else 'normal'}'>"
                f"{txt}</td>"
            )

        html += "</tr>"

    # ---------- CONTEO 1 / 2 / 3 ----------
    def contar_123(codigo):
        if pd.isna(codigo):
            return set()

        c = str(codigo)
        NO_CUENTAN = ["D","Vac","BAJA","perm","Ts","Dc","Dct","Dcc","Dcv","Curso","indisp"]
        if any(x in c for x in NO_CUENTAN):
            return set()

        res = set()
        if "1" in c: res.add("1")
        if "2" in c: res.add("2")
        if "3" in c: res.add("3")
        return res

    conteo_1, conteo_2, conteo_3 = [], [], []

    for dia in tabla.columns:
        c1 = c2 = c3 = 0
        for _, fila in tabla.iterrows():
            t = contar_123(fila[dia])
            c1 += "1" in t
            c2 += "2" in t
            c3 += "3" in t

        conteo_1.append(c1)
        conteo_2.append(c2)
        conteo_3.append(c3)

    def fila_resumen(titulo, datos, color):
        fila = "<tr>"
        fila += f"<td colspan='{'1' if modo_movil else '3'}' style='background:{color};color:#000;font-weight:bold'>{titulo}</td>"
        for v in datos:
            fila += f"<td style='background:{color};color:#000;font-weight:bold'>{v}</td>"
        return fila + "</tr>"

    html += fila_resumen("Mañanas", conteo_1, "#BDD7EE")
    html += fila_resumen("Tardes", conteo_2, "#FFE699")
    html += fila_resumen("Noches", conteo_3, "#F8CBAD")

    html += """
          </tbody>
        </table>
      </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

st.markdown("### 📤 Exportar cuadrante")

if st.session_state.is_admin:
    st.info("ℹ️ El ADMIN exporta en Excel (PDF reservado para usuarios)")
else:
    pdf_file = exportar_pdf_cuadrante(df_mes, mes_sel, mes_label)

    st.download_button(
        label="⬇️ Descargar cuadrante en PDF",
        data=pdf_file,
        file_name=f"Cuadrante_{mes_label.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

# ==================================================
# TAB 2 — MIS TURNOS
# ==================================================
with tab_mis_turnos:
    st.subheader("📆 Mis turnos")

    df_user = df_mes[df_mes["nip"] == st.session_state.nip]
    cal = calendar.Calendar()

    # -------------------------------
    # FUNCIONES AUXILIARES
    # -------------------------------
    def separar(turno):
        if pd.isna(turno):
            return []
        if "y" in turno:
            return turno.split("y")
        if "|" in turno:
            return turno.split("|")
        return [turno]

    def formatear_nombre(nombre):
        partes = nombre.split()
        if partes[0] in {"Iago", "Javier"} and len(partes) > 1:
            return f"{partes[0]} {partes[1][0]}."
        return partes[0]

    def extraer_franjas(turno):
        """
        Devuelve un set con {'1','2','3'} según el turno,
        incluyendo extras y combinados.
        """
        if pd.isna(turno):
            return set()

        t = str(turno)

        NO_CUENTAN = [
            "D","Vac","BAJA","perm","AP","Ts",
            "Dc","Dct","Dcc","Dcv","JuB","JuC",
            "Curso","indisp"
        ]

        if any(x in t for x in NO_CUENTAN):
            return set()

        franjas = set()
        if "1" in t:
            franjas.add("1")
        if "2" in t:
            franjas.add("2")
        if "3" in t:
            franjas.add("3")

        return franjas

    def compañeros(fecha, turno_usuario):
        """
        Devuelve los compañeros que coinciden
        en alguna franja del turno del usuario
        (incluye extras)
        """
        franjas_usuario = extraer_franjas(turno_usuario)

        if not franjas_usuario:
            return []

        df_dia = df_mes[
            (df_mes["fecha"] == fecha) &
            (df_mes["nip"] != st.session_state.nip)
        ]

        resultado = []

        for _, r in df_dia.iterrows():
            franjas_otro = extraer_franjas(r["turno"])
            if franjas_usuario & franjas_otro:
                resultado.append(formatear_nombre(r["nombre"]))

        return resultado

    # -------------------------------
    # CALENDARIO
    # -------------------------------
    for semana in cal.monthdatescalendar(2026, mes_sel):
        cols = st.columns(7)

        for i, d in enumerate(semana):
            with cols[i]:
                if d.month != mes_sel:
                    st.write("")
                    continue

                fila = df_user[df_user["fecha"] == pd.Timestamp(d)]

                html = (
                    "<div style='border:1px solid #999;"
                    "text-align:center;"
                    "padding:4px'>"
                    f"<b>{d.day}</b><br>"
                )

                if not fila.empty:
                    turno_dia = str(fila.iloc[0]["turno"])
                    for p in separar(turno_dia):
                        e = estilo_turno(p)
                        html += (
                            f"<div style='background:{e['bg']};"
                            f"color:{e['fg']};"
                            f"text-align:center'>"
                            f"<b>{nombre_turno(p)}</b><br>"
                        )

                        comps = compañeros(pd.Timestamp(d), p)
                        for c in comps:
                            html += f"{c}<br>"

                        html += "</div>"

                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

        st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)

# ==================================================
# PANEL DE EDICIÓN (SOLO ADMIN)
# ==================================================
if st.session_state.is_admin:

    st.markdown("---")
    st.subheader("🛠️ Edición de turnos (ADMIN)")

    # ---- Selección de trabajador
    df_trab = (
        df_mes[["nombre", "nip"]]
        .drop_duplicates()
        .sort_values("nombre")
    )

    opciones_trab = {
        f"{row['nombre']} ({row['nip']})": row["nip"]
        for _, row in df_trab.iterrows()
    }

    col1, col2, col3 = st.columns(3)

    with col1:
        trabajador_sel = st.selectbox(
            "👮 Trabajador",
            options=list(opciones_trab.keys())
        )
        nip_sel = opciones_trab[trabajador_sel]

    with col2:
        dia_sel = st.selectbox(
            "📅 Día del mes",
            sorted(df_mes["dia"].unique())
        )

    TURNOS_EDITABLES = [
        "1", "2", "3", "L",
        "1ex", "2ex", "3ex",
        "D", "Dc", "Dcv", "Dcc", "Dct", "Dcj",
        "Vac", "BAJA", "perm", "Ts", "AP",
        "JuB", "JuC", "Curso", "Indisp",
        "1y2", "1y3", "2y3",
        "1y2ex", "1y3ex", "2y3ex",
        "1|2ex", "1|3ex", "2|1ex", "2|3ex", "3|1ex", "3|2ex", "L|2ex",
        "1yJuB", "AP|1ex", "AP|2ex", "AP|3ex", "3yJuC"
    ]

    with col3:
        turno_sel = st.selectbox("🔁 Nuevo turno", TURNOS_EDITABLES)
        observaciones = st.text_input(
            "📝 Observaciones (opcional)",
            placeholder="Ej.: Cambio por enfermedad, ajuste de servicio…"
        )

    # ---- Guardar cambio
    if st.button("💾 Guardar cambio"):
        fecha_sel = date(2026, mes_sel, dia_sel)

        mask = (
            (df["nip"] == nip_sel) &
            (df["fecha"] == pd.Timestamp(fecha_sel))
        )

        if mask.any():
            turno_anterior = df.loc[mask, "turno"].iloc[0]
            nombre_afectado = df.loc[mask, "nombre"].iloc[0]
        else:
            turno_anterior = ""
            fila_base = df_mes[df_mes["nip"] == nip_sel].iloc[0]
            nombre_afectado = fila_base["nombre"]

        registro = {
            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "usuario_admin": st.session_state.nip,
            "nip_afectado": normalizar_nip(nip_sel),
            "nombre_afectado": nombre_afectado,
            "fecha_turno": fecha_sel.strftime("%Y-%m-%d"),
            "turno_anterior": turno_anterior,
            "turno_nuevo": turno_sel,
            "observaciones": observaciones.strip()
        }

        try:
            df_hist = pd.read_csv(HISTORIAL_FILE)
            df_hist = pd.concat(
                [df_hist, pd.DataFrame([registro])],
                ignore_index=True
            )
        except FileNotFoundError:
            df_hist = pd.DataFrame([registro])

        guardar_csv_en_github(df_hist, "historial_cambios.csv")

        st.success("✅ Turno actualizado y guardado en el historial")
        st.rerun()

# ==================================================
# TAB HISTORIAL — SOLO ADMIN (EDITAR / ELIMINAR)
# ==================================================
if st.session_state.is_admin:
    with tab_historial:
        st.subheader("📜 Historial de cambios del cuadrante")

        if not os.path.exists(HISTORIAL_FILE):
            st.info("Todavía no hay cambios registrados en el historial.")
            st.stop()

        df_hist = pd.read_csv(HISTORIAL_FILE)
        df_hist["fecha_hora"] = pd.to_datetime(df_hist["fecha_hora"])
        df_hist = df_hist.sort_values("fecha_hora", ascending=False).reset_index(drop=True)

        st.dataframe(df_hist, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("✏️ Editar o eliminar registro")

        # ----- Selección de registro
        opciones = {
            f"{row['fecha_hora']} | {row['nombre_afectado']} | {row['fecha_turno']}":
            i
            for i, row in df_hist.iterrows()
        }

        seleccion = st.selectbox(
            "Selecciona un registro",
            options=list(opciones.keys())
        )

        idx = opciones[seleccion]
        registro = df_hist.loc[idx]

        # ----- Campos editables
        nuevo_turno = st.text_input(
            "🔁 Turno nuevo",
            value=registro["turno_nuevo"]
        )

        nuevas_obs = st.text_input(
            "📝 Observaciones",
            value=str(registro.get("observaciones", ""))
        )

        col1, col2 = st.columns(2)

        # ----- BOTÓN GUARDAR CAMBIOS
        with col1:
            if st.button("💾 Guardar cambios"):
                df_hist.loc[idx, "turno_nuevo"] = nuevo_turno
                df_hist.loc[idx, "observaciones"] = nuevas_obs
                guardar_csv_en_github(df_hist, "historial_cambios.csv")
                st.success("✅ Registro actualizado correctamente")
                st.rerun()

        # ----- BOTÓN ELIMINAR REGISTRO
        with col2:
            if st.button("🗑️ Eliminar registro"):
                df_hist = df_hist.drop(index=idx).reset_index(drop=True)
                guardar_csv_en_github(df_hist, "historial_cambios.csv")

                st.warning("🗑️ Registro eliminado del historial")
                st.rerun()
