import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import os

# ==================================================
# CONFIGURACIÓN
# ==================================================
st.set_page_config(page_title="Cuadrante 2026", layout="wide")

ADMIN_NIP = "ADMIN"
DATA_FILE = "cuadrante_2026.csv"
HORAS_MANUALES_FILE = "horas_manuales.csv"

# ==================================================
# SESIÓN
# ==================================================
if "nip" not in st.session_state:
    st.session_state.nip = None

# ==================================================
# DATOS
# ==================================================
df = pd.read_csv(DATA_FILE, parse_dates=["fecha"])
df["dia"] = df["fecha"].dt.day

# ==================================================
# HORAS MANUALES (CSV AUXILIAR)
# ==================================================
if not os.path.exists(HORAS_MANUALES_FILE):
    pd.DataFrame(columns=["nip", "mes", "tipo", "horas"]).to_csv(
        HORAS_MANUALES_FILE, index=False
    )

df_horas_manual = pd.read_csv(HORAS_MANUALES_FILE)

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
# FESTIVOS
# ==================================================
festivos = {date(2026, 1, 1), date(2026, 1, 6)}

def es_festivo(fecha):
    return fecha in festivos

# ==================================================
# HORAS AUTOMÁTICAS
# ==================================================
HORAS = {
    "1": 8,
    "2": 8,
    "3": 11.875,
    "AP": 7.5,
    "Ts": 7.5,
    "JuB": 4,
    "JuC": 7.5,
}

# ==================================================
# ESTILO TURNOS (COLORES)
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

        "Ts": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
        "Perm": {"bg": "#FFFFFF", "fg": "#FF0000", "bold": True},
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
# MES
# ==================================================
meses = sorted(df["mes"].unique())
mes = st.selectbox(
    "Selecciona mes",
    meses,
    format_func=lambda x: datetime(2026, x, 1).strftime("%B 2026"),
)
df_mes = df[df["mes"] == mes]

# ==================================================
# TABS
# ==================================================
tab1, tab2, tab3 = st.tabs(
    ["📋 Cuadrante general", "📆 Mis turnos", "📊 Resumen"]
)

# ==================================================
# TAB 1 — CUADRANTE GENERAL
# ==================================================
with tab1:
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
        text-align: center;
    }
    th { font-weight: bold; }
    </style>
    <div style="overflow:auto; max-height:80vh">
    <table>
    <tr>
    <th>Nombre y Apellidos</th>
    <th>Categoría</th>
    <th>NIP</th>
    """

    for d in tabla.columns:
        fecha = date(2026, mes, d)
        if es_festivo(fecha) or fecha.weekday() == 6:
            html += f"<th style='background:#92D050;color:#FF0000'>{d}</th>"
        else:
            html += f"<th>{d}</th>"
    html += "</tr>"

    for (nombre, categoria, nip), fila in tabla.iterrows():
        html += f"<tr><td>{nombre}</td><td>{categoria}</td><td>{nip}</td>"
        for v in fila:
            e = estilo_turno(v)
            texto = "" if pd.isna(v) else v
            html += (
                f"<td style='background:{e['bg']};color:{e['fg']};"
                f"{'font-weight:bold;' if e.get('bold') else ''}"
                f"{'font-style:italic;' if e.get('italic') else ''}'>"
                f"{texto}</td>"
            )
        html += "</tr>"
    html += "</table></div>"

    st.markdown(html, unsafe_allow_html=True)

# ==================================================
# TAB 2 — MIS TURNOS
# ==================================================
with tab2:
    st.subheader("📆 Mis turnos")

    df_user = df_mes[df_mes["nip"] == st.session_state.nip]
    cal = calendar.Calendar()

    def separar(turno):
        if "y" in turno:
            return turno.split("y")
        if "|" in turno:
            return turno.split("|")
        return [turno]

    for semana in cal.monthdatescalendar(2026, mes):
        cols = st.columns(7)
        for i, d in enumerate(semana):
            with cols[i]:
                if d.month != mes:
                    st.write("")
                    continue

                fila = df_user[df_user["fecha"] == pd.Timestamp(d)]
                html = f"<div style='border:1px solid #999;border-radius:6px'>"
                html += f"<div style='text-align:center;font-weight:bold'>{d.day}</div>"

                if not fila.empty:
                    for p in separar(str(fila.iloc[0]["turno"])):
                        e = estilo_turno(p)
                        html += (
                            f"<div style='background:{e['bg']};color:{e['fg']};"
                            f"text-align:center;padding:6px'>"
                            f"<b>{p}</b></div>"
                        )
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

# ==================================================
# TAB 3 — RESUMEN
# ==================================================
with tab3:
    st.subheader("📊 Resumen año 2026")

    df_user_all = df[df["nip"] == st.session_state.nip]
    nombre = df_user_all["nombre"].iloc[0]
    nip = st.session_state.nip

    st.markdown(
        f"<h3 style='text-align:center'>RESUMEN 2026<br>{nombre} – {nip}</h3>",
        unsafe_allow_html=True,
    )

    filas = [
        "Mañanas","Tardes","Noches","Vacaciones","APs","Ferias",
        "Trabajo sindical","Días de Baja","Días de Juicio",
        "Permisos","Cursos","Descansos compensados","Indisposiciones",
        "Jefaturas de servicio","Festivos trabajados",
        "Fines de semana trabajados","Domingos trabajados",
        "Horas trabajadas",
    ]
    resumen = {f: [0]*12 for f in filas}

    orden_general = df[["nombre","nip"]].drop_duplicates().reset_index(drop=True)

    for _, r in df_user_all.iterrows():
        m = r["mes"] - 1
        turno = str(r["turno"])
        fecha = r["fecha"]
        dia_sem = fecha.weekday()

        sub = separar(turno)

        for t in sub:
            if t == "1": resumen["Mañanas"][m] += 1
            if t == "2": resumen["Tardes"][m] += 1
            if t == "3": resumen["Noches"][m] += 1

            resumen["Horas trabajadas"][m] += HORAS.get(t, 0)

        if turno == "Vac" and dia_sem < 5 and not es_festivo(fecha):
            resumen["Vacaciones"][m] += 1
        if turno == "AP": resumen["APs"][m] += 1
        if turno == "Ts": resumen["Trabajo sindical"][m] += 1
        if turno == "BAJA": resumen["Días de Baja"][m] += 1
        if turno in ["JuB","JuC"]: resumen["Días de Juicio"][m] += 1
        if turno == "Perm": resumen["Permisos"][m] += 1
        if turno == "Curso": resumen["Cursos"][m] += 1
        if turno.startswith("Dc"): resumen["Descansos compensados"][m] += 1
        if turno == "Indisp": resumen["Indisposiciones"][m] += 1

        if fecha.day in [1,16] and "1" in sub:
            resumen["Ferias"][m] += 1

        if es_festivo(fecha) and any(t in ["1","2","3"] for t in sub):
            resumen["Festivos trabajados"][m] += 1

        if dia_sem in [5,6] and any(t in ["1","2","3"] for t in sub):
            resumen["Fines de semana trabajados"][m] += 0.5
            if dia_sem == 6:
                resumen["Domingos trabajados"][m] += 1

        for t in sub:
            if t not in ["1","2","3"]: continue
            cand = df[(df["fecha"]==fecha) & (df["turno"].str.contains(t))]
            cand = cand.merge(orden_general, on=["nombre","nip"])
            if not cand.empty and cand.iloc[0]["nip"] == nip:
                resumen["Jefaturas de servicio"][m] += 1

    for _, r in df_horas_manual[df_horas_manual["nip"] == nip].iterrows():
        resumen["Horas trabajadas"][r["mes"]-1] += r["horas"]

    meses_txt = [
        "Enero","Febrero","Marzo","Abril","Mayo","Junio",
        "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
    ]

    df_res = pd.DataFrame(
        {meses_txt[i]: [resumen[f][i] for f in filas] for i in range(12)},
        index=filas
    )
    df_res["Total"] = df_res.sum(axis=1)

    st.dataframe(df_res, use_container_width=True)

    if st.session_state.nip == ADMIN_NIP:
        st.markdown("### ✏️ Horas manuales (ADMIN)")
        with st.form("horas_manual"):
            nip_i = st.text_input("NIP")
            mes_i = st.selectbox("Mes", list(range(1,13)))
            tipo_i = st.selectbox("Tipo", ["Baja","Perm","Curso","Indisp"])
            horas_i = st.number_input("Horas", min_value=0.0)
            if st.form_submit_button("Guardar"):
                df_horas_manual.loc[len(df_horas_manual)] = [
                    nip_i, mes_i, tipo_i, horas_i
                ]
                df_horas_manual.to_csv(HORAS_MANUALES_FILE, index=False)
                st.success("Horas guardadas")
                st.rerun()
