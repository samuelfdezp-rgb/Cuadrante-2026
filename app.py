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
# CABECERA
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
    st.session_state.usuario = None
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
# FESTIVOS
# ==================================================
festivos = {date(2026, 1, 1), date(2026, 1, 6)}

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
    return {
        "bg": bg,
        "fg": fg,
        "bold": t in {"perm", "Ts", "AP"}
    }


# ==================================================
# PESTAÑAS
# ==================================================
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

    if modo_movil:
        index_cols = ["nip"]
        orden = df_mes["nip"].drop_duplicates()
    else:
        index_cols = ["nombre", "categoria", "nip"]
        orden = df_mes[index_cols].drop_duplicates()

    tabla = (
        df_mes
        .pivot_table(index=index_cols, columns="dia", values="turno", aggfunc="first")
        .reindex(orden)
    )

    html = f"""
    <style>
    table {{
        border-collapse: collapse;
        font-size: 10px;
        transform: scale({zoom});
        transform-origin: top left;
    }}
    th, td {{
        border: 1px solid #000;
        padding: 2px;
        text-align: center;
        vertical-align: middle;
        white-space: nowrap;
    }}
    th {{
        font-weight: bold;
    }}
    td.nombre {{ white-space: nowrap; }}
    </style>
    <div style="overflow:auto">
    <table>
    <tr>
    """

    html += "<th>NIP</th>" if modo_movil else "<th>Nombre y apellidos</th><th>Categoría</th><th>NIP</th>"

    for d in tabla.columns:
        f = date(2026, mes, d)
        if es_festivo(f) or f.weekday() == 6:
            html += f"<th style='background:#92D050;color:#FF0000'>{d}</th>"
        else:
            html += f"<th>{d}</th>"
    html += "</tr>"

    for idx, fila in tabla.iterrows():
        html += "<tr>"
        if modo_movil:
            html += f"<td>{idx}</td>"
        else:
            nombre, cat, nip = idx
            html += f"<td class='nombre'>{nombre}</td><td>{cat}</td><td>{nip}</td>"

        for v in fila:
            e = estilo_turno(v)
            txt = "" if pd.isna(v) else v
            html += (
                f"<td style='background:{e['bg']};color:{e['fg']};"
                f"font-weight:{'bold' if e['bold'] else 'normal'}'>{txt}</td>"
            )
        html += "</tr>"

    # ==================================================
    # FILAS RESUMEN POR TURNO (ESTILO EXCEL)
    # ==================================================

    def contar(dia, turnos):
        return df_mes[
            (df_mes["dia"] == dia) &
            (df_mes["turno"].notna()) &
            (df_mes["turno"].apply(lambda x: any(t in str(x) for t in turnos)))
        ]["nip"].nunique()

    dias = list(tabla.columns)

    resumen_filas = [
        ("Mañanas", ["1", "1ex", "L"], estilo_turno("1")["bg"]),
        ("Tardes",  ["2", "2ex"],      estilo_turno("2")["bg"]),
        ("Noches",  ["3", "3ex"],      estilo_turno("3")["bg"]),
    ]

    for nombre, turnos, color in resumen_filas:
        html += "<tr>"
        # columnas fijas
        if modo_movil:
            html += f"<td><b>{nombre}</b></td>"
        else:
            html += f"<td></td><td><b>{nombre}</b></td><td></td>"

        # columnas de días
        for d in dias:
            total = contar(d, turnos)
            html += (
                f"<td style='background:{color};"
                f"color:#000;font-weight:bold;text-align:center;"
                f"vertical-align:middle'>{total}</td>"
            )
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
