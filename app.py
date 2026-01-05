import streamlit as st
import pandas as pd
import calendar
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
# CARGA DE DATOS
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
st.title("📅 Cuadrante 2026")
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
# ESTILOS DE TURNO (ÚNICO Y COMPARTIDO)
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
# PESTAÑAS
# ==================================================
tab_general, tab_mis_turnos = st.tabs(
    ["📋 Cuadrante general", "📆 Mis turnos"]
)

# ==================================================
# TAB 1 — CUADRANTE GENERAL (RESTAURADO)
# ==================================================
with tab_general:
    st.subheader("📋 Cuadrante general")

    orden = df_mes[["nombre", "categoria", "nip"]].drop_duplicates()

    tabla = df_mes.pivot_table(
        index=["nombre", "categoria", "nip"],
        columns="dia",
        values="turno",
        aggfunc="first"
    ).reindex(pd.MultiIndex.from_frame(orden))

    html = """
    <style>
    table { border-collapse: collapse; }
    th, td {
        border: 1px solid #000;
        padding: 4px;
        white-space: nowrap;
    }
    th {
        font-weight: bold;
        text-align: center;
    }
    .borde-abajo { border-bottom: 3px solid #000; }
    .borde-derecha { border-right: 3px solid #000; }
    </style>

    <div style="overflow:auto; max-height:80vh">
    <table>
    <tr class="borde-abajo">
    <th>Nombre y Apellidos</th>
    <th>Categoría</th>
    <th class="borde-derecha">NIP</th>
    """

    for d in tabla.columns:
        fecha = date(2026, mes, d)
        if es_especial(fecha):
            html += f"<th style='background:#92D050;color:#FF0000'>{d}</th>"
        else:
            html += f"<th>{d}</th>"

    html += "</tr>"

    for (nombre, categoria, nip), fila in tabla.iterrows():
        html += f"<tr><td>{nombre}</td><td>{categoria}</td><td class='borde-derecha'>{nip}</td>"
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
# TAB 2 — MIS TURNOS
# ==================================================
with tab_mis_turnos:
    st.subheader("📆 Mis turnos")

    df_user = df_mes[df_mes["nip"] == st.session_state.nip]
    cal = calendar.Calendar()

    def separar_turnos(turno):
        if "y" in turno:
            return turno.split("y")
        if "|" in turno:
            return turno.split("|")
        return [turno]

    def compañeros(dia, turno):
        return (
            df_mes[
                (df_mes["dia"] == dia) &
                (df_mes["turno"] == turno) &
                (df_mes["nip"] != st.session_state.nip)
            ]["nombre"]
            .apply(lambda x: x.split()[0])
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
                if fila.empty:
                    st.markdown(f"**{d.day}**")
                    continue

                turno = fila.iloc[0]["turno"]
                partes = separar_turnos(turno)

                html = f"<div style='border:1px solid #999;border-radius:6px'>"
                html += f"<div style='text-align:center;font-weight:bold'>{d.day}</div>"

                altura = 100 // len(partes)

                for p in partes:
                    estilo = estilo_turno(p)
                    comps = compañeros(d.day, p)

                    html += (
                        f"<div style='background:{estilo['bg']};color:{estilo['fg']};"
                        f"padding:4px;height:{altura}px;font-size:12px'>"
                        f"<b>{p}</b><br>"
                    )

                    if p not in ["D", "Vac", "Perm", "BAJA"]:
                        for c in comps:
                            html += f"{c}<br>"

                    html += "</div>"

                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
