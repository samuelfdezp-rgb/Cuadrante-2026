import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date

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
# DÍAS ESPECIALES
# ==================================================
festivos = {
    date(2026, 1, 1),
    date(2026, 1, 6),
}

def es_dia_especial(d):
    return d in festivos or d.weekday() == 6  # domingo

# ==================================================
# ESTILOS DE TURNO (YA DEFINIDOS)
# ==================================================
def estilo_turno(turno):
    t = "" if pd.isna(turno) else str(turno)

    estilos = {
        "1": {"bg": "#BDD7EE", "fg": "#0070C0"},
        "2": {"bg": "#FFE699", "fg": "#0070C0"},
        "3": {"bg": "#F8CBAD", "fg": "#FF0000"},

        "1ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "2ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},

        "1y2": {"bg": "#BDD7EE", "fg": "#FF0000"},
        "1y3": {"bg": "#BDD7EE", "fg": "#FF0000"},
        "2y3": {"bg": "#BDD7EE", "fg": "#FF0000"},

        "1|2ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "1|3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "2|1ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "2|3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "3|1ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "3|2ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "1y2ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "1y3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "2y3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},

        "D": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dc": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcv": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcc": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dct": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcj": {"bg": "#C6E0B4", "fg": "#00B050"},

        "Vac": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True, "italic": True},
        "AP": {"bg": "#FFFFFF", "fg": "#0070C0", "bold": True},
        "Ts": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Perm": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Indisp": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "JuB": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "JuC": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Curso": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Baja": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
    }

    return estilos.get(t, {"bg": "#FFFFFF", "fg": "#000000"})

# ==================================================
# PESTAÑA CUADRANTE GENERAL
# ==================================================
st.subheader("📋 Cuadrante general")

orden = df_mes[["nombre", "categoria", "nip"]].drop_duplicates()

cuadrante = df_mes.pivot_table(
    index=["nombre", "categoria", "nip"],
    columns="dia_mes",
    values="turno",
    aggfunc="first"
).reindex(pd.MultiIndex.from_frame(orden))

html = """
<div style="overflow:auto; max-height:80vh">
<table border="1" style="border-collapse:collapse;font-size:11px;table-layout:fixed;width:100%">
<thead>
<tr>
<th style="position:sticky;left:0;top:0;background:#DDD;z-index:3">Nombre</th>
<th style="position:sticky;left:150px;top:0;background:#DDD;z-index:3">Cat.</th>
<th style="position:sticky;left:230px;top:0;background:#DDD;z-index:3">NIP</th>
"""

for d in cuadrante.columns:
    fecha = date(2026, mes_sel, d)
    if es_dia_especial(fecha):
        html += f"<th style='top:0;position:sticky;background:#92D050;color:#FF0000;font-weight:bold'>{d}</th>"
    else:
        html += f"<th style='top:0;position:sticky;background:#FFFFFF;color:#000000;font-weight:bold'>{d}</th>"

html += "</tr></thead><tbody>"

for (nombre, categoria, nip), fila in cuadrante.iterrows():
    html += "<tr>"
    html += f"<td style='position:sticky;left:0;background:#FFF;white-space:nowrap'>{nombre}</td>"
    html += f"<td style='position:sticky;left:150px;background:#FFF'>{categoria}</td>"
    html += f"<td style='position:sticky;left:230px;background:#FFF'>{nip}</td>"

    for d, v in zip(cuadrante.columns, fila):
        e = estilo_turno(v)
        texto = "" if pd.isna(v) else v
        html += (
            f"<td style='background:{e['bg']};color:{e['fg']};"
            f"{'font-weight:bold;' if e.get('bold') else ''}"
            f"{'font-style:italic;' if e.get('italic') else ''}"
            f"text-align:center'>{texto}</td>"
        )
    html += "</tr>"

html += "</tbody></table></div>"

st.markdown(html, unsafe_allow_html=True)
