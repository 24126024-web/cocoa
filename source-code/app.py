"""Cocoon Analytics - Giai đoạn 5: giao diện Streamlit.

Chạy:  streamlit run app.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from PIL import Image
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

import auth
import data_utils as du

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

    /* Tiêu đề ứng dụng */
    h1 {
        color: #1b4332 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    /* Định dạng Metric KPI Cards */
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

    /* Container cho Biểu đồ & Thống kê */
    div[data-testid="stPlotlyChart"] {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(27, 67, 50, 0.08);
    }

    /* Tab navigation styling */
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

    /* Custom Sidebar */
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

    /* Nút đăng xuất & Button trong sidebar */
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


ALLOW_USER_EXPORT = False

auth.login_gate()
user = auth.current_user()
admin = auth.is_admin()


@st.cache_data(ttl=600, show_spinner="Đang nạp dữ liệu…")
def get_base(signature: tuple) -> pd.DataFrame:
    return du.load_base()


base = du.apply_deletions(get_base(du.data_signature()))


def fmt_int(x) -> str:
    return "—" if pd.isna(x) else f"{int(x):,}".replace(",", ".")


with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=90)
    st.markdown(f"**{user['username']}** · `{user['role']}`")
    if st.button("Đăng xuất"):
        auth.logout()
    st.divider()
    st.header("Bộ lọc")

source = st.sidebar.selectbox("Nền tảng", ["Tất cả", "Shopee", "Hasaki"])
df = base if source == "Tất cả" else base[base["Nguồn"] == source]

if not df.empty and "Hạng mục" in df.columns:
    cats = ["Tất cả"] + sorted([str(x) for x in df["Hạng mục"].dropna().unique() if str(x).strip()])
    category = st.sidebar.selectbox("Hạng mục", cats)
    if category != "Tất cả":
        df = df[df["Hạng mục"] == category]

if not df.empty and "Dòng sản phẩm" in df.columns:
    lines = ["Tất cả"] + sorted([str(x) for x in df["Dòng sản phẩm"].dropna().unique() if str(x).strip()])
    line = st.sidebar.selectbox("Dòng sản phẩm", lines)
    if line != "Tất cả":
        df = df[df["Dòng sản phẩm"] == line]

if not df.empty and "Tên sản phẩm" in df.columns:
    prods = ["Tất cả"] + sorted([str(x) for x in df["Tên sản phẩm"].dropna().unique() if str(x).strip()])
    product = st.sidebar.selectbox("Sản phẩm", prods)
    if product != "Tất cả":
        df = df[df["Tên sản phẩm"] == product]

if not df.empty and "Số sao" in df.columns:
    stars = st.sidebar.multiselect("Số sao", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])
    df = df[df["Số sao"].isin(stars)]

if not df.empty and "Ngày review" in df.columns and df["Ngày review"].notna().any():
    valid_dates = df["Ngày review"].dropna()
    dmin, dmax = valid_dates.min().date(), valid_dates.max().date()
    if dmin <= dmax:
        rng = st.sidebar.date_input("Ngày review", (dmin, dmax), min_value=dmin, max_value=dmax)
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            df = df[(df["Ngày review"].dt.date >= rng[0]) & (df["Ngày review"].dt.date <= rng[1])]

keyword = st.sidebar.text_input("Tìm trong nội dung review")
if keyword.strip() and not df.empty:
    df = df[df["Nội dung review"].str.contains(keyword.strip(), case=False, na=False, regex=False)]

st.sidebar.caption(f"{len(df):,} / {len(base):,} review sau khi lọc".replace(",", "."))
if admin:
    st.sidebar.caption("📁 Dữ liệu: Đã tải")

h1, h2 = st.columns([1, 12], vertical_alignment="center")
if LOGO_PATH.exists():
    h1.image(str(LOGO_PATH), width=70)
h2.title("Cocoon Analytics")
st.caption("Phân tích hành vi người tiêu dùng và phản hồi khách hàng — Shopee & Hasaki")

if df.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc hiện tại.")
    st.stop()

prod = du.product_table(df)
tab_names = ["📊 Tổng quan", "🗂️ Dữ liệu", "📈 Power BI", "🤖 Kết quả mô hình"]
if admin:
    tab_names.append("🔧 Quản trị")
tabs = st.tabs(tab_names)

with tabs[0]:
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Số sản phẩm", fmt_int(len(prod)))
    k2.metric("Số review", fmt_int(len(df)))
    k3.metric("Sao trung bình", f"{df['Số sao'].mean():.2f}" if not df.empty else "0")
    k4.metric("Tỉ lệ tích cực (4–5★)", f"{(df['Số sao'] >= 4).mean():.1%}" if not df.empty else "0%")
    k5.metric("Tỉ lệ tiêu cực (1–2★)", f"{(df['Số sao'] <= 2).mean():.1%}" if not df.empty else "0%")

    st.write("")
    st.subheader("Thống kê Min – Max")
    c1, c2, c3 = st.columns(3)

    def top_product(star: int):
        s = df[df["Số sao"] == star].groupby("Tên sản phẩm").size()
        return (s.idxmax(), int(s.max())) if len(s) else (None, 0)

    p5, n5 = top_product(5)
    p1, n1 = top_product(1)
    with c1:
        st.markdown("**Sản phẩm được 5★ nhiều nhất**")
        st.write(f"{p5} — {n5} lượt" if p5 else "Không có dữ liệu")
        st.markdown("**Sản phẩm bị 1★ nhiều nhất**")
        st.write(f"{p1} — {n1} lượt" if p1 else "Không có review 1★ trong bộ lọc")

    monthly_all = df.dropna(subset=["Tháng"]).groupby("Tháng").size()
    with c2:
        st.markdown("**Tháng nhiều review nhất**")
        if len(monthly_all):
            st.write(f"{monthly_all.idxmax():%m/%Y} — {int(monthly_all.max())} review")
            st.markdown("**Tháng ít review nhất**")
            st.write(f"{monthly_all.idxmin():%m/%Y} — {int(monthly_all.min())} review")
        else:
            st.write("Chưa có thông tin tháng.")
        st.caption("Dữ liệu dùng số review làm thước đo xu hướng mua.")

    rev = prod.dropna(subset=["Doanh thu 30 ngày"])
    rev = rev[rev["Doanh thu 30 ngày"] > 0]
    with c3:
        if len(rev):
            hi = rev.loc[rev["Doanh thu 30 ngày"].idxmax()]
            lo = rev.loc[rev["Doanh thu 30 ngày"].idxmin()]
            st.markdown("**Sản phẩm doanh thu 30 ngày cao nhất**")
            st.write(f"{hi['Tên sản phẩm']} — {fmt_int(hi['Doanh thu 30 ngày'])} ₫")
            st.markdown("**Sản phẩm doanh thu 30 ngày thấp nhất**")
            st.write(f"{lo['Tên sản phẩm']} — {fmt_int(lo['Doanh thu 30 ngày'])} ₫")
        else:
            st.markdown("**Doanh thu 30 ngày**")
            st.write("Không có dữ liệu doanh thu.")

    st.write("")
    st.subheader("Biểu đồ phân tích")
    g1, g2 = st.columns(2)

    with g1:
        pie = rev.groupby("Dòng sản phẩm")["Doanh thu 30 ngày"].sum().reset_index() if not rev.empty else pd.DataFrame()
        if len(pie):
            fig = px.pie(
                pie, 
                names="Dòng sản phẩm", 
                values="Doanh thu 30 ngày", 
                hole=0.45, 
                color_discrete_sequence=COLOR_DISCRETE
            )
            fig = style_plotly_figure(fig, "Cơ cấu doanh thu 30 ngày theo dòng sản phẩm
