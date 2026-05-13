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
        # Secrets'dan JSON ma'lumotlarni o'qish
        gee_info = dict(st.secrets["gee_key"])
        
        # Service account orqali autentifikatsiya
        credentials = service_account.Credentials.from_service_account_info(gee_info)
        ee.Initialize(credentials)
        
        return True
    except Exception as e:
        st.error(f"GEE ulanish xatosi: {str(e)}")
        st.info("💡 Secrets bo'limiga kalitni joylashtiring.")
        return False

# GEE ni ishga tushirish
gee_ok = init_gee()

# ============================================================
# 2. GURLAN TUMANI GEOMETRY
# ============================================================
def get_gurlan_geometry():
    """Gurlan tumanining koordinatalari"""
    # Gurlan tumani (Xorazm viloyati) koordinatalari
    # Siz o'zingizning aniq koordinatalaringizni qo'shishingiz mumkin
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

# Sarlavha
st.title("🛰️ Gurlan tumani: Sun'iy yo'ldosh orqali NDVI monitoringi")

# Sidebar sozlamalari
with st.sidebar:
    st.header("⚙️ Sozlamalar")
    
    # Yil tanlash
    yil = st.slider("📅 Yilni tanlang:", 2020, 2024, 2023)
    
    # Oy tanlash (ixtiyoriy)
    oy = st.selectbox(
        "📅 Oyni tanlang (ixtiyoriy):",
        ["Barcha yil", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
         "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"],
        index=0
    )
    
    # Mahsulot turi
    mahsulot = st.selectbox(
        "🌾 Mahsulot turi:",
        ["Bug'doy", "Paxta", "Galla", "Sabzavot", "Barchasi"]
    )
    
    # GEE holati
    if gee_ok:
        st.success("✅ GEE Tizimi Onlayn")
    else:
        st.error("❌ GEE ulanmadi")

# ============================================================
# 4. SANA FORMATINI TO'G'RILASH
# ============================================================
def get_date_range(yil, oy_tanlash):
    """
    Yil va oy bo'yicha to'g'ri sana oralig'ini qaytaradi
    """
    if oy_tanlash == "Barcha yil":
        # Butun yil
        start_date = f"{yil}-01-01"
        end_date = f"{yil}-12-31"
    else:
        # Oy raqamini aniqlash
        oy_nomlari = {
            "Yanvar": 1, "Fevral": 2, "Mart": 3, "Aprel": 4,
            "May": 5, "Iyun": 6, "Iyul": 7, "Avgust": 8,
            "Sentabr": 9, "Oktabr": 10, "Noyabr": 11, "Dekabr": 12
        }
        oy_raqam = oy_nomlari[oy_tanlash]
        
        # Oyning oxirgi kuni
        _, kunlar = calendar.monthrange(yil, oy_raqam)
        
        start_date = f"{yil}-{oy_raqam:02d}-01"
        end_date = f"{yil}-{oy_raqam:02d}-{kunlar}"
    
    return start_date, end_date

# Sana oralig'ini olish
start_date, end_date = get_date_range(yil, oy)

st.write(f"📊 **Tanlangan davr:** `{start_date}` dan `{end_date}` gacha")

# ============================================================
# 5. NDVI MA'LUMOTLARINI OLISH
# ============================================================
def get_ndvi_data(start_date, end_date, geometry):
    """
    MODIS NDVI ma'lumotlarini olish
    """
    try:
        # MODIS NDVI kolleksiyasi (250m resolution)
        collection = ee.ImageCollection('MODIS/061/MOD13Q1') \
            .filterDate(start_date, end_date) \
            .filterBounds(geometry) \
            .select('NDVI')
        
        # Ma'lumotlar mavjudligini tekshirish
        count = collection.size().getInfo()
        
        if count == 0:
            return None, "Tanlangan davr uchun ma'lumotlar mavjud emas."
        
        # O'rtacha NDVI
        mean_ndvi = collection.mean().clip(geometry)
        
        # Statistika
        stats = mean_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=250,
            maxPixels=1e9
        )
        
        ndvi_value = stats.get('NDVI').getInfo()
        
        # NDVI ni -1 dan 1 ga o'tkazish (MODIS qiymatlari 0.0001 ga ko'paytirilgan)
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
        # Natijalarni ko'rsatish
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="🌿 O'rtacha NDVI",
                value=f"{ndvi_value:.3f}",
                delta="0.00"
            )
        
        with col2:
            # NDVI baholash
            if ndvi_value < 0:
                holat = "❌ Suv/Quyruq"
                rang = "🔴"
            elif ndvi_value < 0.2:
                holat = "⚠️ O'tloqi yomon"
                rang = "🟠"
            elif ndvi_value < 0.4:
                holat = "🟡 O'tloqi o'rta"
                rang = "🟡"
            elif ndvi_value < 0.6:
                holat = "🟢 O'tloqi yaxshi"
                rang = "🟢"
            else:
                holat = "🌳 O'tloqi a'lo"
                rang = "🌳"
            
            st.metric(label="📊 Holat", value=holat)
        
        with col3:
            st.metric(label="🌾 Mahsulot", value=mahsulot)
        
        # NDVI shkalasi
        st.subheader("🎨 NDVI Shkalasi")
        
        # Rangli shkala
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
        progress = max(0, min(1, (ndvi_value + 1) / 2))  # -1 dan 1 ga normalize
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
        sog'lig'ini baholash uchun ishlatiladigan indeks. Qiymat -1 dan 1 
        gacha o'zgaradi. Yuqori qiymat (0.6-0.8) sog'lom o'simliklarni, 
        past qiymat (0.0-0.2) esa kam vegatatsiyali hududlarni ko'rsatadi.
        """)
        
        # Xarita (ixtiyoriy)
        st.subheader("🗺️ Xarita")
        try:
            # Xarita markazi (Gurlan tumani markazi taxminiy)
            map_center = [41.9, 60.15]
            
            # Folium xarita (agar folium o'rnatilgan bo'lsa)
            try:
                import folium
                from streamlit_folium import st_folium
                
                m = folium.Map(location=map_center, zoom_start=10)
                folium.GeoJson(
                    gurlan.getInfo(),
                    name="Gurlan tumani",
                    style_function=lambda x: {
                        'fillColor': '#1a9850' if ndvi_value > 0.6 else 
                                    '#fee08b' if ndvi_value > 0.4 else 
                                    '#fc8d59' if ndvi_value > 0.2 else '#d73027',
                        'color': 'black',
                        'weight': 2,
                        'fillOpacity': 0.5
                    }
                ).add_to(m)
                
                st_folium(m, width=700, height=500)
                
            except ImportError:
                st.warning("🗺️ Xarita ko'rish uchun `folium` va `streamlit-folium` o'rnatilishi kerak.")
                
        except Exception as e:
            st.warning(f"Xarita yuklanmadi: {str(e)}")

else:
    st.warning("⚠️ GEE ulanmagan. Iltimos, Secrets bo'limiga kalitni joylashtiring.")

# Footer
st.markdown("---")
st.caption("🛰️ Ma'lumotlar Google Earth Engine (MODIS Terra) asosida tayyorlandi.")
st.caption("👨‍💻 Dasturchi: Mamurbek | 📅 2024")
