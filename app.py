import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
st.set_page_config(page_title="Cuadrante 2026", layout="wide")

ADMIN_NIP = "ADMIN"
DATA_FILE = "cuadrante_2026.csv"

# ==================================================
# SESIÓN
# ==================================================
if "nip" not in st.session_state:
    st.session_state.nip = None
    st.session_state.is_admin = False

# ==================================================
# CARGA DE DATOS
# ==================================================
def load_data():
    return pd.read_csv(DATA_FILE, parse_dates=["fecha"])

df = load_data()

# ==================================================
# LOGIN
# ==================================================
if st.session_state.nip is None:
    st.title("🔐 Acceso al Cuadrante")

    raw_input = st.text_input("Introduce tu NIP").strip()

    if st.button("Entrar"):
        if raw_input == ADMIN_NIP:
            st.session_state.nip = ADMIN_NIP
            st.session_state.is_admin = True
            st.rerun()

        nip_input = raw_input.zfill(6)
        if nip_input in df["nip"].astype(str).str.zfill(6).unique():
            st.session_state.nip = nip_input
            st.session_state.is_admin = False
            st.rerun()
        else:
            st.error("NIP no válido")

    st.stop()

# ==================================================
# CABECERA
# ==================================================
st.title("📅 Cuadrante 2026")

if st.button("🚪 Cerrar sesión"):
    st.session_state.nip = None
    st.session_state.is_admin = False
    st.rerun()

# ==================================================
# SELECTOR DE MES
# ==================================================
meses = sorted(df["mes"].unique())
mes_sel = st.selectbox(
    "Selecciona mes",
    meses,
    format_func=lambda x: datetime(2026, x, 1).strftime("%B 2026")
)

df_mes = df[df["mes"] == mes_sel].copy()
df_mes["dia_mes"] = df_mes["fecha"].dt.day

# ==================================================
# ESTILOS DE TURNO (COMPLETO)
# ==================================================
def estilo_turno(turno):
    t = "" if pd.isna(turno) else str(turno)

    estilos = {
        # Mañana / Laborable
        "L": {"bg": "#BDD7EE", "fg": "#0070C0"},
        "1": {"bg": "#BDD7EE", "fg": "#0070C0"},

        # Tarde
        "2": {"bg": "#FFE699", "fg": "#0070C0"},

        # Noche
        "3": {"bg": "#F8CBAD", "fg": "#FF0000"},

        # Extras
        "1ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "2ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},

        # Combinados normales
        "1y2": {"bg": "#BDD7EE", "fg": "#FF0000"},
        "1y3": {"bg": "#BDD7EE", "fg": "#FF0000"},
        "2y3": {"bg": "#BDD7EE", "fg": "#FF0000"},

        # Combinados con extras
        "1|2ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "1|3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "2|1ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "2|3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "3|1ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "3|2ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "1y2ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "1y3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "2y3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},

        # Descansos
        "D":   {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dc":  {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcv": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcc": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dct": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcj": {"bg": "#C6E0B4", "fg": "#00B050"},

        # Incidencias
        "Ts":     {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Perm":   {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Indisp": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "JuB":    {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "JuC":    {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Curso":  {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Baja":   {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},

        # Vacaciones
        "Vac": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True, "italic": True},

        # Asuntos particulares
        "AP": {"bg": "#FFFFFF", "fg": "#0070C0", "bold": True},
    }

    return estilos.get(t, {"bg": "#FFFFFF", "fg": "#000000"})

# ==================================================
# PESTAÑAS
# ==================================================
tab_general, tab_personal = st.tabs(["📋 Cuadrante general", "📆 Mi cuadrante"])

# ==================================================
# CUADRANTE GENERAL (COMPACTO)
# ==================================================
with tab_general:
    orden = df_mes[["nombre", "categoria", "nip"]].drop_duplicates()

    cuadrante = df_mes.pivot_table(
        index=["nombre", "categoria", "nip"],
        columns="dia_mes",
        values="turno",
        aggfunc="first"
    ).reindex(pd.MultiIndex.from_frame(orden))

    html = "<div style='overflow-x:auto'><table border='1' style='border-collapse:collapse;font-size:11px'>"
    html += "<tr><th>Nombre</th><th>Cat.</th><th>NIP</th>"
    for d in cuadrante.columns:
        html += f"<th style='width:28px'>{d}</th>"
    html += "</tr>"

    for (nombre, categoria, nip), fila in cuadrante.iterrows():
        html += f"<tr><td>{nombre}</td><td>{categoria}</td><td>{nip}</td>"
        for v in fila:
            e = estilo_turno(v)
            texto = "" if pd.isna(v) else v
            html += (
                f"<td style='background:{e['bg']};color:{e['fg']};"
                f"{'font-weight:bold;' if e.get('bold') else ''}"
                f"{'font-style:italic;' if e.get('italic') else ''}"
                f"text-align:center'>{texto}</td>"
            )
        html += "</tr>"

    html += "</table></div>"
    st.markdown(html, unsafe_allow_html=True)

# ==================================================
# MI CUADRANTE
# ==================================================
with tab_personal:
    df_p = df_mes[df_mes["nip"] == st.session_state.nip]
    cal = calendar.Calendar()
    for semana in cal.monthdatescalendar(2026, mes_sel):
        cols = st.columns(7)
        for i, d in enumerate(semana):
            with cols[i]:
                if d.month != mes_sel:
                    st.write("")
                    continue
                dato = df_p[df_p["fecha"] == pd.Timestamp(d)]
                if not dato.empty:
                    t = dato.iloc[0]["turno"]
                    e = estilo_turno(t)
                    st.markdown(
                        f"<div style='background:{e['bg']};color:{e['fg']};"
                        f"{'font-weight:bold;' if e.get('bold') else ''}"
                        f"{'font-style:italic;' if e.get('italic') else ''}"
                        f"text-align:center;border-radius:6px'>{d.day}<br>{t}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<b>{d.day}</b>", unsafe_allow_html=True)
