"""Quản lý xác thực và phân quyền người dùng (Cocoon Analytics)."""
from __future__ import annotations

from pathlib import Path
import streamlit as st

# Đường dẫn Logo thương hiệu
HERE = Path(__file__).resolve().parent
LOGO = HERE / "logo.png"

# Danh sách tài khoản mẫu (Có thể tùy chỉnh lại username/password)
USERS = {
    "admin": {"password": "123", "role": "admin", "name": "Administrator"},
    "user": {"password": "123", "role": "user", "name": "Nhân viên"},
}


def login_gate() -> None:
    """Hiển thị trang Đăng nhập (Sign-in Gate) nếu chưa đăng nhập."""
    if "user" not in st.session_state:
        st.session_state["user"] = None

    if st.session_state["user"] is not None:
        return

    # Giao diện Trang Đăng Nhập
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.write("")
        st.write("")
        if LOGO.exists():
            st.image(str(LOGO), width=120)
        st.title("Đăng nhập")
        st.caption("Hệ thống Phân tích & Quản trị Dữ liệu Cocoon Analytics")

        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")

        if st.button("Đăng nhập", use_container_width=True):
            user_info = USERS.get(username.strip())
            if user_info and user_info["password"] == password:
                st.session_state["user"] = {
                    "username": username.strip(),
                    "role": user_info["role"],
                    "name": user_info["name"],
                }
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Tên đăng nhập hoặc mật khẩu không đúng!")

        st.stop()


def current_user() -> dict:
    """Lấy thông tin tài khoản đang đăng nhập."""
    return st.session_state.get("user") or {"username": "guest", "role": "user", "name": "Khách"}


def is_admin() -> bool:
    """Kiểm tra xem tài khoản hiện tại có phải Admin không."""
    user = current_user()
    return user.get("role") == "admin"


def logout() -> None:
    """Đăng xuất khỏi hệ thống."""
    st.session_state["user"] = None
    st.rerun()
