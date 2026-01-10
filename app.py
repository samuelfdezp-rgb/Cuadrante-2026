import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import base64

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
st.set_page_config(page_title="Cuadrante 2026", layout="wide")

ADMIN_USER = "ADMIN"
ADMIN_PASS = "PoliciaLocal2021!"
DATA_FILE = "cuadrante_2026.csv"
USERS_FILE = "usuarios.csv"
ESCUDO_FILE = "Placa.png"
CABECERA_FILE = "cabecera.png"

# ==================================================
# SESIÓN
# ==================================================
if "nip" not in st.session_state:
    st.session_state.nip = None
    
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ==================================================
# CARGA DE DATOS
# ==================================================
df = pd.read_csv(DATA_FILE, parse_dates=["fecha"])
df["dia"] = df["fecha"].dt.day
df["nip"] = df["nip"].astype(str)

usuarios = pd.read_csv(USERS_FILE)
usuarios["nip"] = usuarios["nip"].astype(str)
usuarios["dni"] = usuarios["dni"].astype(str)

# ==================================================
# LOGIN
# ==================================================
if st.session_state.nip is None:
    st.markdown(
        """
        <style>
        body, .stApp { background-color: white; }

        label {
            color: black !important;
            font-weight: 600;
        }

        .login-title {
            color: black;
            font-size: 32px;
            font-weight: 700;
            margin: 20px 0 30px 0;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Escudo perfectamente centrado (FORMA CORRECTA)
    with open(ESCUDO_FILE, "rb") as f:
        escudo_base64 = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin-top:20px;">
            <img src="data:image/png;base64,{escudo_base64}" width="220">
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div class='login-title'>🔐 Acceso al cuadrante</div>", unsafe_allow_html=True)

    usuario = st.text_input("Usuario (NIP)")
    password = st.text_input("Contraseña (DNI)", type="password")

    if st.button("Entrar"):
        # ADMIN
        if usuario == ADMIN_USER and password == ADMIN_PASS:
            st.session_state.nip = ADMIN_USER
            st.session_state.is_admin = True
            st.rerun()

        # USUARIOS NORMALES
        usuario_fmt = usuario.strip().zfill(6)
        fila = usuarios[usuarios["nip"] == usuario_fmt]

        if not fila.empty and fila.iloc[0]["dni"] == password.strip():
            st.session_state.nip = usuario_fmt
            st.session_state.is_admin = False
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

# ==================================================
# CABECERA POST LOGIN
# ==================================================
with open(CABECERA_FILE, "rb") as f:
    cabecera = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <div style="width:100%;margin-bottom:10px">
        <img src="data:image/png;base64,{cabecera}" style="width:100%">
    </div>
    """,
    unsafe_allow_html=True
)

st.title("📅 Cuadrante 2026")

if st.button("🚪 Cerrar sesión"):
    st.session_state.nip = None
    st.session_state.is_admin = False
    st.rerun()

# ==================================================
# MESES EN CASTELLANO
# ==================================================
MESES = {
    1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
    7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
}

mes = st.selectbox(
    "Selecciona mes",
    sorted(df["mes"].unique()),
    format_func=lambda m: f"{MESES[m]} 2026"
)

df_mes = df[df["mes"] == mes].copy()
df_mes["dia"] = df_mes["fecha"].dt.day

# ==================================================
# FESTIVOS Y DOMINGOS
# ==================================================
from datetime import date

FESTIVOS_2026 = {
    date(2026, 1, 1),   # Año nuevo
    date(2026, 1, 6),   # Reyes
    # aquí puedes añadir más si quieres
}

def es_especial(fecha):
    """
    Devuelve True si la fecha es domingo o festivo
    """
    return fecha.weekday() == 6 or fecha in FESTIVOS_2026

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
    "Curso": "Curso", "Indisp": "Indisposición",
}

def nombre_turno(c):
    return NOMBRES_TURNO.get(c, c)

# ==================================================
# ESTILOS DE TURNOS
# ==================================================
def estilo_turno(t):
    if pd.isna(t):
        return {"bg": "#FFFFFF", "fg": "#000000", "bold": False}

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
        "BAJA": ("#FFFFFF", "#FF0000"),
        "Ts": ("#FFFFFF", "#FF0000"),
        "AP": ("#FFFFFF", "#0070C0"),
    }

    if t in {"1y2", "1y3", "2y3"}:
        return {"bg": "#DBDBDB", "fg": "#FF0000", "bold": True}

    if "ex" in t and ("y" in t or "|" in t):
        return {"bg": "#00B050", "fg": "#FF0000", "bold": True}

    bg, fg = base.get(t, ("#FFFFFF", "#000000"))
    return {"bg": bg, "fg": fg, "bold": t == "perm"}

# ==================================================
# PESTAÑAS
# ==================================================
tab_general, tab_mis_turnos = st.tabs(
    ["📋 Cuadrante general", "📆 Mis turnos"]
)

# ==================================================
# TAB — CUADRANTE GENERAL (EXCEL REAL A4:AM49)
# ==================================================
from openpyxl import load_workbook
from openpyxl.styles.colors import Color

with tab_general:

    st.subheader("📋 Cuadrante general")

    EXCEL_FILE = "01 - Cuadrante Enero 2026.xlsx"
    SHEET_NAME = "Enero"

    wb = load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active

    # Rango EXACTO
    start_row, end_row = 4, 49
    start_col, end_col = 1, 39   # A=1, AM=39

    def excel_color(cell_color):
        if cell_color is None:
            return None
        if isinstance(cell_color, Color):
            if cell_color.type == "rgb" and cell_color.rgb:
                return f"#{cell_color.rgb[-6:]}"
        return None

    html = """
    <style>
    .excel-wrap {
        overflow-x: auto;
    }
    table.excel {
        border-collapse: collapse;
        font-size: 11px;
        white-space: nowrap;
    }
    table.excel td {
        border: 1px solid #000;
        padding: 3px;
        text-align: center;
        min-width: 26px;
    }
    </style>

    <div class="excel-wrap">
    <table class="excel">
    """

    for r in range(start_row, end_row + 1):
        html += "<tr>"
        for c in range(start_col, end_col + 1):
            cell = ws.cell(row=r, column=c)

            value = "" if cell.value is None else cell.value

            # Colores
            bg = excel_color(cell.fill.fgColor)
            fg = excel_color(cell.font.color)

            styles = ""
            if bg:
                styles += f"background:{bg};"
            if fg:
                styles += f"color:{fg};"
            if cell.font.bold:
                styles += "font-weight:bold;"
            if cell.font.italic:
                styles += "font-style:italic;"

            # Alineación izquierda para nombres
            if c == 1:
                styles += "text-align:left; padding-left:6px;"

            html += f"<td style='{styles}'>{value}</td>"
        html += "</tr>"

    html += "</table></div>"

    st.markdown(html, unsafe_allow_html=True)

# ==================================================
# TAB 2 — MIS TURNOS
# ==================================================
with tab_mis_turnos:
    st.subheader("📆 Mis turnos")

    df_user = df_mes[df_mes["nip"] == st.session_state.nip]
    cal = calendar.Calendar()
    TURNOS_TRABAJO = {"1", "2", "3", "1ex", "2ex", "3ex", "L"}

    def separar(turno):
        if "y" in turno: return turno.split("y")
        if "|" in turno: return turno.split("|")
        return [turno]

    def formatear_nombre(nombre):
        partes = nombre.split()
        if partes[0] in {"Iago", "Javier"} and len(partes) > 1:
            return f"{partes[0]} {partes[1][0]}."
        return partes[0]

    def compañeros(fecha, sub):
        if sub not in TURNOS_TRABAJO:
            return []
        return (
            df_mes[
                (df_mes["fecha"] == fecha) &
                (df_mes["turno"].str.contains(sub)) &
                (df_mes["nip"] != st.session_state.nip)
            ]["nombre"]
            .apply(formatear_nombre)
            .tolist()
        )

    for semana in cal.monthdatescalendar(2026, mes):
        cols = st.columns(7)
        for i, d in enumerate(semana):
            with cols[i]:
                if d.month != mes:
                    st.write("")
                    continue

                fila = df_user[df_user["fecha"] == pd.Timestamp(d)]
                html = f"<div style='border:1px solid #999'><b>{d.day}</b><br>"

                if not fila.empty:
                    for p in separar(str(fila.iloc[0]["turno"])):
                        e = estilo_turno(p)
                        html += (
                            f"<div style='background:{e['bg']};color:{e['fg']};text-align:center'>"
                            f"<b>{nombre_turno(p)}</b><br>"
                        )
                        for c in compañeros(pd.Timestamp(d), p):
                            html += f"{c}<br>"
                        html += "</div>"

                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

        st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)
