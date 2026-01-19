import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import base64
import os
import glob

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
st.set_page_config(page_title="Cuadrante 2026", layout="wide")

ADMIN_USER = "ADMIN"
ADMIN_PASS = "PoliciaLocal2021!"

USERS_FILE = "usuarios.csv"
HISTORIAL_FILE = "historial_cambios.csv"
CUADRANTES_DIR = "cuadrantes"

ESCUDO_FILE = "Placa.png"
CABECERA_FILE = "cabecera.png"

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# ==================================================
# FUNCIONES BASE
# ==================================================
def normalizar_nip(nip):
    return str(nip).strip().zfill(6)

def listar_cuadrantes():
    archivos = sorted(glob.glob(f"{CUADRANTES_DIR}/*.csv"))
    resultado = {}

    for f in archivos:
        nombre = os.path.basename(f).replace(".csv", "")
        try:
            anio, mes = nombre.split("_")
            mes = int(mes)
            resultado[f"{MESES[mes]} {anio}"] = f
        except:
            continue

    return resultado

def cargar_cuadrantes():
    archivos = glob.glob(f"{CUADRANTES_DIR}/*.csv")
    if not archivos:
        st.error("No hay cuadrantes disponibles")
        st.stop()

    dfs = []

    for ruta in archivos:
        df_tmp = pd.read_csv(
            ruta,
            parse_dates=["Fecha"]
        )

        df_tmp["nip"] = df_tmp["NIP"].apply(normalizar_nip)
        df_tmp["fecha"] = df_tmp["Fecha"]
        df_tmp["dia"] = df_tmp["fecha"].dt.day
        df_tmp["mes"] = df_tmp["Mes"]
        df_tmp["anio"] = df_tmp["Año"]

        df_tmp = df_tmp.rename(columns={
            "Nombre y Apellidos": "nombre",
            "Categoría": "categoria",
            "Turno": "turno"
        })

        dfs.append(df_tmp)

    return pd.concat(dfs, ignore_index=True)

def aplicar_historial(df):
    if not os.path.exists(HISTORIAL_FILE):
        return df

    hist = pd.read_csv(
        HISTORIAL_FILE,
        parse_dates=["fecha_turno", "fecha_hora"]
    ).sort_values("fecha_hora")

    for _, r in hist.iterrows():
        nip = normalizar_nip(r["nip_afectado"])
        fecha = pd.Timestamp(r["fecha_turno"])

        mask = (df["nip"] == nip) & (df["fecha"] == fecha)

        if mask.any():
            df.loc[mask, "turno"] = r["turno_nuevo"]
        else:
            df.loc[len(df)] = {
                "anio": fecha.year,
                "mes": fecha.month,
                "fecha": fecha,
                "dia": fecha.day,
                "nip": nip,
                "nombre": r.get("nombre_afectado", ""),
                "categoria": "",
                "turno": r["turno_nuevo"],
            }

    return df

def guardar_historial(registro):
    if os.path.exists(HISTORIAL_FILE):
        df = pd.read_csv(HISTORIAL_FILE)
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
    else:
        df = pd.DataFrame([registro])

    df.to_csv(HISTORIAL_FILE, index=False)

# ==================================================
# SESIÓN
# ==================================================
if "nip" not in st.session_state:
    st.session_state.nip = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ==================================================
# LOGIN
# ==================================================
if st.session_state.nip is None:
    with open(ESCUDO_FILE, "rb") as f:
        escudo = base64.b64encode(f.read()).decode()

    st.markdown(
        f"<div style='display:flex;justify-content:center'><img src='data:image/png;base64,{escudo}' width='220'></div>",
        unsafe_allow_html=True
    )

    st.markdown("<h2 style='text-align:center'>🔐 Acceso al cuadrante</h2>", unsafe_allow_html=True)

    usuario = st.text_input("Usuario (NIP)")
    password = st.text_input("Contraseña (DNI)", type="password")

    usuarios = pd.read_csv(USERS_FILE)
    usuarios["nip"] = usuarios["nip"].apply(normalizar_nip)

    if st.button("Entrar"):
        if usuario == ADMIN_USER and password == ADMIN_PASS:
            st.session_state.nip = ADMIN_USER
            st.session_state.is_admin = True
            st.rerun()

        nip = normalizar_nip(usuario)
        fila = usuarios[usuarios["nip"] == nip]

        if not fila.empty and fila.iloc[0]["dni"] == password:
            st.session_state.nip = nip
            st.session_state.is_admin = False
            st.rerun()

        st.error("Usuario o contraseña incorrectos")

    st.stop()

# ==================================================
# CABECERA
# ==================================================
with open(CABECERA_FILE, "rb") as f:
    cabecera = base64.b64encode(f.read()).decode()

st.markdown(
    f"<img src='data:image/png;base64,{cabecera}' style='width:100%;margin-bottom:10px'>",
    unsafe_allow_html=True
)

st.title("📅 Cuadrante 2026")

if st.button("🚪 Cerrar sesión"):
    st.session_state.nip = None
    st.session_state.is_admin = False
    st.rerun()

# ==================================================
# CARGA DE CUADRANTES
# ==================================================
cuadrantes = listar_cuadrantes()
if not cuadrantes:
    st.error("No hay cuadrantes disponibles")
    st.stop()

mes_label = st.selectbox("📅 Selecciona mes", list(cuadrantes.keys()))
df = cargar_cuadrantes()
df = aplicar_historial(df)

anio_sel, mes_sel = mes_label.split()
mes_sel = list(MESES.keys())[list(MESES.values()).index(anio_sel)]
df_mes = df[df["mes"] == mes_sel]

st.success(f"Mostrando cuadrante de {mes_label}")

# ==================================================
# FESTIVOS
# ==================================================
festivos = {date(2026, 1, 1), date(2026, 1, 6)}

def es_festivo(fecha):
    return fecha in festivos

# ==================================================
# NOMBRES DE TURNOS
# ==================================================
NOMBRES_TURNO = {
    "1": "Mañana", "2": "Tarde", "3": "Noche", "L": "Laborable",
    "1ex": "Mañana extra", "2ex": "Tarde extra", "3ex": "Noche extra",
    "D": "Descanso", "Dc": "Descanso compensado",
    "Dcv": "Desc. comp. verano", "Dcc": "Desc. comp. curso",
    "Dct": "Desc. comp. tiro", "Dcj": "Desc. comp. juicio",
    "Vac": "Vacaciones", "perm": "Permiso", "BAJA": "Baja",
    "Ts": "Tiempo sindical", "AP": "Asuntos particulares",
    "JuB": "Juicio Betanzos", "JuC": "Juicio Coruña",
    "Curso": "Curso", "indisp": "Indisposición",
}

def nombre_turno(c):
    return NOMBRES_TURNO.get(c, c)

# ==================================================
# ESTILOS DE TURNOS
# ==================================================
def estilo_turno(t):
    if pd.isna(t):
        return {"bg": "#FFFFFF", "fg": "#000000", "bold": False, "italic": False}

    t = str(t)

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
        "perm": ("#FFFFFF", "#FF0000"),
        "indisp": ("#FFFFFF", "#FF0000"),
        "curso": ("#FFFFFF", "#FF0000"),
        "BAJA": ("#FFFFFF", "#FF0000"),
        "Ts": ("#FFFFFF", "#FF0000"),
        "JuB": ("#FFFFFF", "#FF0000"),
        "JuC": ("#FFFFFF", "#FF0000"),
        "1yJuB": ("#BDD7EE", "#FF0000"),
        "AP": ("#FFFFFF", "#0070C0"),
    }

    # Turnos dobles normales
    if t in {"1y2", "1y3", "2y3"}:
        return {"bg": "#DBDBDB", "fg": "#FF0000", "bold": True, "italic": False}

    # Turnos dobles con extra
    if "ex" in t and ("y" in t or "|" in t):
        return {"bg": "#00B050", "fg": "#FF0000", "bold": True, "italic": False}

    bg, fg = base.get(t, ("#FFFFFF", "#000000"))

    # ---- NEGRITA
    bold = (
        t in {"perm", "Ts", "JuB", "JuC", "AP", "Ts", "Vac", "BAJA", "indisp", "curso", "1yJuB"} or
        "ex" in t or               # cualquier extra
        t in {"1y2", "1y3", "2y3"}
    )

    # ---- CURSIVA
    italic = t in {"Vac", "BAJA"}

    return {
        "bg": bg,
        "fg": fg,
        "bold": bold,
        "italic": italic
    }

# ==================================================
# PESTAÑAS
# ==================================================
if st.session_state.is_admin:
    tab_general, tab_mis_turnos, tab_historial = st.tabs(
        ["📋 Cuadrante general", "📆 Mis turnos", "📜 Historial"]
    )
else:
    tab_general, tab_mis_turnos = st.tabs(
        ["📋 Cuadrante general", "📆 Mis turnos"]
    )

# ==================================================
# TAB 1 — CUADRANTE GENERAL (MODO MÓVIL + ZOOM)
# ==================================================
with tab_general:
    st.subheader("📋 Cuadrante general")

    modo_movil = st.checkbox("📱 Modo móvil")

    zoom = 1.0
    if modo_movil:
        zoom = st.slider(
            "🔍 Zoom",
            0.3, 1.5, 0.5, 0.05
        )

    # ---------- CUADRANTE ----------
    if modo_movil:
        index_cols = ["nip"]
        orden = df_mes["nip"].drop_duplicates()
    else:
        index_cols = ["nombre", "categoria", "nip"]
        orden = df_mes[index_cols].drop_duplicates()

    tabla = (
        df_mes
        .pivot_table(
            index=index_cols,
            columns="dia",
            values="turno",
            aggfunc="first"
        )
        .reindex(orden)
    )

    # ---------- HTML + CSS ----------
    html = f"""
    <style>
        .wrapper {{
            transform: scale({zoom});
            transform-origin: top left;
            width: fit-content;
        }}
        table {{
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            border: 1px solid #000;
            padding: 6px;
            text-align: center;
            white-space: nowrap;
        }}
    </style>

    <div style="overflow:auto">
      <div class="wrapper">
        <table>
          <tr>
    """

    if modo_movil:
        html += "<th>NIP</th>"
    else:
        html += "<th>Nombre y apellidos</th><th>Categoría</th><th>NIP</th>"

    for d in tabla.columns:
        fecha = date(2026, mes, d)
        if es_festivo(fecha) or fecha.weekday() == 6:
            html += f"<th style='background:#92D050;color:#FF0000'>{d}</th>"
        else:
            html += f"<th>{d}</th>"

    html += "</tr>"

    # ---------- FUNCIÓN CONTEO ----------
    def contar_turnos(codigo):
        if pd.isna(codigo):
            return set()

        c = str(codigo)

        NO_CUENTAN = ["D", "Vac", "BAJA", "perm", "AP", "Ts", "Dc", "Dct", "Dcc", "Dcv"]
        for x in NO_CUENTAN:
            if x in c:
                return set()

        turnos = set()
        if "1" in c:
            turnos.add("M")
        if "2" in c:
            turnos.add("T")
        if "3" in c:
            turnos.add("N")

        return turnos

    conteo_manana = []
    conteo_tarde = []
    conteo_noche = []

    for dia in tabla.columns:
        m = t = n = 0
        for _, fila in tabla.iterrows():
            turnos = contar_turnos(fila[dia])
            if "M" in turnos:
                m += 1
            if "T" in turnos:
                t += 1
            if "N" in turnos:
                n += 1

        conteo_manana.append(m)
        conteo_tarde.append(t)
        conteo_noche.append(n)

    # ---------- FILAS DEL CUADRANTE ----------
    for idx, fila in tabla.iterrows():
        html += "<tr>"

        if modo_movil:
            html += f"<td>{idx}</td>"
        else:
            if isinstance(idx, tuple) and len(idx) == 3:
                nombre, cat, nip = idx
            else:
                nombre, cat, nip = "", "", str(idx)

            html += (
                f"<td class='nombre'>{nombre}</td>"
                f"<td>{cat}</td>"
                f"<td>{nip}</td>"
            )

        for v in fila:
            e = estilo_turno(v)
            txt = "" if pd.isna(v) else v
            html += (
                f"<td style='background:{e['bg']};"
                f"color:{e['fg']};"
                f"font-weight:{'bold' if e.get('bold') else 'normal'};"
                f"font-style:{'italic' if e.get('italic') else 'normal'}'>"
                f"{txt}</td>"
            )

        html += "</tr>"

    # ---------- FILAS RESUMEN ----------
    def fila_resumen(titulo, datos, color):
        fila = "<tr>"
        if modo_movil:
            fila += f"<td style='background:{color};color:#000;font-weight:bold'>{titulo}</td>"
        else:
            fila += f"<td colspan='3' style='background:{color};color:#000;font-weight:bold'>{titulo}</td>"

        for v in datos:
            fila += f"<td style='background:{color};color:#000;font-weight:bold'>{v}</td>"

        return fila + "</tr>"

    html += fila_resumen("Mañanas", conteo_manana, "#BDD7EE")
    html += fila_resumen("Tardes", conteo_tarde, "#FFE699")
    html += fila_resumen("Noches", conteo_noche, "#F8CBAD")

    html += """
        </table>
      </div>
    </div>
    """

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

    def formatear_nombre(nombre):
        partes = nombre.split()
        if partes[0] in {"Iago", "Javier"} and len(partes) > 1:
            return f"{partes[0]} {partes[1][0]}."
        return partes[0]

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

        st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)

# ==================================================
# PANEL DE EDICIÓN (SOLO ADMIN)
# ==================================================
if st.session_state.is_admin:

    st.markdown("---")
    st.subheader("🛠️ Edición de turnos (ADMIN)")

    # ---- Selección de trabajador
    df_trab = (
        df_mes[["nombre", "nip"]]
        .drop_duplicates()
        .sort_values("nombre")
    )

    opciones_trab = {
        f"{row['nombre']} ({row['nip']})": row["nip"]
        for _, row in df_trab.iterrows()
    }

    col1, col2, col3 = st.columns(3)

    with col1:
        trabajador_sel = st.selectbox(
            "👮 Trabajador",
            options=list(opciones_trab.keys())
        )
        nip_sel = opciones_trab[trabajador_sel]

    # ---- Selección de día
    with col2:
        dia_sel = st.selectbox(
            "📅 Día del mes",
            sorted(df_mes["dia"].unique())
        )

    # ---- Selección de turno
    TURNOS_EDITABLES = [
        "1", "2", "3", "L",
        "1ex", "2ex", "3ex",
        "D", "Dc", "Dcv", "Dcc", "Dct", "Dcj",
        "Vac", "BAJA", "perm", "Ts", "AP",
        "JuB", "JuC", "Curso", "Indisp",
        "1y2", "1y3", "2y3",
        "1|2ex", "1|3ex", "2|3ex", "L|2ex",
        "1yJuB"
    ]

    with col3:
        turno_sel = st.selectbox(
            "🔁 Nuevo turno",
            TURNOS_EDITABLES
        )
        
        observaciones = st.text_input(
        "📝 Observaciones (opcional)",
        placeholder="Ej.: Cambio por enfermedad, ajuste de servicio…"
        )

    # ---- Botón guardar
    if st.button("💾 Guardar cambio"):
        fecha_sel = date(2026, mes, dia_sel)
    
        mask = (
            (df["nip"] == nip_sel) &
            (df["fecha"] == pd.Timestamp(fecha_sel))
        )

        if mask.any():
            turno_anterior = df.loc[mask, "turno"].iloc[0]
            nombre_afectado = df.loc[mask, "nombre"].iloc[0]
            categoria_afectado = df.loc[mask, "categoria"].iloc[0]

            df.loc[mask, "turno"] = turno_sel
        else:
            turno_anterior = ""
            fila_base = df_mes[df_mes["nip"] == nip_sel].iloc[0]

            nombre_afectado = fila_base["nombre"]
            categoria_afectado = fila_base["categoria"]
    
            nueva = {
                "anio": 2026,
                "mes": mes,
                "fecha": fecha_sel,
                "dia": dia_sel,
                "nip": nip_sel,
                "nombre": nombre_afectado,
                "categoria": categoria_afectado,
                "turno": turno_sel,
                "tipo": ""
            }
            df.loc[len(df)] = nueva

        # Guardar cuadrante
        guardar_cambio(df, BASE_FILE)

        # Registrar historial
        registro = {
            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "usuario_admin": st.session_state.nip,
            "nip_afectado": normalizar_nip(nip_sel),
            "nombre_afectado": nombre_afectado,
            "fecha_turno": fecha_sel.strftime("%Y-%m-%d"),
            "turno_anterior": turno_anterior,
            "turno_nuevo": turno_sel,
            "observaciones": observaciones.strip()
        }

        try:
            df_hist = pd.read_csv(HISTORIAL_FILE)
            df_hist = pd.concat(
                [df_hist, pd.DataFrame([registro])],
                ignore_index=True
            )
        except FileNotFoundError:
            df_hist = pd.DataFrame([registro])

        df_hist.to_csv(HISTORIAL_FILE, index=False)

        st.success("✅ Turno actualizado y registrado en el historial")
        st.rerun()

# ==================================================
# TAB HISTORIAL — SOLO ADMIN
# ==================================================
if st.session_state.is_admin:
    with tab_historial:
        st.subheader("📜 Historial de cambios del cuadrante")

        try:
            df_hist = pd.read_csv(HISTORIAL_FILE)

            df_hist["fecha_hora"] = pd.to_datetime(df_hist["fecha_hora"])
            df_hist = df_hist.sort_values("fecha_hora", ascending=False)

            st.dataframe(
                df_hist,
                use_container_width=True,
                hide_index=True
            )

        except FileNotFoundError:
            st.info("Todavía no hay cambios registrados en el historial.")
