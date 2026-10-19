import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Modelo NBA +EV", page_icon="🏀", layout="centered"
)

st.title("🏀 Simulador y Modelo Predictivo NBA")
st.write(
    "Herramienta cuantitativa para calcular puntos esperados, ritmos (Pace)"
    " y hándicaps (Spreads)."
)


# Cargar los datos (usamos el CSV que ya generamos)
@st.cache_data
def cargar_datos():
  try:
    # Intentamos cargar la temporada regular o el archivo disponible
    return pd.read_csv("nba_stats_2025-26.csv")
  except:
    try:
      return pd.read_csv("nba_preseason_stats_2026-27.csv")
    except:
      return None


df = cargar_datos()

if df is not None:
  equipos = sorted(df["TEAM_NAME"].unique())

  # Diseño de columnas para la selección de equipos
  col1, col2 = st.columns(2)

  with col1:
    st.subheader("Equipo Local")
    equipo_local = st.selectbox("Selecciona local", equipos, index=0)
    b2b_local = st.checkbox("¿Local en Back-to-Back (B2B)?")

  with col2:
    st.subheader("Equipo Visitante")
    # Seleccionamos por defecto el segundo equipo de la lista
    equipo_vis = st.selectbox(
        "Selecciona visitante", equipos, index=min(1, len(equipos) - 1)
    )
    b2b_vis = st.checkbox("¿Visitante en Back-to-Back (B2B)?")

  st.markdown("---")

  # Botón de cálculo
  if st.button("Calcular Proyección del Partido", type="primary"):
    loc = df[df["TEAM_NAME"] == equipo_local]
    vis = df[df["TEAM_NAME"] == equipo_vis]

    pace_loc, ortg_loc, drtg_loc = (
        loc["PACE"].values[0],
        loc["OFF_RATING"].values[0],
        loc["DEF_RATING"].values[0],
    )
    pace_vis, ortg_vis, drtg_vis = (
        vis["PACE"].values[0],
        vis["OFF_RATING"].values[0],
        vis["DEF_RATING"].values[0],
    )

    # Ajuste por B2B
    if b2b_local:
      drtg_loc *= 1.02
    if b2b_vis:
      drtg_vis *= 1.02

    liga_pace = df["PACE"].mean()
    liga_ortg = df["OFF_RATING"].mean()

    # Motor matemático
    pace_esperado = (pace_loc * pace_vis) / liga_pace
    pts_loc = (ortg_loc * drtg_vis / liga_ortg) * (pace_esperado / 100)
    pts_vis = (ortg_vis * drtg_loc / liga_ortg) * (pace_esperado / 100)

    # Factor de localía (+2.5 puntos repartidos)
    ventaja_localia = 2.5
    pts_loc += ventaja_localia / 2
    pts_vis -= ventaja_localia / 2

    total_proyectado = pts_loc + pts_vis
    spread_loc = pts_loc - pts_vis

    # Mostrar Resultados en Pantalla de forma visual
    st.subheader("📊 Resultados de la Proyección")

    m1, m2, m3 = st.columns(3)
    m1.metric(label=f"Pts {equipo_local}", value=f"{pts_loc:.2f}")
    m2.metric(label=f"Pts {equipo_vis}", value=f"{pts_vis:.2f}")
    m3.metric(label="Total (O/U)", value=f"{total_proyectado:.2f}")

    st.success(
        f"**Spread / Hándicap del Modelo:** {equipo_local} es favorito por"
        f" **{spread_loc:+.2f}** puntos."
    )
    st.info(f"⚡ **Ritmo Esperado (Pace):** {pace_esperado:.2f} posesiones")

else:
  st.error(
      "No se encontró el archivo CSV de estadísticas. Asegúrate de tener tu"
      " archivo en la misma carpeta."
  )
