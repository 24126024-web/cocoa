"""Nạp 4 file Excel (Shopee & Hasaki) vào SQLite: cocoon.db

Chạy:  python build_db.py
Chạy lại bất cứ lúc nào dữ liệu Excel thay đổi (bảng gốc sẽ được ghi đè,
bảng custom_reviews / review_updates do CRUD tạo ra được giữ nguyên).
"""
import sqlite3
from contextlib import closing

import data_utils as du


def main() -> None:
    hk_p, hk_r, sp_p, sp_r = du._load_raw_excel()
    tables = {
        "hasaki_products": hk_p,
        "hasaki_reviews": hk_r,
        "shopee_products": sp_p,
        "shopee_reviews": sp_r,
    }
    du.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(du.DB_PATH)) as con:
        for name, d in tables.items():
            if d is None or d.empty:
                print(f"[BỎ QUA] {name}: không có dữ liệu")
                continue
            d.to_sql(name, con, if_exists="replace", index=False)
            print(f"[OK] {name}: {len(d):,} dòng")
        con.commit()
    print(f"\nĐã tạo: {du.DB_PATH}")


if __name__ == "__main__":
    main()
