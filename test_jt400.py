import os
import jaydebeapi

# --- Cấu hình thông tin kết nối ---
HOST = "TEN_HE_THONG_OR_IP"  # Ví dụ: 10.201.x.x
USER = "YOUR_USERNAME"
PASSWORD = "YOUR_PASSWORD"
DATABASE = "YOUR_LIB"       # Tùy chọn, có thể để trống
PORT = "446"                # Cổng mặc định của DB2 iSeries là 446 (DRDA)

# Đường dẫn tới Driver
project_root = os.path.dirname(os.path.abspath(__file__))
jar_path = os.path.join(project_root, "drivers", "jt400.jar")

if not os.path.exists(jar_path):
    print(f"❌ Không tìm thấy Driver tại: {jar_path}")
    exit(1)

# JDBC URL format: jdbc:as400://systemname[:port][/defaultSchema]
url = f"jdbc:as400://{HOST}:{PORT}/{DATABASE}" if DATABASE else f"jdbc:as400://{HOST}:{PORT}"
driver_class = "com.ibm.as400.access.AS400JDBCDriver"

print(f"--- Đang thử kết nối tới {HOST} ---")
print(f"URL: {url}")

try:
    conn = jaydebeapi.connect(driver_class, url, [USER, PASSWORD], jar_path)
    print("✅ Kết nối THÀNH CÔNG!")
    
    # Thử chạy một truy vấn đơn giản (ví dụ: lấy ngày giờ hệ thống)
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT TIMESTAMP FROM SYSIBM.SYSDUMMY1")
    result = cursor.fetchone()
    print(f"🕒 Thời gian trên server: {result[0]}")
    
    cursor.close()
    conn.close()
    print("--- Đã đóng kết nối ---")

except Exception as e:
    print("❌ Kết nối THẤT BẠI!")
    print(f"Lỗi: {e}")
