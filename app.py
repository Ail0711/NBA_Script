import os
import pandas as pd
from datetime import datetime
from nba_api.stats.endpoints import leaguedashteamstats, scoreboardv2
import streamlit as st
# Configuración inicial
st.set_page_config(page_title="Modelo NBA +EV Pro", page_icon="🏀", layout="wide")

# --- BLOQUE DE DISEÑO CSS PERSONALIZADO ---
st.markdown(
    """
    <style>
    /* Estilo general para las tarjetas/contenedores con borde */
    div[data-testid="stVerticalBlock"] div[data-testid="stContainer"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Personalización de los títulos principales en la barra lateral y cuerpo */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        letter-spacing: -0.5px;
    }

    /* Estilo para los botones principales de acción */
    div.stButton > button:first-child {
        background-color: #238636;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        transition: 0.3s ease;
    }
    
    div.stButton > button:first-child:hover {
        background-color: #2ea043;
        border: none;
    }
    </style>
""",
    unsafe_allow_html=True,
)
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

  # --- BARRA LATERAL (CONTROLES, B2B Y LESIONES) ---
  with st.sidebar:
    st.header("⚙️ Configuración del Partido")

    # 1. EQUIPO LOCAL
    st.subheader("🏠 Equipo Local")
    equipo_local = st.selectbox("Selecciona local", equipos, index=0, key="loc")
    b2b_local = st.checkbox("¿Local en Back-to-Back (B2B)?", key="b2b_l")

    st.markdown("**Reporte de Lesiones (Local):**")
    lesion_top_local = st.number_input(
        "Superestrellas Top 5 ausentes", min_value=0, max_value=3, value=0, key="lt_l"
    )
    lesion_star_local = st.number_input(
        "Estrellas / Titulares Elite ausentes",
        min_value=0,
        max_value=5,
        value=0,
        key="ls_l",
    )
    lesion_role_local = st.number_input(
        "Titulares Regulares / 3&D ausentes",
        min_value=0,
        max_value=5,
        value=0,
        key="lr_l",
    )

    st.markdown("---")

    # 2. EQUIPO VISITANTE
    st.subheader("✈️ Equipo Visitante")
    equipo_vis = st.selectbox(
        "Selecciona visitante",
        equipos,
        index=min(1, len(equipos) - 1),
        key="vis",
    )
    b2b_vis = st.checkbox("¿Visitante en Back-to-Back (B2B)?", key="b2b_v")

    st.markdown("**Reporte de Lesiones (Visitante):**")
    lesion_top_vis = st.number_input(
        "Superestrellas Top 5 ausentes", min_value=0, max_value=3, value=0, key="lt_v"
    )
    lesion_star_vis = st.number_input(
        "Estrellas / Titulares Elite ausentes",
        min_value=0,
        max_value=5,
        value=0,
        key="ls_v",
    )
    lesion_role_vis = st.number_input(
        "Titulares Regulares / 3&D ausentes",
        min_value=0,
        max_value=5,
        value=0,
        key="lr_v",
    )

    st.markdown("---")

    # 3. LÍNEAS DEL CASINO
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

  # --- DISEÑO PRINCIPAL CON ESPACIADOR ---
  col_main, col_spacer, col_right = st.columns([2.7, 0.15, 1.15])

  with col_main:
    with st.container(border=True):
      id_loc = df[df["TEAM_NAME"] == equipo_local]["TEAM_ID"].values[0]
      id_vis = df[df["TEAM_NAME"] == equipo_vis]["TEAM_ID"].values[0]

      col_h1, col_h2, col_h3 = st.columns([2, 1, 2])
      with col_h1:
        st.markdown(
            f"<h3 style='text-align: right; margin-bottom: 0;'>{equipo_local}</h3>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns([3, 1])
        with c2:
          st.image(
              f"https://cdn.nba.com/logos/nba/{id_loc}/global/L/logo.svg",
              width=75,
          )

      with col_h2:
        st.markdown(
            "<h3 style='text-align: center; color: gray; margin-top: 10px;'>"
            "VS</h3>",
            unsafe_allow_html=True,
        )

      with col_h3:
        st.markdown(
            f"<h3 style='text-align: left; margin-bottom: 0;'>{equipo_vis}</h3>",
            unsafe_allow_html=True,
        )
        st.image(
            f"https://cdn.nba.com/logos/nba/{id_vis}/global/L/logo.svg",
            width=75,
        )

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

      # --- AJUSTE POR BACK-TO-BACK ---
      if b2b_local:
        drtg_loc *= 1.02
      if b2b_vis:
        drtg_vis *= 1.02

      # --- AJUSTE MATEMÁTICO POR LESIONES (ACUMULATIVO) ---
      # Descuento porcentual en la eficiencia ofensiva (Offensive Rating)
      descuento_local = (
          (lesion_top_local * 0.09)
          + (lesion_star_local * 0.05)
          + (lesion_role_local * 0.025)
      )
      descuento_vis = (
          (lesion_top_vis * 0.09)
          + (lesion_star_vis * 0.05)
          + (lesion_role_vis * 0.025)
      )

      # Aplicamos el descuento a la ofensiva
      ortg_loc *= 1.0 - min(
          descuento_local, 0.25
      )  # Tope máximo de 25% de caída
      ortg_vis *= 1.0 - min(descuento_vis, 0.25)

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

      st.subheader("📊 Resultados de la Proyección (Con Ajuste de Lesiones)")

      m1, m2, m3 = st.columns(3)
      m1.metric(label=f"Pts {equipo_local}", value=f"{pts_loc:.2f}")
      m2.metric(label=f"Pts {equipo_vis}", value=f"{pts_vis:.2f}")
      m3.metric(label="Total Proyectado", value=f"{total_proyectado:.2f}")

      st.info(f"⚡ **Ritmo Estimado (Pace):** {pace_esperado:.2f} posesiones")

      # --- ANÁLISIS DE VALOR Y MARGEN (TARJETAS PROFESIONALES) ---
    # --- ANÁLISIS DE VALOR Y MARGEN (EN DOS COLUMNAS) ---
st.markdown("### 🎯 Comparación y Margen de Valor (+EV)")

col_mod1, col_mod2 = st.columns(2)

# --- MÓDULO 1: HÁNDICAP (SPREAD) ---
with col_mod1:
    with st.container(border=True):
        st.markdown(f"**1. Hándicap (Spread)**")
        margen_spread = spread_modelo_loc - linea_spread_casino

        st.write(f"- Modelo: **{spread_modelo_loc:+.2f} pts**")
        st.write(f"- Casino: **{linea_spread_casino:+.1f} pts**")
        st.write(f"- **Edge:** `{margen_spread:+.2f} pts`")

        if abs(margen_spread) >= 2.0:
            if linea_spread_casino < 0 and spread_modelo_loc < linea_spread_casino:
                st.success(
                    f"✅ **LÍNEA A TOMAR:** **{equipo_local} ({linea_spread_casino:+.1f})**\n\n"
                    f"**Recomendación:** El modelo proyecta una diferencia mayor a la exigida por el casino. ¡Gran valor cubriendo el hándicap!"
                )
            elif margen_spread > 0:
                st.success(
                    f"✅ **LÍNEA A TOMAR:** **{equipo_local}**\n\n"
                    f"**Recomendación:** Margen favorable de **+{abs(margen_spread):.2f} pts** frente a Las Vegas."
                )
            else:
                st.success(
                    f"✅ **LÍNEA A TOMAR:** **{equipo_vis} (Visitante)**\n\n"
                    f"**Recomendación:** Ventaja detectada del lado visitante. Margen: **{abs(margen_spread):.2f} pts**."
                )
        else:
            st.warning("⚠️ **Línea ajustada:** Sin margen suficiente (< 2 pts). Mejor evitar.")

# --- MÓDULO 2: PUNTUACIÓN TOTAL (O/U) ---
with col_mod2:
    with st.container(border=True):
        st.markdown(f"**2. Puntuación Total (O/U)**")
        margen_total = total_proyectado - linea_total_casino

        st.write(f"- Modelo: **{total_proyectado:.2f} pts**")
        st.write(f"- Casino: **{linea_total_casino:.1f} pts**")
        st.write(f"- **Edge:** `{margen_total:+.2f} pts`")

        if abs(margen_total) >= 3.0:
            if margen_total > 0:
                st.success(
                    f"📈 **LÍNEA A TOMAR:** **OVER (Altas) {linea_total_casino:.1f}**\n\n"
                    f"**Recomendación:** Margen favorable de **+{margen_total:.2f} pts** por encima del casino."
                )
            else:
                st.error(
                    f"📉 **LÍNEA A TOMAR:** **UNDER (Bajas) {linea_total_casino:.1f}**\n\n"
                    f"**Recomendación:** Margen favorable de **-{abs(margen_total):.2f} pts** por debajo del casino."
                )
        else:
            st.warning("⚠️ **Línea ajustada:** Sin margen suficiente (< 3 pts). Mejor evitar.")
            
with col_spacer:
    st.write("")

# --- PANEL DERECHO: PARTIDOS DE HOY ---
with col_right:
    with st.container(border=True):
        st.subheader("📅 Partidos de Hoy")
        st.caption("Cartelera oficial en tiempo real")

        try:
            hoy_str = datetime.today().strftime("%Y-%m-%d")
            board = scoreboardv2.ScoreboardV2(game_date=hoy_str, timeout=10)
            headers = board.game_header.get_data_frame()

            if not headers.empty:
                for idx, row in headers.iterrows():
                    status = row.get("GAME_STATUS_TEXT", "Programado")
                    home_id = row.get("HOME_TEAM_ID")
                    vis_id = row.get("VISITOR_TEAM_ID")

                    home_row = df[df["TEAM_ID"] == home_id]
                    vis_row = df[df["TEAM_ID"] == vis_id]

                    h_name = (
                        home_row["TEAM_NAME"].values[0]
                        if not home_row.empty
                        else f"Equipo {home_id}"
                    )
                    v_name = (
                        vis_row["TEAM_NAME"].values[0]
                        if not vis_row.empty
                        else f"Equipo {vis_id}"
                    )

                    st.markdown(f"🏀 **{v_name} vs {h_name}**")
                    st.caption(f"Estado: {status}")
                    st.markdown("---")
            else:
                st.info(
                    "No hay encuentros programados para hoy en la cartelera"
                    " oficial."
                )

        except Exception as e:
            st.warning(
                "⚠️ **Servidor de la NBA ocupado (Timeout):**"
                " `stats.nba.com` tardó en responder."
            )
            st.caption(
                "El modelo funciona al 100% con tu base local. Intenta recargar"
                " en unos minutos."
            )
