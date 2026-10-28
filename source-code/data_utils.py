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


def _find_file(filename: str) -> Path:
    search_paths = [
        HERE / filename,
        HERE / "dataset" / filename,
        HERE.parent / filename,
        HERE.parent / "dataset" / filename,
        HERE.parent / "source-code" / "dataset" / filename,
        Path.cwd() / filename,
        Path.cwd() / "dataset" / filename,
    ]
    for p in search_paths:
        if p.exists():
            return p
    return HERE / filename


HASAKI_PROD_FILE = _find_file("products_hasaki.xlsx")
HASAKI_REV_FILE = _find_file("Reviews_hasaki.xlsx")
SHOPEE_PROD_FILE = _find_file("cocoon_shopee_products_.xlsx")
SHOPEE_REV_FILE = _find_file("cocoon_shopee_reviews__.xlsx")

DELETED_FILE = HERE / "dataset" / "deleted_rows.json"
if not DELETED_FILE.parent.exists():
    DELETED_FILE = HERE / "deleted_rows.json"

MODEL_DIR = HERE / "dataset" / "model_outputs"


def _norm(s: str) -> str:
    if pd.isna(s):
        return ""
    return unicodedata.normalize("NFC", str(s)).lower()


def classify_category(name: str) -> str:
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


def data_signature() -> tuple:
    return tuple(
        f.stat().st_mtime if f.exists() else 0 
        for f in (HASAKI_PROD_FILE, HASAKI_REV_FILE, SHOPEE_PROD_FILE, SHOPEE_REV_FILE)
    )


def _read_table(path: Path, sheet_name: str | int = 0) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def load_base() -> pd.DataFrame:
    try:
        hk_p = _read_table(HASAKI_PROD_FILE)
        hk_r = _read_table(HASAKI_REV_FILE)

        sheet_sp = "Products" if SHOPEE_PROD_FILE.exists() and "Products" in pd.ExcelFile(SHOPEE_PROD_FILE).sheet_names else 0
        sp_p = _read_table(SHOPEE_PROD_FILE, sheet_name=sheet_sp)
        sp_r = _read_table(SHOPEE_REV_FILE)

        for d in (hk_p, hk_r, sp_p, sp_r):
            if not d.empty:
                d.columns = [str(c).strip() for c in d.columns]
                if "Mã SP" in d.columns:
                    d["Mã SP"] = d["Mã SP"].astype(str).str.strip()

        if "Lượt bán (30 ngày)" in sp_p.columns and "Lượt bán" not in sp_p.columns:
            sp_p = sp_p.rename(columns={"Lượt bán (30 ngày)": "Lượt bán"})
        if "Lượt bán (30 ngày)" in hk_p.columns and "Lượt bán" not in hk_p.columns:
            hk_p = hk_p.rename(columns={"Lượt bán (30 ngày)": "Lượt bán"})

        # Nạp Shopee
        sp_merged = sp_r.merge(sp_p.drop_duplicates("Mã SP"), on="Mã SP", how="left", suffixes=("", "_prod"))
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

        # Nạp Hasaki (Lấy hk_p 84 sản phẩm làm gốc)
        if not hk_p.empty:
            if not hk_r.empty and "Mã SP" in hk_r.columns:
                hk_merged = hk_p.merge(hk_r, on="Mã SP", how="left", suffixes=("", "_rev"))
            else:
                hk_merged = hk_p.copy()

            hasaki_df = pd.DataFrame({
                "rid": [f"HS-{i:06d}" for i in range(len(hk_merged))],
                "Nguồn": "Hasaki",
                "Mã SP": hk_merged["Mã SP"],
                "Tên sản phẩm": hk_merged["Tên sản phẩm"].fillna("Sản phẩm Hasaki #" + hk_merged["Mã SP"].astype(str)),
                "Giá bán": hk_merged["Giá bán"] if "Giá bán" in hk_merged.columns else pd.NA,
                "Lượt bán": hk_merged["Lượt bán"] if "Lượt bán" in hk_merged.columns else pd.NA,
                "Doanh thu 30 ngày": hk_merged["Doanh thu 30 ngày"] if "Doanh thu 30 ngày" in hk_merged.columns else pd.NA,
                "Số sao": hk_merged["Số sao (review)"] if "Số sao (review)" in hk_merged.columns else (hk_merged["Số sao"] if "Số sao" in hk_merged.columns else 5),
                "Nội dung review": hk_merged["Nội dung review"] if "Nội dung review" in hk_merged.columns else "Chưa có review",
                "Ngày review": hk_merged["Ngày review"] if "Ngày review" in hk_merged.columns else pd.Timestamp.now(),
                "Đã mua hàng": hk_merged["Đã mua hàng"] if "Đã mua hàng" in hk_merged.columns else "Có",
            })
        else:
            hasaki_df = pd.DataFrame()

        df = pd.concat([shopee_df, hasaki_df], ignore_index=True)

        df["Ngày review"] = pd.to_datetime(df["Ngày review"], errors="coerce").fillna(pd.Timestamp.now()).dt.normalize()
        df["Tháng"] = df["Ngày review"].dt.to_period("M").dt.to_timestamp()
        df["Nội dung review"] = df["Nội dung review"].fillna("").astype(str)
        df["Tên sản phẩm"] = df["Tên sản phẩm"].fillna("Sản phẩm Cocoon").astype(str)

        for c in ("Giá bán", "Lượt bán", "Doanh thu 30 ngày", "Số sao"):
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df["Hạng mục"] = df["Tên sản phẩm"].map(classify_category)
        df["Dòng sản phẩm"] = df["Tên sản phẩm"].map(classify_line)
        df["Cảm xúc"] = df["Số sao"].apply(sentiment_from_star)

        return df

    except Exception as e:
        print(f"Lỗi load_base: {e}")
        return pd.DataFrame()


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
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    if "rid" not in df.columns:
        return df

    log = log = load_deleted()
    gone = {d["rid"] for d in log if isinstance(d, dict) and "rid" in d}
    return df[~df["rid"].isin(gone)] if gone else df


def product_table(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    
    df = df.copy()
    if "Doanh thu 30 ngày" in df.columns:
        df["Doanh thu 30 ngày"] = pd.to_numeric(df["Doanh thu 30 ngày"], errors="coerce")

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
