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

# --- TỰ ĐỘNG DÒ TÌM FILE (Chuẩn cho cả Local và Streamlit Cloud) ---
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

PRODUCTS_FILE = _find_file("products_final.xlsx")
REVIEWS_FILE = _find_file("Reviews_final.xlsx")

DELETED_FILE = HERE / "dataset" / "deleted_rows.json"
if not DELETED_FILE.parent.exists():
    DELETED_FILE = HERE / "deleted_rows.json"

MODEL_DIR = HERE / "dataset" / "model_outputs"

UNKNOWN_CAT = "Chưa phân loại"

# ---------------------------------------------------------------- phân loại
def _norm(s: str) -> str:
    if pd.isna(s):
        return ""
    return unicodedata.normalize("NFC", str(s)).lower()

def classify_category(name: str) -> str:
    n = _norm(name)
    if not n or n.startswith("hasaki #"): 
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
    if not n or n.startswith("hasaki #"): 
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
    return tuple(f.stat().st_mtime if f.exists() else 0 for f in (PRODUCTS_FILE, REVIEWS_FILE))

def _read_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")
    return pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)

def load_base() -> pd.DataFrame:
    """Gộp review Shopee + Hasaki về một bảng chuẩn."""
    try:
        # 1. SHOPEE
        sp = _read_table(PRODUCTS_FILE).reset_index(drop=True)
        sp.columns = [str(c).strip() for c in sp.columns]
        
        for col in sp.columns:
            if "lượt bán" in col.lower():
                sp = sp.rename(columns={col: "Lượt bán"})
                break

        # Đọc review Hasaki lấy ngày lớn nhất
        hs_raw = _read_table(REVIEWS_FILE)
        default_date = pd.to_datetime(hs_raw["Ngày review"], errors="coerce").max()
        if pd.isna(default_date):
            default_date = pd.Timestamp.now().normalize()

        shopee = pd.DataFrame({
            "rid": [f"SP-{i:05d}" for i in range(len(sp))],
            "Nguồn": "Shopee",
            "Mã SP": sp["Mã SP"] if "Mã SP" in sp.columns else sp.index.astype(str),
            "Tên sản phẩm": sp["Tên sản phẩm"] if "Tên sản phẩm" in sp.columns else "Sản phẩm Shopee",
            "Giá bán": sp["Giá bán"] if "Giá bán" in sp.columns else pd.NA,
            "Lượt bán": sp["Lượt bán"] if "Lượt bán" in sp.columns else pd.NA,
            "Doanh thu 30 ngày": sp["Doanh thu 30 ngày"] if "Doanh thu 30 ngày" in sp.columns else pd.NA,
            "Số sao": 5,
            "Nội dung review": "Không có nội dung review (Từ file sản phẩm)",
            "Ngày review": default_date,
            "Đã mua hàng": "Có",
        })

        # 2. HASAKI
        hs = hs_raw.reset_index(drop=True)
        hs.columns = [str(c).strip() for c in hs.columns]
        
        hasaki = pd.DataFrame({
            "rid": hs["Review_ID"].astype(str) if "Review_ID" in hs.columns else [f"HS-{i:05d}" for i in range(len(hs))],
            "Nguồn": "Hasaki",
            "Mã SP": hs["Mã SP"] if "Mã SP" in hs.columns else pd.NA,
            "Số sao": hs["Số sao (review)"] if "Số sao (review)" in hs.columns else 5,
            "Nội dung review": hs["Nội dung review"] if "Nội dung review" in hs.columns else "",
            "Ngày review": hs["Ngày review"] if "Ngày review" in hs.columns else default_date,
            "Đã mua hàng": hs["Đã mua hàng"] if "Đã mua hàng" in hs.columns else "Có",
        })
        
        hp = sp.drop_duplicates("Mã SP") if "Mã SP" in sp.columns else sp
        prod_cols = ["Tên sản phẩm", "Giá bán", "Lượt bán", "Doanh thu 30 ngày"]
        keep = [c for c in ["Mã SP"] + prod_cols if c in hp.columns]
        
        if "Mã SP" in hasaki.columns and "Mã SP" in hp.columns:
            hasaki = hasaki.merge(hp[keep], on="Mã SP", how="left")
        
        for c in prod_cols:
            if c not in hasaki.columns:
                hasaki[c] = pd.NA
                
        hasaki["Tên sản phẩm"] = hasaki["Tên sản phẩm"].fillna("Hasaki #" + hasaki["Mã SP"].astype(str))

        # 3. GỘP BẢNG
        df = pd.concat([shopee, hasaki[shopee.columns]], ignore_index=True)
        
        df["Ngày review"] = pd.to_datetime(df["Ngày review"], errors="coerce").dt.normalize()
        df["Tháng"] = df["Ngày review"].dt.to_period("M").dt.to_timestamp()
        df["Nội dung review"] = df["Nội dung review"].fillna("").astype(str)
        
        for c in ("Giá bán", "Lượt bán", "Doanh thu 30 ngày", "Số sao"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
        df["Hạng mục"] = df["Tên sản phẩm"].map(classify_category)
        df["Dòng sản phẩm"] = df["Tên sản phẩm"].map(classify_line)
        df["Cảm xúc"] = df["Số sao"].apply(sentiment_from_star)
        
        return df
    except Exception as e:
        # Bắt lỗi khẩn cấp để không làm crash Streamlit app
        print(f"Lỗi load_base: {e}")
        return pd.DataFrame(columns=["rid", "Nguồn", "Mã SP", "Tên sản phẩm", "Giá bán", "Lượt bán", "Doanh thu 30 ngày", "Số sao", "Nội dung review", "Ngày review", "Đã mua hàng", "Tháng", "Hạng mục", "Dòng sản phẩm", "Cảm xúc"])

# ---------------------------------------------------------------- xóa mềm
def load_deleted() -> list[dict]:
    if DELETED_FILE.exists():
        try:
            data = json.loads(DELETED_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [d for d in data if isinstance(d, dict) and "rid" in d]
        except Exception:
            return []
    return []

def delete_rows(rids: list[str], by: str) -> int:
    log = load_deleted()
    existing = {d["rid"] for d in log if isinstance(d, dict) and "rid" in d}
    now = datetime.now().isoformat(timespec="seconds")
    new = [{"rid": r, "by": by, "at": now} for r in rids if r not in existing]
    DELETED_FILE.write_text(json.dumps(log + new, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(new)

def restore_all() -> None:
    if DELETED_FILE.exists(): 
        DELETED_FILE.unlink()

def apply_deletions(df: pd.DataFrame) -> pd.DataFrame:
    # Bảo vệ chống AttributeError nếu df là None hoặc không phải DataFrame
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    
    if "rid" not in df.columns:
        return df

    log = load_deleted()
    gone = {d["rid"] for d in log if isinstance(d, dict) and "rid" in d}
    return df[~df["rid"].isin(gone)] if gone else df

# ---------------------------------------------------------------- tổng hợp
def product_table(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty: 
        return pd.DataFrame()
    g = df.groupby(["Nguồn", "Mã SP", "Tên sản phẩm", "Hạng mục", "Dòng sản phẩm"], observed=True, dropna=False)
    out = g.agg(**{
        "Giá bán": ("Giá bán", "first"),
        "Lượt bán": ("Lượt bán", "first"),
        "Doanh thu 30 ngày": ("Doanh thu 30 ngày", "first"),
        "Số review": ("rid", "size"),
        "Sao TB (review)": ("Số sao", "mean"),
        "Số review 1★": ("Số sao", lambda s: int((s == 1).sum())),
        "Số review 5★": ("Số sao", lambda s: int((s == 5).sum())),
    }).reset_index()
    out["Sao TB (review)"] = out["Sao TB (review)"].round(2)
    return out.sort_values("Số review", ascending=False)

def monthly_table(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    if "Tháng" not in df.columns:
        return pd.DataFrame()
    d = df.dropna(subset=["Tháng"])
    return (d.groupby(["Tháng", "Nguồn"]).size().rename("Số review").reset_index())

# ---------------------------------------------------------------- xuất file
_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
def _clean_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    df = df.copy()
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].map(lambda v: _ILLEGAL.sub("", v) if isinstance(v, str) else v)
    return df

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    if df is None or not isinstance(df, pd.DataFrame):
        return b""
    return df.to_csv(index=False).encode("utf-8-sig")

def to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, frame in sheets.items():
            if isinstance(frame, pd.DataFrame):
                _clean_for_excel(frame).to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()
