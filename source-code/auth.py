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
    if Path(path).exists():
        return base64.b64encode(Path(path).read_bytes()).decode()
    return ""


def check_login_credentials(username: str, password: str) -> bool:
    """Kiểm tra tài khoản và mật khẩu."""
    rec = _users().get(username.strip())
    if rec is not None and hmac.compare_digest(_h(password), str(rec.get("password_sha256", ""))):
        st.session_state["auth"] = {
            "username": username.strip(),
            "role": rec.get("role", "User")
        }
        return True
    return False


def login_gate() -> None:
    """Được giữ lại để tương thích ngược."""
    if st.session_state.get("auth"):
        return


def current_user() -> dict:
    return st.session_state.get("auth", {"username": "Guest", "role": "User"})


def is_admin() -> bool:
    user = current_user()
    return user.get("role") == "Admin"


def logout() -> None:
    st.session_state.pop("auth", None)
    st.rerun()
