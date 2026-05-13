import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
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
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# YORDAMCHI FUNKSIYALAR
# =============================================================================
@st.cache_data(ttl=3600)
def get_xorazm_districts():
    """Xorazm viloyati tumanlari"""
    districts = {
        "Urganch": {"center": [41.55, 60.63], "area": 450},
        "Xiva": {"center": [41.38, 60.37], "area": 380},
        "Gurlan": {"center": [41.85, 60.40], "area": 320},
        "Shovot": {"center": [41.65, 60.30], "area": 290},
        "Yangiariq": {"center": [41.30, 60.55], "area": 410},
        "Yangibozor": {"center": [41.73, 60.55], "area": 350},
        "Xonqa": {"center": [41.47, 60.78], "area": 270},
        "Bog'ot": {"center": [41.35, 60.85], "area": 310},
        "Tuproqqal'a": {"center": [41.75, 61.15], "area": 520},
        "Qo'rg'ontepa": {"center": [41.25, 61.30], "area": 440},
    }
    return districts

# =============================================================================
# NDVI SIMULATSIYA
# =============================================================================
def simulate_ndvi(district, yil, oy):
    """Tuman bo'yicha NDVI simulyatsiyasi"""
    base_ndvi = {
        "Urganch": 0.45, "Xiva": 0.42, "Gurlan": 0.48,
        "Shovot": 0.40, "Yangiariq": 0.50, "Yangibozor": 0.44,
        "Xonqa": 0.46, "Bog'ot": 0.38, "Tuproqqal'a": 0.52,
        "Qo'rg'ontepa": 0.47
    }
    
    oy_factor = {
        1: 0.3, 2: 0.35, 3: 0.45, 4: 0.55,
        5: 0.65, 6: 0.75, 7: 0.80, 8: 0.75,
        9: 0.65, 10: 0.50, 11: 0.40, 12: 0.30
    }
    
    base = base_ndvi.get(district, 0.45)
    factor = oy_factor.get(oy, 0.5)
    yil_factor = 1.0 + (yil - 2020) * 0.01
    random_var = np.random.uniform(-0.05, 0.05)
    
    ndvi = base * factor * yil_factor + random_var
    return max(0, min(0.95, ndvi))

# =============================================================================
# ASOSIY ILova
# =============================================================================
def main():
    st.markdown('<p class="main-header">🌾 Xorazm Viloyati NDVI Monitoring</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sun\'iy yo\'ldosh ma\'lumotlari asosida vegetatsiya monitoringi</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Sozlamalar")
        
        tuman = st.selectbox(
            "📍 Tuman tanlang:",
            list(get_xorazm_districts().keys())
        )
        
        yil = st.slider("📅 Yil:", 2020, 2024, 2023)
        
        oy = st.selectbox(
            "📅 Oy:",
            ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
             "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]
        )
        
        st.info("ℹ️ Bu demo versiya. Haqiqiy sun'iy yo'ldosh ma'lumotlari keyinroq qo'shiladi.")
    
    # Asosiy kontent
    oy_raqamlari = {
        "Yanvar": 1, "Fevral": 2, "Mart": 3, "Aprel": 4,
        "May": 5, "Iyun": 6, "Iyul": 7, "Avgust": 8,
        "Sentabr": 9, "Oktabr": 10, "Noyabr": 11, "Dekabr": 12
    }
    oy_raqam = oy_raqamlari[oy]
    
    # NDVI hisoblash
    ndvi_value = simulate_ndvi(tuman, yil, oy_raqam)
    
    # Ko'rsatkichlar
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🌿 NDVI", f"{ndvi_value:.3f}")
    
    with col2:
        if ndvi_value < 0.2:
            holat = "❌ Yomon"
        elif ndvi_value < 0.4:
            holat = "⚠️ O'rta"
        elif ndvi_value < 0.6:
            holat = "🟡 Yaxshi"
        elif ndvi_value < 0.8:
            holat = "🟢 A'lo"
        else:
            holat = "🌳 Eng yaxshi"
        st.metric("📊 Holat", holat)
    
    with col3:
        districts = get_xorazm_districts()
        maydon = districts[tuman]["area"]
        st.metric("📐 Maydon", f"{maydon} km²")
    
    # Grafik
    st.subheader("📈 NDVI Dinamikasi")
    
    # Barcha tumanlar uchun NDVI
    all_ndvi = []
    for dist in districts.keys():
        val = simulate_ndvi(dist, yil, oy_raqam)
        all_ndvi.append({"Tuman": dist, "NDVI": val})
    
    df = pd.DataFrame(all_ndvi)
    
    fig = px.bar(df, x="Tuman", y="NDVI", 
                 color="NDVI", 
                 color_continuous_scale=["red", "yellow", "green"],
                 title=f"{yil}-yil {oy} oy NDVI ko'rsatkichlari")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Xarita (st.map bilan)
    st.subheader("🗺️ Xarita")
    
    map_data = pd.DataFrame([
        {"lat": info["center"][0], "lon": info["center"][1], "tuman": name}
        for name, info in districts.items()
    ])
    
    st.map(map_data, zoom=9)
    
    # Tahlil
    st.subheader("📋 Tahlil")
    st.info(f"""
    **{tuman} tumani, {yil}-yil {oy} oy:**
    - 🌿 NDVI: **{ndvi_value:.3f}**
    - 📊 Holat: **{holat}**
    - 📐 Maydon: **{maydon} km²**
    
    **Tavsiyalar:**
    - {"💧 Sug'orishni oshiring" if ndvi_value < 0.3 else "✅ Sog'lom o'simlik"}
    - {"🌱 O'g'it qo'shing" if ndvi_value < 0.4 else "✅ O'g'it yetarli"}
    """)

if __name__ == "__main__":
    main()
