"""
Giao diện người dùng cho ứng dụng chat E2EE
- Quản lý cửa sổ chat và launcher
- Hiển thị tin nhắn với bubble style Messenger
- Panel E2EE thời gian thực
- Lưu trữ lịch sử chat
"""

from __future__ import annotations

from typing import Dict, Optional
from dataclasses import dataclass
import os
import re
import datetime
import html as py_html

from PySide6 import QtCore, QtGui, QtWidgets

from .crypto import KeyPair, derive_shared_key, encrypt_message, decrypt_message, public_key_bytes
from .transport import InMemoryBroker, ClientRegistration
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
from cryptography.hazmat.primitives import hashes

# Thư mục lưu trữ lịch sử chat
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class FadeLabel(QtWidgets.QLabel):
    """
    Label với hiệu ứng fade in/out cho thông báo trạng thái
    """
    def __init__(self, text: str = "", parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(text, parent)
        self._opacity = 1.0
        self._effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)

    @QtCore.Property(float)
    def opacity(self) -> float:  # type: ignore[override]
        return self._opacity

    @opacity.setter
    def opacity(self, value: float) -> None:  # type: ignore[override]
        self._opacity = value
        self._effect.setOpacity(value)


@dataclass
class Peer:
    """Thông tin người dùng trong chat"""
    client_id: str
    display_name: str
    public_key_bytes: bytes


def _safe_filename(name: str) -> str:
    """
    Chuyển đổi tên hiển thị thành tên file an toàn
    - Loại bỏ ký tự đặc biệt
    - Chuyển thành chữ thường
    - Thay thế khoảng trắng bằng dấu gạch ngang
    """
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_-]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "nguoi-dung"


def _wrap_html_with_utf8_meta(html_content: str) -> str:
    """
    Đảm bảo HTML có meta charset UTF-8 để hiển thị tiếng Việt đúng
    """
    if "<meta charset=" in html_content.lower():
        return html_content
    head_insert = "<meta charset=\"utf-8\">"
    if "<head>" in html_content.lower():
        return re.sub(r"(?i)<head>", "<head>" + head_insert, html_content, count=1)
    return """<!DOCTYPE html><html><head><meta charset=\"utf-8\"></head><body>{}</body></html>""".format(html_content)


def _format_timestamp() -> str:
    """Định dạng thời gian hiện tại theo dd/MM/yyyy HH:mm"""
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M")


def _format_bubble(sender: str, text: str, outgoing: bool) -> str:
    """
    Tạo HTML cho bubble tin nhắn theo style Messenger
    - Tin gửi: màu xanh, căn phải
    - Tin nhận: màu xám, căn trái
    - Tự động xuống dòng cho text dài
    """
    ts = _format_timestamp()
    safe_text = py_html.escape(text)
    safe_sender = py_html.escape(sender)
    justify = 'flex-end' if outgoing else 'flex-start'
    
    # Màu sắc theo chuẩn Messenger
    bg = "#0084ff" if outgoing else "#e4e6ea"
    fg = "#ffffff" if outgoing else "#1c1e21"
    radius = "18px 18px 4px 18px" if outgoing else "18px 18px 18px 4px"
    
    return (
        f"<div style='display:flex; justify-content:{justify}; margin:2px 0; padding:0 12px;'>"
        f"  <div style='max-width:70%; background:{bg}; color:{fg}; padding:10px 14px; border-radius:{radius}; font-size:14px; line-height:1.4; box-shadow:0 1px 2px rgba(0,0,0,0.1);'>"
        f"    <div style='white-space:pre-wrap; margin-bottom:4px;'>{safe_text}</div>"
        f"    <div style='text-align:right; font-size:11px; opacity:.7; margin-top:4px; font-weight:normal;'>{ts}</div>"
        f"  </div>"
        f"</div>"
    )


class ClientWindow(QtWidgets.QMainWindow):
    """
    Cửa sổ chat chính với giao diện Messenger-style
    - Quản lý tin nhắn E2EE
    - Panel hiển thị thông tin mã hoá thời gian thực
    - Lưu trữ lịch sử chat
    """
    def __init__(self, display_name: str) -> None:
        super().__init__()
        self.setWindowTitle(f"Trò chuyện mã hoá - {display_name}")
        self.resize(1000, 620)

        self.display_name = display_name
        # Tạo cặp khoá X25519 mới cho mỗi phiên
        self.key_pair = KeyPair.generate()
        self.broker = InMemoryBroker.instance()
        
        # Đăng ký client với broker
        self.client_id = self.broker.register_client(
            display_name,
            public_key_bytes(self.key_pair.public_key),
            self._on_ciphertext_received,
        )

        self.peers: Dict[str, Peer] = {}
        self._setup_ui()
        self._ensure_data_dir()
        self._load_history()
        self._refresh_peers()

        # Timer cập nhật danh sách đối tác định kỳ
        self._peer_timer = QtCore.QTimer(self)
        self._peer_timer.setInterval(1200)  # 1.2 giây
        self._peer_timer.timeout.connect(self._refresh_peers)
        self._peer_timer.start()

    def _ensure_data_dir(self) -> None:
        """Tạo thư mục data nếu chưa tồn tại"""
        os.makedirs(DATA_DIR, exist_ok=True)

    def _history_path(self) -> str:
        """Đường dẫn file lịch sử chat"""
        return os.path.join(DATA_DIR, f"{_safe_filename(self.display_name)}.html")

    def _load_history(self) -> None:
        """Tải lịch sử chat từ file HTML"""
        path = self._history_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    html = f.read()
                self.chat_view.setHtml(html)
            except Exception:
                pass

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        """Xử lý khi đóng cửa sổ - lưu lịch sử và hủy đăng ký"""
        try:
            # Lưu lịch sử chat (không lưu khoá)
            html_content = self.chat_view.toHtml()
            html_content = _wrap_html_with_utf8_meta(html_content)
            with open(self._history_path(), "w", encoding="utf-8") as f:
                f.write(html_content)
        except Exception:
            pass
        
        # Hủy đăng ký khỏi broker
        self.broker.unregister_client(self.client_id)
        event.accept()

    def _setup_ui(self) -> None:
        """Thiết lập giao diện người dùng"""
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Header theo style Messenger
        header_container = QtWidgets.QWidget()
        header_container.setStyleSheet("QWidget { background: #ffffff; border-bottom: 1px solid #e4e6ea; }")
        header = QtWidgets.QHBoxLayout(header_container)
        header.setContentsMargins(16, 12, 16, 12)
        header.setSpacing(12)
        
        # Avatar người dùng
        profile_btn = QtWidgets.QPushButton("👤")
        profile_btn.setStyleSheet("QPushButton { background: #0084ff; color: white; border: none; border-radius: 20px; width: 40px; height: 40px; font-size: 18px; }")
        
        # Thông tin chat
        chat_info = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel(f"<b>{self.display_name}</b>")
        title.setStyleSheet("QLabel { color: #1c1e21; font-size: 16px; font-weight: bold; }")
        title.setTextFormat(QtCore.Qt.TextFormat.RichText)
        subtitle = QtWidgets.QLabel("Đang hoạt động")
        subtitle.setStyleSheet("QLabel { color: #65676b; font-size: 12px; }")
        chat_info.addWidget(title)
        chat_info.addWidget(subtitle)
        
        header.addWidget(profile_btn)
        header.addLayout(chat_info, 1)
        
        # Dropdown chọn đối tác
        peer_label = QtWidgets.QLabel("Gửi đến:")
        peer_label.setStyleSheet("QLabel { color: #65676b; font-size: 12px; }")
        self.peer_combo = QtWidgets.QComboBox()
        self.peer_combo.setStyleSheet("QComboBox { background: #f0f2f5; border: 1px-solid #e4e6ea; border-radius: 8px; padding: 4px 8px; color: #1c1e21; }")
        header.addWidget(peer_label)
        header.addWidget(self.peer_combo)
        
        layout.addWidget(header_container)

        # Tab chính
        tabs = QtWidgets.QTabWidget()
        layout.addWidget(tabs, 1)

        # Tab Chat với splitter: trái là tin nhắn, phải là panel E2EE
        chat_tab = QtWidgets.QWidget()
        chat_outer = QtWidgets.QHBoxLayout(chat_tab)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        chat_outer.addWidget(splitter)

        # Phần trái: tin nhắn + input
        left_holder = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_holder)

        # Khung hiển thị tin nhắn
        self.chat_view = QtWidgets.QTextBrowser()
        self.chat_view.setOpenLinks(False)
        self.chat_view.setStyleSheet("QTextBrowser { background: #f0f2f5; color: #1c1e21; border: none; padding: 8px; }")
        left_layout.addWidget(self.chat_view, 1)

        # Thanh nhập tin nhắn theo style Messenger
        input_container = QtWidgets.QWidget()
        input_container.setStyleSheet("QWidget { background: #ffffff; border-top: 1px solid #e4e6ea; }")
        input_row = QtWidgets.QHBoxLayout(input_container)
        input_row.setContentsMargins(16, 12, 16, 12)
        input_row.setSpacing(8)
        
        # Nút thêm file/ảnh
        plus_btn = QtWidgets.QPushButton("+")
        plus_btn.setStyleSheet("QPushButton { background: #0084ff; color: white; border: none; border-radius: 20px; width: 40px; height: 40px; font-size: 18px; font-weight: bold; }")
        
        # Ô nhập tin nhắn
        self.msg_edit = QtWidgets.QLineEdit()
        self.msg_edit.setPlaceholderText("Aa")
        self.msg_edit.setStyleSheet("QLineEdit { background: #f0f2f5; border: none; border-radius: 10px; padding: 8px 16px; font-size: 14px; }")
        self.msg_edit.returnPressed.connect(self._send_clicked)
        
        # Nút emoji
        emoji_btn = QtWidgets.QPushButton("😊")
        emoji_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 20px; }")
        
        # Nút gửi
        send_btn = QtWidgets.QPushButton("📤")
        send_btn.setStyleSheet("QPushButton { background: #0084ff; color: white; border: none; border-radius: 20px; width: 40px; height: 40px; font-size: 16px; }")
        send_btn.clicked.connect(self._send_clicked)
        
        input_row.addWidget(plus_btn)
        input_row.addWidget(self.msg_edit, 1)
        input_row.addWidget(emoji_btn)
        input_row.addWidget(send_btn)
        left_layout.addWidget(input_container)

        splitter.addWidget(left_holder)

        # Panel E2EE thời gian thực (bên phải)
        right_holder = QtWidgets.QWidget()
        right_holder.setMinimumWidth(250)
        right_holder.setMaximumWidth(350)
        right_layout = QtWidgets.QVBoxLayout(right_holder)
        right_layout.setContentsMargins(8, 8, 8, 8)
        
        # Tiêu đề panel E2EE
        right_title = QtWidgets.QLabel("E2EE thời gian thực")
        right_title.setStyleSheet("QLabel { font-weight:600; color:#1976d2; font-size:14px; margin-bottom:12px; padding:8px; background:#e3f2fd; border-radius:6px; }")
        right_layout.addWidget(right_title)
        
        # Các label hiển thị thông tin mã hoá
        self.live_peer = QtWidgets.QLabel("Đối tác: -")
        self.live_key = QtWidgets.QLabel("Băm khoá chung (SHA-256/8): -")
        self.live_nonce = QtWidgets.QLabel("Nonce: -")
        self.live_ct = QtWidgets.QLabel("Ciphertext: -")
        
        for w in [self.live_peer, self.live_key, self.live_nonce, self.live_ct]:
            w.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            w.setWordWrap(True)
            w.setMinimumHeight(60)  # Đặt chiều cao tối thiểu để có chỗ xuống dòng
            w.setMaximumHeight(120)  # Giới hạn chiều cao tối đa
            w.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
            # CSS cải thiện cho word wrap
            w.setStyleSheet("""
                QLabel { 
                    color: #1b5e20; 
                    background: #e8f5e8; 
                    padding: 12px; 
                    border-radius: 8px; 
                    margin: 6px 0; 
                    font-family: 'Consolas', 'Monaco', monospace; 
                    font-size: 11px; 
                    border: 1px solid #c8e6c9;
                    line-height: 1.4;
                }
            """)
            right_layout.addWidget(w)
        right_layout.addStretch(1)
        splitter.addWidget(right_holder)
        # Cải thiện splitter để kéo thả mượt mà hơn và hoạt động trong fullscreen
        splitter.setChildrenCollapsible(False)  # Không cho phép thu gọn hoàn toàn
        splitter.setHandleWidth(12)  # Tăng độ rộng handle để dễ kéo hơn
        splitter.setStretchFactor(0, 2)  # Chat area chiếm 2 phần
        splitter.setStretchFactor(1, 1)  # E2EE panel chiếm 1 phần
        
        # Đặt kích thước ban đầu theo tỷ lệ phần trăm
        def update_splitter_sizes():
            total_width = splitter.width()
            if total_width > 100:  # Đảm bảo có kích thước hợp lệ
                chat_width = int(total_width * 0.68)  # 68% cho chat
                panel_width = int(total_width * 0.32)  # 32% cho E2EE panel
                splitter.setSizes([chat_width, panel_width])
        
        # Kết nối với sự kiện resize để cập nhật kích thước
        splitter.splitterMoved.connect(lambda: None)  # Placeholder
        
        # Style cho splitter handle
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border: 2px solid #2196f3;
                border-radius: 6px;
                margin: 1px;
            }
            QSplitter::handle:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2196f3, stop:1 #1976d2);
                border: 2px solid #0d47a1;
            }
            QSplitter::handle:pressed {
                background: #1565c0;
                border: 2px solid #0d47a1;
            }
        """)
        
        # Gọi update_splitter_sizes sau khi widget được hiển thị
        QtCore.QTimer.singleShot(100, update_splitter_sizes)

        tabs.addTab(chat_tab, "Chat")

        # Tab giải thích E2EE
        explain_tab = QtWidgets.QWidget()
        explain_layout = QtWidgets.QVBoxLayout(explain_tab)
        
        # Khung hiển thị giải thích
        self.explain_text = QtWidgets.QTextBrowser()
        self.explain_text.setStyleSheet("QTextBrowser { background: #0f1528; color: #cfd8dc; border-radius: 8px; padding: 10px; }")
        explain_layout.addWidget(self.explain_text)

        # Nhóm minh hoạ trực quan
        demo_group = QtWidgets.QGroupBox("Minh hoạ trực quan")
        demo_layout = QtWidgets.QVBoxLayout(demo_group)
        
        # Ô nhập tin nhắn mẫu
        self.demo_input = QtWidgets.QLineEdit()
        self.demo_input.setPlaceholderText("Nhập tin nhắn mẫu để minh hoạ mã hoá…")
        
        # Nút chạy demo
        self.demo_btn = QtWidgets.QPushButton("Tạo khoá chung & Mã hoá minh hoạ")
        self.demo_btn.clicked.connect(self._run_demo)
        
        # Khung hiển thị kết quả demo
        self.demo_output = QtWidgets.QTextEdit()
        self.demo_output.setReadOnly(True)
        self.demo_output.setStyleSheet("QTextEdit { background: #0b1020; color: #e8eaf6; border-radius: 8px; padding: 8px; font-family: monospace; }")
        self.demo_output.setWordWrapMode(QtGui.QTextOption.WrapMode.WrapAnywhere)
        self.demo_output.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.WidgetWidth)
        
        demo_layout.addWidget(self.demo_input)
        demo_layout.addWidget(self.demo_btn)
        demo_layout.addWidget(self.demo_output)

        explain_layout.addWidget(demo_group)
        tabs.addTab(explain_tab, "Giải thích E2EE")

        # Label hiển thị trạng thái với hiệu ứng fade
        self.status_label = FadeLabel("")
        self.status_label.setStyleSheet("QLabel { color: #65676b; font-size: 12px; padding: 8px 16px; }")
        layout.addWidget(self.status_label)

        self._update_explain()

        # Áp dụng theme Messenger cho toàn bộ cửa sổ
        style = (
            "QMainWindow { background: #f0f2f5; }"
            "QLabel, QListWidget, QLineEdit { color: #1c1e21; font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }"
            "QPushButton { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }"
            "QPushButton:hover { background:#2e8fff; }"
            "QTabWidget::pane { border: none; background: #ffffff; }"
            "QTabBar::tab { background: #f0f2f5; color: #65676b; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 8px; border-top-right-radius: 8px; }"
            "QTabBar::tab:selected { background: #ffffff; color: #1c1e21; border-bottom: 2px solid #0084ff; }"
            "QTextBrowser, QTextEdit { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }"
        )
        self.setStyleSheet(style)

    def _animate_status(self, text: str) -> None:
        """Hiển thị thông báo trạng thái với hiệu ứng fade in"""
        self.status_label.setText(text)
        anim = QtCore.QPropertyAnimation(self.status_label, b"opacity")
        anim.setDuration(900)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutQuad)
        anim.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _refresh_peers(self) -> None:
        """Cập nhật danh sách đối tác có thể chat"""
        current_cid = self.peer_combo.currentData()
        current_text = self.peer_combo.currentText()

        self.peer_combo.blockSignals(True)
        self.peer_combo.clear()
        self.peers.clear()
        
        # Lấy danh sách client từ broker
        for cid, reg in self.broker.list_clients().items():
            if cid == self.client_id:
                continue
            peer = Peer(client_id=cid, display_name=reg.display_name, public_key_bytes=reg.public_key_bytes)
            self.peers[cid] = peer
            self.peer_combo.addItem(peer.display_name, userData=cid)

        # Khôi phục lựa chọn trước đó
        if current_cid in self.peers:
            idx = self.peer_combo.findData(current_cid)
            if idx >= 0:
                self.peer_combo.setCurrentIndex(idx)
        elif current_text:
            idx = self.peer_combo.findText(current_text)
            if idx >= 0:
                self.peer_combo.setCurrentIndex(idx)
        self.peer_combo.blockSignals(False)

    def _update_explain(self) -> None:
        """Cập nhật nội dung giải thích E2EE với khoá công khai hiện tại"""
        pub_hex = public_key_bytes(self.key_pair.public_key).hex()
        self.explain_text.setHtml(
            """
            <h3>E2EE là gì?</h3>
            <p>E2EE (mã hoá đầu-cuối) đảm bảo chỉ người gửi và người nhận mới đọc được nội dung. Hệ thống chuyển tiếp (broker) chỉ thấy bản mã.</p>
            <h4>Các bước trong demo</h4>
            <ol>
              <li>Mỗi người dùng tạo một cặp khoá X25519 khi mở ứng dụng.</li>
              <li>Gửi tin: dùng <b>khoá bí mật của bạn</b> + <b>khoá công khai của người nhận</b> để tạo <i>mật chung</i> (X25519).</li>
              <li>Dùng HKDF-SHA256 để sinh <b>khoá AES-256</b> từ mật chung.</li>
              <li>Mã hoá tin nhắn bằng <b>AES-GCM</b> → sinh <i>nonce</i> và <i>ciphertext</i>.</li>
              <li>Người nhận dùng <b>khoá bí mật của họ</b> + <b>khoá công khai của bạn</b> để tạo cùng mật chung → giải mã được.</li>
            </ol>
            <p><b>Khoá công khai của bạn (hex):</b></p>
            <code style='display:block; background:#1a1a1a; padding:8px; border-radius:4px;'>%s</code>
            <p><i>Lưu ý:</i> Khoá được tạo mới mỗi phiên; lịch sử chat được lưu, nhưng khoá <u>không</u> lưu.</p>
            """ % pub_hex
        )

    def _append_chat_bubble(self, sender: str, text: str, outgoing: bool) -> None:
        """Thêm bubble tin nhắn vào khung chat"""
        self.chat_view.append(_format_bubble(sender, text, outgoing))

    def _set_live_e2ee(self, peer_name: str, shared_key: bytes, nonce: bytes, ciphertext: bytes) -> None:
        """Cập nhật panel E2EE thời gian thực với thông tin mã hoá"""
        # Tạo hash ngắn của khoá chung để hiển thị
        digest = hashes.Hash(hashes.SHA256())
        digest.update(shared_key)
        key_hash = digest.finalize().hex()[:16]
        
        self.live_peer.setText(f"Đối tác: {peer_name}")
        self.live_key.setText(f"Băm khoá chung (SHA-256/8): {key_hash}")
        self.live_nonce.setText(f"Nonce: {nonce.hex()}")
        self.live_ct.setText(f"Ciphertext: {ciphertext.hex()}")

    def _current_peer(self) -> Optional[Peer]:
        """Lấy đối tác hiện tại được chọn"""
        idx = self.peer_combo.currentIndex()
        if idx < 0:
            return None
        cid = self.peer_combo.itemData(idx)
        return self.peers.get(cid)

    def _send_clicked(self) -> None:
        """Xử lý khi nhấn nút gửi tin nhắn"""
        peer = self._current_peer()
        if peer is None:
            self._animate_status("Chọn một đối tác để gửi.")
            return
            
        text = self.msg_edit.text().strip()
        if not text:
            return
            
        self.msg_edit.clear()

        # Tạo khoá chung và mã hoá tin nhắn
        peer_pub = X25519PublicKey.from_public_bytes(peer.public_key_bytes)
        aes_key = derive_shared_key(self.key_pair.private_key, peer_pub)
        nonce, ciphertext = encrypt_message(aes_key, text.encode("utf-8"))

        # Hiển thị tin nhắn và cập nhật panel E2EE
        self._append_chat_bubble("Bạn → " + peer.display_name, text, outgoing=True)
        self._set_live_e2ee(peer.display_name, aes_key, nonce, ciphertext)

        # Gửi qua broker
        self.broker.send_ciphertext(
            from_client_id=self.client_id,
            to_client_id=peer.client_id,
            from_public_key_bytes=public_key_bytes(self.key_pair.public_key),
            nonce=nonce,
            ciphertext=ciphertext,
        )
        self._animate_status("Đã gửi bản mã qua broker.")

    def _on_ciphertext_received(self, from_client_id: str, from_public_key_bytes: bytes, nonce: bytes, ciphertext: bytes) -> None:
        """Xử lý khi nhận được tin nhắn mã hoá"""
        try:
            # Giải mã tin nhắn
            from_pub = X25519PublicKey.from_public_bytes(from_public_key_bytes)
            aes_key = derive_shared_key(self.key_pair.private_key, from_pub)
            plaintext = decrypt_message(aes_key, nonce, ciphertext)
            
            # Hiển thị tin nhắn và cập nhật panel E2EE
            sender_name = self.broker.clients.get(from_client_id).display_name if from_client_id in self.broker.clients else "?"
            self._append_chat_bubble(sender_name + " → Bạn", plaintext.decode('utf-8'), outgoing=False)
            self._set_live_e2ee(sender_name, aes_key, nonce, ciphertext)
            self._animate_status("Đã nhận bản mã và giải mã cục bộ.")
        except Exception as exc:  # noqa: BLE001
            self.chat_view.append(f"<div style='color:#ef9a9a'>Lỗi giải mã: {py_html.escape(str(exc))}</div>")

    def _run_demo(self) -> None:
        """Chạy demo minh hoạ quá trình E2EE"""
        msg = self.demo_input.text().strip() or "Xin chào, đây là minh hoạ E2EE!"
        
        # Tạo một cặp khoá tạm cho "Người A" và "Người B" để minh hoạ
        a = KeyPair.generate()
        b = KeyPair.generate()
        a_pub_hex = public_key_bytes(a.public_key).hex()
        b_pub_hex = public_key_bytes(b.public_key).hex()

        # Cả hai phía đều suy ra cùng một khoá AES từ X25519 + HKDF
        k_ab = derive_shared_key(a.private_key, b.public_key)
        k_ba = derive_shared_key(b.private_key, a.public_key)
        same = "ĐÚNG" if k_ab == k_ba else "SAI"

        # Mã hoá và giải mã demo
        nonce, ct = encrypt_message(k_ab, msg.encode("utf-8"))
        pt = decrypt_message(k_ba, nonce, ct).decode("utf-8")

        self.demo_output.setPlainText(
            "\n".join([
                "Khoá công khai A (hex): " + a_pub_hex,
                "Khoá công khai B (hex): " + b_pub_hex,
                "Hai bên tạo cùng khoá AES? → " + same,
                "Nonce (hex): " + nonce.hex(),
                "Ciphertext (hex): " + ct.hex(),
                "Giải mã ra: " + pt,
            ])
        )


class Launcher(QtWidgets.QMainWindow):
    """
    Cửa sổ launcher chính để tạo và quản lý các cửa sổ chat
    - Tạo cửa sổ chat mới
    - Hiển thị lịch sử chat với avatar
    - Mở lại chat cũ
    """
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Trò chuyện mã hoá - Trình khởi chạy")
        self.resize(520, 400)
        self._windows: list[ClientWindow] = []
        self._chat_history: list[dict] = []
        self._setup_ui()
        self._load_chat_history()

    def _setup_ui(self) -> None:
        """Thiết lập giao diện launcher"""
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Hướng dẫn sử dụng
        label = QtWidgets.QLabel("Tạo nhiều cửa sổ chat để trò chuyện ngoại tuyến và trải nghiệm E2EE (ngoại tuyến).")
        label.setWordWrap(True)
        layout.addWidget(label)

        # Form tạo cửa sổ chat mới
        form = QtWidgets.QHBoxLayout()
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Nhập tên hiển thị (vd: Alice)")
        add_btn = QtWidgets.QPushButton("Mở cửa sổ chat")
        add_btn.clicked.connect(self._spawn_window)
        form.addWidget(self.name_edit, 1)
        form.addWidget(add_btn)
        layout.addLayout(form)

        # Danh sách lịch sử chat với avatar
        history_label = QtWidgets.QLabel("Lịch sử chat:")
        history_label.setStyleSheet("QLabel { font-weight: bold; color: #1c1e21; margin-top: 10px; }")
        layout.addWidget(history_label)
        
        # List widget hiển thị lịch sử chat
        self.clients_list = QtWidgets.QListWidget()
        self.clients_list.setStyleSheet("""
            QListWidget { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 2px solid #e9ecef;
                border-radius: 16px;
                padding: 12px;
                selection-background-color: transparent;
            }
            QListWidget::item { 
                border-radius: 12px;
                margin: 6px 0px;
                background: transparent;
            }
            QListWidget::item:hover { 
                background: transparent; 
            }
            QListWidget::item:selected { 
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f1f3f4;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c1c8cd;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a8b2ba;
            }
        """)
        self.clients_list.itemClicked.connect(self._open_chat_history)
        layout.addWidget(self.clients_list, 1)

        # Áp dụng theme hiện đại cho launcher
        style = (
            "QMainWindow { "
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
                "stop:0 #4facfe, stop:1 #00f2fe); "
                "border-radius: 0px; "
            "}"
            "QLabel, QListWidget, QLineEdit { "
                "color: #2c3e50; "
                "font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif; "
            "}"
            "QPushButton { "
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                "stop:0 #ff6b6b, stop:1 #ee5a52); "
                "color: white; "
                "border: none; "
                "border-radius: 25px; "
                "padding: 14px 28px; "
                "font-weight: 700; "
                "font-size: 15px; "
                "font-family: 'Segoe UI', 'Roboto', sans-serif; "
                "text-transform: uppercase; "
                "letter-spacing: 1px; "
            "}"
            "QPushButton:hover { "
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                "stop:0 #ff5252, stop:1 #d32f2f); "
                "border: 3px solid rgba(255, 255, 255, 0.4); "
            "}"
            "QPushButton:pressed { "
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                "stop:0 #d32f2f, stop:1 #b71c1c); "
                "padding: 15px 29px; "
            "}"
            "QLineEdit { "
                "background: rgba(255, 255, 255, 0.9); "
                "border: 2px solid rgba(255, 255, 255, 0.3); "
                "border-radius: 12px; "
                "padding: 12px 16px; "
                "font-size: 14px; "
            "}"
            "QLineEdit:focus { "
                "border: 2px solid #667eea; "
                "background: white; "
            "}"
            "QTabWidget::pane { border: none; background: rgba(255, 255, 255, 0.95); border-radius: 16px; }"
            "QTabBar::tab { "
                "background: rgba(255, 255, 255, 0.7); "
                "color: #65676b; "
                "padding: 12px 20px; "
                "margin-right: 4px; "
                "border-top-left-radius: 12px; "
                "border-top-right-radius: 12px; "
                "font-weight: 500; "
            "}"
            "QTabBar::tab:selected { "
                "background: rgba(255, 255, 255, 0.95); "
                "color: #2c3e50; "
                "border-bottom: 3px solid #667eea; "
            "}"
            "QTextBrowser, QTextEdit { "
                "font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif; "
                "background: rgba(255, 255, 255, 0.9); "
                "border-radius: 12px; "
            "}"
        )
        self.setStyleSheet(style)

    def _load_chat_history(self) -> None:
        """Tải lịch sử chat từ thư mục data"""
        if not os.path.exists(DATA_DIR):
            return
        
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.html'):
                name = filename[:-5]  # Bỏ phần mở rộng .html
                # Giữ nguyên tên gốc, chỉ thay dấu gạch ngang bằng khoảng trắng
                display_name = name.replace('-', ' ')
                self._add_chat_history_item(display_name, filename)
    
    def _add_chat_history_item(self, display_name: str, filename: str) -> None:
        """Thêm item lịch sử chat vào danh sách với avatar"""
        item = QtWidgets.QListWidgetItem()
        
        # Tạo widget tùy chỉnh với avatar và thông tin
        widget = QtWidgets.QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 12px;
                margin: 2px;
            }
            QWidget:hover {
                background: rgba(255, 255, 255, 1.0);
                border: 1px solid rgba(33, 150, 243, 0.3);
                margin: 1px;
            }
        """)
        
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)  # Margin đều để căn giữa
        layout.setSpacing(16)  # Khoảng cách vừa phải
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)  # Căn giữa theo chiều dọc
        
        # Avatar với gradient đẹp
        first_letter = display_name[0].upper() if display_name else "?"
        avatar = QtWidgets.QLabel(first_letter)
        
        # Tạo gradient màu dựa trên chữ cái đầu
        colors = {
            'A': '#e74c3c', 'B': '#3498db', 'C': '#9b59b6', 'D': '#2ecc71', 'E': '#f39c12',
            'F': '#e91e63', 'G': '#00bcd4', 'H': '#673ab7', 'I': '#ff5722', 'J': '#795548',
            'K': '#607d8b', 'L': '#ff9800', 'M': '#4caf50', 'N': '#2196f3', 'O': '#9c27b0',
            'P': '#ff6f00', 'Q': '#8bc34a', 'R': '#f44336', 'S': '#009688', 'T': '#ffc107',
            'U': '#3f51b5', 'V': '#cddc39', 'W': '#ff5252', 'X': '#4db6ac', 'Y': '#ffa726',
            'Z': '#ab47bc'
        }
        avatar_color = colors.get(first_letter, '#0084ff')
        
        avatar.setStyleSheet(f"""
            QLabel {{ 
                font-size: 20px; 
                font-weight: bold; 
                color: white; 
                background: {avatar_color};
                border-radius: 25px;
                min-width: 50px;
                min-height: 50px;
                border: 2px solid rgba(255, 255, 255, 0.8);
            }}
        """)
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Tên hiển thị với typography đẹp
        name_label = QtWidgets.QLabel(display_name)
        name_label.setStyleSheet("""
            QLabel { 
                font-weight: 600; 
                color: #2c3e50; 
                font-size: 16px;
                padding: 0px;
                margin: 0px;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
        """)
        name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        name_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        
        # Thêm icon trạng thái
        status_icon = QtWidgets.QLabel("💬")
        status_icon.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #27ae60;
                padding: 4px;
            }
        """)
        status_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        status_icon.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred)
        
        layout.addWidget(avatar)
        layout.addWidget(name_label, 1)
        layout.addWidget(status_icon)
        
        # Đặt kích thước tối thiểu cho item - chiều cao vừa phải để căn giữa đẹp
        item.setSizeHint(QtCore.QSize(300, 82))
        # Lưu cả filename và display_name
        item.setData(QtCore.Qt.ItemDataRole.UserRole, filename)
        item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, display_name)
        self.clients_list.addItem(item)
        self.clients_list.setItemWidget(item, widget)
    
    def _open_chat_history(self, item: QtWidgets.QListWidgetItem) -> None:
        """Mở cửa sổ chat với lịch sử"""
        filename = item.data(QtCore.Qt.ItemDataRole.UserRole)
        display_name = item.data(QtCore.Qt.ItemDataRole.UserRole + 1)
        
        if not filename or not display_name:
            return
        
        # Tạo cửa sổ mới và tải lịch sử
        win = ClientWindow(display_name)
        win.show()
        self._windows.append(win)
    
    def _spawn_window(self) -> None:
        """Tạo cửa sổ chat mới"""
        name = self.name_edit.text().strip() or f"Người dùng {len(self._windows) + 1}"
        win = ClientWindow(name)
        win.show()
        self._windows.append(win)
        
        # Thêm vào danh sách lịch sử (chỉ nếu chưa có)
        safe_name = _safe_filename(name)
        filename = f"{safe_name}.html"
        
        # Kiểm tra xem đã có trong danh sách chưa
        existing_items = []
        for i in range(self.clients_list.count()):
            item = self.clients_list.item(i)
            if item and item.data(QtCore.Qt.ItemDataRole.UserRole) == filename:
                existing_items.append(item)
        
        if not existing_items:
            self._add_chat_history_item(name, filename)
        
        self.name_edit.clear()
