"""
Key Management Module for Encrypted LLM Chat

Handles RSA/ECC key pair generation, certificate creation, and key storage.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, PublicFormat, NoEncryption
)
from cryptography import x509
from cryptography.x509.oid import NameOID


class KeyManager:
    """Manages cryptographic keys and certificates for encrypted LLM chat."""
    
    def __init__(self, certs_dir: str = "certs"):
        """Initialize KeyManager with certificate directory."""
        self.certs_dir = Path(certs_dir)
        self.certs_dir.mkdir(exist_ok=True)
    
    def generate_rsa_key_pair(self, key_size: int = 2048) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """Generate RSA key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    def generate_ecc_key_pair(self) -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
        """Generate ECC key pair using P-256 curve."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        return private_key, public_key
    
    def create_self_signed_certificate(
        self,
        private_key,
        subject_name: str,
        days_valid: int = 365
    ) -> x509.Certificate:
        """Create a self-signed certificate."""
        
        # Create subject and issuer (same for self-signed)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Encrypted LLM Chat"),
            x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
        ])
        
        # Create certificate
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=days_valid)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("encrypted-llm-chat"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        return cert
    
    def save_private_key(self, private_key, filepath: str, password: Optional[bytes] = None):
        """Save private key to file."""
        encryption = NoEncryption() if password is None else serialization.BestAvailableEncryption(password)
        
        pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        )
        
        with open(self.certs_dir / filepath, 'wb') as f:
            f.write(pem)
    
    def save_public_key(self, public_key, filepath: str):
        """Save public key to file."""
        pem = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(self.certs_dir / filepath, 'wb') as f:
            f.write(pem)
    
    def save_certificate(self, certificate: x509.Certificate, filepath: str):
        """Save certificate to file."""
        pem = certificate.public_bytes(Encoding.PEM)
        
        with open(self.certs_dir / filepath, 'wb') as f:
            f.write(pem)
    
    def load_private_key(self, filepath: str, password: Optional[bytes] = None):
        """Load private key from file."""
        with open(self.certs_dir / filepath, 'rb') as f:
            return serialization.load_pem_private_key(f.read(), password=password)
    
    def load_public_key(self, filepath: str):
        """Load public key from file."""
        with open(self.certs_dir / filepath, 'rb') as f:
            return serialization.load_pem_public_key(f.read())
    
    def load_certificate(self, filepath: str) -> x509.Certificate:
        """Load certificate from file."""
        with open(self.certs_dir / filepath, 'rb') as f:
            return x509.load_pem_x509_certificate(f.read())
    
    def setup_user_keys(self, use_ecc: bool = False) -> Tuple[str, str, str]:
        """Generate and save user keys and certificate."""
        if use_ecc:
            private_key, public_key = self.generate_ecc_key_pair()
            key_type = "ecc"
        else:
            private_key, public_key = self.generate_rsa_key_pair()
            key_type = "rsa"
        
        # Create certificate
        cert = self.create_self_signed_certificate(private_key, "user-client")
        
        # Save files
        private_key_file = f"user_{key_type}_private_key.pem"
        public_key_file = f"user_{key_type}_public_key.pem"
        cert_file = f"user_{key_type}_certificate.pem"
        
        self.save_private_key(private_key, private_key_file)
        self.save_public_key(public_key, public_key_file)
        self.save_certificate(cert, cert_file)
        
        return private_key_file, public_key_file, cert_file
    
    def setup_model_keys(self, use_ecc: bool = False) -> Tuple[str, str, str]:
        """Generate and save model keys and certificate."""
        if use_ecc:
            private_key, public_key = self.generate_ecc_key_pair()
            key_type = "ecc"
        else:
            private_key, public_key = self.generate_rsa_key_pair()
            key_type = "rsa"
        
        # Create certificate
        cert = self.create_self_signed_certificate(private_key, "llm-model-server")
        
        # Save files
        private_key_file = f"model_{key_type}_private_key.pem"
        public_key_file = f"model_{key_type}_public_key.pem"
        cert_file = f"model_{key_type}_certificate.pem"
        
        self.save_private_key(private_key, private_key_file)
        self.save_public_key(public_key, public_key_file)
        self.save_certificate(cert, cert_file)
        
        return private_key_file, public_key_file, cert_file


def main():
    """Demo key generation."""
    key_manager = KeyManager()
    
    print("🔑 Generating RSA keys for user and model...")
    user_files = key_manager.setup_user_keys(use_ecc=False)
    model_files = key_manager.setup_model_keys(use_ecc=False)
    
    print(f"✅ User keys: {user_files}")
    print(f"✅ Model keys: {model_files}")
    
    print("\n🔑 Generating ECC keys for user and model...")
    user_ecc_files = key_manager.setup_user_keys(use_ecc=True)
    model_ecc_files = key_manager.setup_model_keys(use_ecc=True)
    
    print(f"✅ User ECC keys: {user_ecc_files}")
    print(f"✅ Model ECC keys: {model_ecc_files}")
    
    print(f"\n📁 All keys saved to: {key_manager.certs_dir}")


if __name__ == "__main__":
    main()
