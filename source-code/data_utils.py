"""Nạp, phân loại, lọc và xuất dữ liệu Cocoon."""
from __future__ import annotations

import io
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent

# --- TỰ ĐỘNG DÒ TÌM FILE (Dành cho cả máy tính và Streamlit Cloud) ---
def _find_file(filename: str) -> Path:
    """Tìm file ở thư mục hiện tại, thư mục cha, hoặc thư mục dataset."""
    search_paths = [
        HERE / filename,
        HERE / "dataset" / filename,
        HERE.parent / filename,
        HERE.parent / "dataset" / filename,
    ]
    for p in search_paths:
        if p.exists():
            return p
    # Nếu không thấy, mặc định trả về đường dẫn trong thư mục dataset để báo lỗi rõ ràng
    return HERE / "dataset" / filename

PRODUCTS_FILE = _find_file("products_final.xlsx")
REVIEWS_FILE = _find_file("Reviews_final.xlsx")

# Thư mục lưu trữ trạng thái xóa
DELETED_FILE = HERE / "dataset" / "deleted_rows.json"
if not DELETED_FILE.parent.exists():
    DELETED_FILE = HERE / "deleted_rows.json"
    
MODEL_DIR = HERE / "dataset" / "model_outputs"

UNKNOWN_CAT = "Chưa phân loại"


# ---------------------------------------------------------------- phân loại
def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", str(s)).lower()


def classify_category(name: str) -> str:
    n = _norm(name)
    if n.startswith("hasaki #"):
        return UNKNOWN_CAT
    if "môi" in n or "son dưỡng" in n:
        return "Chăm sóc môi"
    if any(k in n for k in ("tóc", "dầu gội", "dầu xả", "bưởi")):
        return "Chăm sóc tóc"
    if any(k in n for k in ("body", "gel tắm", "sữa tắm", "toàn thân", "cơ thể", "lưng", "thốt nốt")):
        return "Chăm sóc cơ thể"
    return "Chăm sóc da mặt"


def classify_line(name: str) -> str:
    n = _norm(name).replace("nước hoa hồng", "")
    if n.startswith("hasaki #"):
        return UNKNOWN_CAT
    for key, label in [
        ("bí đao", "Bí đao"), ("cà phê", "Cà phê"), ("bưởi", "Bưởi"),
        ("nghệ", "Nghệ Hưng Yên"), ("sen", "Sen Hậu Giang"),
        ("hoa hồng", "Hoa hồng"), ("dầu dừa", "Dầu dừa"),
        ("sa-chi", "Sa-chi"), ("thốt nốt", "Thốt nốt"),
    ]:
        if key in n:
            return label
    return "Khác"


def sentiment_from_star(s: int) -> str:
    return "Tích cực" if s >= 4 else ("Trung tính" if s == 3 else "Tiêu cực")


# ---------------------------------------------------------------- nạp dữ liệu
def data_signature() -> tuple:
    return tuple(f.stat().st_mtime if f.exists() else 0
                 for f in (PRODUCTS_FILE, REVIEWS_FILE))


def _read_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Lỗi: Không tìm thấy file tại {path}. Bạn hãy kiểm tra lại trên GitHub/Streamlit Cloud xem file đã được upload đúng thư mục chưa.")
    return pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)
