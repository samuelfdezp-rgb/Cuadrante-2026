import pandas as pd
import calendar
from datetime import datetime, date
import os

# ==================================================
# CONFIGURACIÓN GENERAL
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
# CARGA DE DATOS
# ==================================================
df = pd.read_csv(DATA_FILE, parse_dates=["fecha"])
df["dia"] = df["fecha"].dt.day
df["nip"] = df["nip"].astype(str)

# ==================================================
# HORAS MANUALES
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
        if nip in df["nip"].str.zfill(6).unique():
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
# HORAS AUTOMÁTICAS (CORREGIDO)
# ==================================================
HORAS = {
    "1": 8,
    "2": 8,
    "3": 11.875,   # 9,5 × 1,25
    "L": 8,
    "AP": 7.5,
    "Ts": 7.5,
    "JuB": 4,
    "JuC": 7.5,
}

# ==================================================
# NOMBRES DE TURNOS
# ==================================================
NOMBRES_TURNO = {
    "1": "Mañana",
    "2": "Tarde",
    "3": "Noche",
    "L": "Laborable",
    "1ex": "Mañana extra",
    "2ex": "Tarde extra",
    "3ex": "Noche extra",
    "D": "Descanso",
    "Dc": "Descanso compensado",
    "Dcv": "Descanso comp. verano",
    "Dcc": "Descanso comp. curso",
    "Dct": "Descanso comp. tiro",
    "Dcj": "Descanso comp. juicio",
    "Vac": "Vacaciones",
    "Perm": "Permiso",
    "BAJA": "Baja",
    "Ts": "Tiempo sindical",
    "AP": "Asuntos particulares",
    "JuB": "Juicio Betanzos",
    "JuC": "Juicio Coruña",
    "Curso": "Curso",
    "Indisp": "Indisposición",
}

def nombre_turno(codigo):
    return NOMBRES_TURNO.get(codigo, codigo)

# ==================================================
# ESTILOS DE TURNOS (CORREGIDOS)
# ==================================================
def estilo_turno(turno):
    if pd.isna(turno):
        return {"bg": "#FFFFFF", "fg": "#000000", "bold": False}

    t = str(turno)

    base = {
        "1": ("#BDD7EE", "#0070C0"),
        "L": ("#BDD7EE", "#0070C0"),
        "2": ("#FFE699", "#0070C0"),
        "3": ("#F8CBAD", "#FF0000"),
        "1ex": ("#00B050", "#FF0000"),
        "2ex": ("#00B050", "#FF0000"),
        "3ex": ("#00B050", "#FF0000"),
        "D": ("#C6E0B4", "#00B050"),
        "Dc": ("#C6E0B4", "#00B050"),
        "Dcv": ("#C6E0B4", "#00B050"),
        "Dcc": ("#C6E0B4", "#00B050"),
        "Dct": ("#C6E0B4", "#00B050"),
        "Dcj": ("#C6E0B4", "#00B050"),
        "Vac": ("#FFFFFF", "#FF0000"),
        "Perm": ("#FFFFFF", "#FF0000"),
        "BAJA": ("#FFFFFF", "#FF0000"),
        "Ts": ("#FFFFFF", "#FF0000"),
        "AP": ("#FFFFFF", "#0070C0"),
    }

    if t in {"1y2", "1y3", "2y3"}:
        return {"bg": "#DBDBDB", "fg": "#FF0000", "bold": True}

    if "ex" in t and ("y" in t or "|" in t):
        return {"bg": "#00B050", "fg": "#FF0000", "bold": True}

    bg, fg = base.get(t, ("#FFFFFF", "#000000"))
    return {"bg": bg, "fg": fg, "bold": t in {"Perm"}}

# ==================================================
# SELECCIÓN DE MES
# ==================================================
mes = st.selectbox(
    "Selecciona mes",
    sorted(df["mes"].unique()),
    format_func=lambda x: datetime(2026, x, 1).strftime("%B 2026"),
)
df_mes = df[df["mes"] == mes]

# ==================================================
# PESTAÑAS
# ==================================================
tab_general, tab_mis_turnos, tab_resumen = st.tabs(
    ["📋 Cuadrante general", "📆 Mis turnos", "📊 Resumen"]
)

# ==================================================
# TAB 1 — CUADRANTE GENERAL
# ==================================================
with tab_general:
    st.subheader("📋 Cuadrante general")
    modo_movil = st.checkbox("📱 Modo móvil")

    if modo_movil:
        index_cols = ["nip"]
        orden = df_mes["nip"].drop_duplicates()
    else:
        index_cols = ["nombre", "categoria", "nip"]
        orden = df_mes[index_cols].drop_duplicates()

    tabla = df_mes.pivot_table(
        index=index_cols,
        columns="dia",
        values="turno",
        aggfunc="first"
    ).reindex(orden)

    html = """
    <style>
    table { border-collapse:collapse; width:100%; font-size:10px; }
    th, td { border:1px solid #000; padding:2px; text-align:center; white-space:nowrap; }
    td.nombre { white-space:nowrap; }
    </style>
    <table><tr>
    """

    html += "<th>NIP</th>" if modo_movil else "<th>Nombre y apellidos</th><th>Categoría</th><th>NIP</th>"

    for d in tabla.columns:
        f = date(2026, mes, d)
        if es_festivo(f) or f.weekday() == 6:
            html += f"<th style='background:#92D050;color:#FF0000'>{d}</th>"
        else:
            html += f"<th>{d}</th>"
    html += "</tr>"

    for idx, fila in tabla.iterrows():
        html += "<tr>"
        if modo_movil:
            html += f"<td>{idx}</td>"
        else:
            nombre, cat, nip = idx
            html += f"<td class='nombre'>{nombre}</td><td>{cat}</td><td>{nip}</td>"

        for v in fila:
            e = estilo_turno(v)
            txt = "" if pd.isna(v) else v
            html += (
                f"<td style='background:{e['bg']};color:{e['fg']};"
                f"font-weight:{'bold' if e['bold'] else 'normal'}'>{txt}</td>"
            )
        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# ==================================================
# TAB 2 — MIS TURNOS
# ==================================================
with tab_mis_turnos:
    st.subheader("📆 Mis turnos")

    df_user = df_mes[df_mes["nip"] == st.session_state.nip]
    cal = calendar.Calendar()
    TURNOS_TRABAJO = {"1", "2", "3", "1ex", "2ex", "3ex", "L"}

    def separar(turno):
        if "y" in turno: return turno.split("y")
        if "|" in turno: return turno.split("|")
        return [turno]

    def formatear_nombre(n):
        p = n.split()
        if p[0] in {"Iago", "Javier"} and len(p) > 1:
            return f"{p[0]} {p[1][0]}."
        return p[0]

    def compañeros(fecha, sub):
        if sub not in TURNOS_TRABAJO:
            return []
        return (
            df_mes[
                (df_mes["fecha"] == fecha) &
                (df_mes["turno"].str.contains(sub)) &
                (df_mes["nip"] != st.session_state.nip)
            ]["nombre"]
            .apply(formatear_nombre)
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
                html = f"<div style='border:1px solid #999'><b>{d.day}</b><br>"

                if not fila.empty:
                    for p in separar(str(fila.iloc[0]["turno"])):
                        e = estilo_turno(p)
                        html += (
                            f"<div style='background:{e['bg']};color:{e['fg']};text-align:center'>"
                            f"<b>{nombre_turno(p)}</b><br>"
                        )
                        for c in compañeros(pd.Timestamp(d), p):
                            html += f"{c}<br>"
                        html += "</div>"

                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

# ==================================================
# TAB 3 — RESUMEN
# ==================================================
with tab_resumen:
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

    def separar_resumen(turno):
        if "y" in turno:
            return turno.split("y")
        if "|" in turno:
            return turno.split("|")
        return [turno]

    for _, r in df_user_all.iterrows():
        m = r["mes"] - 1
        turno = str(r["turno"])
        fecha = r["fecha"]
        dia_sem = fecha.weekday()
        sub = separar_resumen(turno)

        for t in sub:
            if t in {"1","L"}: resumen["Mañanas"][m] += 1
            if t == "2": resumen["Tardes"][m] += 1
            if t == "3": resumen["Noches"][m] += 1
            resumen["Horas trabajadas"][m] += HORAS.get(t, 0)

        if turno == "Vac" and dia_sem < 5 and not es_festivo(fecha):
            resumen["Vacaciones"][m] += 1
        if turno == "AP": resumen["APs"][m] += 1
        if turno == "Ts": resumen["Trabajo sindical"][m] += 1
        if turno == "BAJA": resumen["Días de Baja"][m] += 1
        if turno in {"JuB","JuC"}: resumen["Días de Juicio"][m] += 1
        if turno == "Perm": resumen["Permisos"][m] += 1
        if turno == "Curso": resumen["Cursos"][m] += 1
        if turno.startswith("Dc"): resumen["Descansos compensados"][m] += 1
        if turno == "Indisp": resumen["Indisposiciones"][m] += 1

        if fecha.day in {1,16} and any(t in {"1","L"} for t in sub):
            resumen["Ferias"][m] += 1

        if es_festivo(fecha) and any(t in {"1","2","3","L"} for t in sub):
            resumen["Festivos trabajados"][m] += 1

        if dia_sem in {5,6} and any(t in {"1","2","3","L"} for t in sub):
            resumen["Fines de semana trabajados"][m] += 0.5
            if dia_sem == 6:
                resumen["Domingos trabajados"][m] += 1

        for t in sub:
            if t not in {"1","2","3","L"}:
                continue
            cand = df[(df["fecha"] == fecha) & (df["turno"].str.contains(t))]
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

    st.dataframe(df_res, use_container_width=True)import streamlit as st
