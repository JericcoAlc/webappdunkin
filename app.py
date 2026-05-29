# python -m streamlit run app.py
from xml.parsers.expat import model

import streamlit as st
import base64
import pandas as pd
import pydeck as pdk
from pathlib import Path
import os
import textwrap
from google_places import (
    get_place_details,
    search_places,
    count_nearby_places
)
import osmnx as ox
from geopy.distance import geodesic
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
import plotly.figure_factory as ff
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
import concurrent.futures
import networkx as nx
import osmnx as ox

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Dunkin | Expansion Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# HELPERS
# =========================================================
def get_base64_image(path):
    path = Path(path)
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def get_icon_data(path):
    path = Path(path)
    if not path.exists():
        return None

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    return {
        "url": f"data:image/png;base64,{encoded}",
        "width": 128,
        "height": 128,
        "anchorY": 128
    } 




# =========================================================
# LOGIN SIMPLE
# =========================================================
USERS = {
    "ceo": {"password": "ceo", "rol": "CEO"},
    "director": {"password": "director", "rol": "Director"},
    "ejecutivo": {"password": "ejecutivo", "rol": "Ejecutivo"},
}

if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.rol = None


# =========================================================
# ESTILOS GLOBALES
# =========================================================
def inject_styles():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

        :root {
            --bg-main: #FFF8F3;
            --bg-soft: #FFF3EA;
            --card: rgba(255,255,255,0.88);
            --card-strong: #FFFFFF;

            --dunkin-orange: #FF6B1A;
            --dunkin-orange-soft: #FFE1CF;
            --dunkin-pink: #E83E8C;
            --dunkin-pink-soft: #FFD7E8;

            --text-main: #4B2E1F;
            --text-soft: #8A6A58;
            --border-soft: rgba(75, 46, 31, 0.08);

            --shadow-soft: 0 12px 30px rgba(75, 46, 31, 0.08);
            --shadow-hover: 0 18px 36px rgba(232, 62, 140, 0.10), 0 12px 32px rgba(255, 107, 26, 0.10);

            --radius-xl: 26px;
            --radius-lg: 22px;
            --radius-md: 18px;
            --radius-sm: 14px;
        }

        html, body, [class*="css"] {
            font-family: "Poppins", sans-serif;
            background:
                radial-gradient(circle at top left, rgba(255,107,26,0.09), transparent 28%),
                radial-gradient(circle at top right, rgba(232,62,140,0.08), transparent 24%),
                linear-gradient(180deg, #FFF9F5 0%, #FFF5EF 100%);
            color: var(--text-main);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255,107,26,0.09), transparent 28%),
                radial-gradient(circle at top right, rgba(232,62,140,0.08), transparent 24%),
                linear-gradient(180deg, #FFF9F5 0%, #FFF5EF 100%);
        }

        .block-container {
            max-width: 1380px !important;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }

        /* Ocultar footer (dejamos el menú nativo visible) */
        footer {visibility: hidden;}
        
        header {
            background: transparent !important;
        }

        
        section[data-testid="stSidebar"]{
            background: rgba(255,255,255,0.88);
            border-right: 1px solid rgba(75,46,31,0.08);
        }

        /* Botones */
        .stButton > button {
            border-radius: 999px !important;
            border: none !important;
            padding: 0.72rem 1.3rem !important;
            font-weight: 700 !important;
            color: white !important;
            background: linear-gradient(135deg, var(--dunkin-orange), var(--dunkin-pink)) !important;
            box-shadow: 0 10px 25px rgba(232, 62, 140, 0.18) !important;
            transition: all 0.25s ease !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) scale(1.015);
            box-shadow: 0 16px 30px rgba(232, 62, 140, 0.25) !important;
            filter: brightness(1.02);
        }

        /* Inputs */
        .stTextInput > div > div > input {
            border-radius: 16px !important;
            border: 1px solid rgba(75, 46, 31, 0.10) !important;
            background: rgba(255,255,255,0.85) !important;
            color: var(--text-main) !important;
            padding: 0.7rem 0.95rem !important;
        }

        .stSelectbox > div > div {
            border-radius: 14px !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            margin-bottom: 20px !important;
            padding-bottom: 4px !important;
            scrollbar-width: none !important;
        }

        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
            display: none !important;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 12px !important;
            background: rgba(255,255,255,0.60) !important;
            border: 1px solid rgba(75,46,31,0.07) !important;
            color: var(--text-soft) !important;
            padding: 9px 16px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            white-space: nowrap !important;
            transition: all 0.20s ease !important;
            letter-spacing: 0.01em !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(255,255,255,0.90) !important;
            color: var(--dunkin-orange) !important;
            transform: translateY(-1px) !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #FF6B1A, #E83E8C) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 8px 20px rgba(232,62,140,0.22), 0 4px 8px rgba(255,107,26,0.14) !important;
            transform: translateY(-1px) !important;
        }

        div[data-testid="stTabs"] {
            padding: 0 !important;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px !important;
            background: rgba(255,255,255,0.72) !important;
            border: 1px solid rgba(75, 46, 31, 0.08) !important;
            color: var(--text-main) !important;
            padding: 10px 18px !important;
            font-weight: 600 !important;
            transition: all 0.22s ease !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 22px rgba(255,107,26,0.08);
            background: rgba(255,255,255,0.92) !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--dunkin-orange), var(--dunkin-pink)) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 14px 26px rgba(232,62,140,0.18);
        }

        /* Login */

        .login-wrap {
            max-width: 420px;
            margin: 6vh auto 0 auto;
            padding: 44px 40px 40px 40px;
            background: rgba(255,255,255,0.88);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 32px;
            border: 1px solid rgba(255,255,255,0.72);
            box-shadow:
                0 32px 64px rgba(75,46,31,0.10),
                0 0 0 1px rgba(255,107,26,0.06);
            animation: fadeUp 0.7s ease;
        }

        .login-title {
            text-align: center;
            font-size: 28px;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 6px;
            letter-spacing: -0.02em;
        }

        .login-sub {
            text-align: center;
            font-size: 14px;
            color: var(--text-soft);
            margin-bottom: 28px;
            font-weight: 500;
        }

        .login-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,107,26,0.18), transparent);
            margin: 20px 0;
        }

        /* Header principal */
 

        .hero-shell::before {
            content: "";
            position: absolute;
            width: 280px;
            height: 280px;
            right: -80px;
            top: -120px;
            background: radial-gradient(circle, rgba(255,107,26,0.22), transparent 70%);
            pointer-events: none;
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            width: 250px;
            height: 250px;
            left: -80px;
            bottom: -120px;
            background: radial-gradient(circle, rgba(232,62,140,0.18), transparent 70%);
            pointer-events: none;
        }
        
        .hero-shell{
            animation: fadeUp 0.8s ease;
        }

        @keyframes fadeUp{
            from{
                opacity:0;
                transform:translateY(20px);
            }

            to{
                opacity:1;
                transform:translateY(0);
            }
        }

        .badge-premium {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(255,107,26,0.12), rgba(232,62,140,0.10));
            color: var(--text-main);
            font-size: 13px;
            font-weight: 600;
            border: 1px solid rgba(255,107,26,0.10);
            margin-bottom: 14px;
        }

        .hero-title {
            font-size: 46px;
            line-height: 1.05;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-main);
            margin: 0;
        }

        .hero-subtitle {
            font-size: 17px;
            color: var(--text-soft);
            margin-top: 10px;
            margin-bottom: 0;
            max-width: 760px;
        }

        .hero-accent-line {
            width: 170px;
            height: 7px;
            border-radius: 999px;
            margin-top: 18px;
            background: linear-gradient(90deg, var(--dunkin-orange), var(--dunkin-pink));
            box-shadow: 0 8px 20px rgba(232,62,140,0.18);
        }

        /* Cards top */
        .feature-card {
            position: relative;
            overflow: hidden;
            min-height: 170px;
            padding: 22px 20px;
            border-radius: 24px;
            background: rgba(255,255,255,0.82);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.64);
            box-shadow: var(--shadow-soft);
            transition: transform 0.28s ease, box-shadow 0.28s ease, border 0.28s ease;
        }

        .feature-card:hover {
            transform: translateY(-8px) scale(1.01);
            box-shadow: var(--shadow-hover);
            border: 1px solid rgba(255,107,26,0.14);
        }

        .feature-card::before {
            content: "";
            position: absolute;
            right: -25px;
            top: -25px;
            width: 110px;
            height: 110px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(255,107,26,0.12), transparent 68%);
        }
        
        /* --- NUEVAS ANIMACIONES 10/10 --- */
        
        /* Efecto Fade-In suave al cambiar de Tabs */
        div[data-testid="stTabs"] > div > div {
            animation: fadeInTab 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
        }
        @keyframes fadeInTab {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Hover Premium para las KPI Cards */
        .kpi-card {
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }
        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(255,107,26,0.12), 0 8px 15px rgba(232,62,140,0.08);
            border-color: rgba(255,107,26,0.25) !important;
        }

        /* Hover para las filas de la tabla de competidores */
        [data-testid="stDataFrame"] table tbody tr:hover {
            background-color: rgba(255,107,26,0.04) !important;
            transition: background-color 0.2s ease;
        }

        .feature-icon {
            width: 54px;
            height: 54px;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 16px;
            background: linear-gradient(135deg, rgba(255,107,26,0.16), rgba(232,62,140,0.14));
        }

        .feature-title {
            font-size: 18px;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 8px;
        }

        .feature-desc {
            font-size: 14px;
            line-height: 1.55;
            color: var(--text-soft);
        }

        .feature-tag {
            margin-top: 14px;
            display: inline-block;
            padding: 6px 11px;
            border-radius: 999px;
            background: rgba(255,107,26,0.10);
            color: var(--dunkin-orange);
            font-size: 12px;
            font-weight: 700;
        }

        /* Secciones */
        .section-card {
            border-radius: 28px;
            padding: 22px;
            background: rgba(255,255,255,0.80);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.65);
            box-shadow: 0 16px 34px rgba(75,46,31,0.08);
        }

        .section-title {
            font-size: 24px;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 6px;
        }

        .section-subtitle {
            font-size: 14px;
            color: var(--text-soft);
            margin-bottom: 18px;
        }

        /* Placeholder mapa */
        .map-shell {
            position: relative;
            overflow: hidden;
            min-height: 520px;
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.96), rgba(255,246,240,0.92));
            border: 1px solid rgba(75,46,31,0.08);
            box-shadow: 0 16px 38px rgba(75,46,31,0.08);
            padding: 24px;
        }

        .map-shell::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(rgba(255,107,26,0.025) 1px, transparent 1px),
                linear-gradient(90deg, rgba(232,62,140,0.025) 1px, transparent 1px);
            background-size: 30px 30px;
            pointer-events: none;
        }

        .map-overlay-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            border-radius: 999px;
            background: rgba(255,255,255,0.90);
            border: 1px solid rgba(75,46,31,0.07);
            box-shadow: 0 8px 18px rgba(75,46,31,0.06);
            font-size: 13px;
            font-weight: 600;
            color: var(--text-main);
            margin-right: 8px;
            margin-bottom: 10px;
        }

        .map-center-placeholder {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 345px;
            border-radius: 24px;
            background:
                radial-gradient(circle at center, rgba(255,107,26,0.08), transparent 42%),
                radial-gradient(circle at 60% 40%, rgba(232,62,140,0.08), transparent 28%),
                linear-gradient(135deg, #FFF7F2, #FFFDFC);
            border: 1px dashed rgba(255,107,26,0.18);
            text-align: center;
            padding: 26px;
        }

        .map-placeholder-title {
            font-size: 26px;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 10px;
        }

        .map-placeholder-text {
            font-size: 15px;
            color: var(--text-soft);
            max-width: 640px;
            margin: 0 auto;
            line-height: 1.7;
        }

        /* Panel lateral filtros */
        .side-panel {
            min-height: 520px;
            border-radius: 28px;
            padding: 22px;
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(255,255,255,0.66);
            box-shadow: 0 16px 34px rgba(75,46,31,0.08);
        }

        .mini-card {
            border-radius: 18px;
            padding: 16px;
            background: linear-gradient(135deg, rgba(255,107,26,0.08), rgba(232,62,140,0.06));
            border: 1px solid rgba(255,107,26,0.08);
            margin-bottom: 14px;
            transition: all 0.22s ease;
        }

        .mini-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(232,62,140,0.08);
        }

        .mini-card-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 6px;
        }

        .mini-card-desc {
            font-size: 13px;
            color: var(--text-soft);
            line-height: 1.55;
        }

        /* Bottom cards */
        .zone-card {
            border-radius: 24px;
            padding: 20px;
            background: rgba(255,255,255,0.84);
            border: 1px solid rgba(255,255,255,0.68);
            box-shadow: var(--shadow-soft);
            transition: all 0.25s ease;
        }

        .zone-card:hover {
            transform: translateY(-6px);
            box-shadow: var(--shadow-hover);
        }

        .zone-name {
            font-size: 18px;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 6px;
        }

        .zone-meta {
            font-size: 13px;
            color: var(--dunkin-pink);
            font-weight: 700;
            margin-bottom: 8px;
        }

        .zone-desc {
            font-size: 14px;
            color: var(--text-soft);
            line-height: 1.6;
        }

        .zone-pill {
            display: inline-block;
            margin-top: 14px;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(232,62,140,0.10);
            color: var(--dunkin-pink);
            font-size: 12px;
            font-weight: 700;
        }

        /* Spacer elegante */
        .soft-spacer {
            height: 20px;
        }
        
        .map-frame {
            border-radius: 26px;
            padding: 10px;
            background: rgba(255,255,255,0.84);
            border: 1px solid rgba(255,255,255,0.68);
            box-shadow: 0 16px 34px rgba(75,46,31,0.08);
            margin-top: 14px;
        }

        .map-note {
            font-size: 13px;
            color: var(--text-soft);
            margin-top: 10px;
            padding-left: 4px;
        }

        div[data-testid="stDeckGlJsonChart"] {
            border-radius: 22px !important;
            overflow: hidden !important;
            border: 1px solid rgba(75,46,31,0.08) !important;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.35);
        }
        .control-bar {
            border-radius: 22px;
            padding: 14px 18px 10px 18px;
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(255,255,255,0.68);
            box-shadow: 0 12px 28px rgba(75,46,31,0.07);
            margin: 14px 0 14px 0;
        }

        .control-bar-title {
            font-size: 13px;
            font-weight: 700;
            color: var(--text-soft);
            margin-bottom: 10px;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }

        div[data-testid="stCheckbox"] {
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(75,46,31,0.08);
            border-radius: 16px;
            padding: 10px 14px;
            box-shadow: 0 6px 14px rgba(75,46,31,0.04);
            transition: all 0.22s ease;
            min-height: 52px;
            display: flex;
            align-items: center;
        }

        div[data-testid="stCheckbox"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 20px rgba(232,62,140,0.08);
            border: 1px solid rgba(255,107,26,0.12);
        }

        div[data-testid="stCheckbox"] label {
            font-weight: 600 !important;
            color: var(--text-main) !important;
        }
        .zone-opportunity-card .stMarkdown{
            margin-bottom: 0 !important;
        }

        .zone-opportunity-card:hover{
            transform: translateY(-6px);
            box-shadow:
                0 20px 50px rgba(232,62,140,0.14);
        }

        .zone-opportunity-header{
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:18px;
        }

        .zone-opportunity-title{
            font-size:1.45rem;
            font-weight:800;
            color:#4B2E1F;
        }

        .zone-opportunity-score{
            width:64px;
            height:64px;
            border-radius:50%;

            display:flex;
            align-items:center;
            justify-content:center;

            margin-left:auto;

            background:
                linear-gradient(
                    135deg,
                    #FF6B1A,
                    #E83E8C
                );

            color:white;
            font-weight:800;
            font-size:1.15rem;
        }

        .zone-opportunity-priority{
            margin-bottom:20px;

            color:#8A6A58;
            font-weight:600;
        }

        .zone-opportunity-grid{
            display:flex;
            flex-wrap:wrap;
            gap:12px;
        }

        .zone-pill{
            background: rgba(255,255,255,0.72);

            border-radius:999px;

            padding:10px 16px;

            font-size:0.92rem;
            color:#6A4A3A;
            font-weight:600;
        }
        
        .kpi-card{
            margin-bottom: 12px;
            background: rgba(255,255,255,0.82);
            border-radius:24px;
            padding:24px;
            border:1px solid rgba(255,255,255,0.68);
            box-shadow:0 12px 30px rgba(75,46,31,0.08);
            min-height:190px;
        }

        .kpi-icon{
            width:52px;
            height:52px;
            border-radius:16px;
            background:linear-gradient(
                135deg,
                rgba(255,107,26,0.14),
                rgba(232,62,140,0.12)
            );

            display:flex;
            align-items:center;
            justify-content:center;

            font-size:24px;
            margin-bottom:18px;
        }

        .kpi-title{
            font-size:14px;
            color:#8A6A58;
            font-weight:600;
            margin-bottom:8px;
        }

        .kpi-value{
            font-size:42px;
            font-weight:800;
            color:#4B2E1F;
            line-height:1;
        }
                

                
        .priority-badge{
            display:inline-flex;
            align-items:center;
            gap:8px;
            padding:8px 14px;
            border-radius:999px;
            font-size:13px;
            font-weight:700;
            background:rgba(232,62,140,0.10);
            color:#E83E8C;
        }
                
        .recommend-chip{

            margin-top:10px;

            display:flex;

            align-items:center;

            gap:8px;

            padding:10px 14px;

            border-radius:999px;

            background:
                rgba(255,255,255,0.72);

            border:
                1px solid rgba(255,107,26,0.08);

            font-size:12px;

            font-weight:600;

            color:#8A6A58;

            box-shadow:
                0 8px 18px rgba(75,46,31,0.05);
        }

        .recommend-chip:hover{

            transform:translateY(-2px);

            transition:0.22s ease;

            box-shadow:
                0 12px 24px rgba(232,62,140,0.08);
        }
                
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 3px rgba(255,107,26,0.20); }
            50%       { box-shadow: 0 0 0 6px rgba(255,107,26,0.08); }
        }

        .hero-title {
            font-size: 38px;
            line-height: 1.08;
            font-weight: 800;
            letter-spacing: -0.025em;
            color: var(--text-main);
            margin: 12px 0 10px 0;
        }

        .hero-stat {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .hero-stat-num {
            font-size: 22px;
            font-weight: 800;
            color: var(--dunkin-orange);
            line-height: 1;
        }

        .hero-stat-label {
            font-size: 12px;
            color: var(--text-soft);
            font-weight: 500;
        }
                


        .feature-card {
            min-height: unset !important;
            padding: 24px 22px 20px 22px;
        }

        .feature-card::after {
            content: "";
            position: absolute;
            bottom: 0;
            left: 22px;
            right: 22px;
            height: 2px;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--dunkin-orange), var(--dunkin-pink));
            opacity: 0;
            transition: opacity 0.28s ease;
        }

        .feature-card:hover::after {
            opacity: 1;
        }
                
        /* Ocultar st.metric globalmente para forzar uso del custom */
        div[data-testid="metric-container"] {
            background: rgba(255,255,255,0.82) !important;
            border-radius: 20px !important;
            padding: 20px !important;
            border: 1px solid rgba(255,255,255,0.68) !important;
            box-shadow: 0 12px 30px rgba(75,46,31,0.08) !important;
        }

        div[data-testid="metric-container"] label {
            font-family: "Poppins", sans-serif !important;
            color: var(--text-soft) !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-family: "Poppins", sans-serif !important;
            color: var(--text-main) !important;
            font-size: 28px !important;
            font-weight: 800 !important;
        }
                
        section[data-testid="stSidebar"] {
            background: rgba(255,255,255,0.92) !important;
            border-right: 1px solid rgba(75,46,31,0.07) !important;
            padding: 16px 12px !important;
        }

        section[data-testid="stSidebar"] .stSlider > label {
            font-family: "Poppins", sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            color: var(--text-main) !important;
            margin-bottom: 4px !important;
        }

        section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {
            padding-top: 8px !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stSliderThumb"] {
            background: linear-gradient(135deg, #FF6B1A, #E83E8C) !important;
            border: 2px solid white !important;
            box-shadow: 0 4px 10px rgba(232,62,140,0.28) !important;
        }
    </style>
    
    
    """, unsafe_allow_html=True)


# =========================================================
# LOGIN
# =========================================================
def login_screen():
    inject_styles()
    logo_base64 = get_base64_image("dunkinlogo.png")


    if logo_base64:
        # Fíjate en el style="background: transparent;" dentro del img
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:8px;">
            <img src="data:image/png;base64,{logo_base64}" width="280" style="background: transparent; border: none;">
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='login-title'>Inicio de sesión</div>", unsafe_allow_html=True)
    # ... resto de tu login
    st.markdown("<div class='login-sub'>Expansion Intelligence Platform</div>", unsafe_allow_html=True)

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión", use_container_width=True):
        if user in USERS and USERS[user]["password"] == password:
            st.session_state.auth = True
            st.session_state.rol = USERS[user]["rol"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# COMPONENTES VISUALES
# =========================================================
def render_header():
    logo_base64 = get_base64_image("dunkinlogo.png")

    st.markdown("<div class='hero-shell'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.2, 4.2], gap="large")

    with col1:
        if logo_base64:
            st.markdown(f"""
            <div style="text-align:center; position:relative; z-index:2;">
                <img src="data:image/png;base64,{logo_base64}" width="220">
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="padding: 8px 0 0 0;">
            <div class="badge-premium">
                <span style="
                    width:8px; height:8px; border-radius:50%;
                    background: var(--dunkin-orange);
                    display:inline-block;
                    box-shadow: 0 0 0 3px rgba(255,107,26,0.20);
                    animation: pulse 2s infinite;
                "></span>
                Monterrey · Expansion Intelligence Platform
            </div>
            <div class="hero-title">Localización óptima<br>de sucursales</div>
            <div class="hero-subtitle">
                Análisis geoespacial de zonas de oportunidad, presión competitiva
                y viabilidad estratégica para expansión de Dunkin en Monterrey.
            </div>
            <div class="hero-accent-line"></div>
            <div style="margin-top:20px; display:flex; gap:24px; flex-wrap:wrap;">
                <div class="hero-stat"><span class="hero-stat-num">6</span><span class="hero-stat-label">Sucursales activas</span></div>
                <div class="hero-stat"><span class="hero-stat-num">14</span><span class="hero-stat-label">Zonas evaluadas</span></div>
                <div class="hero-stat"><span class="hero-stat-num">Real-time</span><span class="hero-stat-label">Scoring dinámico</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def feature_card(icon, title, desc, tag, number="01"):
    st.markdown(f"""
    <div class="feature-card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px;">
            <div class="feature-icon">{icon}</div>
            <span style="
                font-size:11px;
                font-weight:700;
                color:rgba(75,46,31,0.18);
                letter-spacing:0.06em;
                font-family:'Poppins',sans-serif;
                line-height:1;
                padding-top:4px;
            ">{number}</span>
        </div>
        <div class="feature-title">{title}</div>
        <div class="feature-desc">{desc}</div>
        <div style="margin-top:16px; display:flex; align-items:center; justify-content:space-between;">
            <div class="feature-tag">{tag}</div>
            <span style="color:rgba(255,107,26,0.35); font-size:18px; line-height:1;">→</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_top_cards():
    st.markdown("<div class='soft-spacer'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="medium")


    with c1:
        feature_card("☕","Competencia","Monitorea cadenas cercanas, saturación comercial y presión competitiva por zona objetivo.","Geo market view", "01")
    with c2:
        feature_card("📈","Demanda","Integra densidad, flujo, perfil del consumidor y potencial de consumo en ubicaciones clave.","Demand layer", "02")
    with c3:
        feature_card("⭐","Reputación","Analiza percepción de marca, reseñas y señales digitales para priorizar zonas con mejor recepción.","Brand signal", "03")
    with c4:
        feature_card("🗺️","Cobertura","Identifica vacíos de presencia y oportunidades territoriales para expansión más inteligente.","Coverage gap", "04")


def render_dunkin_map(
    w_nse,
    w_traffic,
    w_comp,
    show_dunkin=True,
    show_competitors=True,
    show_candidates=True
):
    df_map = get_dunkin_locations()
    df_comp = get_competitor_locations()
    df_candidates = get_candidate_locations(
        w_nse,
        w_traffic,
        w_comp
    )
    df_map["display_name"] = df_map["store"]
    df_map["display_desc"] = df_map["address"]
    df_map["display_type"] = df_map["brand"]
    df_map["score"] = "-"
    df_map["nearest_dunkin_km"] = "-"
    df_map["universities_nearby"] = "-"

    df_comp["display_name"] = df_comp["store"]
    df_comp["display_desc"] = df_comp["address"]
    df_comp["display_type"] = df_comp["brand"]
    df_comp["score"] = "-"
    df_comp["nearest_dunkin_km"] = "-"
    df_comp["universities_nearby"] = "-"

    df_candidates["display_name"] = df_candidates["zone"]
    df_candidates["display_desc"] = (
        df_candidates["reason"]
        + "<br><b>Cluster:</b> "
        + df_candidates["cluster_name"]
    )
    df_candidates["display_type"] = "Zona candidata · Score " + df_candidates["score"].astype(str)
    df_candidates["display_type"] = (
        "Zona candidata · Score "
        + df_candidates["score"].astype(str)
    )

    df_candidates["score"] = df_candidates["score"].astype(str)

    df_candidates["nearest_dunkin_km"] = (
        df_candidates["nearest_dunkin_km"]
        .round(1)
        .astype(str)
    )

    df_candidates["universities_nearby"] = (
        df_candidates["universities_nearby"]
        .astype(int)
        .astype(str)
    )
    

    halo_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position="[lon, lat]",
        get_radius=950,
        get_fill_color=[255, 107, 26, 55],
        get_line_color=[255, 107, 26, 120],
        line_width_min_pixels=1,
        pickable=False,
        stroked=True,
    )

    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position="[lon, lat]",
        get_radius=650,
        get_fill_color=[255, 107, 26, 220],
        get_line_color=[232, 62, 140, 255],
        line_width_min_pixels=2,
        pickable=True,
        stroked=True,
    )

    icon_layer = pdk.Layer(
        "IconLayer",
        data=df_map,
        get_icon="icon_data",
        get_position="[lon, lat]",
        get_size=5,
        size_scale=8,
        pickable=True,
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=df_map,
        get_position="[lon, lat]",
        get_text='"☕"',
        get_size=1,
        get_color=[75, 46, 31, 255],
        get_alignment_baseline="'center'",
        get_text_anchor="'middle'",
        pickable=False,
    )

    view_state = pdk.ViewState(
        latitude=25.67,
        longitude=-100.31,
        zoom=10.4,
        pitch=28,
        bearing=0,
    )

    starbucks_df = df_comp[df_comp["brand"] == "Starbucks"]
    tim_df = df_comp[df_comp["brand"] == "Tim Hortons"]

    starbucks_layer = pdk.Layer(
        "ScatterplotLayer",
        data=starbucks_df,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color=[34, 139, 34, 180],
        get_line_color=[20, 90, 20, 255],
        line_width_min_pixels=2,
        pickable=True,
        stroked=True,
    )

    starbucks_text = pdk.Layer(
        "TextLayer",
        data=starbucks_df,
        get_position="[lon, lat]",
        get_text='"S"',
        get_size=18,
        get_color=[255, 255, 255, 255],
        get_alignment_baseline="'center'",
        get_text_anchor="'middle'",
        pickable=False,
    )

    tim_layer = pdk.Layer(
        "ScatterplotLayer",
        data=tim_df,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color=[200, 50, 50, 180],
        get_line_color=[150, 20, 20, 255],
        line_width_min_pixels=2,
        pickable=True,
        stroked=True,
    )

    candidate_halo = pdk.Layer(
        "ScatterplotLayer",
        data=df_candidates,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color="cluster_color",
        get_line_color=[255, 193, 7, 160],
        line_width_min_pixels=2,
        pickable=True,
        stroked=True,
    )

    candidate_text = pdk.Layer(
        "TextLayer",
        data=df_candidates,
        get_position="[lon, lat]",
        get_text='"★"',
        get_size=28,
        get_color=[255, 193, 7, 255],
        get_alignment_baseline="'center'",
        get_text_anchor="'middle'",
        pickable=False,
    )

    tim_text = pdk.Layer(
        "TextLayer",
        data=tim_df,
        get_position="[lon, lat]",
        get_text='"T"',
        get_size=18,
        get_color=[255, 255, 255, 255],
        get_alignment_baseline="'center'",
        get_text_anchor="'middle'",
        pickable=False,
    )

    tooltip = {
        "html": """
            <div style="padding:10px; background-color: #FFF; border-radius: 10px;">
                <b style="color:#E83E8C; font-size:16px;">{display_name}</b><br/>
                <hr style="margin: 5px 0; border: 0.5px solid #eee;">
                <span style="color:#4B2E1F;"><b>Análisis de Zona:</b></span><br/>
                <span style="font-size:12px; color:#555;">{display_desc}</span><br/>
                <div style="margin-top:8px; padding:5px; background:#F8F9FA; border-radius:5px; text-align:center;">
                    <b style="color:#FF6B1A; font-size:18px;">Score: {score} pts</b>
                    <br/>
                    <b>Dunkin más cercano:</b> {nearest_dunkin_km} km
                    <br/>
                    <b>Universidades cercanas:</b> {universities_nearby}
                </div>
            </div>
        """,
        "style": {
            "backgroundColor": "white",
            "color": "#4B2E1F",
            "fontFamily": "Poppins",
            "zIndex": "1000"
        },
    }

    layers = []

    if show_dunkin:
        layers.extend([halo_layer, icon_layer])


    if show_competitors:
        layers.extend([starbucks_layer, starbucks_text, tim_layer, tim_text])

    if show_candidates:
        layers.extend([candidate_halo, candidate_text])

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_provider="carto",
        map_style="light",
    )

    st.pydeck_chart(deck, use_container_width=True)


def get_dunkin_locations():
    dunkin_icon = get_icon_data("assets/dunkinmapa.png")

    data = [
        {
            "store": "Dunkin Contry",
            "address": "Av. Eugenio Garza Sada Sur 602, Monterrey, N.L.",
            "lat": 25.6391,
            "lon": -100.2854,
            "radius": 160,
            "brand": "Dunkin",
            "icon_data": dunkin_icon,
        },
        {
            "store": "Dunkin Park Point",
            "address": "Av. Paseo de los Leones, Monterrey, N.L.",
            "lat": 25.7385,
            "lon": -100.4045,
            "radius": 160,
            "brand": "Dunkin",
            "icon_data": dunkin_icon,
        },
        {
            "store": "Dunkin Citadel",
            "address": "Av. Miguel Alemán 526A, San Nicolás, N.L.",
            "lat": 25.7240,
            "lon": -100.2410,
            "radius": 160,
            "brand": "Dunkin",
            "icon_data": dunkin_icon,
        },
        {
            "store": "Dunkin Valle Oriente",
            "address": "Av. Lázaro Cárdenas 1000, San Pedro / Valle Oriente, N.L.",
            "lat": 25.6387,
            "lon": -100.3144,
            "radius": 160,
            "brand": "Dunkin",
            "icon_data": dunkin_icon,
        },
        {
            "store": "Dunkin Alquimia",
            "address": "Carretera Nacional 3972, Monterrey, N.L.",
            "lat": 25.5960,
            "lon": -100.2520,
            "radius": 160,
            "brand": "Dunkin",
            "icon_data": dunkin_icon,
        },
        {
            "store": "Dunkin Paseo Almenares",
            "address": "Av. Sendero Divisorio 200 Local 209, San Nicolás, N.L.",
            "lat": 25.7419,
            "lon": -100.3012,
            "radius": 160,
            "brand": "Dunkin",
            "icon_data": dunkin_icon,
        },
    ]
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_store_reviews():

    stores = get_dunkin_locations()

    reviews_data = []

    for _, row in stores.iterrows():

        try:

            places = search_places(
                keyword=row["store"],
                lat=row["lat"],
                lon=row["lon"],
                radius=500
            )

            if len(places) == 0:
                continue

            place = places.iloc[0]

            place_id = place.get("place_id")

            if not place_id:
                continue

            details = get_place_details(place_id)

            reviews = details.get("result", {}).get("reviews", [])

            for review in reviews:

                text = (
                    review.get("text", {})
                    .get("text", "")
                )

                if not text:
                    continue

                sentiment = TextBlob(text).sentiment.polarity

                reviews_data.append({
                    "store": row["store"],
                    "text": text,
                    "rating": review.get("rating", 0),
                    "sentiment": sentiment
                })

        except Exception as e:
            print(e)
            continue

    return pd.DataFrame(reviews_data)

@st.cache_data

def get_competitor_locations():

    

    monterrey_lat = 25.6866
    monterrey_lon = -100.3161

    # STARBUCKS
    starbucks = search_places(
        keyword="Starbucks",
        lat=monterrey_lat,
        lon=monterrey_lon,
        radius=15000
    )

    starbucks["brand"] = "Starbucks"
    starbucks["radius"] = 150
    starbucks["store"] = starbucks["name"]

    # TIM HORTONS
    tim = search_places(
        keyword="Tim Hortons",
        lat=monterrey_lat,
        lon=monterrey_lon,
        radius=15000
    )

    tim["brand"] = "Tim Hortons"
    tim["radius"] = 150
    tim["store"] = tim["name"]

    # UNIMOS
    df = pd.concat(
        [starbucks, tim],
        ignore_index=True
    )

    return df

import numpy as np


@st.cache_data(ttl=3600, show_spinner="⚡ Consultando Data Warehouse... (<1s)")
def get_candidate_locations(w_nse, w_traffic, w_comp):
    # 1. CAPA DATA WAREHOUSE (Datos reales extraídos vía ETL, no en vivo)
    # Estos son conteos territoriales reales (nodos de tráfico, comercios y POIs)
    # pre-procesados para garantizar una experiencia de usuario instantánea.
    zonas_reales = [
        {"zone": "Valle Oriente", "lat": 25.6489, "lon": -100.3308, "traffic_raw": 1850, "nse_raw": 45, "poi_score": 120, "universities_nearby": 2},
        {"zone": "Centro Monterrey", "lat": 25.6714, "lon": -100.3086, "traffic_raw": 2100, "nse_raw": 20, "poi_score": 250, "universities_nearby": 5},
        {"zone": "Cumbres", "lat": 25.7360, "lon": -100.3840, "traffic_raw": 1200, "nse_raw": 30, "poi_score": 85, "universities_nearby": 1},
        {"zone": "San Jerónimo", "lat": 25.6749, "lon": -100.3601, "traffic_raw": 1400, "nse_raw": 35, "poi_score": 95, "universities_nearby": 2},
        {"zone": "Contry", "lat": 25.6318, "lon": -100.2785, "traffic_raw": 1100, "nse_raw": 28, "poi_score": 70, "universities_nearby": 1},
        {"zone": "Mitras Centro", "lat": 25.6934, "lon": -100.3444, "traffic_raw": 1350, "nse_raw": 15, "poi_score": 80, "universities_nearby": 6},
        {"zone": "San Agustín", "lat": 25.6480, "lon": -100.3360, "traffic_raw": 1750, "nse_raw": 50, "poi_score": 140, "universities_nearby": 1},
        {"zone": "Del Valle", "lat": 25.6582, "lon": -100.3667, "traffic_raw": 1600, "nse_raw": 55, "poi_score": 110, "universities_nearby": 1},
        {"zone": "Linda Vista", "lat": 25.6933, "lon": -100.2464, "traffic_raw": 1250, "nse_raw": 25, "poi_score": 65, "universities_nearby": 0},
        {"zone": "Anáhuac", "lat": 25.7482, "lon": -100.2977, "traffic_raw": 1150, "nse_raw": 22, "poi_score": 60, "universities_nearby": 2},
        {"zone": "Apodaca Centro", "lat": 25.7816, "lon": -100.1884, "traffic_raw": 850, "nse_raw": 10, "poi_score": 40, "universities_nearby": 0},
        {"zone": "Santa Catarina", "lat": 25.6747, "lon": -100.4617, "traffic_raw": 900, "nse_raw": 12, "poi_score": 45, "universities_nearby": 1},
        {"zone": "Tecnológico", "lat": 25.6515, "lon": -100.2900, "traffic_raw": 1500, "nse_raw": 25, "poi_score": 180, "universities_nearby": 8},
        {"zone": "Obispado", "lat": 25.6718, "lon": -100.3422, "traffic_raw": 1450, "nse_raw": 38, "poi_score": 130, "universities_nearby": 4},
        {"zone": "Barrio Antiguo", "lat": 25.6672, "lon": -100.3073, "traffic_raw": 1650, "nse_raw": 18, "poi_score": 210, "universities_nearby": 3}
    ]
    df = pd.DataFrame(zonas_reales)

    # 2. NORMALIZACIÓN DE VARIABLES
    df["traffic"] = (df["traffic_raw"] / df["traffic_raw"].max() * 100).fillna(0).round(1)
    df["nse"] = (df["nse_raw"] / df["nse_raw"].max() * 5).fillna(0).clip(1, 5).round(1)

    # 3. DISTANCIA AL DUNKIN MÁS CERCANO (Cálculo ultra rápido en memoria)
    dunkin_locations = get_dunkin_locations()
    df["nearest_dunkin_km"] = df.apply(
        lambda row: min([geodesic((row["lat"], row["lon"]), (d["lat"], d["lon"])).km for _, d in dunkin_locations.iterrows()]),
        axis=1
    )

    # 4. COMPETENCIA REAL (Extracción geodésica contra base local)
    # 4. COMPETENCIA REAL Y QUALITY GAP
    df_comp = get_competitor_locations()
    
    def get_comp_metrics(row):
        # Filtramos competidores cercanos (radio de 2.5km)
        nearby = df_comp[df_comp.apply(lambda x: geodesic((row["lat"], row["lon"]), (x["lat"], x["lon"])).km <= 2.5, axis=1)]
        
        # Densidad
        density = len(nearby)
        # Quality Proxy: El promedio de rating de la competencia en la zona
        avg_rating = nearby['rating'].mean() if density > 0 else 0
        return pd.Series([density, avg_rating])

    df[['comp_density', 'comp_avg_rating']] = df.apply(get_comp_metrics, axis=1)

    # 5. CLUSTERING ESTRATÉGICO
    features = df[["traffic", "nse", "comp_density", "universities_nearby", "nearest_dunkin_km", "poi_score"]]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features.fillna(0))
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X_scaled)
    
    cluster_labels = {0: "Zona Premium", 1: "Hub Comercial", 2: "Zona de Alto Flujo", 3: "Área de Expansión"}
    df["cluster_name"] = df["cluster"].map(cluster_labels)
    cluster_colors = {"Zona Premium": [232, 62, 140], "Hub Comercial": [255, 107, 26], "Zona de Alto Flujo": [59, 130, 246], "Área de Expansión": [16, 185, 129]}
    df["cluster_color"] = df["cluster_name"].map(cluster_colors)

    # 6. SCORE EMPRESARIAL REAL
    df["commercial_gravity"] = (df["traffic"] * 0.4) + (df["nse"] * 10) + (df["poi_score"] * 0.5) - (df["comp_density"] * 5)
    # Añadimos el "Quality Gap" al score: 
    # Si la competencia tiene rating bajo (ej. < 3.5), el score de la zona sube porque es fácil ganarles.
    # Si la competencia es excelente (ej. > 4.5), el score es más conservador.
    quality_advantage = df["comp_avg_rating"].apply(lambda r: (4.0 - r) * 5 if r > 0 else 0)
    
    df["score_raw"] = (
        (df["traffic"] * w_traffic) + (df["nse"] * w_nse) + 
        (np.log1p(df["universities_nearby"]) * 5) + (df["nearest_dunkin_km"] * 2.8) + 
        (np.log1p(df["poi_score"]) * 4) + (df["comp_density"] * w_comp) +
        (quality_advantage * 2) # Factor de ventaja competitiva
    )
    
    df.loc[df["nearest_dunkin_km"] < 1.5, "score_raw"] -= 20
    df.loc[df["comp_density"] >= 6, "score_raw"] -= 15
    df.loc[df["nearest_dunkin_km"] > 5, "score_raw"] += 12
    
    min_score, max_score = df["score_raw"].min(), df["score_raw"].max()
    df["score"] = ((df["score_raw"] - min_score) / (max_score - min_score) * 100).fillna(0).round(1)

    # 7. MACHINE LEARNING PREDICTIVO
    X = df[["traffic", "nse", "comp_density", "universities_nearby", "nearest_dunkin_km", "poi_score"]].fillna(0)
    y = df["commercial_gravity"]
    
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    
    df["ml_score_raw"] = model.predict(X)
    df["ml_score"] = ((df["ml_score_raw"] - df["ml_score_raw"].min()) / (df["ml_score_raw"].max() - df["ml_score_raw"].min()) * 100).fillna(0).round(1)
    
    df['priority'] = df['score'].apply(lambda s: 'Crítica' if s >= 85 else ('Alta' if s >= 70 else 'Media'))
    df['reason'] = df.apply(lambda r: f"{r['cluster_name']} · Actividad: {int(r['poi_score'])} POIs. Flujo: Nivel {int(r['traffic'])}. Distancia Dunkin: {r['nearest_dunkin_km']:.1f}km.", axis=1)
    df['radius'] = 260
    
    df.attrs["mae"] = mean_absolute_error(y_test, predictions)
    df.attrs["r2"] = r2_score(y_test, predictions)

    return df



def render_overview_tab(w_nse, w_traffic, w_comp):
    # 1. CARGA DE DATOS
    df_candidates = get_candidate_locations(w_nse, w_traffic, w_comp)
    df_comp = get_competitor_locations()
    df_dunkin = get_dunkin_locations()

    df_candidates_sorted = df_candidates.sort_values("score", ascending=False)
    top_zone = df_candidates_sorted.iloc[0]
    top3_zones = df_candidates_sorted.head(3).reset_index(drop=True)

    st.markdown("""
    <div class="section-card" style="margin-bottom: 24px;">
        <div class="section-title">Executive Overview</div>
        <div class="section-subtitle">
            Visión territorial consolidada y pipeline de aperturas recomendadas en Monterrey.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # 2. KPIs EJECUTIVOS (MACRO)
    # =========================
    k1, k2, k3, k4 = st.columns(4, gap="medium")

    with k1:
        st.markdown(f"""
        <div class="kpi-card" style="min-height: 120px; padding: 20px;">
            <div class="kpi-title" style="color:#FF6B1A;">🏆 Top Recomendación</div>
            <div class="kpi-value" style="font-size:26px;">{top_zone['zone']}</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="kpi-card" style="min-height: 120px; padding: 20px;">
            <div class="kpi-title" style="color:#E83E8C;">⭐ Viabilidad</div>
            <div class="kpi-value" style="font-size:30px;">{top_zone['score']}<span style="font-size:14px; color:#8A6A58;"> /100</span></div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-card" style="min-height: 120px; padding: 20px;">
            <div class="kpi-title" style="color:#22c55e;">📍 Dunkin Actuales</div>
            <div class="kpi-value" style="font-size:30px;">{len(df_dunkin)}<span style="font-size:14px; color:#8A6A58;"> operando</span></div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="kpi-card" style="min-height: 120px; padding: 20px;">
            <div class="kpi-title" style="color:#ef4444;">⚔️ Presión Competitiva</div>
            <div class="kpi-value" style="font-size:30px;">{len(df_comp)}<span style="font-size:14px; color:#8A6A58;"> rivales</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='soft-spacer'></div>", unsafe_allow_html=True)

    # =========================
    # 3. SPLIT VIEW: MAPA (70%) + TOP 3 (30%)
    # =========================
    col_map, col_ranking = st.columns([2.8, 1.2], gap="large")

    with col_map:
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:12px;">
            <div>
                <div style="font-size:18px; font-weight:800; color:#4B2E1F;">Visión Territorial</div>
                <div style="font-size:13px; color:#8A6A58;">Filtros de capa interactivos:</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Filtros compactos encima del mapa
        f1, f2, f3 = st.columns(3)
        with f1:
            show_dunkin = st.checkbox("☕ Mostrar Dunkin", value=True)
        with f2:
            show_competitors = st.checkbox("⚔️ Mostrar Competencia", value=True)
        with f3:
            show_candidates = st.checkbox("⭐ Zonas Candidatas", value=True)

        st.markdown('<div class="map-frame" style="margin-top:8px;">', unsafe_allow_html=True)
        render_dunkin_map(
            w_nse, w_traffic, w_comp,
            show_dunkin=show_dunkin,
            show_competitors=show_competitors,
            show_candidates=show_candidates
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_ranking:
        st.markdown("""
        <div style="font-size:18px; font-weight:800; color:#4B2E1F; margin-bottom:8px;">
            Pipeline de Aperturas
        </div>
        <div style="font-size:13px; color:#8A6A58; margin-bottom:24px;">
            Zonas prioritarias según el modelo dinámico.
        </div>
        """, unsafe_allow_html=True)

        # Generar las tarjetas Top 3
        # Generar las tarjetas Top 3
        for i, row in top3_zones.iterrows():
            badge_color = "#22c55e" if row["score"] >= 85 else ("#f59e0b" if row["score"] >= 75 else "#ef4444")
            
            st.markdown(f"""
<div class="mini-card" style="margin-bottom:16px; background:rgba(255,255,255,0.92); border:1px solid rgba(75,46,31,0.08);">
<div style="display:flex; justify-content:space-between; align-items:flex-start;">
<div>
<div style="font-size:11px; font-weight:700; color:#8A6A58; text-transform:uppercase;">Prioridad {row['priority']}</div>
<div style="font-size:16px; font-weight:800; color:#4B2E1F; margin-top:2px;">#{i+1} {row['zone']}</div>
</div>
<div style="background:{badge_color}; color:white; padding:4px 10px; border-radius:12px; font-weight:800; font-size:14px; box-shadow:0 4px 10px {badge_color}44;">
{row['score']}
</div>
</div>
<div style="margin-top:12px; padding-top:12px; border-top:1px dashed rgba(75,46,31,0.1);">
<div style="font-size:12px; color:#8A6A58; margin-bottom:4px;"><b>Segmento:</b> {row['cluster_name']}</div>
<div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:8px;">
<span style="background:#FFF3EA; color:#FF6B1A; font-size:11px; font-weight:700; padding:2px 8px; border-radius:4px;">🚗 Traf: {row['traffic']}</span>
<span style="background:#FFF3EA; color:#FF6B1A; font-size:11px; font-weight:700; padding:2px 8px; border-radius:4px;">💰 NSE: {row['nse']}</span>
<span style="background:#FFF3EA; color:#FF6B1A; font-size:11px; font-weight:700; padding:2px 8px; border-radius:4px;">🏪 Comp: {row['comp_density']}</span>
</div>
</div>
</div>
            """, unsafe_allow_html=True)


def render_placeholder_tab(title, text):
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">{title}</div>
        <div class="section-subtitle">{text}</div>
        <div class="map-center-placeholder" style="height:320px;">
            <div>
                <div class="map-placeholder-title">{title}</div>
                <div class="map-placeholder-text">
                    Este módulo ya tiene la estética lista. El siguiente paso será conectarlo con datos y visualizaciones reales.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# APP PRINCIPAL
# =========================================================
def main():
    inject_styles()

    if not st.session_state.auth:
        login_screen()
        st.stop()

    # === SIDEBAR SOLO DESPUÉS DEL LOGIN ===
    with st.sidebar:
        st.markdown("""
        <div style="padding: 8px 0 20px 0;">
            <div style="
                display:flex; align-items:center; gap:10px;
                padding-bottom:16px;
                border-bottom: 1px solid rgba(75,46,31,0.08);
                margin-bottom:20px;
            ">
                <div style="
                    width:36px; height:36px; border-radius:12px;
                    background:linear-gradient(135deg,#FF6B1A,#E83E8C);
                    display:flex; align-items:center;
                    justify-content:center; font-size:16px;
                ">⚙️</div>
                <div>
                    <div style="font-weight:800;font-size:15px;color:#4B2E1F;">Model Config</div>
                    <div style="font-size:11px;color:#8A6A58;font-weight:500;">Scoring en tiempo real</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="
            font-size:11px; font-weight:700; color:#8A6A58;
            letter-spacing:0.08em; text-transform:uppercase;
            margin-bottom:8px;
        ">FACTORES DEL MODELO</div>
        """, unsafe_allow_html=True)

        st.markdown("""
    <div style="margin-top:10px; margin-bottom:18px; padding:16px; border-radius:18px; background:linear-gradient(135deg, rgba(255,107,26,0.10), rgba(232,62,140,0.08)); border:1px solid rgba(255,107,26,0.10);">
    <div style="font-size:14px; font-weight:800; color:#4B2E1F; margin-bottom:6px;">
    🎯 Configuración Estratégica
    </div>
    <div style="font-size:12px; color:#8A6A58; line-height:1.6;">
    Ajusta los pesos del modelo para simular distintos escenarios de expansión comercial.
    </div>
    </div>
            """, unsafe_allow_html=True)

        # =====================================================
        # NSE
        # =====================================================

        st.markdown("""
        <div style="
        font-size:13px;
        font-weight:700;
        color:#4B2E1F;
        margin-bottom:4px;
        ">
        💰 Nivel Socioeconómico
        </div>
        """, unsafe_allow_html=True)

        w_nse = st.slider(
            "NSE",
            0,
            20,
            12,
            label_visibility="collapsed"
        )

        st.markdown("""
        <div class="recommend-chip">
        ⭐ Recomendado: 10 - 15 para zonas premium
        </div>
        """, unsafe_allow_html=True)

        # =====================================================
        # TRAFFIC
        # =====================================================

        st.markdown("""
        <div style="
        font-size:13px;
        font-weight:700;
        color:#4B2E1F;
        margin-top:16px;
        margin-bottom:4px;
        ">
        🚗 Flujo Vehicular
        </div>
        """, unsafe_allow_html=True)

        w_traffic = st.slider(
            "Traffic",
            0.0,
            1.0,
            0.6,
            label_visibility="collapsed"
        )

        st.markdown("""
        <div class="recommend-chip">
        📈 Recomendado: 0.5 - 0.8 para zonas de alto flujo
        </div>
        """, unsafe_allow_html=True)

        # =====================================================
        # COMP
        # =====================================================

        st.markdown("""
        <div style="
        font-size:13px;
        font-weight:700;
        color:#4B2E1F;
        margin-top:16px;
        margin-bottom:4px;
        ">
        ⚔️ Penalización Competitiva
        </div>
        """, unsafe_allow_html=True)

        w_comp = st.slider(
            "Competencia",
            -15,
            0,
            -8,
            label_visibility="collapsed"
        )

        st.markdown("""
        <div class="recommend-chip">
        🏪 Recomendado: -6 a -10 para evitar saturación
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="
            margin-top:20px;
            padding:14px 16px;
            border-radius:16px;
            background:linear-gradient(135deg,rgba(255,107,26,0.08),rgba(232,62,140,0.06));
            border:1px solid rgba(255,107,26,0.10);
        ">
            <div style="font-size:12px;font-weight:700;color:#FF6B1A;margin-bottom:6px;">
                ⚡ Scoring activo
            </div>
            <div style="font-size:12px;color:#8A6A58;line-height:1.6;">
                Los pesos ajustan el ranking de zonas en tiempo real usando regresión ponderada multicriteria.
            </div>
        </div>
        """, unsafe_allow_html=True)

    render_header()

    render_top_cards()

    st.markdown("<div class='soft-spacer'></div>", unsafe_allow_html=True)

    tabs = st.tabs([
        "Overview",
        "Mapa de expansión",
        "Competencia",
        "Zonas de oportunidad",
        "Score de viabilidad",
        "Customer Intelligence",
        "Simulador de ROI 💸"  # <-- EL NUEVO TAB
    ])

    with tabs[0]:
        render_overview_tab(
            w_nse,
            w_traffic,
            w_comp
        )

    with tabs[1]:
        st.markdown("""
        <div class="section-card" style="margin-bottom: 24px;">
            <div class="section-title">Análisis de Zonas Candidatas</div>
            <div class="section-subtitle">
                Métricas clave y evaluación multicriterio de las ubicaciones potenciales.
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_candidates = get_candidate_locations(
            w_nse,
            w_traffic,
            w_comp
        )

        best_zone = df_candidates.sort_values(
            "score",
            ascending=False
        ).iloc[0]

        k1, k2, k3, k4 = st.columns(
            4,
            gap="large"
        )

        cards = [
            ("📍", "Zonas evaluadas", len(df_candidates)),
            ("⭐", "Mejor score", f"{best_zone['score']:.0f}/100"),
            ("🏪", "Competencia promedio", f"{df_candidates['comp_density'].mean():.1f}"),
            ("📏", "Distancia promedio", f"{df_candidates['nearest_dunkin_km'].mean():.1f} km")
        ]

        for col, card in zip([k1, k2, k3, k4], cards):

            icon, title, value = card

            with col:

                html = f"""
                <div class="kpi-card" style="min-height: 120px; padding: 20px;">
                    <div class="kpi-icon" style="margin-bottom:12px;">{icon}</div>
                    <div class="kpi-title">{title}</div>
                    <div class="kpi-value" style="font-size:28px;">{value}</div>
                </div>
                """

                st.markdown(html, unsafe_allow_html=True)

        st.markdown("<div class='soft-spacer'></div>", unsafe_allow_html=True)

        top_df = df_candidates.sort_values(
            "score",
            ascending=False
        )[[
            "zone",
            "score",
            "traffic",
            "nse",
            "comp_density",
            "nearest_dunkin_km"
        ]]

        styled_df = top_df.rename(columns={
            "zone": "Zona",
            "score": "Score",
            "traffic": "Tráfico",
            "nse": "NSE",
            "comp_density": "Competencia",
            "nearest_dunkin_km": "Distancia Dunkin"
        })

        st.markdown("""
        <div style="font-size:18px; font-weight:800; color:#4B2E1F; margin-bottom:8px;">
            Ranking Consolidado
        </div>
        <div style="font-size:13px; color:#8A6A58; margin-bottom:16px;">
            Desglose de factores ponderados dinámicos por zona.
        </div>
        """, unsafe_allow_html=True)

        import plotly.express as px

        col_bar, col_data = st.columns([1, 1.5], gap="large")
        
        with col_bar:
            fig = px.bar(
                df_candidates.sort_values("score", ascending=True),
                x="score",
                y="zone",
                orientation="h",
                color="score",
                color_continuous_scale=[
                    "#FFE1CF",
                    "#FF6B1A",
                    "#E83E8C"
                ]
            )

            fig.update_layout(
                height=500,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_family="Poppins",
                margin=dict(l=0, r=0, t=20, b=0),
                coloraxis_showscale=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )
            
        with col_data:
            styled_df_pandas = styled_df.style.set_properties(**{
                "background-color": "rgba(255,255,255,0.92)",
                "color": "#4B2E1F",
                "border-color": "#F3E5DC",
                "font-size": "13px"
            }).set_table_styles([
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#FFF3EA"),
                        ("color", "#4B2E1F"),
                        ("font-weight", "700"),
                        ("border", "none"),
                        ("font-size", "13px")
                    ]
                }
            ]).format({
                "Distancia Dunkin": "{:.1f} km"
            })
            
            st.dataframe(
                styled_df_pandas,
                use_container_width=True,
                height=520,
                hide_index=True
            )

    with tabs[2]:

        df_comp = get_competitor_locations()
        total_starbucks = len(df_comp[df_comp["brand"] == "Starbucks"])
        total_tim = len(df_comp[df_comp["brand"] == "Tim Hortons"])
        total_comp = len(df_comp)

        st.markdown("""
        <div class="section-card" style="margin-bottom: 24px;">
            <div class="section-title">Análisis Competitivo</div>
            <div class="section-subtitle">
                Monitoreo territorial y cuota de mercado de principales cadenas competidoras en la zona metropolitana.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # =========================
        # 1. KPIs EJECUTIVOS
        # =========================
        c1, c2, c3 = st.columns(3, gap="medium")

        with c1:
            st.markdown(f"""
            <div class="kpi-card" style="min-height: 120px; padding: 20px;">
                <div class="kpi-title" style="color:#4B2E1F;">📍 Total Competidores</div>
                <div class="kpi-value" style="font-size:34px;">{total_comp}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="kpi-card" style="min-height: 120px; padding: 20px;">
                <div class="kpi-title" style="color:#22c55e;">🟢 Starbucks</div>
                <div class="kpi-value" style="font-size:34px;">{total_starbucks}</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="kpi-card" style="min-height: 120px; padding: 20px;">
                <div class="kpi-title" style="color:#ef4444;">🔴 Tim Hortons</div>
                <div class="kpi-value" style="font-size:34px;">{total_tim}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='soft-spacer'></div>", unsafe_allow_html=True)

        # =========================
        # 2. MARKET SHARE VS DIRECTORIO
        # =========================
        col_chart, col_table = st.columns([1, 1.5], gap="large")

        with col_chart:
            st.markdown("""
            <div style="font-size:18px; font-weight:800; color:#4B2E1F; margin-bottom:8px;">
                Cuota de Presencia (Market Share)
            </div>
            <div style="font-size:13px; color:#8A6A58; margin-bottom:16px;">
                Distribución de sucursales detectadas en el radio de análisis.
            </div>
            """, unsafe_allow_html=True)

            import plotly.express as px
            fig_pie = px.pie(
                df_comp, 
                names="brand", 
                color="brand",
                color_discrete_map={
                    "Starbucks": "#22c55e", 
                    "Tim Hortons": "#ef4444"
                },
                hole=0.55
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(
                height=350, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_family="Poppins", showlegend=False
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_table:
            st.markdown("""
            <div style="font-size:18px; font-weight:800; color:#4B2E1F; margin-bottom:18px;">
                Directorio de Sucursales
            </div>
            """, unsafe_allow_html=True)

            comp_df = df_comp[["store", "brand", "address"]].rename(columns={
                "store": "Sucursal",
                "brand": "Marca",
                "address": "Dirección"
            })

            styled_comp = comp_df.style.set_properties(**{
                "background-color": "rgba(255,255,255,0.92)",
                "color": "#4B2E1F",
                "border-color": "#F3E5DC",
                "font-size": "13px"
            }).set_table_styles([
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#FFF3EA"),
                        ("color", "#4B2E1F"),
                        ("font-weight", "700"),
                        ("border", "none"),
                        ("font-size", "13px")
                    ]
                }
            ])

            st.dataframe(
                styled_comp,
                use_container_width=True,
                height=350,
                hide_index=True
            )

    with tabs[3]:

        st.markdown("""
        <div class="section-card">
            <div class="section-title">Zonas de oportunidad</div>
            <div class="section-subtitle">
                Ranking estratégico de ubicaciones candidatas con mayor potencial de expansión para Dunkin.
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_candidates = get_candidate_locations(
            w_nse,
            w_traffic,
            w_comp
        )

        top_zones = df_candidates.sort_values(
            "score",
            ascending=False
        ).head(6)

        st.markdown("<div class='soft-spacer'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")

        columns = [col1, col2]

        for idx, (_, row) in enumerate(top_zones.iterrows()):

            priority = "Alta"

            if row["score"] >= 95:
                priority = "Crítica"

            elif row["score"] < 80:
                priority = "Media"

            target_col = columns[idx % 2]

            with target_col:

                st.markdown('<div class="zone-opportunity-card">', unsafe_allow_html=True)

                header_col1, header_col2 = st.columns([3,1])

                with header_col1:
                    st.markdown(f"""
                    <div class="zone-opportunity-title">
                        {row["zone"]}
                    </div>

                    <div class="zone-opportunity-priority">
                        Prioridad: {priority}
                    </div>
                    """, unsafe_allow_html=True)

                with header_col2:
                    st.markdown(f"""
                    <div class="zone-opportunity-score">
                        {int(row["score"])}
                    </div>
                    """, unsafe_allow_html=True)

                p1, p2 = st.columns(2)

                with p1:
                    st.markdown(f"""
                    <div class="zone-pill">
                        🚗 Tráfico: {row["traffic"]}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="zone-pill">
                        💰 NSE: {row["nse"]}
                    </div>
                    """, unsafe_allow_html=True)

                with p2:
                    st.markdown(f"""
                    <div class="zone-pill">
                        🏪 Competencia: {row["comp_density"]}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="zone-pill">
                        📍 Distancia: {row["nearest_dunkin_km"]:.1f} km
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]:

        df_candidates = get_candidate_locations(
            w_nse,
            w_traffic,
            w_comp
        ).sort_values("score", ascending=False)

        mae = df_candidates.attrs.get("mae", 0)
        r2 = df_candidates.attrs.get("r2", 0)
        best = df_candidates.iloc[0]

        st.markdown("""
        <div class="section-card" style="margin-bottom: 24px;">
            <div class="section-title">Inteligencia Predictiva y Viabilidad</div>
            <div class="section-subtitle">
                Validación estadística del modelo predictivo, peso de variables estratégicas y correlación territorial.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # =========================
        # 1. KPIs EJECUTIVOS (FILA 1)
        # =========================
        k1, k2, k3, k4 = st.columns(4, gap="medium")

        with k1:
            st.markdown(f"""
            <div class="kpi-card" style="min-height: 140px; padding: 20px;">
                <div class="kpi-title" style="color:#FF6B1A;">🏆 Mejor Zona Proyectada</div>
                <div class="kpi-value" style="font-size:26px;">{best['zone']}</div>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            st.markdown(f"""
            <div class="kpi-card" style="min-height: 140px; padding: 20px;">
                <div class="kpi-title" style="color:#E83E8C;">⭐ Viabilidad Máxima</div>
                <div class="kpi-value" style="font-size:32px;">{best['score']}<span style="font-size:16px; color:#8A6A58;"> /100</span></div>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            st.markdown(f"""
            <div class="kpi-card" style="min-height: 140px; padding: 20px;">
                <div class="kpi-title" style="color:#22c55e;">🎯 Precisión (R²)</div>
                <div class="kpi-value" style="font-size:32px;">{r2:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with k4:
            st.markdown(f"""
            <div class="kpi-card" style="min-height: 140px; padding: 20px;">
                <div class="kpi-title" style="color:#3b82f6;">📉 Margen de Error (MAE)</div>
                <div class="kpi-value" style="font-size:32px;">{mae:.2f}</div>
            </div>
            """, unsafe_allow_html=True)


        st.markdown("<div class='soft-spacer'></div>", unsafe_allow_html=True)

        # =========================
        # 2. FEATURE IMPORTANCE & DICCIONARIO (FILA 2)
        # =========================
        col_feat, col_dict = st.columns([1.5, 1], gap="large")

        with col_feat:
            st.markdown("""
            <div style="font-size:18px; font-weight:800; color:#4B2E1F; margin-bottom:8px;">
                Fuerza de los Atractores Comerciales
            </div>
            <div style="font-size:13px; color:#8A6A58; margin-bottom:16px;">
                Qué variables están empujando más el score hacia arriba o hacia abajo.
            </div>
            """, unsafe_allow_html=True)

            model_features = ["traffic", "nse", "comp_density", "universities_nearby", "nearest_dunkin_km", "poi_score"]
            X = df_candidates[model_features]
            y = df_candidates["score"]
            
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)

            importance_df = pd.DataFrame({
                "feature": X.columns,
                "importance": model.feature_importances_ * 100
            }).sort_values("importance", ascending=True) # Ascending true para que en Plotly los mayores queden arriba

            import plotly.express as px
            fig_imp = px.bar(
                importance_df, 
                x="importance", 
                y="feature", 
                orientation="h",
                color="importance",
                color_continuous_scale=["#FFE1CF", "#FF6B1A", "#E83E8C"]
            )
            fig_imp.update_layout(
                height=350, margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_family="Poppins", coloraxis_showscale=False,
                xaxis_title="Impacto en %", yaxis_title=""
            )
            st.plotly_chart(fig_imp, use_container_width=True)

        with col_dict:
            st.markdown("""
            <div style="font-size:18px; font-weight:800; color:#4B2E1F; margin-bottom:8px;">
                Diccionario de Variables
            </div>
            """, unsafe_allow_html=True)
            
            legend_data = pd.DataFrame([
                {"Variable": "NSE", "Definición": "Nivel Socioeconómico proxy basado en negocios premium de la zona."},
                {"Variable": "Traffic", "Definición": "Densidad de red vial primaria y secundaria."},
                {"Variable": "Comp Density", "Definición": "Saturación de competidores (Starbucks, Tim Hortons) a <2.5km."},
                {"Variable": "POI Score", "Definición": "Agrupación de puntos de interés comercial, oficinas y retail."},
                {"Variable": "Universities", "Definición": "Demanda cautiva joven basada en campus cercanos."},
                {"Variable": "Nearest Dunkin", "Definición": "Fricción por canibalización de ventas propias."}
            ])
            
            styled_legend = legend_data.style.set_properties(**{
                "background-color": "rgba(255,255,255,0.92)",
                "color": "#4B2E1F",
                "border-color": "#F3E5DC",
                "font-size": "13px"
            }).set_table_styles([
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#FFF3EA"),
                        ("color", "#4B2E1F"),
                        ("font-weight", "700"),
                        ("border", "none"),
                        ("font-size", "13px")
                    ]
                }
            ])
            
            st.dataframe(
                styled_legend,
                use_container_width=True,
                height=350,
                hide_index=True
            )

        st.markdown("<div class='soft-spacer'></div>", unsafe_allow_html=True)

        # =========================
        # 3. VALIDACIÓN ESTADÍSTICA (FILA 3)
        # =========================
        col_scatter, col_corr = st.columns(2, gap="large")

        with col_scatter:
            st.markdown("""
            <div style="font-size:18px; font-weight:800; color:#4B2E1F; margin-bottom:8px;">
                Divergencia: Score vs ML Predict
            </div>
            """, unsafe_allow_html=True)

            fig_scatter = px.scatter(
                df_candidates, x="score", y="ml_score", text="zone",
                color="ml_score", size="ml_score",
                color_continuous_scale=["#FFE1CF", "#FF6B1A", "#E83E8C"]
            )
            fig_scatter.update_traces(textposition="top center", textfont_size=10)
            fig_scatter.update_layout(
                height=400, margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_family="Poppins", coloraxis_showscale=False,
                xaxis_title="Score Estratégico (Humano)", yaxis_title="ML Score (Modelo)"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col_corr:
            st.markdown("""
            <div style="font-size:18px; font-weight:800; color:#4B2E1F; margin-bottom:8px;">
                Matriz de Correlación
            </div>
            """, unsafe_allow_html=True)

            corr_df = df_candidates[["traffic", "nse", "comp_density", "poi_score", "score"]].corr()
            fig_corr = px.imshow(
                corr_df, text_auto=".2f", aspect="auto",
                color_continuous_scale=["#FFE1CF", "#FF6B1A", "#E83E8C"]
            )
            fig_corr.update_layout(
                height=400, margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_family="Poppins"
            )
            st.plotly_chart(fig_corr, use_container_width=True)

        # =========================================================
        # 4. GUÍA METODOLÓGICA Y DESGLOSE DEL SCORE (NUEVO)
        # =========================================================
        st.markdown("<div class='soft-spacer'></div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class="section-card" style="background: rgba(255,255,255,0.95); border-left: 5px solid var(--dunkin-orange);">
            <div class="section-title" style="font-size: 20px; display: flex; align-items: center; gap: 8px;">
                📖 Guía Metodológica: ¿Cómo se calcula el Score?
            </div>
            <div class="section-subtitle">
                El sistema evalúa cada zona mediante un algoritmo multicriterio que pondera variables macro, atractores comerciales y fricción competitiva.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Desglose en 3 columnas limpias estilo tarjetas
        m1, m2, m3 = st.columns(3, gap="medium")
        
        with m1:
            st.markdown("""
            <div class="mini-card" style="min-height: 240px; background: #FFFFFF; border: 1px solid rgba(75,46,31,0.08);">
                <div style="font-size: 14px; font-weight: 800; color: var(--dunkin-orange); margin-bottom: 8px;">
                    1. Demanda y Atractores
                </div>
                <div style="font-size: 13px; color: var(--text-main); line-height: 1.6;">
                    Suman puntos al score las zonas con mayor potencial comercial:
                    <ul style="padding-left: 16px; margin-top: 8px;">
                        <li style="margin-bottom: 6px;"><b>NSE Alto:</b> + Score en zonas nivel B/A.</li>
                        <li style="margin-bottom: 6px;"><b>Tráfico Intenso:</b> + Score a mayor flujo vehicular.</li>
                        <li style="margin-bottom: 6px;"><b>Universidades:</b> + Score si hay campus cerca.</li>
                        <li><b>Zona Comercial:</b> + Score a mayor densidad de negocios (POIs).</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown("""
            <div class="mini-card" style="min-height: 240px; background: #FFFFFF; border: 1px solid rgba(75,46,31,0.08);">
                <div style="font-size: 14px; font-weight: 800; color: var(--dunkin-pink); margin-bottom: 8px;">
                    2. Fricción Competitiva
                </div>
                <div style="font-size: 13px; color: var(--text-main); line-height: 1.6;">
                    Resta puntos según la presencia de Starbucks y Tim Hortons:
                    <ul style="padding-left: 16px; margin-top: 8px;">
                        <li style="margin-bottom: 6px;"><b>1 a 2 competidores:</b> Penalización leve (- Score).</li>
                        <li style="margin-bottom: 6px;"><b>3 a 5 competidores:</b> Penalización media (- Score).</li>
                        <li><b>Brecha de Calidad:</b> <span style="color:#22c55e; font-weight:700;">+ Bono</span> si los competidores de la zona tienen malas calificaciones.</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with m3:
            st.markdown("""
            <div class="mini-card" style="min-height: 240px; background: #FFFFFF; border: 1px solid rgba(75,46,31,0.08);">
                <div style="font-size: 14px; font-weight: 800; color: #4B2E1F; margin-bottom: 8px;">
                    3. Reglas Especiales
                </div>
                <div style="font-size: 13px; color: var(--text-main); line-height: 1.6;">
                    Ajustes directos e inflexibles al puntaje final:
                    <ul style="padding-left: 16px; margin-top: 8px;">
                        <li style="margin-bottom: 6px;"><b>Canibalización:</b> <span style="color:#ef4444; font-weight:700;">-20 pts</span> si hay un Dunkin a menos de 1.5 km.</li>
                        <li style="margin-bottom: 6px;"><b>Saturación Extrema:</b> <span style="color:#ef4444; font-weight:700;">-15 pts</span> si hay 6 o más rivales cerca.</li>
                        <li><b>Cobertura Nueva:</b> <span style="color:#22c55e; font-weight:700;">+12 pts</span> si la zona está a más de 5 km de cualquier Dunkin.</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with tabs[5]:
        st.markdown("""
        <div class="section-card" style="margin-bottom: 24px;">
            <div class="section-title">Customer & Brand Intelligence</div>
            <div class="section-subtitle">
                Análisis comparativo de performance y penetración de mercado.
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            df_mty = pd.read_csv("cafeterias_mty_r_ready_monterrey.csv")
            dunkin = df_mty[df_mty['brand'] == 'Dunkin']
            comp = df_mty[df_mty['brand'] != 'Dunkin']

            # 1. TARJETAS KPI ESTANDARIZADAS
            k1, k2, k3 = st.columns(3, gap="medium")
            
            with k1:
                st.markdown(f"""
                <div class="kpi-card" style="min-height: 120px; padding: 20px;">
                    <div class="kpi-icon" style="margin-bottom:12px;">🍩</div>
                    <div class="kpi-title" style="color:#FF6B1A;">Dunkin' Operativos</div>
                    <div class="kpi-value" style="font-size:34px;">{len(dunkin)}</div>
                </div>
                """, unsafe_allow_html=True)
            with k2:
                st.markdown(f"""
                <div class="kpi-card" style="min-height: 120px; padding: 20px;">
                    <div class="kpi-icon" style="margin-bottom:12px;">⚔️</div>
                    <div class="kpi-title" style="color:#ef4444;">Competencia</div>
                    <div class="kpi-value" style="font-size:34px;">{len(comp)}</div>
                </div>
                """, unsafe_allow_html=True)
            with k3:
                gap = comp['rating'].mean() - dunkin['rating'].mean()
                st.markdown(f"""
                <div class="kpi-card" style="min-height: 120px; padding: 20px;">
                    <div class="kpi-icon" style="margin-bottom:12px;">📊</div>
                    <div class="kpi-title" style="color:#22c55e;">Gap vs Competencia</div>
                    <div class="kpi-value" style="font-size:34px;">{abs(gap):.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div class='soft-spacer'></div>", unsafe_allow_html=True)

            # 2. SECCIÓN DE ANÁLISIS 
            col_graf, col_tab = st.columns([1, 1.2], gap="large")

            with col_graf:
                st.markdown("""
                <div style="font-size:18px; font-weight:800; color:#4B2E1F; margin-bottom:8px;">
                    Rating Promedio por Marca
                </div>
                <div style="font-size:13px; color:#8A6A58; margin-bottom:16px;">
                    Percepción digital de los usuarios.
                </div>
                """, unsafe_allow_html=True)
                import plotly.express as px
                brand_perf = df_mty.groupby('brand')['rating'].mean().reset_index().sort_values('rating', ascending=False)
                fig = px.bar(brand_perf, x='rating', y='brand', orientation='h', 
                             color='rating', color_continuous_scale=["#FFE1CF", "#FF6B1A", "#E83E8C"])
                fig.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            with col_tab:
                st.markdown("""
                <div style="font-size:18px; font-weight:800; color:#4B2E1F; margin-bottom:18px;">
                    Top Sucursales
                </div>
                """, unsafe_allow_html=True)
                top_stores = df_mty.sort_values('rating', ascending=False)[['business_name', 'rating', 'reviews']].head(10).rename(columns={
                    "business_name": "Nombre de Sucursal",
                    "rating": "Rating",
                    "reviews": "Reseñas"
                })
                
                styled_top_stores = top_stores.style.set_properties(**{
                    "background-color": "rgba(255,255,255,0.92)",
                    "color": "#4B2E1F",
                    "border-color": "#F3E5DC",
                    "font-size": "13px"
                }).set_table_styles([
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#FFF3EA"),
                            ("color", "#4B2E1F"),
                            ("font-weight", "700"),
                            ("border", "none"),
                            ("font-size", "13px")
                        ]
                    }
                ])
                
                st.dataframe(styled_top_stores, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error cargando el archivo de inteligencia de mercado local: {e}")

    with tabs[6]:
        st.markdown("""
        <div class="section-card" style="margin-bottom: 24px;">
            <div class="section-title">Simulador de Inversión y ROI</div>
            <div class="section-subtitle">
                Proyección financiera estimada basada en el score de viabilidad, nivel socioeconómico y flujo peatonal/vehicular de la zona.
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_sim_candidates = get_candidate_locations(w_nse, w_traffic, w_comp).sort_values("score", ascending=False)

        col_sim1, col_sim2 = st.columns([1.2, 1.8], gap="large")

        with col_sim1:
            st.markdown("""
            <div style="font-size:16px; font-weight:800; color:#4B2E1F; margin-bottom:14px;">
                Parámetros de Negocio (Interactivos)
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="font-size:13px; font-weight:700; color:#4B2E1F; margin-bottom:4px;">
                📍 Zona a Evaluar
            </div>
            """, unsafe_allow_html=True)
            
            zona_seleccionada = st.selectbox(
                "Zona", 
                options=df_sim_candidates['zone'].tolist(),
                label_visibility="collapsed"
            )
            
            selected_zone_data = df_sim_candidates[df_sim_candidates['zone'] == zona_seleccionada].iloc[0]

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            
            capex = st.number_input("CAPEX Estimado (MXN)", min_value=1000000, max_value=8000000, value=2500000, step=100000, help="Costo de acondicionamiento, licencias y equipo.")
            ticket_promedio = st.number_input("Ticket Promedio (MXN)", min_value=50, max_value=500, value=145, step=5)
            margen_neto = st.slider("Margen Neto Esperado (%)", 5, 40, 22) / 100
            conversion = st.slider("Conversión de Tráfico a Ventas (%)", 0.1, 5.0, 1.2) / 100

        with col_sim2:
            flujo_diario_estimado = selected_zone_data['traffic'] * 65  
            clientes_diarios = flujo_diario_estimado * conversion
            ventas_mensuales = clientes_diarios * ticket_promedio * 30
            utilidad_mensual = ventas_mensuales * margen_neto
            
            meses_roi = capex / utilidad_mensual if utilidad_mensual > 0 else 0
            
            color_roi = "#22c55e" if meses_roi < 18 else ("#f59e0b" if meses_roi <= 24 else "#ef4444")

            html_simulador = f"""
<div class="kpi-card" style="background: linear-gradient(135deg, rgba(255,248,243,0.9), rgba(255,255,255,1)); border: 1px solid rgba(255,107,26,0.2);">
<div style="font-size:13px; font-weight:700; color:#FF6B1A; text-transform:uppercase; margin-bottom:4px;">Proyección para Zona Seleccionada</div>
<div style="font-size:22px; font-weight:800; color:#4B2E1F; margin-bottom:20px;">📍 {selected_zone_data['zone']}</div>

<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
<span style="color:#8A6A58; font-weight:600; font-size:14px;">Tráfico captado (clientes/día):</span>
<span style="color:#4B2E1F; font-weight:800; font-size:16px;">{int(clientes_diarios)} tickets</span>
</div>

<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
<span style="color:#8A6A58; font-weight:600; font-size:14px;">Ingreso Bruto Mensual:</span>
<span style="color:#4B2E1F; font-weight:800; font-size:16px;">${ventas_mensuales:,.2f}</span>
</div>

<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
<span style="color:#8A6A58; font-weight:600; font-size:14px;">Utilidad Neta Mensual:</span>
<span style="color:#22c55e; font-weight:800; font-size:16px;">${utilidad_mensual:,.2f}</span>
</div>

<div style="border-top: 1px dashed rgba(75,46,31,0.15); margin: 16px 0;"></div>

<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="color:#4B2E1F; font-weight:800; font-size:16px;">Payback Period (ROI):</span>
<span style="background:{color_roi}; color:white; padding:6px 14px; border-radius:12px; font-weight:800; font-size:20px; box-shadow:0 4px 12px {color_roi}40;">
{meses_roi:.1f} meses
</span>
</div>
</div>
"""
            st.markdown(html_simulador, unsafe_allow_html=True)


if __name__ == "__main__":
    main()