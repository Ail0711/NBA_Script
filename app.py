import os
import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Modelo NBA +EV Pro", page_icon="🏀", layout="centered"
)

st.title("🏀 Simulador y Modelo Predictivo NBA (+EV)")
st.write(
    "Herramienta cuantitativa avanzada para calcular valor, margen y líneas de"
    " apuestas."
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
        f"Spread del Local ({equipo_local}) (Ej: -4.5 o +2.5)",
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

  if st.button("Calcular y Analizar Margen (+EV)", type="primary"):
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
    spread_modelo_loc = (
        pts_loc - pts_vis
    )  # Positivo si el local gana por el modelo

    st.subheader("📊 Resultados de la Proyección")

    m1, m2, m3 = st.columns(3)
    m1.metric(label=f"Pts {equipo_local}", value=f"{pts_loc:.2f}")
    m2.metric(label=f"Pts {equipo_vis}", value=f"{pts_vis:.2f}")
    m3.metric(label="Total Proyectado", value=f"{total_proyectado:.2f}")

    st.info(f"⚡ **Ritmo Estimado (Pace):** {pace_esperado:.2f} posesiones")

   # --- ANÁLISIS DE VALOR Y MARGEN (EN DOS COLUMNAS) ---
    st.markdown("### 🎯 Auditoría y Margen de Valor (+EV)")

    col_mod1, col_mod2 = st.columns(2)

    # --- MÓDULO 1: HÁNDICAP (SPREAD) ---
    with col_mod1:
      st.markdown(f"**1. Hándicap (Spread)**")
      margen_spread = spread_modelo_loc - linea_spread_casino

      st.write(f"- Modelo: **{spread_modelo_loc:+.2f}**")
      st.write(f"- Casino: **{linea_spread_casino:+.1f}**")
      st.write(f"- **Edge:** `{margen_spread:+.2f} pts`")

      if abs(margen_spread) >= 2.0:
        if margen_spread > 0:
          st.success(
              f"✅ **VALOR:** Margen favorable de **+{margen_spread:.2f} pts**"
              f" para ir con **{equipo_local}**."
          )
        else:
          st.success(
              f"✅ **VALOR:** Ventaja detectada del lado visitante/rival."
              f" Margen: **{abs(margen_spread):.2f} pts**."
          )
      else:
        st.warning("⚠️ Sin margen suficiente (< 2 pts).")

# --- MÓDULO 2: TOTALES (OVER / UNDER) ---
    with col_mod2:
      st.markdown(f"**2. Puntuación Total (O/U)**")
      margen_total = total_proyectado - linea_total_casino

      st.write(f"- Modelo: **{total_proyectado:.2f}**")
      st.write(f"- Casino: **{linea_total_casino:.1f}**")
      st.write(f"- **Edge:** `{margen_total:+.2f} pts`")

      if abs(margen_total) >= 3.0:
        if margen_total > 0:
          # Si el margen es positivo, se pinta de VERDE (Over / Altas)
          st.success(
              f"📈 **Over (Altas):** Margen favorable de **+{margen_total:.2f}"
              f" pts** sobre el casino."
          )
        else:
          # Si el margen es negativo, se pinta de ROJO (Under / Bajas)
          st.error(
              f"📉 **Under (Bajas):** Margen favorable de"
              f" **-{abs(margen_total):.2f} pts** por debajo del casino."
          )
      else:
        st.warning("⚠️ Línea ajustada (< 3 pts). Sin valor claro.")
          )
 
          
else:
  st.error("No se pudieron cargar los datos de la NBA.")
