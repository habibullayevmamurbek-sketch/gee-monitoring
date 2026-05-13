import streamlit as st
import ee
from google.oauth2 import service_account
import pandas as pd
import numpy as np
from datetime import datetime
import calendar

# ============================================================
# 1. GEE AUTHENTIFIKATSIYA
# ============================================================
@st.cache_resource
def init_gee():
    """GEE bilan ulanish"""
    try:
        gee_info = dict(st.secrets["gee_key"])
        credentials = service_account.Credentials.from_service_account_info(gee_info)
        ee.Initialize(credentials)
        return True
    except Exception as e:
        st.error(f"GEE ulanish xatosi: {str(e)}")
        st.info("💡 Secrets bo'limiga kalitni joylashtiring.")
        return False

gee_ok = init_gee()

# ============================================================
# 2. GURLAN TUMANI GEOMETRY
# ============================================================
def get_gurlan_geometry():
    """Gurlan tumanining koordinatalari"""
    gurlan = ee.Geometry.Polygon([
        [
            [60.0, 41.8],
            [60.3, 41.8],
            [60.3, 42.0],
            [60.0, 42.0],
            [60.0, 41.8]
        ]
    ])
    return gurlan

# ============================================================
# 3. STREAMLIT UI
# ============================================================
st.set_page_config(
    page_title="Gurlan tumani NDVI monitoringi",
    page_icon="🛰️",
    layout="wide"
)

st.title("🛰️ Gurlan tumani: Sun'iy yo'ldosh orqali NDVI monitoringi")

with st.sidebar:
    st.header("⚙️ Sozlamalar")
    yil = st.slider("📅 Yilni tanlang:", 2020, 2024, 2023)
    oy = st.selectbox(
        "📅 Oyni tanlang (ixtiyoriy):",
        ["Barcha yil", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
         "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"],
        index=0
    )
    mahsulot = st.selectbox(
        "🌾 Mahsulot turi:",
        ["Bug'doy", "Paxta", "Galla", "Sabzavot", "Barchasi"]
    )
    if gee_ok:
        st.success("✅ GEE Tizimi Onlayn")
    else:
        st.error("❌ GEE ulanmadi")

# ============================================================
# 4. SANA FORMATINI TO'G'RILASH
# ============================================================
def get_date_range(yil, oy_tanlash):
    if oy_tanlash == "Barcha yil":
        start_date = f"{yil}-01-01"
        end_date = f"{yil}-12-31"
    else:
        oy_nomlari = {
            "Yanvar": 1, "Fevral": 2, "Mart": 3, "Aprel": 4,
            "May": 5, "Iyun": 6, "Iyul": 7, "Avgust": 8,
            "Sentabr": 9, "Oktabr": 10, "Noyabr": 11, "Dekabr": 12
        }
        oy_raqam = oy_nomlari[oy_tanlash]
        _, kunlar = calendar.monthrange(yil, oy_raqam)
        start_date = f"{yil}-{oy_raqam:02d}-01"
        end_date = f"{yil}-{oy_raqam:02d}-{kunlar}"
    return start_date, end_date

start_date, end_date = get_date_range(yil, oy)
st.write(f"📊 **Tanlangan davr:** `{start_date}` dan `{end_date}` gacha")

# ============================================================
# 5. NDVI MA'LUMOTLARINI OLISH
# ============================================================
def get_ndvi_data(start_date, end_date, geometry):
    try:
        collection = ee.ImageCollection('MODIS/061/MOD13Q1') \
            .filterDate(start_date, end_date) \
            .filterBounds(geometry) \
            .select('NDVI')
        
        count = collection.size().getInfo()
        if count == 0:
            return None, "Tanlangan davr uchun ma'lumotlar mavjud emas."
        
        mean_ndvi = collection.mean().clip(geometry)
        stats = mean_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=250,
            maxPixels=1e9
        )
        
        ndvi_value = stats.get('NDVI').getInfo()
        if ndvi_value is not None:
            ndvi_value = ndvi_value * 0.0001
        
        return ndvi_value, None
    except Exception as e:
        return None, str(e)

# ============================================================
# 6. VIZUALIZATSIYA
# ============================================================
if gee_ok:
    with st.spinner("🛰️ Sun'iy yo'ldosh ma'lumotlari yuklanmoqda..."):
        gurlan = get_gurlan_geometry()
        ndvi_value, error = get_ndvi_data(start_date, end_date, gurlan)
    
    if error:
        st.error(f"❌ Xato: {error}")
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="🌿 O'rtacha NDVI", value=f"{ndvi_value:.3f}")
        
        with col2:
            if ndvi_value < 0:
                holat = "❌ Suv/Quyruq"
            elif ndvi_value < 0.2:
                holat = "⚠️ O'tloqi yomon"
            elif ndvi_value < 0.4:
                holat = "🟡 O'tloqi o'rta"
            elif ndvi_value < 0.6:
                holat = "🟢 O'tloqi yaxshi"
            else:
                holat = "🌳 O'tloqi a'lo"
            st.metric(label="📊 Holat", value=holat)
        
        with col3:
            st.metric(label="🌾 Mahsulot", value=mahsulot)
        
        # NDVI shkalasi
        st.subheader("🎨 NDVI Shkalasi")
        shkala_col1, shkala_col2, shkala_col3, shkala_col4, shkala_col5 = st.columns(5)
        
        with shkala_col1:
            st.markdown(
                "<div style='background: #d73027; padding: 10px; border-radius: 5px; text-align: center;'>"
                "<b>0.0 - 0.2</b><br>Yomon</div>",
                unsafe_allow_html=True
            )
        with shkala_col2:
            st.markdown(
                "<div style='background: #fc8d59; padding: 10px; border-radius: 5px; text-align: center;'>"
                "<b>0.2 - 0.4</b><br>O'rta</div>",
                unsafe_allow_html=True
            )
        with shkala_col3:
            st.markdown(
                "<div style='background: #fee08b; padding: 10px; border-radius: 5px; text-align: center;'>"
                "<b>0.4 - 0.6</b><br>Yaxshi</div>",
                unsafe_allow_html=True
            )
        with shkala_col4:
            st.markdown(
                "<div style='background: #d9ef8b; padding: 10px; border-radius: 5px; text-align: center;'>"
                "<b>0.6 - 0.8</b><br>A'lo</div>",
                unsafe_allow_html=True
            )
        with shkala_col5:
            st.markdown(
                "<div style='background: #1a9850; padding: 10px; border-radius: 5px; text-align: center;'>"
                "<b>0.8 - 1.0</b><br>Eng yaxshi</div>",
                unsafe_allow_html=True
            )
        
        # NDVI progress bar
        st.subheader("📈 Joriy NDVI Ko'rsatkichi")
        progress = max(0, min(1, (ndvi_value + 1) / 2))
        st.progress(progress)
        
        # Tahlil
        st.subheader("📋 Tahlil")
        st.info(f"""
        **{yil}-yil uchun tahlil:**
        - 📅 Davr: {start_date} - {end_date}
        - 🌿 O'rtacha NDVI: **{ndvi_value:.3f}**
        - 🌾 Tanlangan mahsulot: **{mahsulot}**
        - 📊 Vegitatsiya holati: **{holat}**
        
        NDVI (Normalized Difference Vegetation Index) - bu o'simliklarning 
        sog'lig'ini baholash uchun ishlatiladigan indeks.
        """)
        
        # Xarita - vaqtincha olib tashlangan
        st.subheader("🗺️ Xarita")
        st.info("🗺️ Xarita ko'rish uchun keyinroq qo'shiladi.")

else:
    st.warning("⚠️ GEE ulanmagan. Iltimos, Secrets bo'limiga kalitni joylashtiring.")

st.markdown("---")
st.caption("🛰️ Ma'lumotlar Google Earth Engine (MODIS Terra) asosida tayyorlandi.")
st.caption("👨‍💻 Dasturchi: Mamurbek | 📅 2024")
