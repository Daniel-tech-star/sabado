import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO
import xlsxwriter

st.set_page_config(page_title="Autoevaluación & Plan de Carrera", layout="wide")

# ------------------------------------------------------------------
# 1. CARGA DE DATOS BASE
# ------------------------------------------------------------------
FILE_BASE = "Valoracion_Jobs.xlsx"

@st.cache_data(show_spinner=True)
def load_base(path):
    df_comp = pd.read_excel(path, sheet_name="Competencias")
    return df_comp

try:
    df_comp = load_base(FILE_BASE)
except FileNotFoundError:
    st.error("⚠️ No se encontró 'Valoracion_Jobs.xlsx'. Sube el archivo al repositorio de la app.")
    st.stop()

competencias_cols = df_comp.columns[3:11].tolist()

# ------------------------------------------------------------------
# 2. MAPA DE COMPORTAMIENTOS
# ------------------------------------------------------------------
behaviors_map = {
    "Conocimientos técnicos": [],
    "Desarrollar nuestro negocio": [
        "Emprender, buscar y encontrar opciones mejores",
        "Hacer crecer el negocio",
        "Cumplir objetivos en el largo plazo",
        "Tomar decisiones",
        "Priorizar y decidir con velocidad",
        "Aplicar pensamiento estratégico y crear planes de negocio versátiles",
        "Usar datos para tomar decisiones",
    ],
    "Desarrollarse y contribuir al desarrollo de otr@s": [
        "Desarrollar conocimiento y nuevas habilidades",
        "Nutrir el talento",
        "Hacer crecer a los demás",
        "Estar disponible y accesible",
        "Hacer mentoring/coaching para maximizar el desempeño de los demás",
        "Asegurar la sucesión",
    ],
    "Navegar en lo desconocido": [
        "Buscar oportunidades y actuar",
        "Cuidar de la salud y el bienestar para conseguir un negocio sostenible",
        "Equilibrar la carga de trabajo",
        "Agradecer y celebrar con el equipo",
    ],
    "Generar resultados": [
        "Conseguir objetivos",
        "Pasión por los clientes y la decoración en el hogar",
        "Aplicar datos en el trabajo diario",
        "Simplificar y reducir costes, residuos y recursos para generar beneficios",
        "Hacer cumplir a los demás compromisos adquiridos",
        "Reconocer talentos",
        "Usar y hacer crecer el talento",
    ],
    "Comunicar con impacto": [
        "Comunicar de forma directa e inspiradora",
        "Dialogar con los demás",
        "Influir y hacer que las cosas sucedan",
        "Hacer que los demás entiendan su contribución en las estrategias de negocio",
    ],
    "Colaborar y co-crear": [
        "Crear equipos de alto rendimiento",
        "Hacer colaborar diferentes equipos, funciones, niveles, identidades y entornos",
    ],
    "Liderar con el ejemplo": [
        "Hacer que los demás lideren",
        "Hacer que la cultura y los valores sean parte del desempeño",
    ],
}

def behaviors_for_comp(col_name):
    clean_name = re.sub(r"^\d+\.\s*", "", col_name).strip()
    return behaviors_map.get(clean_name, [])

# ------------------------------------------------------------------
# 3. ENCABEZADO CON IMAGEN
# ------------------------------------------------------------------
col1, col2 = st.columns([1, 8])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135767.png", width=80)
with col2:
    st.title("Autoevaluación de Competencias y Comportamientos")

# ------------------------------------------------------------------
# 4. FORMULARIO DE AUTOEVALUACIÓN
# ------------------------------------------------------------------
nombre = st.text_input("Nombre completo")
areas_unique = sorted(df_comp["Area"].dropna().unique())
area_sel = st.selectbox("Área", ["-- Selecciona --"] + areas_unique)
puestos_sel = sorted(df_comp[df_comp["Area"] == area_sel]["Job Title"].unique()) if area_sel != "-- Selecciona --" else []
puesto = st.selectbox("Puesto actual", ["-- Selecciona --"] + puestos_sel)

# ------------------------------------------------------------------
# 5. COMPETENCIAS
# ------------------------------------------------------------------
st.header("1️⃣ Reparte 100 puntos entre las 8 competencias")
cols = st.columns(4)
comp_values = {comp: st.number_input(comp, 0, 100, 0, 1, key=f"comp_{i}") for i, comp in enumerate(competencias_cols)}
total_comp = sum(comp_values.values())
st.markdown(f"**Total asignado:** {total_comp} / 100")

# ------------------------------------------------------------------
# 6. COMPORTAMIENTOS
# ------------------------------------------------------------------
st.header("2️⃣ Evalúa los comportamientos (1‑5)")
beh_values = {}
for comp in competencias_cols:
    st.subheader(comp)
    for i, beh in enumerate(behaviors_for_comp(comp)):
        beh_values[beh] = st.slider(beh, 1, 5, 3, key=f"beh_{comp}_{i}")

# ------------------------------------------------------------------
# 7. PLAN DE CARRERA
# ------------------------------------------------------------------
if st.button("Generar plan de carrera"):
    if area_sel == "-- Selecciona --" or puesto == "-- Selecciona --":
        st.error("Selecciona tu área y puesto actual.")
        st.stop()
    if total_comp != 100:
        st.error("Distribuye exactamente 100 puntos entre las competencias.")
        st.stop()
    if not nombre:
        st.error("Por favor, introduce tu nombre.")
        st.stop()

    st.success("✅ Plan de carrera generado")

    df_persona = pd.DataFrame({"Competencia": list(comp_values.keys()), "Valor": list(comp_values.values())})
    df_puestos = df_comp.copy()

    resultados = []
    for idx, row in df_puestos.iterrows():
        comp_puesto = row[competencias_cols]
        gap_comp = np.linalg.norm(df_persona["Valor"] - comp_puesto)

        gap_beh = 0
        total_beh = 0
        for comp in competencias_cols:
            for beh in behaviors_for_comp(comp):
                val_persona = beh_values.get(beh, 3)
                val_ideal = 5
                gap_beh += abs(val_persona - val_ideal)
                total_beh += 1

        gap_total = 0.7 * gap_comp + 0.3 * (gap_beh / total_beh if total_beh > 0 else 0)

        resultados.append({
            "Job Title": row["Job Title"],
            "Area": row["Area"],
            "IPE": row.get("IPE", "N/A"),
            "Gap Total": round(gap_total, 2)
        })

    df_resultados = pd.DataFrame(resultados).sort_values("Gap Total")
    st.subheader("🔍 Resultados del Plan de Carrera")
    st.dataframe(df_resultados, use_container_width=True)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_resultados.to_excel(writer, index=False, sheet_name="Plan de Carrera")
    st.download_button("📥 Descargar plan en Excel", data=buffer.getvalue(), file_name="plan_carrera.xlsx")
