"""Đăng nhập phân quyền User / Admin - Giao diện Sign In Cocoon chuẩn thiết kế."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from pathlib import Path

import streamlit as st

MAX_ATTEMPTS = 5

# TỰ ĐỘNG TÌM ĐÚNG THƯ MỤC ASSETS
CURRENT_DIR = Path(__file__).resolve().parent
if (CURRENT_DIR / "assets").exists():
    ASSETS = CURRENT_DIR / "assets"
elif (CURRENT_DIR.parent / "assets").exists():
    ASSETS = CURRENT_DIR.parent / "assets"
else:
    ASSETS = CURRENT_DIR / "assets"

# ĐỔI ƯU TIÊN: Dùng logo1.png trước, nếu không thấy mới dùng logo.png
LOGO = ASSETS / "logo1.png" if (ASSETS / "logo1.png").exists() else ASSETS / "logo.png"


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


def get_image_base64(file_path: Path | str) -> str:
    """Đọc file ảnh và chuyển sang chuỗi Base64."""
    p = Path(file_path)
    if p.exists():
        data = p.read_bytes()
        ext = p.suffix.lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        return f"data:image/{ext};base64,{base64.b64encode(data).decode()}"
    return ""


def login_gate() -> None:
    """Hiện giao diện Đăng nhập Cocoon; dừng app nếu chưa đăng nhập."""
    if st.session_state.get("auth"):
        return

    # Lấy base64 của ảnh logo1.png và ảnh bg1.jpg
    bg1_file = ASSETS / "bg1.jpg"
    if not bg1_file.exists():
        bg1_file = ASSETS / "bg1.png"

    bg1_b64 = get_image_base64(bg1_file)
    logo_b64 = get_image_base64(LOGO)

    # CSS Nền mảng màu trắng kem (#F8F5EE) & Ảnh hiển thị góc dưới
    custom_css = f"""
    <style>
        [data-testid="stSidebar"] {{ display: none !important; }}
        header {{ display: none !important; }}
        footer {{ display: none !important; }}
        
        .stApp {{
            background-color: #0d1e16 !important;
        }}

        /* Khung chứa trung tâm */
        .block-container {{
            max-width: 920px !important;
            padding-top: 10vh !important;
            padding-bottom: 0px !important;
        }}

        /* Bo góc khung đăng nhập chính */
        div[data-testid="stHorizontalBlock"] {{
            background: #F8F5EE !important;
            border-radius: 28px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.45);
            overflow: hidden;
            position: relative;
            min-height: 480px;
        }}

        /* Cột trái - Xanh lá Cocoon */
        div[data-testid="stColumn"]:nth-child(1) {{
            background-color: #1b4332;
            color: #ffffff;
            padding: 40px 30px !important;
            text-align: center;
            border-top-right-radius: 130px;
            border-bottom-right-radius: 130px;
            z-index: 3;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}

        .left-logo {{
            width: 85px;
            margin-bottom: 15px;
        }}

        .left-title {{
            color: #ffffff !important;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .left-desc {{
            color: rgba(255, 255, 255, 0.85);
            font-size: 12.5px;
            line-height: 1.5;
            margin-bottom: 30px;
        }}

        .left-badge {{
            color: rgba(255, 255, 255, 0.6);
            font-size: 9px;
            letter-spacing: 1.2px;
            text-transform: uppercase;
        }}

        /* Cột phải - Nền màu trắng kem + Ảnh sản phẩm hiển thị góc dưới */
        div[data-testid="stColumn"]:nth-child(2) {{
            background-color: #F8F5EE !important;
            padding: 40px 45px !important;
            position: relative;
            background-image: url('{bg1_b64}') !important;
            background-repeat: no-repeat !important;
            background-position: bottom right !important;
            background-size: 320px auto !important;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .welcome-title {{
            color: #1b4332;
            font-size: 38px;
            font-weight: 800;
            margin-bottom: 2px;
        }}

        .welcome-sub {{
            color: #666666;
            font-size: 13px;
            margin-bottom: 25px;
            font-weight: 500;
        }}

        /* Styling Form Streamlit */
        div[data-testid="stForm"] {{
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
            position: relative;
            z-index: 2;
            max-width: 320px;
        }}

        /* Tùy chỉnh Nút Đăng nhập */
        .stButton > button {{
            background-color: #1b4332 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            height: 42px !important;
            font-weight: bold !important;
            border: none !important;
            margin-top: 10px;
        }}

        .stButton > button:hover {{
            background-color: #2d6a4f !important;
            color: #ffffff !important;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    # Dựng cấu trúc 2 cột
    col_left, col_right = st.columns([4, 5])

    with col_left:
        if logo_b64:
            st.markdown(f'<img src="{logo_b64}" class="left-logo">', unsafe_allow_html=True)
        st.markdown('<div class="left-title">Welcome Back!</div>', unsafe_allow_html=True)
        st.markdown('<div class="left-desc">To stay connected with us please login with your personal info</div>', unsafe_allow_html=True)
        st.markdown('<div class="left-badge">COCOON ORIGINAL VIETNAM | NATURALLY CRAFTED</div>', unsafe_allow_html=True)

    with col_right:
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
