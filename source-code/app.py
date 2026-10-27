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

# Đặt True nếu muốn tài khoản User cũng được tải file (mặc định: chỉ Admin).
ALLOW_USER_EXPORT = False

# -----------------------------------------------------------------------------
# 1. HELPER CHUYỂN LOGO SANG BASE64 CHO CSS
# -----------------------------------------------------------------------------
def get_base64_of_bin_file(bin_file):
    p = Path(bin_file)
    if p.exists():
        with open(p, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_b64 = get_base64_of_bin_file(LOGO_PATH)

# -----------------------------------------------------------------------------
# 2. XỬ LÝ ĐĂNG NHẬP / TÙY CHỈNH GIAO DIỆN SIGN IN CHUẨN DESIGN SYSTEM
# -----------------------------------------------------------------------------
# Kiểm tra nếu chưa đăng nhập -> Hiển thị Form Đăng Nhập Tùy Chỉnh
if not st.session_state.get("authenticated", False):
    st.markdown(f"""
    <style>
    /* Ẩn Header, Footer & Sidebar khi ở màn hình đăng nhập */
    [data-testid="stSidebar"] {{ display: none !important; }}
    header {{ visibility: hidden !important; }}
    footer {{ visibility: hidden !important; }}
    
    .stApp {{
        background: #111e16 !important;
        display: flex;
        justify-content: center;
        align-items: center;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    
    /* Login Wrapper (Container 2 cột) */
    .login-wrapper {{
        display: flex;
        width: 880px;
        max-width: 95vw;
        min-height: 500px;
        background: #F8F5EE;
        border-radius: 24px;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        margin: auto;
    }}
    
    /* Khung Bên Trái: Banner / Branding Panel */
    .login-left {{
        flex: 1;
        background: linear-gradient(135deg, #1A4D2E 0%, #11331E 100%);
        padding: 40px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: #FFFFFF;
        text-align: center;
        position: relative;
    }}
    
    .login-left img.logo {{
        width: 110px;
        margin-bottom: 20px;
        filter: drop-shadow(0px 4px 8px rgba(0,0,0,0.3));
    }}
    
    .login-left h2 {{
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 10px;
        color: #FFFFFF !important;
    }}
    
    .login-left p {{
        font-size: 13.5px;
        color: #D1E2D6;
        margin-bottom: 25px;
        line-height: 1.5;
    }}
    
    .btn-outline-signin {{
        border: 1.5px solid #FFFFFF;
        background: transparent;
        color: #FFFFFF;
        padding: 8px 30px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 1px;
    }}
    
    .brand-footer {{
        position: absolute;
        bottom: 20px;
        font-size: 10px;
        letter-spacing: 1px;
        color: rgba(255,255,255,0.6);
    }}

    /* Khung Bên Phải: Form Đăng Nhập */
    .login-right-container {{
        flex: 1.1;
        background: #F8F5EE;
        padding: 45px 40px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    
    .login-right-container h1 {{
        color: #1A4D2E !important;
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 4px;
        text-transform: lowercase;
    }}
    
    .login-right-container p.sub-title {{
        color: #666666;
        font-size: 13.5px;
        margin-bottom: 25px;
    }}
    
    /* Style cho Ô nhập liệu */
    div[data-baseweb="input"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #2E6F40 !important;
        border-radius: 12px !important;
    }}
    
    div[data-baseweb="input"] input {{
        color: #1A4D2E !important;
    }}
    
    /* Style cho Nút Bấm Đăng Nhập */
    .stButton > button {{
        background: #1A4D2E !important;
        color: #FFFFFF !important;
        border-radius: 22px !important;
        padding: 10px 0 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(26, 77, 46, 0.3) !important;
        transition: all 0.3s ease !important;
    }}
    
    .stButton > button:hover {{
        background: #11331E !important;
        box-shadow: 0 6px 16px rgba(26, 77, 46, 0.4) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    c_left, c_mid, c_right = st.columns([1, 8, 1])
    with c_mid:
        st.markdown(f"""
        <div class="login-wrapper">
            <div class="login-left">
                {'<img src="data:image/png;base64,' + logo_b64 + '" class="logo"/>' if logo_b64 else '🌿'}
                <h2>Welcome Back!</h2>
                <p>To stay connected with us please login with your personal info</p>
                <div class="btn-outline-signin">SIGN IN</div>
                <div class="brand-footer">COCOON ORIGINAL VIETNAM | NATURALLY CRAFTED</div>
            </div>
            <div class="login-right-container">
                <h1>welcome</h1>
                <p class="sub-title">Login in to your account to continue</p>
        """, unsafe_allow_html=True)
        
        # Form đăng nhập tương thích với auth.py
        auth.login_gate()

        st.markdown("""
                <div style="text-align: center; margin-top: 15px; font-size: 13px; color: #666666;">
                    Don't have an account? <a href="#" style="color: #1A4D2E; font-weight: 700; text-decoration: none;">Sign up</a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# -----------------------------------------------------------------------------
# 3. TRANG DASHBOARD CHÍNH (Đã đăng nhập)
# -----------------------------------------------------------------------------
user = auth.current_user()
admin = auth.is_admin()

# Theme CSS cho Dashboard
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

.stApp {
    background-color: #F8F5EE !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: #1A4D2E !important;
    border-right: 1px solid #11331E;
}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
    color: #F8F5EE !important;
}

/* Metric Card Styling */
div[data-testid="metric-container"] {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 16px 20px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
[data-testid="stMetricLabel"] {
    color: #64748B !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
[data-testid="stMetricValue"] {
    color: #1A4D2E !important;
    font-weight: 700 !important;
}

/* Tab Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    background-color: #EFECE6;
    border-radius: 8px 8px 0px 0px;
    padding: 8px 16px;
    color: #1A4D2E;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background-color: #1A4D2E !important;
    color: #FFFFFF !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Đang nạp dữ liệu…")
def get_base(signature: tuple) -> pd.DataFrame:
    return du.load_base()


base = du.apply_deletions(get_base(du.data_signature()))


def fmt_int(x) -> str:
    return "—" if pd.isna(x) else f"{int(x):,}".replace(",", ".")


with st.sidebar:
    st.image(str(LOGO_PATH), width=90)
    st.markdown(f"👤 **{user['username']}** · `{user['role']}`")
    if st.button("Đăng xuất"):
        auth.logout()
    st.divider()
    st.header("Bộ lọc")

source = st.sidebar.selectbox("Nền tảng", ["Tất cả", "Shopee", "Hasaki"])
df = base if source == "Tất cả" else base[base["Nguồn"] == source]

categories = ["Tất cả"] + sorted(df["Hạng mục"].dropna().unique())
category = st.sidebar.selectbox("Hạng mục", categories)
if category != "Tất cả":
    df = df[df["Hạng mục"] == category]

lines = ["Tất cả"] + sorted(df["Dòng sản phẩm"].dropna().unique())
line = st.sidebar.selectbox("Dòng sản phẩm", lines)
if line != "Tất cả":
    df = df[df["Dòng sản phẩm"] == line]

products = ["Tất cả"] + sorted(df["Tên sản phẩm"].dropna().unique())
product = st.sidebar.selectbox("Sản phẩm", products)
if product != "Tất cả":
    df = df[df["Tên sản phẩm"] == product]

stars = st.sidebar.multiselect("Số sao", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])
df = df[df["Số sao"].isin(stars)]

if df["Ngày review"].notna().any():
    dmin, dmax = df["Ngày review"].min().date(), df["Ngày review"].max().date()
    rng = st.sidebar.date_input("Ngày review", (dmin, dmax), min_value=dmin, max_value=dmax)
    if isinstance(rng, (tuple, list)) and len(rng) == 2:
        df = df[(df["Ngày review"].dt.date >= rng[0]) & (df["Ngày review"].dt.date <= rng[1])]

keyword = st.sidebar.text_input("Tìm trong nội dung review")
if keyword.strip():
    df = df[df["Nội dung review"].str.contains(keyword.strip(), case=False, na=False, regex=False)]

st.sidebar.caption(f"{len(df):,} / {len(base):,} review sau khi lọc".replace(",", "."))
if admin:
    st.sidebar.caption(f"📁 Dữ liệu: Đã tải")

# --- KHỞI TẠO BẢNG MÀU CHUẨN ĐƯỢC PHÂN CHIA CHO HASAKI & SHOPEE ---
COLOR_HASAKI = {
    "primary": "#2D6844",
    "sec1": "#4E9F6E",
    "sec2": "#86C89B",
    "sec3": "#C2EABD",
    "accent": "#E8A838",
    "pie": ["#2D6844", "#4E9F6E", "#86C89B", "#C2EABD", "#E8A838"]
}

COLOR_SHOPEE = {
    "primary": "#EE4D2D",
    "sec1": "#FF7337",
    "sec2": "#FFA066",
    "sec3": "#FFCFA8",
    "accent": "#26A69A",
    "pie": ["#EE4D2D", "#FF7337", "#FFA066", "#FFCFA8", "#26A69A"]
}

# Chọn màu linh hoạt theo bộ lọc nền tảng
if source == "Hasaki":
    active_primary = COLOR_HASAKI["primary"]
    active_pie = COLOR_HASAKI["pie"]
elif source == "Shopee":
    active_primary = COLOR_SHOPEE["primary"]
    active_pie = COLOR_SHOPEE["pie"]
else:
    active_primary = "#1A4D2E"
    active_pie = ["#2D6844", "#EE4D2D", "#4E9F6E", "#FF7337", "#86C89B"]

h1, h2 = st.columns([1, 12], vertical_alignment="center")
h1.image(str(LOGO_PATH), width=70)
h2.title("Cocoon Analytics")
st.caption("Phân tích hành vi người tiêu dùng và phản hồi khách hàng — Shopee & Hasaki")

if df.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc hiện tại.")
    st.stop()

prod = du.product_table(df)
tab_names = ["📊 Tổng quan", "🗂️ Dữ liệu", "📈 Power BI", "🤖 Kết quả mô hình"]
if admin:
    tab_names.append("🔧 Quản trị")
tabs = st.tabs(tab_names)


with tabs[0]:
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Số sản phẩm", fmt_int(len(prod)))
    k2.metric("Số review", fmt_int(len(df)))
    k3.metric("Sao trung bình", f"{df['Số sao'].mean():.2f}")
    k4.metric("Tỉ lệ tích cực (4–5★)", f"{(df['Số sao'] >= 4).mean():.1%}")
    k5.metric("Tỉ lệ tiêu cực (1–2★)", f"{(df['Số sao'] <= 2).mean():.1%}")

    st.subheader("Thống kê Min – Max")
    c1, c2, c3 = st.columns(3)

    def top_product(star: int):
        s = df[df["Số sao"] == star].groupby("Tên sản phẩm").size()
        return (s.idxmax(), int(s.max())) if len(s) else (None, 0)

    p5, n5 = top_product(5)
    p1, n1 = top_product(1)
    c1.markdown("**Sản phẩm được 5★ nhiều nhất**")
    c1.write(f"{p5} — {n5} lượt" if p5 else "Không có dữ liệu")
    c1.markdown("**Sản phẩm bị 1★ nhiều nhất**")
    c1.write(f"{p1} — {n1} lượt" if p1 else "Không có review 1★ trong bộ lọc")

    monthly_all = df.dropna(subset=["Tháng"]).groupby("Tháng").size()
    c2.markdown("**Tháng nhiều review nhất**")
    if len(monthly_all):
        c2.write(f"{monthly_all.idxmax():%m/%Y} — {int(monthly_all.max())} review")
        c2.markdown("**Tháng ít review nhất**")
        c2.write(f"{monthly_all.idxmin():%m/%Y} — {int(monthly_all.min())} review")
    c2.caption("Dữ liệu không có doanh thu theo tháng nên dùng số review làm thước đo xu hướng mua.")

    rev = prod.dropna(subset=["Doanh thu 30 ngày"])
    rev = rev[rev["Doanh thu 30 ngày"] > 0]
    if len(rev):
        hi = rev.loc[rev["Doanh thu 30 ngày"].idxmax()]
        lo = rev.loc[rev["Doanh thu 30 ngày"].idxmin()]
        c3.markdown("**Sản phẩm doanh thu 30 ngày cao nhất**")
        c3.write(f"{hi['Tên sản phẩm']} — {fmt_int(hi['Doanh thu 30 ngày'])} ₫")
        c3.markdown("**Sản phẩm doanh thu 30 ngày thấp nhất**")
        c3.write(f"{lo['Tên sản phẩm']} — {fmt_int(lo['Doanh thu 30 ngày'])} ₫")
    else:
        c3.markdown("**Doanh thu 30 ngày**")
        c3.write("Không có dữ liệu doanh thu (chỉ có ở Shopee).")

    st.subheader("Biểu đồ")
    g1, g2 = st.columns(2)

    with g1:
        pie = (rev.groupby("Dòng sản phẩm")["Doanh thu 30 ngày"].sum().reset_index())
        if len(pie):
            fig = px.pie(
                pie, 
                names="Dòng sản phẩm", 
                values="Doanh thu 30 ngày", 
                hole=0.35,
                title="Cơ cấu doanh thu 30 ngày theo dòng sản phẩm",
                color_discrete_sequence=active_pie
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu doanh thu để vẽ biểu đồ tròn.")

    with g2:
        mt = du.monthly_table(df)
        if source == "Tất cả":
            fig = px.line(
                mt, x="Tháng", y="Số review", color="Nguồn", markers=True,
                title="Xu hướng số lượng review theo tháng",
                color_discrete_map={"Hasaki": COLOR_HASAKI["primary"], "Shopee": COLOR_SHOPEE["primary"]}
            )
        else:
            fig = px.line(
                mt, x="Tháng", y="Số review", markers=True,
                title="Xu hướng số lượng review theo tháng",
                color_discrete_sequence=[active_primary]
            )
        fig.update_traces(line=dict(width=3))
        st.plotly_chart(fig, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        dist = df.groupby(["Số sao", "Nguồn"]).size().reset_index(name="Số review")
        if source == "Tất cả":
            fig = px.bar(
                dist, x="Số sao", y="Số review", color="Nguồn", barmode="group",
                title="Phân bố số sao",
                color_discrete_map={"Hasaki": COLOR_HASAKI["primary"], "Shopee": COLOR_SHOPEE["primary"]}
            )
        else:
            fig = px.bar(
                dist, x="Số sao", y="Số review",
                title="Phân bố số sao",
                color_discrete_sequence=[active_primary]
            )
        fig.update_traces(marker_cornerRadius=6)
        st.plotly_chart(fig, use_container_width=True)

    with g4:
        top = prod.nlargest(10, "Số review")
        fig = px.bar(
            top, x="Số review", y="Tên sản phẩm", orientation="h",
            title="Top 10 sản phẩm theo số review",
            color_discrete_sequence=[active_primary]
        )
        fig.update_traces(marker_cornerRadius=6)
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)


with tabs[1]:
    st.subheader("Bảng sản phẩm")
    st.dataframe(prod, use_container_width=True, hide_index=True)
    st.subheader("Bảng review")
    show = ["Nguồn", "Mã SP", "Tên sản phẩm", "Hạng mục", "Số sao", "Cảm xúc",
            "Nội dung review", "Ngày review", "Đã mua hàng"]
    st.dataframe(df[show].sort_values("Ngày review", ascending=False).head(2000),
                 use_container_width=True, hide_index=True)
    if len(df) > 2000:
        st.caption("Hiển thị 2.000 review mới nhất; bản xuất file (Admin) chứa đầy đủ.")

    st.subheader("Kết xuất báo cáo")
    if admin or ALLOW_USER_EXPORT:
        summary = pd.DataFrame({
            "Chỉ số": ["Số review", "Số sản phẩm", "Sao trung bình", "% tích cực (4-5★)", "% tiêu cực (1-2★)"],
            "Giá trị": [len(df), len(prod), round(df["Số sao"].mean(), 2),
                        round((df["Số sao"] >= 4).mean() * 100, 1),
                        round((df["Số sao"] <= 2).mean() * 100, 1)],
        })
        d1, d2, d3 = st.columns(3)
        d1.download_button("⬇️ Review (CSV)", du.to_csv_bytes(df.drop(columns=["rid", "Tháng"])),
                           "cocoon_reviews.csv", "text/csv")
        d2.download_button("⬇️ Sản phẩm (CSV)", du.to_csv_bytes(prod),
                           "cocoon_products.csv", "text/csv")
        d3.download_button(
            "⬇️ Báo cáo (Excel)",
            du.to_excel_bytes({"Tóm tắt": summary, "Sản phẩm": prod,
                               "Review": df.drop(columns=["rid", "Tháng"])}),
            "cocoon_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Chỉ tài khoản Admin được tải dữ liệu.")


with tabs[2]:
    st.subheader("Dashboard Power BI")
    url = os.environ.get("POWERBI_EMBED_URL", "")
    try:
        url = st.secrets.get("POWERBI_EMBED_URL", url)
    except Exception:
        pass
    if admin:
        url = st.text_input("Link nhúng Power BI (Publish to web)", value=url,
                            help="Có thể đặt cố định trong secrets.toml → POWERBI_EMBED_URL")
    if url and url.startswith("https://"):
        components.iframe(url, height=720, scrolling=True)
    else:
        st.info(
            "Chưa cấu hình link Power BI.\n\n"
            "1. Mở `dashboard_CK_real.pbix` → **Publish** lên Power BI Service.\n"
            "2. Vào báo cáo → **File → Embed report → Publish to web (public)** → copy link.\n"
            "3. Dán vào `POWERBI_EMBED_URL` trong `.streamlit/secrets.toml` (hoặc ô nhập ở trên, nếu là Admin).\n\n"
            "Lưu ý: *Publish to web* công khai báo cáo với bất kỳ ai có link.")


with tabs[3]:
    st.subheader("Kết quả mô hình (Giai đoạn 4)")
    st.caption("Đặt file kết quả vào `dataset/model_outputs/` — app tự hiển thị.")
    expected = {
        "kmeans_clusters.csv": "K-Means: phân cụm khách hàng / review",
        "sentiment_predictions.csv": "Dự đoán cảm xúc (Random Forest / Logistic Regression)",
        "apriori_rules.csv": "Luật kết hợp Apriori (gợi ý combo)",
    }
    found = False
    for fname, title in expected.items():
        p = du.MODEL_DIR / fname
        if p.exists():
            found = True
            with st.expander(f"{title} — {fname}", expanded=True):
                st.dataframe(pd.read_csv(p), use_container_width=True, hide_index=True)
    if not found:
        st.info("Chưa có file kết quả. Tên file mong đợi: "
                + ", ".join(f"`{k}`" for k in expected))


if admin:
    with tabs[4]:
        st.subheader("Quản trị dữ liệu")
        st.caption("Xóa là *xóa mềm*: file dữ liệu gốc không bị sửa, có thể khôi phục.")

        st.markdown("**1. Chọn từng review để xóa** (tối đa 300 dòng theo bộ lọc hiện tại)")
        cols = ["rid", "Nguồn", "Tên sản phẩm", "Số sao", "Nội dung review"]
        sample = df[cols].head(300).copy()
        sample.insert(0, "Xóa", False)
        edited = st.data_editor(
            sample, hide_index=True, use_container_width=True, key="del_editor",
            disabled=cols,
            column_config={"Xóa": st.column_config.CheckboxColumn("Xóa"),
                           "rid": st.column_config.TextColumn("ID")})
        picked = edited.loc[edited["Xóa"], "rid"].tolist()
        if st.button(f"🗑️ Xóa {len(picked)} review đã chọn", disabled=not picked):
            n = du.delete_rows(picked, user["username"])
            st.success(f"Đã xóa {n} review.")
            st.rerun()

        st.markdown("**2. Xóa toàn bộ review đang lọc**")
        confirm = st.text_input(f"Gõ XOA để xác nhận xóa {len(df)} review", key="confirm_all")
        if st.button("🗑️ Xóa toàn bộ kết quả lọc", disabled=confirm != "XOA"):
            n = du.delete_rows(df["rid"].tolist(), user["username"])
            st.success(f"Đã xóa {n} review.")
            st.rerun()

        st.markdown("**3. Nhật ký xóa / khôi phục**")
        log = du.load_deleted()
        if log:
            st.dataframe(pd.DataFrame(log), use_container_width=True, hide_index=True)
            if st.button("♻️ Khôi phục tất cả"):
                du.restore_all()
                st.rerun()
        else:
            st.write("Chưa có review nào bị xóa.")
