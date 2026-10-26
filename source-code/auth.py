"""Đăng nhập đơn giản, phân quyền User / Admin + giao diện trang Sign in."""
from __future__ import annotations

import base64
import hashlib
import hmac
from pathlib import Path

import streamlit as st

MAX_ATTEMPTS = 5
ASSETS = Path(__file__).resolve().parent / "assets"
LOGO = ASSETS / "logo.png"
GREEN = "#1f9d57"
GREEN_DARK = "#14804a"


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
    except Exception:  # chưa có secrets.toml
        pass
    return DEFAULT_USERS


def using_default_accounts() -> bool:
    return _users() is DEFAULT_USERS


@st.cache_resource(show_spinner=False)
def _b64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()



_ICON_USER = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
              "fill='none' stroke='%23777' stroke-width='1.8' stroke-linecap='round'>"
              "<circle cx='12' cy='8' r='4'/><path d='M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7'/></svg>")
_ICON_KEY = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
             "fill='none' stroke='%23777' stroke-width='1.8' stroke-linecap='round'>"
             "<circle cx='8' cy='15' r='4'/><path d='M11 12l9-9M16 7l3 3'/></svg>")

_CSS = """
<style>
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"], footer { visibility: hidden; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: transparent !important; }
.cc-bg { position: fixed; inset: 0; z-index: 0; pointer-events: none; background-size: cover;
         background-position: center; opacity: 0; animation: ccfade 24s infinite; }
.cc-b1 { background-image: url(data:image/jpeg;base64,__B1__); }
.cc-b2 { background-image: url(data:image/jpeg;base64,__B2__); animation-delay: 8s; }
.cc-b3 { background-image: url(data:image/jpeg;base64,__B3__); animation-delay: 16s; }
.cc-shade { position: fixed; inset: 0; z-index: 0; pointer-events: none;
            background: linear-gradient(135deg, rgba(10,60,35,.40), rgba(10,40,25,.25)); }
@keyframes ccfade { 0% {opacity:0} 5% {opacity:1} 33% {opacity:1} 38% {opacity:0} 100% {opacity:0} }

.block-container { position: relative; z-index: 1; max-width: 560px !important; padding-top: 6vh !important; }
[data-testid="stForm"] { background: #fff; border: none; border-radius: 32px;
                         padding: 34px 44px 30px; box-shadow: 0 24px 60px rgba(0,0,0,.35); }
.cc-logo { display: block; margin: 0 auto 4px; width: 92px; }
.cc-title { color: __G__; font-size: 46px; font-weight: 800; line-height: 1.1; margin: 4px 0 6px; }
.cc-sub, .cc-forgot { font-size: 15px; color: #8a8f94; }
.cc-sub summary, .cc-forgot summary { cursor: pointer; list-style: none; }
.cc-sub summary b, .cc-forgot summary { color: __G__; font-weight: 600; }
.cc-forgot { text-align: right; padding-top: 6px; }
.cc-sub div, .cc-forgot div { margin-top: 6px; color: #555; font-size: 14px; }

[data-testid="stForm"] [data-baseweb="input"], [data-testid="stForm"] [data-baseweb="base-input"] {
    background: #eef0f1 !important; border: none !important; border-radius: 999px !important; }
[data-testid="stForm"] [data-baseweb="input"]:focus-within { box-shadow: 0 0 0 2px __G__; }
[data-testid="stForm"] input[type="text"], [data-testid="stForm"] input[type="password"] { height: 54px; padding-left: 58px !important; font-size: 17px;
    background-color: transparent !important; background-repeat: no-repeat;
    background-position: 20px center; background-size: 24px; }
[data-testid="stForm"] input[placeholder="Username"] { background-image: url("__USER__"); }
[data-testid="stForm"] input[placeholder="Password"] { background-image: url("__KEY__"); }
[data-testid="stForm"] label p { color: #8a8f94; font-size: 15px; }

[data-testid="stFormSubmitButton"] button { width: 100%; height: 58px; border: none; border-radius: 999px;
    color: #fff; font-size: 22px; font-weight: 600;
    background: linear-gradient(90deg, __G__, __GD__); box-shadow: 0 8px 18px rgba(31,157,87,.35); }
[data-testid="stFormSubmitButton"] button:hover { filter: brightness(1.07); color: #fff; }
[data-testid="stFormSubmitButton"] button p { font-size: 22px; }
.cc-hint { margin-top: 16px; padding: 12px 18px; border-radius: 16px; background: rgba(255,255,255,.9);
           color: #333; font-size: 14px; text-align: center; }
</style>
"""


def _inject_login_css() -> None:
    css = (_CSS.replace("__B1__", _b64(str(ASSETS / "bg1.jpg")))
               .replace("__B2__", _b64(str(ASSETS / "bg2.jpg")))
               .replace("__B3__", _b64(str(ASSETS / "bg3.jpg")))
               .replace("__G__", GREEN).replace("__GD__", GREEN_DARK)
               .replace("__USER__", _ICON_USER).replace("__KEY__", _ICON_KEY))
    st.markdown(css, unsafe_allow_html=True)
    st.markdown('<div class="cc-bg cc-b1"></div><div class="cc-bg cc-b2"></div>'
                '<div class="cc-bg cc-b3"></div><div class="cc-shade"></div>',
                unsafe_allow_html=True)


def login_gate() -> None:
    """Hiện form đăng nhập; dừng app nếu chưa đăng nhập."""
    if st.session_state.get("auth"):
        return
    st.session_state.setdefault("attempts", 0)
    locked = st.session_state["attempts"] >= MAX_ATTEMPTS
    _inject_login_css()

    with st.form("login"):
        st.markdown(
            f'<img class="cc-logo" src="data:image/png;base64,{_b64(str(LOGO))}" alt="Cocoon">'
            '<div class="cc-title">Sign in</div>'
            '<details class="cc-sub"><summary>Not registered? <b>Click here to register.</b></summary>'
            '<div>Tài khoản do Admin cấp. Vui lòng liên hệ Admin của nhóm để được tạo tài khoản.</div></details>',
            unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Username",
                                 value=st.session_state.get("remembered_user", ""),
                                 label_visibility="collapsed")
        password = st.text_input("Password", placeholder="Password", type="password",
                                 label_visibility="collapsed")
        c1, c2 = st.columns(2)
        remember = c1.checkbox("Remember Me", value=True)
        c2.markdown('<details class="cc-forgot"><summary>Forgot Password?</summary>'
                    '<div>Liên hệ Admin để được cấp lại mật khẩu.</div></details>',
                    unsafe_allow_html=True)
        go = st.form_submit_button("Sign in", disabled=locked)

    if locked:
        st.error("Sai quá nhiều lần. Tải lại trang để thử lại.")
    elif go:
        rec = _users().get(username.strip())
        ok = rec is not None and hmac.compare_digest(
            _h(password), str(rec.get("password_sha256", "")))
        if ok:
            st.session_state["auth"] = {"username": username.strip(),
                                        "role": rec.get("role", "User")}
            st.session_state["attempts"] = 0
            if remember:
                st.session_state["remembered_user"] = username.strip()
            else:
                st.session_state.pop("remembered_user", None)
            st.rerun()
        else:
            st.session_state["attempts"] += 1
            st.error("Sai tên đăng nhập hoặc mật khẩu.")

    if using_default_accounts():
        st.markdown('<div class="cc-hint">Tài khoản demo — Admin: <code>admin / admin123</code> · '
                    'User: <code>user / user123</code></div>', unsafe_allow_html=True)
    st.stop()


def current_user() -> dict:
    return st.session_state["auth"]


def is_admin() -> bool:
    return current_user()["role"] == "Admin"


def logout() -> None:
    st.session_state.pop("auth", None)
    st.rerun()
