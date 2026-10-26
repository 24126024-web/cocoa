"""Nạp, phân loại, lọc và xuất dữ liệu Cocoon (Shopee + Hasaki)."""
from __future__ import annotations

import io
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "dataset"
if not DATA_DIR.exists():
    DATA_DIR = HERE / "dataset"

SHOPEE_FILE = DATA_DIR / "cocoon_shopee_clean.xlsx"
HASAKI_FILE = DATA_DIR / "Reviews_final.xlsx"
# Bảng sản phẩm Hasaki (từ products_final.xlsx): "Mã SP", "Tên sản phẩm", Giá bán, Lượt bán, Doanh thu 30 ngày
HASAKI_PRODUCTS_FILE = next(
    (f for f in (DATA_DIR / "hasaki_products.xlsx", DATA_DIR / "hasaki_products.csv") if f.exists()),
    DATA_DIR / "hasaki_products.xlsx",
)
DELETED_FILE = DATA_DIR / "deleted_rows.json"
MODEL_DIR = DATA_DIR / "model_outputs"

UNKNOWN_CAT = "Chưa phân loại"



def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", str(s)).lower()


def classify_category(name: str) -> str:
    """Hạng mục: Chăm sóc da mặt / tóc / cơ thể / môi."""
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
    """Dòng sản phẩm theo thành phần chủ đạo (dùng cho biểu đồ tròn)."""
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



def data_signature() -> tuple:
    """Thời điểm sửa file dữ liệu — dùng làm khóa cache để app tự nạp lại khi file đổi."""
    return tuple(f.stat().st_mtime if f.exists() else 0
                 for f in (SHOPEE_FILE, HASAKI_FILE, HASAKI_PRODUCTS_FILE))


def _read_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)


def load_base() -> pd.DataFrame:
    """Gộp review Shopee + Hasaki về một bảng chuẩn (chưa trừ dòng đã xóa)."""
    # --- Shopee
    sp = _read_table(SHOPEE_FILE).reset_index(drop=True)
    shopee = pd.DataFrame({
        "rid": [f"SP-{i:05d}" for i in range(len(sp))],
        "Nguồn": "Shopee",
        "Mã SP": sp["Mã SP"],
        "Tên sản phẩm": sp["Tên sản phẩm"],
        "Giá bán": sp["Giá bán"],
        "Lượt bán": sp["Lượt bán"],
        "Doanh thu 30 ngày": sp["Doanh thu 30 ngày"],
        "Số sao": sp["Số sao (review)"],
        "Nội dung review": sp["Nội dung review"],
        "Ngày review": sp["Ngày review"],
        "Đã mua hàng": sp["Đã mua hàng"],
    })

    #  Hasaki
    hs = _read_table(HASAKI_FILE).reset_index(drop=True)
    hasaki = pd.DataFrame({
        "rid": hs["Review_ID"].astype(str),
        "Nguồn": "Hasaki",
        "Mã SP": hs["Mã SP"],
        "Số sao": hs["Số sao (review)"],
        "Nội dung review": hs["Nội dung review"],
        "Ngày review": hs["Ngày review"],
        "Đã mua hàng": hs["Đã mua hàng"],
    })
    prod_cols = ["Tên sản phẩm", "Giá bán", "Lượt bán", "Doanh thu 30 ngày"]
    if HASAKI_PRODUCTS_FILE.exists():
        hp = _read_table(HASAKI_PRODUCTS_FILE).drop_duplicates("Mã SP")
        hp = hp.rename(columns={c: "Lượt bán" for c in hp.columns if c.startswith("Lượt bán")})
        keep = ["Mã SP"] + [c for c in prod_cols if c in hp.columns]
        hasaki = hasaki.merge(hp[keep], on="Mã SP", how="left")
    for c in prod_cols:
        if c not in hasaki.columns:
            hasaki[c] = pd.NA
    hasaki["Tên sản phẩm"] = hasaki["Tên sản phẩm"].fillna(
        "Hasaki #" + hasaki["Mã SP"].astype(str))

    df = pd.concat([shopee, hasaki[shopee.columns]], ignore_index=True)
    df["Ngày review"] = pd.to_datetime(df["Ngày review"], errors="coerce")
    df["Tháng"] = df["Ngày review"].dt.to_period("M").dt.to_timestamp()
    df["Nội dung review"] = df["Nội dung review"].fillna("").astype(str)
    for c in ("Giá bán", "Lượt bán", "Doanh thu 30 ngày"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Hạng mục"] = df["Tên sản phẩm"].map(classify_category)
    df["Dòng sản phẩm"] = df["Tên sản phẩm"].map(classify_line)
    df["Cảm xúc"] = df["Số sao"].map(sentiment_from_star)
    return df



def load_deleted() -> list[dict]:
    if DELETED_FILE.exists():
        try:
            return json.loads(DELETED_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def delete_rows(rids: list[str], by: str) -> int:
    """Đánh dấu xóa (không sửa file gốc). Trả về số dòng mới bị xóa."""
    log = load_deleted()
    existing = {d["rid"] for d in log}
    now = datetime.now().isoformat(timespec="seconds")
    new = [{"rid": r, "by": by, "at": now} for r in rids if r not in existing]
    DELETED_FILE.write_text(
        json.dumps(log + new, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(new)


def restore_all() -> None:
    if DELETED_FILE.exists():
        DELETED_FILE.unlink()


def apply_deletions(df: pd.DataFrame) -> pd.DataFrame:
    gone = {d["rid"] for d in load_deleted()}
    return df[~df["rid"].isin(gone)] if gone else df



def product_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    g = df.groupby(["Nguồn", "Mã SP", "Tên sản phẩm", "Hạng mục", "Dòng sản phẩm"],
                   observed=True, dropna=False)
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
    d = df.dropna(subset=["Tháng"])
    return (d.groupby(["Tháng", "Nguồn"]).size().rename("Số review").reset_index())



_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _clean_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].map(lambda v: _ILLEGAL.sub("", v) if isinstance(v, str) else v)
    return df


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")  


def to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, frame in sheets.items():
            _clean_for_excel(frame).to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()
