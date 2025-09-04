"""
Mô-đun transport cho ứng dụng chat E2EE
- Quản lý broker trong bộ nhớ để chuyển tiếp tin nhắn
- Đăng ký/hủy đăng ký client
- Chuyển tiếp bản mã giữa các client
"""

from __future__ import annotations

from typing import Callable, Dict, Optional
from dataclasses import dataclass
import uuid

# Type alias cho callback nhận tin nhắn mã hoá
CipherDelivery = Callable[[str, bytes, bytes, bytes], None]
# Signature: from_client_id, peer_public_key_bytes, nonce, ciphertext


@dataclass
class ClientRegistration:
    """
    Thông tin đăng ký client trong broker
    - client_id: ID duy nhất của client
    - display_name: Tên hiển thị của client
    - public_key_bytes: Khoá công khai X25519
    - deliver: Callback để nhận tin nhắn mã hoá
    """
    client_id: str
    display_name: str
    public_key_bytes: bytes
    deliver: CipherDelivery


class InMemoryBroker:
    """
    Broker trong bộ nhớ để chuyển tiếp tin nhắn E2EE
    - Singleton pattern để đảm bảo chỉ có 1 broker
    - Quản lý danh sách client đã đăng ký
    - Chuyển tiếp bản mã giữa các client
    """
    _instance: Optional["InMemoryBroker"] = None

    def __init__(self) -> None:
        """Khởi tạo broker với danh sách client trống"""
        self.clients: Dict[str, ClientRegistration] = {}

    @classmethod
    def instance(cls) -> "InMemoryBroker":
        """
        Lấy instance duy nhất của broker (Singleton pattern)
        Returns:
            InMemoryBroker: Instance duy nhất của broker
        """
        if cls._instance is None:
            cls._instance = InMemoryBroker()
        return cls._instance

    def register_client(self, display_name: str, public_key_bytes: bytes, deliver: CipherDelivery) -> str:
        """
        Đăng ký client mới vào broker
        Args:
            display_name: Tên hiển thị của client
            public_key_bytes: Khoá công khai X25519
            deliver: Callback để nhận tin nhắn
        Returns:
            str: Client ID duy nhất được tạo
        """
        client_id = str(uuid.uuid4())
        self.clients[client_id] = ClientRegistration(
            client_id=client_id,
            display_name=display_name,
            public_key_bytes=public_key_bytes,
            deliver=deliver,
        )
        return client_id

    def unregister_client(self, client_id: str) -> None:
        """
        Hủy đăng ký client khỏi broker
        Args:
            client_id: ID của client cần hủy đăng ký
        """
        self.clients.pop(client_id, None)

    def list_clients(self) -> Dict[str, ClientRegistration]:
        """
        Lấy danh sách tất cả client đã đăng ký
        Returns:
            Dict[str, ClientRegistration]: Dictionary chứa tất cả client
        """
        return dict(self.clients)

    def send_ciphertext(self, from_client_id: str, to_client_id: str, from_public_key_bytes: bytes, nonce: bytes, ciphertext: bytes) -> None:
        """
        Chuyển tiếp bản mã từ client này sang client khác
        Args:
            from_client_id: ID của client gửi
            to_client_id: ID của client nhận
            from_public_key_bytes: Khoá công khai của client gửi
            nonce: Nonce đã sử dụng khi mã hoá
            ciphertext: Bản mã cần chuyển tiếp
        """
        if to_client_id not in self.clients:
            return
        
        # Lấy thông tin client nhận và gửi tin nhắn
        registration = self.clients[to_client_id]
        registration.deliver(from_client_id, from_public_key_bytes, nonce, ciphertext)
