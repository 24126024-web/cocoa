# -*- coding: utf-8 -*-
"""
powerbi_dashboard.py  (phiên bản 2 - theo dashboard_cocoon_shopee_CK.pbix)
Dựng lại dashboard Power BI bằng Streamlit + Plotly: 8 trang
  Shopee : Tổng quan / Phân tích sản phẩm / Phân tích đánh giá / Min-Max
  Hasaki : Tổng quan / Phân tích sản phẩm / Phân tích đánh giá / Min-Max

Dùng trong app.py (giữ nguyên cách gọi cũ):
    from powerbi_dashboard import render_powerbi_dashboard
    render_powerbi_dashboard(**get_powerbi_tables(du.data_signature()))
Cần `plotly` trong requirements.txt.
"""
from __future__ import annotations

import re
import unicodedata
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# 1. CẤU HÌNH TÊN CỘT (sửa ở đây nếu file dữ liệu đặt tên khác)
# ----------------------------------------------------------------------------
ID, NAME, CAT = "Mã SP", "Tên sản phẩm", "Category"
PRICE, ORIG, DISC = "Giá bán", "Giá gốc", "% Giảm giá"
REV, RATING, STATUS = "Doanh thu 30 ngày", "Điểm đánh giá TB", "Trang_Thai_Mau"
SOLD = {"Shopee": "Lượt bán", "Hasaki": "Lượt bán (30 ngày)"}
R_STAR, R_DATE = "Số sao (review)", "Ngày review"
R_SENT, R_VERIFIED = "Sentiment", "Xác nhận mua hàng"
REVM = "Doanh thu (triệu đồng)"          # cột phụ: doanh thu quy ra triệu

GREEN, ORANGE = "#116B3A", "#EE4D2D"
THEME = {
    "Shopee": dict(accent=ORANGE, bg="#FFF7F4",
                   seq=[ORANGE, GREEN, "#C83B22", "#16834A", "#D64124", "#245C3A", "#BD2426", "#8FBF9F"],
                   title="HIỆU QUẢ KINH DOANH CỦA COCOON TRÊN SHOPEE"),
    "Hasaki": dict(accent=GREEN, bg="#EAF5EE",
                   seq=[GREEN, "#16834A", "#245C3A", ORANGE, "#8FBF9F", "#C83B22", "#BD2426", "#D64124"],
                   title="HIỆU QUẢ KINH DOANH CỦA COCOON TRÊN HASAKI"),
}
BIN_EDGES = [0, 100e3, 200e3, 300e3, 500e3, 1e6, np.inf]
BIN_LABELS = ["<100K", "100–200K", "200–300K", "300–500K", "500K–1M", ">1M"]
PERIOD = {"Ngày": "D", "Tuần": "W", "Tháng": "M", "Quý": "Q", "Năm": "Y"}


# ----------------------------------------------------------------------------
# 2. TIỆN ÍCH
# ----------------------------------------------------------------------------
@contextmanager
def safe(label: str = ""):
    """Một biểu đồ lỗi không làm sập cả trang."""
    try:
        yield
    except Exception as e:  # noqa: BLE001
        st.warning(f"⚠️ Không vẽ được «{label}»: {e}")


def _key(s) -> str:
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d").replace("Đ", "D")
    return re.sub(r"[^a-z0-9]", "", s.lower())


_CANON = [ID, NAME, CAT, PRICE, ORIG, DISC, REV, RATING, STATUS, "Lượt bán", "Lượt bán (30 ngày)",
          R_STAR, R_DATE, R_SENT, R_VERIFIED]
_ALIASES = {CAT: ["Hạng mục", "Danh mục"], R_VERIFIED: ["Đã mua hàng"], R_STAR: ["Số sao"]}


def canon_cols(d: pd.DataFrame) -> pd.DataFrame:
    """Đưa tên cột về đúng chuẩn (không phân biệt hoa/thường, dấu, khoảng trắng)."""
    d = d.copy()
    d.columns = [str(c).strip() for c in d.columns]
    exist = {_key(c): c for c in d.columns}
    ren = {}
    for c in _CANON:
        if c not in d.columns and _key(c) in exist:
            ren[exist[_key(c)]] = c
    for tgt, alts in _ALIASES.items():
        if tgt not in d.columns and tgt not in ren.values():
            for a in alts:
                if a in d.columns:
                    ren[a] = tgt
                    break
    return d.rename(columns=ren)


def _num(s: pd.Series) -> pd.Series:
    """Ép về số, hiểu cả định dạng Việt Nam '1.250.000đ'."""
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce")
    t = s.astype(str).str.strip().str.replace(r"[^\d,.\-]", "", regex=True)
    thousands = t.str.match(r"^-?\d{1,3}(\.\d{3})+$")
    t = t.where(~thousands, t.str.replace(".", "", regex=False))
    t = t.str.replace(",", ".", regex=False)
    return pd.to_numeric(t, errors="coerce")


def fint(x) -> str:
    return "—" if pd.isna(x) else f"{x:,.0f}".replace(",", ".")


def fvnd(x) -> str:
    if pd.isna(x):
        return "—"
    if abs(x) >= 1e9:
        return f"{x / 1e9:,.2f} tỷ".replace(",", ".")
    if abs(x) >= 1e6:
        return f"{x / 1e6:,.1f} triệu".replace(",", ".")
    return fint(x)


def fpct(x) -> str:
    return "—" if pd.isna(x) else f"{x:.1f}%"


def fdec(x, n=2) -> str:
    return "—" if pd.isna(x) else f"{x:.{n}f}"


def short(s, n: int = 34) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def uniq_labels(names: pd.Series, n: int = 34) -> list:
    seen, out = {}, []
    for s in names:
        lab = short(s, n)
        seen[lab] = seen.get(lab, 0) + 1
        out.append(lab if seen[lab] == 1 else f"{lab} ({seen[lab]})")
    return out


def show(fig, plat: str, height: int = 360) -> None:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="white", plot_bgcolor="white",
        title=dict(font=dict(size=15, color=THEME[plat]["accent"])),
        legend=dict(orientation="h", y=-0.2),
        font=dict(family="Segoe UI, Arial, sans-serif"),
    )
    key = f"pbi|{plat}|{fig.layout.title.text}"
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except TypeError:          # streamlit cũ
        st.plotly_chart(fig, use_container_width=True, key=key)


def show_df(df: pd.DataFrame) -> None:
    try:
        st.dataframe(df, hide_index=True, width="stretch")
    except TypeError:
        st.dataframe(df, hide_index=True, use_container_width=True)


def kpi(col, label: str, value: str, plat: str) -> None:
    th = THEME[plat]
    col.markdown(
        f"""<div style="background:{th['bg']};border-left:6px solid {th['accent']};
            border-radius:10px;padding:14px 16px;margin-bottom:10px;">
            <div style="font-size:13px;color:#555;">{label}</div>
            <div style="font-size:28px;font-weight:700;color:{th['accent']};">{value}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def banner(text: str, plat: str) -> None:
    st.markdown(
        f"""<div style="background:{THEME[plat]['accent']};color:white;text-align:center;
            padding:12px;border-radius:10px;font-size:20px;font-weight:700;margin-bottom:14px;">
            {text}</div>""",
        unsafe_allow_html=True,
    )


def top_n(d: pd.DataFrame, value: str, n: int, agg: str = "sum") -> pd.DataFrame:
    g = d.groupby(NAME, as_index=False).agg({value: agg}).dropna(subset=[value])
    g = g.nlargest(n, value).copy()
    g["_ten"] = uniq_labels(g[NAME])
    return g


def hbar(g, val, title, plat, text=".3s", cat="_ten", full=NAME):
    fig = px.bar(g, x=val, y=cat, orientation="h", text_auto=text,
                 hover_name=full if full in g else None,
                 color_discrete_sequence=[THEME[plat]["accent"]], title=title)
    fig.update_yaxes(categoryorder="total ascending", title=None)
    fig.update_xaxes(title=None)
    fig.update_traces(textposition="outside", cliponaxis=False)
    return fig


def vbar(g, cat, val, title, plat, text=".3s", full=NAME):
    fig = px.bar(g, x=cat, y=val, text_auto=text, hover_name=full if full in g else None,
                 color_discrete_sequence=[THEME[plat]["accent"]], title=title)
    fig.update_xaxes(categoryorder="total descending", title=None, tickangle=-35)
    fig.update_yaxes(title=None)
    fig.update_traces(textposition="outside", cliponaxis=False)
    return fig


def donut(d, cat, val, title, plat):
    if val:
        g = d.groupby(cat, as_index=False).agg({val: "sum"})
    else:
        g = d[cat].value_counts().rename_axis(cat).reset_index(name="n")
        val = "n"
    fig = px.pie(g, names=cat, values=val, hole=0.55, title=title,
                 color_discrete_sequence=THEME[plat]["seq"])
    fig.update_traces(textinfo="percent+label")
    return fig


def grouped_price(g, title, plat):
    """Cột đôi Giá gốc / Giá bán, giữ đúng thứ tự g."""
    fig = go.Figure([go.Bar(name="Giá gốc", x=g["_ten"], y=g[ORIG], marker_color="#8FBF9F"),
                     go.Bar(name="Giá bán", x=g["_ten"], y=g[PRICE], marker_color=THEME[plat]["accent"])])
    fig.update_layout(barmode="group", title=title)
    fig.update_xaxes(tickangle=-35, categoryorder="array", categoryarray=list(g["_ten"]))
    return fig


# ----------------------------------------------------------------------------
# 3. CHUẨN BỊ DỮ LIỆU
# ----------------------------------------------------------------------------
def _clean_id(d: pd.DataFrame) -> pd.DataFrame:
    if ID in d:
        d[ID] = d[ID].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    return d


def prep_products(df: pd.DataFrame, plat: str) -> pd.DataFrame:
    d = _clean_id(canon_cols(df))
    sold = SOLD[plat]
    other = next(v for v in SOLD.values() if v != sold)
    if sold not in d and other in d:
        d = d.rename(columns={other: sold})
    if NAME not in d:
        d[NAME] = "Sản phẩm " + d[ID].astype(str) if ID in d else "Sản phẩm"
    if CAT not in d:
        d[CAT] = "Khác"
    for c in (PRICE, ORIG, DISC, sold, REV, RATING):
        if c in d:
            d[c] = _num(d[c])
    if DISC in d:
        if d[DISC].abs().max() <= 1:               # 0.25 -> 25 %
            d[DISC] = d[DISC] * 100
    elif PRICE in d and ORIG in d:
        d[DISC] = (1 - d[PRICE] / d[ORIG]) * 100
    if REV not in d and PRICE in d and sold in d:
        d[REV] = d[PRICE] * d[sold]
    for c in (PRICE, ORIG, DISC, sold, REV, RATING):
        if c not in d:
            d[c] = np.nan
    d[REVM] = d[REV] / 1e6
    d["Nhóm giá bán"] = pd.cut(d[PRICE], BIN_EDGES, labels=BIN_LABELS, right=False)
    return d.reset_index(drop=True)


def prep_reviews(df) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame()
    d = _clean_id(canon_cols(df))
    if R_STAR in d:
        d[R_STAR] = _num(d[R_STAR])
    if R_DATE in d:
        d[R_DATE] = pd.to_datetime(d[R_DATE], errors="coerce", dayfirst=True)
    if R_SENT not in d and R_STAR in d:
        d[R_SENT] = np.where(d[R_STAR] >= 4, "Tích cực", np.where(d[R_STAR] == 3, "Trung tính", "Tiêu cực"))
    return d.reset_index(drop=True)


def attach_review_stats(p: pd.DataFrame, r: pd.DataFrame) -> pd.DataFrame:
    p = p.copy()
    key = next((k for k in (ID, NAME) if k in p and k in r), None)
    if key and R_STAR in r and not r.empty:
        g = r.dropna(subset=[R_STAR]).groupby(key)[R_STAR].agg(n_reviews="size", avg_star="mean")
        p = p.merge(g, left_on=key, right_index=True, how="left")
    else:
        p["n_reviews"], p["avg_star"] = np.nan, np.nan
    p["rating_final"] = p["avg_star"].fillna(p[RATING])
    return p


def is_negative(r: pd.DataFrame) -> pd.Series:
    if R_SENT in r:
        return r[R_SENT].astype(str).str.lower().str.strip().isin(["negative", "tiêu cực", "tieu cuc", "neg"])
    return r[R_STAR] <= 2


def is_verified(r: pd.DataFrame):
    if R_VERIFIED not in r:
        return None
    return r[R_VERIFIED].astype(str).str.lower().str.strip().isin(
        ["true", "1", "1.0", "yes", "có", "co", "đã mua", "đã mua hàng", "verified"])


# ----------------------------------------------------------------------------
# 4. TRANG 1 – TỔNG QUAN
# ----------------------------------------------------------------------------
def page_overview(p: pd.DataFrame, plat: str) -> None:
    sold = SOLD[plat]
    banner(THEME[plat]["title"], plat)
    c = st.columns(4)
    kpi(c[0], "Số lượng sản phẩm" if plat == "Shopee" else "Tổng số sản phẩm",
        fint(p[ID].nunique()) if ID in p else fint(len(p)), plat)
    kpi(c[1], "Tổng số lượt bán" if plat == "Shopee" else "Tổng lượt bán (30 ngày)", fint(p[sold].sum()), plat)
    kpi(c[2], "Điểm đánh giá TB", fdec(p[RATING].mean()), plat)
    kpi(c[3], "Tổng doanh thu 30 ngày", fvnd(p[REV].sum()), plat)

    if plat == "Shopee":
        a, b = st.columns(2)
        with a, safe("Doanh thu theo danh mục"):
            g = p.groupby(CAT, as_index=False)[REVM].sum().sort_values(REVM, ascending=False)
            fig = px.bar(g, x=REVM, y=CAT, orientation="h", text_auto=".1f",
                         color_discrete_sequence=[ORANGE], title="Tổng doanh thu theo danh mục sản phẩm")
            fig.update_yaxes(categoryorder="total ascending", title=None)
            fig.update_xaxes(title="Triệu đồng")
            fig.update_traces(textposition="outside", cliponaxis=False)
            show(fig, plat, 340)
        with b, safe("Top 10 doanh thu"):
            g = top_n(p, REVM, 10)
            show(vbar(g, "_ten", REVM, "Top 10 sản phẩm có doanh thu 30 ngày cao nhất (triệu đồng)", plat, text=".1f"),
                 plat, 340)
        a, b = st.columns(2)
        with a, safe("Tỷ trọng doanh thu"):
            show(donut(p, CAT, REV, "Tỷ trọng doanh thu theo danh mục", plat), plat, 340)
        with b, safe("Top 10 giảm giá"):
            g = top_n(p, DISC, 10, agg="mean")
            show(hbar(g, DISC, "Top 10 sản phẩm có tỷ lệ giảm giá cao nhất (%)", plat, text=".1f"), plat, 340)
        with safe("Top 10 lượt bán"):
            show(hbar(top_n(p, sold, 10), sold, "Top 10 sản phẩm có lượt bán cao nhất", plat, text=",.0f"), plat, 400)
    else:
        a, b = st.columns(2)
        with a, safe("Doanh thu theo danh mục"):
            g = p.groupby(CAT, as_index=False)[REVM].sum().sort_values(REVM, ascending=False)
            show(vbar(g, CAT, REVM, "Doanh thu 30 ngày theo danh mục (triệu đồng)", plat, text=".1f", full=CAT), plat, 380)
        with b, safe("Top 10 lượt bán"):
            show(hbar(top_n(p, sold, 10), sold, "Top 10 sản phẩm có lượt bán 30 ngày cao nhất", plat, text=",.0f"),
                 plat, 380)
        a, b = st.columns([2, 3])
        with a, safe("Tỷ trọng doanh thu"):
            show(donut(p, CAT, REV, "Tỷ trọng Doanh thu 30 ngày theo danh mục", plat), plat, 400)
        with b, safe("Scatter danh mục"):
            g = p.groupby(CAT, as_index=False).agg(gia=(PRICE, "mean"), ban=(sold, "sum"), dt=(REV, "sum"),
                                                   goc=(ORIG, "mean"), dg=(RATING, "mean"))
            fig = px.scatter(g, x="gia", y="ban", size=g["dt"].clip(lower=0).fillna(0) + 1, color=CAT,
                             hover_data={"goc": ":,.0f", "dg": ":.2f", "dt": ":,.0f"}, size_max=55,
                             labels={"gia": "Giá bán TB", "ban": "Tổng lượt bán"},
                             color_discrete_sequence=THEME[plat]["seq"],
                             title="So sánh giá bán và lượt bán theo danh mục sản phẩm")
            show(fig, plat, 400)


# ----------------------------------------------------------------------------
# 5. TRANG 2 – PHÂN TÍCH SẢN PHẨM
# ----------------------------------------------------------------------------
def page_products(p: pd.DataFrame, plat: str) -> None:
    sold = SOLD[plat]
    if plat == "Shopee":
        banner("PHÂN TÍCH GIÁ VÀ LƯỢT BÁN CỦA COCOON TRÊN SHOPEE", plat)
        a, b = st.columns([3, 2])
        with a, safe("Phân bố mức giá"):
            g = (p["Nhóm giá bán"].value_counts().rename_axis("Nhóm giá bán (VNĐ)").reset_index(name="Số SP"))
            g = g[g["Số SP"] > 0].sort_values("Số SP", ascending=False)      # Power BI sắp theo số lượng giảm dần
            fig = px.bar(g, x="Nhóm giá bán (VNĐ)", y="Số SP", text_auto=True, title="Phân bố sản phẩm theo mức giá",
                         color_discrete_sequence=[ORANGE])
            fig.update_xaxes(type="category", categoryorder="array", categoryarray=[str(x) for x in g["Nhóm giá bán (VNĐ)"]])
            show(fig, plat, 330)
        with b, safe("Giá cao nhất / thấp nhất theo danh mục"):
            t = p.groupby(CAT).agg(**{"Giá bán cao nhất": (PRICE, "max"), "Giá bán thấp nhất": (PRICE, "min")}).reset_index()
            st.markdown("**Giá bán cao nhất / thấp nhất theo danh mục**")
            show_df(t)
        with safe("Scatter giá – lượt bán"):
            g = p.groupby([NAME, CAT], as_index=False).agg(gia=(PRICE, "mean"), ban=(sold, "sum"), dt=(REV, "sum"))
            fig = px.scatter(g, x="gia", y="ban", color=CAT, size=g["dt"].clip(lower=0).fillna(0) + 1, size_max=40,
                             hover_name=NAME, labels={"gia": "Giá bán TB", "ban": "Tổng lượt bán"},
                             color_discrete_sequence=THEME[plat]["seq"],
                             title="Mối quan hệ giữa giá bán và lượt bán của sản phẩm Shopee")
            show(fig, plat, 420)
        with safe("Giá gốc vs giá bán"):
            top = p.groupby(NAME, as_index=False).agg({PRICE: "sum", ORIG: "sum", REV: "sum"}).nlargest(10, REV)
            top = top.sort_values(PRICE, ascending=False)                    # Power BI sắp theo Giá bán giảm dần
            top["_ten"] = uniq_labels(top[NAME])
            show(grouped_price(top, "Giá gốc và giá bán của Top 10 sản phẩm doanh thu cao nhất", plat), plat, 420)
    else:
        banner("PHÂN TÍCH GIÁ, LƯỢT BÁN VÀ DOANH THU CỦA COCOON TRÊN HASAKI", plat)
        sl = st.columns(3)
        d = p
        for col, field, label in ((sl[0], CAT, "Danh mục"), (sl[1], STATUS, "Trạng thái màu"), (sl[2], NAME, "Sản phẩm")):
            if field in d:
                chosen = col.multiselect(label, sorted(d[field].dropna().astype(str).unique()), key=f"hsk_{field}")
                if chosen:
                    d = d[d[field].astype(str).isin(chosen)]
        if d.empty:
            st.info("Không có dữ liệu với bộ lọc đã chọn.")
            return
        with safe("Giá gốc vs giá bán"):
            g = d.groupby(NAME, as_index=False).agg({PRICE: "mean", ORIG: "mean", REV: "sum"}).nlargest(10, REV)
            g["_ten"] = uniq_labels(g[NAME])
            show(grouped_price(g, "So sánh giá gốc và giá bán theo sản phẩm", plat), plat, 400)
        with safe("Scatter giá – điểm – lượt bán"):
            g = d.groupby([NAME, CAT], as_index=False).agg(gia=(PRICE, "mean"), dg=(RATING, "mean"), ban=(sold, "sum"))
            fig = px.scatter(g, x="gia", y="dg", size=g["ban"].clip(lower=0).fillna(0) + 1, color=CAT, size_max=40,
                             hover_name=NAME, labels={"gia": "Giá bán TB", "dg": "Điểm đánh giá TB"},
                             color_discrete_sequence=THEME[plat]["seq"],
                             title="Mối quan hệ giữa giá bán, điểm đánh giá và lượt bán sản phẩm Cocoon trên Hasaki")
            show(fig, plat, 420)
        a, b = st.columns(2)
        with a, safe("Top 10 doanh thu"):
            show(hbar(top_n(d, REVM, 10), REVM, "Top 10 sản phẩm theo doanh thu 30 ngày (triệu đồng)", plat, text=".1f"),
                 plat, 380)
        with b, safe("Lượt bán theo danh mục"):
            g = d.groupby(CAT, as_index=False)[sold].sum()
            show(vbar(g, CAT, sold, "Tổng lượt bán 30 ngày theo danh mục", plat, text=",.0f", full=CAT), plat, 380)


# ----------------------------------------------------------------------------
# 6. TRANG 3 – PHÂN TÍCH ĐÁNH GIÁ
# ----------------------------------------------------------------------------
def page_reviews(p: pd.DataFrame, r: pd.DataFrame, plat: str) -> None:
    banner("PHÂN TÍCH ĐÁNH GIÁ VÀ TRẢI NGHIỆM CỦA KHÁCH HÀNG", plat)
    if r.empty or R_STAR not in r:
        st.info("Chưa có dữ liệu đánh giá (bảng Reviews) cho sàn này.")
        return
    r = r.dropna(subset=[R_STAR])
    c = st.columns(4)
    kpi(c[0], "Điểm đánh giá trung bình", fdec(r[R_STAR].mean()), plat)
    kpi(c[1], "Tổng số lượt đánh giá", fint(len(r)), plat)
    kpi(c[2], "Tỷ lệ đánh giá 5 sao", fpct((r[R_STAR] == 5).mean() * 100), plat)
    if plat == "Shopee":
        kpi(c[3], "Tỷ lệ đánh giá tiêu cực", fpct(is_negative(r).mean() * 100), plat)
    else:
        v = is_verified(r)
        kpi(c[3], "Tỷ lệ xác nhận mua hàng", fpct(v.mean() * 100) if v is not None else "—", plat)

    cols = st.columns(3) if plat == "Shopee" else st.columns([2, 3])
    i = 0
    if plat == "Shopee":
        with cols[0], safe("Cơ cấu cảm xúc"):
            show(donut(r, R_SENT, None, "Cơ cấu cảm xúc đánh giá", plat), plat, 330)
        i = 1
    with cols[i], safe("Phân bố số sao"):
        g = r[R_STAR].value_counts().sort_index().rename_axis("Số sao").reset_index(name="Số đánh giá")
        fig = px.bar(g, x="Số sao", y="Số đánh giá", text_auto=True, title="Phân bố số sao đánh giá",
                     color_discrete_sequence=[THEME[plat]["accent"]])
        fig.update_xaxes(type="category")
        show(fig, plat, 330)
    with cols[i + 1], safe("Xu hướng đánh giá"):
        if R_DATE in r and r[R_DATE].notna().any():
            gran = st.radio("Mức thời gian", list(PERIOD), index=0, horizontal=True, key=f"gran_{plat}")
            dd = r.dropna(subset=[R_DATE])
            per = dd[R_DATE].dt.to_period(PERIOD[gran]).dt.to_timestamp()
            g = dd.groupby(per).size().rename("Số đánh giá").rename_axis("Thời gian").reset_index()
            fig = px.line(g, x="Thời gian", y="Số đánh giá", markers=True,
                          title="Xu hướng đánh giá của khách hàng theo thời gian",
                          color_discrete_sequence=[THEME[plat]["accent"]])
            show(fig, plat, 330)

    p = attach_review_stats(p, r)
    n_top = 8 if plat == "Shopee" else 10
    with safe("Top sản phẩm nhiều đánh giá"):
        g = top_n(p, "n_reviews", n_top)
        show(vbar(g, "_ten", "n_reviews", f"Top {n_top} sản phẩm có nhiều lượt đánh giá cao nhất", plat, text=",.0f"),
             plat, 400)
    with safe("Điểm đánh giá theo sản phẩm"):
        g = p.groupby(NAME, as_index=False).agg(n=("n_reviews", "sum"), diem=("rating_final", "mean"))
        g = g.dropna(subset=["diem"]).nlargest(10, "n").sort_values("diem", ascending=False)   # Top 10 theo số đánh giá
        g["_ten"] = uniq_labels(g[NAME])
        show(hbar(g, "diem", "Điểm đánh giá trung bình theo sản phẩm", plat, text=".2f"), plat, 420)


# ----------------------------------------------------------------------------
# 7. TRANG 4 – LIỆT KÊ MIN / MAX
# ----------------------------------------------------------------------------
def page_minmax(p: pd.DataFrame, r: pd.DataFrame, plat: str) -> None:
    banner(f"DASHBOARD {plat.upper()} COCOON", plat)
    sold = SOLD[plat]
    p = attach_review_stats(p, r)

    def row(label, col, fmt, d):
        if col not in d or d[col].dropna().empty:
            return None
        hi, lo = d[col].idxmax(), d[col].idxmin()
        return {"Chỉ tiêu": label,
                "Max": f"{fmt(d.at[hi, col])} · {short(d.at[hi, NAME], 40)}",
                "Min": f"{fmt(d.at[lo, col])} · {short(d.at[lo, NAME], 40)}"}

    spec = [("Giá bán", PRICE, fint), ("Giá gốc", ORIG, fint), ("% Giảm giá", DISC, fpct),
            ("Lượt bán", sold, fint), ("Doanh thu 30 ngày", REV, fvnd), ("Điểm đánh giá TB", RATING, fdec),
            ("Số lượt đánh giá", "n_reviews", fint)]
    a, b = st.columns(2)
    with a, safe("Chỉ tiêu sản phẩm"):
        st.markdown("**Chỉ tiêu sản phẩm**")
        show_df(pd.DataFrame([x for x in (row(*s, p) for s in spec) if x]))
    with b, safe("Chỉ tiêu đánh giá"):
        st.markdown("**Chỉ tiêu đánh giá**")
        rr = []
        if not r.empty and R_STAR in r:
            rr.append({"Chỉ tiêu": "Số sao", "Max": fint(r[R_STAR].max()), "Min": fint(r[R_STAR].min())})
        if not r.empty and R_DATE in r and r[R_DATE].notna().any():
            rr.append({"Chỉ tiêu": "Ngày review", "Max": r[R_DATE].max().strftime("%d/%m/%Y"),
                       "Min": r[R_DATE].min().strftime("%d/%m/%Y")})
        x = row("Điểm đánh giá TB theo SP", "rating_final", fdec, p)
        if x:
            rr.append(x)
        show_df(pd.DataFrame(rr))


# ----------------------------------------------------------------------------
# 8. ĐỌC DỮ LIỆU TỰ ĐỘNG (chỉ dùng khi không truyền DataFrame)
# ----------------------------------------------------------------------------
def _read_any(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path)
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def load_datasets(folder: str = "dataset") -> dict:
    base = Path(__file__).resolve().parent / folder
    files = [f for ext in ("*.csv", "*.xlsx") for f in base.rglob(ext)]
    out = {}
    for plat in ("shopee", "hasaki"):
        for kind in ("products", "reviews"):
            hit = next((f for f in files if plat in f.stem.lower()
                        and (("review" in f.stem.lower()) == (kind == "reviews"))), None)
            out[f"{kind}_{plat}"] = _read_any(hit) if hit else None
    return out


# ----------------------------------------------------------------------------
# 9. HÀM CHÍNH
# ----------------------------------------------------------------------------
def render_powerbi_dashboard(products_shopee=None, reviews_shopee=None,
                             products_hasaki=None, reviews_hasaki=None) -> None:
    if products_shopee is None and products_hasaki is None:
        data = load_datasets()
        products_shopee, reviews_shopee = data["products_shopee"], data["reviews_shopee"]
        products_hasaki, reviews_hasaki = data["products_hasaki"], data["reviews_hasaki"]

    st.subheader("Dashboard phân tích Cocoon (Shopee & Hasaki)")
    plat_tabs = st.tabs(["🟠 Shopee", "🟢 Hasaki"])
    inputs = {"Shopee": (products_shopee, reviews_shopee), "Hasaki": (products_hasaki, reviews_hasaki)}

    for tab, plat in zip(plat_tabs, ("Shopee", "Hasaki")):
        with tab:
            p_raw, r_raw = inputs[plat]
            if p_raw is None or len(p_raw) == 0:
                st.warning(f"Không có dữ liệu sản phẩm {plat}.")
                continue
            p, r = prep_products(p_raw, plat), prep_reviews(r_raw)
            pages = st.tabs(["Tổng quan", "Phân tích sản phẩm", "Phân tích đánh giá", "Liệt kê Min – Max"])
            with pages[0]:
                page_overview(p, plat)
            with pages[1]:
                page_products(p, plat)
            with pages[2]:
                page_reviews(p, r, plat)
            with pages[3]:
                page_minmax(p, r, plat)


if __name__ == "__main__":      # chạy thử riêng: streamlit run powerbi_dashboard.py
    st.set_page_config(page_title="Cocoon Dashboard", layout="wide")
    render_powerbi_dashboard()
