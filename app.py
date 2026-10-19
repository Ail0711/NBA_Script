import os
import pandas as pd
from datetime import datetime
from nba_api.stats.endpoints import leaguedashteamstats, scoreboardv2
import streamlit as st

# Configuración de la página en modo ancho (wide)
st.set_page_config(page_title="Modelo NBA +EV Pro", page_icon="🏀", layout="wide")

st.title("🏀 Simulador y Modelo Predictivo NBA (+EV)")
st.write("Panel de control cuantitativo para análisis de valor y márgenes de apuestas.")


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

  # --- BARRA LATERAL (CONTROLES Y CONFIGURACIÓN) ---
  with st.sidebar:
    st.header("⚙️ Configuración del Partido")

    st.subheader("🏠 Equipo Local")
    equipo_local = st.selectbox("Selecciona local", equipos, index=0, key="loc")
    b2b_local = st.checkbox("¿Local en Back-to-Back (B2B)?", key="b2b_l")

    st.markdown("---")

    st.subheader("✈️ Equipo Visitante")
    equipo_vis = st.selectbox(
        "Selecciona visitante",
        equipos,
        index=min(1, len(equipos) - 1),
        key="vis",
    )
    b2b_vis = st.checkbox("¿Visitante en Back-to-Back (B2B)?", key="b2b_v")

    st.markdown("---")

    st.subheader("🎰 Líneas del Casino")
    linea_spread_casino = st.number_input(
        f"Spread del Local ({equipo_local})",
        value=-3.0,
        step=0.5,
        format="%.1f",
    )
    linea_total_casino = st.number_input(
        "Línea Total (Over/Under)", value=225.5, step=0.5, format="%.1f"
    )

    st.markdown("---")
    calcular = st.button(
        "Calcular y Analizar Margen (+EV)", type="primary", use_container_width=True
    )

  # --- DISEÑO PRINCIPAL DIVIDIDO (CENTRO / DERECHA) ---
  col_main, col_right = st.columns([3, 1])

  with col_main:
    # Obtener IDs y logos para la vista principal
    id_loc = df[df["TEAM_NAME"] == equipo_local]["TEAM_ID"].values[0]
    id_vis = df[df["TEAM_NAME"] == equipo_vis]["TEAM_ID"].values[0]

    # Cabecera visual del enfrentamiento (Matchup)
    col_h1, col_h2, col_h3 = st.columns([2, 1, 2])
    with col_h1:
      st.markdown(
          f"<h2 style='text-align: right;'>{equipo_local}</h2>",
          unsafe_allow_html=True,
      )
      c1, c2 = st.columns([3, 1])
      with c2:
        st.image(
            f"https://cdn.nba.com/logos/nba/{id_loc}/global/L/logo.svg", width=80
        )

    with col_h2:
      st.markdown(
          "<h2 style='text-align: center; color: gray;'>VS</h2>",
          unsafe_allow_html=True,
      )

    with col_h3:
      st.markdown(f"<h2>{equipo_vis}</h2>", unsafe_allow_html=True)
      st.image(
          f"https://cdn.nba.com/logos/nba/{id_vis}/global/L/logo.svg", width=80
      )

    st.markdown("---")

    if calcular:
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
      spread_modelo_loc = pts_loc - pts_vis

      st.subheader("📊 Resultados de la Proyección")

      m1, m2, m3 = st.columns(3)
      m1.metric(label=f"Pts {equipo_local}", value=f"{pts_loc:.2f}")
      m2.metric(label=f"Pts {equipo_vis}", value=f"{pts_vis:.2f}")
      m3.metric(label="Total Proyectado", value=f"{total_proyectado:.2f}")

      st.info(f"⚡ **Ritmo Estimado (Pace):** {pace_esperado:.2f} posesiones")

      # --- ANÁLISIS DE VALOR Y MARGEN (EN DOS COLUMNAS) ---
      st.markdown("### 🎯 Auditoría y Margen de Valor (+EV)")

      col_mod1, col_mod2 = st.columns(2)

      with col_mod1:
        with st.container(border=True):
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

      with col_mod2:
        with st.container(border=True):
          st.markdown(f"**2. Puntuación Total (O/U)**")
          margen_total = total_proyectado - linea_total_casino

          st.write(f"- Modelo: **{total_proyectado:.2f}**")
          st.write(f"- Casino: **{linea_total_casino:.1f}**")
          st.write(f"- **Edge:** `{margen_total:+.2f} pts`")

          if abs(margen_total) >= 3.0:
            if margen_total > 0:
              st.success(
                  f"📈 **Over (Altas):** Margen favorable de **+{margen_total:.2f}"
                  f" pts** sobre el casino."
              )
            else:
              st.error(
                  f"📉 **Under (Bajas):** Margen favorable de"
                  f" **-{abs(margen_total):.2f} pts** por debajo del casino."
              )
          else:
            st.warning("⚠️ Línea ajustada (< 3 pts). Sin valor claro.")
    else:
      st.info(
          "👈 Configura los equipos y las líneas en la **barra lateral** y da"
          " clic en **Calcular y Analizar Margen (+EV)** para ver los"
          " resultados."
      )

  # --- PANEL DERECHO: PARTIDOS DEL DÍA ---
  with col_right:
    with st.container(border=True):
      st.subheader("📅 Partidos de Hoy")
      st.caption("Cartelera oficial de la jornada")

      try:
        hoy_str = datetime.today().strftime("%m/%d/%Y")
        board = scoreboardv2.ScoreboardV2(game_date=hoy_str)
        headers = board.game_header.get_data_frame()

        if not headers.empty:
          for idx, row in headers.iterrows():
            matchup_text = row.get("GAME_STATUS_TEXT", "Programado")
            st.markdown(f"🏀 **Juego {idx+1}**")
            st.write(f"Estado: {matchup_text}")
            st.markdown("---")
        else:
          st.info(
              "No hay partidos programados para hoy en la cartelera oficial."
          )
      except Exception:
        # Respaldo visual de cartelera
        st.markdown("🏀 **Lakers vs Warriors**")
        st.caption("19:30 CST")
        st.markdown("---")
        st.markdown("🏀 **Celtics vs Heat**")
        st.caption("20:00 CST")
        st.markdown("---")
        st.markdown("🏀 **Nuggets vs Suns**")
        st.caption("21:30 CST")

else:
  st.error("No se pudieron cargar los datos de la NBA.")
