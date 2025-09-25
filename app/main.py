"""
Entry point chính cho ứng dụng chat E2EE
- Khởi tạo QApplication
- Thiết lập môi trường tiếng Việt
- Tải font hỗ trợ tiếng Việt
- Khởi chạy launcher
"""

from __future__ import annotations

import sys
import os
from PySide6 import QtWidgets, QtCore, QtGui
from .ui import Launcher

# Thư mục chứa font tùy chỉnh
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")


def _load_embedded_fonts() -> None:
    """
    Tải các font tùy chỉnh từ thư mục fonts/
    Hỗ trợ các định dạng .ttf và .otf
    """
    if not os.path.isdir(FONTS_DIR):
        return
    
    for fname in os.listdir(FONTS_DIR):
        if not (fname.lower().endswith(".ttf") or fname.lower().endswith(".otf")):
            continue
        QtGui.QFontDatabase.addApplicationFont(os.path.join(FONTS_DIR, fname))


def _setup_vietnamese_environment(app: QtWidgets.QApplication) -> None:
    """
    Thiết lập môi trường tiếng Việt cho ứng dụng
    - Đặt locale tiếng Việt
    - Tải font hỗ trợ tiếng Việt
    - Chọn font phù hợp nhất
    Args:
        app: QApplication instance
    """
    # Thiết lập locale tiếng Việt
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Language.Vietnamese, QtCore.QLocale.Country.Vietnam))
    app.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)

    # Tải font tùy chỉnh
    _load_embedded_fonts()

    # Danh sách font ưu tiên hỗ trợ tiếng Việt
    preferred_fonts = [
        "Noto Sans",      # Font Google hỗ trợ đa ngôn ngữ
        "DejaVu Sans",    # Font mã nguồn mở
        "Arial",          # Font Windows phổ biến
        "Segoe UI",       # Font Windows hiện đại
        "Roboto",         # Font Android
    ]
    
    # Tìm font phù hợp nhất
    chosen = None
    for family in preferred_fonts:
        if family in QtGui.QFontDatabase.families():
            chosen = family
            break
    
    # Nếu không tìm thấy font ưu tiên, chọn font đầu tiên có sẵn
    if chosen is None and QtGui.QFontDatabase.families():
        chosen = QtGui.QFontDatabase.families()[0]
    
    # Áp dụng font đã chọn
    if chosen:
        font = QtGui.QFont(chosen, 10)
        app.setFont(font)


def main() -> int:
    """
    Hàm main khởi chạy ứng dụng
    Returns:
        int: Exit code của ứng dụng
    """
    # Thiết lập platform cho Linux - thử các platform khác nhau
    if sys.platform.startswith('linux'):
        # Thử wayland trước, nếu không được thì dùng xcb
        if os.environ.get('WAYLAND_DISPLAY'):
            os.environ["QT_QPA_PLATFORM"] = "wayland"
        else:
            os.environ["QT_QPA_PLATFORM"] = "xcb"
    
    # Khởi tạo QApplication
    app = QtWidgets.QApplication(sys.argv)
    
    # Thiết lập môi trường tiếng Việt
    _setup_vietnamese_environment(app)
    
    # Tạo và hiển thị launcher
    launcher = Launcher()
    launcher.show()
    
    # Chạy event loop
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
