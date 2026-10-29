"""Cocoon Analytics - Giai đoạn 5: giao diện Streamlit.

Chạy:  streamlit run app.py
"""
from __future__ import annotations

import io
import os
import re
import traceback
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
from PIL import Image
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

import auth
import data_utils as du

# Tìm Logo
LOGO_PATH = du.HERE / "logo.png"
if not LOGO_PATH.exists():
    LOGO_PATH = du.HERE / "dataset" / "logo.png"
if hasattr(auth, "LOGO") and isinstance(auth.LOGO, Path) and auth.LOGO.exists():
    LOGO_PATH = auth.LOGO

st.set_page_config(
    page_title="Cocoon Analytics", 
    page_icon=Image.open(LOGO_PATH) if LOGO_PATH.exists() else None, 
    layout="wide"
)

# ==========================================
# CUSTOM CSS DASHBOARD EXECUTIVE UI
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    .stApp {
        background-color: #f4efe6 !important;
    }

    h1 {
        color: #1b4332 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(27, 67, 50, 0.08);
        border-left: 5px solid #1b4332;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #666666 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #1b4332 !important;
    }

    div[data-testid="stPlotlyChart"] {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(27, 67, 50, 0.08);
    }

    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 15px !important;
        color: #555555 !important;
        padding: 10px 20px !important;
    }
    button[aria-selected="true"] {
        color: #1b4332 !important;
        border-bottom-color: #1b4332 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0d1e16 !important;
        color: #ffffff;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #ee4d2d !important;
        border-color: #ee4d2d !important;
    }
</style>
""", unsafe_allow_html=True)

COLOR_DISCRETE = ["#1b4332", "#2d6a4f", "#40916c", "#52b788", "#74c69d", "#b7e4c7"]
MAP_SOURCES = {"Shopee": "#ee4d2d", "Hasaki": "#117a50"}


def style_plotly_figure(fig, title=""):
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(family="Inter, sans-serif", size=15, color="#1b4332")),
        font=dict(family="Inter, sans-serif", color="#444444"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", zeroline=False)
    return fig


@contextmanager
def guard(name: str):
    """Tab nào lỗi thì hiện khung đỏ ngay trong tab đó, không làm các tab khác bị trống."""
    try:
        yield
    except Exception as e:  # noqa: BLE001
        st.error(f"Lỗi ở tab «{name}»: {type(e).__name__}: {e}")
        with st.expander("Chi tiết lỗi (gửi cho người hỗ trợ)"):
            st.code(traceback.format_exc())


_ILLEGAL_XL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def xl_clean(d: pd.DataFrame) -> pd.DataFrame:
    """Bỏ ký tự điều khiển để ghi Excel không bị lỗi."""
    d = d.copy()
    for c in d.select_dtypes(include=["object"]).columns:
        d[c] = d[c].map(lambda v: _ILLEGAL_XL.sub("", v) if isinstance(v, str) else v)
    return d


ALLOW_USER_EXPORT = True

auth.login_gate()
user = auth.current_user()
admin = auth.is_admin()


@st.cache_data(ttl=600, show_spinner="Đang nạp dữ liệu...")
def get_base(signature: tuple) -> pd.DataFrame:
    return du.load_base()


@st.cache_data(ttl=600, show_spinner="Đang nạp dữ liệu Power BI...")
def get_powerbi_tables(signature: tuple) -> dict:
    return du.load_powerbi_tables()


base = du.apply_deletions(get_base(du.data_signature()))


def fmt_int(x) -> str:
    return "-" if pd.isna(x) else f"{int(x):,}".replace(",", ".")


with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=90)
    st.markdown(f"**{user['username']}** · `{user['role']}`")
    if st.button("Đăng xuất"):
        auth.logout()
        st.rerun()
    st.divider()
    st.header("Bộ lọc")

source = st.sidebar.selectbox("Nền tảng", ["Tất cả", "Shopee", "Hasaki"])
df = base if source == "Tất cả" else base[base["Nguồn"] == source]

categories = ["Tất cả"] + sorted([str(x) for x in df["Hạng mục"].dropna().unique() if str(x).strip()])
category = st.sidebar.selectbox("Hạng mục", categories)
if category != "Tất cả":
    df = df[df["Hạng mục"] == category]

lines = ["Tất cả"] + sorted([str(x) for x in df["Dòng sản phẩm"].dropna().unique() if str(x).strip()])
line = st.sidebar.selectbox("Dòng sản phẩm", lines)
if line != "Tất cả":
    df = df[df["Dòng sản phẩm"] == line]

products = ["Tất cả"] + sorted([str(x) for x in df["Tên sản phẩm"].dropna().unique() if str(x).strip()])
product = st.sidebar.selectbox("Sản phẩm", products)
if product != "Tất cả":
    df = df[df["Tên sản phẩm"] == product]

stars = st.sidebar.multiselect("Số sao", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])
if stars and set(stars) != {1, 2, 3, 4, 5} and not df.empty:
    df = df[df["Số sao"].isin(stars)]

if not df.empty and df["Ngày review"].notna().any():
    valid_dates = df["Ngày review"].dropna()
    dmin, dmax = valid_dates.min().date(), valid_dates.max().date()
    if dmin <= dmax:
        rng = st.sidebar.date_input("Ngày review", (dmin, dmax), min_value=dmin, max_value=dmax)
        if isinstance(rng, (tuple, list)) and len(rng) == 2 and (rng[0] != dmin or rng[1] != dmax):
            df = df[(df["Ngày review"].dt.date >= rng[0]) & (df["Ngày review"].dt.date <= rng[1])]

keyword = st.sidebar.text_input("Tìm trong nội dung review")
if keyword.strip() and not df.empty:
    df = df[df["Nội dung review"].str.contains(keyword.strip(), case=False, na=False, regex=False)]

st.sidebar.caption(f"{int(df['Số sao'].notna().sum()):,} / {int(base['Số sao'].notna().sum()):,} review sau khi lọc".replace(",", "."))
if admin:
    st.sidebar.caption("Dữ liệu: Đã tải")

if admin:
    with st.sidebar.expander("🔍 Kiểm tra nguồn dữ liệu"):
        try:
            for label, f in (("Hasaki - SP", du.HASAKI_PROD_FILE), ("Hasaki - Review", du.HASAKI_REV_FILE),
                             ("Shopee - SP", du.SHOPEE_PROD_FILE), ("Shopee - Review", du.SHOPEE_REV_FILE)):
                st.caption(f"{label}: {'✅' if f.exists() else '❌'} {f}")
            _hp = du._clean_raw(du._read_table(du.HASAKI_PROD_FILE))
            _hr = du._clean_raw(du._read_table(du.HASAKI_REV_FILE))
            st.caption(f"File SP Hasaki: {len(_hp)} dòng, {_hp['Mã SP'].nunique() if len(_hp) else 0} mã SP")
            st.caption(f"File Review Hasaki: {len(_hr)} dòng, {_hr['Mã SP'].nunique() if len(_hr) else 0} mã SP")
            _hb = base[base["Nguồn"] == "Hasaki"]
            st.caption(f"Sau khi nạp: {_hb['Mã SP'].nunique()} sản phẩm Hasaki")
        except Exception as e:
            st.caption(f"Không kiểm tra được: {e}")
        if st.button("Xóa cache dữ liệu"):
            st.cache_data.clear()
            st.rerun()

h1, h2 = st.columns([1, 12], vertical_alignment="center")
if LOGO_PATH.exists():
    h1.image(str(LOGO_PATH), width=70)
h2.title("Cocoon Analytics")
st.caption("Phân tích hành vi người tiêu dùng và phản hồi khách hàng - Shopee & Hasaki")

if df.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc hiện tại.")
    st.stop()

prod = du.product_table(df)
rv = df[df["Số sao"].notna()]   # chỉ các dòng có review thật
tab_names = ["📊 Tổng quan", "🗂️ Dữ liệu", "📈 Power BI", "🤖 Kết quả mô hình"]
if admin:
    tab_names.append("🔧 Quản trị")
tabs = st.tabs(tab_names)


with tabs[0], guard("Tổng quan"):
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Số sản phẩm", fmt_int(len(prod)))
    k2.metric("Số review", fmt_int(len(rv)))
    k3.metric("Sao trung bình", f"{rv['Số sao'].mean():.2f}" if len(rv) else "-")
    k4.metric("Tỉ lệ tích cực (4-5 sao)", f"{(rv['Số sao'] >= 4).mean():.1%}" if len(rv) else "-")
    k5.metric("Tỉ lệ tiêu cực (1-2 sao)", f"{(rv['Số sao'] <= 2).mean():.1%}" if len(rv) else "-")

    st.write("")
    st.subheader("Thống kê Min - Max")
    c1, c2, c3 = st.columns(3)

    def top_product(star: int):
        s = df[df["Số sao"] == star].groupby("Tên sản phẩm").size()
        return (s.idxmax(), int(s.max())) if len(s) else (None, 0)

    p5, n5 = top_product(5)
    p1, n1 = top_product(1)
    with c1:
        st.markdown("**Sản phẩm được 5 sao nhiều nhất**")
        st.write(f"{p5} - {n5} lượt" if p5 else "Không có dữ liệu")
        st.markdown("**Sản phẩm bị 1 sao nhiều nhất**")
        st.write(f"{p1} - {n1} lượt" if p1 else "Không có review 1 sao trong bộ lọc")

    monthly_all = df.dropna(subset=["Tháng"]).groupby("Tháng").size()
    with c2:
        st.markdown("**Tháng nhiều review nhất**")
        if len(monthly_all):
            st.write(f"{monthly_all.idxmax():%m/%Y} - {int(monthly_all.max())} review")
            st.markdown("**Tháng ít review nhất**")
            st.write(f"{monthly_all.idxmin():%m/%Y} - {int(monthly_all.min())} review")
        st.caption("Dữ liệu không có doanh thu theo tháng nên dùng số review làm thước đo xu hướng mua.")

    rev = prod.dropna(subset=["Doanh thu 30 ngày"])
    rev = rev[rev["Doanh thu 30 ngày"] > 0]
    with c3:
        if len(rev):
            hi = rev.loc[rev["Doanh thu 30 ngày"].idxmax()]
            lo = rev.loc[rev["Doanh thu 30 ngày"].idxmin()]
            st.markdown("**Sản phẩm doanh thu 30 ngày cao nhất**")
            st.write(f"{hi['Tên sản phẩm']} - {fmt_int(hi['Doanh thu 30 ngày'])} d")
            st.markdown("**Sản phẩm doanh thu 30 ngày thấp nhất**")
            st.write(f"{lo['Tên sản phẩm']} - {fmt_int(lo['Doanh thu 30 ngày'])} d")
        else:
            st.markdown("**Doanh thu 30 ngày**")
            st.write("Không có dữ liệu doanh thu (chỉ có ở Shopee).")

    st.write("")
    st.subheader("Biểu đồ phân tích")
    g1, g2 = st.columns(2)

    with g1:
        rev_data = prod.copy()
        if "Doanh thu 30 ngày" in rev_data.columns:
            rev_data["Doanh thu 30 ngày"] = pd.to_numeric(rev_data["Doanh thu 30 ngày"], errors="coerce").fillna(0)
            rev_valid = rev_data[rev_data["Doanh thu 30 ngày"] > 0]
            pie = rev_valid.groupby("Dòng sản phẩm", as_index=False)["Doanh thu 30 ngày"].sum()
        else:
            pie = pd.DataFrame()

        if not pie.empty and pie["Doanh thu 30 ngày"].sum() > 0:
            fig = px.pie(
                pie, 
                names="Dòng sản phẩm", 
                values="Doanh thu 30 ngày", 
                hole=0.45, 
                color_discrete_sequence=COLOR_DISCRETE
            )
            fig = style_plotly_figure(fig, "Cơ cấu doanh thu 30 ngày theo dòng sản phẩm")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu doanh thu để vẽ biểu đồ tròn.")

    with g2:
        mt = du.monthly_table(df)
        if len(mt):
            fig = px.line(
                mt, 
                x="Tháng", 
                y="Số review", 
                color="Nguồn", 
                markers=True, 
                color_discrete_map=MAP_SOURCES
            )
            fig = style_plotly_figure(fig, "Xu hướng số lượng review theo tháng")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu review theo tháng.")

    g3, g4 = st.columns(2)
    with g3:
        dist = df.groupby(["Số sao", "Nguồn"]).size().reset_index(name="Số review")
        fig = px.bar(
            dist, 
            x="Số sao", 
            y="Số review", 
            color="Nguồn", 
            barmode="group", 
            color_discrete_map=MAP_SOURCES
        )
        fig = style_plotly_figure(fig, "Phân bố số sao")
        st.plotly_chart(fig, use_container_width=True)

    with g4:
        top = prod.nlargest(10, "Số review")
        fig = px.bar(
            top, 
            x="Số review", 
            y="Tên sản phẩm", 
            orientation="h", 
            color_discrete_sequence=["#1b4332"]
        )
        fig = style_plotly_figure(fig, "Top 10 sản phẩm theo số review")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)


with tabs[1], guard("Dữ liệu"):
    st.subheader("Bảng sản phẩm")
    st.dataframe(prod, use_container_width=True, hide_index=True)
    st.subheader("Bảng review")
    show = ["Nguồn", "Mã SP", "Tên sản phẩm", "Hạng mục", "Số sao", "Cảm xúc", "Nội dung review", "Ngày review", "Đã mua hàng"]
    show = [c for c in show if c in rv.columns]
    st.dataframe(rv[show].sort_values("Ngày review", ascending=False).head(2000), use_container_width=True, hide_index=True)
    if len(rv) > 2000:
        st.caption("Hiển thị 2.000 review mới nhất; bản xuất file (Admin) chứa đầy đủ.")

    # ---------------------------------------------------------
    # KẾT XUẤT BÁO CÁO (CSV UTF-8-SIG & EXCEL MULTI-SHEET)
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📥 Kết xuất báo cáo dữ liệu")

    if admin or ALLOW_USER_EXPORT:
        # 1. Chuẩn bị bảng tóm tắt chỉ số KPI
        summary_df = pd.DataFrame({
            "Chỉ số": ["Tổng số review", "Tổng số sản phẩm", "Điểm sao trung bình", "Tỉ lệ tích cực (4-5 sao)", "Tỉ lệ tiêu cực (1-2 sao)"],
            "Giá trị": [
                len(rv),
                len(prod),
                round(rv["Số sao"].mean(), 2) if len(rv) else None,
                f"{round((rv['Số sao'] >= 4).mean() * 100, 1)}%" if len(rv) else "-",
                f"{round((rv['Số sao'] <= 2).mean() * 100, 1)}%" if len(rv) else "-"
            ],
        })

        # Lọc bỏ các cột kỹ thuật nội bộ trước khi xuất file
        clean_df = rv.drop(columns=["rid", "Tháng"], errors="ignore")

        # Chia 3 cột chứa 3 nút tải
        d1, d2, d3 = st.columns(3)

        # Nút 1: Tải file CSV Review (mã hóa utf-8-sig hiển thị Tiếng Việt chuẩn)
        csv_rev_bytes = clean_df.to_csv(index=False).encode("utf-8-sig")
        d1.download_button(
            label="📄 Tải Review (CSV)",
            data=csv_rev_bytes,
            file_name="cocoon_reviews.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Nút 2: Tải file CSV Sản phẩm
        csv_prod_bytes = prod.to_csv(index=False).encode("utf-8-sig")
        d2.download_button(
            label="📄 Tải Sản Phẩm (CSV)",
            data=csv_prod_bytes,
            file_name="cocoon_products.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Nút 3: Tải file Excel (.xlsx) chứa 3 Sheet: Tóm tắt, Sản phẩm, Review
        try:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                xl_clean(summary_df).to_excel(writer, sheet_name="Tóm Tắt Chỉ Số", index=False)
                xl_clean(prod).to_excel(writer, sheet_name="Danh Sách Sản Phẩm", index=False)
                xl_clean(clean_df).to_excel(writer, sheet_name="Chi Tiết Review", index=False)

            d3.download_button(
                label="📊 Tải Báo Cáo (Excel)",
                data=excel_buffer.getvalue(),
                file_name="cocoon_analytics_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            d3.warning(f"Không tạo được file Excel: {e}")
    else:
        st.info("🔒 Tính năng tải dữ liệu hiện bị khóa bởi Quản trị viên.")


with tabs[2], guard("Power BI"):
    try:
        from powerbi_dashboard import render_powerbi_dashboard
        render_powerbi_dashboard(**get_powerbi_tables(du.data_signature()))
    except ModuleNotFoundError as e:
        st.error(f"Thiếu file `powerbi_dashboard.py` hoặc thư viện `plotly` ({e}) - hãy đặt file cùng thư mục với app.py và thêm plotly vào requirements.txt.")
    except AttributeError as e:
        st.error(f"File data_utils.py chưa cập nhật (thiếu hàm load_powerbi_tables): {e}")
    except Exception as e:
        st.error(f"Không dựng được dashboard Power BI: {type(e).__name__}: {e}")
        with st.expander("Chi tiết lỗi"):
            st.code(traceback.format_exc())


with tabs[3], guard("Kết quả mô hình"):
    st.subheader("Kết quả mô hình (Giai đoạn 4)")
    st.caption("Kết quả từ notebook huấn luyện mô hình trên dữ liệu Shopee & Hasaki.")

    MODEL_SECTIONS = [
        ("Tổng quan dữ liệu", [], ["00_eda_tong_quan"]),
        ("A1. Dự báo review tiêu cực - Logistic Regression / Decision Tree / Random Forest",
         ["A1_phan_loai_chi_so", "A1_bang_nguong_canh_bao", "A1_tu_khoa_tieu_cuc", "A1_canh_bao_cskh"],
         ["A1_so_sanh_va_confusion_matrix", "A1_tu_khoa"]),
        ("A2. Dự báo doanh thu 30 ngày Hasaki - Hồi quy",
         ["A2_hoi_quy_chi_so_test", "A2_hoi_quy_chi_so_cv", "A2_phan_du_san_pham"],
         ["A2_hoi_quy", "A2_do_quan_trong_dac_trung"]),
        ("B1. Phân khúc RFM sản phẩm", ["B1_rfm_san_pham"], ["B1_rfm_phan_khuc"]),
        ("B2. K-Means - phân cụm sản phẩm", ["B2_kmeans_dac_trung_cum"], ["B2_kmeans"]),
        ("B3. Luật kết hợp - Apriori / FP-Growth", ["B3_luat_ket_hop"], ["B3_luat_ket_hop"]),
        ("C. Topic modeling - TF-IDF + NMF", ["C_topic_tong_hop"], ["C_topic_tu_khoa", "C_topic_san_sao"]),
    ]

    def _find_model_file(name, ext):
        for root in (du.HERE / "dataset", du.HERE.parent / "dataset", du.HERE.parent):
            if root.exists():
                for p in root.rglob(f"{name}.{ext}"):
                    return p
        return None

    found = False
    for i, (title, tables, figures) in enumerate(MODEL_SECTIONS):
        t_files = [(n, _find_model_file(n, "csv")) for n in tables]
        f_files = [(n, _find_model_file(n, "png")) for n in figures]
        t_files = [(n, p) for n, p in t_files if p]
        f_files = [(n, p) for n, p in f_files if p]
        if not t_files and not f_files:
            continue
        found = True
        with st.expander(title, expanded=(i == 1)):
            for n, p in f_files:
                try:
                    st.image(str(p), width="stretch")
                except TypeError:
                    st.image(str(p), use_container_width=True)
            for n, p in t_files:
                st.markdown(f"**{n}**")
                st.dataframe(pd.read_csv(p), use_container_width=True, hide_index=True)

    if not found:
        st.info("Chưa có file kết quả A1, A2, B1, B2, B3, C trong repo.")
        _all = sorted(str(p.relative_to(du.HERE.parent)) for p in du.HERE.parent.rglob("*")
                      if p.suffix.lower() in (".csv", ".png") and ".git" not in p.parts)
        st.caption("Các file CSV/PNG đang có trong repo:")
        st.code("\n".join(_all[:60]) if _all else "(không có file nào)")

if admin:
    with tabs[4], guard("Quản trị"):
        st.subheader("Quản trị dữ liệu")
        st.caption("Xóa là *xóa mềm*: file dữ liệu gốc không bị sửa, có thể khôi phục.")

        st.markdown("**1. Chọn từng review để xóa** (tối đa 300 dòng theo bộ lọc hiện tại)")
        cols = ["rid", "Nguồn", "Tên sản phẩm", "Số sao", "Nội dung review"]
        sample = rv[cols].head(300).copy()
        sample.insert(0, "Xóa", False)
        edited = st.data_editor(
            sample,
            hide_index=True,
            use_container_width=True,
            key="del_editor",
            disabled=cols,
            column_config={
                "Xóa": st.column_config.CheckboxColumn("Xóa"),
                "rid": st.column_config.TextColumn("ID")
            }
        )
        picked = edited.loc[edited["Xóa"], "rid"].tolist()
        if st.button(f"Xóa {len(picked)} review đã chọn", disabled=not picked):
            n = du.delete_rows(picked, user["username"])
            st.success(f"Đã xóa {n} review.")
            st.rerun()

        st.markdown("**2. Xóa toàn bộ review đang lọc**")
        confirm = st.text_input(f"Gõ XOA để xác nhận xóa {len(rv)} review", key="confirm_all")
        if st.button("Xóa toàn bộ kết quả lọc", disabled=confirm != "XOA"):
            n = du.delete_rows(rv["rid"].tolist(), user["username"])
            st.success(f"Đã xóa {n} review.")
            st.rerun()

        st.markdown("**3. Nhật ký xóa / khôi phục**")
        log = du.load_deleted()
        if log:
            st.dataframe(pd.DataFrame(log), use_container_width=True, hide_index=True)
            if st.button("Khôi phục tất cả"):
                du.restore_all()
                st.rerun()
        else:
            st.write("Chưa có review nào bị xóa.")
