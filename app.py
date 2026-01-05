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
# FUNCIONES AUXILIARES
# ==================================================
def estilo_turno(turno):
    if pd.isna(turno):
        return {"bg": "#FFFFFF", "fg": "#000000"}

    t = str(turno).strip()

    estilos = {
        "L": ("#BDD7EE", "#0070C0"),
        "1": ("#BDD7EE", "#0070C0"),
        "2": ("#FFE699", "#0070C0"),
        "3": ("#F8CBAD", "#FF0000"),
        "1ex": ("#00B050", "#FF0000"),
        "2ex": ("#00B050", "#FF0000"),
        "3ex": ("#00B050", "#FF0000"),
        "D": ("#C6E0B4", "#00B050"),
        "Vac": ("#FFFFFF", "#FF0000"),
        "Perm": ("#FFFFFF", "#FF0000"),
        "Baja": ("#FFFFFF", "#FF0000"),
        "AP": ("#FFFFFF", "#0070C0"),
    }

    bg, fg = estilos.get(t, ("#FFFFFF", "#000000"))
    return {"bg": bg, "fg": fg}

def separar_turnos(turno):
    if "y" in turno:
        return turno.split("y")
    if "|" in turno:
        return turno.split("|")
    return [turno]

def compañeros_turno(dia, turno, nip_propio):
    compañeros = df_mes[
        (df_mes["dia"] == dia) &
        (df_mes["turno"] == turno) &
        (df_mes["nip"] != nip_propio)
    ]["nombre"].tolist()

    return [c.split()[0] for c in compañeros]

# ==================================================
# PESTAÑAS
# ==================================================
tab_general, tab_mis_turnos = st.tabs(
    ["📋 Cuadrante general", "📆 Mis turnos"]
)

# ==================================================
# TAB MIS TURNOS
# ==================================================
with tab_mis_turnos:
    st.subheader("📆 Mis turnos")

    df_user = df_mes[df_mes["nip"] == st.session_state.nip]
    cal = calendar.Calendar()

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
                    comps = compañeros_turno(d.day, p, st.session_state.nip)

                    html += (
                        f"<div style='background:{estilo['bg']};"
                        f"color:{estilo['fg']};"
                        f"padding:4px;"
                        f"height:{altura}px;"
                        f"font-size:12px'>"
                        f"<b>{p}</b><br>"
                    )

                    if p not in ["D", "Vac", "Perm", "Baja"]:
                        for c in comps:
                            html += f"{c}<br>"

                    html += "</div>"

                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
