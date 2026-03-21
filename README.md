# HSql - Desktop SQL Client (DataGrip Clone)

Đây là phiên bản clone giao diện cơ bản của DataGrip được xây dựng bằng **Python** và **PyQt6**. Ứng dụng chạy hoàn toàn trên môi trường Windows Desktop thông qua các thư viện GUI gốc (native), mang lại trải nghiệm nhanh và mượt mà mà không dựa vào trình duyệt web.

## Yêu cầu hệ thống
- Máy tính chạy hệ điều hành Windows.
- Đã cài đặt [Python](https://www.python.org/downloads/) (phiên bản 3.8 trở lên).

## Hướng dẫn cài đặt và chạy ứng dụng

### Bước 1: Mở Terminal hoặc Command Prompt
Mở ứng dụng Command Prompt hoặc PowerShell trên Windows và di chuyển đến thư mục chứa dự án `HSql`:
```bash
cd c:\Users\AmkorAdmin\Desktop\Hacker\HSql
```

### Bước 2: Tạo môi trường ảo (Khuyến nghị)
Việc tạo môi trường ảo (virtual environment) giúp các thư viện của dự án này không bị xung đột với các dự án khác trên máy.
```bash
python -m venv venv
```

### Bước 3: Kích hoạt môi trường ảo
Trên Windows, bạn chạy lệnh sau để kích hoạt môi trường vừa tạo:
```bash
venv\Scripts\activate
```

### Bước 4: Cài đặt thư viện giao diện
Cài đặt thư viện `PyQt6` để ứng dụng có thể vẽ được giao diện cửa sổ:
```bash
pip install -r requirements.txt
```

### Bước 5: Khởi động chương trình
Sau khi cài đặt xong, chỉ cần dùng Python chạy file `main.py` để mở giao diện HSql:
```bash
python main.py
```

---

## Tính năng giao diện đã được thiết kế trong bản Mockup này:
- **Ngôn ngữ thiết kế IDE Dark Mode:** Nền tối, chữ sáng (giống font màu sắc của series JetBrains/DataGrip).
- **Database Explorer (Cột bên trái):** Giao diện dạng cây (Tree) hiển thị mô phỏng kết nối, database, schema và table. Có thể thu nhỏ kéo giãn.
- **SQL Editor (Trên giữa):** Trình soạn thảo văn bản nơi bạn có thể gõ câu lệnh SQL. Đã hỗ trợ phím tắt `Ctrl + Enter` hoặc nhấn biểu tượng `▶` trên Toolbar để chạy giả lập.
- **Data Results (Dưới giữa):** Một bảng (Table Widget) hiển thị dữ liệu kết quả giống hệt DataGrip.
- **Khung có thể điều chỉnh linh hoạt:** Có các đường ngăn (Splitter) giúp bạn kéo lên/xuống, sang trái/phải để thu phóng Editor hay bảng dữ liệu như ý.

## Cách tiếp tục phát triển (Phần Logic API):
Khi bạn đã hài lòng với UI này, bước tiếp theo hoàn toàn có thể tự code thêm:
1. Kết nối DB thật thông qua `psycopg2` (cho PostgreSQL), `pymysql` (cho MySQL) hoặc `pyodbc` (SQL Server).
2. Khi người dùng bấm Execute -> Gọi DB lấy record -> Đổ dữ liệu thật vào vòng lặp sinh bảng `QTableWidget`.
3. Có thể đưa thêm `QsciScintilla` (Thư viện phụ) để code SQL có màu sắc highlight xịn xò như DataGrip!
