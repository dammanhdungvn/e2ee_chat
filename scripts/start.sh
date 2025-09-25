#!/usr/bin/env bash
# 🔐 Script khởi chạy ứng dụng Chat E2EE Mini
# 
# Tính năng:
# ✅ Tự động tạo virtual environment Python
# ✅ Cài đặt dependencies từ require.txt  
# ✅ Kiểm tra và cài đặt system dependencies
# ✅ Khởi chạy ứng dụng với error handling
# ✅ Hỗ trợ Linux và macOS
#
# Sử dụng: ./start.sh
# Yêu cầu: Python 3.8+, pip

set -euo pipefail
# Chuyển về thư mục gốc của dự án (parent directory của scripts/)
cd "$(dirname "$0")/.."

# Màu sắc cho output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Header đẹp
echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🔐 Chat E2EE Mini 🔐                    ║"
echo "║              Ứng dụng Chat mã hóa đầu cuối                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Kiểm tra Python version
echo -e "${BLUE}🔍 Kiểm tra Python version...${NC}"
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $python_version${NC}"

# Kiểm tra system dependencies cho Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${BLUE}🔍 Kiểm tra system dependencies...${NC}"
    
    # Kiểm tra Qt dependencies
    missing_deps=()
    if ! dpkg -l libxcb-cursor0 2>/dev/null | grep -q "^ii.*libxcb-cursor0"; then
        missing_deps+=("libxcb-cursor0")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Cần cài đặt system dependencies: ${missing_deps[*]}${NC}"
        echo -e "${BLUE}📦 Đang cài đặt...${NC}"
        sudo apt-get update -qq
        sudo apt-get install -y "${missing_deps[@]}"
        echo -e "${GREEN}✅ Đã cài đặt system dependencies${NC}"
    else
        echo -e "${GREEN}✅ System dependencies OK${NC}"
    fi
fi

# Tạo virtual environment nếu chưa có
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}🏗️  Tạo virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Đã tạo virtual environment${NC}"
else
    echo -e "${GREEN}✅ Virtual environment đã tồn tại${NC}"
fi

# Kích hoạt virtual environment
echo -e "${BLUE}🔌 Kích hoạt virtual environment...${NC}"
# shellcheck disable=SC1091
source .venv/bin/activate

# Nâng cấp pip và cài đặt dependencies
echo -e "${BLUE}📦 Cài đặt dependencies...${NC}"
python -m pip install --upgrade pip setuptools wheel --quiet
if [ -f "require.txt" ]; then
    pip install -r require.txt --quiet
    echo -e "${GREEN}✅ Đã cài đặt dependencies từ require.txt${NC}"
else
    echo -e "${RED}❌ Không tìm thấy require.txt${NC}"
    exit 1
fi

# Tạo thư mục data nếu chưa có
if [ ! -d "data" ]; then
    mkdir -p data
    echo -e "${GREEN}✅ Đã tạo thư mục data/${NC}"
fi

# Khởi chạy ứng dụng với error handling
echo -e "${BLUE}🚀 Khởi chạy ứng dụng Chat E2EE...${NC}"
echo -e "${YELLOW}💡 Tip: Tạo nhiều cửa sổ chat để trải nghiệm E2EE!${NC}"
echo ""

if python -m app.main; then
    echo -e "${GREEN}✅ Ứng dụng đã thoát thành công${NC}"
else
    echo -e "${RED}❌ Ứng dụng gặp lỗi (exit code: $?)${NC}"
    echo -e "${YELLOW}💡 Hãy kiểm tra log ở trên để biết chi tiết lỗi${NC}"
    exit 1
fi
