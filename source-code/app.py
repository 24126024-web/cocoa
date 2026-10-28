"""Cocoon Analytics - Giai đoạn 5: giao diện Streamlit.

Chạy:  streamlit run app.py
"""
from __future__ import annotations

import io
import os
from pathlib import Path

import pandas as pd
from PIL import Image
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

import auth
import data_utils as du

# Tìm Logo
LOGO_PATH = du.HERE / "logo.png"
if not LOGO_PATH.exists():
    LOGO_PATH = du.HERE / "dataset" / "logo.png"
if hasattr(auth, "LOGO") and isinstance(auth.LOGO, Path) and auth.LOGO.exists():
    LOGO_PATH = auth.LOGO

st.set_page_config(
    page_title="Cocoon Analytics", 
    page_icon=Image.open(LOGO_PATH) if LOGO_PATH.exists() else None, 
    layout="wide"
)

# ==========================================
# CUSTOM CSS DASHBOARD EXECUTIVE UI
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    .stApp {
        background-color: #f4efe6 !important;
    }

    h1 {
        color: #1b4332 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(27, 67, 50, 0.08);
        border-left: 5px solid #1b4332;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #666666 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #1b4332 !important;
    }

    div[data-testid="stPlotlyChart"] {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(27, 67, 50, 0.08);
    }

    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 15px !important;
        color: #555555 !important;
        padding: 10px 20px !important;
    }
    button[aria-selected="true"] {
        color: #1b4332 !important;
        border-bottom-color: #1b4332 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0d1e16 !important;
        color: #ffffff;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #ee4d2d !important;
        border-color: #ee4d2d !important;
    }
</style>
""", unsafe_allow_html=True)

COLOR_DISCRETE = ["#1b4332", "#2d6a4f", "#40916c", "#52b788", "#74c69d", "#b7e4c7"]
MAP_SOURCES = {"Shopee": "#ee4d2d", "Hasaki": "#117a50"}


def style_plotly_figure(fig, title=""):
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(family="Inter, sans-serif", size=15, color="#1b4332")),
        font=dict(family="Inter, sans-serif", color="#444444"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", zeroline=False)
    return fig


ALLOW_USER_EXPORT = True

auth.login_gate()
user = auth.current_user()
admin = auth.is_admin()


@st.cache_data(ttl=600, show_spinner="Đang nạp dữ liệu...")
def get_base(signature: tuple) -> pd.DataFrame:
    return du.load_base()


@st.cache_data(ttl=600, show_spinner="Đang nạp dữ liệu Power BI...")
def get_powerbi_tables(signature: tuple) -> dict:
    return du.load_powerbi_tables()


base = du.apply_deletions(get_base(du.data_signature()))


def fmt_int(x) -> str:
    return "-" if pd.isna(x) else f"{int(x):,}".replace(",", ".")


with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=90)
    st.markdown(f"**{user['username']}** · `{user['role']}`")
    if st.button("Đăng xuất"):
        auth.logout()
        st.rerun()
    st.divider()
    st.header("Bộ lọc")

source = st.sidebar.selectbox("Nền tảng", ["Tất cả", "Shopee", "Hasaki"])
df = base if source == "Tất cả" else base[base["Nguồn"] == source]

categories = ["Tất cả"] + sorted([str(x) for x in df["Hạng mục"].dropna().unique() if str(x).strip()])
category = st.sidebar.selectbox("Hạng mục", categories)
if category != "Tất cả":
    df = df[df["Hạng mục"] == category]

lines = ["Tất cả"] + sorted([str(x) for x in df["Dòng sản phẩm"].dropna().unique() if str(x).strip()])
line = st.sidebar.selectbox("Dòng sản phẩm", lines)
if line != "Tất cả":
    df = df[df["Dòng sản phẩm"] == line]

products = ["Tất cả"] + sorted([str(x) for x in df["Tên sản phẩm"].dropna().unique() if str(x).strip()])
product = st.sidebar.selectbox("Sản phẩm", products)
if product != "Tất cả":
    df = df[df["Tên sản phẩm"] == product]

stars = st.sidebar.multiselect("Số sao", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])
if stars and set(stars) != {1, 2, 3, 4, 5} and not df.empty:
    df = df[df["Số sao"].isin(stars)]

if not df.empty and df["Ngày review"].notna().any():
    valid_dates = df["Ngày review"].dropna()
    dmin, dmax = valid_dates.min().date(), valid_dates.max().date()
    if dmin <= dmax:
        rng = st.sidebar.date_input("Ngày review", (dmin, dmax), min_value=dmin, max_value=dmax)
        if isinstance(rng, (tuple, list)) and len(rng) == 2 and (rng[0] != dmin or rng[1] != dmax):
            df = df[(df["Ngày review"].dt.date >= rng[0]) & (df["Ngày review"].dt.date <= rng[1])]

keyword = st.sidebar.text_input("Tìm trong nội dung review")
if keyword.strip() and not df.empty:
    df = df[df["Nội dung review"].str.contains(keyword.strip(), case=False, na=False, regex=False)]

st.sidebar.caption(f"{int(df['Số sao'].notna().sum()):,} / {int(base['Số sao'].notna().sum()):,} review sau khi lọc".replace(",", "."))
if admin:
    st.sidebar.caption("Dữ liệu: Đã tải")

h1, h2 = st.columns([1, 12], vertical_alignment="center")
if LOGO_PATH.exists():
    h1.image(str(LOGO_PATH), width=70)
h2.title("Cocoon Analytics")
st.caption("Phân tích hành vi người tiêu dùng và phản hồi khách hàng - Shopee & Hasaki")

if df.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc hiện tại.")
    st.stop()

if admin:
    with st.sidebar.expander("🔍 Kiểm tra nguồn dữ liệu"):
        for label, f in (("Hasaki - SP", du.HASAKI_PROD_FILE), ("Hasaki - Review", du.HASAKI_REV_FILE),
                         ("Shopee - SP", du.SHOPEE_PROD_FILE), ("Shopee - Review", du.SHOPEE_REV_FILE)):
            st.caption(f"{label}: {'✅' if f.exists() else '❌'} {f}")
        _hp = du._clean_raw(du._read_table(du.HASAKI_PROD_FILE))
        _hr = du._clean_raw(du._read_table(du.HASAKI_REV_FILE))
        st.caption(f"File SP Hasaki: {len(_hp)} dòng, {_hp['Mã SP'].nunique() if len(_hp) else 0} mã SP")
        st.caption(f"File Review Hasaki: {len(_hr)} dòng, {_hr['Mã SP'].nunique() if len(_hr) else 0} mã SP")
        _hb = base[base["Nguồn"] == "Hasaki"]
        st.caption(f"Sau khi nạp: {_hb['Mã SP'].nunique()} sản phẩm Hasaki")
        if st.button("Xóa cache dữ liệu"):
            st.cache_data.clear()
            st.rerun()

prod = du.product_table(df)
rv = df[df["Số sao"].notna()]   # chỉ các dòng có
