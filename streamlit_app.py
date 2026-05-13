import streamlit as st
import ee
import pandas as pd
import datetime

# 1. Sahifa sozlamalari
st.set_page_config(page_title="GEE Monitoring - Shovot", layout="wide")
st.title("🛰️ Shovot tumani: Sun'iy yo'ldosh orqali NDVI monitoringi")

# 2. Google Earth Engine-ni autentifikatsiya qilish (Secrets orqali)
def authenticate_gee():
    try:
        # Streamlit Secrets-dan kalitni olish
        gee_json = st.secrets["gee_key"]
        credentials = ee.ServiceAccountCredentials(gee_json['client_email'], key_data=gee_json['private_key'])
        ee.Initialize(credentials)
        return True
    except Exception as e:
        st.error(f"GEE bilan ulanishda xato: {e}")
        return False

if authenticate_gee():
    st.sidebar.success("✅ GEE Tizimi Onlayn")
    
    # 3. Sidebar: Foydalanuvchi tanlovlari
    st.sidebar.header("Parametrlarni tanlang")
    year = st.sidebar.slider("Yilni tanlang:", 2015, 2024, 2023)
    
    # 4. Hududni belgilash (Shovot tumani koordinatalari)
    # Taxminiy Shovot tumani markazi
    shovot_region = ee.Geometry.Polygon([
        [[60.2, 41.6], [60.5, 41.6], [60.5, 41.8], [60.2, 41.8]]
    ])

    # 5. Ma'lumotlarni yuklash (MODIS NDVI ma'lumotlari)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    dataset = ee.ImageCollection('MODIS/006/MOD13A2') \
                .filterDate(start_date, end_date) \
                .select('NDVI')

    # 6. Grafik uchun ma'lumot tayyorlash
    def get_ndvi_stats(img):
        mean_ndvi = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=shovot_region,
            scale=1000
        ).get('NDVI')
        date = img.date().format('YYYY-MM-DD')
        return ee.Feature(None, {'date': date, 'NDVI': ee.Number(mean_ndvi).multiply(0.0001)})

    stats = dataset.map(get_ndvi_stats).getInfo()
    
    # Ma'lumotlarni jadval ko'rinishiga o'tkazish
    data_list = [f['properties'] for f in stats['features']]
    df = pd.DataFrame(data_list)
    df['date'] = pd.to_datetime(df['date'])

    # 7. Natijalarni ekranga chiqarish
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader(f"{year}-yil uchun NDVI o'zgarishi")
        st.line_chart(df.set_index('date')['NDVI'])

    with col2:
        st.subheader("Statistika va Xulosa")
        avg_ndvi = df['NDVI'].mean()
        st.metric(label="O'rtacha yillik NDVI", value=f"{avg_ndvi:.3f}")

        if avg_ndvi < 0.25:
            st.warning("⚠️ Diqqat: Yashillik darajasi past. Qurg'oqchilik xavfi bo'lishi mumkin.")
        else:
            st.success("✅ Hududda vegetatsiya holati barqaror.")

    st.info("Eslatma: NDVI (Normalized Difference Vegetation Index) - o'simliklarning zichligi va salomatligini ko'rsatuvchi indeksdir.")
else:
    st.warning("Iltimos, Streamlit Secrets bo'limiga GEE kalitini kiriting.")
