import streamlit as st
import ee
import pandas as pd
import datetime

# 1. Sahifa sozlamalari
st.set_page_config(page_title="GEE Monitoring - Gurlan", layout="wide")
st.title("🛰️ Gurlan tumani: Sun'iy yo'ldosh orqali NDVI monitoringi")

# 2. Google Earth Engine-ni autentifikatsiya qilish
def authenticate_gee():
    try:
        # Streamlit Secrets-dan kalitni olish
        if "gee_key" in st.secrets:
            gee_json = st.secrets["gee_key"]
            credentials = ee.ServiceAccountCredentials(
                gee_json['client_email'], 
                key_data=gee_json['private_key']
            )
            ee.Initialize(credentials)
            return True
        else:
            st.error("Secrets bo'limida 'gee_key' topilmadi!")
            return False
    except Exception as e:
        st.error(f"GEE bilan ulanishda xato: {e}")
        return False

if authenticate_gee():
    st.sidebar.success("✅ GEE Tizimi Onlayn")
    
    # 3. Sidebar: Yilni tanlash
    st.sidebar.header("Sozlamalar")
    year = st.sidebar.slider("Yilni tanlang:", 2015, 2024, 2023)
    
    # 4. Gurlan tumani koordinatalari (Polygon)
    # Gurlan tumani uchun taxminiy chegaralar
    gurlan_region = ee.Geometry.Polygon([
        [[60.30, 41.75], [60.65, 41.75], [60.65, 42.05], [60.30, 42.05]]
    ])

    # 5. MODIS NDVI ma'lumotlarini yuklash
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    dataset = ee.ImageCollection('MODIS/006/MOD13A2') \
                .filterDate(start_date, end_date) \
                .select('NDVI')

    # 6. NDVI hisoblash funksiyasi
    def get_ndvi_stats(img):
        mean_ndvi = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=gurlan_region,
            scale=1000
        ).get('NDVI')
        date = img.date().format('YYYY-MM-DD')
        return ee.Feature(None, {
            'date': date, 
            'NDVI': ee.Number(mean_ndvi).multiply(0.0001)
        })

    # Ma'lumotlarni olish
    with st.spinner('Ma'lumotlar tahlil qilinmoqda...'):
        stats = dataset.map(get_ndvi_stats).getInfo()
        
        # Jadvalga o'tkazish
        data_list = [f['properties'] for f in stats['features']]
        df = pd.DataFrame(data_list)
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            # 7. Natijalarni chiqarish
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader(f"Gurlan tumani: {year}-yilgi o'simlik qoplami dinamikasi")
                st.line_chart(df.set_index('date')['NDVI'])

            with col2:
                st.subheader("📊 Yillik Tahlil")
                avg_ndvi = df['NDVI'].mean()
                max_ndvi = df['NDVI'].max()
                
                st.metric(label="O'rtacha NDVI", value=f"{avg_ndvi:.3f}")
                st.metric(label="Eng yuqori yashillik", value=f"{max_ndvi:.3f}")

                if avg_ndvi < 0.20:
                    st.error("🚨 Hududda jiddiy qurg'oqchilik yoki sho'rlanish aniqlandi.")
                elif avg_ndvi < 0.30:
                    st.warning("⚠️ Vegetatsiya darajasi o'rtacha.")
                else:
                    st.success("🌿 Hududda o'simlik qoplami yaxshi holatda.")
        else:
            st.warning("Ushbu yil uchun ma'lumot topilmadi.")

    st.divider()
    st.caption("Ma'lumotlar MODIS (Terra) sun'iy yo'ldoshidan olindi. Koordinatalar: Gurlan, Xorazm.")
else:
    st.info("💡 Davom etish uchun Streamlit Cloud Settings -> Secrets bo'limiga GEE JSON kalitini joylang.")
