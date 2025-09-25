@echo off
REM 🔐 Script khởi chạy ứng dụng Chat E2EE Mini cho Windows
REM 
REM Tính năng:
REM ✅ Tự động tạo virtual environment Python
REM ✅ Cài đặt dependencies từ require.txt
REM ✅ Kiểm tra Python version và system requirements
REM ✅ Khởi chạy ứng dụng với error handling
REM ✅ Hỗ trợ Windows 10/11
REM
REM Sử dụng: start.bat (double-click hoặc chạy từ cmd)
REM Yêu cầu: Python 3.8+, pip

setlocal ENABLEDELAYEDEXPANSION
REM Chuyển về thư mục gốc của dự án (parent directory của scripts/)
cd /d "%~dp0.."

REM Header đẹp với Unicode
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🔐 Chat E2EE Mini 🔐                    ║
echo ║              Ứng dụng Chat mã hóa đầu cuối                  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Kiểm tra Python installation
echo 🔍 Kiểm tra Python installation...
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Python không được cài đặt hoặc không có trong PATH
    echo 💡 Vui lòng cài đặt Python 3.8+ từ https://python.org
    pause
    exit /b 1
)

REM Hiển thị Python version
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python !PYTHON_VERSION!

REM Kiểm tra pip
echo 🔍 Kiểm tra pip...
python -m pip --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ pip không khả dụng
    echo 💡 Vui lòng cài đặt pip
    pause
    exit /b 1
)
echo ✅ pip OK

REM Tạo virtual environment nếu chưa có
if not exist .venv (
    echo 🏗️  Tạo virtual environment...
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo ❌ Không thể tạo virtual environment
        pause
        exit /b 1
    )
    echo ✅ Đã tạo virtual environment
) else (
    echo ✅ Virtual environment đã tồn tại
)

REM Kích hoạt virtual environment
echo 🔌 Kích hoạt virtual environment...
call .venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo ❌ Không thể kích hoạt virtual environment
    pause
    exit /b 1
)

REM Nâng cấp pip và cài đặt dependencies
echo 📦 Cài đặt dependencies...
python -m pip install --upgrade pip setuptools wheel --quiet
if !errorlevel! neq 0 (
    echo ⚠️  Cảnh báo: Không thể nâng cấp pip
)

if exist require.txt (
    pip install -r require.txt --quiet
    if !errorlevel! neq 0 (
        echo ❌ Lỗi cài đặt dependencies
        echo 💡 Hãy kiểm tra kết nối internet và thử lại
        pause
        exit /b 1
    )
    echo ✅ Đã cài đặt dependencies từ require.txt
) else (
    echo ❌ Không tìm thấy require.txt
    pause
    exit /b 1
)

REM Tạo thư mục data nếu chưa có
if not exist data (
    mkdir data
    echo ✅ Đã tạo thư mục data\
)

REM Khởi chạy ứng dụng với error handling
echo 🚀 Khởi chạy ứng dụng Chat E2EE...
echo 💡 Tip: Tạo nhiều cửa sổ chat để trải nghiệm E2EE!
echo.

python -m app.main
set APP_EXIT_CODE=!errorlevel!

if !APP_EXIT_CODE! equ 0 (
    echo.
    echo ✅ Ứng dụng đã thoát thành công
) else (
    echo.
    echo ❌ Ứng dụng gặp lỗi (exit code: !APP_EXIT_CODE!)
    echo 💡 Hãy kiểm tra log ở trên để biết chi tiết lỗi
)

echo.
echo 🔐 Cảm ơn bạn đã sử dụng Chat E2EE Mini!
pause
