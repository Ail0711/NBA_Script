import os
import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Modelo NBA +EV", page_icon="🏀", layout="centered"
)

st.title("🏀 Simulador y Modelo Predictivo NBA (+EV)")
st.write(
    "Herramienta cuantitativa para comparar proyecciones contra las líneas del"
    " casino."
)


@st.cache_data
def obtener_o_cargar_datos():
  archivo_csv = "nba_stats_2025-26.csv"
  if os.path.exists(archivo_csv):
    return pd.read_csv(archivo_csv)
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
    id_loc = df[df["TEAM_NAME"] == equipo_local]["TEAM_ID"].values[0]
    st.image(
        f"https://cdn.nba.com/logos/nba/{id_loc}/global/L/logo.svg", width=80
    )
    b2b_local = st.checkbox("¿Local en Back-to-Back (B2B)?", key="b2b_l")

  with col2:
    st.subheader("Equipo Visitante")
    equipo_vis = st.selectbox(
        "Selecciona visitante",
        equipos,
        index=min(1, len(equipos) - 1),
        key="vis",
    )
    id_vis = df[df["TEAM_NAME"] == equipo_vis]["TEAM_ID"].values[0]
    st.image(
        f"https://cdn.nba.com/logos/nba/{id_vis}/global/L/logo.svg", width=80
    )
    b2b_vis = st.checkbox("¿Visitante en Back-to-Back (B2B)?", key="b2b_v")

  st.markdown("---")

  # --- SECCIÓN DE LÍNEAS DEL CASINO ---
  st.subheader("🎰 Líneas del Casino (Las Vegas / Casa de Apuestas)")
  col_c1, col_c2 = st.columns(2)
  with col_c1:
    linea_spread_casino = st.number_input(
        f"Spread de {equipo_local} (Ej: -4.5 o +2.5)",
        value=-3.0,
        step=0.5,
        format="%.1f",
    )
  with col_c2:
    linea_total_casino = st.number_input(
        "Línea Total de Puntos (Over/Under)",
        value=225.5,
        step=0.5,
        format="%.1f",
    )

  st.markdown("---")

  if st.button("Calcular y Buscar Valor (+EV)", type="primary"):
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
    # Spread del modelo desde la perspectiva del local (positivo si el modelo ve favorito al local)
    spread_modelo_loc = pts_loc - pts_vis

    st.subheader("📊 Resultados de la Proyección y Comparación")

    m1, m2, m3 = st.columns(3)
    m1.metric(label=f"Pts {equipo_local}", value=f"{pts_loc:.2f}")
    m2.metric(label=f"Pts {equipo_vis}", value=f"{pts_vis:.2f}")
    m3.metric(label="Total Proyectado", value=f"{total_proyectado:.2f}")

    st.info(f"⚡ **Ritmo Estimado (Pace):** {pace_esperado:.2f} posesiones")

    # --- ANÁLISIS DE VALOR (EDGE) ---
    st.markdown("### 🎯 Análisis de Valor contra el Casino")

    # Comparación de Spread: El modelo arroja qué tanto gana el local.
    # Si spread_modelo_loc es +5.0, el modelo cree que gana por 5.
    diferencia_spread = spread_modelo_loc - (-linea_spread_casino)

    st.write(
        f"• **Hándicap del Modelo:** {equipo_local} por"
        f" {spread_modelo_loc:+.2f} pts"
    )
    st.write(
        f"• **Hándicap del Casino:** {equipo_local} con línea en"
        f" {linea_spread_casino:+.1f} pts"
    )

    # Lógica de recomendación simple basada en la diferencia
    if abs(diferencia_spread) >= 2.0:
      if diferencia_spread > 0:
        st.success(
            f"✅ **¡ALERTA DE VALOR (+EV)!** El modelo ve una diferencia de"
            f" {diferencia_spread:.2f} puntos a favor de **{equipo_local}**"
            " respecto a la línea del casino. Podría haber una gran jugada"
            " aquí."
        )
      else:
        st.success(
            f"✅ **¡ALERTA DE VALOR (+EV)!** El modelo considera que la línea"
            f" del casino está desinflada para el visitante (**{equipo_vis}**)."
            f" Diferencia detectada: {abs(diferencia_spread):.2f} puntos."
        )
    else:
      st.warning(
          "⚠️ **Sin valor claro:** La diferencia entre el modelo y la línea del"
          " casino es menor a 2 puntos. El mercado está muy bien medido;"
          " mejor pasar de este partido."
      )

    # Comparación de Totales (Over/Under)
    diferencia_total = total_proyectado - linea_total_casino
    if abs(diferencia_total) >= 3.0:
      if diferencia_total > 0:
        st.info(
            f"📈 **Tendencia Over (Altas):** El modelo proyecta"
            f" {total_proyectado:.2f} puntos frente a los"
            f" {linea_total_casino:.1f} del casino (+{diferencia_total:.2f}"
            " pts de margen)."
        )
      else:
        st.info(
            f"📉 **Tendencia Under (Bajas):** El modelo proyecta"
            f" {total_proyectado:.2f} puntos frente a los"
            f" {linea_total_casino:.1f} del casino"
            f" (-{abs(diferencia_total):.2f} pts de margen)."
        )

else:
  st.error("No se pudieron cargar los datos de la NBA.")
