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
