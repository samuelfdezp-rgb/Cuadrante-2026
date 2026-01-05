import streamlit as st
import pandas as pd
from datetime import datetime, date

# ==================================================
# CONFIGURACIÓN
# ==================================================
st.set_page_config(page_title="Cuadrante 2026", layout="wide")

ADMIN_NIP = "ADMIN"
DATA_FILE = "cuadrante_2026.csv"

# ==================================================
# SESIÓN
# ==================================================
if "nip" not in st.session_state:
    st.session_state.nip = None

# ==================================================
# CARGA DATOS
# ==================================================
df = pd.read_csv(DATA_FILE, parse_dates=["fecha"])

# ==================================================
# LOGIN
# ==================================================
if st.session_state.nip is None:
    st.title("🔐 Acceso al Cuadrante")
    nip_raw = st.text_input("Introduce tu NIP").strip()

    if st.button("Entrar"):
        if nip_raw == ADMIN_NIP:
            st.session_state.nip = ADMIN_NIP
            st.rerun()

        nip = nip_raw.zfill(6)
        if nip in df["nip"].astype(str).str.zfill(6).unique():
            st.session_state.nip = nip
            st.rerun()
        else:
            st.error("NIP no válido")
    st.stop()

# ==================================================
# CABECERA
# ==================================================
st.title("📋 Cuadrante general 2026")
if st.button("🚪 Cerrar sesión"):
    st.session_state.nip = None
    st.rerun()

# ==================================================
# MES
# ==================================================
meses = sorted(df["mes"].unique())
mes = st.selectbox(
    "Selecciona mes",
    meses,
    format_func=lambda x: datetime(2026, x, 1).strftime("%B 2026")
)

df_mes = df[df["mes"] == mes].copy()
df_mes["dia"] = df_mes["fecha"].dt.day

# ==================================================
# FESTIVOS Y DOMINGOS
# ==================================================
festivos = {date(2026, 1, 1), date(2026, 1, 6)}

def es_especial(fecha):
    return fecha in festivos or fecha.weekday() == 6

# ==================================================
# ESTILO TURNOS
# ==================================================
def estilo_turno(turno):
    if pd.isna(turno):
        return {"bg": "#FFFFFF", "fg": "#000000"}

    t = str(turno).strip()
    if t.lower() == "baja":
        t = "BAJA"
    if t.lower() == "perm":
        t = "Perm"

    estilos = {
        "L": {"bg": "#BDD7EE", "fg": "#0070C0"},
        "1": {"bg": "#BDD7EE", "fg": "#0070C0"},
        "2": {"bg": "#FFE699", "fg": "#0070C0"},
        "3": {"bg": "#F8CBAD", "fg": "#FF0000"},

        "1ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "2ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},
        "3ex": {"bg": "#00B050", "fg": "#FF0000", "bold": True},

        "1y2": {"bg": "#BDD7EE", "fg": "#FF0000"},
        "1y3": {"bg": "#BDD7EE", "fg": "#FF0000"},
        "2y3": {"bg": "#BDD7EE", "fg": "#FF0000"},

        "D": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dc": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcv": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcc": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dct": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcj": {"bg": "#C6E0B4", "fg": "#00B050"},

        "Perm": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Ts": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Indisp": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "JuB": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "JuC": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Curso": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "BAJA": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},

        "Vac": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True, "italic": True},
        "AP": {"bg": "#FFFFFF", "fg": "#0070C0", "bold": True},
    }
    return estilos.get(t, {"bg": "#FFFFFF", "fg": "#000000"})

# ==================================================
# CUADRANTE (DOS TABLAS)
# ==================================================
orden = df_mes[["nombre", "categoria", "nip"]].drop_duplicates()

tabla = df_mes.pivot_table(
    index=["nombre", "categoria", "nip"],
    columns="dia",
    values="turno",
    aggfunc="first"
).reindex(pd.MultiIndex.from_frame(orden))

html = """
<style>
.container {
    display: flex;
    max-height: 80vh;
    overflow-y: auto;
}
table {
    border-collapse: collapse;
}
th, td {
    border: 1px solid #000;
    padding: 4px;
    white-space: nowrap;
}
th {
    background: #FFFFFF;
    color: #000000;
    font-weight: bold;
    text-align: center;   /* 👈 CLAVE */
}
.fija {
    border-right: 3px solid #000;
}
.abajo {
    border-bottom: 3px solid #000;
}
</style>

<div class="container">

<!-- TABLA IZQUIERDA -->
<table>
<thead>
<tr class="abajo">
<th>Nombre y Apellidos</th>
<th>Categoría</th>
<th class="fija">NIP</th>
</tr>
</thead>
<tbody>
"""

for (nombre, categoria, nip), _ in tabla.iterrows():
    html += f"<tr><td>{nombre}</td><td>{categoria}</td><td class='fija'>{nip}</td></tr>"

html += """
</tbody>
</table>

<!-- TABLA DERECHA -->
<div style="overflow-x:auto">
<table>
<thead>
<tr class="abajo">
"""

for d in tabla.columns:
    fecha = date(2026, mes, d)
    if es_especial(fecha):
        html += f"<th style='background:#92D050;color:#FF0000'>{d}</th>"
    else:
        html += f"<th>{d}</th>"

html += "</tr></thead><tbody>"

for fila in tabla.itertuples(index=False):
    html += "<tr>"
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

html += """
</tbody>
</table>
</div>
</div>
"""

st.markdown(html, unsafe_allow_html=True)
