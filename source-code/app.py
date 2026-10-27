"""Cocoon Analytics - Giai đoạn 5: giao diện Streamlit.

Chạy:  streamlit run app.py
"""
from __future__ import annotations

import base64
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
st.set_page_config(page_title="Cocoon Analytics", page_icon=Image.open(LOGO_PATH), layout="wide")

ALLOW_USER_EXPORT = False

# Convert Logo sang Base64
def get_base64_of_bin_file(bin_file):
    p = Path(bin_file)
    if p.exists():
        with open(p, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""

logo_b64 = get_base64_of_bin_file(LOGO_PATH)

# ==============================================================================
# TRANG ĐĂNG NHẬP (SIGN IN - THIẾT KẾ CHUẨN THEO MẪU HÌNH THỨ 2)
# ==============================================================================
if not st.session_state.get("authenticated", False):
    # CSS thuần tách riêng không dùng f-string để tránh vỡ cú pháp Python
    css_login = """
    <style>
    /* Ẩn Header, Footer & Sidebar mặc định */
    [data-testid="stSidebar"] { display: none !important; }
    header { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    
    /* Nền đen xám nhám tổng thể giống hình mẫu thứ 2 */
    .stApp {
        background-color: #2F3331 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }
    
    /* Cấu trúc Cột Bên Trái (Banner Xanh Rêu) */
    .login-left-banner {
        background: linear-gradient(145deg, #1A4D2E 0%, #0F331D 100%);
        border-radius: 24px 0 0 24px;
        padding: 50px 30px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        min-height: 480px;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.2);
    }
    .login-left-banner img {
        width: 110px !important;
        margin-bottom: 20px;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
    }
    .login-left-banner h2 {
        color: #FFFFFF !important;
        font-size: 26px !important;
        font-weight: 700 !important;
        margin-bottom: 12px !important;
    }
    .login-left-banner p {
        color: #C2D6C8 !important;
        font-size: 13.5px !important;
        line-height: 1.5;
        margin-bottom: 30px;
    }
    .btn-signin-outline {
        border: 1.5px solid #FFFFFF;
        background: transparent;
        color: #FFFFFF;
        padding: 8px 35px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 1px;
    }
    .brand-tag {
        margin-top: 40px;
        font-size: 10px;
        color: rgba(255,255,255,0.5);
        letter-spacing: 1px;
    }

    /* Cấu trúc Cột Bên Phải (Form Nền Kem Mộc) */
    div[data-testid="column"]:nth-child(2) {
        background-color: #F8F5EE !important;
        border-radius: 0 24px 24px 0;
        padding: 40px 35px !important;
    }
    
    .login-title {
        color: #1A4D2E !important;
        font-size: 32px !important;
        font-weight: 700 !important;
        margin-bottom: 4px;
        text-transform: lowercase;
    }
    .login-sub {
        color: #666666 !important;
        font-size: 13.5px !important;
        margin-bottom: 25px;
    }

    /* Sửa Lỗi Font & Style Ô Nhập Liệu Input */
    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border: 1px solid #2E6F40 !important;
        border-radius: 20px !important;
        padding: 2px 8px !important;
    }
    div[data-baseweb="input"] input {
        color: #1A4D2E !important;
        font-size: 14px !important;
    }
    label {
        color: #1A4D2E !important;
        font-weight: 600 !important;
    }

    /* Style Nút Bấm LOG IN */
    div.stButton > button {
        background-color: #1A4D2E !important;
        color: #FFFFFF !important;
        border-radius: 22px !important;
        padding: 10px 0 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(26, 77, 46, 0.3) !important;
        margin-top: 15px !important;
    }
    div.stButton > button:hover {
        background-color: #11331E !important;
        box-shadow: 0 6px 16px rgba(26, 77, 46, 0.4) !important;
    }
    </style>
    """
    st.markdown(css_login, unsafe_allow_html=True)

    # Đưa Card vào giữa màn hình
    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    _, card_col, _ = st.columns([1, 6, 1])
    
    with card_col:
        c_left, c_right = st.columns([1, 1.1], gap="small")
        
        # Cột Bên Trái (Xanh Rêu)
        with c_left:
            img_html = f'<img src="data:image/png;base64,{logo_b64}"/>' if logo_b64 else '🌿'
            left_content = f"""
            <div class="login-left-banner">
                {img_html}
                <h2>Welcome Back!</h2>
                <p>To stay connected with us please login with your personal info</p>
                <div class="btn-signin-outline">SIGN IN</div>
                <div class="brand-tag">COCOON ORIGINAL VIETNAM | NATURALLY CRAFTED</div>
            </div>
            """
            st.markdown(left_content, unsafe_allow_html=True)

        # Cột Bên Phải (Form Đăng nhập Nền Kem)
        with c_right:
            st.markdown("""
                <div class="login-title">welcome</div>
                <div class="login-sub">Login in to your account to continue</div>
            """, unsafe_allow_html=True)
            
            # Gọi Form Đăng nhập từ auth.py
            auth.login_gate()
            
            st.markdown("""
                <div style="text-align: center; margin-top: 15px; font-size: 13px; color: #666666;">
                    Don't have an account? <a href="#" style="color: #1A4D2E; font-weight: 700; text-decoration: none;">Sign up</a>
                </div>
            """, unsafe_allow_html=True)
            
    st.stop()

# ==============================================================================
# TRANG DASHBOARD CHÍNH (Đã Đăng Nhập Thành Công)
# ==============================================================================
user = auth.current_user()
admin = auth.is_admin()

# Thêm Theme CSS cho trang Dashboard
st.markdown("""
<style>
.stApp { background-color: #F8F5EE !important; }
[data-testid="stSidebar"] { background: #1A4D2E !important; }
[data-testid="stSidebar"] * { color: #F8F5EE !important; }
div[data-testid="metric-container"] {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 16px;
    border: 1px solid #E2E8F0;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner="Đang nạp dữ liệu…")
def get_base(signature: tuple) -> pd.DataFrame:
    return du.load_base()

base = du.apply_deletions(get_base(du.data_signature()))

def fmt_int(x) -> str:
    return "—" if pd.isna(x) else f"{int(x):,}".replace(",", ".")

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.image(str(LOGO_PATH), width=90)
    st.markdown(f"👤 **{user['username']}** · `{user['role']}`")
    if st.button("Đăng xuất"):
        auth.logout()
    st.divider()
    st.header("Bộ lọc")

source = st.sidebar.selectbox("Nền tảng", ["Tất cả", "Shopee", "Hasaki"])
df = base if source == "Tất cả" else base[base["Nguồn"] == source]

categories = ["Tất cả"] + sorted(df["Hạng mục"].dropna().unique())
category = st.sidebar.selectbox("Hạng mục", categories)
if category != "Tất cả":
    df = df[df["Hạng mục"] == category]

lines = ["Tất cả"] + sorted(df["Dòng sản phẩm"].dropna().unique())
line = st.sidebar.selectbox("Dòng sản phẩm", lines)
if line != "Tất cả":
    df = df[df["Dòng sản phẩm"] == line]

products = ["Tất cả"] + sorted(df["Tên sản phẩm"].dropna().unique())
product = st.sidebar.selectbox("Sản phẩm", products)
if product != "Tất cả":
    df = df[df["Tên sản phẩm"] == product]

stars = st.sidebar.multiselect("Số sao", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])
df = df[df["Số sao"].isin(stars)]

if df["Ngày review"].notna().any():
    dmin, dmax = df["Ngày review"].min().date(), df["Ngày review"].max().date()
    rng = st.sidebar.date_input("Ngày review", (dmin, dmax), min_value=dmin, max_value=dmax)
    if isinstance(rng, (tuple, list)) and len(rng) == 2:
        df = df[(df["Ngày review"].dt.date >= rng[0]) & (df["Ngày review"].dt.date <= rng[1])]

keyword = st.sidebar.text_input("Tìm trong nội dung review")
if keyword.strip():
    df = df[df["Nội dung review"].str.contains(keyword.strip(), case=False, na=False, regex=False)]

st.sidebar.caption(f"{len(df):,} / {len(base):,} review sau khi lọc".replace(",", "."))

# PALETTE MÀU THEO NỀN TẢNG HASAKI / SHOPEE
COLOR_HASAKI = {"primary": "#2D6844", "pie": ["#2D6844", "#4E9F6E", "#86C89B", "#C2EABD", "#E8A838"]}
COLOR_SHOPEE = {"primary": "#EE4D2D", "pie": ["#EE4D2D", "#FF7337", "#FFA066", "#FFCFA8", "#26A69A"]}

if source == "Hasaki":
    active_primary = COLOR_HASAKI["primary"]
    active_pie = COLOR_HASAKI["pie"]
elif source == "Shopee":
    active_primary = COLOR_SHOPEE["primary"]
    active_pie = COLOR_SHOPEE["pie"]
else:
    active_primary = "#1A4D2E"
    active_pie = ["#2D6844", "#EE4D2D", "#4E9F6E", "#FF7337", "#86C89B"]

h1, h2 = st.columns([1, 12], vertical_alignment="center")
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
    k3.metric("Sao trung bình", f"{df['Số sao'].mean():.2f}")
    k4.metric("Tỉ lệ tích cực (4–5★)", f"{(df['Số sao'] >= 4).mean():.1%}")
    k5.metric("Tỉ lệ tiêu cực (1–2★)", f"{(df['Số sao'] <= 2).mean():.1%}")

    st.subheader("Biểu đồ")
    g1, g2 = st.columns(2)

    with g1:
        rev = prod.dropna(subset=["Doanh thu 30 ngày"])
        rev = rev[rev["Doanh thu 30 ngày"] > 0]
        pie = (rev.groupby("Dòng sản phẩm")["Doanh thu 30 ngày"].sum().reset_index())
        if len(pie):
            fig = px.pie(pie, names="Dòng sản phẩm", values="Doanh thu 30 ngày", hole=0.35,
                         title="Cơ cấu doanh thu 30 ngày theo dòng sản phẩm",
                         color_discrete_sequence=active_pie)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu doanh thu để vẽ biểu đồ tròn.")

    with g2:
        mt = du.monthly_table(df)
        if source == "Tất cả":
            fig = px.line(mt, x="Tháng", y="Số review", color="Nguồn", markers=True,
                          title="Xu hướng số lượng review theo tháng",
                          color_discrete_map={"Hasaki": COLOR_HASAKI["primary"], "Shopee": COLOR_SHOPEE["primary"]})
        else:
            fig = px.line(mt, x="Tháng", y="Số review", markers=True,
                          title="Xu hướng số lượng review theo tháng",
                          color_discrete_sequence=[active_primary])
        st.plotly_chart(fig, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        dist = df.groupby(["Số sao", "Nguồn"]).size().reset_index(name="Số review")
        if source == "Tất cả":
            fig = px.bar(dist, x="Số sao", y="Số review", color="Nguồn", barmode="group",
                         title="Phân bố số sao",
                         color_discrete_map={"Hasaki": COLOR_HASAKI["primary"], "Shopee": COLOR_SHOPEE["primary"]})
        else:
            fig = px.bar(dist, x="Số sao", y="Số review",
                         title="Phân bố số sao",
                         color_discrete_sequence=[active_primary])
        st.plotly_chart(fig, use_container_width=True)

    with g4:
        top = prod.nlargest(10, "Số review")
        fig = px.bar(top, x="Số review", y="Tên sản phẩm", orientation="h",
                     title="Top 10 sản phẩm theo số review",
                     color_discrete_sequence=[active_primary])
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.subheader("Bảng sản phẩm")
    st.dataframe(prod, use_container_width=True, hide_index=True)
    st.subheader("Bảng review")
    show = ["Nguồn", "Mã SP", "Tên sản phẩm", "Hạng mục", "Số sao", "Cảm xúc",
            "Nội dung review", "Ngày review", "Đã mua hàng"]
    st.dataframe(df[show].sort_values("Ngày review", ascending=False).head(2000),
                 use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Dashboard Power BI")
    url = os.environ.get("POWERBI_EMBED_URL", "")
    try:
        url = st.secrets.get("POWERBI_EMBED_URL", url)
    except Exception:
        pass
    if admin:
        url = st.text_input("Link nhúng Power BI", value=url)
    if url and url.startswith("https://"):
        components.iframe(url, height=720, scrolling=True)

with tabs[3]:
    st.subheader("Kết quả mô hình (Giai đoạn 4)")
    expected = {
        "kmeans_clusters.csv": "K-Means: phân cụm khách hàng / review",
        "sentiment_predictions.csv": "Dự đoán cảm xúc",
        "apriori_rules.csv": "Luật kết hợp Apriori",
    }
    for fname, title in expected.items():
        p = du.MODEL_DIR / fname
        if p.exists():
            with st.expander(f"{title} — {fname}", expanded=True):
                st.dataframe(pd.read_csv(p), use_container_width=True, hide_index=True)

if admin:
    with tabs[4]:
        st.subheader("Quản trị dữ liệu")
        cols = ["rid", "Nguồn", "Tên sản phẩm", "Số sao", "Nội dung review"]
        sample = df[cols].head(300).copy()
        sample.insert(0, "Xóa", False)
        edited = st.data_editor(sample, hide_index=True, use_container_width=True, key="del_editor")
        picked = edited.loc[edited["Xóa"], "rid"].tolist()
        if st.button(f"🗑️ Xóa {len(picked)} review đã chọn", disabled=not picked):
            n = du.delete_rows(picked, user["username"])
            st.success(f"Đã xóa {n} review.")
            st.rerun()
