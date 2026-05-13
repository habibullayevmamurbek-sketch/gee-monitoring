import streamlit as st
import folium
from streamlit_folium import folium_static
import numpy as np

# 1. Sahifa sozlamalari
st.set_page_config(page_title="Gurlan NDVI Monitoring (No GEE)", layout="wide")
st.title("🛰️ Gurlan tumani: Avtonom Monitoring Tizimi")

# 2. Sidebar sozlamalari
st.sidebar.header("Sozlamalar")
year = st.sidebar.slider("Yilni tanlang:", 2015, 2024, 2023)
month = st.sidebar.selectbox("Oyni tanlang:", ["Aprel", "May", "Iyun", "Iyul"])
crop_type = st.sidebar.selectbox("Mahsulot turi:", ["Bug'doy", "Paxta", "Galla", "Barchasi"])

# 3. Gurlan tumani markazi koordinatalari
gurlan_center = [41.844, 60.575]

# 4. Xaritani yaratish
m = folium.Map(location=gurlan_center, zoom_start=12, tiles="cartodbpositron")

# 5. GEE-siz "NDVI" effektini yaratish (Simulyatsiya)
# Bu qismda biz tuman hududiga rangli qatlam qo'shamiz
def add_simulated_ndvi(m, crop):
    # Simulyatsiya uchun ranglar
    colors = {
        "Bug'doy": "#2ecc71", # Yashil
        "Paxta": "#f1c40f",   # Sariq
        "Galla": "#27ae60",   # To'q yashil
        "Barchasi": "#e67e22" # To'q sariq
    }
    
    # Tuman hududini belgilash (Polygon)
    gurlan_poly = [
        [41.80, 60.50], [41.90, 60.50], 
        [41.92, 60.65], [41.80, 60.65]
    ]
    
    # Xaritaga rangli hududni qo'shish
    folium.Polygon(
        locations=gurlan_poly,
        color=colors.get(crop, "green"),
        fill=True,
        fill_color=colors.get(crop, "green"),
        fill_opacity=0.4,
        popup=f"Gurlan tumani: {crop} maydoni ({year}-yil)"
    ).add_to(m)

# 6. Natijani chiqarish
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("🗺️ Vizualizatsiya")
    add_simulated_ndvi(m, crop_type)
    folium_static(m)

with col2:
    st.subheader("📊 Statistika")
    # Tasodifiy ko'rsatkichlar (GEE-siz bo'lgani uchun)
    sim_ndvi = np.random.uniform(0.3, 0.7)
    st.metric(label="O'rtacha NDVI", value=f"{sim_ndvi:.2f}")
    st.info(f"Hozirda {month} oyi uchun {crop_type} qatlami ko'rsatilmoqda.")

st.warning("⚠️ Diqqat: Bu xarita Google Earth Engine-siz (Offline modda) ishlamoqda. Haqiqiy sun'iy yo'ldosh ma'lumotlari uchun GEE kalitini sozlashingiz kerak.")
