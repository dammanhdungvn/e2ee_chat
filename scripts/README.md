# 🚀 Scripts

Thư mục chứa các script khởi chạy ứng dụng cho các hệ điều hành khác nhau.

## 📁 Nội dung

### 🐧 Linux/macOS:
- `start.sh` - Script bash để khởi chạy ứng dụng trên Linux/macOS

### 🪟 Windows:
- `start.bat` - Script batch để khởi chạy ứng dụng trên Windows

## 🎯 Cách sử dụng

### Linux/macOS:
```bash
# Cấp quyền thực thi
chmod +x scripts/start.sh

# Chạy script
./scripts/start.sh
```

### Windows:
```cmd
# Chạy script
scripts\start.bat
```

## ⚡ Chức năng

Cả hai script đều thực hiện các bước sau:
1. ✅ Kiểm tra Python version (>= 3.8)
2. ✅ Tạo virtual environment (nếu chưa có)
3. ✅ Cài đặt dependencies từ `require.txt`
4. ✅ Khởi chạy ứng dụng

## 🔧 Tùy chỉnh

Nếu cần thay đổi cấu hình:
- Chỉnh sửa script tương ứng
- Đảm bảo đường dẫn đúng với cấu trúc dự án
- Test script trên hệ điều hành tương ứng
