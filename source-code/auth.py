"""Đăng nhập đơn giản, phân quyền User / Admin + giao diện trang Sign in Cocoon."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from pathlib import Path
from string import Template

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
    """Hiện giao diện Đăng nhập Cocoon mới; dừng app nếu chưa đăng nhập."""
    if st.session_state.get("auth"):
        return

    slideshow_files = [
        str(ASSETS / "bg13.png"),
        str(ASSETS / "bg10.png"),
        str(ASSETS / "bg7.png"),
        str(ASSETS / "bg3.jpg"),
        str(ASSETS / "bg1.jpg")
    ]
    
    slides_b64 = [get_image_base64(p) for p in slideshow_files if os.path.exists(p)]
    logo_b64 = get_image_base64(str(LOGO))

    js_img_array = str(slides_b64).replace("'", '"')
    first_slide = slides_b64[0] if slides_b64 else ""

    template = Template("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        header { display: none !important; }
        footer { display: none !important; }
        
        .stApp {
            background-color: #0d1e16 !important;
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

    st.markdown(template.substitute(logo_b64=logo_b64, first_slide=first_slide, js_img_array=js_img_array), unsafe_allow_html=True)

    col_l, col_r = st.columns([1.1, 1])
    with col_r:
        st.write("### ")
        st.write("### ")
        with st.form("cocoon_login_form"):
            username = st.text_input("Username", placeholder="Username")
            password = st.text_input("Password", type="password", placeholder="Password")
            st.write("")
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
