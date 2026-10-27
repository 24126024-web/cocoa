"""Nạp, phân loại, lọc và xuất dữ liệu Cocoon (Shopee & Hasaki)."""
from __future__ import annotations

import io
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent

# --- TỰ ĐỘNG DÒ TÌM FILE (Local & Streamlit Cloud) ---
def _find_file(filename: str) -> Path:
    search_paths = [
        HERE / filename,
        HERE / "dataset" / filename,
        HERE.parent / filename,
        HERE.parent / "dataset" / filename,
        HERE.parent / "source-code" / "dataset" / filename,
    ]
    for p in search_paths:
        if p.exists():
            return p
    return HERE / "dataset" / filename

# 4 FILE DỮ LIỆU MỚI
HASAKI_PROD_FILE = _find_file("products_hasaki.xlsx")
HASAKI_REV_FILE = _find_file("Reviews_hasaki.xlsx")
SHOPEE_PROD_FILE = _find_file("cocoon_shopee_products_.xlsx")
SHOPEE_REV_FILE = _find_file("cocoon_shopee_reviews__.xlsx")

DELETED_FILE = HERE / "dataset" / "deleted_rows.json"
if not DELETED_FILE.parent.exists():
    DELETED_FILE = HERE / "deleted_rows.json"

MODEL_DIR = HERE / "dataset" / "model_outputs"


# ---------------------------------------------------------------- phân loại
def _norm(s: str) -> str:
    if pd.isna(s):
        return ""
    return unicodedata.normalize("NFC", str(s)).lower()


def classify_category(name: str) -> str:
    """Phân loại hạng mục sản phẩm - Không trả về 'Chưa phân loại'."""
    n = _norm(name)
    if not n:
        return "Chăm sóc da mặt"
    
    if any(k in n for k in ("môi", "son dưỡng")):
        return "Chăm sóc môi"
    if any(k in n for k in ("tóc", "dầu gội", "dầu xả", "bưởi", "huyết thanh", "sa-chi", "sachi")):
        return "Chăm sóc tóc"
    if any(k in n for k in ("body", "gel tắm", "sữa tắm", "toàn thân", "cơ thể", "lưng", "thốt nốt", "tẩy tế bào chết body")):
        return "Chăm sóc cơ thể"
    
    return "Chăm sóc da mặt"


def classify_line(name: str) -> str:
    """Phân loại dòng sản phẩm - Mặc định 'Khác' thay vì 'Chưa phân loại'."""
    n = _norm(name).replace("nước hoa hồng", "")
    if not n:
        return "Khác"
        
    for key, label in [
        ("bí đao", "Bí đao"), ("cà phê", "Cà phê"), ("bưởi", "Bưởi"),
        ("nghệ", "Nghệ Hưng Yên"), ("sen", "Sen Hậu Giang"),
        ("hoa hồng", "Hoa hồng"), ("dầu dừa", "Dầu dừa"),
        ("sa-chi", "Sa-chi"), ("thốt nốt", "Thốt nốt"),
    ]:
        if key in n:
            return label
    return "Khác"


def sentiment_from_star(s) -> str:
    if pd.isna(s):
        return "Chưa có đánh giá"
    try:
        val = float(s)
        return "Tích cực" if val >= 4 else ("Trung tính" if val == 3 else "Tiêu cực")
    except (ValueError, TypeError):
        return "Chưa có đánh giá"


# ---------------------------------------------------------------- nạp dữ liệu
def data_signature() -> tuple:
    return tuple(
        f.stat().st_mtime if f.exists() else 0 
        for f in (HASAKI_PROD_FILE, HASAKI_REV_FILE, SHOPEE_PROD_FILE, SHOPEE_REV_FILE)
    )


def _read_table(path: Path, sheet_name: str | int = 0) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path, sheet_name=sheet_name)


def load_base() -> pd.DataFrame:
    """Nạp và kết hợp dữ liệu 4 file mới của Shopee và Hasaki."""
    try:
        # 1. ĐỌC CÁC BẢNG SẢN PHẨM & REVIEW HASAKI
        hk_p = _read_table(HASAKI_PROD_FILE)
        hk_p.columns = [str(c).strip() for c in hk_p.columns]
        
        hk_r = _read_table(HASAKI_REV_FILE)
        hk_r.columns = [str(c).strip() for c in hk_r.columns]

        # 2. ĐỌC CÁC BẢNG SẢN PHẨM & REVIEW SHOPEE
        sheet_sp = "Products" if "Products" in pd.ExcelFile(SHOPEE_PROD_FILE).sheet_names else 0
        sp_p = _read_table(SHOPEE_PROD_FILE, sheet_name=sheet_sp)
        sp_p.columns = [str(c).strip() for c in sp_p.columns]
        
        sp_r = _read_table(SHOPEE_REV_FILE)
        sp_r.columns = [str(c).strip() for c in sp_r.columns]

        # Đổi tên cột lượt bán đồng nhất
        if "Lượt bán (30 ngày)" in sp_p.columns and "Lượt bán" not in sp_p.columns:
            sp_p = sp_p.rename(columns={"Lượt bán (30 ngày)": "Lượt bán"})
        if "Lượt bán (30 ngày)" in hk_p.columns and "Lượt bán" not in hk_p.columns:
            hk_p = hk_p.rename(columns={"Lượt bán (30 ngày)": "Lượt bán"})

        # --- XỬ LÝ SHOPEE ---
        sp_merged = sp_r.merge(
            sp_p[["Mã SP", "Tên sản phẩm", "Giá bán", "Lượt bán", "Doanh thu 30 ngày"]].drop_duplicates("Mã SP"),
            on="Mã SP",
            how="left"
        )
        
        shopee_df = pd.DataFrame({
            "rid": [f"SP-{i:06d}" for i in range(len(sp_merged))],
            "Nguồn": "Shopee",
            "Mã SP": sp_merged["Mã SP"],
            "Tên sản phẩm": sp_merged["Tên sản phẩm"].fillna("Sản phẩm Shopee #" + sp_merged["Mã SP"].astype(str)),
            "Giá bán": sp_merged["Giá bán"] if "Giá bán" in sp_merged.columns else pd.NA,
            "Lượt bán": sp_merged["Lượt bán"] if "Lượt bán" in sp_merged.columns else pd.NA,
            "Doanh thu 30 ngày": sp_merged["Doanh thu 30 ngày"] if "Doanh thu 30 ngày" in sp_merged.columns else pd.NA,
            "Số sao": sp_merged["Số sao (review)"] if "Số sao (review)" in sp_merged.columns else 5,
            "Nội dung review": sp_merged["Nội dung review"] if "Nội dung review" in sp_merged.columns else "",
            "Ngày review": sp_merged["Ngày review"] if "Ngày review" in sp_merged.columns else pd.Timestamp.now(),
            "Đã mua hàng": sp_merged["Đã mua hàng"] if "Đã mua hàng" in sp_merged.columns else "Có",
        })

        # --- XỬ LÝ HASAKI ---
        all_p = pd.concat([
            hk_p[["Mã SP", "Tên sản phẩm", "Giá bán", "Lượt bán", "Doanh thu 30 ngày"]],
            sp_p[["Mã SP", "Tên sản phẩm", "Giá bán", "Lượt bán", "Doanh thu 30 ngày"]]
        ], ignore_index=True).drop_duplicates("Mã SP")

        hk_merged = hk_r.merge(all_p, on="Mã SP", how="left")

        hasaki_df = pd.DataFrame({
            "rid": [f"HS-{i:06d}" for i in range(len(hk_merged))],
            "Nguồn": "Hasaki",
            "Mã SP": hk_merged["Mã SP"],
            "Tên sản phẩm": hk_merged["Tên sản phẩm"].fillna("Sản phẩm Hasaki #" + hk_merged["Mã SP"].astype(str)),
            "Giá bán": hk_merged["Giá bán"] if "Giá bán" in hk_merged.columns else pd.NA,
            "Lượt bán": hk_merged["Lượt bán"] if "Lượt bán" in hk_merged.columns else pd.NA,
            "Doanh thu 30 ngày": hk_merged["Doanh thu 30 ngày"] if "Doanh thu 30 ngày" in hk_merged.columns else pd.NA,
            "Số sao": hk_merged["Số sao (review)"] if "Số sao (review)" in hk_merged.columns else 5,
            "Nội dung review": hk_merged["Nội dung review"] if "Nội dung review" in hk_merged.columns else "",
            "Ngày review": hk_merged["Ngày review"] if "Ngày review" in hk_merged.columns else pd.Timestamp.now(),
            "Đã mua hàng": hk_merged["Đã mua hàng"] if "Đã mua hàng" in hk_merged.columns else "Có",
        })

        # --- GỘP CẢ
