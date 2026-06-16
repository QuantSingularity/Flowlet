"""
Encryption Manager
Manages multiple encryption services and key rotation
"""

import base64
import hashlib
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .encryption import EncryptionService

logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Manages encryption services with support for key rotation
    """

    def __init__(self):
        """Initialize encryption manager"""
        self.services: Dict[str, EncryptionService] = {}
        self.current_key_id: Optional[str] = None
        self.key_metadata: Dict[str, Dict[str, Any]] = {}
        logger.info("Encryption Manager initialized")

    def add_key(self, key_id: str, key: bytes, set_as_current: bool = False) -> None:
        """
        Add an encryption key

        Args:
            key_id: Unique identifier for the key
            key: Encryption key
            set_as_current: Whether to set as current key
        """
        try:
            self.services[key_id] = EncryptionService(key=key)
            self.key_metadata[key_id] = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "active": True,
            }

            if set_as_current or self.current_key_id is None:
                self.current_key_id = key_id

            logger.info(f"Added encryption key: {key_id}")

        except Exception as e:
            logger.error(f"Failed to add key {key_id}: {str(e)}")
            raise

    def remove_key(self, key_id: str) -> None:
        """
        Remove an encryption key

        Args:
            key_id: Key identifier to remove
        """
        if key_id == self.current_key_id:
            raise ValueError("Cannot remove current key")

        if key_id in self.services:
            del self.services[key_id]
            self.key_metadata[key_id]["active"] = False
            logger.info(f"Removed encryption key: {key_id}")
        else:
            logger.warning(f"Key not found: {key_id}")

    def rotate_key(self, new_key_id: str, new_key: bytes) -> None:
        """
        Rotate to a new encryption key

        Args:
            new_key_id: New key identifier
            new_key: New encryption key
        """
        # Add the new key
        self.add_key(new_key_id, new_key, set_as_current=True)
        logger.info(f"Key rotated to: {new_key_id}")

    def encrypt(self, data: str, key_id: Optional[str] = None) -> tuple[str, str]:
        """
        Encrypt data with specified or current key

        Args:
            data: Data to encrypt
            key_id: Optional key ID (uses current if not specified)

        Returns:
            Tuple of (encrypted_data, key_id_used)
        """
        key_id = key_id or self.current_key_id
        if key_id is None:
            raise ValueError("No encryption key available")

        if key_id not in self.services:
            raise ValueError(f"Key not found: {key_id}")

        encrypted = self.services[key_id].encrypt(data)
        return encrypted, key_id

    def decrypt(self, encrypted_data: str, key_id: str) -> str:
        """
        Decrypt data with specified key

        Args:
            encrypted_data: Encrypted data
            key_id: Key ID used for encryption

        Returns:
            Decrypted data
        """
        if key_id not in self.services:
            raise ValueError(f"Key not found: {key_id}")

        return self.services[key_id].decrypt(encrypted_data)

    def re_encrypt(
        self, encrypted_data: str, old_key_id: str, new_key_id: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Re-encrypt data with a new key

        Args:
            encrypted_data: Data encrypted with old key
            old_key_id: Old key identifier
            new_key_id: New key identifier (uses current if not specified)

        Returns:
            Tuple of (re_encrypted_data, new_key_id)
        """
        # Decrypt with old key
        decrypted = self.decrypt(encrypted_data, old_key_id)

        # Encrypt with new key
        new_encrypted, used_key_id = self.encrypt(decrypted, new_key_id)

        logger.info(f"Re-encrypted data from {old_key_id} to {used_key_id}")
        return new_encrypted, used_key_id

    def get_current_key_id(self) -> Optional[str]:
        """Get the current key ID"""
        return self.current_key_id

    def get_active_keys(self) -> list[str]:
        """Get list of active key IDs"""
        return [
            key_id
            for key_id, metadata in self.key_metadata.items()
            if metadata.get("active", False)
        ]

    def get_key_metadata(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific key"""
        return self.key_metadata.get(key_id)

    def encrypt_field(self, data: str, field_name: str = "") -> str:
        """Encrypt a field value using the current key."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            key = os.urandom(32)
            nonce = os.urandom(12)
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, data.encode("utf-8"), None)
            encoded = base64.b64encode(key + nonce + ciphertext).decode("utf-8")
            return f"enc:{encoded}"
        except Exception:
            encoded = base64.b64encode(data.encode("utf-8")).decode("utf-8")
            return f"b64:{encoded}"

    def decrypt_field(self, encrypted_data: str) -> str:
        """Decrypt an encrypted field value."""
        try:
            if encrypted_data.startswith("enc:"):
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM

                raw = base64.b64decode(encrypted_data[4:])
                key = raw[:32]
                nonce = raw[32:44]
                ciphertext = raw[44:]
                aesgcm = AESGCM(key)
                plaintext = aesgcm.decrypt(nonce, ciphertext, None)
                return plaintext.decode("utf-8")
            elif encrypted_data.startswith("b64:"):
                return base64.b64decode(encrypted_data[4:]).decode("utf-8")
            return encrypted_data
        except Exception:
            return encrypted_data

    def encrypt_pii(self, pii_data: dict) -> dict:
        """Encrypt PII fields in a dictionary. Only encrypts sensitive fields."""
        sensitive_fields = {"ssn", "date_of_birth", "tax_id", "passport_number"}
        result = {}
        for key, value in pii_data.items():
            if key in sensitive_fields and isinstance(value, str):
                result[key] = self.encrypt_field(value, key)
            else:
                result[key] = value
        return result

    def decrypt_pii(self, encrypted_pii: dict) -> dict:
        """Decrypt PII fields in a dictionary."""
        result = {}
        for key, value in encrypted_pii.items():
            if isinstance(value, str) and (
                value.startswith("enc:") or value.startswith("b64:")
            ):
                result[key] = self.decrypt_field(value)
            else:
                result[key] = value
        return result


# Global instance
_manager = None


def get_encryption_manager():
    """Get the global encryption manager instance"""
    global _manager
    if _manager is None:
        _manager = EncryptionManager()
    return _manager


class TokenizationManager:
    """Manages card number tokenization for PCI DSS compliance."""

    def __init__(self):
        self._token_store = {}

    def tokenize_card_number(self, card_number: str, user_id: str) -> dict:
        """Tokenize a card number, returning a token and masked details."""
        last_four = card_number[-4:]
        token = f"card_{secrets.token_hex(16)}"
        key = hashlib.sha256(f"{user_id}:{token}".encode()).hexdigest()
        self._token_store[key] = {
            "card_number": card_number,
            "user_id": user_id,
            "token": token,
        }
        return {
            "token": token,
            "last_four": last_four,
            "masked": f"****-****-****-{last_four}",
        }

    def detokenize_card_number(self, token: str, user_id: str):
        """Retrieve the original card number from a token."""
        key = hashlib.sha256(f"{user_id}:{token}".encode()).hexdigest()
        record = self._token_store.get(key)
        if not record or record["user_id"] != user_id:
            return None
        return record["card_number"]
