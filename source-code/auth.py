"""Đăng nhập đơn giản, phân quyền User / Admin + giao diện trang Sign in Cocoon."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from pathlib import Path

import streamlit as st

MAX_ATTEMPTS = 5
ASSETS = Path(__file__).resolve().parent / "assets"
LOGO = ASSETS / "logo.png"


def _h(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


DEFAULT_USERS = {
    "admin": {"password_sha256": _h("admin123"), "role": "Admin"},
    "user": {"password_sha256": _h("user123"), "role": "User"},
}


def _users() -> dict:
    try:
        if "users" in st.secrets:
            return {k: dict(v) for k, v in st.secrets["users"].items()}
    except Exception:
        pass
    return DEFAULT_USERS


def using_default_accounts() -> bool:
    return _users() is DEFAULT_USERS


def get_image_base64(file_path: str) -> str:
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        ext = Path(file_path).suffix.lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        return f"data:image/{ext};base64,{base64.b64encode(data).decode()}"
    return ""


def login_gate() -> None:
    """Hiện giao diện Đăng nhập Cocoon; dừng app nếu chưa đăng nhập."""
    if st.session_state.get("auth"):
        return

    # 1. Lấy danh sách ảnh slideshow (bg13, bg10, bg7, bg3, bg1)
    slideshow_files = [
        str(ASSETS / "bg13.png"),
        str(ASSETS / "bg10.png"),
        str(ASSETS / "bg7.png"),
        str(ASSETS / "bg3.jpg"),
        str(ASSETS / "bg1.jpg")
    ]
    slides_b64 = [get_image_base64(p) for p in slideshow_files if os.path.exists(p)]
    logo_b64 = get_image_base64(str(LOGO))
    first_slide = slides_b64[0] if slides_b64 else ""
    js_img_array = str(slides_b64).replace("'", '"')

    # 2. Inject CSS định hình giao diện theo đúng mẫu thiết kế
    custom_css = f"""
    <style>
        [data-testid="stSidebar"] {{ display: none !important; }}
        header {{ display: none !important; }}
        footer {{ display: none !important; }}
        
        .stApp {{
            background-color: #0d1e16 !important;
        }}

        /* Khung chứa giao diện trung tâm */
        .block-container {{
            max-width: 960px !important;
            padding-top: 8vh !important;
            padding-bottom: 0px !important;
        }}

        /* Bo góc khung đăng nhập chính */
        div[data-testid="stHorizontalBlock"] {{
            background: #f4efe6;
            border-radius: 28px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.4);
            overflow: hidden;
            position: relative;
        }}

        /* Cột trái (Xanh lá Cocoon) */
        div[data-testid="stColumn"]:nth-child(1) {{
            background-color: #1b4332;
            color: #ffffff;
            padding: 40px 30px !important;
            text-align: center;
            border-top-right-radius: 110px;
            border-bottom-right-radius: 110px;
            z-index: 2;
        }}

        .left-logo {{
            width: 100px;
            margin-bottom: 20px;
        }}

        .left-title {{
            color: #ffffff !important;
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .left-desc {{
            color: rgba(255, 255, 255, 0.85);
            font-size: 13px;
            line-height: 1.5;
            margin-bottom: 40px;
        }}

        .left-badge {{
            color: rgba(255, 255, 255, 0.6);
            font-size: 10px;
            letter-spacing: 1.2px;
            text-transform: uppercase;
        }}

        /* Cột phải (Form Đăng Nhập & Slideshow) */
        div[data-testid="stColumn"]:nth-child(2) {{
            padding: 40px 45px !important;
            position: relative;
            background: transparent;
        }}

        .welcome-title {{
            color: #1b4332;
            font-size: 40px;
            font-weight: 800;
            margin-bottom: 2px;
        }}

        .welcome-sub {{
            color: #666666;
            font-size: 14px;
            margin-bottom: 25px;
        }}

        /* Khung ảnh đổi background liên tục 1s */
        .slide-bg-wrap {{
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            width: 50%;
            z-index: 0;
            pointer-events: none;
            overflow: hidden;
        }}

        .slide-bg-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            opacity: 0.3;
            mask-image: linear-gradient(to right, rgba(0,0,0,0) 0%, rgba(0,0,0,1) 100%);
            -webkit-mask-image: linear-gradient(to right, rgba(0,0,0,0) 0%, rgba(0,0,0,1) 100%);
        }}

        /* Styling cho Form Input & Nút bấm */
        div[data-testid="stForm"] {{
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
            position: relative;
            z-index: 2;
        }}

        .stButton > button {{
            background-color: #1b4332 !important;
            color: #ffffff !important;
            border-radius: 20px !important;
            height: 45px !important;
            font-weight: bold !important;
            border: none !important;
            margin-top: 15px;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    # 3. Dựng cấu trúc giao diện 2 cột chuẩn Streamlit
    col_left, col_right = st.columns([4, 5])

    with col_left:
        st.markdown(f'<img src="{logo_b64}" class="left-logo">', unsafe_allow_html=True)
        st.markdown('<div class="left-title">Welcome Back!</div>', unsafe_allow_html=True)
        st.markdown('<div class="left-desc">To stay connected with us please login with your personal info</div>', unsafe_allow_html=True)
        st.markdown('<div class="left-badge">COCOON ORIGINAL VIETNAM | NATURALLY CRAFTED</div>', unsafe_allow_html=True)

    with col_right:
        # Chèn Background Slideshow đổi ảnh mỗi 1s
        st.markdown(
            f'''
            <div class="slide-bg-wrap">
                <img id="cocoonSlide" class="slide-bg-img" src="{first_slide}">
            </div>
            <script>
                const slideImages = {js_img_array};
                let currentIdx = 0;
                const imgEl = document.getElementById('cocoonSlide');
                if (slideImages.length > 0 && imgEl) {{
                    setInterval(() => {{
                        currentIdx = (currentIdx + 1) % slideImages.length;
                        imgEl.src = slideImages[currentIdx];
                    }}, 1000);
                }}
            </script>
            ''',
            unsafe_allow_html=True
        )

        st.markdown('<div class="welcome-title">welcome</div>', unsafe_allow_html=True)
        st.markdown('<div class="welcome-sub">Login in to your account to continue</div>', unsafe_allow_html=True)

        with st.form("cocoon_login_form"):
            username = st.text_input("Username", placeholder="Email / Username", label_visibility="collapsed")
            password = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            
            submitted = st.form_submit_button("LOG IN", use_container_width=True)

            if submitted:
                rec = _users().get(username.strip())
                ok = rec is not None and hmac.compare_digest(_h(password), str(rec.get("password_sha256", "")))
                if ok:
                    st.session_state["auth"] = {"username": username.strip(), "role": rec.get("role", "User")}
                    st.rerun()
                else:
                    st.error("Sai tên đăng nhập hoặc mật khẩu.")

        if using_default_accounts():
            st.caption("Demo — Admin: `admin / admin123` · User: `user / user123`")

    st.stop()


def current_user() -> dict:
    return st.session_state.get("auth", {"username": "Guest", "role": "User"})


def is_admin() -> bool:
    return current_user().get("role") == "Admin"


def logout() -> None:
    st.session_state.pop("auth", None)
    st.rerun()
