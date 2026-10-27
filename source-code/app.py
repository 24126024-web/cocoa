"""Cocoon Analytics - Giai đoạn 5: giao diện Streamlit.

Chạy:  streamlit run app.py
"""
from __future__ import annotations

import base64
import os
from pathlib import Path

import pandas as pd
from PIL import Image
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

import auth
import data_utils as du

LOGO_PATH = auth.LOGO
st.set_page_config(page_title="Cocoon Analytics", page_icon=Image.open(LOGO_PATH), layout="wide")

ALLOW_USER_EXPORT = False

# Convert Logo sang Base64
def get_base64_of_bin_file(bin_file):
    p = Path(bin_file)
    if p.exists():
        with open(p, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""

logo_b64 = get_base64_of_bin_file(LOGO_PATH)

# ==============================================================================
# TRANG ĐĂNG NHẬP (SIGN IN - THIẾT KẾ CHUẨN THEO MẪU HÌNH THỨ 2)
# ==============================================================================
if not st.session_state.get("authenticated", False):
    st.markdown(f"""
    <style>
    /* Ẩn Header, Footer & Sidebar mặc định */
    [data-testid="stSidebar"] {{ display: none !important; }}
    header {{ visibility: hidden !important; }}
    footer {{ visibility: hidden !important; }}
    
    /* Nền đen xám nhám tổng thể giống hình mẫu thứ 2 */
    .stApp {{
        background-color: #2F3331 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }}
    
    /* Cấu trúc Cột Bên Trái (Banner Xanh Rêu) */
    .login-left-banner {{
        background: linear-gradient(145deg, #1A4D2E 0%, #0F331D 100%);
        border-radius: 24px 0 0 24px;
        padding: 50px 30px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        min-height: 480px;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.2);
    }}
    .login-left-banner img {{
        width: 110px !important;
        margin-bottom: 20px;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
    }}
    .login-left-banner h2 {{
        color: #FFFFFF !important;
        font-size: 26px !important;
        font-weight: 700 !important;
        margin-bottom: 12px !important;
    }}
    .login-left-banner p {{
        color: #C2D6C8 !important;
        font-size: 13.5px !important;
        line-height: 1.5;
        margin-bottom: 30px;
    }}
    .btn-signin-outline {{
        border: 1.5px solid #FFFFFF;
        background: transparent;
        color: #FFFFFF;
        padding: 8px 35px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 1px;
    }}
    .brand-tag {{
        margin-top: 40px;
        font-size: 10px;
        color: rgba(255,255,255,0.5);
        letter-spacing: 1px;
    }}

    /* Cấu trúc Cột Bên Phải (Form Nền Kem Mộc) */
    div[data-testid="column"]:nth-child(2) {{
        background-color: #F8F5EE !important;
        border-radius: 0 24px 24px 0;
        padding: 40px 35px !important;
    }}
    
    .login-title {{
        color: #1A4D2E !important;
        font-size: 32px !important;
        font-weight: 700 !important;
        margin-bottom: 4px;
        text-transform: lowercase;
    }}
    .login-sub {{
        color: #666666 !important;
        font-size: 13.5px !important;
        margin-bottom: 25px;
    }}

    /* Sửa Lỗi Font & Style Ô Nhập Liệu Input */
    div[data-baseweb="input"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #2E6F40 !important;
        border-radius: 20px !important;
        padding: 2px 8px !important;
    }}
    div[data-baseweb="input"] input {{
        color: #1A4D2E !important;
        font-size: 14px !important;
    }}
    label {{
        color: #1A4D2E !important;
        font-weight: 600 !important;
    }}

    /* Style Nút Bấm LOG IN */
    div.stButton > button {{
        background-color: #1A4D2E !important;
        color: #FFFFFF !important;
        border-radius: 22px !important;
        padding: 10px 0 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(26, 77, 46, 0.3) !important;
        margin
