import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import calendar

# ============================================================
# 1. NASA POWER API (BEPUL, GEEsiz)
# ============================================================

def get_nasa_power_data(lat, lon, start_date, end_date):
    """
    NASA POWER API - bepul, GEEsiz
    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    params = {
        "parameters": "NDVI",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start_date.replace("-", ""),
        "end": end_date.replace("-", ""),
        "format": "JSON"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except Exception as e:
        st.error(f"NASA API xatosi: {str(e)}")
        return None

# ============================================================
# 2. OPEN-METEO API (BEPUL ob-havo)
# ============================================================

def get_openmeteo_data(lat, lon, start_date, end_date):
    """
    Open-Meteo API - bepul ob-havo ma'lumotlari
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_mean", "precipitation_sum", "soil_moisture_0_to_10cm"],
        "timezone": "Asia/Tashkent"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Open-Meteo API xatosi: {str(e)}")
        return None

# ============================================================
# 3. NDVI SIMULATSIYA
# ============================================================

def simulate_ndvi(yil, oy, mahsulot_turi):
    """
    Vegitatsiya indeksini simulyatsiya qilish
    """
    ndvi_base = {
        "Bug'doy": 0.45,
        "Paxta": 0.35,
        "Galla": 0.50,
        "Sabzavot": 0.55,
        "Barchasi": 0.42
    }
    
    oy_factor = {
        1: 0.3,   2: 0.35,  3: 0.45,  4: 0.55,
        5: 0.65,  6: 0.75,  7: 0.80,  8: 0.75,
        9: 0.65,  10: 0.50, 11: 0.40, 12: 0.30
    }
    
    base = ndvi_base.get(mahsulot_turi, 0.42)
    factor = oy_factor.get(oy, 0.5)
    yil_factor = 1.0 + (yil - 2020) * 0.02
    random_var = np.random.uniform(-0.05, 0.05)
    
    ndvi = base * factor * yil_factor + random_var
    return max(0, min(0.95, ndvi))

# ============================================================
# 4. GURLAN TUMANI
# ============================================================

GURLAN_CENTER = {"lat": 41.85, "lon": 60.15, "name": "Gurlan tumani markazi"}

GURLAN_VILLAGES = [
    {"name": "Gurlan shaharchasi", "lat": 41.85, "lon": 60.15},
    {"name": "Xonqa", "lat": 41.87, "lon": 60.12},
    {"name": "Bog'ot", "lat": 41.83, "lon": 60.18},
    {"name": "Yangiariq", "lat": 41.80, "lon": 60.10},
    {"name": "Qizilqum", "lat": 41.90, "lon": 60.20},
]

# ============================================================
# 5. STREAMLIT UI
# ============================================================

st.set_page_config(
    page_title="Gurlan tumani NDVI monitoringi",
    page_icon="🛰️",
    layout="wide"
)

st.title("🛰️ Gurlan tumani: Sun'iy yo'ldosh orqali NDVI monitoringi")
st.markdown("*(GEEsiz versiya - NASA POWER va Open-Meteo API)*")

with st.sidebar:
    st.header("⚙️ Sozlamalar")
    
    yil = st.slider("📅 Yilni tanlang:", 2020, 2024, 2023)
    
    oy = st.selectbox(
        "📅 Oyni tanlang:",
        ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
         "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"],
        index=5
    )
    
    mahsulot = st.selectbox(
        "🌾 Mahsulot turi:",
        ["Bug'doy", "Paxta", "Galla", "Sabzavot", "Barchasi"]
    )
    
    joy = st.selectbox(
        "📍 Joyni tanlang:",
        ["Gurlan tumani markazi"] + [v["name"] for v in GURLAN_VILLAGES]
    )
    
    st.info("ℹ️ Bu demo versiya. Haqiqiy sun'iy yo'ldosh ma'lumotlari keyinroq qo'shiladi.")

# ============================================================
# 6. SANA HISOBLASH
# ============================================================

oy_raqamlari = {
    "Yanvar": 1, "Fevral": 2, "Mart": 3, "Aprel": 4,
    "May": 5, "Iyun": 6, "Iyul": 7, "Avgust": 8,
    "Sentabr": 9, "Oktabr": 10, "Noyabr": 11, "Dekabr": 12
}

oy_raqam = oy_raqamlari[oy]
start_date = f"{yil}-{oy_raqam:02d}-01"
_, kunlar = calendar.monthrange(yil, oy_raqam)
end_date = f"{yil}-{oy_raqam:02d}-{kunlar}"

# ============================================================
# 7. MA'LUMOTLARNI OLISH
# ============================================================

if joy == "Gurlan tumani markazi":
    lat, lon = GURLAN_CENTER["lat"], GURLAN_CENTER["lon"]
else:
    village = next(v for v in GURLAN_VILLAGES if v["name"] == joy)
    lat, lon = village["lat"], village["lon"]

with st.spinner("🛰️ Sun'iy yo'ldosh ma'lumotlari yuklanmoqda..."):
    nasa_data = get_nasa_power_data(lat, lon, start_date, end_date)
    weather_data = get_openmeteo_data(lat, lon, start_date, end_date)

# NDVI qiymatini olish
if nasa_data and 'properties' in nasa_data:
    try:
        ndvi_value = nasa_data['properties']['parameter']['NDVI']['mean']
    except:
        ndvi_value = simulate_ndvi(yil, oy_raqam, mahsulot)
else:
    ndvi_value = simulate_ndvi(yil, oy_raqam, mahsulot)

# ============================================================
# 8. VIZUALIZATSIYA
# ============================================================

st.write(f"📊 **Tanlangan davr:** `{start_date}` dan `{end_date}` gacha")
st.write(f"📍 **Joy:** {joy} ({lat}°N, {lon}°E)")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="🌿 O'rtacha NDVI", value=f"{ndvi_value:.3f}")

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
    
    st.metric(label="📊 Holat", value=holat)

with col3:
    st.metric(label="🌾 Mahsulot", value=mahsulot)

# NDVI shkalasi
st.subheader("🎨 NDVI Shkalasi")

shkala_cols = st.columns(5)
colors = ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#1a9850"]
labels = ["0.0-0.2\nYomon", "0.2-0.4\nO'rta", "0.4-0.6\nYaxshi", "0.6-0.8\nA'lo", "0.8-1.0\nEng yaxshi"]

for i, (col, color, label) in enumerate(zip(shkala_cols, colors, labels)):
    with col:
        st.markdown(
            f"<div style='background: {color}; padding: 15px; border-radius: 8px; "
            f"text-align: center; color: white; font-weight: bold;'>"
            f"{label}</div>",
            unsafe_allow_html=True
        )

# Progress bar
st.subheader("📈 Joriy NDVI Ko'rsatkichi")
progress = max(0, min(1, ndvi_value))
st.progress(progress)

# Tahlil
st.subheader("📋 Tahlil")

st.info(f"""
**{yil}-yil, {oy} oy uchun tahlil:**
- 📅 Davr: {start_date} - {end_date}
- 📍 Joy: {joy}
- 🌿 O'rtacha NDVI: **{ndvi_value:.3f}**
- 🌾 Tanlangan mahsulot: **{mahsulot}**
- 📊 Vegitatsiya holati: **{holat}**

**Tavsiyalar:**
- {"💧 Sug'orishni oshiring" if ndvi_value < 0.3 else "✅ Sog'lom o'simlik"}
- {"🌱 O'g'it qo'shing" if ndvi_value < 0.4 else "✅ O'g'it yetarli"}
""")

# Ob-havo ma'lumotlari
if weather_data:
    st.subheader("🌤️ Ob-havo ma'lumotlari")
    
    daily = weather_data.get('daily', {})
    
    if daily:
        # ✅ TO'G'RI - ikki tirnoq (") ishlatilgan
        weather_df = pd.DataFrame({
            "Sana": daily.get('time', []),
            "Harorat (°C)": daily.get('temperature_2m_mean', []),
            "Yogingarchilik (mm)": daily.get('precipitation_sum', []),
            "Tuproq namligi": daily.get('soil_moisture_0_to_10cm', [])
        })
        
        st.dataframe(weather_df, use_container_width=True)
        
        st.line_chart(weather_df.set_index("Sana")[["Harorat (°C)", "Yogingarchilik (mm)"]])

# Xarita
st.subheader("🗺️ Xarita")

map_data = pd.DataFrame([
    {"lat": v["lat"], "lon": v["lon"], "name": v["name"]} 
    for v in [GURLAN_CENTER] + GURLAN_VILLAGES
])

st.map(map_data, zoom=10)

# Footer
st.markdown("---")
st.caption("🛰️ Ma'lumotlar NASA POWER va Open-Meteo API asosida tayyorlandi.")
st.caption("👨‍💻 Dasturchi: Mamurbek | 📅 2024")
st.caption("⚠️ Bu demo versiya. Haqiqiy sun'iy yo'ldosh ma'lumotlari keyinroq qo'shiladi.")
