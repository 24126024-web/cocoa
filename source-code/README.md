# Cocoon Analytics – Streamlit (Giai đoạn 5)

## Chạy
```
cd source-code
pip install -r requirements.txt
streamlit run app.py
```
Dữ liệu đọc từ `../dataset/` (`cocoon_shopee_clean.xlsx`, `Reviews_final.xlsx`).

## Tài khoản demo
| Vai trò | Tài khoản | Mật khẩu | Quyền |
|---|---|---|---|
| Admin | admin | admin123 | Xem, tải CSV/Excel, xóa/khôi phục review |
| User | user | user123 | Chỉ xem |
Đổi mật khẩu thật: sao chép `.streamlit/secrets.toml.example` → `secrets.toml` (đừng commit).

## Chức năng
- Giao diện: KPI, thống kê Min–Max, biểu đồ tròn/đường/cột, bảng dữ liệu, nhúng Power BI (iframe).
- Phân quyền: form login, User/Admin.
- Lọc: `st.sidebar.selectbox` theo Nền tảng, Hạng mục (da mặt/tóc/cơ thể/môi), Dòng sản phẩm, Sản phẩm; thêm lọc sao, ngày, từ khóa.
- Kết xuất: `st.download_button` CSV + Excel (Admin).
- Xóa mềm: ghi `dataset/deleted_rows.json`, file gốc giữ nguyên, có thể khôi phục.
- Tab "Kết quả mô hình": tự đọc `dataset/model_outputs/{kmeans_clusters,sentiment_predictions,apriori_rules}.csv`.

## Lưu ý dữ liệu
- Hasaki (`Reviews_final.xlsx`) chỉ có Mã SP, không có tên/giá → hạng mục hiện là "Chưa phân loại". Thêm `dataset/hasaki_products.csv` (cột `Mã SP`, `Tên sản phẩm`, tùy chọn `Giá bán`, `Lượt bán`, `Doanh thu 30 ngày`) là app tự phân loại.
- Doanh thu chỉ có dạng "30 ngày" theo sản phẩm (Shopee), không theo tháng.

## Cập nhật dữ liệu Hasaki
`dataset/hasaki_products.xlsx` (từ `products_final.xlsx`) chứa tên/giá/doanh thu 84 sản phẩm Hasaki; 25 mã SP còn lại trong review chưa có thông tin nên hiện "Chưa phân loại".

## Giao diện đăng nhập
Trang Sign in dùng màu xanh lá, nền xoay vòng 3 ảnh sản phẩm (`assets/bg1-3.jpg`), logo cô gái đội nón lá (`assets/logo.png`). Có thể thay ảnh bằng cách ghi đè các file trong `assets/` (giữ nguyên tên).
