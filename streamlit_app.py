import streamlit as st
import ee
import pandas as pd

# 1. Sahifa sozlamalari
st.set_page_config(page_title="GEE Monitoring - Gurlan", layout="wide")
st.title("🛰️ Gurlan tumani: Sun'iy yo'ldosh orqali NDVI monitoringi")

# 2. Google Earth Engine-ni autentifikatsiya qilish (Secrets orqali)
def authenticate_gee():
    try:
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
        st.error(f"GEE ulanish xatosi: {e}")
        return False

if authenticate_gee():
    st.sidebar.success("✅ GEE Tizimi Onlayn")
    
    # 3. Sidebar: Monitoring yilini tanlash
    st.sidebar.header("Sozlamalar")
    year = st.sidebar.slider("Yilni tanlang:", 2015, 2024, 2023)
    
    # 4. Gurlan tumani koordinatalari (Polygon)
    gurlan_region = ee.Geometry.Polygon([
        [[60.30, 41.75], [60.75, 41.75], [60.75, 42.10], [60.30, 42.10]]
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

    # Ma'lumotlarni tahlil qilish
    with st.spinner("Gurlan tumani ma'lumotlari tahlil qilinmoqda..."):
        try:
            stats = dataset.map(get_ndvi_stats).getInfo()
            data_list = [f['properties'] for f in stats['features']]
            df = pd.DataFrame(data_list)
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')

                # 7. Grafik va Statistika
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader(f"{year}-yildagi vegetatsiya holati")
                    st.line_chart(df.set_index('date')['NDVI'])

                with col2:
                    st.subheader("📊 Natijalar")
                    avg_ndvi = df['NDVI'].mean()
                    st.metric(label="O'rtacha yillik NDVI", value=f"{avg_ndvi:.3f}")

                    if avg_ndvi < 0.22:
                        st.error("🚨 Holat: Yashillik darajasi juda past (Qurg'oqchilik ehtimoli).")
                    elif avg_ndvi < 0.32:
                        st.warning("⚠️ Holat: Vegetatsiya o'rtacha.")
                    else:
                        st.success("🌿 Holat: O'simlik qoplami barqaror.")
            else:
                st.warning("Ma'lumot topilmadi.")
        except Exception as e:
            st.error(f"Xato yuz berdi: {e}")

    st.divider()
    st.caption("Ma'lumotlar Google Earth Engine (MODIS Terra) asosida tayyorlandi.")
else:
    st.info("💡 Secrets bo'limiga kalitni joylashtiring.")
