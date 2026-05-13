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
            st.error("Secrets bo'limida 'gee_key' topilmadi! Iltimos, kalitni joylang.")
            return False
    except Exception as e:
        st.error(f"GEE bilan ulanishda xato yuz berdi: {e}")
        return False

if authenticate_gee():
    st.sidebar.success("✅ GEE Tizimi Onlayn")
    
    # 3. Sidebar: Yilni tanlash
    st.sidebar.header("Sozlamalar")
    year = st.sidebar.slider("Monitoring yilini tanlang:", 2015, 2024, 2023)
    
    # 4. Gurlan tumani koordinatalari (Polygon)
    # Gurlan tumani chegaralarini qamrab oluvchi koordinatalar
    gurlan_region = ee.Geometry.Polygon([
        [[60.30, 41.75], [60.75, 41.75], [60.75, 42.10], [60.30, 42.10]]
    ])

    # 5. MODIS NDVI ma'lumotlarini yuklash (MOD13A2 mahsuloti)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    dataset = ee.ImageCollection('MODIS/006/MOD13A2') \
                .filterDate(start_date, end_date) \
                .select('NDVI')

    # 6. Har bir rasm uchun o'rtacha NDVI qiymatini hisoblash funksiyasi
    def get_ndvi_stats(img):
        mean_ndvi = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=gurlan_region,
            scale=1000
        ).get('NDVI')
        date = img.date().format('YYYY-MM-DD')
        return ee.Feature(None, {
            'date': date, 
            'NDVI': ee.Number(mean_ndvi).multiply(0.0001) # MODIS skalasini (0-1) oralig'iga o'tkazish
        })

    # Ma'lumotlarni tahlil qilish jarayoni
    with st.spinner("Ma'lumotlar tahlil qilinmoqda, iltimos kuting..."):
        try:
            stats = dataset.map(get_ndvi_stats).getInfo()
            
            # Ma'lumotlarni jadval (DataFrame) ko'rinishiga o'tkazish
            data_list = [f['properties'] for f in stats['features']]
            df = pd.DataFrame(data_list)
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')

                # 7. Natijalarni vizuallashtirish
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader(f"Gurlan tumani: {year}-yilgi vegetatsiya grafigi")
                    # Chiziqli grafik chizish
                    st.line_chart(df.set_index('date')['NDVI'])

                with col2:
                    st.subheader("📊 Statistik ko'rsatkichlar")
                    avg_ndvi = df['NDVI'].mean()
                    max_ndvi = df['NDVI'].max()
                    
                    st.metric(label="Yillik o'rtacha NDVI", value=f"{avg_ndvi:.3f}")
                    st.metric(label="Maksimal yashillik", value=f"{max_ndvi:.3f}")

                    # Xulosa qismi
                    if avg_ndvi < 0.20:
                        st.error("🚨 Xulosa: Yashillik darajasi juda past. Qurg'oqchilik alomatlari mavjud.")
                    elif avg_ndvi < 0.30:
                        st.warning("⚠️ Xulosa: Vegetatsiya holati o'rtacha darajada.")
                    else:
                        st.success("🌿 Xulosa: O'simliklar qoplami yaxshi va barqaror.")
                
                # Ma'lumotlar jadvalini ko'rsatish (ixtiyoriy)
                if st.checkbox("Xom ma'lumotlarni ko'rish"):
                    st.write(df)
            else:
                st.warning(f"Afsuski, {year}-yil uchun sun'iy yo'ldosh ma'lumotlari topilmadi.")
        
        except Exception as e:
            st.error(f"Ma'lumotlarni qayta ishlashda xato: {e}")

    st.divider()
    st.info("ℹ️ Ushbu tizim MODIS sun'iy yo'ldosh ma'lumotlari asosida real vaqtda NDVI indeksini hisoblaydi.")
else:
    st.warning("Diqqat: Google Earth Engine autentifikatsiyadan o'tmadi. Secrets bo'limini tekshiring.")
