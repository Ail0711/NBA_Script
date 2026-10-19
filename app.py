import os
import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats
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


# Cargar los datos (busca el archivo o lo descarga automáticamente si no existe)
@st.cache_data
def obtener_o_cargar_datos():
  archivo_csv = "nba_stats_2025-26.csv"

  # Si el archivo ya está en el repositorio, lo leemos
  if os.path.exists(archivo_csv):
    return pd.read_csv(archivo_csv)

  # Si por alguna razón no está, lo descargamos al vuelo con la API
  try:
    team_stats = leaguedashteamstats.LeagueDashTeamStats(
        season="2025-26", measure_type_detailed_defense="Advanced"
    )
    df = team_stats.get_data_frames()[0]
    columnas_clave = [
        "TEAM_ID",
        "TEAM_NAME",
        "GP",
        "W",
        "L",
        "OFF_RATING",
        "DEF_RATING",
        "NET_RATING",
        "PACE",
    ]
    df_filtrado = df[columnas_clave]
    df_filtrado.to_csv(archivo_csv, index=False)
    return df_filtrado
  except Exception as e:
    return None


df = obtener_o_cargar_datos()

if df is not None:
  equipos = sorted(df["TEAM_NAME"].unique())

  col1, col2 = st.columns(2)

  with col1:
    st.subheader("Equipo Local")
    equipo_local = st.selectbox("Selecciona local", equipos, index=0, key="loc")

    # Obtener el TEAM_ID del local para su escudo
    id_loc = df[df["TEAM_NAME"] == equipo_local]["TEAM_ID"].values[0]
    # URL oficial del escudo de la NBA usando el ID
    logo_loc = f"https://cdn.nba.com/logos/nba/{id_loc}/global/L/logo.svg"
    st.image(logo_loc, width=100)

    b2b_local = st.checkbox("¿Local en Back-to-Back (B2B)?", key="b2b_l")

  with col2:
    st.subheader("Equipo Visitante")
    equipo_vis = st.selectbox(
        "Selecciona visitante",
        equipos,
        index=min(1, len(equipos) - 1),
        key="vis",
    )

    # Obtener el TEAM_ID del visitante para su escudo
    id_vis = df[df["TEAM_NAME"] == equipo_vis]["TEAM_ID"].values[0]
    logo_vis = f"https://cdn.nba.com/logos/nba/{id_vis}/global/L/logo.svg"
    st.image(logo_vis, width=100)

    b2b_vis = st.checkbox("¿Visitante en Back-to-Back (B2B)?", key="b2b_v")
  st.markdown("---")

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

    if b2b_local:
      drtg_loc *= 1.02
    if b2b_vis:
      drtg_vis *= 1.02

    liga_pace = df["PACE"].mean()
    liga_ortg = df["OFF_RATING"].mean()

    pace_esperado = (pace_loc * pace_vis) / liga_pace
    pts_loc = (ortg_loc * drtg_vis / liga_ortg) * (pace_esperado / 100)
    pts_vis = (ortg_vis * drtg_loc / liga_ortg) * (pace_esperado / 100)

    ventaja_localia = 2.5
    pts_loc += ventaja_localia / 2
    pts_vis -= ventaja_localia / 2

    total_proyectado = pts_loc + pts_vis
    spread_loc = pts_loc - pts_vis

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
      "No se pudieron cargar los datos de la NBA. Revisa la conexión con la"
      " API."
  )
