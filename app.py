import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import base64

def normalizar_nip(nip):
    return str(nip).strip().zfill(6)

def cargar_cuadrante_actual():
    # 1. Cargar cuadrante base
    df = pd.read_csv(BASE_FILE, parse_dates=["fecha"])
    df["nip"] = df["nip"].apply(normalizar_nip)
    df["dia"] = df["fecha"].dt.day

    # 2. Cargar historial si existe
    try:
        hist = pd.read_csv(
            HISTORIAL_FILE,
            parse_dates=["fecha_turno", "fecha_hora"]
        )
    except FileNotFoundError:
        return df

    # Orden cronológico
    hist = hist.sort_values("fecha_hora")

    # Aplicar cambios
    for _, r in hist.iterrows():
        nip = normalizar_nip(r["nip_afectado"])
        fecha_turno = pd.Timestamp(r["fecha_turno"])

        mask = (df["nip"] == nip) & (df["fecha"] == fecha_turno)

        if mask.any():
            df.loc[mask, "turno"] = r["turno_nuevo"]
        else:
            # Intentar obtener datos base del trabajador
            filas_nip = df[df["nip"] == nip]

            if not filas_nip.empty:
                fila_base = filas_nip.iloc[0]
                nombre = fila_base["nombre"]
                categoria = fila_base["categoria"]
                anio = fila_base["anio"]
            else:
                # Último recurso: sacar nombre del historial
                nombre = r.get("nombre_afectado", "")
                categoria = ""
                anio = fecha_turno.year

            nueva = {
                "anio": anio,
                "mes": fecha_turno.month,
                "fecha": fecha_turno,
                "dia": fecha_turno.day,
                "nip": nip,
                "nombre": nombre,
                "categoria": categoria,
                "turno": r["turno_nuevo"],
                "tipo": ""
            }

            df.loc[len(df)] = nueva

    return df

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
st.set_page_config(page_title="Cuadrante 2026", layout="wide")

ADMIN_USER = "ADMIN"
ADMIN_PASS = "PoliciaLocal2021!"
BASE_FILE = "cuadrante_base.csv"
HISTORIAL_FILE = "historial_cambios.csv"
USERS_FILE = "usuarios.csv"
ESCUDO_FILE = "Placa.png"
CABECERA_FILE = "cabecera.png"
HISTORIAL_FILE = "historial_cambios.csv"

# ==================================================
# SESIÓN
# ==================================================
if "nip" not in st.session_state:
    st.session_state.nip = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ==================================================
# CARGA DE DATOS
# ==================================================
df = cargar_cuadrante_actual()
df["dia"] = df["fecha"].dt.day
df["nip"] = df["nip"].apply(normalizar_nip)

usuarios = pd.read_csv(USERS_FILE)
usuarios["nip"] = usuarios["nip"].apply(normalizar_nip)
usuarios["dni"] = usuarios["dni"].astype(str)

# ==================================================
# FUNCIONES AUXILIARES
# ==================================================
def guardar_cambio(df, data_file):
    df.to_csv(data_file, index=False)

# ==================================================
# LOGIN
# ==================================================
if st.session_state.nip is None:
    st.markdown(
        """
        <style>
        body, .stApp { background-color: white; }

        label {
            color: black !important;
            font-weight: 600;
        }

        .login-title {
            color: black;
            font-size: 32px;
            font-weight: 700;
            margin: 20px 0 30px 0;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Escudo perfectamente centrado (FORMA CORRECTA)
    with open(ESCUDO_FILE, "rb") as f:
        escudo_base64 = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin-top:20px;">
            <img src="data:image/png;base64,{escudo_base64}" width="220">
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div class='login-title'>🔐 Acceso al cuadrante</div>", unsafe_allow_html=True)

    usuario = st.text_input("Usuario (NIP)")
    password = st.text_input("Contraseña (DNI)", type="password")

    if st.button("Entrar"):
        # ADMIN
        if usuario == ADMIN_USER and password == ADMIN_PASS:
            st.session_state.nip = ADMIN_USER
            st.session_state.is_admin = True
            st.rerun()

        # USUARIOS NORMALES
        usuario_fmt = usuario.strip().zfill(6)
        fila = usuarios[usuarios["nip"] == usuario_fmt]

        if not fila.empty and fila.iloc[0]["dni"] == password.strip():
            st.session_state.nip = usuario_fmt
            st.session_state.is_admin = False
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

# ==================================================
# CABECERA
# ==================================================
with open(CABECERA_FILE, "rb") as f:
    cabecera = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <div style="width:100%;margin-bottom:10px">
        <img src="data:image/png;base64,{cabecera}" style="width:100%">
    </div>
    """,
    unsafe_allow_html=True
)

st.title("📅 Cuadrante 2026")

if st.button("🚪 Cerrar sesión"):
    st.session_state.usuario = None
    st.rerun()

# ==================================================
# MESES EN CASTELLANO
# ==================================================
MESES = {
    1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
    7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
}

mes = st.selectbox(
    "Selecciona mes",
    sorted(df["mes"].unique()),
    format_func=lambda m: f"{MESES[m]} 2026"
)

df_mes = df[df["mes"] == mes].copy()
df_mes["dia"] = df_mes["fecha"].dt.day

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

    dias = list(tabla.columns)

    def contar_turnos(regex):
        return (
            df_mes[df_mes["turno"].astype(str).str.contains(regex, regex=True)]
            .groupby("dia")
            .size()
            .reindex(dias, fill_value=0)
        )

    conteo_man = contar_turnos(r"^1$|1ex")
    conteo_tar = contar_turnos(r"^2$|2ex")
    conteo_noc = contar_turnos(r"^3$|3ex")

    for idx, fila in tabla.iterrows():
        html += "<tr>"

        if modo_movil:
            html += f"<td>{idx}</td>"
        else:
            nombre, cat, nip = idx
            html += f"<td>{nombre}</td><td>{cat}</td><td>{nip}</td>"

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

    # ----- FILAS RESUMEN (MISMA TABLA) -----
    def fila_resumen(titulo, datos, color):
        fila = "<tr>"
        if modo_movil:
            fila += f"<td><b>{titulo}</b></td>"
        else:
            fila += f"<td colspan='3'><b>{titulo}</b></td>"

        for v in datos:
            fila += (
                f"<td style='background:{color};"
                f"color:#000;font-weight:bold'>"
                f"{v}</td>"
            )
        return fila + "</tr>"

    html += fila_resumen("Mañanas", conteo_man, "#BDD7EE")
    html += fila_resumen("Tardes", conteo_tar, "#FFE699")
    html += fila_resumen("Noches", conteo_noc, "#F8CBAD")

    html += """
        </table>
      </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

    # ---------- RESUMEN POR TURNOS (TABLA SEPARADA) ----------
    st.markdown("### 📊 Resumen diario de turnos")

    dias = sorted(df_mes["dia"].unique())

    def cuenta(turnos):
        return df_mes[
            df_mes["turno"].astype(str).str.contains(turnos, regex=True)
        ].groupby("dia").size().reindex(dias, fill_value=0)

    man = cuenta(r"^1$|^L$|1ex")
    tar = cuenta(r"^2$|2ex")
    noc = cuenta(r"^3$|3ex")

    resumen_html = """
    <table style="border-collapse:collapse;font-size:14px;margin-top:10px">
      <tr>
        <th>Turno</th>
    """

    for d in dias:
        resumen_html += f"<th>{d}</th>"

    resumen_html += "</tr>"

    def fila(nombre, datos, bg):
        fila = f"<tr><td><b>{nombre}</b></td>"
        for v in datos:
            fila += f"<td style='background:{bg};color:#000'>{v}</td>"
        return fila + "</tr>"

    resumen_html += fila("Mañanas", man, "#BDD7EE")
    resumen_html += fila("Tardes", tar, "#FFE699")
    resumen_html += fila("Noches", noc, "#F8CBAD")

    resumen_html += "</table>"

    st.markdown(resumen_html, unsafe_allow_html=True)

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
