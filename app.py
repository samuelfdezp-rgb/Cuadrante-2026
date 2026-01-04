import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# ---------------- CONFIG ----------------
ADMIN_NIP = "ADMIN"
DATA_FILE = "cuadrante_2026.csv"

COLORES_TURNO = {
    "1": "#A7C7E7", "2": "#FFD966", "3": "#C00000",
    "1ex": "#9BC2E6", "2ex": "#FFE699", "3ex": "#E06666",
    "Vac": "#92D050", "Vacaciones": "#92D050",
    "D": "#D9D9D9", "Dc": "#B4C6E7", "Dcv": "#8FAADC",
    "Perm": "#F4B084", "Baja": "#7030A0",
    "Curso": "#00B0F0", "Ts": "#FCE4D6",
    "Indisp": "#FF9999", "JuB": "#BDD7EE",
    "JuC": "#9DC3E6", "Tiro": "#FFE699",
}

st.set_page_config(page_title="Cuadrante 2026", layout="wide")

# ---------------- SESIÓN ----------------
if "nip" not in st.session_state:
    st.session_state.nip = None
    st.session_state.is_admin = False

# ---------------- DATOS ----------------
@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE, parse_dates=["fecha"])

df = load_data()

# ---------------- LOGIN ----------------
if st.session_state.nip is None:
    st.title("🔐 Acceso al Cuadrante")
    nip_input = st.text_input("Introduce tu NIP")

    if st.button("Entrar"):
        if nip_input == ADMIN_NIP:
            st.session_state.nip = ADMIN_NIP
            st.session_state.is_admin = True
            st.st.rerun()()
        elif nip_input in df["nip"].astype(str).unique():
            st.session_state.nip = nip_input
            st.session_state.is_admin = False
            st.st.rerun()()
        else:
            st.error("NIP no válido")

    st.stop()

# ---------------- HEADER ----------------
st.title("📅 Cuadrante 2026")

if st.button("🚪 Cerrar sesión"):
    st.session_state.nip = None
    st.session_state.is_admin = False
    st.st.rerun()()

# ---------------- SELECTOR MES ----------------
meses = sorted(df["mes"].unique())
mes_sel = st.selectbox(
    "Selecciona mes",
    meses,
    format_func=lambda x: datetime(2026, x, 1).strftime("%B 2026")
)

df_mes = df[df["mes"] == mes_sel]

# ---------------- CUADRANTE GENERAL ----------------
st.subheader("📋 Cuadrante general")
st.dataframe(
    df_mes[["fecha", "dia", "nip", "nombre", "turno"]],
    use_container_width=True
)

# ---------------- VISTA INDIVIDUAL ----------------
st.subheader("📆 Mi cuadrante")

df_persona = df_mes[df_mes["nip"].astype(str) == st.session_state.nip]

cal = calendar.Calendar(firstweekday=0)
mes_cal = cal.monthdatescalendar(2026, mes_sel)

for semana in mes_cal:
    cols = st.columns(7)
    for i, dia in enumerate(semana):
        with cols[i]:
            if dia.month != mes_sel:
                st.write(" ")
                continue

            dato = df_persona[df_persona["fecha"] == pd.Timestamp(dia)]
            if not dato.empty:
                turno = dato.iloc[0]["turno"]
                color = COLORES_TURNO.get(turno, "#FFFFFF")

                st.markdown(
                    f"""
                    <div style="
                        background-color:{color};
                        padding:10px;
                        border-radius:10px;
                        text-align:center;
                        color:black;
                        min-height:80px;
                    ">
                    <b>{dia.day}</b><br>{turno}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f"<b>{dia.day}</b>", unsafe_allow_html=True)

# ---------------- EDICIÓN ADMIN ----------------
if st.session_state.is_admin:
    st.markdown("---")
    st.subheader("✏️ Edición administrador")

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Guardar cambios"):
        edited_df.to_csv(DATA_FILE, index=False)
        st.cache_data.clear()
        st.success("Cambios guardados correctamente")
