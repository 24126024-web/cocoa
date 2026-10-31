"""Nạp, phân loại, lọc và xuất dữ liệu Cocoon (Shopee & Hasaki)."""
from __future__ import annotations

import io
import json
import re
import sqlite3
import unicodedata
import zipfile
from contextlib import closing
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

# SQLite (DBMS)
_DB_DIR = HERE / "dataset"
DB_PATH = (_DB_DIR if _DB_DIR.exists() else HERE) / "cocoon.db"
_DB_TABLES = ("hasaki_products", "hasaki_reviews", "shopee_products", "shopee_reviews")


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
        (str(f), f.stat().st_mtime, f.stat().st_size) if f.exists() else (str(f), 0, 0)
        for f in (HASAKI_PROD_FILE, HASAKI_REV_FILE, SHOPEE_PROD_FILE, SHOPEE_REV_FILE, DB_PATH)
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


def _clean_raw(d: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hoá tên cột và Mã SP (bỏ khoảng trắng, bỏ đuôi '.0' do Excel)."""
    if d is None or d.empty:
        return pd.DataFrame()
    d = d.copy()
    d.columns = [str(c).strip() for c in d.columns]
    if "Mã SP" in d.columns:
        d["Mã SP"] = d["Mã SP"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        d = d[~d["Mã SP"].isin(["", "nan", "None", "<NA>"])]
    return d.reset_index(drop=True)


def _load_raw_excel():
    hk_p = _clean_raw(_read_table(HASAKI_PROD_FILE))
    hk_r = _clean_raw(_read_table(HASAKI_REV_FILE))

    sheet_sp: str | int = 0
    if SHOPEE_PROD_FILE.exists():
        try:
            if "Products" in pd.ExcelFile(SHOPEE_PROD_FILE).sheet_names:
                sheet_sp = "Products"
        except Exception:
            sheet_sp = 0
    sp_p = _clean_raw(_read_table(SHOPEE_PROD_FILE, sheet_name=sheet_sp))
    sp_r = _clean_raw(_read_table(SHOPEE_REV_FILE))
    return hk_p, hk_r, sp_p, sp_r



# SQLite

def _db_read(table: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        with closing(sqlite3.connect(DB_PATH)) as con:
            return pd.read_sql(f'SELECT * FROM "{table}"', con)
    except Exception:
        return pd.DataFrame()


def _db_has(table: str) -> bool:
    if not DB_PATH.exists():
        return False
    try:
        with closing(sqlite3.connect(DB_PATH)) as con:
            row = con.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
        return row is not None
    except Exception:
        return False



# MongoDB Atlas (đọc cấu hình từ st.secrets["mongo"])

_MONGO: dict = {}
_MONGO_COLS = {
    "hasaki_products": "Cocoon.Hasaki.productss",
    "hasaki_reviews": "Cocoon.Hasaki.reviewss",
    "shopee_products": "Cocoon.Shopee.productss",
    "shopee_reviews": "Cocoon.Shopee.reviewss",
}


def _mongo_cfg() -> dict | None:
    try:
        import streamlit as st
        cfg = dict(st.secrets["mongo"])
        return cfg if cfg.get("uri") else None
    except Exception:
        return None


def _mongo_db():
    """Trả về database MongoDB, hoặc None nếu chưa cấu hình / không kết nối được."""
    cfg = _mongo_cfg()
    if not cfg:
        return None
    if "client" not in _MONGO:
        try:
            from pymongo import MongoClient
            c = MongoClient(cfg["uri"], serverSelectionTimeoutMS=5000)
            c.admin.command("ping")
            _MONGO["client"] = c
        except Exception as e:  # noqa: BLE001
            _MONGO["client"] = None
            _MONGO["error"] = f"{type(e).__name__}: {e}"
    c = _MONGO["client"]
    return c[cfg.get("db", "Cocoon")] if c else None


def mongo_status() -> str:
    """Dòng trạng thái để hiện trong app."""
    if not _mongo_cfg():
        return "Chưa cấu hình MongoDB (đang dùng SQLite/Excel)"
    if _mongo_db() is None:
        return "Lỗi kết nối MongoDB: " + _MONGO.get("error", "không rõ")
    return "Đã kết nối MongoDB Atlas"


def _mongo_read(table: str) -> pd.DataFrame:
    db = _mongo_db()
    if db is None:
        return pd.DataFrame()
    cfg = _mongo_cfg() or {}
    name = cfg.get("col_" + table, _MONGO_COLS.get(table, table))
    try:
        return pd.DataFrame(list(db[name].find({}, {"_id": 0})))
    except Exception:
        return pd.DataFrame()


def _custom_read(table: str) -> pd.DataFrame:
    """Bảng review thêm mới / sửa: ưu tiên MongoDB, không có thì SQLite."""
    if _mongo_db() is not None:
        return _mongo_read(table)
    return _db_read(table)


def _custom_append(table: str, row: pd.DataFrame) -> None:
    db = _mongo_db()
    if db is not None:
        db[table].insert_many(row.to_dict("records"))
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as con:
        row.to_sql(table, con, if_exists="append", index=False)
        con.commit()


def _load_raw():
    """Thứ tự ưu tiên: MongoDB -> SQLite -> Excel."""
    if _mongo_db() is not None:
        dfs = tuple(_clean_raw(_mongo_read(t)) for t in _DB_TABLES)
        if any(not d.empty for d in dfs):
            return dfs
    if any(_db_has(t) for t in _DB_TABLES):
        return tuple(_clean_raw(_db_read(t)) for t in _DB_TABLES)
    return _load_raw_excel()


def load_base() -> pd.DataFrame:
    try:
        hk_p, hk_r, sp_p, sp_r = _load_raw()

        if "Lượt bán (30 ngày)" in sp_p.columns and "Lượt bán" not in sp_p.columns:
            sp_p = sp_p.rename(columns={"Lượt bán (30 ngày)": "Lượt bán"})
        if "Lượt bán (30 ngày)" in hk_p.columns and "Lượt bán" not in hk_p.columns:
            hk_p = hk_p.rename(columns={"Lượt bán (30 ngày)": "Lượt bán"})

        # ---------------- Shopee ----------------
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

        # ---------------- Hasaki: file sản phẩm làm gốc  ----------------
        if not hk_p.empty:
            hk_base = hk_p.drop_duplicates("Mã SP")
            if not hk_r.empty and "Mã SP" in hk_r.columns:
                hk_merged = hk_base.merge(hk_r, on="Mã SP", how="left", suffixes=("", "_rev"))
            else:
                hk_merged = hk_base.copy()

            def hcol(name, default):
                return hk_merged[name] if name in hk_merged.columns else default

            star_col = "Số sao (review)" if "Số sao (review)" in hk_merged.columns else "Số sao"
            hasaki_df = pd.DataFrame({
                "rid": [f"HS-{i:06d}" for i in range(len(hk_merged))],
                "Nguồn": "Hasaki",
                "Mã SP": hk_merged["Mã SP"],
                "Tên sản phẩm": hk_merged["Tên sản phẩm"].fillna("Sản phẩm Hasaki #" + hk_merged["Mã SP"].astype(str)),
                "Giá bán": hcol("Giá bán", pd.NA),
                "Lượt bán": hcol("Lượt bán", pd.NA),
                "Doanh thu 30 ngày": hcol("Doanh thu 30 ngày", pd.NA),
                "Số sao": hcol(star_col, pd.NA),          # sản phẩm chưa có review -> NaN
                "Nội dung review": hcol("Nội dung review", ""),
                "Ngày review": hcol("Ngày review", pd.NaT),  # không gán ngày giả
                "Đã mua hàng": hcol("Đã mua hàng", pd.NA),
            })
        else:
            hasaki_df = pd.DataFrame()

        frames = [f for f in (shopee_df, hasaki_df) if not f.empty]
        if not frames:
            return pd.DataFrame()
        df = pd.concat(frames, ignore_index=True)

        df["Ngày review"] = pd.to_datetime(df["Ngày review"], errors="coerce").dt.normalize()
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


# Dữ liệu cho tab Power BI (đúng tên cột mà powerbi_dashboard.py cần)

_SOLD_COL = {"Shopee": "Lượt bán", "Hasaki": "Lượt bán (30 ngày)"}


def _powerbi_products(p: pd.DataFrame, plat: str) -> pd.DataFrame:
    if p.empty or "Mã SP" not in p.columns:
        return pd.DataFrame()
    p = p.drop_duplicates("Mã SP").copy()
    sold = _SOLD_COL[plat]
    other = "Lượt bán" if sold != "Lượt bán" else "Lượt bán (30 ngày)"
    if sold not in p.columns and other in p.columns:
        p = p.rename(columns={other: sold})

    if "Tên sản phẩm" not in p.columns:
        p["Tên sản phẩm"] = "Sản phẩm " + p["Mã SP"].astype(str)
    if "Category" not in p.columns:
        alt = next((c for c in ("Hạng mục", "Danh mục") if c in p.columns), None)
        p["Category"] = p[alt] if alt else p["Tên sản phẩm"].map(classify_category)

    nums = ("Giá bán", "Giá gốc", "% Giảm giá", sold, "Doanh thu 30 ngày", "Điểm đánh giá TB")
    for c in nums:
        if c in p.columns:
            p[c] = pd.to_numeric(p[c], errors="coerce")
    if "% Giảm giá" not in p.columns and "Giá bán" in p.columns and "Giá gốc" in p.columns:
        p["% Giảm giá"] = (1 - p["Giá bán"] / p["Giá gốc"]) * 100
    if "Doanh thu 30 ngày" not in p.columns and "Giá bán" in p.columns and sold in p.columns:
        p["Doanh thu 30 ngày"] = p["Giá bán"] * p[sold]
    for c in nums:
        if c not in p.columns:
            p[c] = float("nan")
    return p.reset_index(drop=True)


def _powerbi_reviews(r: pd.DataFrame, p: pd.DataFrame) -> pd.DataFrame:
    if r.empty or "Mã SP" not in r.columns:
        return pd.DataFrame()
    r = r.copy()
    if not p.empty:
        in_file = r[r["Mã SP"].isin(p["Mã SP"])]
        if not in_file.empty:
            r = in_file
    r["Số sao (review)"] = pd.to_numeric(r["Số sao (review)"], errors="coerce") if "Số sao (review)" in r.columns else float("nan")
    if "Ngày review" not in r.columns:
        r["Ngày review"] = pd.NaT
    if "Sentiment" not in r.columns:
        r["Sentiment"] = r["Số sao (review)"].apply(sentiment_from_star)
    if "Xác nhận mua hàng" not in r.columns and "Đã mua hàng" in r.columns:
        r["Xác nhận mua hàng"] = r["Đã mua hàng"]
    return r.reset_index(drop=True)


def load_powerbi_tables() -> dict:
    hk_p, hk_r, sp_p, sp_r = _load_raw()
    ps = _powerbi_products(sp_p, "Shopee")
    ph = _powerbi_products(hk_p, "Hasaki")
    return {
        "products_shopee": ps,
        "reviews_shopee": _powerbi_reviews(sp_r, ps),
        "products_hasaki": ph,
        "reviews_hasaki": _powerbi_reviews(hk_r, ph),
    }


# Xóa mềm

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
    log = load_deleted()
    gone = {d["rid"] for d in log if isinstance(d, dict) and "rid" in d}
    return df[~df["rid"].isin(gone)] if gone else df



# CRUD: Create + Update

def add_review(source: str, ma_sp: str, stars: int, content: str, date) -> str:
    """Thêm review mới. Trả về rid."""
    rid = f"NEW-{datetime.now():%Y%m%d%H%M%S%f}"
    row = pd.DataFrame([{
        "rid": rid,
        "Nguồn": source,
        "Mã SP": str(ma_sp),
        "Số sao": float(stars),
        "Nội dung review": content,
        "Ngày review": pd.Timestamp(date).isoformat(),
    }])
    _custom_append("custom_reviews", row)
    return rid


def update_review(rid: str, stars, content: str) -> None:
    """Sửa số sao / nội dung của một review (lưu dạng bản ghi ghi đè)."""
    row = pd.DataFrame([{
        "rid": rid,
        "Số sao": float(stars),
        "Nội dung review": content,
        "at": datetime.now().isoformat(timespec="seconds"),
    }])
    _custom_append("review_updates", row)


def apply_crud(df: pd.DataFrame) -> pd.DataFrame:
    """Áp review thêm mới + review đã sửa lên bảng base."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
    df = df.copy()

    ups = _custom_read("review_updates")
    if not ups.empty:
        ups = ups.drop_duplicates("rid", keep="last").set_index("rid")
        m = df["rid"].isin(ups.index)
        df.loc[m, "Số sao"] = df.loc[m, "rid"].map(ups["Số sao"])
        df.loc[m, "Nội dung review"] = df.loc[m, "rid"].map(ups["Nội dung review"])

    new = _custom_read("custom_reviews")
    if not new.empty:
        rows = []
        for _, r in new.iterrows():
            tpl = df[(df["Nguồn"] == r["Nguồn"]) & (df["Mã SP"].astype(str) == str(r["Mã SP"]))]
            if tpl.empty:
                continue
            row = tpl.iloc[0].copy()
            row["rid"] = r["rid"]
            row["Số sao"] = r["Số sao"]
            row["Nội dung review"] = r["Nội dung review"]
            row["Ngày review"] = r["Ngày review"]
            rows.append(row)
        if rows:
            df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)

    df["Số sao"] = pd.to_numeric(df["Số sao"], errors="coerce")
    df["Ngày review"] = pd.to_datetime(df["Ngày review"], errors="coerce").dt.normalize()
    df["Tháng"] = df["Ngày review"].dt.to_period("M").dt.to_timestamp()
    df["Cảm xúc"] = df["Số sao"].apply(sentiment_from_star)
    return df



# Sao lưu / phục hồi

_BACKUP_FILES = {"cocoon.db": lambda: DB_PATH, "deleted_rows.json": lambda: DELETED_FILE}


def make_backup() -> bytes:
    """Nén cocoon.db + deleted_rows.json thành 1 file zip (trong bộ nhớ)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for arcname, getter in _BACKUP_FILES.items():
            p = getter()
            if p.exists():
                z.write(p, arcname)
    return buf.getvalue()


def restore_backup(data: bytes) -> list[str]:
    """Khôi phục từ file zip backup. Chỉ chấp nhận đúng 2 tên file ở trên."""
    restored = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = set(z.namelist())
        if not names & set(_BACKUP_FILES):
            raise ValueError("File zip không phải bản sao lưu của Cocoon Analytics.")
        for arcname, getter in _BACKUP_FILES.items():
            if arcname in names:
                dest = getter()
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(arcname))
                restored.append(arcname)
    return restored


# Bảng tổng hợp

def product_table(df: pd.DataFrame) -> pd.DataFrame:
    """Mỗi (Nguồn, Mã SP) đúng 1 dòng; 'Số review' chỉ đếm review thật."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()

    df = df.copy()
    if "Doanh thu 30 ngày" in df.columns:
        df["Doanh thu 30 ngày"] = pd.to_numeric(df["Doanh thu 30 ngày"], errors="coerce")

    g = df.groupby(["Nguồn", "Mã SP"], observed=True, dropna=False)
    out = g.agg(**{
        "Tên sản phẩm": ("Tên sản phẩm", "first"),
        "Hạng mục": ("Hạng mục", "first"),
        "Dòng sản phẩm": ("Dòng sản phẩm", "first"),
        "Giá bán": ("Giá bán", "first"),
        "Lượt bán": ("Lượt bán", "first"),
        "Doanh thu 30 ngày": ("Doanh thu 30 ngày", "first"),
        "Số review": ("Số sao", "count"),
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
    d = df.dropna(subset=["Tháng", "Số sao"])
    return d.groupby(["Tháng", "Nguồn"]).size().rename("Số review").reset_index()


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
