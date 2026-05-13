import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# ============================================================
# 1. SENTINEL HUB API (GEEsiz)
# ============================================================

SENTINEL_HUB_CLIENT_ID = "your-client-id"
SENTINEL_HUB_CLIENT_SECRET = "your-client-secret"

# Yoki bepul usul - Open-Meteo va boshqa manbalar

# ============================================================
# 2. NASA POWER API (BEPUL, GEEsiz)
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
# 3. OPEN-METEO API (BEPUL ob-havo)
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
# 4. NDVI SIMULATSIYA (REAL MA'LUMOTLAR YO'Q BO'LSA)
# ============================================================

def simulate_ndvi(yil, oy, mahsulot_turi):
    """
    Vegitatsiya indeksini simulyatsiya qilish
    (Real ma'lumotlar kelguniga qadar)
    """
    # Mahsulot bo'yicha bazaviy NDVI
    ndvi_base = {
        "Bug'doy": 0.45,
        "Paxta": 0.35,
        "Galla": 0.50,
        "Sabzavot": 0.55,
        "Barchasi": 0.42
    }
    
    # Oy bo'yicha o'zgarish (o'rtacha)
    oy_factor = {
        1: 0.3,   # Yanvar - qish
        2: 0.35,  # Fevral
        3: 0.45,  # Mart - bahor
        4: 0.55,  # Aprel
        5: 0.65,  # May
        6: 0.75,  # Iyun - yoz
        7: 0.80,  # Iyul
        8: 0.75,  # Avgust
        9: 0.65,  # Sentabr - kuz
        10: 0.50, # Oktabr
        11: 0.40, # Noyabr
        12: 0.30  # Dekabr
    }
    
    base = ndvi_base.get(mahsulot_turi, 0.42)
    factor = oy_factor.get(oy, 0.5)
    
    # Yil bo'yicha ozgina o'zgarish
    yil_factor = 1.0 + (yil - 2020) * 0.02
    
    # Tasodifiy o'zgarish (±0.05)
    random_var = np.random.uniform(-0.05, 0.05)
    
    ndvi = base * factor * yil_factor + random_var
    return max(0, min(0.95, ndvi))

# ============================================================
# 5. GURLAN TUMANI KOORDINATALARI
# ============================================================

GURLAN_CENTER = {
    "lat": 41.85,
    "lon": 60.15,
    "name": "Gurlan tumani markazi"
}

GURLAN_VILLAGES = [
    {"name": "Gurlan shaharchasi", "lat": 41.85, "lon": 60.15},
    {"name": "Xonqa", "lat": 41.87, "lon": 60.12},
    {"name": "Bog'ot", "lat": 41.83, "lon": 60.18},
    {"name": "Yangiariq", "lat": 41.80, "lon": 60.10},
    {"name": "Qizilqum", "lat": 41.90, "lon": 60.20},
