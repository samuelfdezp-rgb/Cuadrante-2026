import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
st.set_page_config(page_title="Cuadrante 2026", layout="wide")

ADMIN_USER = "ADMIN"
ADMIN_PASS = "PoliciaLocal2021!"
DATA_FILE = "cuadrante_2026.csv"
USERS_FILE = "usuarios.csv"
ESCUDO_FILE = "Placa.png"

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
df = pd.read_csv(DATA_FILE, parse_dates=["fecha"])
df["dia"] = df["fecha"].dt.day
df["nip"] = df["nip"].astype(str)

usuarios = pd.read_csv(USERS_FILE)
usuarios["nip"] = usuarios["nip"].astype(str)
usuarios["dni"] = usuarios["dni"].astype(str)

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

    # Escudo centrado (FORMA CORRECTA)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(ESCUDO_FILE, width=220)

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
# CABECERA POST LOGIN
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
festivos = {date(2026,1,1), date(2026,1,6)}
def es_especial(f): return f in festivos or f.weekday()==6

# ==================================================
# ESTILO TURNOS
# ==================================================
def estilo_turno(t):
    if pd.isna(t): return "#fff","#000",""
    t=str(t)

    if t.lower()=="perm": t="Perm"
    if t.lower()=="baja": t="BAJA"

    dobles_gris = ["1y2","1y3","2y3"]
    if t in dobles_gris:
        return "#DBDBDB","#FF0000","font-weight:bold;"

    if "ex" in t:
        return "#00B050","#FF0000","font-weight:bold;"

    colores={
        "1":("#BDD7EE","#0070C0",""),
        "2":("#FFE699","#0070C0",""),
        "3":("#F8CBAD","#FF0000",""),
        "D":("#C6E0B4","#00B050",""),
        "Dc":("#C6E0B4","#00B050",""),
        "Dcc":("#C6E0B4","#00B050",""),
        "Dcv":("#C6E0B4","#00B050",""),
        "Dcj":("#C6E0B4","#00B050",""),
        "Dct":("#C6E0B4","#00B050",""),
        "Ts":("#FFFFFF","#FF0000","font-weight:bold;"),
        "Perm":("#FFFFFF","#FF0000","font-weight:bold;"),
        "AP":("#FFFFFF","#0070C0","font-weight:bold;"),
        "Vac":("#FFFFFF","#FF0000","font-weight:bold;font-style:italic;"),
        "BAJA":("#FFFFFF","#FF0000","font-weight:bold;"),
        "L":("#BDD7EE","#0070C0",""),
    }
    return colores.get(t,("#fff","#000",""))

# ==================================================
# PESTAÑAS
# ==================================================
tab_general, tab_mis = st.tabs(["📋 Cuadrante general","📆 Mis turnos"])

# ==================================================
# TAB GENERAL
# ==================================================
with tab_general:
    orden = df_mes[["nombre","categoria","nip"]].drop_duplicates()

    tabla = df_mes.pivot_table(
        index=["nombre","categoria","nip"],
        columns="dia",
        values="turno",
        aggfunc="first"
    ).reindex(pd.MultiIndex.from_frame(orden))

    html = """
    <style>
    table{border-collapse:collapse;font-size:12px}
    th,td{border:1px solid #000;padding:3px;white-space:nowrap}
    th{text-align:center;font-weight:bold}
    </style>
    <div style="overflow:auto;max-height:80vh">
    <table>
    <tr>
    <th>Nombre y Apellidos</th><th>Categoría</th><th>NIP</th>
    """

    for d in tabla.columns:
        f=date(2026,mes,d)
        if es_especial(f):
            html+=f"<th style='background:#92D050;color:#FF0000'>{d}</th>"
        else:
            html+=f"<th>{d}</th>"
    html+="</tr>"

    for (n,c,nip),fila in tabla.iterrows():
        html+=f"<tr><td>{n}</td><td>{c}</td><td>{nip}</td>"
        for v in fila:
            bg,fg,extra=estilo_turno(v)
            txt="" if pd.isna(v) else v
            html+=f"<td style='background:{bg};color:{fg};text-align:center;{extra}'>{txt}</td>"
        html+="</tr>"

    # ================= RESUMEN =================
    resumen={d:{"1":0,"2":0,"3":0} for d in tabla.columns}

    def contar(t):
        if pd.isna(t): return []
        t=str(t)
        excluir=["D","Dc","Dcc","Dcv","Dcj","Dct","Vac","Perm","AP","Ts","BAJA","L"]
        if any(x in t for x in excluir): return []
        t=t.replace("ex","")
        if "y" in t: return t.split("y")
        if "|" in t: return t.split("|")
        return [t]

    for _,fila in tabla.iterrows():
        for d,t in fila.items():
            for p in contar(t):
                if p in resumen[d]: resumen[d][p]+=1

    for label,color,key in [
        ("Mañanas","#BDD7EE","1"),
        ("Tardes","#FFE699","2"),
        ("Noches","#F8CBAD","3")
    ]:
        html+=f"<tr><td colspan='3' style='font-weight:bold;background:{color}'>{label}</td>"
        for d in tabla.columns:
            html+=f"<td style='background:{color};text-align:center;font-weight:bold'>{resumen[d][key]}</td>"
        html+="</tr>"

    html+="</table></div>"
    st.markdown(html,unsafe_allow_html=True)

# ==================================================
# TAB MIS TURNOS
# ==================================================
with tab_mis:
    df_u=df_mes[df_mes["nip"]==st.session_state.usuario]
    cal=calendar.Calendar()

    NOMBRES={
        "1":"Mañana","2":"Tarde","3":"Noche","D":"Descanso",
        "1ex":"Mañana extra","2ex":"Tarde extra","3ex":"Noche extra"
    }

    for semana in cal.monthdatescalendar(2026,mes):
        cols=st.columns(7)
        for i,d in enumerate(semana):
            with cols[i]:
                if d.month!=mes: st.write(""); continue
                fila=df_u[df_u["fecha"]==pd.Timestamp(d)]
                html=f"<div style='border:1px solid #aaa;border-radius:6px'>"
                html+=f"<div style='text-align:center;font-weight:bold'>{d.day}</div>"
                if not fila.empty:
                    t=fila.iloc[0]["turno"]
                    partes=contar(t)
                    for p in partes:
                        bg,fg,_=estilo_turno(p)
                        html+=f"<div style='background:{bg};color:{fg};text-align:center'>{NOMBRES.get(p,p)}</div>"
                html+="</div>"
                st.markdown(html,unsafe_allow_html=True)
