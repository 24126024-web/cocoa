import streamlit as st
import time

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Đăng Nhập - Shopee & Hasaki",
    page_icon="🔒",
    layout="wide"
)

# 1. Khai báo trạng thái Theme mặc định trong Session State
if "theme" not in st.session_state:
    st.session_state["theme"] = "shopee"

# Hàm chuyển đổi theme
def set_theme(theme_name):
    st.session_state["theme"] = theme_name

# 2. Định nghĩa màu sắc theo từng Theme
if st.session_state["theme"] == "shopee":
    primary_color = "#ee4d2d"
    hover_color = "#d73211"
    brand_name = "Shopee (Cam)"
else:
    primary_color = "#327856"
    hover_color = "#24583e"
    brand_name = "Hasaki (Xanh)"

# 3. Cấu hình danh sách ảnh trong thư mục assets/
# Đảm bảo bạn đã có thư mục assets/ nằm cùng cấp với file app.py
bg_image_path = "assets/bg1.jpg"       # Đường dẫn ảnh nền chính
floating_img_path = "assets/bg1.jpg"   # Đường dẫn ảnh đã cắt phông nền

# 4. Inject CSS tùy chỉnh & Hiệu ứng chuyển động (Animation + Dynamic Theme)
custom_css = f"""
<style>
    /* Ẩn bớt thanh header/footer mặc định của Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Background tổng thể */
    .stApp {{
        background: url('{bg_image_path}') no-repeat center center fixed;
        background-size: cover;
        transition: all 0.5s ease;
    }}

    /* Hiệu ứng ảnh trôi nổi đằng sau (Floating Asset) */
    @keyframes floatAnim {{
        0% {{ transform: translateY(0px) rotate(0deg) scale(1); }}
        50% {{ transform: translateY(-25px) rotate(8deg) scale(1.05); }}
        100% {{ transform: translateY(15px) rotate(-8deg) scale(0.95); }}
    }}

    .floating-asset {{
        position: fixed;
        width: 100px;
        opacity: 0.85;
        z-index: 1;
        pointer-events: none;
        animation: floatAnim 6s infinite ease-in-out alternate;
    }}

    /* Vị trí các ảnh trôi nổi */
    .asset-1 {{ top: 15%; left: 10%; animation-delay: 0s; }}
    .asset-2 {{ top: 60%; left: 15%; animation-delay: 1.5s; }}
    .asset-3 {{ top: 20%; right: 12%; animation-delay: 0.8s; }}
    .asset-4 {{ top: 65%; right: 10%; animation-delay: 2.2s; }}

    /* Styling cho Khung Đăng Nhập */
    div[data-testid="stColumn"] > div {{
        background: rgba(255, 255, 255, 0.92);
        padding: 35px 30px;
        border-radius: 16px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(10px);
    }}

    /* Tùy chỉnh màu sắc Button & Input theo Theme */
    .stButton > button {{
        background-color: {primary_color} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }}

    .stButton > button:hover {{
        background-color: {hover_color} !important;
        transform: translateY(-2px);
    }}

    /* Style tiêu đề */
    .login-title {{
        text-align: center;
        color: #333333;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 5px;
    }}

    .theme-info {{
        text-align: center;
        font-size: 14px;
        color: {primary_color};
        font-weight: bold;
        margin-bottom: 20px;
    }}
</style>

<!-- Chèn các hình ảnh trôi nổi trên màn hình -->
<img src="{floating_img_path}" class="floating-asset asset-1">
<img src="{floating_img_path}" class="floating-asset asset-2">
<img src="{floating_img_path}" class="floating-asset asset-3">
<img src="{floating_img_path}" class="floating-asset asset-4">
"""

st.markdown(custom_css, unsafe_allow_html=True)

# 5. Dựng Giao Diện Form Đăng Nhập Cân Bằng Giữa Màn Hình
col1, col2, col3 = st.columns([1, 1.2, 1])

with col2:
    st.markdown('<div class="login-title">ĐĂNG NHẬP</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="theme-info">Đang chọn Theme: {brand_name}</div>', unsafe_allow_html=True)

    # Nút bấm chuyển Theme (Shopee / Hasaki)
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Tông Shopee 🟠", use_container_width=True):
            set_theme("shopee")
            st.rerun()
    with btn_col2:
        if st.button("Tông Hasaki 🟢", use_container_width=True):
            set_theme("hasaki")
            st.rerun()

    st.write("---")

    # Form nhập thông tin
    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập / Email / SĐT", placeholder="Nhập tài khoản...")
        password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
        
        submit_button = st.form_submit_button("ĐĂNG NHẬP", use_container_width=True)

        if submit_button:
            if username and password:
                st.success(f"Đăng nhập thành công tài khoản: **{username}**!")
            else:
                st.error("Vui lòng điền đầy đủ Tên đăng nhập và Mật khẩu!")
