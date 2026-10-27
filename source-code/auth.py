"""Đăng nhập phân quyền User / Admin - Giao diện Sign In Cocoon chuẩn thiết kế."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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
    """Đọc file ảnh và đổi sang định dạng Base64."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        ext = Path(file_path).suffix.lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        return f"data:image/{ext};base64,{base64.b64encode(data).decode()}"
    return ""


def login_gate() -> None:
    """Giao diện Đăng nhập Cocoon khớp 100% mẫu thiết kế."""
    if st.session_state.get("auth"):
        return

    # Đường dẫn ảnh bg1.jpg (hoặc bg1.png nếu file của bạn là .png)
    bg1_path = str(ASSETS / "bg1.jpg") if (ASSETS / "bg1.jpg").exists() else str(ASSETS / "bg1.png")
    bg1_b64 = get_image_base64(bg1_path)
    logo_b64 = get_image_base64(str(LOGO))

    # CSS Ẩn bớt giao diện thừa của Streamlit bên ngoài
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            header { display: none !important; }
            footer { display: none !important; }
            .stApp { background-color: #0d1e16 !important; }
            .block-container { max-width: 100% !important; padding: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    # HTML/CSS/JS tái tạo 100% giao diện trong ảnh mẫu
    html_card = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }}
        body {{
            background-color: #0d1e16;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
        }}
        
        .cocoon-card {{
            width: 860px;
            height: 480px;
            background: #f4efe6;
            border-radius: 28px;
            display: flex;
            position: relative;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.45);
            overflow: hidden;
        }}

        /* Cột bên trái xanh lá */
        .card-left {{
            width: 360px;
            background-color: #1b4332;
            color: #ffffff;
            padding: 40px 30px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            border-top-right-radius: 130px;
            border-bottom-right-radius: 130px;
            z-index: 3;
            position: relative;
        }}

        .card-left .logo {{
            width: 85px;
            margin-bottom: 20px;
        }}

        .card-left h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }}

        .card-left p {{
            font-size: 12.5px;
            line-height: 1.5;
            opacity: 0.85;
            margin-bottom: 30px;
            padding: 0 10px;
        }}

        .btn-signin-left {{
            border: 1.5px solid #ffffff;
            background: transparent;
            color: #ffffff;
            padding: 8px 40px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 1px;
            cursor: pointer;
            margin-bottom: 30px;
        }}

        .left-badge {{
            font-size: 9px;
            letter-spacing: 1.2px;
            opacity: 0.65;
            text-transform: uppercase;
        }}

        /* Cột bên phải chứa Form & Hình nền bg1 */
        .card-right {{
            flex: 1;
            padding: 45px 50px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
            z-index: 2;
        }}

        .bg-product {{
            position: absolute;
            right: -20px;
            bottom: -20px;
            width: 320px;
            height: 320px;
            background-image: url('{bg1_b64}');
            background-size: contain;
            background-repeat: no-repeat;
            background-position: bottom right;
            z-index: 1;
            pointer-events: none;
            opacity: 0.95;
        }}

        .welcome-title {{
            font-size: 38px;
            font-weight: 800;
            color: #1b4332;
            text-align: center;
            margin-bottom: 4px;
        }}

        .welcome-sub {{
            font-size: 13px;
            color: #666;
            text-align: center;
            margin-bottom: 35px;
        }}

        .form-group {{
            margin-bottom: 22px;
            position: relative;
            z-index: 2;
            width: 280px;
        }}

        .input-underline {{
            width: 100%;
            border: none;
            border-bottom: 1.5px solid #1b4332;
            background: transparent;
            padding: 6px 0 6px 55px;
            font-size: 14px;
            color: #333;
            outline: none;
        }}

        .input-label {{
            position: absolute;
            left: 0;
            top: 6px;
            font-size: 14px;
            color: #1b4332;
            font-weight: 500;
        }}

        .forgot-pass {{
            font-size: 12px;
            color: #333;
            text-align: right;
            margin-top: 5px;
            cursor: pointer;
            width: 280px;
            z-index: 2;
        }}

        .btn-login {{
            width: 130px;
            height: 38px;
            background-color: #1b4332;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
            margin: 20px 0 15px 75px;
            z-index: 2;
            letter-spacing: 0.5px;
        }}

        .signup-text {{
            font-size: 12px;
            color: #444;
            z-index: 2;
            width: 280px;
            text-align: center;
        }}

        .signup-text a {{
            color: #1b4332;
            font-weight: bold;
            text-decoration: none;
        }}

        .error-msg {{
            color: #d90429;
            font-size: 12px;
            margin-top: 8px;
            width: 280px;
            text-align: center;
        }}
    </style>
    </head>
    <body>
        <div class="cocoon-card">
            <div class="card-left">
                <img src="{logo_b64}" class="logo" alt="Cocoon Logo">
                <h1>Welcome Back!</h1>
                <p>To stay connected with us please login with your personal info</p>
                <button class="btn-signin-left">SIGN IN</button>
                <div class="left-badge">COCOON ORIGINAL VIETNAM | NATURALLY CRAFTED</div>
            </div>

            <div class="card-right">
                <div class="bg-product"></div>

                <div class="welcome-title">welcome</div>
                <div class="welcome-sub">Login in to your account to continue</div>

                <form id="loginForm">
                    <div class="form-group">
                        <span class="input-label">Email</span>
                        <input type="text" id="userInput" class="input-underline" required>
                    </div>

                    <div class="form-group">
                        <span class="input-label">Password</span>
                        <input type="password" id="passInput" class="input-underline" required>
                    </div>

                    <div class="forgot-pass">Forgot your password?</div>

                    <button type="submit" class="btn-login">LOG IN</button>

                    <div class="signup-text">
                        Don't have an account? <a href="#">sign up</a>
                    </div>
                    <div id="errMsg" class="error-msg"></div>
                </form>
            </div>
        </div>

        <script>
            document.getElementById('loginForm').addEventListener('submit', function(e) {{
                e.preventDefault();
                const u = document.getElementById('userInput').value;
                const p = document.getElementById('passInput').value;
                
                // Gửi dữ liệu về Streamlit
                window.parent.postMessage({{
                    type: 'COCOON_LOGIN',
                    username: u,
                    password: p
                }}, '*');
            }});
        </script>
    </body>
    </html>
    """

    components.html(html_card, height=650)

    # Nhận sự kiện đăng nhập từ iframe HTML
    st.components.v1.html(
        """
        <script>
            window.addEventListener('message', function(event) {
                if (event.data.type === 'COCOON_LOGIN') {
                    const url = new URL(window.location.href);
                    url.searchParams.set('u', event.data.username);
                    url.searchParams.set('p', event.data.password);
                    window.location.href = url.href;
                }
            });
        </script>
        """,
        height=0
    )

    # Xử lý xác thực thông tin tài khoản
    params = st.query_params
    if "u" in params and "p" in params:
        u_val = params["u"]
        p_val = params["p"]
        st.query_params.clear()

        rec = _users().get(u_val.strip())
        ok = rec is not None and hmac.compare_digest(_h(p_val), str(rec.get("password_sha256", "")))
        if ok:
            st.session_state["auth"] = {"username": u_val.strip(), "role": rec.get("role", "User")}
            st.rerun()
        else:
            st.error("Sai tên đăng nhập hoặc mật khẩu.")

    st.stop()


def current_user() -> dict:
    return st.session_state.get("auth", {"username": "Guest", "role": "User"})


def is_admin() -> bool:
    return current_user().get("role") == "Admin"


def logout() -> None:
    st.session_state.pop("auth", None)
    st.rerun()
