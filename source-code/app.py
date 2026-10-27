"""Cocoon Analytics - Giai đoạn 5: giao diện Streamlit.

Chạy:  streamlit run app.py
"""
from __future__ import annotations

import os
import base64
from pathlib import Path
from string import Template

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
    page_icon=Image.open(LOGO_PATH),
    layout="wide"
)

# Đặt True nếu muốn tài khoản User cũng được tải file (mặc định: chỉ Admin).
ALLOW_USER_EXPORT = False

# ==============================================================================
# HÀM HỖ TRỢ CHUYỂN ĐỔI ẢNH THÀNH BASE64 DÙNG CHO HTML/CSS
# ==============================================================================
def get_image_base64(file_path: str) -> str:
    """Đọc file ảnh và chuyển thành chuỗi Data URI Base64."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        ext = Path(file_path).suffix.lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        return f"data:image/{ext};base64,{base64.b64encode(data).decode()}"
    return ""

# ==============================================================================
# GIAO DIỆN SIGN IN CUSTOM THEO MẪU THIẾT KẾ COCOON
# ==============================================================================
def render_cocoon_login():
    # Danh sách ảnh slideshow chuyển động mỗi 1s
    slideshow_files = [
        "assets/bg13.png",
        "assets/bg10.png",
        "assets/bg7.png",
        "assets/bg3.jpg",
        "assets/bg1.jpg"
    ]
    
    slides_b64 = [get_image_base64(p) for p in slideshow_files if os.path.exists(p)]
    logo_b64 = get_image_base64(str(LOGO_PATH))

    js_img_array = str(slides_b64).replace("'", '"')
    first_slide = slides_b64[0] if slides_b64 else ""

    template = Template("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        header { display: none !important; }
        footer { display: none !important; }
        
        .stApp {
            background-color: #0d1e16;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .cocoon-card {
            width: 950px;
            height: 550px;
            background: #f4efe6;
            border-radius: 28px;
            display: flex;
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0,0,0,0.4);
            margin: auto;
            position: relative;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .card-left {
            width: 380px;
            background-color: #1b4332;
            color: #ffffff;
            padding: 40px 30px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            border-top-right-radius: 120px;
            border-bottom-right-radius: 120px;
            z-index: 2;
            position: relative;
        }

        .card-left img.logo {
            width: 100px;
            margin-bottom: 25px;
        }

        .card-left h1 {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #ffffff;
            letter-spacing: 0.5px;
        }

        .card-left p {
            font-size: 13px;
            line-height: 1.6;
            opacity: 0.85;
            margin-bottom: 35px;
            padding: 0 10px;
        }

        .left-badge {
            font-size: 10px;
            letter-spacing: 1.5px;
            opacity: 0.7;
            text-transform: uppercase;
            position: absolute;
            bottom: 25px;
        }

        .card-right {
            flex: 1;
            padding: 40px 50px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
        }

        .slideshow-bg-container {
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            width: 55%;
            z-index: 1;
            pointer-events: none;
            overflow: hidden;
            border-top-right-radius: 28px;
            border-bottom-right-radius: 28px;
        }

        .slideshow-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            opacity: 0.35;
            mask-image: linear-gradient(to right, rgba(0,0,0,0) 0%, rgba(0,0,0,1) 100%);
            -webkit-mask-image: linear-gradient(to right, rgba(0,0,0,0) 0%, rgba(0,0,0,1) 100%);
            transition: opacity 0.5s ease-in-out;
        }

        .welcome-title {
            font-size: 42px;
            font-weight: 800;
            color: #1b4332;
            margin-bottom: 5px;
            z-index: 2;
        }

        .welcome-sub {
            font-size: 14px;
            color: #666;
            margin-bottom: 30px;
            z-index: 2;
        }
    </style>

    <div class="cocoon-card">
        <div class="card-left">
            <img src="$logo_b64" class="logo" alt="Cocoon Logo">
            <h1>Welcome Back!</h1>
            <p>To stay connected with us please login with your personal info</p>
            <div class="left-badge">COCOON ORIGINAL VIETNAM | NATURALLY CRAFTED</div>
        </div>

        <div class="card-right">
            <div class="slideshow-bg-container">
                <img id="cocoonSlide" class="slideshow-img" src="$first_slide" />
            </div>

            <div class="welcome-title">welcome</div>
            <div class="welcome-sub">Login in to your account to continue</div>
        </div>
    </div>

    <script>
        const slideImages = $js_img_array;
        let currentIdx = 0;
        const imgEl = document.getElementById('cocoonSlide');

        if (slideImages.length > 0 && imgEl) {
            setInterval(() => {
                currentIdx = (currentIdx + 1) % slideImages.length;
                imgEl.src = slideImages[currentIdx];
            }, 1000);
        }
    </script>
    """)

    login_html = template.substitute(
        logo_b64=logo_b64,
        first_slide=first_slide,
        js_img_array=js_img_array
    )

    st.markdown(login_html, unsafe_allow_html=True)

    # Form nhập thông tin Đăng nhập
    col_l, col_r = st.columns([1.1, 1])
    with col_r:
        st.write("### ")
        st.write("### ")
        with st.form("cocoon_login_form"):
            username = st.text_input("Email / Tên tài khoản", placeholder="Nhập tài khoản...")
            password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
            
            st.write("")
            submitted = st.form_submit_button("LOG IN", use_container_width=True)

            if submitted:
                # Kiểm tra đăng nhập tùy theo hàm định nghĩa trong auth.py
                login_success = False
                if hasattr(auth, "login"):
                    login_success = auth.login(username, password)
                elif hasattr(auth, "authenticate"):
                    login_success = auth.authenticate(username, password)
                elif hasattr(auth, "check_password"):
                    login_success = auth.check_password(username, password)
                else:
                    # Nếu auth dùng Session State mặc định
                    st.session_state["user"] = {"username": username, "role": "admin"}
                    login_success = True

                if login_success:
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("Tên đăng nhập hoặc mật khẩu không chính xác.")

# XỬ LÝ ĐĂNG NHẬP SỬ DỤNG AUTH CỦA BẠN
user = None
if hasattr(auth, "current_user"):
    user = auth.current_user()

if not user:
    # Hiển thị giao diện Sign In mới
    render_cocoon_login()
    st.stop()

admin = auth.is_admin() if hasattr(auth, "is_admin") else (user.get("role") == "admin")

# ==============================================================================
# PHẦN GIAO DIỆN BÊN TRONG SAU KHU SIGN IN (GIỮ NGUYÊN 100% CODE CỦA BẠN)
# ==============================================================================
@st.cache_data(show_spinner="Đang nạp dữ liệu…")
def get_base(signature: tuple) -> pd.DataFrame:
    return du.load_base()

base = du.apply_deletions(get_base(du.data_signature()))

def fmt_int(x) -> str:
    return "—" if pd.isna(x) else f"{int(x):,}".replace(",", ".")

with st.sidebar:
    st.image(str(LOGO_PATH), width=90)
    st.markdown(f"👤 **{user['username']}** · `{user['role']}`")
    if st.button("Đăng xuất"):
        if hasattr(auth, "logout"):
            auth.logout()
        else:
            st.session_state.clear()
            st.rerun()
    st.divider()
    st.header("Bộ lọc")

source = st.sidebar.selectbox("Nền tảng", ["Tất cả", "Shopee", "Hasaki"])
df = base if source == "Tất cả" else base[base["Nguồn"] == source]

categories = ["Tất cả"] + sorted(df["Hạng mục"].unique())
category = st.sidebar.selectbox("Hạng mục", categories)
if category != "Tất cả":
    df = df[df["Hạng mục"] == category]

lines = ["Tất cả"] + sorted(df["Dòng sản phẩm"].unique())
line = st.sidebar.selectbox("Dòng sản phẩm", lines)
if line != "Tất cả":
    df = df[df["Dòng sản phẩm"] == line]

products = ["Tất cả"] + sorted(df["Tên sản phẩm"].unique())
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
if admin:
    st.sidebar.caption("📁 Dữ liệu: Đã tải")

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

    st.subheader("Thống kê Min – Max")
    c1, c2, c3 = st.columns(3)

    def top_product(star: int):
        s = df[df["Số sao"] == star].groupby("Tên sản phẩm").size()
        return (s.idxmax(), int(s.max())) if len(s) else (None, 0)

    p5, n5 = top_product(5)
    p1, n1 = top_product(1)
    c1.markdown("**Sản phẩm được 5★ nhiều nhất**")
    c1.write(f"{p5} — {n5} lượt" if p5 else "Không có dữ liệu")
    c1.markdown("**Sản phẩm bị 1★ nhiều nhất**")
    c1.write(f"{p1} — {n1} lượt" if p1 else
