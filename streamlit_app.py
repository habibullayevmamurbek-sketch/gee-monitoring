import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap, Draw, MeasureControl, MiniMap, Fullscreen
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
from branca.colormap import linear, StepColormap
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =============================================================================
# SAHLAMA VA KONFIGURATSIYA
# =============================================================================
st.set_page_config(
    page_title="🌾 Xorazm NDVI Monitoring",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stillar
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .info-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-left: 5px solid #1f4e79;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f4e79 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# YORDAMCHI FUNKSIYALAR
# =============================================================================
@st.cache_data(ttl=3600)
def get_xorazm_districts():
    """Xorazm viloyati tumanlari geoJSON ma'lumotlari"""
    # Xorazm viloyati tumanlari koordinatalari
    districts = {
        "Urganch": {"center": [41.55, 60.63], "area": 450, "color": "#FF6B6B"},
        "Xiva": {"center": [41.38, 60.37], "area": 380, "color": "#4ECDC4"},
        "Gurlan": {"center": [41.85, 60.40], "area": 320, "color": "#45B7D1"},
        "Shovot": {"center": [41.65, 60.30], "area": 290, "color": "#96CEB4"},
        "Yangiariq": {"center": [41.30, 60.55], "area": 410, "color": "#FFEAA7"},
        "Yangibozor": {"center": [41.73, 60.55], "area": 350, "color": "#DDA0DD"},
        "Xonqa": {"center": [41.47, 60.78], "area": 270, "color": "#98D8C8"},
        "Bog'ot": {"center": [41.35, 60.85], "area": 310, "color": "#F7DC6F"},
        "Tuproqqal'a": {"center": [41.75, 61.15], "area": 520, "color": "#BB8FCE"},
        "Qo'rg'ontepa": {"center": [41.25, 61.30], "area": 440, "color": "#85C1E9"},
    }
    return districts
