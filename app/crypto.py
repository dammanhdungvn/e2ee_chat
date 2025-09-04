"""
Mô-đun mã hoá E2EE cho ứng dụng chat
- Tạo cặp khoá X25519
- Trao đổi khoá Diffie-Hellman
- Mã hoá/giải mã AES-GCM
- Sử dụng HKDF để tạo khoá AES từ shared secret
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import os

# Các hằng số cho HKDF và AES
HKDF_SALT = b"e2ee-mini-chat-hkdf-salt"  # Salt cho HKDF
HKDF_INFO = b"e2ee-mini-chat-session-key"  # Info cho HKDF
AES_KEY_BYTES = 32  # 256-bit AES key
NONCE_BYTES = 12  # 96-bit nonce cho AES-GCM


@dataclass
class KeyPair:
    """
    Cặp khoá X25519 cho mã hoá E2EE
    - private_key: Khoá bí mật (không bao giờ chia sẻ)
    - public_key: Khoá công khai (có thể chia sẻ an toàn)
    """
    private_key: X25519PrivateKey
    public_key: X25519PublicKey

    @staticmethod
    def generate() -> "KeyPair":
        """
        Tạo cặp khoá X25519 mới
        Returns:
            KeyPair: Cặp khoá mới được tạo
        """
        private_key = X25519PrivateKey.generate()
        public_key = private_key.public_key()
        return KeyPair(private_key=private_key, public_key=public_key)

    def public_bytes(self) -> bytes:
        """
        Chuyển đổi khoá công khai thành bytes
        Returns:
            bytes: Khoá công khai dạng raw bytes
        """
        return self.public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)


def public_key_bytes(pub: X25519PublicKey) -> bytes:
    """
    Chuyển đổi khoá công khai X25519 thành bytes
    Args:
        pub: Khoá công khai X25519
    Returns:
        bytes: Khoá công khai dạng raw bytes
    """
    return pub.public_bytes(Encoding.Raw, PublicFormat.Raw)


def derive_shared_key(own_private: X25519PrivateKey, peer_public: X25519PublicKey) -> bytes:
    """
    Tạo khoá AES chung từ cặp khoá X25519 bằng ECDH + HKDF
    Args:
        own_private: Khoá bí mật của mình
        peer_public: Khoá công khai của đối tác
    Returns:
        bytes: Khoá AES 256-bit được tạo từ shared secret
    """
    # Trao đổi khoá Diffie-Hellman
    shared_secret = own_private.exchange(peer_public)
    
    # Sử dụng HKDF để tạo khoá AES từ shared secret
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=AES_KEY_BYTES,
        salt=HKDF_SALT,
        info=HKDF_INFO,
    )
    return hkdf.derive(shared_secret)


def encrypt_message(aes_key: bytes, plaintext: bytes, aad: bytes | None = None) -> Tuple[bytes, bytes]:
    """
    Mã hoá tin nhắn bằng AES-GCM
    Args:
        aes_key: Khoá AES 256-bit
        plaintext: Tin nhắn gốc cần mã hoá
        aad: Additional Authenticated Data (tùy chọn)
    Returns:
        Tuple[bytes, bytes]: (nonce, ciphertext) - nonce và bản mã
    """
    # Tạo nonce ngẫu nhiên
    nonce = os.urandom(NONCE_BYTES)
    
    # Mã hoá bằng AES-GCM
    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
    
    return nonce, ciphertext


def decrypt_message(aes_key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes | None = None) -> bytes:
    """
    Giải mã tin nhắn bằng AES-GCM
    Args:
        aes_key: Khoá AES 256-bit
        nonce: Nonce đã sử dụng khi mã hoá
        ciphertext: Bản mã cần giải mã
        aad: Additional Authenticated Data (tùy chọn)
    Returns:
        bytes: Tin nhắn gốc đã được giải mã
    Raises:
        InvalidTag: Nếu xác thực thất bại (tin nhắn bị sửa đổi)
    """
    aesgcm = AESGCM(aes_key)
    return aesgcm.decrypt(nonce, ciphertext, aad)
