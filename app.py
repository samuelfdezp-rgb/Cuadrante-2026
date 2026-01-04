import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------
ADMIN_NIP = "ADMIN"

DATA_FILE = "cuadrante_2026.csv"
EXCEL_FILE = "01 - Cuadrante Enero 2026.xlsx"
EXCEL_SHEET = "Enero 2026"

st.set_page_config(
    page_title="Cuadrante 2026",
    layout="wide"
)

# --------------------------------------------------
# SESIÓN
# --------------------------------------------------
if "nip" not in st.session_state:
    st.session_state.nip = None
    st.session_state.is_admin = False

# --------------------------------------------------
# CARGA DE DATOS CSV
# --------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE, parse_dates=["fecha"])

df = load_data()

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
if st.session_state.nip is None:
    st.title("🔐 Acceso al Cuadrante")

    nip_input = st.text_input("Introduce tu NIP").strip().zfill(6)

    if st.button("Entrar"):
        if nip_input == ADMIN_NIP:
            st.session_state.nip = ADMIN_NIP
            st.session_state.is_admin = True
            st.rerun()
        elif nip_input in df["nip"].astype(str).str.strip().str.zfill(6).unique():
            st.session_state.nip = nip_input
            st.session_state.is_admin = False
            st.rerun()
        else:
            st.error("NIP no válido")

    st.stop()

# --------------------------------------------------
# CABECERA PRINCIPAL
# --------------------------------------------------
st.title("📅 Cuadrante 2026")

if st.button("🚪 Cerrar sesión"):
    st.session_state.nip = None
    st.session_state.is_admin = False
    st.rerun()

# --------------------------------------------------
# SELECTOR DE MES (para CSV)
# --------------------------------------------------
meses = sorted(df["mes"].unique())
mes_sel = st.selectbox(
    "Selecciona mes",
    meses,
    format_func=lambda x: datetime(2026, x, 1).strftime("%B 2026")
)

df_mes = df[df["mes"] == mes_sel]

# --------------------------------------------------
# PESTAÑAS
# --------------------------------------------------
tab_general, tab_personal = st.tabs(
    ["📋 Cuadrante general", "📆 Mi cuadrante"]
)

# --------------------------------------------------
# PESTAÑA 1 – CUADRANTE GENERAL (EXCEL VISUAL)
# --------------------------------------------------
with tab_general:
    st.subheader("📋 Cuadrante general (vista mensual)")

    try:
        df_excel = pd.read_excel(
            EXCEL_FILE,
            sheet_name=EXCEL_SHEET,
            header=None
        )

        # Rango A3 : AM44
        df_visual = df_excel.iloc[2:44, 0:39]

        st.dataframe(
            df_visual,
            use_container_width=True,
            height=800
        )

    except Exception as e:
        st.error("No se pudo cargar el cuadrante general")
        st.write(e)

# --------------------------------------------------
# PESTAÑA 2 – MI CUADRANTE (CALENDARIO)
# --------------------------------------------------
with tab_personal:
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

                    st.markdown(
                        f"""
                        <div style="
                            background-color:#E7E6E6;
                            padding:10px;
                            border-radius:10px;
                            text-align:center;
                            min-height:80px;
                        ">
                        <b>{dia.day}</b><br>{turno}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<b>{dia.day}</b>", unsafe_allow_html=True)

# --------------------------------------------------
# EDICIÓN ADMINISTRADOR
# --------------------------------------------------
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
