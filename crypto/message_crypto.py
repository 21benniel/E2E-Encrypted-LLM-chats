"""
Message Encryption/Decryption Module for Encrypted LLM Chat

Provides secure message encryption using RSA/ECC with hybrid encryption
(RSA/ECC for key exchange, AES for actual data encryption).
"""

import os
import json
import base64
from typing import Dict, Any, Union

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography import x509


class MessageCrypto:
    """Handles encryption and decryption of messages using hybrid cryptography."""
    
    def __init__(self):
        """Initialize MessageCrypto."""
        pass
    
    def _generate_aes_key(self) -> bytes:
        """Generate a random 256-bit AES key."""
        return os.urandom(32)  # 256 bits
    
    def _encrypt_aes(self, data: bytes, key: bytes) -> Dict[str, str]:
        """Encrypt data using AES-GCM."""
        # Generate random IV
        iv = os.urandom(12)  # 96 bits for GCM
        
        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        
        # Encrypt data
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'iv': base64.b64encode(iv).decode(),
            'tag': base64.b64encode(encryptor.tag).decode()
        }
    
    def _decrypt_aes(self, encrypted_data: Dict[str, str], key: bytes) -> bytes:
        """Decrypt data using AES-GCM."""
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        iv = base64.b64decode(encrypted_data['iv'])
        tag = base64.b64decode(encrypted_data['tag'])
        
        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()
        
        # Decrypt data
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext
    
    def _encrypt_key_rsa(self, aes_key: bytes, public_key: rsa.RSAPublicKey) -> str:
        """Encrypt AES key using RSA public key."""
        encrypted_key = public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted_key).decode()
    
    def _decrypt_key_rsa(self, encrypted_key: str, private_key: rsa.RSAPrivateKey) -> bytes:
        """Decrypt AES key using RSA private key."""
        encrypted_key_bytes = base64.b64decode(encrypted_key)
        aes_key = private_key.decrypt(
            encrypted_key_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return aes_key
    
    def _encrypt_key_ecc(self, aes_key: bytes, public_key: ec.EllipticCurvePublicKey) -> str:
        """Encrypt AES key using ECC (ECIES-like approach with HKDF)."""
        # Generate ephemeral key pair
        ephemeral_private_key = ec.generate_private_key(ec.SECP256R1())
        ephemeral_public_key = ephemeral_private_key.public_key()
        
        # Perform ECDH
        shared_key = ephemeral_private_key.exchange(ec.ECDH(), public_key)
        
        # Derive encryption key using HKDF
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'encrypted-llm-chat-key-derivation'
        ).derive(shared_key)
        
        # Encrypt AES key using derived key
        encrypted_aes = self._encrypt_aes(aes_key, derived_key)
        
        # Serialize ephemeral public key
        ephemeral_public_pem = ephemeral_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Combine ephemeral public key and encrypted AES key
        result = {
            'ephemeral_public_key': base64.b64encode(ephemeral_public_pem).decode(),
            'encrypted_aes_key': encrypted_aes
        }
        
        return base64.b64encode(json.dumps(result).encode()).decode()
    
    def _decrypt_key_ecc(self, encrypted_key: str, private_key: ec.EllipticCurvePrivateKey) -> bytes:
        """Decrypt AES key using ECC private key."""
        # Decode the encrypted key data
        encrypted_data = json.loads(base64.b64decode(encrypted_key).decode())
        
        # Load ephemeral public key
        ephemeral_public_pem = base64.b64decode(encrypted_data['ephemeral_public_key'])
        ephemeral_public_key = serialization.load_pem_public_key(ephemeral_public_pem)
        
        # Perform ECDH
        shared_key = private_key.exchange(ec.ECDH(), ephemeral_public_key)
        
        # Derive decryption key using HKDF
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'encrypted-llm-chat-key-derivation'
        ).derive(shared_key)
        
        # Decrypt AES key
        aes_key = self._decrypt_aes(encrypted_data['encrypted_aes_key'], derived_key)
        return aes_key
    
    def encrypt_message(
        self, 
        message: str, 
        public_key: Union[rsa.RSAPublicKey, ec.EllipticCurvePublicKey],
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Encrypt a message using hybrid encryption.
        
        Args:
            message: The message to encrypt
            public_key: RSA or ECC public key
            metadata: Optional metadata to include
            
        Returns:
            Base64-encoded encrypted message bundle
        """
        # Convert message to bytes
        message_bytes = message.encode('utf-8')
        
        # Generate AES key
        aes_key = self._generate_aes_key()
        
        # Encrypt message with AES
        encrypted_message = self._encrypt_aes(message_bytes, aes_key)
        
        # Encrypt AES key with public key
        if isinstance(public_key, rsa.RSAPublicKey):
            encrypted_aes_key = self._encrypt_key_rsa(aes_key, public_key)
            key_type = "rsa"
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            encrypted_aes_key = self._encrypt_key_ecc(aes_key, public_key)
            key_type = "ecc"
        else:
            raise ValueError("Unsupported key type")
        
        # Create message bundle
        bundle = {
            'version': '1.0',
            'key_type': key_type,
            'encrypted_aes_key': encrypted_aes_key,
            'encrypted_message': encrypted_message,
            'metadata': metadata or {}
        }
        
        # Encode bundle
        bundle_json = json.dumps(bundle)
        return base64.b64encode(bundle_json.encode()).decode()
    
    def decrypt_message(
        self, 
        encrypted_bundle: str, 
        private_key: Union[rsa.RSAPrivateKey, ec.EllipticCurvePrivateKey]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Decrypt a message using hybrid decryption.
        
        Args:
            encrypted_bundle: Base64-encoded encrypted message bundle
            private_key: RSA or ECC private key
            
        Returns:
            Tuple of (decrypted_message, metadata)
        """
        # Decode bundle
        bundle_json = base64.b64decode(encrypted_bundle).decode()
        bundle = json.loads(bundle_json)
        
        # Extract components
        key_type = bundle['key_type']
        encrypted_aes_key = bundle['encrypted_aes_key']
        encrypted_message = bundle['encrypted_message']
        metadata = bundle.get('metadata', {})
        
        # Decrypt AES key
        if key_type == "rsa" and isinstance(private_key, rsa.RSAPrivateKey):
            aes_key = self._decrypt_key_rsa(encrypted_aes_key, private_key)
        elif key_type == "ecc" and isinstance(private_key, ec.EllipticCurvePrivateKey):
            aes_key = self._decrypt_key_ecc(encrypted_aes_key, private_key)
        else:
            raise ValueError(f"Key type mismatch: bundle has {key_type}, got {type(private_key)}")
        
        # Decrypt message
        message_bytes = self._decrypt_aes(encrypted_message, aes_key)
        message = message_bytes.decode('utf-8')
        
        return message, metadata
    
    def verify_certificate(self, cert: x509.Certificate) -> bool:
        """
        Basic certificate verification.
        In production, you'd want more thorough validation.
        """
        try:
            # Check if certificate is within valid time range
            now = x509.datetime.datetime.utcnow()
            if now < cert.not_valid_before or now > cert.not_valid_after:
                return False
            
            # For self-signed certificates, we can't verify the chain
            # In production, you'd verify against a trusted CA
            return True
            
        except Exception:
            return False


def main():
    """Demo encryption/decryption."""
    from crypto.key_manager import KeyManager
    
    # Setup keys
    key_manager = KeyManager()
    
    # Load or generate keys
    try:
        user_private_key = key_manager.load_private_key("user_rsa_private_key.pem")
        model_public_key = key_manager.load_public_key("model_rsa_public_key.pem")
        model_private_key = key_manager.load_private_key("model_rsa_private_key.pem")
        print("✅ Loaded existing RSA keys")
    except FileNotFoundError:
        print("⚠️  Keys not found. Run 'python crypto/key_manager.py' first to generate keys.")
        return
    
    # Create crypto instance
    crypto = MessageCrypto()
    
    # Test message
    original_message = "Hello, encrypted LLM! This is a secret prompt about AI safety."
    metadata = {"timestamp": "2024-01-01T12:00:00Z", "user_id": "demo_user"}
    
    print(f"\n📝 Original message: {original_message}")
    print(f"📋 Metadata: {metadata}")
    
    # Encrypt message (user encrypts for model)
    encrypted_bundle = crypto.encrypt_message(original_message, model_public_key, metadata)
    print(f"\n🔐 Encrypted bundle (first 100 chars): {encrypted_bundle[:100]}...")
    print(f"📏 Bundle size: {len(encrypted_bundle)} characters")
    
    # Decrypt message (model decrypts)
    decrypted_message, recovered_metadata = crypto.decrypt_message(encrypted_bundle, model_private_key)
    print(f"\n🔓 Decrypted message: {decrypted_message}")
    print(f"📋 Recovered metadata: {recovered_metadata}")
    
    # Verify
    assert original_message == decrypted_message
    assert metadata == recovered_metadata
    print("\n✅ Encryption/decryption test passed!")


if __name__ == "__main__":
    main()
