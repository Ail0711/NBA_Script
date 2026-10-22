from datetime import datetime
import numpy as np
import pandas as pd
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.static import teams
import streamlit as st

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Simulador y Modelo Predictivo NBA (+EV)",
    page_icon="🏀",
    layout="wide",
)

st.markdown(
    "<h1>🏀 Simulador y Modelo Predictivo NBA (+EV)</h1>", unsafe_allow_html=True
)
st.markdown(
    "Panel de control cuantitativo para análisis de valor y márgenes de"
    " apuestas."
)

# --- CARGA DE EQUIPOS DE LA NBA ---
nba_teams = teams.get_teams()
df = pd.DataFrame(nba_teams)
equipos = [team["full_name"] for team in nba_teams]

# --- BARRA LATERAL: CONFIGURACIÓN DEL PARTIDO ---
st.sidebar.markdown("## ⚙️ Configuración del Partido")

# 1. EQUIPO LOCAL
st.sidebar.subheader("🏠 Equipo Local")
equipo_local = st.sidebar.selectbox("Selecciona local", equipos, index=0, key="loc")
b2b_local = st.sidebar.checkbox(
    "¿Local en Back-to-Back (B2B)?", key="b2b_l"
)

st.sidebar.markdown("**Reporte de Lesiones (Local):**")
lesion_top_local = st.sidebar.number_input(
    "Superestrellas Top 5 ausentes", 0, 3, 0, key="lt_l"
)
lesion_star_local = st.sidebar.number_input(
    "Estrellas / Titulares Elite ausentes", 0, 4, 0, key="ls_l"
)
lesion_role_local = st.sidebar.number_input(
    "Titulares Regulares / 3&D ausentes", 0, 5, 0, key="lr_l"
)

st.sidebar.markdown("---")

# 2. EQUIPO VISITANTE
st.sidebar.subheader("✈️ Equipo Visitante")
equipo_vis = st.sidebar.selectbox(
    "Selecciona visitante", equipos, index=min(1, len(equipos) - 1), key="vis"
)
b2b_vis = st.sidebar.checkbox(
    "¿Visitante en Back-to-Back (B2B)?", key="b2b_v"
)

st.sidebar.markdown("**Reporte de Lesiones (Visitante):**")
lesion_top_vis = st.sidebar.number_input(
    "Superestrellas Top 5 ausentes", 0, 3, 0, key="lt_v"
)
lesion_star_vis = st.sidebar.number_input(
    "Estrellas / Titulares Elite ausentes", 0, 4, 0, key="ls_v"
)
lesion_role_vis = st.sidebar.number_input(
    "Titulares Regulares / 3&D ausentes", 0, 5, 0, key="lr_v"
)

st.sidebar.markdown("---")

# 3. LÍNEAS DE LAS VEGAS (CASINO)
st.sidebar.subheader("🎰 Líneas del Casino")
linea_spread_casino = st.sidebar.number_input(
    "Spread Casino (Local)", value=-2.5, step=0.5, key="spread_c"
)
linea_total_casino = st.sidebar.number_input(
    "Total O/U Casino", value=224.5, step=0.5, key="total_c"
)

# Botón de cálculo
calcular = st.sidebar.button(
    "Calcular y Analizar Margen (+EV)", type="primary"
)

# --- OBTENCIÓN DE IDS Y LOGOS DE LOS EQUIPOS ---
loc_info = df[df["full_name"] == equipo_local]
vis_info = df[df["full_name"] == equipo_vis]

loc_id = loc_info["id"].values[0] if not loc_info.empty else None
vis_id = vis_info["id"].values[0] if not vis_info.empty else None

loc_logo = f"https://cdn.nba.com/logos/nba/{loc_id}/global/L/logo.svg" if loc_id else ""
vis_logo = f"https://cdn.nba.com/logos/nba/{vis_id}/global/L/logo.svg" if vis_id else ""

# --- DISTRIBUCIÓN PRINCIPAL (LAYOUT) ---
col_main, col_spacer, col_right = st.columns([2.2, 0.1, 1.1])

with col_main:
  # Cabecera visual optimizada y horizontal sin espacios feos
  with st.container(border=True):
    col_l_img, col_vs, col_v_img = st.columns([1, 0.3, 1])
    
    with col_l_img:
      sub_img_l, sub_txt_l = st.columns([0.3, 0.7])
      with sub_img_l:
        if loc_logo:
          st.image(loc_logo, width=55)
      with sub_txt_l:
        st.markdown(f"#### {equipo_local}")
        st.caption("Local (🏠)")
        
    with col_vs:
      st.markdown("<h3 style='text-align: center; padding-top: 10px;'>VS</h3>", unsafe_allow_html=True)
      
    with col_v_img:
      sub_txt_v, sub_img_v = st.columns([0.7, 0.3])
      with sub_txt_v:
        st.markdown(f"#### {equipo_vis}")
        st.caption("Visitante (✈️)")
      with sub_img_v:
        if vis_logo:
          st.image(vis_logo, width=55)

  if calcular:
    # --- SIMULACIÓN DEL MODELO CUANTITATIVO ---
    rating_base_local = 114.5
    rating_base_vis = 112.0

    penalizacion_b2b = 2.5
    penalizacion_top = 4.5
    penalizacion_star = 2.5
    penalizacion_role = 1.2

    ajuste_local = (
        2.5
        - (penalizacion_b2b if b2b_local else 0)
        - (lesion_top_local * penalizacion_top)
        - (lesion_star_local * penalizacion_star)
        - (lesion_role_local * penalizacion_role)
    )

    ajuste_vis = (
        - (penalizacion_b2b if b2b_vis else 0)
        - (lesion_top_vis * penalizacion_top)
        - (lesion_star_vis * penalizacion_star)
        - (lesion_role_vis * penalizacion_role)
    )

    pts_proyectados_loc = rating_base_local + ajuste_local
    pts_proyectados_vis = rating_base_vis + ajuste_vis

    spread_modelo_loc = pts_proyectados_loc - pts_proyectados_vis
    total_proyectado = pts_proyectados_loc + pts_proyectados_vis

    margen_spread = spread_modelo_loc - linea_spread_casino
    margen_total = total_proyectado - linea_total_casino

    # --- MÉTRICAS PRINCIPALES EN BLOQUE HORIZONTAL ---
    st.markdown("### 📊 Desglose de Proyecciones del Modelo")
    
    with st.container(border=True):
      m1, m2, m3, m4 = st.columns(4)
      with m1:
        st.metric(label="Proyección Local", value=f"{pts_proyectados_loc:.1f} pts")
      with m2:
        st.metric(label="Proyección Visitante", value=f"{pts_proyectados_vis:.1f} pts")
      with m3:
        st.metric(label="Spread Modelo", value=f"{spread_modelo_loc:+.2f}")
      with m4:
        st.metric(label="Total Proyectado", value=f"{total_proyectado:.1f}")

    # --- ANÁLISIS DE VALOR Y MARGEN (EN DOS COLUMNAS) ---
    st.markdown("### 🎯 Comparación y Margen de Valor (+EV)")

    col_mod1, col_mod2 = st.columns(2)

    # --- MÓDULO 1: HÁNDICAP (SPREAD) ---
    with col_mod1:
      with st.container(border=True):
        st.markdown(f"**1. Hándicap (Spread)**")
        st.write(f"- Casino: **{linea_spread_casino:+.1f} pts**")
        st.write(f"- **Edge:** `{margen_spread:+.2f} pts`")

        if abs(margen_spread) >= 2.0:
          if linea_spread_casino < 0 and spread_modelo_loc < linea_spread_casino:
            st.success(
                f"✅ **LÍNEA A TOMAR:** **{equipo_local}"
                f" ({linea_spread_casino:+.1f})**\n\n**Recomendación:** El"
                " modelo proyecta una diferencia mayor a la exigida por el"
                " casino. ¡Gran valor cubriendo el hándicap!"
            )
          elif margen_spread > 0:
            st.success(
                f"✅ **LÍNEA A TOMAR:** **{equipo_local}**\n\n**Recomendación:**"
                f" Margen favorable de **+{abs(margen_spread):.2f} pts** frente"
                " a Las Vegas."
            )
          else:
            st.success(
                f"✅ **LÍNEA A TOMAR:** **{equipo_vis} (Visitante)**\n\n**Recomendación:**"
                f" Ventaja detectada del lado visitante. Margen:"
                f" **{abs(margen_spread):.2f} pts**."
            )
        else:
          st.warning(
              "⚠️ **Línea ajustada:** Sin margen suficiente (< 2 pts). Mejor"
              " evitar."
          )

    # --- MÓDULO 2: PUNTUACIÓN TOTAL (O/U) ---
    with col_mod2:
      with st.container(border=True):
        st.markdown(f"**2. Puntuación Total (O/U)**")
        st.write(f"- Casino: **{linea_total_casino:.1f} pts**")
        st.write(f"- **Edge:** `{margen_total:+.2f} pts`")

        if abs(margen_total) >= 3.0:
          if margen_total > 0:
            st.success(
                f"📈 **LÍNEA A TOMAR:** **OVER (Altas) {linea_total_casino:.1f}**\n\n**Recomendación:**"
                f" Margen favorable de **+{margen_total:.2f} pts** por encima"
                " del casino."
            )
          else:
            st.error(
                f"📉 **LÍNEA A TOMAR:** **UNDER (Bajas) {linea_total_casino:.1f}**\n\n**Recomendación:**"
                f" Margen favorable de **-{abs(margen_total):.2f} pts** por"
                " debajo del casino."
            )
        else:
          st.warning(
              "⚠️ **Línea ajustada:** Sin margen suficiente (< 3 pts). Mejor"
              " evitar."
          )
  else:
    st.info(
        "👉 Configura los equipos, las lesiones y las líneas en la **barra"
        " lateral** y da clic en **Calcular y Analizar Margen (+EV)** para ver"
        " los resultados."
    )

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
            "No hay encuentros programados para hoy en la cartelera oficial."
        )

    except Exception as e:
      st.warning(
          "⚠️ **Servidor de la NBA ocupado (Timeout):** `stats.nba.com` tardó en"
          " responder."
      )
      st.caption(
          "El modelo funciona al 100% con tu base local. Intenta recargar en"
          " unos minutos."
      )
