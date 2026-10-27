"""Cocoon Analytics - Giai đoạn 5: giao diện Streamlit.

Chạy:  streamlit run app.py
"""
from __future__ import annotations

import os
import base64
from pathlib import Path

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
# HÀM HỖ TRỢ CHUYỂN ĐỔI ẢNH THÀNH BASE64 DÙNG CHO HTML/CSS KHÔNG BỊ LỖI ĐƯỜNG DẪN
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
# GIAO DIỆN SIGN IN / LOGIN CUSTOM THEO MẪU THIẾT KẾ COCOON
# ==============================================================================
def render_cocoon_login():
    # Chuẩn bị danh sách ảnh slideshow (bg13, bg10, bg7, bg3, bg1)
    slideshow_files = [
        "assets/bg13.png",
        "assets/bg10.png",
        "assets/bg7.png",
        "assets/bg3.jpg",
        "assets/bg1.jpg"
    ]
    
    # Chuyển đổi các ảnh slideshow sang dạng base64
    slides_b64 = [get_image_base64(p) for p in slideshow_files if os.path.exists(p)]
    logo_b64 = get_image_base64(str(LOGO_PATH))

    # JavaScript mảng ảnh slideshow
    js_img_array = str(slides_b64).replace("'", '"')

    # CSS & HTML dựng giao diện Sign In theo ảnh mẫu
    login_html = f"""
    <style>
        /* Ẩn bớt giao diện mặc định của Streamlit khi chưa đăng nhập */
        [data-testid="stSidebar"] {{ display: none; }}
        header {{ display: none !important; }}
        footer {{ display: none !important; }}
        
        .stApp {{
            background-color: #0d1e16;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}

        /* Khung tổng Login Container */
        .cocoon-card {{
            width: 950px;
            height: 550px;
            background: #f4efe6;
            border-radius: 28px;
            display: flex;
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0,0,0,0.4);
            margin: auto;
            position: relative;
            font-family: 'Segoe UI', sans-serif;
        }}

        /* Cột trái - Khung Xanh lá Cocoon */
        .card-left {{
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
        }}

        .card-left img.logo {{
            width: 100px;
            margin-bottom: 25px;
        }}

        .card-left h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #ffffff;
            letter-spacing: 0.5px;
        }}

        .card-left p {{
            font-size: 13px;
            line-height: 1.6;
            opacity: 0.85;
            margin-bottom: 35px;
            padding: 0 10px;
        }}

        .left-badge {{
            font-size: 10px;
            letter-spacing: 1.5px;
            opacity: 0.7;
            text-transform: uppercase;
            position: absolute;
            bottom: 25px;
        }}

        /* Cột phải - Form & Chuyển ảnh Slideshow */
        .card-right {{
            flex: 1;
            padding: 40px 50px;
            display: flex;
            flex-direction: column;
            justify-content: center;
