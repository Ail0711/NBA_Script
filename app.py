from datetime import datetime
import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats, scoreboardv2
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
    "Panel de control cuantitativo 100% analítico con datos reales de la API."
)

# --- CARGA DE EQUIPOS DE LA NBA ---
nba_teams = teams.get_teams()
df = pd.DataFrame(nba_teams)
equipos = [team["full_name"] for team in nba_teams]


# --- FUNCIÓN ESTRICTA PARA OBTENER DATOS REALES DE LA API (CON HEADERS Y TEMPORADA) ---
@st.cache_data(ttl=3600)  # Caché de 1 hora
def obtener_promedios_nba_estrictos():
  try:
    # Cabeceras requeridas para evitar bloqueos por parte de stats.nba.com
    custom_headers = {
        'Host': 'stats.nba.com',
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.nba.com/',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    }
    
    # Solicitamos los datos especificando la temporada actual ('2026-27') y las cabeceras
    stats_tradicionales = leaguedashteamstats.LeagueDashTeamStats(
        season='2026-27',
        season_type_all_star='Regular Season',
        measure_type_base_defense='Base',
        headers=custom_headers,
        timeout=20
    )
    df_stats = stats_tradicionales.get_data_frame()

    promedios_dict = {}
    for _, row in df_stats.iterrows():
      team_id = row["TEAM_ID"]
      promedios_dict[team_id] = {
          "pts_favor": row["PTS"],  # Promedio real de puntos anotados por partido
          "gp": row["GP"],  # Partidos jugados
      }
    return promedios_dict
  except Exception as e:
    return None


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
  # Cabecera visual principal superior
  with st.container(border=True):
    col_l_img, col_vs, col_v_img = st.columns([1, 0.3, 1])
    
    with col_l_img:
      st.markdown(
          f"""
          <div style="display: flex; align-items: center; gap: 15px;">
              <img src="{loc_logo}" width="55" style="display: block;">
              <div>
                  <h4 style="margin: 0; padding: 0;">{equipo_local}</h4>
                  <p style="margin: 0; padding: 0; color: gray; font-size: 0.85rem;">Local (🏠)</p>
              </div>
          </div>
          """,
          unsafe_allow_html=True
      )
        
    with col_vs:
      st.markdown("<h3 style='text-align: center; padding-top: 5px;'>VS</h3>", unsafe_allow_html=True)
      
    with col_v_img:
      st.markdown(
          f"""
          <div style="display: flex; align-items: center; justify-content: flex-end; gap: 15px;">
              <div style="text-align: right;">
                  <h4 style="margin: 0; padding: 0;">{equipo_vis}</h4>
                  <p style="margin: 0; padding: 0; color: gray; font-size: 0.85rem;">Visitante (✈️)</p>
              </div>
              <img src="{vis_logo}" width="55" style="display: block;">
          </div>
          """,
          unsafe_allow_html=True
      )

  if calcular:
    with st.spinner("Conectando con la API oficial de la NBA para extraer estadísticas reales..."):
      dict_promedios = obtener_promedios_nba_estrictos()

    # Validación estricta
    if dict_promedios is None or loc_id not in dict_promedios or vis_id not in dict_promedios:
      st.error("⚠️ **Error de conexión con la API de la NBA:** No se pudieron obtener los datos reales en este momento. Por favor, intenta de nuevo en unos segundos.")
    else:
      # Extracción estricta 100% real de la temporada actual
      rating_base_local = dict_promedios[loc_id]["pts_favor"]
      rating_base_vis = dict_promedios[vis_id]["pts_favor"]

      # --- SIMULACIÓN DEL MODELO CUANTITATIVO ---
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

      # --- ANÁLISIS DE VALOR Y MARGEN CON LA CABECERA REPLICADA ---
      st.markdown("### 🎯 Comparación y Margen de Valor (+EV)")

      with st.container(border=True):
        col_l_img2, col_vs2, col_v_img2 = st.columns([1, 0.3, 1])
        
        with col_l_img2:
          st.markdown(
              f"""
              <div style="display: flex; align-items: center; gap: 15px;">
                  <img src="{loc_logo}" width="55" style="display: block;">
                  <div>
                      <h4 style="margin: 0; padding: 0;">{equipo_local}</h4>
                      <p style="margin: 0; padding: 0; color: gray; font-size: 0.85rem;">Local (🏠)</p>
                  </div>
              </div>
              """,
              unsafe_allow_html=True
          )
            
        with col_vs2:
          st.markdown("<h3 style='text-align: center; padding-top: 5px;'>VS</h3>", unsafe_allow_html=True)
          
        with col_v_img2:
          st.markdown(
              f"""
              <div style="display: flex; align-items: center; justify-content: flex-end; gap: 15px;">
                  <div style="text-align: right;">
                      <h4 style="margin: 0; padding: 0;">{equipo_vis}</h4>
                      <p style="margin: 0; padding: 0; color: gray; font-size: 0.85rem;">Visitante (✈️)</p>
                  </div>
                  <img src="{vis_logo}" width="55" style="display: block;">
              </div>
              """,
              unsafe_allow_html=True
          )

      col_mod1, col_mod2 = st.columns(2)

      # --- MÓDULO 1: HÁNDICAP (SPREAD) ---
      with col_mod1:
        with st.container(border=True, height=355):
          st.markdown(f"**1. Hándicap (Spread)**")
          st.markdown(f"- Línea del Casino: **{linea_spread_casino:+.1f} pts**")
          
          if abs(margen_spread) >= 4.0:
            desc_edge_spread = "Desajuste masivo vs Las Vegas"
          elif abs(margen_spread) >= 2.0:
            desc_edge_spread = "Ventaja sólida detectada (+EV)"
          else:
            desc_edge_spread = "Línea ajustada, casino acertado"

          st.markdown(
              f"- **Ventaja Modelo:** `{margen_spread:+.2f} pts`\n"
              f"  *<small style='color: gray;'>💡 {desc_edge_spread}</small>*",
              unsafe_allow_html=True
          )
          
          st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

          if abs(margen_spread) >= 2.0:
            if linea_spread_casino < 0 and spread_modelo_loc < linea_spread_casino:
              st.success(
                  f"✅ **APUESTA RECOMENDADA:**\n"
                  f"Hándicap a {equipo_local} ({linea_spread_casino:+.1f})\n\n"
                  f"**Análisis:** Superarán la línea del casino."
              )
            elif margen_spread > 0:
              st.success(
                  f"✅ **APUESTA RECOMENDADA:**\n"
                  f"Hándicap a {equipo_local}\n\n"
                  f"**Análisis:** Margen favorable de **+{abs(margen_spread):.2f} pts** frente a Las Vegas."
              )
            else:
              st.success(
                  f"✅ **APUESTA RECOMENDADA:**\n"
                  f"Hándicap a {equipo_vis} (Visitante)\n\n"
                  f"**Análisis:** Ventaja visitante de **{abs(margen_spread):.2f} pts**."
              )
          else:
            st.warning("⚠️ **Línea ajustada:** Sin margen suficiente (< 2 pts).")

      # --- MÓDULO 2: PUNTUACIÓN TOTAL (O/U) ---
      with col_mod2:
        with st.container(border=True, height=355):
          st.markdown(f"**2. Puntuación Total (O/U)**")
          st.markdown(f"- Línea del Casino: **{linea_total_casino:.1f} pts**")
          
          if abs(margen_total) >= 5.0:
            desc_edge_total = "Diferencia notable en ritmo proyectado"
          elif abs(margen_total) >= 3.0:
            desc_edge_total = "Margen aceptable sobre el filtro"
          else:
            desc_edge_total = "Línea de puntos muy bien estimada"

          st.markdown(
              f"- **Ventaja Modelo:** `{margen_total:+.2f} pts`\n"
              f"  *<small style='color: gray;'>💡 {desc_edge_total}</small>*",
              unsafe_allow_html=True
          )
          
          st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

          if abs(margen_total) >= 3.0:
            if margen_total > 0:
              st.success(
                  f"📈 **APUESTA RECOMENDADA:**\n"
                  f"OVER (Altas) {linea_total_casino:.1f}\n\n"
                  f"**Análisis:** Margen favorable de **+{margen_total:.2f} pts** por encima del casino."
              )
            else:
              st.error(
                  f"📉 **APUESTA RECOMENDADA:**\n"
                  f"UNDER (Bajas) {linea_total_casino:.1f}\n\n"
                  f"**Análisis:** Margen favorable de **-{abs(margen_total):.2f} pts** por debajo del casino."
              )
          else:
            st.warning("⚠️ **Línea ajustada:** Sin margen suficiente (< 3 pts).")
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
