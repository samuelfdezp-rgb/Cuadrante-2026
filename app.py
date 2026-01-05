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
def estilo_turno(turno):
    t = "" if pd.isna(turno) else str(turno)

    estilos = {
        # Laborable / Mañana
        "L":  {"bg": "#BDD7EE", "fg": "#0070C0"},
        "1":  {"bg": "#BDD7EE", "fg": "#0070C0"},
        "1ex":{"bg": "#00B050", "fg": "#FF0000", "bold": True},

        # Tarde
        "2":  {"bg": "#FFE699", "fg": "#0070C0"},
        "2ex":{"bg": "#00B050", "fg": "#FF0000", "bold": True},

        # Noche
        "3":  {"bg": "#F8CBAD", "fg": "#FF0000"},
        "3ex":{"bg": "#00B050", "fg": "#FF0000", "bold": True},

        # Descansos
        "D":   {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dc":  {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcv": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcc": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dct": {"bg": "#C6E0B4", "fg": "#00B050"},
        "Dcj": {"bg": "#C6E0B4", "fg": "#00B050"},

        # Incidencias (negrita)
        "Ts":     {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Perm":   {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Indisp": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "JuB":    {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "JuC":    {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Curso":  {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Baja":   {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},

        # Vacaciones (negrita + cursiva)
        "Vac":        {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True, "italic": True},
        "Vacaciones": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True, "italic": True},

        # Asuntos particulares
        "AP": {"bg": "#FFFFFF", "fg": "#0070C0", "bold": True},
    }

    return estilos.get(t, {"bg": "#FFFFFF", "fg": "#000000"})

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
            estilo = estilo_turno(valor)

            bg = estilo.get("bg")
            fg = estilo.get("fg")
            bold = "font-weight:bold;" if estilo.get("bold") else ""
            italic = "font-style:italic;" if estilo.get("italic") else ""
            html += f"<td style='background-color:{color}; text-align:center'>{texto}</td>"

        html += (
            f"<td style='background-color:{bg}; color:{fg}; "
            f"{bold}{italic} text-align:center'>{texto}</td>"
        )

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
