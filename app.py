import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# --------------------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------------------
st.set_page_config(
    page_title="Cuadrante 2026",
    layout="wide"
)

ADMIN_NIP = "ADMIN"
DATA_FILE = "cuadrante_2026.csv"

# --------------------------------------------------
# SESIÓN
# --------------------------------------------------
if "nip" not in st.session_state:
    st.session_state.nip = None
    st.session_state.is_admin = False

# --------------------------------------------------
# CARGA DE DATOS
# --------------------------------------------------
def load_data():
    return pd.read_csv(DATA_FILE, parse_dates=["fecha"])

df = load_data()

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
if st.session_state.nip is None:
    st.title("🔐 Acceso al Cuadrante")

    raw_input = st.text_input("Introduce tu NIP").strip()

    if st.button("Entrar"):
        if raw_input == ADMIN_NIP:
            st.session_state.nip = ADMIN_NIP
            st.session_state.is_admin = True
            st.rerun()

        nip_input = raw_input.zfill(6)
        nips_validos = df["nip"].astype(str).str.zfill(6).unique()

        if nip_input in nips_validos:
            st.session_state.nip = nip_input
            st.session_state.is_admin = False
            st.rerun()
        else:
            st.error("NIP no válido")

    st.stop()

# --------------------------------------------------
# CABECERA
# --------------------------------------------------
st.title("📅 Cuadrante 2026")

if st.button("🚪 Cerrar sesión"):
    st.session_state.nip = None
    st.session_state.is_admin = False
    st.rerun()

# --------------------------------------------------
# SELECTOR DE MES
# --------------------------------------------------
meses = sorted(df["mes"].unique())
mes_sel = st.selectbox(
    "Selecciona mes",
    meses,
    format_func=lambda x: datetime(2026, x, 1).strftime("%B 2026")
)

df_mes = df[df["mes"] == mes_sel].copy()

# --------------------------------------------------
# PESTAÑAS
# --------------------------------------------------
tab_general, tab_personal = st.tabs(
    ["📋 Cuadrante general", "📆 Mi cuadrante"]
)

# --------------------------------------------------
# FUNCIÓN DE COLORES
# --------------------------------------------------
def color_turno(turno):
    colores = {
        "1": "#B7DEE8",      # Mañana
        "2": "#FCD5B4",      # Tarde
        "3": "#D9D2E9",      # Noche
        "D": "#E7E6E6",      # Descanso
        "Vac": "#C6EFCE",    # Vacaciones
        "Baja": "#F4CCCC",   # Baja
        "Ts": "#FFF2CC",     # Tiempo sindical
    }
    return colores.get(str(turno), "#FFFFFF")

# --------------------------------------------------
# PESTAÑA 1 – CUADRANTE GENERAL
# --------------------------------------------------
with tab_general:
    st.subheader("📋 Cuadrante general")

    df_mes["dia_mes"] = df_mes["fecha"].dt.day

    orden = (
        df_mes[["nombre", "categoria", "nip"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    cuadrante = df_mes.pivot_table(
        index=["nombre", "categoria", "nip"],
        columns="dia_mes",
        values="turno",
        aggfunc="first"
    )

    cuadrante = cuadrante.reindex(
        pd.MultiIndex.from_frame(orden)
    )

    cuadrante = cuadrante.reindex(
        sorted(cuadrante.columns),
        axis=1
    )

    # Construcción HTML con colores
    html = "<div style='overflow-x:auto'><table border='1' style='border-collapse:collapse; font-size:14px'>"

    # Cabecera
    html += "<tr>"
    html += "<th>Nombre y Apellidos</th><th>Categoría</th><th>NIP</th>"
    for dia in cuadrante.columns:
        html += f"<th>{dia}</th>"
    html += "</tr>"

    # Filas
    for (nombre, categoria, nip), fila in cuadrante.iterrows():
        html += "<tr>"
        html += f"<td>{nombre}</td>"
        html += f"<td>{categoria}</td>"
        html += f"<td>{nip}</td>"

        for valor in fila:
            texto = "" if pd.isna(valor) else valor
            color = color_turno(valor)
            html += f"<td style='background-color:{color}; text-align:center'>{texto}</td>"

        html += "</tr>"

    html += "</table></div>"

    st.markdown(html, unsafe_allow_html=True)

# --------------------------------------------------
# PESTAÑA 2 – MI CUADRANTE
# --------------------------------------------------
with tab_personal:
    st.subheader("📆 Mi cuadrante")

    df_persona = df_mes[df_mes["nip"] == st.session_state.nip]

    cal = calendar.Calendar(firstweekday=0)
    semanas = cal.monthdatescalendar(2026, mes_sel)

    for semana in semanas:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            with cols[i]:
                if dia.month != mes_sel:
                    st.write("")
                    continue

                dato = df_persona[df_persona["fecha"] == pd.Timestamp(dia)]

                if not dato.empty:
                    turno = dato.iloc[0]["turno"]
                    color = color_turno(turno)

                    st.markdown(
                        f"""
                        <div style="
                            background-color:{color};
                            padding:10px;
                            border-radius:8px;
                            text-align:center;
                            min-height:70px;
                        ">
                        <b>{dia.day}</b><br>{turno}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<b>{dia.day}</b>", unsafe_allow_html=True)
