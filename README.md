# 🔐 Ứng Dụng Chat E2EE Mini

> **Ứng dụng chat mã hóa đầu cuối (End-to-End Encryption) với giao diện đẹp mắt và tính năng giáo dục**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.6+-green.svg)](https://pypi.org/project/PySide6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Mô Tả

Ứng dụng chat E2EE Mini là một dự án giáo dục nhằm minh họa cách thức hoạt động của mã hóa đầu cuối. Ứng dụng cho phép người dùng:

- 💬 **Chat an toàn**: Tạo nhiều cửa sổ chat và trò chuyện với nhau
- 🔒 **E2EE thực sự**: Sử dụng X25519 + AES-GCM cho bảo mật tối đa
- 📚 **Tính năng giáo dục**: Hiển thị chi tiết quá trình mã hóa/giải mã
- 🎨 **Giao diện hiện đại**: UI/UX đẹp mắt với gradient và animation
- 💾 **Lưu trữ lịch sử**: Tự động lưu và khôi phục cuộc trò chuyện
- 🌐 **Đa nền tảng**: Chạy trên Windows, Linux, macOS

## 🛡️ Tính Năng Bảo Mật

### 🔑 Mã Hóa Mạnh Mẽ
- **X25519**: Elliptic Curve Diffie-Hellman key exchange
- **AES-256-GCM**: Authenticated encryption với 256-bit key
- **HKDF-SHA256**: Key derivation function để tạo AES key
- **Ephemeral Keys**: Khóa mới cho mỗi phiên, không lưu trữ

### 🔍 Tính Năng Giáo Dục
- **Live E2EE Panel**: Hiển thị real-time thông tin mã hóa
- **Demo tương tác**: Minh họa trực quan quá trình E2EE
- **Chi tiết kỹ thuật**: Hiển thị public key, nonce, ciphertext
- **Giải thích dễ hiểu**: Hướng dẫn từng bước về E2EE

## 🚀 Cài Đặt Nhanh

### 📦 Yêu Cầu Hệ Thống
- **Python**: 3.8 trở lên
- **RAM**: Tối thiểu 512MB
- **Dung lượng**: ~50MB sau khi cài đặt
- **Hệ điều hành**: Windows 10+, Ubuntu 18.04+, macOS 10.14+

### ⚡ Khởi Chạy Tự Động

#### 🐧 Linux/macOS:
```bash
chmod +x start.sh
./start.sh
```

#### 🪟 Windows:
```cmd
start.bat
```

Script tự động sẽ:
1. ✅ Tạo virtual environment (nếu chưa có)
2. ✅ Cài đặt dependencies từ `require.txt`
3. ✅ Khởi chạy ứng dụng

### 🔧 Cài Đặt Thủ Công

```bash
# Tạo virtual environment
python3 -m venv .venv

# Kích hoạt environment
source .venv/bin/activate  # Linux/macOS
# hoặc
.venv\Scripts\activate.bat  # Windows

# Cài đặt dependencies
pip install -r require.txt

# Chạy ứng dụng
python -m app.main
```

## 🎮 Hướng Dẫn Sử Dụng

### 1️⃣ Khởi Tạo Chat
1. Mở ứng dụng → Nhập tên hiển thị
2. Click **"MỞ CỬA SỔ CHAT"**
3. Lặp lại để tạo nhiều cửa sổ chat

### 2️⃣ Trò Chuyện An Toàn
1. Chọn người nhận từ dropdown **"Gửi đến"**
2. Nhập tin nhắn → Click **Gửi** hoặc nhấn **Enter**
3. Tin nhắn được mã hóa E2EE trước khi gửi

### 3️⃣ Theo Dõi E2EE
- **Panel bên phải**: Hiển thị thông tin mã hóa real-time
- **Tab "Giải thích E2EE"**: Tìm hiểu chi tiết về E2EE
- **Demo tương tác**: Thử nghiệm mã hóa/giải mã

### 4️⃣ Quản Lý Lịch Sử
- **Tự động lưu**: Mọi cuộc trò chuyện được lưu vào `data/`
- **Khôi phục**: Click vào tên trong **"Lịch sử chat"** để mở lại
- **Avatar màu**: Mỗi người dùng có màu avatar riêng biệt

## 📁 Cấu Trúc Dự Án

```
e2eee/
├── 📂 app/                 # Mã nguồn chính
│   ├── 🐍 main.py         # Entry point, thiết lập ứng dụng
│   ├── 🔒 crypto.py       # Mô-đun mã hóa E2EE
│   ├── 🚀 transport.py    # Broker chuyển tiếp tin nhắn
│   ├── 🎨 ui.py           # Giao diện người dùng
│   └── 📋 __init__.py     # Package initialization
├── 📂 data/               # Lưu trữ lịch sử chat (HTML)
├── 📋 require.txt         # Dependencies Python
├── 🚀 start.sh           # Script khởi chạy Linux/macOS
├── 🚀 start.bat          # Script khởi chạy Windows
├── 📖 README.md          # Tài liệu này
└── 📊 baocao.md          # Báo cáo kỹ thuật chi tiết
```

## 🔬 Chi Tiết Kỹ Thuật

### 🔐 Quy Trình E2EE

1. **Key Generation**: Mỗi client tạo cặp khóa X25519
2. **Key Exchange**: Trao đổi public key qua broker
3. **Shared Secret**: ECDH tạo shared secret
4. **Key Derivation**: HKDF-SHA256 tạo AES-256 key
5. **Encryption**: AES-256-GCM mã hóa tin nhắn
6. **Transport**: Chỉ ciphertext được gửi qua broker
7. **Decryption**: Receiver giải mã bằng shared key

### 🏗️ Kiến Trúc Hệ Thống

```mermaid
graph TB
    A[Client A] --> B[InMemoryBroker]
    C[Client B] --> B
    D[Client C] --> B
    
    B --> A
    B --> C
    B --> D
    
    A -.->|Public Key Exchange| C
    C -.->|Encrypted Messages| A
```

### 📦 Dependencies

| Package | Version | Mục Đích |
|---------|---------|----------|
| **PySide6** | 6.6+ | GUI framework hiện đại |
| **cryptography** | 42+ | Thư viện mã hóa mạnh mẽ |

## 💾 Lưu Trữ & Bảo Mật

### 📄 Định Dạng Lưu Trữ
- **Format**: HTML với UTF-8 encoding
- **Location**: `data/{display-name}.html`
- **Content**: Chỉ tin nhắn đã giải mã (plaintext)

### 🔒 Chính Sách Bảo Mật
- ✅ **Keys không lưu trữ**: Ephemeral keys, tạo mới mỗi session
- ✅ **Forward Secrecy**: Tin nhắn cũ an toàn khi key mới bị lộ
- ✅ **Local Only**: Không có kết nối internet, chạy hoàn toàn offline
- ✅ **Open Source**: Code mở, có thể audit bảo mật

## 🎨 Tính Năng UI/UX

### 🌈 Giao Diện Hiện Đại
- **Gradient Background**: Màu sắc chuyển tiếp mượt mà
- **Avatar Đa Màu**: 26 màu khác nhau cho từng chữ cái
- **Messenger-Style Bubbles**: Tin nhắn hiển thị như Facebook Messenger
- **Responsive Design**: Tự động điều chỉnh kích thước

### ⚡ Hiệu Ứng Tương Tác
- **Hover Effects**: Hiệu ứng khi di chuột
- **Smooth Animations**: Chuyển tiếp mượt mà
- **Resizable Panels**: Kéo thả panel E2EE
- **Real-time Updates**: Cập nhật thông tin tức thì

## 🛠️ Phát Triển

### 🧪 Chạy Tests
```bash
# Sẽ được thêm trong phiên bản tương lai
python -m pytest tests/
```

### 🐛 Debug Mode
```bash
# Chạy với debug logging
PYTHONPATH=. python -m app.main --debug
```

### 📝 Đóng Góp
1. Fork repository
2. Tạo feature branch: `git checkout -b feature-amazing`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature-amazing`
5. Tạo Pull Request

## ⚠️ Lưu Ý Bảo Mật

> **Chỉ dành cho mục đích giáo dục và demo**

- 🔴 **Không sử dụng cho production**: Đây là ứng dụng demo
- 🔴 **Broker không bảo mật**: InMemoryBroker có thể thấy metadata
- 🔴 **Không có authentication**: Không xác thực danh tính người dùng
- 🔴 **Local storage**: Lịch sử chat lưu dạng plaintext

## 🆘 Hỗ Trợ

### 🐛 Gặp Lỗi?
1. **Kiểm tra Python version**: `python --version` (cần >= 3.8)
2. **Cài đặt lại dependencies**: `pip install -r require.txt --force-reinstall`
3. **Xóa virtual environment**: `rm -rf .venv` và chạy lại script

### 💡 Tính Năng Mới?
- Mở issue trên GitHub với tag `enhancement`
- Mô tả chi tiết tính năng mong muốn
- Giải thích use case cụ thể

## 📄 License

Dự án được phát hành dưới [MIT License](LICENSE). Bạn có thể tự do sử dụng, sửa đổi và phân phối.

---

<div align="center">

**🔐 Made with ❤️ for E2EE Education 🔐**

[⭐ Star this repo](https://github.com/your-username/e2eee) • [🐛 Report Bug](https://github.com/your-username/e2eee/issues) • [✨ Request Feature](https://github.com/your-username/e2eee/issues)

</div>